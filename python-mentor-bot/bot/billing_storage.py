"""Transactional ledger for paid Telegram Stars subscriptions and one-time trials."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from sqlite3 import Row
from time import time

import aiosqlite

from bot.storage import DatabaseManager

_PRO_PRODUCT = "pro_monthly_v1"
_INVOICE_TTL = 15 * 60
_TRIAL_MONTHS = 3
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_ACTIVE_PAID_PRO = """
    SELECT 1 FROM billing_invoices AS existing
    JOIN billing_charges AS charge ON charge.payload = existing.payload
    WHERE existing.user_id = ? AND existing.product = ?
      AND charge.expires_at > ? AND charge.refunded_at IS NULL
"""
_LIVE_CHECKOUT = """
    SELECT 1 FROM billing_invoices AS pending
    WHERE pending.user_id = ? AND pending.product = ? AND pending.checkout_at > ?
      AND NOT EXISTS (
          SELECT 1 FROM billing_charges WHERE payload = pending.payload
      )
"""


@dataclass(frozen=True, slots=True)
class ProSubscription:
    """Latest unrefunded paid expiry and the original recurring charge reference."""

    expires_at: datetime
    initial_charge_id: str | None
    renewal_enabled: bool

    @property
    def is_active(self) -> bool:
        """Report access at the current instant."""
        return self.expires_at.timestamp() > time()


@dataclass(frozen=True, slots=True)
class ProTrial:
    """An account's one-time trial with no payment or renewal mandate."""

    expires_at: datetime

    @property
    def is_active(self) -> bool:
        """Report whether the free access window is still open."""
        return self.expires_at.timestamp() > time()


