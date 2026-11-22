"""Telegram identity boundaries, operator roles and bounded admission."""

from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatType
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
    Update,
    User,
)


@dataclass(frozen=True, slots=True)
class Roles:
    """Server-side role membership keyed by Telegram user ID."""

    owners: frozenset[int] = frozenset()
    mentors: frozenset[int] = frozenset()
    editors: frozenset[int] = frozenset()

    def can_mentor(self, user_id: int) -> bool:
        """Return whether the user can handle learner questions."""
        return user_id in self.owners or user_id in self.mentors

    def can_edit(self, user_id: int) -> bool:
        """Return whether the user can access the editorial workflow."""
        return user_id in self.owners or user_id in self.editors


type ChatEvent = Message | CallbackQuery


def telegram_user(event: ChatEvent) -> User | None:
    """Return a real Telegram user, excluding posts made as a group or channel."""
    if isinstance(event, Message) and event.sender_chat is not None:
        return None
    sender = event.from_user
    return sender if sender is not None and not sender.is_bot else None


def has_private_chat(event: ChatEvent) -> bool:
    """Allow personal operations only in the real user's own private chat."""
    message = event if isinstance(event, Message) else event.message
    user = telegram_user(event)
    return (
        user is not None
        and isinstance(message, Message)
        and message.chat.type == ChatType.PRIVATE
        and message.chat.id == user.id
    )


async def private_keyboard(
    bot: Bot, label: str, *, username: str | None = None
) -> InlineKeyboardMarkup | None:
    """Link to the bot's private conversation without identifying the user."""
    if not username:
        username = getattr(await bot.me(), "username", None)
    if not username:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, url=f"https://t.me/{username}?start=menu")]
        ]
    )


class UserRateLimit(BaseMiddleware):
    """Apply a fixed request budget before FSM locks and database work."""

    def __init__(self, limit: int, window: float, *, capacity: int = 8192) -> None:
        if limit < 1 or window <= 0 or capacity < 1:
            raise ValueError("Rate limit, window and capacity must be positive.")
        self._limit = limit
        self._window = window
        self._capacity = capacity
        self._buckets: OrderedDict[int, tuple[float, int]] = OrderedDict()

    def _admit(self, key: int, now: float) -> bool:
        while self._buckets and next(iter(self._buckets.values()))[0] <= now:
            self._buckets.popitem(last=False)
        bucket = self._buckets.get(key)
        if bucket is None:
            if len(self._buckets) >= self._capacity:
                return False
            self._buckets[key] = (now + self._window, 1)
            return True
        end, count = bucket
        if count >= self._limit:
            return False
        self._buckets[key] = (end, count + 1)
        return True

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update) and (entry := event.message or event.callback_query):
            sender = telegram_user(entry)
            message = entry if isinstance(entry, Message) else entry.message
            if sender is not None:
                key = sender.id
            elif isinstance(message, (Message, InaccessibleMessage)):
                key = message.chat.id
            else:
                return None
            if not self._admit(key, monotonic()):
                return None
        return await handler(event, data)
