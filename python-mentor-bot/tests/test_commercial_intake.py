"""Verify consent binding and payment intake independently of external services."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from aiogram.methods import AnswerPreCheckoutQuery, GetUpdates
from aiogram.types import Update
from test_handlers import telegram

from bot import payment_intake
from bot.billing_storage import BillingStore
from bot.i18n import Locale
from bot.mentor_answers import MentorAnswerer
from bot.storage import DatabaseManager, StorageError


class RecordingProvider:
    """Capture whether the private question was consented to."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def answer(self, question: str, locale: Locale) -> str:
        self.calls.append(question)
        return "This is the complete answer from the simulated provider."


def test_consent_is_specific_to_the_current_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        provider = RecordingProvider()
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            client.dispatcher["answerer"] = MentorAnswerer(provider)
            await client.message("/ask Could this custom descriptor support class lookup?")
            old_consent = next(key for key in client.inline_buttons() if key.startswith("ask:ai:"))
            assert not provider.calls
            latest = "How should this custom metaclass coordinate instance creation?"
            await client.message(f"/ask {latest}")
            new_consent = next(key for key in client.inline_buttons() if key.startswith("ask:ai:"))
            assert old_consent != new_consent
            await client.callback(old_consent)
            assert not provider.calls
            await client.callback(new_consent)
            assert provider.calls == [latest]
            assert "complete answer" in client.last_message().text
            await client.callback(new_consent)
            assert provider.calls == [latest]
            assert await client.db.list_questions(19) == ()

    asyncio.run(scenario())


def _financial_update(payload: str, expiration: int) -> Update:
    return Update.model_validate(
        {
            "update_id": 1002,
            "message": {
                "message_id": 23,
                "date": 1_700_000_000,
                "from": {"id": 19, "is_bot": False, "first_name": "Fixture"},
                "chat": {"id": 19, "type": "private"},
                "successful_payment": {
                    "currency": "XTR",
                    "total_amount": 299,
                    "invoice_payload": payload,
                    "telegram_payment_charge_id": "charge-fixture-1002",
                    "provider_payment_charge_id": "",
                    "subscription_expiration_date": expiration,
                    "is_recurring": True,
                    "is_first_recurring": True,
                },
            },
        }
    )


def test_journal_persists_before_polling_receives_the_update(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db, Bot("123:offline-test") as bot:
            store = BillingStore(db)
            payload = await store.create_billing_intent(19, 299)
            assert await store.validate_billing_checkout(payload, 19, 299, checkout_id="fixture")
            expiration = int(datetime.now(UTC).timestamp()) + 2_592_000
            updates = [_financial_update(payload, expiration)]

            async def transport(_bot: Bot, _method: GetUpdates) -> list[Update]:
                return updates

            journal = payment_intake.ReceiptJournal(db)
            assert await journal(transport, bot, GetUpdates()) == updates
            plan = await store.get_pro_subscription(19)
            assert plan is not None and plan.expires_at.timestamp() == expiration

    asyncio.run(scenario())


def test_journal_failure_withholds_the_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db, Bot("123:offline-test") as bot:

            async def unavailable(*_args: object) -> bool:
                raise StorageError("Simulated SQLite failure.")

            monkeypatch.setattr(payment_intake, "persist_payment_update", unavailable)

            async def transport(_bot: Bot, _method: GetUpdates) -> list[Update]:
                return [_financial_update("fixture-payload", 1_900_000_000)]

            journal = payment_intake.ReceiptJournal(db)
            with pytest.raises(StorageError, match="Retrying intake"):
                await journal(transport, bot, GetUpdates(offset=1002))

    asyncio.run(scenario())


def test_checkout_does_not_wait_for_same_users_dialogue_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            key = StorageKey(bot_id=client.bot.id, chat_id=19, user_id=19)
            async with client.dispatcher.fsm.events_isolation.lock(key), asyncio.timeout(1):
                await client.dispatcher.feed_raw_update(
                    client.bot,
                    {
                        "update_id": 101,
                        "pre_checkout_query": {
                            "id": "test-query",
                            "from": client.user,
                            "currency": "XTR",
                            "total_amount": 299,
                            "invoice_payload": "fixture-payload",
                        },
                    },
                    db=client.db,
                )
            reply = client.requests[-1]
            assert isinstance(reply, AnswerPreCheckoutQuery)
            assert reply.ok is False  # Sales disabled in this test.

    asyncio.run(scenario())
