"""Check the bundled curriculum against Telegram's rendering and routing constraints."""

from html.parser import HTMLParser

import pytest

from bot.handlers import (
    LessonSelection,
    lesson_keyboard,
    lesson_text,
    parse_selection,
    topics_keyboard,
)
from bot.i18n import Locale, tr
from bot.lesson_models import LessonLevel
from bot.lessons import LessonManager, LessonTopic


class TelegramText(HTMLParser):
    """Extract entity-decoded text and reject unbalanced generated markup."""

    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.tags: list[str] = []

    def handle_data(self, data: str) -> None:
        self.text.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        assert self.tags and self.tags[-1] == tag, f"Unexpected closing HTML tag: {tag}"
        self.tags.pop()

    @property
    def utf16_units(self) -> int:
        return len("".join(self.text).encode("utf-16-le")) // 2


@pytest.mark.parametrize("topic", tuple(LessonTopic))
def test_page_indices_are_stable_across_locales(topic: LessonTopic) -> None:
    page_count = LessonManager.get_total_pages(topic, Locale.RU)
    assert page_count > 0
    for locale in Locale:
        assert LessonManager.get_total_pages(topic, locale) == page_count
        for page_number in range(page_count):
            payload = f"page:{topic.value}:{page_number}"
            assert parse_selection(payload, locale) == LessonSelection(topic, page_number, "lesson")
            page = LessonManager.get_topic_content(topic, page_number, locale)
            reference = LessonManager.get_topic_content(topic, page_number, Locale.RU)
            assert page is not None and reference is not None
            assert isinstance(page.level, LessonLevel)
            assert page.level is reference.level
        assert parse_selection(f"page:{topic.value}:{page_count}", locale) is None


def _verify_telegram_view(selection: LessonSelection, locale: Locale) -> set[str]:
    page = LessonManager.get_topic_content(selection.topic, selection.page, locale)
    assert page is not None
    rendered = TelegramText()
    rendered.feed(lesson_text(selection, page, locale))
    rendered.close()
    assert not rendered.tags, (selection, locale, rendered.tags)
    assert 1 <= rendered.utf16_units <= 4096, (selection, locale, rendered.utf16_units)
    if selection.view == "lesson":
        assert tr(locale, f"level_{page.level}") in "".join(rendered.text)

    markup = lesson_keyboard(selection, page, locale)
    payloads = [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data is not None
    ]
    assert len(payloads) == len(set(payloads)), (selection, locale)
    for payload in payloads:
        assert 1 <= len(payload.encode()) <= 64, (selection, locale, payload)
        if payload.startswith(("topic:", "page:", "code:")):
            assert parse_selection(payload, locale) is not None, (selection, locale, payload)
    return set(payloads)


@pytest.mark.parametrize("locale", tuple(Locale))
def test_all_reachable_lesson_views_fit_telegram(locale: Locale) -> None:
    for topic in LessonTopic:
        for page_number in range(LessonManager.get_total_pages(topic, locale)):
            payloads = _verify_telegram_view(LessonSelection(topic, page_number, "lesson"), locale)
            if f"code:{topic.value}:{page_number}" in payloads:
                _verify_telegram_view(LessonSelection(topic, page_number, "code"), locale)


@pytest.mark.parametrize("locale", tuple(Locale))
def test_topics_start_with_basics_and_offer_versioned_learning_paths(locale: Locale) -> None:
    markup = topics_keyboard(locale)
    buttons = [
        button
        for row in markup.inline_keyboard
        for button in row
        if (button.callback_data or "").startswith("topic:")
    ]
    assert buttons[0].callback_data == "topic:basics"
    assert {button.callback_data for button in buttons} == {
        f"topic:{topic.value}" for topic in LessonTopic if topic is not LessonTopic.INSTALL
    }
    by_payload = {button.callback_data: button for button in buttons}
    for topic, version in ((LessonTopic.PYTHON_314, "3.14"), (LessonTopic.PYTHON_315, "3.15")):
        payload = f"topic:{topic.value}"
        assert version in by_payload[payload].text
        assert parse_selection(payload, locale) == LessonSelection(topic, 0, "lesson")


@pytest.mark.parametrize(
    "topic", (LessonTopic.PYTHON_314, LessonTopic.PYTHON_315, LessonTopic.TEST)
)
def test_version_and_testing_topics_progress_through_all_levels(topic: LessonTopic) -> None:
    levels = []
    for number in range(LessonManager.get_total_pages(topic, Locale.EN)):
        page = LessonManager.get_topic_content(topic, number, Locale.EN)
        assert page is not None
        levels.append(page.level)
    order = list(LessonLevel)
    assert set(levels) == set(order)
    assert levels == sorted(levels, key=order.index)
