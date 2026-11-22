"""Exercise opt-in Pro trials with real SQLite and captured Telegram transport."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aiogram.methods import (
    AnswerPreCheckoutQuery,
    CreateInvoiceLink,
    EditUserStarSubscription,
    RefundStarPayment,
    SendInvoice,
)
from test_handlers import TelegramHarness, telegram
from test_monetization import QUESTION, _displayed, _plain

from bot import billing_storage, monetization
from bot.config import Config
from bot.i18n import Locale
from bot.lessons import LessonTopic
from bot.storage import UserProgress
from main import create_dispatcher

LEARNER = 19
NOW = int(datetime(2026, 8, 31, 19, 30, tzinfo=UTC).timestamp())
EXPECTED_EXPIRY = datetime(2026, 11, 30, 19, 30, tzinfo=UTC)
FOOTER = "Footer for the completed Free answer."
REVIEW = "/review def collect(values=[]):\n    return values"


@asynccontextmanager
async def _trial_bot(
    db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[TelegramHarness]:
    cfg = Config.from_sources(
        {"BOT_TOKEN": "123:offline-test", "BILLING_ENABLED": "false"}, environ={}
    )
    async with telegram(db_path, monkeypatch, language_code="en") as client:
        client.dispatcher = create_dispatcher(cfg)
        yield client


def _assert_no_purchase_requests(client: TelegramHarness) -> None:
    payment = (
        AnswerPreCheckoutQuery
        | CreateInvoiceLink
        | EditUserStarSubscription
        | RefundStarPayment
        | SendInvoice
    )
    assert not any(isinstance(request, payment) for request in client.requests)


def test_trial_activates_pro_without_a_purchase_and_expiration_restores_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = float(NOW)
    monkeypatch.setattr(billing_storage, "time", lambda: now)

    def notice(
        _locale: Locale, _previous_index: int | None = None, **_options: object
    ) -> tuple[str, int]:
        return FOOTER, 0

    monkeypatch.setattr(monetization, "free_footer", notice)

    async def scenario() -> None:
        nonlocal now
        async with _trial_bot(tmp_path / "trial.db", monkeypatch) as client:
            store = billing_storage.BillingStore(client.db)
            await client.message("/start")
            assert await store.get_pro_trial(LEARNER) is None
            await client.message(REVIEW)
            assert "require active Pro" in _plain(client.last_display().text)

            await client.message("/pro")
            assert "pro:trial" in client.inline_buttons()
            await client.callback("pro:trial")
            trial = await store.get_pro_trial(LEARNER)
            assert trial is not None and trial.is_active
            assert trial.expires_at == EXPECTED_EXPIRY
            assert await store.get_pro_subscription(LEARNER) is None

            await client.message(REVIEW)
            assert "Mutable default" in _plain(client.last_display().text)
            await client.message(f"/ask {QUESTION}")
            trial_answer = _plain(client.last_display().text)
            assert "A list allows insertion" in trial_answer
            assert FOOTER not in trial_answer
            _assert_no_purchase_requests(client)

            now = trial.expires_at.timestamp()
            await client.message(REVIEW)
            assert "require active Pro" in _plain(client.last_display().text)
            before_free_answer = len(_displayed(client))
            await client.message(f"/ask {QUESTION}")
            free_answer = "\n".join(map(_plain, _displayed(client)[before_free_answer:]))
            assert free_answer.count(FOOTER) == 1
            assert free_answer.endswith(FOOTER)
            assert free_answer.removesuffix(FOOTER).rstrip() == trial_answer.rstrip()

            await client.message("/pro")
            assert "pro:trial" not in client.inline_buttons()
            await client.callback("pro:trial")
            expired = await store.get_pro_trial(LEARNER)
            assert expired is not None and not expired.is_active
            assert expired.expires_at == trial.expires_at
            _assert_no_purchase_requests(client)

    asyncio.run(scenario())


def test_an_existing_free_learner_can_choose_a_trial_without_losing_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(billing_storage, "time", lambda: NOW)

    async def scenario() -> None:
        async with _trial_bot(tmp_path / "trial.db", monkeypatch) as client:
            store = billing_storage.BillingStore(client.db)
            await client.db.save_user(
                UserProgress(
                    user_id=LEARNER,
                    username="older_learner",
                    current_topic=LessonTopic.PYTHON_314,
                    current_page=2,
                    created_at=datetime(2024, 1, 1, tzinfo=UTC),
                )
            )
            await client.message("/start")
            assert await store.get_pro_trial(LEARNER) is None
            await client.message("/pro")
            assert "pro:trial" in client.inline_buttons()
            await client.callback("pro:trial")

            trial = await store.get_pro_trial(LEARNER)
            assert trial is not None and trial.is_active
            user = await client.db.get_user(LEARNER)
            assert user is not None
            assert (user.current_topic, user.current_page) == (LessonTopic.PYTHON_314, 2)
            assert user.created_at == datetime(2024, 1, 1, tzinfo=UTC)
            _assert_no_purchase_requests(client)

    asyncio.run(scenario())


@pytest.mark.parametrize("paid", [False, True])
def test_trial_is_unavailable_with_an_active_payment_or_pending_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, paid: bool
) -> None:
    monkeypatch.setattr(billing_storage, "time", lambda: NOW)

    async def scenario() -> None:
        async with _trial_bot(tmp_path / "trial.db", monkeypatch) as client:
            store = billing_storage.BillingStore(client.db)
            payload = await store.create_billing_intent(LEARNER, 299)
            assert await store.validate_billing_checkout(
                payload, LEARNER, 299, checkout_id="offline-pending-checkout"
            )
            if paid:
                assert await store.record_billing_payment(
                    payload,
                    LEARNER,
                    "offline-paid-charge",
                    299,
                    datetime.fromtimestamp(NOW + 3600, tz=UTC),
                    True,
                )

            await client.message("/pro")
            if paid:
                assert "pro:trial" not in client.inline_buttons()
            await client.callback("pro:trial")
            assert await store.get_pro_trial(LEARNER) is None
            _assert_no_purchase_requests(client)

    asyncio.run(scenario())
