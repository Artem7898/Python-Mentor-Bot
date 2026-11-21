"""Typed lesson catalogue records."""

from dataclasses import dataclass
from enum import StrEnum


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
    steps: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Lesson:
    """Topic title and ordered pages for one locale."""

    title: str
    pages: tuple[LessonPage, ...]
