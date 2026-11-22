"""Native Telegram views and stable lesson references for learning features."""

from collections.abc import Collection, Iterable
from enum import StrEnum
from typing import Final
from unicodedata import category, normalize

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.formatting import escape_html
from bot.i18n import LANGUAGE_NAMES, Locale, tr
from bot.lesson_models import LessonLevel, LessonTopic
from bot.lessons import LessonManager
from bot.study_copy import QUIZZES, localize, study_tr

type View = tuple[str, InlineKeyboardMarkup]
type Location = tuple[LessonTopic, int]
type LessonEntry = tuple[str, LessonTopic, int]

_BOOKMARKS_PER_PAGE = 8
_SEARCH_LIMIT = 10


class CatalogueGroup(StrEnum):
    """Top-level curriculum sections, independent of the display language."""

    PYTHON = "python"
    BACKEND = "backend"
    PRACTICE = "practice"


_GROUPS: Final[dict[CatalogueGroup, tuple[LessonTopic, ...]]] = {
    CatalogueGroup.PYTHON: (
        LessonTopic.BASICS,
        LessonTopic.SYNTAX,
        LessonTopic.PYTHON_314,
        LessonTopic.PYTHON_315,
        LessonTopic.OOP,
        LessonTopic.FILES,
        LessonTopic.ASYNC,
        LessonTopic.INSTALL,
    ),
    CatalogueGroup.BACKEND: (
        LessonTopic.FRAMEWORKS,
        LessonTopic.DJANGO,
        LessonTopic.FASTAPI,
        LessonTopic.DRF,
        LessonTopic.PYDANTIC,
    ),
    CatalogueGroup.PRACTICE: (
        LessonTopic.TEST,
        LessonTopic.TOOLS,
        LessonTopic.DATASCIENCE,
    ),
}

