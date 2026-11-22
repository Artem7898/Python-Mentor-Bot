"""Telegram Stars purchase, receipt ingestion and subscription management."""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime
from hashlib import blake2s

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.access import ChatEvent, telegram_user
from bot.billing_copy import billing_tr
from bot.billing_storage import BillingStore, ProSubscription, ProTrial
from bot.config import PRO_PRICE_STARS, Config
from bot.i18n import Locale, resolve_locale
from bot.presentation import present, require_private
from bot.storage import DatabaseManager, StorageError

STARS_CURRENCY = "XTR"
SUBSCRIPTION_PERIOD = 2_592_000
_CHECKOUT_VALIDATION_TIMEOUT = 2

logger = logging.getLogger(__name__)


def _date(expires_at: datetime) -> str:
    return expires_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _reference(charge_id: str) -> str:
    return blake2s(charge_id.encode(), digest_size=12).hexdigest()


async def _active_plan(store: BillingStore, user_id: int) -> ProSubscription | None:
    subscription = await store.get_pro_subscription(user_id)
    return subscription if subscription is not None and subscription.is_active else None


def subscription_view(
    locale: Locale,
    config: Config | None,
    subscription: ProSubscription | None,
    trial: ProTrial | None = None,
) -> tuple[str, InlineKeyboardMarkup]:
    """Show the user's paid term, free trial, or eligible offers."""
    markup = InlineKeyboardBuilder()
    paragraphs = [billing_tr(locale, "home")]
    active_trial = trial is not None and trial.is_active
    if (subscription is not None and subscription.is_active) or active_trial:
        markup.button(text=billing_tr(locale, "review"), callback_data="pro:review")
        markup.button(text=billing_tr(locale, "interview"), callback_data="pro:interview")

    if subscription is not None and subscription.is_active:
        paragraphs.append(billing_tr(locale, "active", date=_date(subscription.expires_at)))
        if not subscription.renewal_enabled:
            paragraphs.append(billing_tr(locale, "renewal_stopped"))
        if subscription.initial_charge_id is not None:
            action = "cancel" if subscription.renewal_enabled else "resume"
            reference = _reference(subscription.initial_charge_id)
            markup.button(
                text=billing_tr(locale, action), callback_data=f"pro:{action}:{reference}"
            )
    else:
        if trial is None:
            paragraphs.append(billing_tr(locale, "trial_offer"))
            markup.button(text=billing_tr(locale, "trial_start"), callback_data="pro:trial")
        elif active_trial:
            paragraphs.append(billing_tr(locale, "trial_active", date=_date(trial.expires_at)))
        else:
            paragraphs.append(billing_tr(locale, "trial_used"))
        paragraphs.append(billing_tr(locale, "offer", stars=PRO_PRICE_STARS))
        if config is None or not config.billing_enabled:
            paragraphs.append(billing_tr(locale, "unavailable"))
        elif not active_trial:
            markup.button(text=billing_tr(locale, "buy"), callback_data="pro:buy")

    if config is not None and config.billing_terms_url is not None:
        markup.button(text=billing_tr(locale, "terms"), url=str(config.billing_terms_url))
    markup.button(text=billing_tr(locale, "support"), callback_data="pro:support")
    markup.button(text=billing_tr(locale, "dashboard"), callback_data="dashboard:home")
    markup.adjust(1)
    return "\n\n".join(paragraphs), markup.as_markup()


async def show_subscription(
    event: ChatEvent,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    config: Config | None = None,
) -> None:
    """Present subscription management in the buyer's private chat."""
    if not await require_private(event, locale, bot):
        return
    sender = telegram_user(event)
    if sender is None:
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    store = BillingStore(db)
    subscription = await _active_plan(store, sender.id)
    trial = await store.get_pro_trial(sender.id) if subscription is None else None
    await present(event, *subscription_view(locale, config, subscription, trial))


async def start_trial(
    callback: CallbackQuery,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    config: Config | None = None,
) -> None:
    """Start a one-time free term for the authenticated private account."""
    if not await require_private(callback, locale, bot):
        return
    sender = telegram_user(callback)
    if sender is None:
        return
    await callback.answer()

    store = BillingStore(db)
    trial = await store.activate_pro_trial(sender.id)
    subscription = await _active_plan(store, sender.id)
    if trial is None and subscription is None:
        trial = await store.get_pro_trial(sender.id)
    text, markup = subscription_view(locale, config, subscription, trial)
    if trial is None and subscription is None:
        text = f"{billing_tr(locale, 'trial_pending')}\n\n{text}"
    await present(callback, text, markup)


