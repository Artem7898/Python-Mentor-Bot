"""Exercise privacy and role boundaries through the Telegram dispatcher."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from aiogram import Bot
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage
from aiogram.types import InlineKeyboardMarkup, User
from test_handlers import TelegramHarness, telegram

from bot import access
from bot.config import Config
from bot.lesson_models import LessonLevel
from bot.lessons import LessonTopic
from main import create_dispatcher

LEARNER = 19
MENTOR = 82
EDITOR = 84
OTHER_LEARNER = 96
GROUP = {"id": -100001, "type": "supergroup", "title": "Study group"}


def _private(user_id: int) -> dict[str, object]:
    return {"id": user_id, "type": "private"}


def _identify(client: TelegramHarness, user_id: int) -> None:
    client.user.update({"id": user_id, "username": f"learner_{user_id}"})


def _responses(client: TelegramHarness) -> str:
    texts: list[str] = []
    for method in client.requests:
        if isinstance(method, AnswerCallbackQuery | EditMessageText | SendMessage):
            texts.append(method.text or "")
        if isinstance(method, EditMessageText | SendMessage) and isinstance(
            method.reply_markup, InlineKeyboardMarkup
        ):
            texts.extend(
                button.text for row in method.reply_markup.inline_keyboard for button in row
            )
    return "\n".join(texts)


@asynccontextmanager
async def _telegram(
    db_path: Path, monkeypatch: pytest.MonkeyPatch, *, request_limit: int = 20
) -> AsyncIterator[TelegramHarness]:
    config = Config.from_sources(
        {
            "BOT_TOKEN": "123:offline-test",
            "BOT_MENTOR_IDS": str(MENTOR),
            "BOT_EDITOR_IDS": str(EDITOR),
        },
        environ={},
    )

    async def bot_profile(_bot: Bot) -> User:
        return User(id=123, is_bot=True, first_name="Mentor", username="mentor_test_bot")

    monkeypatch.setattr(Bot, "me", bot_profile)
    async with telegram(db_path, monkeypatch, language_code="en") as client:
        client.dispatcher = create_dispatcher(config, request_limit=request_limit)
        client.dispatcher["bot_username"] = "mentor_test_bot"
        yield client


def test_shared_chat_neither_discloses_nor_changes_personal_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.db.get_or_create_user(LEARNER, "private_handle")
            await client.db.update_user_progress(LEARNER, LessonTopic.PYTHON_315, 1)
            await client.db.submit_question(LEARNER, "My private worksheet question")

            await client.callback("dashboard:progress", chat=GROUP)
            markup = client.last_message().reply_markup
            assert isinstance(markup, InlineKeyboardMarkup)
            assert markup.inline_keyboard[0][0].url == "https://t.me/mentor_test_bot?start=menu"
            await client.message("/questions", chat=GROUP)
            assert "private_handle" not in _responses(client)
            assert "My private worksheet question" not in _responses(client)
            assert "current topic" not in _responses(client).casefold()
            await client.callback("topic:oop", chat=GROUP)

            user = await client.db.get_user(LEARNER)
            assert user is not None
            assert (user.current_topic, user.current_page) == (LessonTopic.PYTHON_315, 1)

    asyncio.run(scenario())


def test_shared_chat_does_not_capture_followup_text_as_a_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.callback("dashboard:ask", chat=GROUP)
            await client.message("Unrelated group discussion", chat=GROUP)

            assert await client.db.get_user(LEARNER) is None
            assert not await client.db.list_questions(LEARNER)

    asyncio.run(scenario())


def test_chat_identity_placeholder_cannot_register_a_personal_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.message("/start", chat=GROUP, sender_chat=GROUP)
            assert await client.db.get_user(LEARNER) is None

    asyncio.run(scenario())


def test_private_delete_requires_confirmation_and_only_removes_the_requesting_learner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            for user_id in (LEARNER, OTHER_LEARNER):
                await client.db.get_or_create_user(user_id, f"learner_{user_id}")
                await client.db.submit_question(user_id, f"Question from learner {user_id}")

            await client.callback("privacy:confirm-delete")
            assert await client.db.get_user(LEARNER) is not None
            await client.message("/privacy")
            assert "privacy:delete" in client.inline_buttons()
            await client.callback("privacy:delete")
            assert {"privacy:confirm-delete", "privacy:cancel"} <= client.inline_buttons().keys()
            await client.callback("privacy:cancel")
            await client.callback("privacy:confirm-delete")
            assert await client.db.get_user(LEARNER) is not None

            await client.callback("privacy:delete")
            await client.callback("privacy:confirm-delete", chat=GROUP)
            assert await client.db.get_user(LEARNER) is not None
            await client.callback("privacy:confirm-delete")

            assert await client.db.get_user(LEARNER) is None
            assert not await client.db.list_questions(LEARNER)
            assert await client.db.get_user(OTHER_LEARNER) is not None
            assert len(await client.db.list_questions(OTHER_LEARNER)) == 1

            await client.message("/start")
            await client.callback("privacy:confirm-delete")
            assert await client.db.get_user(LEARNER) is not None

    asyncio.run(scenario())


def test_mentor_actions_are_restricted_by_sender_and_chat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.db.get_or_create_user(OTHER_LEARNER, "question_author")
            question = await client.db.submit_question(OTHER_LEARNER, "Unique private question")

            await client.message("/mentor")
            await client.message("/editor")
            await client.callback(f"mentor:view:{question.id}")
            await client.callback(f"mentor:review:{question.id}")
            assert "Unique private question" not in _responses(client)
            assert "Course editing" not in _responses(client)
            assert (await client.db.list_questions(OTHER_LEARNER))[0].status.value == "new"

            _identify(client, EDITOR)
            client.requests.clear()
            await client.callback(f"mentor:view:{question.id}", chat=_private(EDITOR))
            assert "Unique private question" not in _responses(client)
            await client.message("/editor", chat=_private(EDITOR))
            assert "Course editing" in _responses(client)

            _identify(client, MENTOR)
            client.requests.clear()
            await client.callback(f"mentor:view:{question.id}", chat=GROUP)
            await client.callback(f"mentor:review:{question.id}", chat=GROUP)
            assert "Unique private question" not in _responses(client)
            assert (await client.db.list_questions(OTHER_LEARNER))[0].status.value == "new"

    asyncio.run(scenario())


def test_private_question_review_and_reply_updates_learner_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with _telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.message("/start")
            await client.callback("dashboard:ask")
            await client.message("How do I use <list>?")
            await client.message("/questions")
            questions = await client.db.list_questions(LEARNER)
            assert len(questions) == 1
            question = questions[0]
            assert question.status.value == "new"

            _identify(client, MENTOR)
            await client.message("/mentor", chat=_private(MENTOR))
            assert f"mentor:view:{question.id}" in client.inline_buttons()
            client.requests.clear()
            await client.callback(f"mentor:view:{question.id}", chat=_private(MENTOR))
            assert "&lt;list&gt;" in _responses(client)
            assert "<list>" not in _responses(client)

            await client.callback(f"mentor:review:{question.id}", chat=_private(MENTOR))
            assert (await client.db.list_questions(LEARNER))[0].status.value == "in_review"
            await client.callback(f"mentor:reply:{question.id}", chat=_private(MENTOR))
            await client.message("Use list() to convert an iterable.", chat=_private(MENTOR))
            answered = (await client.db.list_questions(LEARNER))[0]
            assert answered.status.value == "answered"
            assert answered.answer == "Use list() to convert an iterable."
            await client.callback(f"mentor:reply:{question.id}", chat=_private(MENTOR))
            await client.message("Another draft answer.", chat=_private(MENTOR))
            assert (await client.db.list_questions(LEARNER))[0].answer == answered.answer

            _identify(client, LEARNER)
            await client.message("/questions")
            assert f"questions:view:{question.id}" in client.inline_buttons()
            await client.callback(f"questions:view:{question.id}")
            answer_button = f"questions:read:{question.id}:a:0"
            assert answer_button in client.inline_buttons()
            await client.callback(answer_button)
            assert "Use list() to convert an iterable." in client.last_display().text

            _identify(client, OTHER_LEARNER)
            client.requests.clear()
            await client.callback(answer_button, chat=_private(OTHER_LEARNER))
            assert "Use list() to convert an iterable." not in _responses(client)

    asyncio.run(scenario())


def test_rate_limit_leaves_capacity_for_other_senders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = 1.0
    monkeypatch.setattr(access, "monotonic", lambda: now)

    async def scenario() -> None:
        nonlocal now
        async with _telegram(tmp_path / "bot.db", monkeypatch, request_limit=1) as client:
            await client.message("/help")
            assert "/help" in _responses(client)
            await client.message("/start")
            assert await client.db.get_user(LEARNER) is None

            _identify(client, OTHER_LEARNER)
            await client.message("/start", chat=_private(OTHER_LEARNER))
            assert await client.db.get_user(OTHER_LEARNER) is not None

            now += 11.0
            _identify(client, LEARNER)
            await client.message("/start")
            assert await client.db.get_user(LEARNER) is not None

    asyncio.run(scenario())


def test_learning_preferences_change_only_in_the_private_learner_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "bot.db"

    async def select() -> None:
        async with _telegram(db_path, monkeypatch) as client:
            await client.message("/start")
            await client.callback("study:settings")
            assert {"study:level:professional", "study:compact:0"} <= client.inline_buttons().keys()

            await client.callback("study:level:professional", chat=GROUP)
            assert (await client.db.get_preferences(LEARNER)).level is None
            await client.callback("study:level:professional")
            await client.callback("study:compact:0")

    async def reopen() -> None:
        async with _telegram(db_path, monkeypatch) as client:
            preferences = await client.db.get_preferences(LEARNER)
            assert preferences.level is LessonLevel.PROFESSIONAL
            assert not preferences.compact
            await client.callback("study:settings")
            assert "study:compact:1" in client.inline_buttons()

    asyncio.run(select())
    asyncio.run(reopen())
