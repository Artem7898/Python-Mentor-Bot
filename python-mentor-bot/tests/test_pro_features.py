"""Verify the bounded Pro tools without evaluating any submitted code."""

import pytest

from bot.i18n import Locale
from bot.pro_features import (
    INTERVIEW_COUNT,
    MAX_INTERVIEW_ANSWER,
    MAX_REVIEW_SOURCE,
    Finding,
    ReviewStatus,
    analyze_code,
    interview_complete,
    interview_feedback,
    interview_question,
    review_code,
    review_prompt,
    valid_interview_answer,
)
from bot.pro_review_copy import Rule


def test_review_uses_line_numbers_and_resolves_direct_import_aliases() -> None:
    source = """from requests import get as request
from time import sleep as pause

async def index():
    pause(0.01)
    return request("https://example.org", timeout=None, verify=False)"""
    results = analyze_code(source)

    assert results.status == ReviewStatus.OK
    assert results.findings == (
        Finding(6, Rule.TLS),
        Finding(6, Rule.HTTP_TIMEOUT),
        Finding(5, Rule.BLOCKING_ASYNC),
        Finding(6, Rule.BLOCKING_ASYNC),
    )


@pytest.mark.parametrize(
    ("source", "rule"),
    [
        ("result = eval(fragment)", Rule.DYNAMIC_EXECUTION),
        ("subprocess.run(command, shell=True)", Rule.SHELL),
        ("value = pickle.loads(payload)", Rule.DESERIALIZE),
        ("data = yaml.load(document)", Rule.YAML),
        ('db.execute(f"SELECT name FROM users WHERE id = {user_id}")', Rule.SQL),
        ("def append(items=[]):\n    return items", Rule.MUTABLE_DEFAULT),
        ("try:\n    parse()\nexcept:\n    pass", Rule.BARE_EXCEPT),
        ("try:\n    parse()\nexcept ValueError:\n    pass", Rule.SWALLOWED_ERROR),
        ("total = sum([price for price in prices])", Rule.MATERIALIZATION),
        ("asyncio.create_task(work())", Rule.DETACHED_TASK),
    ],
)
def test_review_detects_known_advice_patterns(source: str, rule: Rule) -> None:
    assert rule in {finding.rule for finding in analyze_code(source).findings}


def test_review_does_not_flag_safe_forms_or_nested_sync_scopes() -> None:
    source = """import asyncio
import time
import yaml

db.execute("SELECT name FROM users " + "WHERE id = ?", (user_id,))
yaml.load(document, Loader=yaml.SafeLoader)
result = sum(price for price in prices)

async def route():
    def blocking():
        time.sleep(1)
    await asyncio.to_thread(blocking)
    return await fetch()"""
    assert analyze_code(source).findings == ()


def test_review_supports_fences_without_echoing_a_literal() -> None:
    source = "```python\npassword = '<REVIEW_FIXTURE_123>'\n```"
    result = review_code(source, Locale.EN)

    assert "Line 1" in result
    assert "Literal in a secret field" in result
    assert "REVIEW_FIXTURE_123" not in result


def test_review_rejects_invalid_and_oversized_input() -> None:
    assert analyze_code("   ").status == ReviewStatus.EMPTY
    assert analyze_code("#" * (MAX_REVIEW_SOURCE + 1)).status == ReviewStatus.TOO_LONG
    assert analyze_code("total = " + "+".join("1" for _ in range(70))).status == (
        ReviewStatus.TOO_COMPLEX
    )
    result = analyze_code("name = 'Ada'\nbroken =")
    assert result.status == ReviewStatus.SYNTAX
    assert result.syntax_line == 2
    assert "broken =" not in review_code("name = 'Ada'\nbroken =", Locale.EN)


@pytest.mark.parametrize("locale", list(Locale))
def test_review_limits_html_size_and_findings(locale: Locale) -> None:
    source = "\n".join(
        (
            "result = eval(fragment)",
            "subprocess.run(command, shell=True)",
            "data = pickle.loads(payload)",
            "data = yaml.load(document)",
            'db.execute(f"SELECT name FROM users WHERE id = {user_id}")',
            "httpx.Client(verify=False)",
            "password = 'review-fixture-secret'",
            "total = sum([price for price in prices])",
        )
    )
    review = analyze_code(source)
    rendered = review_code(source, locale)
    assert len(review.findings) == 6 and review.truncated
    assert "review-fixture-secret" not in rendered
    assert len(rendered.encode("utf-16-le")) // 2 <= 4096
    assert str(MAX_REVIEW_SOURCE) in review_prompt(locale)


@pytest.mark.parametrize("locale", list(Locale))
def test_interview_renders_all_questions_and_feedback_within_telegram_limits(
    locale: Locale,
) -> None:
    for index in range(INTERVIEW_COUNT):
        question = interview_question(index, locale)
        feedback = interview_feedback(index, "answer fixture <tag>", locale)
        assert question is not None and feedback is not None
        assert f"{index + 1}/{INTERVIEW_COUNT}" in question
        assert "answer fixture" not in feedback
        assert len(f"{feedback}\n\n{question}".encode("utf-16-le")) // 2 <= 4096
    assert interview_complete(locale)
    assert interview_question(-1, locale) is None
    assert interview_question(INTERVIEW_COUNT, locale) is None
    assert interview_feedback(INTERVIEW_COUNT, "try", locale) is None


def test_interview_feedback_identifies_topics_without_grading() -> None:
    feedback = interview_feedback(2, "Use select_related, then count queries.", Locale.EN)
    assert feedback is not None
    mentioned, todo = feedback.split("What to cover in more detail", maxsplit=1)
    assert "select_related for customer" in mentioned
    assert "prefetch_related for items" in todo
    assert "Sample answer" in feedback
    assert "This check uses terms in your text" in feedback


def test_interview_input_bound_is_checked_before_feedback() -> None:
    assert valid_interview_answer("x" * MAX_INTERVIEW_ANSWER)
    assert not valid_interview_answer("x" * (MAX_INTERVIEW_ANSWER + 1))
    assert not valid_interview_answer(" \t\n")
    assert interview_feedback(0, "", Locale.EN) == (
        f"Enter a text answer of up to {MAX_INTERVIEW_ANSWER} characters."
    )
