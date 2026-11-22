"""Configure and run the Telegram polling process."""

import asyncio
import logging
from contextlib import suppress
from urllib.request import getproxies, proxy_bypass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand
from aiohttp_socks import ProxyConnectionError, ProxyError, ProxyTimeoutError

from bot.access import Roles, UserRateLimit
from bot.config import Config, ConfigError
from bot.dialogue import DialogueIsolation, DialogueStorage
from bot.formatting import markdown_to_html as markdown_to_html
from bot.formatting import validate_markdown as validate_markdown
from bot.handlers import create_router
from bot.i18n import COMMANDS, Locale, tr
from bot.personal import RETENTION_DAYS
from bot.storage import DatabaseManager, StorageError

logger = logging.getLogger(__name__)


def create_dispatcher(
    config: Config | None = None, *, request_limit: int = 20, request_window: float = 10.0
) -> Dispatcher:
    """Create an independent dispatcher and bounded in-memory dialogue storage."""
    roles = Roles(config.owner_ids, config.mentor_ids, config.editor_ids) if config else Roles()
    dispatcher = Dispatcher(
        storage=DialogueStorage(), events_isolation=DialogueIsolation(), roles=roles
    )
    dispatcher.update.outer_middleware.unregister(dispatcher.fsm)
    dispatcher.update.outer_middleware.register(UserRateLimit(request_limit, request_window))
    dispatcher.update.outer_middleware.register(dispatcher.fsm)
    dispatcher.include_router(create_router())
    return dispatcher


async def _purge_questions_periodically(db: DatabaseManager) -> None:
    while True:
        await asyncio.sleep(3600)
        try:
            await db.purge_expired_questions(RETENTION_DAYS)
        except StorageError:
            logger.error("Scheduled question retention cleanup failed.")


async def main(config: Config | None = None, *, session: AiohttpSession | None = None) -> None:
    """Run one bot and close its database and HTTP session on shutdown."""
    if config is None:
        config = await asyncio.to_thread(Config.load)
    logging.basicConfig(
        level=config.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    # The dependencies can log raw updates and bound database values at DEBUG.
    for name in ("aiogram", "aiosqlite"):
        dependency_logger = logging.getLogger(name)
        dependency_logger.setLevel(max(logging.INFO, dependency_logger.getEffectiveLevel()))
    if session is None:
        try:
            proxy = None if proxy_bypass("api.telegram.org") else getproxies().get("https")
            session = AiohttpSession(proxy=proxy, timeout=30)
        except ValueError as exc:
            raise ConfigError("Invalid HTTPS proxy configuration.") from exc

    async with session, DatabaseManager(config.database_path) as db:
        await db.purge_expired_questions(RETENTION_DAYS)
        bot = Bot(
            config.bot_token.get_secret_value(),
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        for locale in Locale:
            await bot.set_my_commands(
                [
                    BotCommand(command=command, description=tr(locale, key))
                    for command, key in COMMANDS
                ],
                language_code=None if locale == Locale.RU else locale.value,
            )
        dispatcher = create_dispatcher(config)
        retention = asyncio.create_task(_purge_questions_periodically(db))
        try:
            await dispatcher.start_polling(
                bot,
                db=db,
                tasks_concurrency_limit=32,
                tasks_shutdown_timeout=35,
                close_bot_session=False,
            )
        finally:
            retention.cancel()
            with suppress(asyncio.CancelledError):
                await retention


def cli() -> int:
    """Return a failure status for configuration, storage or startup API errors."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        return 0
    except ConfigError as exc:
        logger.error("Ошибка конфигурации: %s", exc)
        return 2
    except (
        StorageError,
        TelegramAPIError,
        ProxyError,
        ProxyConnectionError,
        ProxyTimeoutError,
    ) as exc:
        logger.error("Не удалось запустить бота (%s).", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
