"""Telegram dashboard, lesson navigation and localized conversation handlers."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeIs

from aiogram import BaseMiddleware, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    InaccessibleMessage,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
    User,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp_socks import ProxyConnectionError, ProxyError, ProxyTimeoutError

from bot.evaluator import EvaluationError, evaluate_expression
from bot.formatting import escape_html, format_code
from bot.i18n import COMMANDS, LANGUAGE_NAMES, Locale, resolve_locale, tr
from bot.lessons import LessonManager, LessonPage, LessonTopic
from bot.storage import DatabaseManager, StorageError

logger = logging.getLogger(__name__)

_TOPICS = (
    LessonTopic.BASICS,
    LessonTopic.SYNTAX,
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

    waiting_question = State()


class LocaleMiddleware(BaseMiddleware):
    """Resolve the user's explicit preference ahead of their Telegram locale."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        sender = event.from_user if isinstance(event, (Message, CallbackQuery)) else None
        db: DatabaseManager = data["db"]
        chosen = await db.get_language(sender.id) if sender else None
        data["locale"] = resolve_locale(chosen or (sender.language_code if sender else None))
        return await handler(event, data)


@dataclass(frozen=True, slots=True)
class LessonSelection:
    """A validated callback pointing to a single lesson page."""

    topic: LessonTopic
    page: int
    view: Literal["lesson", "code"]


def is_accessible(message: Message | InaccessibleMessage | None) -> TypeIs[Message]:
    """Narrow an optional Telegram callback message to an accessible one."""
    return isinstance(message, Message)


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


def dashboard_keyboard(locale: Locale) -> InlineKeyboardMarkup:
    """Build the Telegram dashboard with the lessons action emphasized."""
    builder = InlineKeyboardBuilder()
    builder.button(text=tr(locale, "topics"), callback_data="dashboard:topics", style="primary")
    for action in ("examples", "progress", "ask", "install"):
        builder.button(text=tr(locale, action), callback_data=f"dashboard:{action}")
    builder.button(text=tr(locale, "language"), callback_data="languages")
    builder.adjust(1, 2, 2, 1)
    return builder.as_markup()


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
        ("💻 Windows", page.windows_code, "python"),
        ("🐧 Linux", page.linux_code, "python"),
        (tr(locale, "install_code"), page.install_code, "bash"),
        (tr(locale, "windows_install"), page.windows_install, "bash"),
        (tr(locale, "linux_install"), page.linux_install, "bash"),
        (tr(locale, "example"), page.example_code, "python"),
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


def lesson_text(selection: LessonSelection, page: LessonPage, locale: Locale = Locale.RU) -> str:
    """Render the selected page as escaped Telegram HTML."""
    title = escape_html(page.title)
    if selection.view == "code":
        body = [f"<b>{tr(locale, 'example')}: {title}</b>"]
    else:
        topic_title = escape_html(LessonManager.get_topic_title(selection.topic, locale))
        explanation = escape_html(page.explanation)
        # Preserve authored bold headings in the bundled catalogue.
        explanation = explanation.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        body = [f"<b>{topic_title}</b>", f"<b>{title}</b>", explanation]
        if page.steps:
            body.append("\n".join(f"• {escape_html(step)}" for step in page.steps))

    for label, code, language in _code_sections(page, locale):
        body.append(f"<b>{label}:</b>\n{format_code(code, language)}")

    return "\n\n".join(body)


async def _present(
    event: Message | CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None
) -> None:
    if isinstance(event, Message):
        await event.answer(text, reply_markup=markup)
        return
    message = event.message
    if not is_accessible(message):
        return
    if message.chat.type != "private":
        # Editing a shared dashboard would replace everyone else's language and view.
        await message.answer(text, reply_markup=markup)
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" not in exc.message.casefold():
            raise


async def start(message: Message, state: FSMContext, db: DatabaseManager, locale: Locale) -> None:
    """Register the learner and show their localized dashboard."""
    if message.from_user:
        await db.get_or_create_user(message.from_user.id, message.from_user.username)
    await state.clear()
    await _present(message, tr(locale, "home"), dashboard_keyboard(locale))


async def help_command(message: Message, locale: Locale) -> None:
    """Show localized command descriptions without changing the dialogue state."""
    lines = (f"/{command} — {tr(locale, key)}" for command, key in COMMANDS)
    await message.answer("\n".join((f"<b>{tr(locale, 'help_title')}</b>", *lines)))


async def cancel(message: Message, state: FSMContext, locale: Locale) -> None:
    """Cancel a pending question."""
    await state.clear()
    await _present(message, tr(locale, "cancelled"), dashboard_keyboard(locale))


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


async def _show_dashboard_action(
    event: Message | CallbackQuery,
    action: str,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
) -> None:
    match action:
        case "topics" | "examples":
            examples = action == "examples"
            await _present(
                event,
                tr(locale, "choose_example" if examples else "choose_topic"),
                topics_keyboard(locale, examples=examples),
            )
        case "install":
            selection = LessonSelection(LessonTopic.INSTALL, 0, "lesson")
            page = LessonManager.get_topic_content(selection.topic, selection.page, locale)
            if page is None:
                await _present(event, tr(locale, "invalid_page"))
            else:
                await _present(
                    event,
                    lesson_text(selection, page, locale),
                    lesson_keyboard(selection, page, locale),
                )
        case "ask":
            await _present(event, tr(locale, "ask_prompt"), dashboard_keyboard(locale))
            await state.set_state(Conversation.waiting_question)
        case "progress":
            await _show_progress(event, event.from_user, db, locale)
        case _:
            await _present(event, tr(locale, "home"), dashboard_keyboard(locale))