# Each slug is an immutable storage key. Update the lookup title when renaming a
# lesson, but keep its existing slug. Matching titles rather than offsets lets
# stored progress survive reordering lessons and switching languages.
_SLUGS: Final[dict[LessonTopic, dict[str, str]]] = {
    LessonTopic.BASICS: {
        "Introduction to Python": "intro",
        "Control flow and functions": "control-flow",
        "Calculate a receipt": "receipt",
        "Group expenses": "expenses",
        "A shipping fee function": "shipping",
    },
    LessonTopic.OOP: {
        "OOP basics": "intro",
        "A ticket as a value object": "value-object",
        "A factory returning Self": "self-factory",
        "Composition and Protocol": "composition",
    },
    LessonTopic.FILES: {
        "Reading and writing files": "intro",
        "Handle text with pathlib": "pathlib",
        "Stream a CSV report": "csv-stream",
        "Replace a JSON file atomically": "atomic-json",
    },
    LessonTopic.TOOLS: {
        "pip: the package installer": "pip",
        "Git: version control": "git",
        "Reproducible environments with uv": "uv",
        "Linting, formatting, and tests": "lint-and-tests",
        "One verification command for development and CI": "ci-command",
    },
    LessonTopic.FRAMEWORKS: {
        "Flask: a microframework": "flask",
        "Django: a full-featured framework": "django",
        "Application logic outside HTTP": "domain-logic",
        "Test the HTTP contract": "http-contract",
    },
    LessonTopic.DATASCIENCE: {
        "NumPy and pandas": "numpy-pandas",
        "Machine learning": "machine-learning",
        "Checking a schema when reading CSV": "csv-schema",
        "Vectorized computations and missing data with NumPy": "missing-data",
        "Evaluating a model without data leakage": "leakage",
    },
    LessonTopic.SYNTAX: {
        "Modern syntax": "intro",
        "Match a request shape": "match",
        "A generic first item": "generics",
        "Narrow types with TypeIs": "typeis",
    },
    LessonTopic.ASYNC: {
        "async/await": "intro",
        "Concurrent waiting with TaskGroup": "taskgroup",
        "A queue with bounded capacity": "bounded-queue",
        "Deadlines, cancellation, and exception groups": "cancellation",
    },
    LessonTopic.TEST: {
        "Your first automated tests": "intro",
        "Parameters and fixtures": "fixtures",
        "A contract and its failure path": "contract",
    },
    LessonTopic.INSTALL: {
        "Windows": "windows",
        "Linux and macOS": "linux-macos",
        "Check the Python version and build": "interpreter",
        "An isolated project environment": "venv",
    },
    LessonTopic.DJANGO: {
        "First project and HTTP route": "routes",
        "Models, migrations and admin": "models",
        "Forms, templates and access": "forms",
        "ORM queries and the N+1 problem": "n-plus-one",
        "Transactions and concurrent updates": "transactions",
        "Testing HTTP, permissions and stock": "tests",
        "ASGI and deployment": "asgi",
        "Version map and upgrade practice": "upgrade",
        "Django 6.0\N{EN DASH}6.1 lab: tasks and ORM": "latest",
    },
    LessonTopic.FASTAPI: {
        "Routes and parameter validation": "routes",
        "Request bodies, responses and tests": "responses",
        "Routers and dependencies": "routers",
        "Lifespan and asynchronous HTTP": "lifespan",
        "Service authentication": "auth",
        "Uniqueness and transactions": "transactions",
        "Testing with dependency overrides": "tests",
    },
    LessonTopic.DRF: {
        "Serializers and APIView": "serializers",
        "ViewSets, routers and permissions": "viewsets",
        "Writable resources and owner isolation": "ownership",
        "Pagination and search": "pagination",
        "Browser sessions and CSRF": "csrf",
        "Atomic inventory writes": "transactions",
        "Testing permissions and API boundaries": "tests",
    },
    LessonTopic.PYDANTIC: {
        "Strict fields and a validator": "strict",
        "Cross-field validation and JSON": "cross-fields",
        "Nested models and object lists": "nested",
        "Event models with discriminators": "discriminators",
        "Secrets, public models, and diagnostics": "secrets",
    },
    LessonTopic.PYTHON_314: {
        "Check your interpreter": "interpreter",
        "Template strings": "tstrings",
        "Deferred annotations": "annotations",
        "Zstandard compression": "zstd",
        "Isolated interpreters": "interpreters",
    },
    LessonTopic.PYTHON_315: {
        "Python 3.15 and UTF-8": "utf8",
        "Unpacking in comprehensions": "unpacking",
        "Settings with frozendict": "frozendict",
        "Missing values": "missing-values",
        "Lazy imports": "lazy-imports",
        "Profiling on 3.15": "profiling",
    },
}


def _index_lessons() -> dict[str, Location]:
    entries: dict[str, Location] = {}
    for topic, slugs in _SLUGS.items():
        for index in range(LessonManager.get_total_pages(topic, "en")):
            page = LessonManager.get_topic_content(topic, index, "en")
            if page is not None and (slug := slugs.get(page.title)):
                entries[f"{topic.value}.{slug}"] = (topic, index)
    return entries


_INDEX = _index_lessons()
_IDS = {location: slug for slug, location in _INDEX.items()}


def lesson_id(topic: LessonTopic, page: int) -> str | None:
    """Resolve legacy topic and index coordinates to a stable curriculum ID."""
    return _IDS.get((topic, page))


def lesson_location(key: str) -> Location | None:
    """Find current topic and page coordinates for a stable curriculum ID."""
    return _INDEX.get(key)


def _group_for(topic: LessonTopic) -> CatalogueGroup | None:
    return next((group for group, topics in _GROUPS.items() if topic in topics), None)


def _matches_level(
    topic: LessonTopic, index: int, locale: Locale, level: LessonLevel | None
) -> bool:
    page = LessonManager.get_topic_content(topic, index, locale)
    return page is not None and (level is None or page.level == level)


def _entries(
    topics: Iterable[LessonTopic], locale: Locale, level: LessonLevel | None
) -> list[LessonEntry]:
    return [
        (key, topic, index)
        for topic in topics
        for index in range(LessonManager.get_total_pages(topic, locale))
        if (key := lesson_id(topic, index)) and _matches_level(topic, index, locale, level)
    ]


