"""Add one optional plan reminder after a complete mentor answer."""

import logging
from collections import OrderedDict
from secrets import randbelow

from aiogram.enums import ParseMode
from aiogram.types import Message

from bot.access import telegram_user
from bot.billing_storage import BillingStore
from bot.formatting import escape_html
from bot.i18n import Locale
from bot.storage import DatabaseManager, StorageError

logger = logging.getLogger(__name__)
_TEXT_LIMIT = 3900
_TRACKING_LIMIT = 4096
_NOTICES = {
    Locale.RU: (
        "Кстати, полный разбор кода с комментариями и тренажёр собеседований доступны в Pro.",
        "Если захочешь глубже разобрать свой код и попрактиковать собеседования, это есть в Pro.",
        "В Pro есть подробный разбор кода и практика технических собеседований.",
        "Для более детального разбора кода и тренировки собеседований можно заглянуть в Pro.",
        "Кстати, Pro включает подробные замечания к коду и тренажёр технических собеседований.",
        "Полный разбор кода и тренажёр собеседований доступны в Pro, если понадобятся.",
        "Если захочешь больше практики, в Pro есть подробный разбор кода и собеседования.",
    ),
    Locale.EN: (
        "By the way, Pro includes a detailed code review and an interview trainer.",
        "If you'd like a deeper look at your code and some interview practice, both are in Pro.",
        "You can get a detailed code review and practise technical interviews in Pro.",
        "For more detailed feedback on your code and interview practice, take a look at Pro.",
        "Pro includes extra code review detail and a technical interview trainer.",
        "Detailed code review and interview practice are available in Pro if you need them.",
        "If you want more practice, Pro offers detailed code review and mock interviews.",
    ),
    Locale.ES: (
        "Por cierto, Pro incluye una revisión detallada de código y un simulador de entrevistas.",
        "Si quieres revisar tu código a fondo y practicar entrevistas, ambas están en Pro.",
        "En Pro puedes obtener una revisión detallada de código y practicar entrevistas técnicas.",
        "Para revisar tu código con más detalle y practicar entrevistas, puedes consultar Pro.",
        "Pro incluye comentarios detallados sobre el código y prácticas de entrevistas técnicas.",
        "La revisión de código y el simulador de entrevistas están en Pro si te sirven.",
        "Si quieres más práctica, en Pro hay revisiones detalladas y simulaciones de entrevistas.",
    ),
}


def free_footer(locale: Locale, previous_index: int | None = None) -> tuple[str, int]:
    """Select a short localized notice, excluding the previous phrase."""
    options = _NOTICES[locale]
    if previous_index is None or not 0 <= previous_index < len(options):
        index = randbelow(len(options))
    else:
        index = randbelow(len(options) - 1)
        if index >= previous_index:
            index += 1
    return options[index], index


def _width(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _split_at_limit(text: str, limit: int) -> int:
    units = 0
    natural_break = 0
    for index, char in enumerate(text):
        units += 2 if ord(char) > 0xFFFF else 1
        if units > limit:
            return natural_break if natural_break >= index // 2 else index
        if char.isspace():
            natural_break = index + 1
    return len(text)


def render_answer_parts(text: str, footer: str | None = None) -> tuple[str, ...]:
    """Split an answer to Telegram-size messages and preserve the full final notice."""
    body = text.encode("utf-8", errors="replace").decode("utf-8").strip()
    if not body:
        return ()
    suffix = f"\n\n{footer}" if footer else ""
    tail_capacity = _TEXT_LIMIT - _width(suffix)
    remaining = _width(body)
    parts: list[str] = []
    while remaining > _TEXT_LIMIT:
        boundary = _split_at_limit(body, _TEXT_LIMIT)
        part, body = body[:boundary], body[boundary:]
        parts.append(part)
        remaining -= _width(part)
    if remaining > tail_capacity:
        # Only the final message reserves space for the whole notice.
        boundary = _split_at_limit(body, min(tail_capacity, remaining // 2))
        parts.append(body[:boundary])
        body = body[boundary:]
    parts.append(body + suffix)
    return tuple(escape_html(part) for part in parts)


async def has_pro(db: DatabaseManager, user_id: int) -> bool:
    """Authorize Pro from a verified payment or this account's active trial."""
    billing = BillingStore(db)
    subscription = await billing.get_pro_subscription(user_id)
    if subscription is not None and subscription.is_active:
        return True
    trial = await billing.get_pro_trial(user_id)
    return trial is not None and trial.is_active


class MentorReplies:
    """Apply the Free footer consistently to live and stored mentor replies."""

    def __init__(self) -> None:
        self._last: OrderedDict[int, int] = OrderedDict()

    async def footer_for(self, user_id: int, locale: Locale, db: DatabaseManager) -> str | None:
        """Resolve the user's live entitlement after the substantive answer is ready."""
        try:
            if await has_pro(db, user_id):
                return None
        except StorageError:
            logger.warning("Could not read the current plan for a mentor answer.")
            return None
        note, index = free_footer(locale, self._last.get(user_id))
        self._last[user_id] = index
        self._last.move_to_end(user_id)
        if len(self._last) > _TRACKING_LIMIT:
            self._last.popitem(last=False)
        return note

    async def send(
        self,
        message: Message,
        text: str,
        locale: Locale,
        db: DatabaseManager,
        *,
        user_id: int | None = None,
    ) -> None:
        """Deliver the same complete answer to either plan with a final Free-only notice."""
        sender = telegram_user(message)
        recipient = user_id if user_id is not None else (sender.id if sender else None)
        footer = (
            await self.footer_for(recipient, locale, db)
            if recipient is not None and text.strip()
            else None
        )
        for part in render_answer_parts(text, footer):
            await message.answer(part, parse_mode=ParseMode.HTML)
