"""Telegram dashboard, lesson navigation and localized conversation handlers."""

import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from aiogram import BaseMiddleware, Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, CommandStart, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp_socks import ProxyConnectionError, ProxyError, ProxyTimeoutError

from bot.access import ChatEvent, Roles, has_private_chat, telegram_user
from bot.billing import register_billing_routes
from bot.evaluator import EvaluationError, evaluate_expression
from bot.formatting import escape_html, format_code
from bot.i18n import COMMANDS, LANGUAGE_NAMES, Locale, resolve_locale, tr
from bot.lesson_models import LessonLevel
from bot.lessons import LessonManager, LessonPage, LessonTopic
from bot.personal import ask_question, register_personal_routes
from bot.presentation import is_accessible, present, require_private
from bot.pro_workflows import register_pro_replies, register_pro_routes
from bot.storage import DatabaseManager, LearnerPreferences, StorageError
from bot.study_copy import study_tr
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

logger = logging.getLogger(__name__)

_TOPICS = (
    LessonTopic.BASICS,
    LessonTopic.SYNTAX,
    LessonTopic.PYTHON_314,
    LessonTopic.PYTHON_315,
    LessonTopic.OOP,
    LessonTopic.FILES,
    LessonTopic.FRAMEWORKS,
    LessonTopic.DJANGO,
    LessonTopic.FASTAPI,
    LessonTopic.DRF,
    LessonTopic.PYDANTIC,
    LessonTopic.TOOLS,
    LessonTopic.DATASCIENCE,
    LessonTopic.ASYNC,
    LessonTopic.TEST,
)
_LEGACY_ACTIONS = {
    "📚 Темы обучения": "topics",
    "💻 Пример кода": "examples",
    "❓ Задать вопрос": "ask",
    "📊 Мой прогресс": "progress",
    "📥 Установка Python": "install",
}


class Conversation(StatesGroup):
    """State for questions that need a follow-up message."""

    search = State()