async def legacy_action(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale
) -> None:
    """Accept previously issued Telegram reply-keyboard buttons."""
    await _show_dashboard_action(message, _LEGACY_ACTIONS[message.text or ""], state, db, locale)


async def dashboard_action(
    callback: CallbackQuery, state: FSMContext, db: DatabaseManager, locale: Locale
) -> None:
    """Navigate an existing dashboard, including links from older menus."""
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    action = {
        "show_topics": "topics",
        "back_to_main": "home",
    }.get(callback.data or "", (callback.data or "").removeprefix("dashboard:"))
    await callback.answer()
    await _show_dashboard_action(callback, action, state, db, locale)


async def show_languages(event: Message | CallbackQuery, locale: Locale) -> None:
    """Open the language picker via its button or /language."""
    if isinstance(event, CallbackQuery):
        if not is_accessible(event.message):
            await event.answer(tr(locale, "invalid_message"))
            return
        await event.answer()
    await _present(event, tr(locale, "picker"), language_keyboard(locale))


async def choose_language(callback: CallbackQuery, db: DatabaseManager, locale: Locale) -> None:
    """Persist the selected language for the user who pressed the button."""
    try:
        selected = Locale((callback.data or "").removeprefix("lang:"))
    except ValueError:
        await callback.answer(tr(locale, "unsupported"))
        return
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    sender = callback.from_user
    await db.get_or_create_user(sender.id, sender.username)
    await db.set_language(sender.id, selected.value)
    await callback.answer(tr(selected, "saved"))
    await _present(callback, tr(selected, "home"), dashboard_keyboard(selected))


async def record_question(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale
) -> None:
    """Persist a nonempty text question and close the dialogue."""
    sender = message.from_user
    question = (message.text or "").strip()
    if sender is None or not question or len(question) > 4096:
        await message.answer(tr(locale, "ask_validation"))
        return
    await db.get_or_create_user(sender.id, sender.username)
    await db.save_question(sender.id, question)
    await state.clear()
    await _present(message, tr(locale, "ask_saved"), dashboard_keyboard(locale))


async def _show_progress(
    event: Message | CallbackQuery, sender: User | None, db: DatabaseManager, locale: Locale
) -> None:
    user = await db.get_user(sender.id) if sender else None
    if user is None:
        await _present(event, tr(locale, "no_progress"), dashboard_keyboard(locale))
        return
    topic = LessonManager.get_topic_title(user.current_topic, locale) or user.current_topic.value
    keyboard = InlineKeyboardBuilder()
    if user.current_page < LessonManager.get_total_pages(user.current_topic, locale):
        keyboard.button(
            text=tr(locale, "resume"),
            callback_data=f"topic:{user.current_topic.value}:{user.current_page}",
            style="primary",
        )
    keyboard.button(text=tr(locale, "dashboard"), callback_data="dashboard:home")
    keyboard.adjust(1)
    await _present(
        event,
        f"<b>{tr(locale, 'progress')}</b>\n\n"
        f"👤 {tr(locale, 'learner')}: {escape_html(user.username or tr(locale, 'anonymous'))}\n"
        f"🎯 {tr(locale, 'current_topic')}: {escape_html(topic)}\n"
        f"📄 {tr(locale, 'page')}: {user.current_page + 1}\n"
        f"📅 {tr(locale, 'joined')}: {user.created_at:%Y-%m-%d}",
        keyboard.as_markup(),
    )


async def select_lesson(callback: CallbackQuery, db: DatabaseManager, locale: Locale) -> None:
    """Render a valid lesson and record progress in the selected topic."""
    selection = parse_selection(callback.data or "", locale)
    if selection is None:
        await callback.answer(tr(locale, "invalid_page"))
        return
    if not is_accessible(callback.message):
        await callback.answer(tr(locale, "invalid_message"))
        return
    page = LessonManager.get_topic_content(selection.topic, selection.page, locale)
    if page is None or (selection.view == "code" and not _code_sections(page, locale)):
        await callback.answer(tr(locale, "invalid_page"))
        return
    await _present(
        callback, lesson_text(selection, page, locale), lesson_keyboard(selection, page, locale)
    )
    if selection.view == "lesson":
        user = callback.from_user
        await db.get_or_create_user(user.id, user.username)
        await db.update_user_progress(user.id, selection.topic, selection.page)
    await callback.answer()


async def current_page(callback: CallbackQuery) -> None:
    """Acknowledge a page-indicator tap."""
    await callback.answer()


async def fallback_text(message: Message, locale: Locale) -> None:
    """Invite the learner to use the dashboard or help."""
    await _present(message, tr(locale, "fallback"), dashboard_keyboard(locale))


async def report_failure(event: ErrorEvent) -> bool:
    """Report operational errors without exposing request or database details."""
    logger.warning("Update %s failed (%s)", event.update.update_id, type(event.exception).__name__)
    target = event.update.callback_query or event.update.message
    if target is None:
        return True
    locale = resolve_locale(target.from_user.language_code if target.from_user else None)
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
    router.message.register(record_question, Conversation.waiting_question)
    router.message.register(fallback_text, F.text)
    router.callback_query.register(show_languages, F.data == "languages")
    router.callback_query.register(choose_language, F.data.startswith("lang:"))
    router.callback_query.register(select_lesson, F.data.startswith(("topic:", "page:", "code:")))
    router.callback_query.register(dashboard_action, F.data.startswith("dashboard:"))
    router.callback_query.register(dashboard_action, F.data.in_({"show_topics", "back_to_main"}))
    router.callback_query.register(current_page, F.data == "current_page")
    router.error.register(
        report_failure,
        ExceptionTypeFilter(
            StorageError, TelegramAPIError, ProxyError, ProxyConnectionError, ProxyTimeoutError
        ),
    )
    return router
