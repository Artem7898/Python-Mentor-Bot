import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
import pytest
from pydantic import SecretStr

from bot import mentor_answers
from bot.i18n import Locale
from bot.mentor_answers import MAX_ANSWER_UNITS, MentorAnswerer, OpenAIAnswerProvider
from bot.mentor_topics import local_answer


@pytest.mark.parametrize(
    ("question", "locale", "expected", "lesson"),
    [
        (
            "в чём разница между списком и кортежем?",
            Locale.RU,
            "TypeError",
            "Урок по теме",
        ),
        (
            "What is the difference between a list and a tuple?",
            Locale.EN,
            "fixed sequence",
            "Related lesson",
        ),
        (
            "¿Cuál es la diferencia entre las listas y las tuplas?",
            Locale.ES,
            "secuencia fija",
            "Lección relacionada",
        ),
        ("Что такое проблема N+1 в Django?", Locale.RU, "assertNumQueries", "Урок по теме"),
        (
            "Why does FastAPI return 422 on POST?",
            Locale.EN,
            "detail[].loc",
            "Related lesson",
        ),
        ("¿Qué es el modo estricto de Pydantic?", Locale.ES, "ConfigDict", "Lección relacionada"),
        ("What is a generator?", Locale.EN, "next()", "Related lesson"),
        ("TaskGroup vs asyncio.gather()", Locale.EN, "ExceptionGroup", "Related lesson"),
    ],
)
def test_curated_answer_has_explanation_and_course_reference(
    question: str, locale: Locale, expected: str, lesson: str
) -> None:
    answer = local_answer(question, locale)
    assert answer and expected in answer and lesson in answer


@pytest.mark.parametrize(
    "question",
    [
        "Why is this novel FastAPI 422 happening with my Pydantic model?",
        "FastAPI 422\nprint('unrelated code')",
        "Django 6.2",
        "What happened here?",
    ],
)
def test_local_answer_does_not_guess_from_keywords(question: str) -> None:
    assert local_answer(question, Locale.EN) is None


class _External:
    def __init__(self, reply: str | None = "A provider answer.") -> None:
        self.reply = reply
        self.calls: list[tuple[str, Locale]] = []

    async def answer(self, question: str, locale: Locale) -> str | None:
        self.calls.append((question, locale))
        return self.reply


def test_external_answer_requires_consent_and_is_skipped_for_local_coverage() -> None:
    async def execute() -> None:
        provider = _External()
        mentor = MentorAnswerer(provider)
        assert mentor.external_enabled
        assert not MentorAnswerer().external_enabled

        assert await mentor.answer("How do I test a custom callback?", Locale.ES) is None
        assert await mentor.answer("FastAPI 422", Locale.ES, allow_external=True)
        assert (
            await mentor.answer(
                "Please debug Authorization: Bearer example-private-value",
                Locale.EN,
                allow_external=True,
            )
            is None
        )
        assert provider.calls == []
        result = await mentor.answer(
            "How do I test a custom callback?", Locale.ES, allow_external=True
        )
        assert result == "A provider answer."
        assert provider.calls == [("How do I test a custom callback?", Locale.ES)]

    asyncio.run(execute())


def test_oversized_provider_output_goes_to_fallback_without_sending_a_partial_answer() -> None:
    mentor = MentorAnswerer(_External("🧪" * MAX_ANSWER_UNITS))
    answer = asyncio.run(mentor.answer("unfamiliar question", Locale.EN, allow_external=True))
    assert answer is None


def _payload(text: str) -> dict[str, object]:
    return {
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            },
        ],
    }


def _fake_http(
    monkeypatch: pytest.MonkeyPatch, payload: object, status: int = 200
) -> list[tuple[str, dict[str, Any]]]:
    requests: list[tuple[str, dict[str, Any]]] = []

    class Content:
        async def iter_chunked(self, _: int) -> AsyncIterator[bytes]:
            data = json.dumps(payload).encode()
            yield data[:13]
            yield data[13:]

    class Response:
        content = Content()

        def __init__(self) -> None:
            self.status = status

    class Session:
        def __init__(self, *, timeout: aiohttp.ClientTimeout, trust_env: bool) -> None:
            assert timeout.total == 15 and timeout.connect == 4 and trust_env

        async def __aenter__(self) -> Session:
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        @asynccontextmanager
        async def post(self, url: str, **kwargs: Any) -> AsyncIterator[Response]:
            requests.append((url, kwargs))
            yield Response()

    monkeypatch.setattr(mentor_answers.aiohttp, "ClientSession", Session)
    return requests


def test_openai_prompt_roles_and_text_only_response(monkeypatch: pytest.MonkeyPatch) -> None:
    requests = _fake_http(monkeypatch, _payload("TestCase creates an isolated test database."))
    model = OpenAIAnswerProvider(SecretStr("stub-private-key"))
    answer = asyncio.run(model.answer("Django test isolation?", Locale.ES))
    assert answer == "TestCase creates an isolated test database."
    assert len(requests) == 1
    url, request = requests[0]
    assert url == "https://api.openai.com/v1/responses"
    assert request["allow_redirects"] is False
    assert request["headers"]["Authorization"] == "Bearer stub-private-key"
    message = request["json"]
    assert message["store"] is False
    assert message["tools"] == []
    assert message["input"] == [{"role": "user", "content": "Django test isolation?"}]
    assert "Answer in Spanish." in message["instructions"]
    assert "stub-private-key" not in str(message)


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        (_payload("NO_ANSWER"), 200),
        (_payload("Echoed token stub-private-key"), 200),
        (_payload("Ignored"), 401),
        ({"status": "incomplete", "output": _payload("Ignored")["output"]}, 200),
        ({"status": "completed", "output": "invalid shape"}, 200),
    ],
)
def test_unusable_openai_responses_fall_back(
    monkeypatch: pytest.MonkeyPatch, payload: object, status: int
) -> None:
    _fake_http(monkeypatch, payload, status=status)
    mentor = MentorAnswerer(OpenAIAnswerProvider("stub-private-key"))
    result = asyncio.run(mentor.answer("unfamiliar question", Locale.EN, allow_external=True))
    assert result is None


def test_external_network_failure_falls_back_without_leaking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timeout(**kwargs: object) -> None:
        raise TimeoutError("stub-private-key")

    monkeypatch.setattr(mentor_answers.aiohttp, "ClientSession", timeout)
    mentor = MentorAnswerer(OpenAIAnswerProvider("stub-private-key"))
    result = asyncio.run(mentor.answer("unfamiliar question", Locale.EN, allow_external=True))
    assert result is None