class LocaleMiddleware(BaseMiddleware):
    """Resolve the user's explicit preference ahead of their Telegram locale."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and (event.successful_payment or event.refunded_payment):
            data["locale"] = resolve_locale(
                event.from_user.language_code if event.from_user else None
            )
            return await handler(event, data)
        sender = telegram_user(event) if isinstance(event, (Message, CallbackQuery)) else None
        db: DatabaseManager = data["db"]
        chosen = (
            await db.get_language(sender.id)
            if sender and isinstance(event, (Message, CallbackQuery)) and has_private_chat(event)
            else None
        )
        data["locale"] = resolve_locale(chosen or (sender.language_code if sender else None))
        return await handler(event, data)


@dataclass(frozen=True, slots=True)
class LessonSelection:
    """A validated callback pointing to a single lesson page."""

    topic: LessonTopic
    page: int
    view: Literal["lesson", "code"]


def parse_selection(data: str, locale: Locale = Locale.RU) -> LessonSelection | None:
    """Accept current and legacy callback payloads with an existing page."""
    parts = data.split(":")
    if len(parts) not in (2, 3):
        return None
    action, raw_topic, *pages = parts
    if action not in {"topic", "page", "code"} or (action == "page" and not pages):
        return None

    try:
        topic = LessonTopic(raw_topic)
    except ValueError:
        return None

    raw_page = pages[0] if pages else "0"
    if len(raw_page) > 3 or not raw_page.isascii() or not raw_page.isdecimal():
        return None
    page = int(raw_page)
    if page >= LessonManager.get_total_pages(topic, locale):
        return None
    return LessonSelection(topic, page, "code" if action == "code" else "lesson")


def language_keyboard(locale: Locale) -> InlineKeyboardMarkup:
    """Show the three languages in their own names."""
    builder = InlineKeyboardBuilder()
    for option, name in LANGUAGE_NAMES.items():
        builder.button(
            text=f"✓ {name}" if option == locale else name,
            callback_data=f"lang:{option}",
            style="success" if option == locale else None,
        )
    builder.button(text=tr(locale, "dashboard"), callback_data="dashboard:home")
    builder.adjust(1)
    return builder.as_markup()


def _code_sections(page: LessonPage, locale: Locale) -> list[tuple[str, str, str]]:
    sections = (
        ("💻 Windows", page.windows_code, "text"),
        ("🐧 Linux", page.linux_code, "text"),
        (tr(locale, "install_code"), page.install_code, "bash"),
        (tr(locale, "windows_install"), page.windows_install, "bash"),
        (tr(locale, "linux_install"), page.linux_install, "bash"),
        (tr(locale, "example"), page.example_code, page.example_language),
    )
    return [(title, code, language) for title, code, language in sections if code]


def _example_pages(topic: LessonTopic, locale: Locale) -> list[int]:
    return [
        index
        for index in range(LessonManager.get_total_pages(topic, locale))
        if (page := LessonManager.get_topic_content(topic, index, locale))
        and _code_sections(page, locale)
    ]


def topics_keyboard(locale: Locale, *, examples: bool = False) -> InlineKeyboardMarkup:
    """List localized topics or the topics with code examples."""
    builder = InlineKeyboardBuilder()
    for topic in _TOPICS:
        if examples:
            pages = _example_pages(topic, locale)
            if not pages:
                continue
            target = f"code:{topic.value}:{pages[0]}"
        else:
            target = f"topic:{topic.value}"
        builder.button(text=LessonManager.get_topic_title(topic, locale), callback_data=target)
    builder.button(text=tr(locale, "back"), callback_data="dashboard:home")
    builder.adjust(2)
    return builder.as_markup()


def lesson_keyboard(
    selection: LessonSelection, page: LessonPage, locale: Locale
) -> InlineKeyboardMarkup:
    """Build previous and next controls using the current lesson language."""
    topic, current = selection.topic, selection.page
    builder = InlineKeyboardBuilder()
    if selection.view == "code":
        pages = _example_pages(topic, locale)
        index = pages.index(current)
        if index > 0:
            builder.button(
                text=tr(locale, "back"), callback_data=f"code:{topic.value}:{pages[index - 1]}"
            )
        if index + 1 < len(pages):
            builder.button(
                text=tr(locale, "next"), callback_data=f"code:{topic.value}:{pages[index + 1]}"
            )
        builder.button(
            text=tr(locale, "full_lesson"), callback_data=f"topic:{topic.value}:{current}"
        )
    else:
        count = LessonManager.get_total_pages(topic, locale)
        if current > 0:
            builder.button(
                text=tr(locale, "back"), callback_data=f"page:{topic.value}:{current - 1}"
            )
        builder.button(text=f"{current + 1}/{count}", callback_data="current_page")
        if current + 1 < count:
            builder.button(
                text=tr(locale, "next"), callback_data=f"page:{topic.value}:{current + 1}"
            )
        if _code_sections(page, locale):
            builder.button(
                text=tr(locale, "example"), callback_data=f"code:{topic.value}:{current}"
            )
    builder.button(text=tr(locale, "topics"), callback_data="dashboard:topics")
    builder.button(text=tr(locale, "dashboard"), callback_data="dashboard:home")
    builder.adjust(3, 2, 1)
    return builder.as_markup()


def lesson_text(
    selection: LessonSelection,
    page: LessonPage,
    locale: Locale = Locale.RU,
    *,
    compact: bool = False,
) -> str:
    """Render the selected page as escaped Telegram HTML."""
    title = escape_html(page.title)
    if selection.view == "code":
        body = [f"<b>{tr(locale, 'example')}: {title}</b>"]
    else:
        topic_title = escape_html(LessonManager.get_topic_title(selection.topic, locale))
        explanation = escape_html(page.explanation)
        # Preserve authored bold headings in the bundled catalogue.
        explanation = explanation.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        level = tr(locale, f"level_{page.level}")
        body = [f"<b>{topic_title}</b>\n{level}", f"<b>{title}</b>", explanation]
        if page.steps:
            body.append("\n".join(f"• {escape_html(step)}" for step in page.steps))

    sections = _code_sections(page, locale)
    if compact and selection.view == "lesson":
        if sections:
            body.append(study_tr(locale, "compact_hint"))
    else:
        for label, code, language in sections:
            body.append(f"<b>{label}:</b>\n{format_code(code, language)}")

    return "\n\n".join(body)


async def _preferences(event: ChatEvent, db: DatabaseManager) -> LearnerPreferences:
    sender = telegram_user(event)
    if sender and has_private_chat(event):
        return await db.get_preferences(sender.id)
    return LearnerPreferences()


async def _resume(db: DatabaseManager, user_id: int) -> str | None:
    stable = await db.get_last_lesson(user_id)
    if stable and lesson_location(stable):
        return stable
    previous = await db.get_user(user_id)
    if previous and (previous.current_topic != LessonTopic.BASICS or previous.current_page != 0):
        return lesson_id(previous.current_topic, previous.current_page)
    return None


async def _dashboard(event: ChatEvent, db: DatabaseManager, locale: Locale) -> None:
    sender = telegram_user(event)
    resume = await _resume(db, sender.id) if sender and has_private_chat(event) else None
    text, markup = dashboard_view(locale, resume)
    if has_private_chat(event):
        markup.inline_keyboard.append(
            [InlineKeyboardButton(text=tr(locale, "pro_cmd"), callback_data="pro:home")]
        )
    await present(event, text, markup)


async def start(message: Message, state: FSMContext, db: DatabaseManager, locale: Locale) -> None:
    """Start the course and show a public or personalized dashboard."""
    sender = telegram_user(message)
    if sender and has_private_chat(message):
        await db.get_or_create_user(sender.id, sender.username)
    await state.clear()
    await _dashboard(message, db, locale)


async def help_command(message: Message, locale: Locale, roles: Roles) -> None:
    """Show localized command descriptions without changing the dialogue state."""
    commands = list(COMMANDS)
    sender = telegram_user(message)
    if sender and has_private_chat(message):
        if roles.can_mentor(sender.id):
            commands.append(("mentor", "mentor_cmd"))
        if roles.can_edit(sender.id):
            commands.append(("editor", "editor_cmd"))
    lines = (f"/{command} — {tr(locale, key)}" for command, key in commands)
    await message.answer("\n".join((f"<b>{tr(locale, 'help_title')}</b>", *lines)))


async def cancel(message: Message, state: FSMContext, locale: Locale, db: DatabaseManager) -> None:
    """Cancel a private conversation and return to the dashboard."""
    await state.clear()
    await message.answer(tr(locale, "cancelled"))
    await _dashboard(message, db, locale)


async def run_expression(message: Message, command: CommandObject, locale: Locale) -> None:
    """Evaluate a bounded arithmetic expression."""
    if not command.args:
        await message.answer(tr(locale, "run_prompt"))
        return
    try:
        result = evaluate_expression(command.args)
    except EvaluationError as exc:
        await message.answer(
            escape_html(str(exc)) if locale == Locale.RU else tr(locale, "run_invalid")
        )
        return
    await message.answer(f"<b>{tr(locale, 'result')}:</b> <code>{result}</code>")


async def _progress(event: ChatEvent, db: DatabaseManager, locale: Locale, bot: Bot) -> None:
    if not await require_private(event, locale, bot):
        return
    sender = telegram_user(event)
    if not sender:
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    done = await db.list_completed_lessons(sender.id)
    await present(event, *progress_view(locale, done, await _resume(db, sender.id)))


async def _show_dashboard_action(
    event: ChatEvent, action: str, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    if action == "ask":
        await ask_question(event, state, locale, bot)
        return
    if action == "progress":
        await _progress(event, db, locale, bot)
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    match action:
        case "topics":
            prefs = await _preferences(event, db)
            await present(event, *catalog_view(locale, level=prefs.level))
        case "examples":
            await present(
                event, tr(locale, "choose_example"), topics_keyboard(locale, examples=True)
            )
        case "install":
            await _show_lesson(event, LessonSelection(LessonTopic.INSTALL, 0, "lesson"), db, locale)
        case _:
            await _dashboard(event, db, locale)


async def legacy_action(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Accept previously issued Telegram reply-keyboard buttons."""
    await _show_dashboard_action(
        message, _LEGACY_ACTIONS[message.text or ""], state, db, locale, bot
    )


