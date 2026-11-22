import pytest

from bot.lessons import LessonManager, LessonTopic


@pytest.mark.parametrize("topic", tuple(LessonTopic))
def test_page_lookup_rejects_negative_and_out_of_range_pages(topic: LessonTopic) -> None:
    total = LessonManager.get_total_pages(topic)

    assert LessonManager.get_topic_content(topic, -1) is None
    assert LessonManager.get_topic_content(topic, total) is None
    for page in range(total):
        assert LessonManager.get_topic_content(topic, page) is not None


def test_framework_page_retains_platform_specific_installation() -> None:
    page = LessonManager.get_topic_content(LessonTopic.FRAMEWORKS)

    assert page is not None
    assert page.windows_install and "venv\\Scripts\\activate" in page.windows_install
    assert page.linux_install and "source venv/bin/activate" in page.linux_install


@pytest.mark.parametrize("topic", tuple(LessonTopic))
def test_every_lesson_has_translated_pages(topic: LessonTopic) -> None:
    page_count = LessonManager.get_total_pages(topic)
    assert page_count > 0
    for index in range(page_count):
        pages = tuple(
            LessonManager.get_topic_content(topic, index, language)
            for language in ("ru", "en", "es")
        )
        assert all(page is not None for page in pages)
        translated = [page for page in pages if page is not None]
        assert len({page.explanation for page in translated}) == 3
        assert len({page.example_code for page in translated}) == 1


def test_unknown_language_uses_russian_catalogue() -> None:
    assert LessonManager.get_topic_content(
        LessonTopic.PYDANTIC, language="unknown"
    ) == LessonManager.get_topic_content(LessonTopic.PYDANTIC)
