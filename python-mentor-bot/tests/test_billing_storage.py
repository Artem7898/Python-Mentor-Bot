"""Exercise Stars receipt verification without connecting to Telegram."""

import asyncio
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from bot import billing_storage
from bot.billing_storage import BillingStore
from bot.storage import DatabaseManager


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    value = [int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())]
    monkeypatch.setattr(billing_storage, "time", lambda: value[0])
    return value


def _expiry(clock: list[int], days: int) -> datetime:
    return datetime.fromtimestamp(clock[0], tz=UTC) + timedelta(days=days)


def test_invoice_binding_and_expiration(tmp_path: Path, clock: list[int]) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            payload = await billing.create_billing_intent(100, 99)
            unrelated = await billing.create_billing_intent(100, 99)
            assert payload != unrelated
            assert 0 < len(payload.encode()) <= 128

            assert not await billing.validate_billing_checkout(payload, 101, 99, checkout_id="q1")
            assert not await billing.validate_billing_checkout(payload, 100, 98, checkout_id="q1")
            assert not await billing.validate_billing_checkout(
                payload, 100, 99, checkout_id="q1", currency="USD"
            )
            assert not await billing.validate_billing_checkout("unknown", 100, 99, checkout_id="q1")
            assert await billing.validate_billing_checkout(payload, 100, 99, checkout_id="q1")
            assert await billing.validate_billing_checkout(payload, 100, 99, checkout_id="q1")
            assert not await billing.validate_billing_checkout(payload, 100, 99, checkout_id="q2")
            assert not await billing.validate_billing_checkout(unrelated, 100, 99, checkout_id="q2")
            assert await billing.get_pro_subscription(100) is None

            clock[0] += 901
            assert not await billing.validate_billing_checkout(unrelated, 100, 99, checkout_id="q3")
            refreshed = await billing.create_billing_intent(100, 120)
            assert not await billing.validate_billing_checkout(
                refreshed, 100, 120, checkout_id="q1"
            )
            assert await billing.validate_billing_checkout(refreshed, 100, 120, checkout_id="q3")

    asyncio.run(scenario())


def test_concurrent_checkouts_cannot_create_overlapping_claims(tmp_path: Path) -> None:
    async def scenario() -> None:
        path = tmp_path / "bot.db"
        async with DatabaseManager(path) as db1, DatabaseManager(path) as db2:
            first = BillingStore(db1)
            second = BillingStore(db2)
            ticket1 = await first.create_billing_intent(100, 50)
            ticket2 = await second.create_billing_intent(100, 50)
            approvals = await asyncio.gather(
                first.validate_billing_checkout(ticket1, 100, 50, checkout_id="checkout-1"),
                second.validate_billing_checkout(ticket2, 100, 50, checkout_id="checkout-2"),
            )
            assert sum(approvals) == 1

    asyncio.run(scenario())


def test_verified_payment_is_idempotent_and_rejects_mismatched_fields(
    tmp_path: Path, clock: list[int]
) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            payload = await billing.create_billing_intent(100, 99)
            other = await billing.create_billing_intent(101, 99)
            expiration = _expiry(clock, 30)
            charge_id = "telegram-charge"
            assert not await billing.record_billing_payment(
                payload, 101, charge_id, 99, expiration, True
            )
            assert not await billing.record_billing_payment(
                payload, 100, charge_id, 98, expiration, True
            )
            assert not await billing.record_billing_payment(
                payload, 100, charge_id, 99, expiration, True, currency="USD"
            )
            assert not await billing.record_billing_payment(
                "unknown", 100, charge_id, 99, expiration, True
            )
            assert not await billing.record_billing_payment(
                payload, 100, charge_id, 99, expiration.replace(tzinfo=None), True
            )
            assert await billing.get_pro_subscription(100) is None

            assert await billing.record_billing_payment(
                payload, 100, charge_id, 99, expiration, True
            )
            assert await billing.record_billing_payment(
                payload, 100, charge_id, 99, expiration, True
            )
            assert not await billing.record_billing_payment(
                other, 101, charge_id, 99, expiration, True
            )
            assert not await billing.record_billing_payment(
                payload, 100, charge_id, 99, expiration + timedelta(days=3), True
            )
            assert not await billing.record_billing_payment(
                payload, 100, "second-initial", 99, expiration, True
            )
            assert await billing.get_pro_subscription(101) is None
            status = await billing.get_pro_subscription(100)
            assert status is not None and status.is_active
            assert status.expires_at == expiration and status.initial_charge_id == charge_id

            next_invoice = await billing.create_billing_intent(100, 120)
            assert not await billing.validate_billing_checkout(
                next_invoice, 100, 120, checkout_id="cannot-overlap"
            )

    asyncio.run(scenario())