async def payment_support(
    event: ChatEvent, locale: Locale, bot: Bot, config: Config | None = None
) -> None:
    """Give buyers a direct support link or the private mentor inbox."""
    if not await require_private(event, locale, bot):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    markup = InlineKeyboardBuilder()
    if config is not None and config.billing_support_url is not None:
        markup.button(text=billing_tr(locale, "contact"), url=str(config.billing_support_url))
    else:
        markup.button(text=billing_tr(locale, "contact"), callback_data="payment:human")
    markup.button(text=billing_tr(locale, "back"), callback_data="pro:home")
    markup.adjust(1)
    await present(event, billing_tr(locale, "support_hint"), markup.as_markup())


async def create_invoice(
    callback: CallbackQuery,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    config: Config | None = None,
) -> None:
    """Issue a buyer-bound 30-day Stars invoice through Telegram."""
    if not await require_private(callback, locale, bot):
        return
    sender = telegram_user(callback)
    if sender is None:
        return
    await callback.answer()
    store = BillingStore(db)
    subscription = await _active_plan(store, sender.id)
    trial = await store.get_pro_trial(sender.id) if subscription is None else None
    if (
        subscription is not None
        or (trial is not None and trial.is_active)
        or config is None
        or not config.billing_enabled
    ):
        await present(callback, *subscription_view(locale, config, subscription, trial))
        return

    payload = await store.create_billing_intent(sender.id, config.pro_price_stars)
    title = billing_tr(locale, "invoice_title")
    link = await bot.create_invoice_link(
        title=title,
        description=billing_tr(locale, "invoice_description"),
        payload=payload,
        provider_token="",
        currency=STARS_CURRENCY,
        prices=[LabeledPrice(label=title, amount=config.pro_price_stars)],
        subscription_period=SUBSCRIPTION_PERIOD,
    )
    markup = InlineKeyboardBuilder()
    markup.button(text=billing_tr(locale, "pay"), url=link)
    if config.billing_terms_url is not None:
        markup.button(text=billing_tr(locale, "terms"), url=str(config.billing_terms_url))
    markup.button(text=billing_tr(locale, "back"), callback_data="pro:home")
    markup.adjust(1)
    text = billing_tr(locale, "offer", stars=config.pro_price_stars)
    await present(callback, text, markup.as_markup())


async def _verify_checkout(query: PreCheckoutQuery, db: DatabaseManager) -> bool:
    try:
        return await BillingStore(db).validate_billing_checkout(
            query.invoice_payload,
            query.from_user.id,
            query.total_amount,
            checkout_id=query.id,
            currency=query.currency,
        )
    except StorageError:
        logger.warning("Checkout storage validation failed.")
        return False


async def pre_checkout(
    query: PreCheckoutQuery,
    db: DatabaseManager,
    bot: Bot,
    config: Config | None = None,
) -> None:
    """Verify the one-time checkout claim and answer Telegram within its deadline."""
    approved = False
    validation: asyncio.Task[bool] | None = None
    locale = resolve_locale(query.from_user.language_code)
    try:
        if (
            config is not None
            and config.billing_enabled
            and not query.from_user.is_bot
            and query.currency == STARS_CURRENCY
            and query.total_amount == PRO_PRICE_STARS
        ):
            validation = asyncio.create_task(_verify_checkout(query, db))
            ready, _ = await asyncio.wait((validation,), timeout=_CHECKOUT_VALIDATION_TIMEOUT)
            if ready:
                approved = validation.result()
            else:
                validation.cancel()
                logger.warning("Checkout validation exceeded its deadline.")
        # Answer before waiting for a canceled database transaction to roll back.
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=approved,
            error_message=None if approved else billing_tr(locale, "checkout_error"),
            request_timeout=5,
        )
    finally:
        if validation is not None:
            if not validation.done() and not validation.cancelling():
                validation.cancel()
            with suppress(asyncio.CancelledError):
                await validation