class BillingStore:
    """Retain server-issued invoice, payment, refund and trial records."""

    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    async def create_billing_intent(self, user_id: int, stars: int) -> str:
        """Create an opaque invoice payload with immutable user, product and price."""
        if not _valid_user_id(user_id) or not _valid_stars(stars):
            raise ValueError("Invalid subscription customer or price.")
        payload = token_urlsafe(32)
        async with self._database.connection() as db:
            await db.execute_fetchall(
                "INSERT INTO billing_invoices (payload, product, user_id, stars, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (payload, _PRO_PRODUCT, user_id, stars, int(time())),
            )
        return payload

    async def validate_billing_checkout(
        self,
        payload: str,
        user_id: int,
        stars: int,
        *,
        checkout_id: str,
        currency: str = "XTR",
    ) -> bool:
        """Reserve the first checkout after checking price, owner and overlap."""
        if not (
            _valid_event(payload, stars, currency)
            and _valid_user_id(user_id)
            and _valid_identifier(checkout_id, 1024)
        ):
            return False
        now = int(time())
        cutoff = now - _INVOICE_TTL
        async with self._database.transaction() as db:
            invoice = await _match_invoice(db, payload, stars, user_id=user_id)
            if invoice is None or invoice["created_at"] <= cutoff:
                return False
            if invoice["checkout_id"] is not None:
                return bool(invoice["checkout_id"] == checkout_id)
            rows = await db.execute_fetchall(
                f"""
                UPDATE billing_invoices SET checkout_id = ?, checkout_at = ?
                WHERE payload = ? AND NOT EXISTS (
                    SELECT 1 FROM billing_invoices
                    WHERE checkout_id = ?
                ) AND NOT EXISTS ({_ACTIVE_PAID_PRO})
                  AND NOT EXISTS ({_LIVE_CHECKOUT})
                  AND NOT EXISTS (
                    SELECT 1 FROM billing_trials WHERE user_id = ? AND expires_at > ?
                )
                RETURNING payload
                """,
                (
                    checkout_id,
                    now,
                    payload,
                    checkout_id,
                    user_id,
                    _PRO_PRODUCT,
                    now,
                    user_id,
                    _PRO_PRODUCT,
                    cutoff,
                    user_id,
                    now,
                ),
            )
            return next(iter(rows), None) is not None

    async def record_billing_payment(
        self,
        payload: str,
        user_id: int,
        telegram_charge_id: str,
        stars: int,
        expires_at: datetime,
        is_first_recurring: bool,
        *,
        currency: str = "XTR",
    ) -> bool:
        """Store the exact Telegram expiry. An already recorded refund still prevails."""
        expiration = _expiry_seconds(expires_at)
        if not (
            _valid_event(payload, stars, currency)
            and _valid_user_id(user_id)
            and _valid_identifier(telegram_charge_id, 1024)
            and expiration is not None
            and type(is_first_recurring) is bool
        ):
            return False
        first = int(is_first_recurring)
        async with self._database.transaction() as db:
            if await _match_invoice(db, payload, stars, user_id=user_id) is None:
                return False
            charge = await _find_charge(db, telegram_charge_id)
            if charge is not None:
                if charge["payload"] != payload:
                    return False
                if charge["expires_at"] is not None:
                    return bool(
                        charge["expires_at"] == expiration and charge["first_recurring"] == first
                    )
            if is_first_recurring:
                first_payments = await db.execute_fetchall(
                    "SELECT 1 FROM billing_charges WHERE payload = ? AND first_recurring = 1",
                    (payload,),
                )
                if next(iter(first_payments), None) is not None:
                    return False

            await db.execute_fetchall(
                """
                INSERT INTO billing_charges (charge_id, payload, expires_at, first_recurring)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (charge_id) DO UPDATE SET
                    expires_at = excluded.expires_at,
                    first_recurring = excluded.first_recurring
                """,
                (telegram_charge_id, payload, expiration, first),
            )
        return True

    async def record_billing_refund(
        self,
        telegram_charge_id: str,
        payload: str,
        stars: int,
        *,
        currency: str = "XTR",
        user_id: int | None = None,
    ) -> bool:
        """Record a confirmed Telegram refund, even if its payment arrives later."""
        if not (
            _valid_event(payload, stars, currency) and _valid_identifier(telegram_charge_id, 1024)
        ):
            return False
        if user_id is not None and not _valid_user_id(user_id):
            return False
        async with self._database.transaction() as db:
            if await _match_invoice(db, payload, stars, user_id=user_id) is None:
                return False
            charge = await _find_charge(db, telegram_charge_id)
            if charge is not None and charge["payload"] != payload:
                return False
            await db.execute_fetchall(
                """
                INSERT INTO billing_charges (charge_id, payload, refunded_at)
                VALUES (?, ?, ?)
                ON CONFLICT (charge_id) DO UPDATE SET
                    refunded_at = coalesce(billing_charges.refunded_at, excluded.refunded_at)
                """,
                (telegram_charge_id, payload, int(time())),
            )
        return True

    async def purge_unused_intents(self) -> None:
        """Remove old drafts that were never approved or matched to a charge."""
        async with self._database.connection() as db:
            async with db.execute(
                """
                DELETE FROM billing_invoices
                WHERE created_at < ? AND checkout_id IS NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM billing_charges WHERE payload = billing_invoices.payload
                  )
                """,
                (int(time()) - 86_400,),
            ):
                pass

    async def get_pro_subscription(self, user_id: int) -> ProSubscription | None:
        """Get the maximum unrefunded expiration from authenticated payment records."""
        if not _valid_user_id(user_id):
            return None
        async with self._database.connection() as db:
            rows = await db.execute_fetchall(
                """
                SELECT paid.expires_at, invoice.renewal_enabled, initial.charge_id AS initial_charge
                FROM billing_invoices AS invoice
                JOIN billing_charges AS paid ON paid.payload = invoice.payload
                LEFT JOIN billing_charges AS initial
                    ON initial.payload = invoice.payload AND initial.first_recurring = 1
                WHERE invoice.user_id = ? AND invoice.product = ?
                  AND paid.refunded_at IS NULL AND paid.expires_at IS NOT NULL
                ORDER BY paid.expires_at DESC, paid.first_recurring DESC, paid.charge_id
                LIMIT 1
                """,
                (user_id, _PRO_PRODUCT),
            )
        row = next(iter(rows), None)
        if row is None:
            return None
        return ProSubscription(
            expires_at=_EPOCH + timedelta(seconds=row["expires_at"]),
            initial_charge_id=row["initial_charge"],
            renewal_enabled=bool(row["renewal_enabled"]),
        )

    async def get_pro_trial(self, user_id: int) -> ProTrial | None:
        """Read the account's grant, including expired grants."""
        if not _valid_user_id(user_id):
            return None
        async with self._database.connection() as db:
            rows = await db.execute_fetchall(
                "SELECT expires_at FROM billing_trials WHERE user_id = ?", (user_id,)
            )
        row = next(iter(rows), None)
        return ProTrial(_EPOCH + timedelta(seconds=row["expires_at"])) if row is not None else None

    async def activate_pro_trial(self, user_id: int) -> ProTrial | None:
        """Grant three UTC calendar months once if no active paid term or checkout exists."""
        if not _valid_user_id(user_id):
            return None
        async with self._database.transaction() as db:
            now = int(time())
            expiry = _trial_expiry(now)
            rows = await db.execute_fetchall(
                f"""
                INSERT INTO billing_trials (user_id, activated_at, expires_at)
                SELECT ?, ?, ? WHERE NOT EXISTS ({_ACTIVE_PAID_PRO})
                  AND NOT EXISTS ({_LIVE_CHECKOUT})
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id
                """,
                (
                    user_id,
                    now,
                    (expiry - _EPOCH) // timedelta(seconds=1),
                    user_id,
                    _PRO_PRODUCT,
                    now,
                    user_id,
                    _PRO_PRODUCT,
                    now - _INVOICE_TTL,
                ),
            )
            return ProTrial(expiry) if next(iter(rows), None) is not None else None

    async def set_billing_renewal(
        self, user_id: int, initial_charge_id: str, enabled: bool
    ) -> bool:
        """Record an acknowledged renewal toggle without changing existing access."""
        if not (
            _valid_user_id(user_id)
            and _valid_identifier(initial_charge_id, 1024)
            and type(enabled) is bool
        ):
            return False
        async with self._database.connection() as db:
            rows = await db.execute_fetchall(
                """
                UPDATE billing_invoices SET renewal_enabled = ?
                WHERE user_id = ? AND product = ? AND payload = (
                    SELECT payload FROM billing_charges WHERE charge_id = ? AND first_recurring = 1
                )
                RETURNING payload
                """,
                (int(enabled), user_id, _PRO_PRODUCT, initial_charge_id),
            )
        return next(iter(rows), None) is not None