def test_out_of_order_renewals_and_cancellation_keep_telegram_expiry(
    tmp_path: Path, clock: list[int]
) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            payload = await billing.create_billing_intent(100, 100)
            latest = _expiry(clock, 90)
            oldest = _expiry(clock, 30)
            assert await billing.record_billing_payment(payload, 100, "renewal", 100, latest, False)
            status = await billing.get_pro_subscription(100)
            assert status is not None and status.is_active and status.initial_charge_id is None

            assert await billing.record_billing_payment(payload, 100, "initial", 100, oldest, True)
            assert await billing.record_billing_payment(
                payload, 100, "stale", 100, _expiry(clock, 60), False
            )
            status = await billing.get_pro_subscription(100)
            assert status is not None and status.expires_at == latest
            assert status.initial_charge_id == "initial" and status.renewal_enabled

            assert not await billing.set_billing_renewal(101, "initial", False)
            assert not await billing.set_billing_renewal(100, "renewal", False)
            assert await billing.set_billing_renewal(100, "initial", False)
            cancelled = await billing.get_pro_subscription(100)
            assert cancelled is not None and not cancelled.renewal_enabled
            assert cancelled.is_active and cancelled.expires_at == latest
            assert await billing.set_billing_renewal(100, "initial", True)
            resumed = await billing.get_pro_subscription(100)
            assert resumed is not None and resumed.renewal_enabled
            clock[0] = int(latest.timestamp())
            assert not resumed.is_active

    asyncio.run(scenario())


def test_refunds_restore_other_paid_periods_and_win_over_late_payment(
    tmp_path: Path, clock: list[int]
) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            payload = await billing.create_billing_intent(100, 99)
            other = await billing.create_billing_intent(101, 99)
            initial_expiry = _expiry(clock, 30)
            renewal_expiry = _expiry(clock, 60)
            assert await billing.record_billing_payment(
                payload, 100, "first", 99, initial_expiry, True
            )
            assert await billing.record_billing_payment(
                payload, 100, "second", 99, renewal_expiry, False
            )
            assert not await billing.record_billing_refund("second", other, 99)
            assert not await billing.record_billing_refund("second", payload, 98)
            assert not await billing.record_billing_refund("second", payload, 99, currency="EUR")
            assert await billing.record_billing_refund("second", payload, 99)
            assert await billing.record_billing_refund("second", payload, 99)
            status = await billing.get_pro_subscription(100)
            assert status is not None and status.expires_at == initial_expiry

            assert await billing.record_billing_refund("late", payload, 99)
            assert not await billing.record_billing_payment(
                other, 101, "late", 99, renewal_expiry, False
            )
            assert await billing.record_billing_payment(
                payload, 100, "late", 99, renewal_expiry, False
            )
            assert await billing.get_pro_subscription(100) == status
            assert await billing.record_billing_refund("first", payload, 99)
            assert await billing.record_billing_payment(
                payload, 100, "first", 99, initial_expiry, True
            )
            assert await billing.get_pro_subscription(100) is None

    asyncio.run(scenario())


