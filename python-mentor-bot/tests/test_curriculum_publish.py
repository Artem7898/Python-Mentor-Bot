"""Guard the bundled lesson catalog against publishing incomplete translations or examples."""

import sys

import pytest

from bot.i18n import Locale
from bot.lessons import LessonManager, LessonTopic


@pytest.mark.parametrize("topic", tuple(LessonTopic))
def test_published_pages_have_localized_prose_and_consistent_examples(topic: LessonTopic) -> None:
    for index in range(LessonManager.get_total_pages(topic)):
        explanations: set[str] = set()
        steps: set[int] = set()
        examples: set[str | None] = set()

        for locale in Locale:
            page = LessonManager.get_topic_content(topic, index, locale)
            assert page is not None, (topic, index, locale)
            assert page.title.strip() and page.explanation.strip(), (topic, index, locale)
            assert all(step.strip() for step in page.steps), (topic, index, locale)
            if page.example_code is not None:
                assert page.example_code.strip(), (topic, index, locale)
            explanations.add(page.explanation.strip())
            steps.add(len(page.steps))
            examples.add(page.example_code)

        assert len(explanations) == len(Locale), (topic, index)
        assert len(steps) == 1 and len(examples) == 1, (topic, index)


@pytest.mark.parametrize(
    ("topic", "minimum"),
    [
        (LessonTopic.PYTHON_314, (3, 14)),
        (LessonTopic.PYTHON_315, (3, 15)),
        (LessonTopic.TEST, (3, 14)),
    ],
)
def test_python_and_testing_examples_compile(topic: LessonTopic, minimum: tuple[int, int]) -> None:
    if sys.version_info < minimum:
        pytest.skip(
            f"Compile the {topic.value} examples in the Python {minimum[0]}.{minimum[1]} job"
        )

    for index in range(LessonManager.get_total_pages(topic, Locale.EN)):
        page = LessonManager.get_topic_content(topic, index, Locale.EN)
        assert page is not None and page.example_code, (topic, index)
        compile(page.example_code, f"<{topic.value} page {index + 1}>", "exec")