async def _match_invoice(
    db: aiosqlite.Connection, payload: str, stars: int, *, user_id: int | None = None
) -> Row | None:
    rows = await db.execute_fetchall(
        "SELECT created_at, checkout_id FROM billing_invoices "
        "WHERE payload = ? AND product = ? AND stars = ? AND (? IS NULL OR user_id = ?)",
        (payload, _PRO_PRODUCT, stars, user_id, user_id),
    )
    return next(iter(rows), None)


async def _find_charge(db: aiosqlite.Connection, charge_id: str) -> Row | None:
    rows = await db.execute_fetchall(
        "SELECT payload, expires_at, first_recurring FROM billing_charges WHERE charge_id = ?",
        (charge_id,),
    )
    return next(iter(rows), None)


def _valid_identifier(value: str, limit: int) -> bool:
    return isinstance(value, str) and 0 < len(value) <= limit and "\x00" not in value


def _valid_event(payload: str, stars: int, currency: str) -> bool:
    return currency == "XTR" and _valid_stars(stars) and _valid_identifier(payload, 128)


def _valid_stars(stars: int) -> bool:
    return type(stars) is int and 1 <= stars <= 10_000


def _valid_user_id(user_id: int) -> bool:
    return type(user_id) is int and 0 < user_id < 2**63


def _trial_expiry(activation: int) -> datetime:
    start = _EPOCH + timedelta(seconds=activation)
    offset, month = divmod(start.month - 1 + _TRIAL_MONTHS, 12)
    year, month = start.year + offset, month + 1
    return start.replace(year=year, month=month, day=min(start.day, monthrange(year, month)[1]))


def _expiry_seconds(expires_at: datetime) -> int | None:
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        return None
    try:
        if expires_at.utcoffset() is None:
            return None
        delta = expires_at.astimezone(UTC) - _EPOCH
    except OverflowError, ValueError:
        return None
    value = delta.days * 86_400 + delta.seconds
    return value if value > 0 else None
