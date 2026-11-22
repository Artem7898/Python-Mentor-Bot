"""Check Free and Pro replies through a captured Telegram transport."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aiogram.methods import EditMessageText, SendMessage
from aiogram.types import Message
from test_expanded_curriculum import TelegramText
from test_handlers import TelegramHarness, telegram

from bot import billing_storage, monetization
from bot.i18n import Locale
from bot.storage import QuestionStatus

LEARNER = 19
QUESTION = "What is the difference between lists and tuples?"
ANSWER_FRAGMENT = "A list allows insertion"
FOOTER_MARKER = "Support notice for this completed answer."


@dataclass
class Access:
    """Allow tests to simulate a subscription expiring between Telegram updates."""

    is_active: bool


def _entitlement(monkeypatch: pytest.MonkeyPatch, *, active: bool) -> tuple[Access, list[int]]:
    entitlement = Access(active)
    seen_users: list[int] = []

    async def lookup(_store: billing_storage.BillingStore, user_id: int) -> Access | None:
        seen_users.append(user_id)
        return entitlement if user_id == LEARNER else None

    monkeypatch.setattr(billing_storage.BillingStore, "get_pro_subscription", lookup)
    return entitlement, seen_users


def _footer_marker(monkeypatch: pytest.MonkeyPatch) -> list[Locale]:
    calls: list[Locale] = []

    def marker(locale: Locale, previous_index: int | None = None) -> tuple[str, int]:
        calls.append(locale)
        return FOOTER_MARKER, 0 if previous_index != 0 else 1

    monkeypatch.setattr(monetization, "free_footer", marker)
    return calls


def _displayed(client: TelegramHarness) -> list[str]:
    return [
        request.text
        for request in client.requests
        if isinstance(request, SendMessage | EditMessageText)
    ]


def _plain(html: str) -> str:
    parser = TelegramText()
    parser.feed(html)
    parser.close()
    assert not parser.tags
    return "".join(parser.text)


@pytest.mark.parametrize("locale", tuple(Locale))
def test_footer_rotates_without_immediate_repetition(locale: Locale) -> None:
    first, first_index = monetization.free_footer(locale)
    second, second_index = monetization.free_footer(locale, first_index)
    assert first.strip() and second.strip()
    assert first_index != second_index
    assert first != second


@pytest.mark.parametrize("via_menu", [False, True])
def test_a_free_answer_has_one_footer_after_the_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, via_menu: bool
) -> None:
    calls = _footer_marker(monkeypatch)
    _entitlement(monkeypatch, active=False)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.message("/start")
            if via_menu:
                await client.callback("dashboard:ask")
            assert not calls
            client.requests.clear()

            await client.message(QUESTION if via_menu else f"/ask {QUESTION}")

            messages = list(map(_plain, _displayed(client)))
            full_answer = "\n".join(messages)
            assert ANSWER_FRAGMENT in full_answer
            assert full_answer.count(FOOTER_MARKER) == 1
            assert messages[-1].rstrip().endswith(FOOTER_MARKER)
            assert calls == [Locale.EN]

    asyncio.run(scenario())


def test_pro_educational_answer_has_no_support_footer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _footer_marker(monkeypatch)
    _, seen_users = _entitlement(monkeypatch, active=True)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.message(f"/ask {QUESTION}")
            answer = "\n".join(_displayed(client))
            assert ANSWER_FRAGMENT in answer
            assert FOOTER_MARKER not in answer
            assert not calls
            assert LEARNER in seen_users

    asyncio.run(scenario())


@pytest.mark.parametrize("active", [False, True])
def test_stored_mentor_answer_only_shows_a_notice_on_the_last_free_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, active: bool
) -> None:
    calls = _footer_marker(monkeypatch)
    _entitlement(monkeypatch, active=active)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.db.get_or_create_user(LEARNER)
            question = await client.db.submit_question(LEARNER, "How should I annotate this?")
            await client.db.set_question_status(
                question.id,
                QuestionStatus.ANSWERED,
                answer="Review the local type annotations. " * 50 + "End of the mentor answer.",
            )
            await client.callback(f"questions:view:{question.id}")
            assert FOOTER_MARKER not in client.last_display().text

            await client.callback(f"questions:read:{question.id}:a:0")
            assert f"questions:read:{question.id}:a:1" in client.inline_buttons()
            assert FOOTER_MARKER not in client.last_display().text
            assert not calls
            await client.callback(f"questions:read:{question.id}:a:1")

            last = _plain(client.last_display().text)
            assert "End of the mentor answer." in last
            if active:
                assert FOOTER_MARKER not in last
                assert not calls
            else:
                assert last.count(FOOTER_MARKER) == 1
                assert last.rstrip().endswith(FOOTER_MARKER)
                assert calls == [Locale.EN]

    asyncio.run(scenario())


def test_navigation_prompts_and_queued_questions_do_not_receive_a_footer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _footer_marker(monkeypatch)
    _entitlement(monkeypatch, active=False)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.message("/start")
            await client.message("/help")
            await client.callback("study:catalog")
            await client.callback("dashboard:ask")
            await client.message("What is the weather in Lima today?")
            assert len(await client.db.list_questions(LEARNER)) == 1
            assert FOOTER_MARKER not in "\n".join(_displayed(client))
            assert not calls

    asyncio.run(scenario())


def test_fragmented_answer_stays_within_telegram_limits_and_appends_one_footer_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _footer_marker(monkeypatch)
    _entitlement(monkeypatch, active=False)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            message = Message.model_validate(
                {
                    "message_id": 1,
                    "chat": {"id": LEARNER, "type": "private"},
                    "date": 1_700_000_000,
                    "from": client.user,
                },
                context={"bot": client.bot},
            )
            body = "🐍" * 4800 + "\nCompare a < b & b > a."
            await monetization.MentorReplies().send(message, body, Locale.EN, client.db)

            messages = _displayed(client)
            assert len(messages) >= 3
            assert all(FOOTER_MARKER not in part for part in messages[:-1])
            assert "&lt;" in messages[-1] and "&amp;" in messages[-1]
            decoded = list(map(_plain, messages))
            assert decoded[-1].rstrip().endswith(FOOTER_MARKER)
            assert "Compare a < b & b > a." in decoded[-1]
            assert all(1 <= len(part.encode("utf-16-le")) // 2 <= 4096 for part in decoded)
            assert sum(part.count("🐍") for part in decoded) == 4800
            assert calls == [Locale.EN]

    asyncio.run(scenario())


def test_active_pro_receives_static_review_and_interview_feedback_without_notices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _footer_marker(monkeypatch)
    _entitlement(monkeypatch, active=True)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.message("/review")
            await client.message("def collect(values=[]):\n    return values")
            assert "Mutable default" in _plain(client.last_display().text)

            await client.message("/interview")
            assert "Interview · 1/" in _plain(client.last_display().text)
            client.requests.clear()
            await client.message(
                "TypeIs narrows both branches, and an empty string is still a string."
            )
            answer = "\n".join(map(_plain, _displayed(client)))
            assert "Sample answer" in answer
            assert "Interview · 2/" in answer
            assert FOOTER_MARKER not in answer
            assert not calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("command", "followup"),
    [
        ("/review", "def double(value: int) -> int:\n    return value * 2"),
        ("/interview", "A list is mutable and a tuple is immutable."),
    ],
)
def test_pro_workflow_rechecks_entitlement_on_command_and_followup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str, followup: str
) -> None:
    access, seen_users = _entitlement(monkeypatch, active=False)

    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            state = client.dispatcher.fsm.get_context(
                bot=client.bot, chat_id=LEARNER, user_id=LEARNER
            )
            await client.message(command)
            assert await state.get_state() is None
            assert "pro" in client.last_display().text.casefold()
            assert seen_users and set(seen_users) == {LEARNER}
            before_open = len(seen_users)

            access.is_active = True
            await client.message(command)
            assert await state.get_state() is not None
            assert len(seen_users) > before_open

            before_followup = len(seen_users)
            access.is_active = False
            await client.message(followup)
            assert len(seen_users) > before_followup
            assert seen_users[-1] == LEARNER
            assert "pro" in client.last_display().text.casefold()
            assert await state.get_state() is None

    asyncio.run(scenario())


def test_verified_payment_and_refund_change_pro_access_without_restarting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            store = billing_storage.BillingStore(client.db)
            payload = await store.create_billing_intent(LEARNER, 299)
            assert await store.validate_billing_checkout(
                payload, LEARNER, 299, checkout_id="offline-checkout"
            )
            receipt = {
                "currency": "XTR",
                "total_amount": 299,
                "invoice_payload": payload,
                "telegram_payment_charge_id": "offline-charge",
                "provider_payment_charge_id": "",
            }
            await client.message(
                successful_payment={
                    **receipt,
                    "is_recurring": True,
                    "is_first_recurring": True,
                    "subscription_expiration_date": int(datetime.now(UTC).timestamp()) + 3600,
                }
            )
            await client.message("/review def collect(values=[]):\n    return values")
            assert "Mutable default" in _plain(client.last_display().text)

            await client.message(refunded_payment=receipt)
            await client.message("/review")
            assert "require active Pro" in _plain(client.last_display().text)
            assert await store.get_pro_subscription(LEARNER) is None

    asyncio.run(scenario())