def _open_button(key: str, text: str, *, primary: bool = False) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=f"study:open:{key}",
        style="primary" if primary else None,
    )


def _label(entry: LessonEntry, locale: Locale) -> str:
    _, topic, index = entry
    page = LessonManager.get_topic_content(topic, index, locale)
    return page.title if page else LessonManager.get_topic_title(topic, locale)


def _list_button(builder: InlineKeyboardBuilder, entry: LessonEntry, locale: Locale) -> None:
    builder.add(_open_button(entry[0], _label(entry, locale)))


def _home_button(builder: InlineKeyboardBuilder, locale: Locale) -> None:
    builder.button(text=study_tr(locale, "dashboard"), callback_data="dashboard:home")


def _catalog_button(builder: InlineKeyboardBuilder, locale: Locale) -> None:
    builder.button(text=study_tr(locale, "catalog"), callback_data="study:catalog")


def _level_label(locale: Locale, level: LessonLevel | None) -> str:
    return study_tr(locale, "level_all") if level is None else tr(locale, f"level_{level.value}")


def dashboard_view(locale: Locale, resume: str | None = None) -> View:
    """Show the next useful action and the learner's last visited lesson."""
    builder = InlineKeyboardBuilder()
    location = lesson_location(resume) if resume else None
    if location is not None and resume is not None:
        topic, index = location
        title = escape_html(LessonManager.get_topic_title(topic, locale))
        page = escape_html(_label((resume, topic, index), locale))
        position = study_tr(locale, "resume_position").format(
            page=index + 1, total=LessonManager.get_total_pages(topic, locale)
        )
        text = f"<b>Python Mentor Bot</b>\n\n<b>{title}</b>\n{page}\n{position}"
        builder.add(_open_button(resume, study_tr(locale, "resume"), primary=True))
    else:
        text = study_tr(locale, "welcome")
        first = lesson_id(LessonTopic.BASICS, 0)
        if first is not None:
            builder.add(_open_button(first, study_tr(locale, "get_started"), primary=True))

    for key, target in (
        ("catalog", "study:catalog"),
        ("bookmarks", "study:bookmarks"),
        ("progress", "study:progress"),
        ("settings", "study:settings"),
    ):
        builder.button(text=study_tr(locale, key), callback_data=target)
    for key in ("examples", "ask", "install"):
        builder.button(text=tr(locale, key), callback_data=f"dashboard:{key}")
    builder.adjust(1, 2, 2, 2, 1)
    return text, builder.as_markup()


def settings_view(locale: Locale, level: LessonLevel | None, compact: bool) -> View:
    """Present the saved language, difficulty preference and reading mode."""
    builder = InlineKeyboardBuilder()
    lang_label = f"{study_tr(locale, 'language')} · {LANGUAGE_NAMES[locale]}"
    builder.button(text=lang_label, callback_data="languages")
    for option in (None, *LessonLevel):
        marker = "✓ " if level == option else ""
        builder.button(
            text=f"{marker}{_level_label(locale, option)}",
            callback_data=f"study:level:{option.value if option is not None else 'all'}",
            style="success" if level == option else None,
        )
    builder.button(
        text=study_tr(locale, "compact_on" if compact else "compact_off"),
        callback_data=f"study:compact:{int(not compact)}",
        style="success" if compact else None,
    )
    _home_button(builder, locale)
    builder.adjust(1)
    title = study_tr(locale, "settings")
    return f"<b>{title}</b>\n\n{study_tr(locale, 'settings_intro')}", builder.as_markup()