async def dashboard_action(
    callback: CallbackQuery, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Navigate an existing dashboard, including links from older menus."""
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    data = callback.data or ""
    action = {"show_topics": "topics", "back_to_main": "home"}.get(
        data, data.removeprefix("dashboard:")
    )
    await _show_dashboard_action(callback, action, state, db, locale, bot)


async def show_languages(event: ChatEvent, locale: Locale, bot: Bot) -> None:
    """Open the language picker via its button or /language."""
    if not await require_private(event, locale, bot):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    await present(event, tr(locale, "picker"), language_keyboard(locale))


async def choose_language(
    callback: CallbackQuery, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Persist the language for the person who pressed the button in private."""
    if not await require_private(callback, locale, bot):
        return
    try:
        selected = Locale((callback.data or "").removeprefix("lang:"))
    except ValueError:
        await callback.answer(tr(locale, "unsupported"))
        return
    sender = telegram_user(callback)
    if sender is None:
        return
    await db.get_or_create_user(sender.id, sender.username)
    await db.set_language(sender.id, selected.value)
    await callback.answer(tr(selected, "saved"))
    await _dashboard(callback, db, selected)


async def _show_lesson(
    event: ChatEvent,
    selection: LessonSelection,
    db: DatabaseManager,
    locale: Locale,
    *,
    record: bool = True,
) -> bool:
    page = LessonManager.get_topic_content(selection.topic, selection.page, locale)
    if page is None or (selection.view == "code" and not _code_sections(page, locale)):
        return False
    sender = telegram_user(event)
    prefs = await _preferences(event, db)
    markup = lesson_keyboard(selection, page, locale)
    key = lesson_id(selection.topic, selection.page)
    private = sender is not None and has_private_chat(event)
    if key and sender and private and selection.view == "lesson":
        actions = lesson_actions(
            locale,
            key,
            bookmark=key in await db.list_bookmarks(sender.id),
            completed=key in await db.list_completed_lessons(sender.id),
        )
        markup.inline_keyboard.extend([button] for button in actions)
    await present(event, lesson_text(selection, page, locale, compact=prefs.compact), markup)
    if key and sender and private and selection.view == "lesson" and record:
        await db.get_or_create_user(sender.id, sender.username)
        await db.record_lesson_visit(sender.id, key, selection.topic, selection.page)
    return True


async def select_lesson(callback: CallbackQuery, db: DatabaseManager, locale: Locale) -> None:
    """Accept older lesson buttons without storing activity from groups."""
    selection = parse_selection(callback.data or "", locale)
    if selection is None:
        await callback.answer(tr(locale, "invalid_page"))
        return
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    shown = await _show_lesson(callback, selection, db, locale)
    await callback.answer(None if shown else tr(locale, "invalid_page"))


async def _settings(
    callback: CallbackQuery, action: str, values: Sequence[str], db: DatabaseManager, locale: Locale
) -> bool:
    sender = telegram_user(callback)
    if sender is None:
        return False
    if action == "level" and len(values) == 1 and (values[0] == "all" or values[0] in LessonLevel):
        await db.get_or_create_user(sender.id, sender.username)
        await db.set_level(sender.id, None if values[0] == "all" else LessonLevel(values[0]))
    elif action == "compact" and len(values) == 1 and values[0] in {"0", "1"}:
        await db.get_or_create_user(sender.id, sender.username)
        await db.set_compact(sender.id, values[0] == "1")
    elif action != "settings" or values:
        return False
    prefs = await db.get_preferences(sender.id)
    text, markup = settings_view(locale, prefs.level, prefs.compact)
    personal_menu = InlineKeyboardBuilder()
    personal_menu.button(text=tr(locale, "privacy_cmd"), callback_data="privacy:show")
    personal_menu.button(text=tr(locale, "questions_cmd"), callback_data="study:questions")
    personal_menu.adjust(1)
    markup.inline_keyboard.extend(personal_menu.as_markup().inline_keyboard)
    await present(callback, text, markup)
    return True


async def _lesson_action(
    callback: CallbackQuery, action: str, values: Sequence[str], db: DatabaseManager, locale: Locale
) -> bool:
    if not values or (location := lesson_location(values[0])) is None:
        return False
    key = values[0]
    selection = LessonSelection(*location, "lesson")
    if action == "open" and len(values) == 1:
        return await _show_lesson(callback, selection, db, locale)
    if action == "quiz" and (
        len(values) == 1 or (len(values) == 2 and values[1] in {"0", "1", "2", "3"})
    ):
        rendered = quiz_view(locale, key, int(values[1]) if len(values) == 2 else None)
        if rendered is None:
            return False
        await present(callback, *rendered)
        return True
    sender = telegram_user(callback)
    if sender is None:
        return False
    if action == "complete" and len(values) == 1:
        await db.get_or_create_user(sender.id, sender.username)
        await db.complete_lesson(sender.id, key)
    elif action == "bookmark" and len(values) == 2 and values[1] in {"0", "1"}:
        await db.get_or_create_user(sender.id, sender.username)
        await db.set_bookmark(sender.id, key, bookmarked=values[1] == "1")
    else:
        return False
    return await _show_lesson(callback, selection, db, locale, record=False)


async def study_action(
    callback: CallbackQuery, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Handle the grouped curriculum and private study tools."""
    _, action, *values = (callback.data or "").split(":")
    if action == "progress":
        await _progress(callback, db, locale, bot)
        return
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    public = action in {"open", "catalog", "contents"}
    if not public and not await require_private(callback, locale, bot):
        return
    shown = True
    match action:
        case "settings" | "level" | "compact":
            shown = await _settings(callback, action, values, db, locale)
        case "catalog":
            prefs = await _preferences(callback, db)
            group = values[0] if len(values) == 1 else None
            await present(callback, *catalog_view(locale, group, prefs.level))
        case "contents" if len(values) == 1 and values[0] in LessonTopic:
            prefs = await _preferences(callback, db)
            await present(callback, *contents_view(locale, LessonTopic(values[0]), prefs.level))
        case "search" if not values:
            await state.clear()
            await state.set_state(Conversation.search)
            await present(callback, study_tr(locale, "search_prompt"))
        case "bookmarks":
            sender = telegram_user(callback)
            page = 0
            if (
                len(values) == 1
                and values[0].isascii()
                and values[0].isdigit()
                and len(values[0]) <= 3
            ):
                page = int(values[0])
            saved = await db.list_bookmarks(sender.id) if sender else ()
            await present(callback, *bookmarks_view(locale, saved, page))
        case "open" | "complete" | "bookmark" | "quiz":
            shown = await _lesson_action(callback, action, values, db, locale)
        case _:
            shown = False
    await callback.answer(None if shown else tr(locale, "invalid_page"))


async def search_lessons(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Search translated lesson titles in a private conversation."""
    if not await require_private(message, locale, bot):
        return
    query = (message.text or "").strip()
    if not 2 <= len(query) <= 100:
        await message.answer(study_tr(locale, "search_invalid"))
        return
    prefs = await _preferences(message, db)
    await state.clear()
    await present(message, *search_view(locale, query, prefs.level))


async def current_page(callback: CallbackQuery) -> None:
    """Acknowledge a page-indicator tap."""
    await callback.answer()


async def fallback_text(message: Message, locale: Locale, db: DatabaseManager) -> None:
    """Offer help in private chats without responding to arbitrary group messages."""
    if has_private_chat(message):
        sender = telegram_user(message)
        resume = await _resume(db, sender.id) if sender else None
        await present(message, tr(locale, "fallback"), dashboard_view(locale, resume)[1])


async def report_failure(event: ErrorEvent) -> bool:
    """Report operational errors without exposing request or database details."""
    logger.warning("Update %s failed (%s)", event.update.update_id, type(event.exception).__name__)
    target = event.update.callback_query or event.update.message
    if target is None:
        return True
    sender = telegram_user(target)
    locale = resolve_locale(sender.language_code if sender else None)
    try:
        await target.answer(tr(locale, "failure"))
    except TelegramAPIError, ProxyError, ProxyConnectionError, ProxyTimeoutError:
        logger.warning("Could not notify user about update %s", event.update.update_id)
    return True


def create_router() -> Router:
    """Build a router that prioritizes commands and navigation before free text."""
    router = Router(name="mentor")
    middleware = LocaleMiddleware()
    router.message.middleware(middleware)
    router.callback_query.middleware(middleware)
    router.message.register(start, CommandStart())
    router.message.register(help_command, Command("help"))
    router.message.register(show_languages, Command("language"))
    router.message.register(cancel, Command("cancel"))
    router.message.register(run_expression, Command("run"))
    router.message.register(legacy_action, F.text.in_(set(_LEGACY_ACTIONS)))
    register_billing_routes(router)
    register_pro_routes(router)
    register_personal_routes(router)
    register_pro_replies(router)
    router.message.register(search_lessons, Conversation.search)
    router.message.register(fallback_text, F.text)
    router.callback_query.register(show_languages, F.data == "languages")
    router.callback_query.register(choose_language, F.data.startswith("lang:"))
    router.callback_query.register(select_lesson, F.data.startswith(("topic:", "page:", "code:")))
    router.callback_query.register(dashboard_action, F.data.startswith("dashboard:"))
    router.callback_query.register(dashboard_action, F.data.in_({"show_topics", "back_to_main"}))
    router.callback_query.register(study_action, F.data.startswith("study:"))
    router.callback_query.register(current_page, F.data == "current_page")
    router.error.register(
        report_failure,
        ExceptionTypeFilter(
            StorageError, TelegramAPIError, ProxyError, ProxyConnectionError, ProxyTimeoutError
        ),
    )
    return router
