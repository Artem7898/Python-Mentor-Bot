from collections.abc import Iterator

import pytest
from aiogram.types import InlineKeyboardMarkup

from bot.i18n import Locale
from bot.lesson_models import LessonLevel, LessonTopic
from bot.lessons import LessonManager
from bot.study_copy import QUIZZES, study_tr
from bot.study_ui import (
    bookmarks_view,
    catalog_view,
    contents_view,
    dashboard_view,
    lesson_actions,
    lesson_id,
    lesson_location,
    progress_view,
    quiz_view,
    search_view,
    settings_view,
)


def _payloads(keyboard: InlineKeyboardMarkup) -> Iterator[str]:
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data is not None:
                yield button.callback_data


def test_every_current_lesson_has_a_unique_stable_id() -> None:
    references = set()
    for topic in LessonTopic:
        for index in range(LessonManager.get_total_pages(topic)):
            key = lesson_id(topic, index)
            assert key is not None
            assert key not in references
            assert lesson_location(key) == (topic, index)
            references.add(key)
    assert QUIZZES.keys() <= references
    assert lesson_id(LessonTopic.BASICS, 0) == "basics.intro"
    assert lesson_id(LessonTopic.DJANGO, 1) == "django.models"
    assert lesson_location("retired") is None


def test_first_and_returning_dashboard_have_different_primary_actions() -> None:
    initial, first_keyboard = dashboard_view(Locale.EN)
    returning, resume_keyboard = dashboard_view(Locale.EN, "django.models")

    assert "first lesson" in initial
    assert next(_payloads(first_keyboard)) == "study:open:basics.intro"
    assert next(_payloads(resume_keyboard)) == "study:open:django.models"
    assert "Models, migrations and admin" in returning
    assert "Lesson 2 of" in returning
    assert dashboard_view(Locale.EN, "retired") == dashboard_view(Locale.EN)


def test_catalogue_filter_and_localized_diacritic_insensitive_search() -> None:
    _, contents = contents_view(Locale.ES, LessonTopic.DJANGO, LessonLevel.PROFESSIONAL)
    listed = [payload for payload in _payloads(contents) if payload.startswith("study:open:")]
    assert "study:open:django.asgi" in listed
    assert "study:open:django.models" not in listed
    _, matches = search_view(Locale.ES, " validacion   cruzada ")
    assert next(_payloads(matches)) == "study:open:pydantic.cross-fields"
    markup, _ = search_view(Locale.EN, "<b>Python</b>")
    assert "&lt;b&gt;Python&lt;/b&gt;" in markup


def test_partial_results_and_paginated_bookmarks() -> None:
    text, search = search_view(Locale.EN, "django")
    assert "Showing the first 10" in text
    assert sum(payload.startswith("study:open:") for payload in _payloads(search)) == 10

    bookmarks = tuple(
        f"django.{slug}"
        for slug in (
            "routes",
            "models",
            "forms",
            "n-plus-one",
            "transactions",
            "tests",
            "asgi",
            "upgrade",
            "latest",
        )
    )
    _, first_page = bookmarks_view(Locale.EN, bookmarks)
    _, last_page = bookmarks_view(Locale.EN, bookmarks, page=10)
    assert "study:bookmarks:1" in _payloads(first_page)
    assert "study:bookmarks:0" in _payloads(last_page)
    assert tuple(p for p in _payloads(last_page) if p.startswith("study:open:")) == (
        "study:open:django.latest",
    )


@pytest.mark.parametrize("locale", tuple(Locale))
def test_views_and_quiz_feedback_fit_telegram(locale: Locale) -> None:
    views = [
        dashboard_view(locale, "python315.profiling"),
        settings_view(locale, LessonLevel.PROFESSIONAL, True),
        catalog_view(locale, "practice", None),
        contents_view(locale, LessonTopic.DRF),
        search_view(locale, "Django"),
        progress_view(locale, ("retired", "drf.serializers")),
        bookmarks_view(locale, ("drf.serializers",)),
    ]
    for key, quiz in QUIZZES.items():
        question = quiz_view(locale, key)
        right = quiz_view(locale, key, quiz.correct)
        wrong = quiz_view(locale, key, (quiz.correct + 1) % len(quiz.options))
        assert question is not None and right is not None and wrong is not None
        assert study_tr(locale, "quiz_right") in right[0]
        assert study_tr(locale, "quiz_wrong") in wrong[0]
        assert right[0] != question[0]
        assert quiz_view(locale, key, len(quiz.options)) is None
        views.extend((question, right, wrong))

    for text, keyboard in views:
        assert 0 < len(text.encode("utf-16-le")) // 2 <= 4096
        assert all(0 < len(data.encode()) <= 64 for data in _payloads(keyboard))

    actions = lesson_actions(locale, "django.n-plus-one", bookmark=True, completed=True)
    assert any(button.callback_data == "study:bookmark:django.n-plus-one:0" for button in actions)
    assert any(button.callback_data == "study:quiz:django.n-plus-one" for button in actions)
