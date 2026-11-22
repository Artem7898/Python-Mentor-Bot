"""Typed lesson catalogue records."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

type LocalizedText = tuple[str, str, str]

LESSON_LANGUAGES: Final = ("ru", "en", "es")


class LessonTopic(StrEnum):
    """Стабильные идентификаторы тем в SQLite и кнопках Telegram."""

    BASICS = "basics"
    OOP = "oop"
    FILES = "files"
    TOOLS = "tools"
    FRAMEWORKS = "frameworks"
    DATASCIENCE = "datascience"
    SYNTAX = "syntax"
    ASYNC = "async"
    TEST = "test"
    INSTALL = "install"
    DJANGO = "django"
    FASTAPI = "fastapi"
    DRF = "drf"
    PYDANTIC = "pydantic"
    PYTHON_314 = "python314"
    PYTHON_315 = "python315"


class LessonLevel(StrEnum):
    """Difficulty of a curriculum page."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    PROFESSIONAL = "professional"


@dataclass(frozen=True, slots=True, kw_only=True)
class LessonPage:
    """Страница урока, содержащая пояснение и необязательные примеры."""

    title: str
    explanation: str
    windows_code: str | None = None
    linux_code: str | None = None
    windows_install: str | None = None
    linux_install: str | None = None
    install_code: str | None = None
    example_code: str | None = None
    example_language: str = "python"
    steps: tuple[str, ...] = ()
    level: LessonLevel = LessonLevel.BEGINNER


@dataclass(frozen=True, slots=True)
class Lesson:
    """Topic title and ordered pages for one locale."""

    title: str
    pages: tuple[LessonPage, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalizedPage:
    """Author lesson copy in Russian, English and Spanish with a shared example."""

    title: LocalizedText
    explanation: LocalizedText
    example_code: str | None = None
    example_language: str = "python"
    install_code: str | None = None
    steps: tuple[LocalizedText, ...] = ()
    level: LessonLevel = LessonLevel.BEGINNER

    def localize(self, index: int) -> LessonPage:
        """Build the page for one supported locale."""
        return LessonPage(
            title=self.title[index],
            explanation=self.explanation[index],
            install_code=self.install_code,
            example_code=self.example_code,
            example_language=self.example_language,
            steps=tuple(step[index] for step in self.steps),
            level=self.level,
        )


def localize_pages(*pages: LocalizedPage) -> dict[str, tuple[LessonPage, ...]]:
    """Build equivalent page sequences for every language."""
    return {
        language: tuple(page.localize(index) for page in pages)
        for index, language in enumerate(LESSON_LANGUAGES)
    }


def localize_lesson(title: LocalizedText, *pages: LocalizedPage) -> dict[str, Lesson]:
    """Build one titled lesson sequence per language."""
    localized = localize_pages(*pages)
    return {
        language: Lesson(title[index], localized[language])
        for index, language in enumerate(LESSON_LANGUAGES)
    }
