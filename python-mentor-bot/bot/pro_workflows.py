"""Require a live Pro entitlement before each private Pro action."""

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.access import ChatEvent, telegram_user
from bot.i18n import Locale
from bot.monetization import has_pro
from bot.presentation import present, require_private
from bot.pro_features import (
    INTERVIEW_COUNT,
    interview_complete,
    interview_feedback,
    interview_question,
    review_code,
    review_prompt,
    valid_interview_answer,
)
from bot.storage import DatabaseManager

_ACCESS = {
    Locale.RU: ("Разбор кода и тренажёр доступны с активным Pro.", "Посмотреть Pro"),
    Locale.EN: ("Code review and interview practice require active Pro.", "See Pro"),
    Locale.ES: ("La revisión y el simulador requieren una suscripción Pro activa.", "Ver Pro"),
}


class ProState(StatesGroup):
    """Private code review and interview conversations."""

    review = State()
    interview = State()


async def _authorized(
    event: ChatEvent, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> bool:
    if not await require_private(event, locale, bot):
        return False
    sender = telegram_user(event)
    if sender is not None and await has_pro(db, sender.id):
        return True
    current = await state.get_state()
    if current in {ProState.review.state, ProState.interview.state}:
        await state.clear()
    if isinstance(event, CallbackQuery):
        await event.answer()
    notice, label = _ACCESS[locale]
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="pro:home")]]
    )
    await present(event, notice, markup)
    return False


async def start_review(
    event: ChatEvent,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    command: CommandObject | None = None,
) -> None:
    """Accept Python in the command or request one bounded text example."""
    if not await _authorized(event, state, db, locale, bot):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    await state.clear()
    source = command.args if command else None
    if source:
        await present(event, review_code(source, locale))
        return
    await state.set_state(ProState.review)
    await present(event, review_prompt(locale))


async def review_submission(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Recheck the entitlement before inspecting a submitted snippet."""
    if not await _authorized(message, state, db, locale, bot):
        return
    if not message.text:
        await message.answer(review_prompt(locale))
        return
    await message.answer(review_code(message.text, locale))
    await state.clear()


async def start_interview(
    event: ChatEvent, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Start a localized technical interview from the first question."""
    if not await _authorized(event, state, db, locale, bot):
        return
    first = interview_question(0, locale)
    if first is None:
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    await state.clear()
    await state.set_state(ProState.interview)
    await state.set_data({"interview_index": 0})
    await present(event, first)


async def interview_submission(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Evaluate one answer and advance while the subscription remains active."""
    if not await _authorized(message, state, db, locale, bot):
        return
    index = (await state.get_data()).get("interview_index")
    if type(index) is not int or not 0 <= index < INTERVIEW_COUNT:
        await state.clear()
        return
    answer = message.text or ""
    text = interview_feedback(index, answer, locale)
    if text is None:
        await state.clear()
        return
    if not valid_interview_answer(answer):
        await message.answer(text)
        return

    next_index = index + 1
    next_prompt = interview_question(next_index, locale)
    if next_prompt is None:
        await message.answer(text)
        await message.answer(interview_complete(locale))
        await state.clear()
    else:
        await message.answer(text)
        await message.answer(next_prompt)
        await state.set_data({"interview_index": next_index})


def register_pro_routes(router: Router) -> None:
    """Register the authorized Pro commands and their continuation states."""
    router.message.register(start_review, Command("review"))
    router.message.register(start_interview, Command("interview"))
    router.callback_query.register(start_review, F.data == "pro:review")
    router.callback_query.register(start_interview, F.data == "pro:interview")


def register_pro_replies(router: Router) -> None:
    """Route free-form replies after the public command handlers."""
    router.message.register(review_submission, ProState.review)
    router.message.register(interview_submission, ProState.interview)