def catalog_view(
    locale: Locale, group: str | None = None, level: LessonLevel | None = None
) -> View:
    """Show curriculum groups or matching topics in one group."""
    builder = InlineKeyboardBuilder()
    if group in CatalogueGroup:
        selected = CatalogueGroup(group)
        name = study_tr(locale, f"group_{selected.value}")
        text = f"<b>{name}</b>\n\n{_level_label(locale, level)}"
        for topic in _GROUPS[selected]:
            if _entries((topic,), locale, level):
                builder.button(
                    text=LessonManager.get_topic_title(topic, locale),
                    callback_data=f"study:contents:{topic.value}",
                )
        _catalog_button(builder, locale)
    else:
        text = f"{study_tr(locale, 'catalog_intro')}\n\n{_level_label(locale, level)}"
        for item in CatalogueGroup:
            builder.button(
                text=study_tr(locale, f"group_{item.value}"),
                callback_data=f"study:catalog:{item.value}",
            )
        builder.button(text=study_tr(locale, "search"), callback_data="study:search")
    _home_button(builder, locale)
    builder.adjust(1)
    return text, builder.as_markup()


def contents_view(locale: Locale, topic: LessonTopic, level: LessonLevel | None = None) -> View:
    """List a topic's chapters using their localized titles and current position."""
    builder = InlineKeyboardBuilder()
    title = escape_html(LessonManager.get_topic_title(topic, locale) or topic.value)
    text = f"<b>{title}</b>\n{study_tr(locale, 'contents')} · {_level_label(locale, level)}"
    entries = _entries((topic,), locale, level)
    for entry in entries:
        builder.add(_open_button(entry[0], f"{entry[2] + 1}. {_label(entry, locale)}"))
    if not entries:
        text += f"\n\n{study_tr(locale, 'empty_group')}"
    group = _group_for(topic)
    if group is not None:
        builder.button(
            text=study_tr(locale, f"group_{group.value}"),
            callback_data=f"study:catalog:{group.value}",
        )
    _catalog_button(builder, locale)
    _home_button(builder, locale)
    builder.adjust(1)
    return text, builder.as_markup()


def _search_key(value: str) -> str:
    return "".join(char for char in normalize("NFKD", value.casefold()) if category(char) != "Mn")


def search_view(locale: Locale, query: str, level: LessonLevel | None = None) -> View:
    """Find localized lesson and topic titles, preferring direct lesson matches."""
    builder = InlineKeyboardBuilder()
    display = " ".join(query.split())[:100]
    words = _search_key(display).split()
    matches: list[tuple[bool, LessonEntry]] = []
    if words:
        for entry in _entries(LessonTopic, locale, level):
            title = _search_key(_label(entry, locale))
            topic = _search_key(LessonManager.get_topic_title(entry[1], locale))
            if all(word in title or word in topic for word in words):
                matches.append((all(word in title for word in words), entry))
    matches.sort(key=lambda match: not match[0])

    text = f"<b>{study_tr(locale, 'search')}</b>"
    if display:
        text += f"\n«{escape_html(display)}»"
    if matches:
        text += f"\n\n{study_tr(locale, 'search_matches').format(count=len(matches))}"
        for _, entry in matches[:_SEARCH_LIMIT]:
            _list_button(builder, entry, locale)
        if len(matches) > _SEARCH_LIMIT:
            text += f"\n{study_tr(locale, 'search_more').format(shown=_SEARCH_LIMIT)}"
    else:
        text += f"\n\n{study_tr(locale, 'nothing_found')}"
    builder.button(text=study_tr(locale, "search"), callback_data="study:search")
    _catalog_button(builder, locale)
    _home_button(builder, locale)
    builder.adjust(1)
    return text, builder.as_markup()


def _completion(locale: Locale, completed: int, total: int) -> str:
    percent = completed * 100 // total if total else 0
    return study_tr(locale, "completion").format(done=completed, total=total, percent=percent)


def progress_view(locale: Locale, completed: Collection[str], resume: str | None = None) -> View:
    """Summarize explicitly completed lessons across the current catalogue."""
    builder = InlineKeyboardBuilder()
    active = _INDEX.keys() & completed
    lines = [
        f"<b>{study_tr(locale, 'progress')}</b>",
        "",
        _completion(locale, len(active), len(_INDEX)),
        "",
    ]
    for group, topics in _GROUPS.items():
        keys = {key for key, topic, _ in _entries(topics, locale, None)}
        name = study_tr(locale, f"group_{group.value}")
        lines.append(f"<b>{name}</b> · {_completion(locale, len(active & keys), len(keys))}")
    if resume is not None and lesson_location(resume) is not None:
        builder.add(_open_button(resume, study_tr(locale, "resume"), primary=True))
    _catalog_button(builder, locale)
    _home_button(builder, locale)
    builder.adjust(1)
    return "\n".join(lines), builder.as_markup()


