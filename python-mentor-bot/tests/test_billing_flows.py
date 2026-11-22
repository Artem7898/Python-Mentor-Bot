"""Exercise the Stars subscription lifecycle without contacting Telegram."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from aiogram import Bot, Dispatcher, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import (
    AnswerPreCheckoutQuery,
    CreateInvoiceLink,
    EditUserStarSubscription,
    RefundStarPayment,
    TelegramMethod,
)
from aiogram.types import InlineKeyboardMarkup
from test_handlers import TelegramHarness, telegram

from bot import billing, billing_storage
from bot.billing import SUBSCRIPTION_PERIOD, register_billing_routes
from bot.billing_storage import BillingStore
from bot.config import Config, ConfigError
from bot.i18n import Locale

STAR_PRICE = 299
INVOICE_URL = "https://t.me/$synthetic-offline-invoice"
SUPPORT_URL = "https://support.example.invalid/payment"
ACCOUNT = 19


def _config(*, enabled: bool = True, **overrides: str) -> Config:
    values = {
        "BOT_TOKEN": "123:offline-test",
        "BILLING_ENABLED": "true" if enabled else "false",
        "BILLING_SUPPORT_URL": SUPPORT_URL,
        **overrides,
    }
    return Config.from_sources(values, environ={})


@asynccontextmanager
async def _billing(
    db_path: Path, monkeypatch: pytest.MonkeyPatch, config: Config
) -> AsyncIterator[TelegramHarness]:
    async with telegram(db_path, monkeypatch, language_code="en") as client:
        fallback = AiohttpSession.make_request

        async def capture(
            session: AiohttpSession,
            bot: Bot,
            method: TelegramMethod[Any],
            timeout: int | None = None,
        ) -> Any:
            if isinstance(method, CreateInvoiceLink):
                client.requests.append(method)
                return INVOICE_URL
            if isinstance(method, AnswerPreCheckoutQuery):
                assert timeout == 5
            return await fallback(session, bot, method, timeout)

        monkeypatch.setattr(AiohttpSession, "make_request", capture)
        client.dispatcher = Dispatcher(config=config, locale=Locale.EN)
        router = Router()
        register_billing_routes(router)
        client.dispatcher.include_router(router)
        yield client


async def _invoice(client: TelegramHarness) -> CreateInvoiceLink:
    await client.callback("pro:buy")
    return next(
        method for method in reversed(client.requests) if isinstance(method, CreateInvoiceLink)
    )


async def _checkout(
    client: TelegramHarness, payload: str, **changes: object
) -> AnswerPreCheckoutQuery:
    update_id = next(client.update_ids)
    await client.dispatcher.feed_raw_update(
        client.bot,
        {
            "update_id": update_id,
            "pre_checkout_query": {
                "id": str(update_id),
                "from": client.user,
                "currency": "XTR",
                "total_amount": STAR_PRICE,
                "invoice_payload": payload,
                **changes,
            },
        },
        db=client.db,
    )
    method = client.requests[-1]
    assert isinstance(method, AnswerPreCheckoutQuery)
    return method


async def _receipt(
    client: TelegramHarness,
    payload: str,
    expiration: int,
    charge: str,
    *,
    first: bool,
    **changes: object,
) -> None:
    await client.message(
        successful_payment={
            "currency": "XTR",
            "total_amount": STAR_PRICE,
            "invoice_payload": payload,
            "telegram_payment_charge_id": charge,
            "provider_payment_charge_id": "",
            "subscription_expiration_date": expiration,
            "is_recurring": True,
            "is_first_recurring": first,
            **changes,
        }
    )


async def _refund(client: TelegramHarness, payload: str, charge: str) -> None:
    await client.message(
        refunded_payment={
            "currency": "XTR",
            "total_amount": STAR_PRICE,
            "invoice_payload": payload,
            "telegram_payment_charge_id": charge,
        }
    )


def test_billing_and_mentor_config_defaults_and_validation() -> None:
    defaults = Config.from_sources({"BOT_TOKEN": "123:offline-test"}, environ={})
    assert defaults.billing_enabled is False
    assert defaults.pro_price_stars == STAR_PRICE
    assert defaults.mentor_openai_api_key is None
    assert defaults.mentor_openai_model == "gpt-4.1-mini"

    with pytest.raises(ConfigError, match="support"):
        Config.from_sources(
            {"BOT_TOKEN": "123:offline-test", "BILLING_ENABLED": "true"}, environ={}
        )
    assert _config(PRO_PRICE_STARS="299").pro_price_stars == STAR_PRICE
    for bad_price in ("0", "298", "300", "10001", "299.0", "-1"):
        with pytest.raises(ConfigError, match="PRO_PRICE_STARS"):
            _config(PRO_PRICE_STARS=bad_price)
    with pytest.raises(ConfigError, match="BILLING_SUPPORT_URL"):
        _config(BILLING_SUPPORT_URL="http://support.example.invalid")
    with pytest.raises(ConfigError, match="MENTOR_OPENAI_MODEL"):
        _config(MENTOR_OPENAI_MODEL="three invalid words")

    synthetic_key = "offline-synthetic-key"
    configured = _config(MENTOR_OPENAI_API_KEY=synthetic_key)
    assert configured.mentor_openai_api_key is not None
    assert synthetic_key not in repr(configured)
    assert synthetic_key not in configured.model_dump_json()


def test_invoice_and_checkout_verify_amount_currency_buyer_and_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            await client.message("/pro")
            assert str(STAR_PRICE) in client.last_message().text
            assert "pro:buy" in client.inline_buttons()
            await client.callback(
                "pro:buy", chat={"id": -10001, "type": "supergroup", "title": "Shared"}
            )
            assert not any(isinstance(method, CreateInvoiceLink) for method in client.requests)

            invoice = await _invoice(client)
            assert invoice.currency == "XTR"
            assert invoice.provider_token == ""
            assert invoice.subscription_period == SUBSCRIPTION_PERIOD
            assert [cost.amount for cost in invoice.prices] == [STAR_PRICE]
            assert 1 <= len(invoice.payload.encode()) <= 128
            markup = client.last_display().reply_markup
            assert isinstance(markup, InlineKeyboardMarkup)
            assert markup.inline_keyboard[0][0].url == INVOICE_URL

            wrong_user = dict(client.user, id=999)
            other_checkout = await _checkout(client, invoice.payload, **{"from": wrong_user})
            assert not other_checkout.ok and other_checkout.error_message
            assert not (await _checkout(client, invoice.payload, total_amount=1)).ok
            assert not (await _checkout(client, invoice.payload, currency="USD")).ok
            assert not (await _checkout(client, "unknown-intent")).ok
            assert (await _checkout(client, invoice.payload)).ok
            assert not (await _checkout(client, invoice.payload)).ok
            assert await BillingStore(client.db).get_pro_subscription(ACCOUNT) is None

    asyncio.run(run())


def test_authoritative_events_survive_disabling_offers_and_apply_refunds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            invoice = await _invoice(client)
            assert (await _checkout(client, invoice.payload)).ok
            expiration = int(datetime.now(UTC).timestamp()) + SUBSCRIPTION_PERIOD
            await _receipt(
                client, invoice.payload, expiration, "not-recurring", first=True, is_recurring=False
            )
            assert await BillingStore(client.db).get_pro_subscription(ACCOUNT) is None

            await _receipt(client, invoice.payload, expiration, "first-charge", first=True)
            await _receipt(client, invoice.payload, expiration, "first-charge", first=True)

            client.dispatcher["config"] = _config(enabled=False)
            renewal = expiration + SUBSCRIPTION_PERIOD
            await _receipt(client, invoice.payload, renewal, "second-charge", first=False)
            subscription = await BillingStore(client.db).get_pro_subscription(ACCOUNT)
            assert subscription is not None and subscription.is_active
            assert int(subscription.expires_at.timestamp()) == renewal
            assert subscription.initial_charge_id == "first-charge"

            await _refund(client, invoice.payload, "second-charge")
            subscription = await BillingStore(client.db).get_pro_subscription(ACCOUNT)
            assert subscription is not None
            assert int(subscription.expires_at.timestamp()) == expiration
            await _refund(client, invoice.payload, "first-charge")
            assert await BillingStore(client.db).get_pro_subscription(ACCOUNT) is None
            assert not any(isinstance(method, RefundStarPayment) for method in client.requests)

            client.requests.clear()
            await client.callback("pro:buy")
            assert not any(isinstance(method, CreateInvoiceLink) for method in client.requests)
            assert "unavailable" in client.last_display().text

    asyncio.run(run())


def test_manage_renewal_requires_matching_subscription_and_preserves_paid_term(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            invoice = await _invoice(client)
            assert (await _checkout(client, invoice.payload)).ok
            expiration = int(datetime.now(UTC).timestamp()) + SUBSCRIPTION_PERIOD
            await _receipt(client, invoice.payload, expiration, "first-charge", first=True)
            await client.message("/pro")
            buttons = client.inline_buttons()
            assert {"pro:review", "pro:interview"} <= buttons.keys()
            cancel = next(key for key in buttons if key.startswith("pro:cancel:"))
            await client.callback(cancel)
            confirmation = next(
                key for key in client.inline_buttons() if key.startswith("pro:confirm_cancel:")
            )
            await client.callback("pro:confirm_cancel:stale")
            assert not any(
                isinstance(method, EditUserStarSubscription) for method in client.requests
            )
            await client.callback(confirmation)
            edit = next(
                method for method in client.requests if isinstance(method, EditUserStarSubscription)
            )
            assert edit.user_id == ACCOUNT
            assert edit.telegram_payment_charge_id == "first-charge"
            assert edit.is_canceled is True
            subscription = await BillingStore(client.db).get_pro_subscription(ACCOUNT)
            assert subscription is not None and subscription.is_active
            assert subscription.renewal_enabled is False
            assert int(subscription.expires_at.timestamp()) == expiration

            resume = next(key for key in client.inline_buttons() if key.startswith("pro:resume:"))
            await client.callback(resume)
            edit = next(
                method
                for method in reversed(client.requests)
                if isinstance(method, EditUserStarSubscription)
            )
            assert edit.is_canceled is False

    asyncio.run(run())


def test_payment_support_uses_configured_secure_contact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            await client.message("/paysupport")
            markup = client.last_message().reply_markup
            assert isinstance(markup, InlineKeyboardMarkup)
            assert markup.inline_keyboard[0][0].url == SUPPORT_URL

    asyncio.run(run())


def test_payment_support_defaults_to_human_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = Config.from_sources(
        {"BOT_TOKEN": "123:offline-test", "BILLING_ENABLED": "1", "BOT_OWNER_IDS": str(ACCOUNT)},
        environ={},
    )

    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, config) as client:
            await client.message("/paysupport")
            assert "payment:human" in client.inline_buttons()

    asyncio.run(run())


def test_checkout_declines_before_slow_storage_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            answered = asyncio.Event()
            capture_payment_request = AiohttpSession.make_request

            async def mark_answer(
                session: AiohttpSession,
                bot: Bot,
                method: TelegramMethod[Any],
                timeout: int | None = None,
            ) -> Any:
                if isinstance(method, AnswerPreCheckoutQuery):
                    answered.set()
                return await capture_payment_request(session, bot, method, timeout)

            async def busy_store(_store: BillingStore, *args: object, **kwargs: object) -> bool:
                try:
                    await asyncio.sleep(30)
                finally:
                    await answered.wait()
                return True

            monkeypatch.setattr(AiohttpSession, "make_request", mark_answer)
            monkeypatch.setattr(BillingStore, "validate_billing_checkout", busy_store)
            monkeypatch.setattr(billing, "_CHECKOUT_VALIDATION_TIMEOUT", 0.01)
            reply = await asyncio.wait_for(_checkout(client, "slow-validation"), timeout=1)
            assert not reply.ok

    asyncio.run(run())


def test_trial_is_explicit_private_and_preserves_price_without_creating_a_charge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(2026, 11, 30, 12, tzinfo=UTC)
    expiration = datetime(2027, 2, 28, 12, tzinfo=UTC)
    monkeypatch.setattr(billing_storage, "time", lambda: now.timestamp())

    async def run() -> None:
        nonlocal now
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            store = BillingStore(client.db)
            await client.message("/pro")
            view = client.last_message().text
            assert "three calendar months" in view
            assert "no charge or auto-renewal" in view
            assert "299 Telegram Stars" in view
            assert {"pro:trial", "pro:buy"} <= client.inline_buttons().keys()
            assert await store.get_pro_trial(ACCOUNT) is None

            invoice = await _invoice(client)
            client.requests.clear()
            await client.callback(
                "pro:trial", chat={"id": -10001, "type": "supergroup", "title": "Shared"}
            )
            assert await store.get_pro_trial(ACCOUNT) is None

            await client.callback("pro:trial")
            recorded = await store.get_pro_trial(ACCOUNT)
            assert recorded is not None and recorded.is_active
            assert recorded.expires_at == expiration
            assert "Your free Pro trial is active" in client.last_display().text
            assert "299 Telegram Stars" in client.last_display().text
            keys = client.inline_buttons().keys()
            assert {"pro:review", "pro:interview"} <= keys
            assert "pro:buy" not in keys and "pro:trial" not in keys
            assert await store.get_pro_subscription(ACCOUNT) is None

            await client.callback("pro:trial")
            await client.callback("pro:buy")
            assert await store.get_pro_trial(ACCOUNT) == recorded
            assert not (await _checkout(client, invoice.payload)).ok
            assert not any(
                isinstance(method, CreateInvoiceLink | EditUserStarSubscription | RefundStarPayment)
                for method in client.requests
            )

            now = expiration
            await client.message("/pro")
            assert "free trial has ended" in client.last_message().text
            assert "pro:buy" in client.inline_buttons()
            assert "pro:trial" not in client.inline_buttons()
            await client.callback("pro:trial")
            assert await store.get_pro_trial(ACCOUNT) == recorded

    asyncio.run(run())


def test_trial_can_start_when_new_paid_offers_are_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config(enabled=False)) as client:
            await client.message("/pro")
            assert "pro:trial" in client.inline_buttons()
            assert "pro:buy" not in client.inline_buttons()
            await client.callback("pro:trial")
            trial = await BillingStore(client.db).get_pro_trial(ACCOUNT)
            assert trial is not None and trial.is_active
            assert {"pro:review", "pro:interview"} <= client.inline_buttons().keys()

    asyncio.run(run())


def test_legacy_paid_receipt_is_authoritative_without_offering_legacy_price(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        async with _billing(tmp_path / "bot.db", monkeypatch, _config()) as client:
            store = BillingStore(client.db)
            old_price = 350
            payload = await store.create_billing_intent(ACCOUNT, old_price)
            assert not (await _checkout(client, payload, total_amount=old_price)).ok
            assert await store.validate_billing_checkout(
                payload, ACCOUNT, old_price, checkout_id="before-price-change"
            )
            expiration = int(datetime.now(UTC).timestamp()) + SUBSCRIPTION_PERIOD
            await _receipt(
                client, payload, expiration, "historic-charge", first=True, total_amount=old_price
            )
            paid = await store.get_pro_subscription(ACCOUNT)
            assert paid is not None and paid.is_active
            await client.message("/pro")
            assert "pro:trial" not in client.inline_buttons()

    asyncio.run(run())
