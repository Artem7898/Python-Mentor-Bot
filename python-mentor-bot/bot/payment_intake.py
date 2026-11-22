"""Persist Telegram payment events before polling advances its update offset."""

from collections.abc import Awaitable, Callable
from logging import getLogger

from aiogram import Bot
from aiogram.methods import GetUpdates, TelegramMethod
from aiogram.types import Update

from bot.billing import persist_payment_update
from bot.storage import DatabaseManager, StorageError

logger = getLogger(__name__)


class ReceiptJournal:
    """Record payments and refunds while GetUpdates still owns its current offset."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def __call__[Result](
        self,
        make_request: Callable[[Bot, TelegramMethod[Result]], Awaitable[Result]],
        bot: Bot,
        method: TelegramMethod[Result],
    ) -> Result:
        result = await make_request(bot, method)
        if not isinstance(method, GetUpdates) or not isinstance(result, list):
            return result
        for update in result:
            if not isinstance(update, Update) or (message := update.message) is None:
                continue
            if message.successful_payment is None and message.refunded_payment is None:
                continue
            try:
                accepted = await persist_payment_update(message, self._db)
            except StorageError:
                # aiogram retries GetUpdates without advancing the offset.
                raise StorageError("Payment journal write failed. Retrying intake.") from None
            if not accepted:
                logger.warning(
                    "Unrecognized financial update %d requires review.", update.update_id
                )
        return result