def test_reopen_retains_verified_receipts_after_profile_deletion(
    tmp_path: Path, clock: list[int]
) -> None:
    path = tmp_path / "bot.db"

    async def scenario() -> None:
        expiration = _expiry(clock, 30)
        display_timezone = timezone(timedelta(hours=3))
        async with DatabaseManager(path) as db:
            billing = BillingStore(db)
            await db.get_or_create_user(100)
            payload = await billing.create_billing_intent(100, 99)
            assert await billing.record_billing_payment(
                payload, 100, "receipt", 99, expiration.astimezone(display_timezone), True
            )
            assert await db.delete_user_data(100)

        async with DatabaseManager(path) as db:
            assert await db.get_user(100) is None
            billing = BillingStore(db)
            status = await billing.get_pro_subscription(100)
            assert status is not None and status.expires_at == expiration
            assert await billing.record_billing_refund("receipt", payload, 99)
            assert await billing.get_pro_subscription(100) is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("activation_date", "expiry_date"),
    [
        ((2026, 1, 31), (2026, 4, 30)),
        ((2026, 10, 31), (2027, 1, 31)),
        ((2026, 11, 30), (2027, 2, 28)),
        ((2027, 11, 30), (2028, 2, 29)),
    ],
)
def test_trial_uses_three_utc_calendar_months(
    tmp_path: Path,
    clock: list[int],
    activation_date: tuple[int, int, int],
    expiry_date: tuple[int, int, int],
) -> None:
    activation = datetime(*activation_date, 14, 5, 7, tzinfo=UTC)
    expiry = datetime(*expiry_date, 14, 5, 7, tzinfo=UTC)
    clock[0] = int(activation.timestamp())

    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            assert await billing.get_pro_trial(100) is None
            trial = await billing.activate_pro_trial(100)
            assert trial is not None and trial.is_active
            assert trial.expires_at == expiry
            assert await billing.get_pro_subscription(100) is None
            async with db.connection() as connection:
                rows = await connection.execute_fetchall("SELECT COUNT(*) FROM billing_invoices")
            assert next(iter(rows))[0] == 0
            clock[0] = int(expiry.timestamp())
            assert not trial.is_active
            assert await billing.activate_pro_trial(100) is None
            assert await billing.get_pro_trial(100) == trial

    asyncio.run(scenario())


def test_trial_is_one_per_account_across_connections_and_profile_deletion(
    tmp_path: Path, clock: list[int]
) -> None:
    path = tmp_path / "bot.db"

    async def scenario() -> None:
        async with DatabaseManager(path) as db1, DatabaseManager(path) as db2:
            first = BillingStore(db1)
            second = BillingStore(db2)
            await db1.get_or_create_user(100)
            attempts = await asyncio.gather(
                first.activate_pro_trial(100),
                second.activate_pro_trial(100),
            )
            grants = [grant for grant in attempts if grant is not None]
            assert len(grants) == 1
            grant = grants[0]
            assert await db1.delete_user_data(100)
            assert await second.get_pro_trial(100) == grant

        async with DatabaseManager(path) as reopened:
            assert await reopened.get_user(100) is None
            billing = BillingStore(reopened)
            assert await billing.activate_pro_trial(100) is None
            assert await billing.get_pro_trial(100) == grant
            assert await billing.activate_pro_trial(101) is not None
            clock[0] = int(grant.expires_at.timestamp()) + 1
            assert not grant.is_active
            assert await billing.activate_pro_trial(100) is None

    asyncio.run(scenario())


def test_live_checkout_and_trial_mutually_exclude_each_other(
    tmp_path: Path, clock: list[int]
) -> None:
    path = tmp_path / "bot.db"

    async def scenario() -> None:
        async with DatabaseManager(path) as db1, DatabaseManager(path) as db2:
            checkout = BillingStore(db1)
            grants = BillingStore(db2)

            stale_invoice = await checkout.create_billing_intent(100, 99)
            assert await grants.activate_pro_trial(100) is not None
            assert not await checkout.validate_billing_checkout(
                stale_invoice, 100, 99, checkout_id="during-trial"
            )

            pending = await checkout.create_billing_intent(101, 99)
            assert await checkout.validate_billing_checkout(pending, 101, 99, checkout_id="pending")
            assert await grants.activate_pro_trial(101) is None
            assert await grants.get_pro_trial(101) is None
            clock[0] += 901
            assert await grants.activate_pro_trial(101) is not None

            invoice = await checkout.create_billing_intent(102, 99)
            approved, trial = await asyncio.gather(
                checkout.validate_billing_checkout(invoice, 102, 99, checkout_id="racing"),
                grants.activate_pro_trial(102),
            )
            assert approved is (trial is None)

    asyncio.run(scenario())


def test_paid_pro_blocks_trial_until_no_active_paid_entitlement(
    tmp_path: Path, clock: list[int]
) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            billing = BillingStore(db)
            price = 99
            intent = await billing.create_billing_intent(100, price)
            expiry = _expiry(clock, 30)
            assert await billing.record_billing_payment(intent, 100, "charge", price, expiry, True)
            assert await billing.activate_pro_trial(100) is None
            assert await billing.get_pro_trial(100) is None
            clock[0] = int(expiry.timestamp())
            assert await billing.activate_pro_trial(100) is not None

    asyncio.run(scenario())
