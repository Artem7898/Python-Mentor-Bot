"""Render public and private Telegram views consistently."""

from typing import TypeIs

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InaccessibleMessage, InlineKeyboardMarkup, Message

from bot.access import ChatEvent, has_private_chat, private_keyboard
from bot.i18n import Locale

_PRIVATE_NOTICE = {
    Locale.RU: ("Эта функция доступна в личном чате.", "Открыть в личном чате"),
    Locale.EN: ("This feature is available in a private chat.", "Open private chat"),
    Locale.ES: ("Esta función está disponible en el chat privado.", "Abrir chat privado"),
}


def is_accessible(message: Message | InaccessibleMessage | None) -> TypeIs[Message]:
    """Narrow an optional Telegram callback target to an accessible message."""
    return isinstance(message, Message)


async def present(event: ChatEvent, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    """Edit a private callback target and send a fresh view in shared chats."""
    if isinstance(event, Message):
        await event.answer(text, reply_markup=markup)
        return
    message = event.message
    if not is_accessible(message):
        return
    if message.chat.type != ChatType.PRIVATE:
        await message.answer(text, reply_markup=markup)
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        if "message is not modified" not in exc.message.casefold():
            raise


async def require_private(
    event: ChatEvent, locale: Locale, bot: Bot, bot_username: str | None = None
) -> bool:
    """Redirect a personal action from a shared chat."""
    if has_private_chat(event):
        return True
    notice, label = _PRIVATE_NOTICE[locale]
    if isinstance(event, CallbackQuery):
        await event.answer(notice)
        if not is_accessible(event.message):
            return False
    markup = await private_keyboard(bot, label, username=bot_username)
    await present(event, notice, markup)
    return False