def bookmarks_view(locale: Locale, bookmarks: Collection[str], page: int = 0) -> View:
    """List saved lessons and paginate when there are more than eight."""
    builder = InlineKeyboardBuilder()
    entries = [
        (key, *location)
        for key in dict.fromkeys(bookmarks)
        if (location := lesson_location(key)) is not None
    ]
    text = f"<b>{study_tr(locale, 'bookmarks')}</b>\n\n"
    if entries:
        last_page = (len(entries) - 1) // _BOOKMARKS_PER_PAGE
        page = min(max(page, 0), last_page)
        start = page * _BOOKMARKS_PER_PAGE
        end = min(start + _BOOKMARKS_PER_PAGE, len(entries))
        text += study_tr(locale, "page_range").format(first=start + 1, last=end, total=len(entries))
        for entry in entries[start:end]:
            _list_button(builder, entry, locale)
        if page > 0:
            builder.button(text=tr(locale, "back"), callback_data=f"study:bookmarks:{page - 1}")
        if page < last_page:
            builder.button(text=tr(locale, "next"), callback_data=f"study:bookmarks:{page + 1}")
    else:
        text += study_tr(locale, "no_bookmarks")
    _home_button(builder, locale)
    builder.adjust(1)
    return text, builder.as_markup()


def lesson_actions(
    locale: Locale,
    lesson_id: str,
    bookmark: bool = False,
    completed: bool = False,
) -> tuple[InlineKeyboardButton, ...]:
    """Build personal lesson actions that are safe to retry."""
    location = lesson_location(lesson_id)
    if location is None:
        return ()
    topic, _ = location
    buttons = [
        InlineKeyboardButton(
            text=study_tr(locale, "completed" if completed else "mark_complete"),
            callback_data=f"study:complete:{lesson_id}",
            style="success" if completed else None,
        ),
        InlineKeyboardButton(
            text=study_tr(locale, "bookmark_remove" if bookmark else "bookmark_add"),
            callback_data=f"study:bookmark:{lesson_id}:{int(not bookmark)}",
        ),
        InlineKeyboardButton(
            text=study_tr(locale, "contents"),
            callback_data=f"study:contents:{topic.value}",
        ),
    ]
    if lesson_id in QUIZZES:
        buttons.append(
            InlineKeyboardButton(
                text=study_tr(locale, "quiz"),
                callback_data=f"study:quiz:{lesson_id}",
            )
        )
    return tuple(buttons)


def quiz_view(locale: Locale, lesson_id: str, answer: int | None = None) -> View | None:
    """Show a question or localized feedback on the chosen answer."""
    quiz = QUIZZES.get(lesson_id)
    if quiz is None or (answer is not None and not 0 <= answer < len(quiz.options)):
        return None

    builder = InlineKeyboardBuilder()
    heading = study_tr(locale, "quiz")
    question = escape_html(localize(locale, quiz.question))
    text = f"<b>{heading}</b>\n\n{question}"
    if answer is None:
        for index, option in enumerate(quiz.options):
            builder.button(
                text=localize(locale, option),
                callback_data=f"study:quiz:{lesson_id}:{index}",
            )
    else:
        outcome = study_tr(locale, "quiz_right" if answer == quiz.correct else "quiz_wrong")
        explanation = escape_html(localize(locale, quiz.explanation))
        text += f"\n\n<b>{outcome}</b>\n{explanation}"
        if answer != quiz.correct:
            builder.button(
                text=study_tr(locale, "quiz_retry"),
                callback_data=f"study:quiz:{lesson_id}",
            )
    builder.add(_open_button(lesson_id, study_tr(locale, "lesson")))
    builder.adjust(1)
    return text, builder.as_markup()