async def persist_payment_update(message: Message, db: DatabaseManager) -> bool:
    """Persist an authoritative payment or refund before acknowledging its update."""
    if message.chat.type != ChatType.PRIVATE or message.chat.id <= 0:
        return False
    store = BillingStore(db)
    if (payment := message.successful_payment) is not None:
        sender = message.from_user
        if sender is not None and not sender.is_bot and sender.id != message.chat.id:
            return False
        expiry = payment.subscription_expiration_date
        if payment.currency != STARS_CURRENCY or payment.is_recurring is not True or expiry is None:
            return False
        try:
            expires_at = datetime.fromtimestamp(expiry, tz=UTC)
        except OSError, OverflowError, ValueError:
            return False
        return await store.record_billing_payment(
            payment.invoice_payload,
            message.chat.id,
            payment.telegram_payment_charge_id,
            payment.total_amount,
            expires_at,
            payment.is_first_recurring is True,
            currency=payment.currency,
        )
    if (refund := message.refunded_payment) is not None and refund.currency == STARS_CURRENCY:
        return await store.record_billing_refund(
            refund.telegram_payment_charge_id,
            refund.invoice_payload,
            refund.total_amount,
            currency=refund.currency,
            user_id=message.chat.id,
        )
    return False


async def payment_message(message: Message, db: DatabaseManager) -> None:
    """Handle payment messages when a transport delivers them to the dispatcher."""
    await persist_payment_update(message, db)


async def manage_renewal(
    callback: CallbackQuery,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    config: Config | None = None,
) -> None:
    """Apply a renewal change bound to the buyer and original subscription charge."""
    if not await require_private(callback, locale, bot):
        return
    sender = telegram_user(callback)
    if sender is None:
        return
    action, _, reference = (callback.data or "").removeprefix("pro:").partition(":")
    store = BillingStore(db)
    subscription = await _active_plan(store, sender.id)
    charge_id = subscription.initial_charge_id if subscription is not None else None
    if subscription is None or charge_id is None or _reference(charge_id) != reference:
        await callback.answer(billing_tr(locale, "stale"))
        return

    if action == "cancel" and subscription.renewal_enabled:
        markup = InlineKeyboardBuilder()
        markup.button(
            text=billing_tr(locale, "confirm_button"),
            callback_data=f"pro:confirm_cancel:{reference}",
        )
        markup.button(text=billing_tr(locale, "back"), callback_data="pro:home")
        markup.adjust(1)
        await callback.answer()
        await present(
            callback,
            billing_tr(locale, "confirm_cancel", date=_date(subscription.expires_at)),
            markup.as_markup(),
        )
        return

    if action not in {"confirm_cancel", "resume"}:
        await callback.answer(billing_tr(locale, "stale"))
        return
    enabled = action == "resume"
    await callback.answer()
    if subscription.renewal_enabled != enabled:
        acknowledged = await bot.edit_user_star_subscription(
            user_id=sender.id,
            telegram_payment_charge_id=charge_id,
            is_canceled=not enabled,
        )
        if not acknowledged or not await store.set_billing_renewal(sender.id, charge_id, enabled):
            await present(callback, billing_tr(locale, "stale"))
            return
    current = await _active_plan(store, sender.id)
    trial = await store.get_pro_trial(sender.id) if current is None else None
    text, markup = subscription_view(locale, config, current, trial)
    key = "resumed" if enabled else "cancelled"
    notice = billing_tr(locale, key, date=_date(subscription.expires_at))
    await present(callback, f"{notice}\n\n{text}", markup)


def register_billing_routes(router: Router) -> None:
    """Register Stars payment handlers before any free-text message catchall."""
    router.message.register(show_subscription, Command("pro"))
    router.message.register(payment_support, Command("paysupport"))
    router.message.register(payment_message, F.successful_payment | F.refunded_payment)
    router.pre_checkout_query.register(pre_checkout)
    router.callback_query.register(show_subscription, F.data == "pro:home")
    router.callback_query.register(payment_support, F.data == "pro:support")
    router.callback_query.register(start_trial, F.data == "pro:trial")
    router.callback_query.register(create_invoice, F.data == "pro:buy")
    router.callback_query.register(
        manage_renewal, F.data.startswith(("pro:cancel:", "pro:confirm_cancel:", "pro:resume:"))
    )
