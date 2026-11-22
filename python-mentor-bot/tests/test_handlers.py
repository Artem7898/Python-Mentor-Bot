"""Exercise real aiogram dispatch and SQLite with Telegram replaced at the transport."""

import asyncio
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Any

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, GetMe, SendMessage, TelegramMethod
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, User

from bot.storage import DatabaseManager
from main import create_dispatcher

USER = {"id": 19, "is_bot": False, "first_name": "Test", "username": "mentor_student"}
CHAT = {"id": USER["id"], "type": "private"}
QUESTION_MENU = "❓ Задать вопрос"
DASHBOARD_ACTIONS = {
    "study:catalog",
    "dashboard:examples",
    "dashboard:ask",
    "study:progress",
    "study:bookmarks",
    "study:settings",
    "dashboard:install",
}
LANGUAGE_ACTIONS = {"lang:en", "lang:es", "lang:ru"}


@dataclass
class TelegramHarness:
    bot: Bot
    dispatcher: Dispatcher
    db: DatabaseManager
    requests: list[TelegramMethod[Any]]
    user: dict[str, object]
    update_ids: Iterator[int] = field(default_factory=lambda: count(1))

    async def message(self, text: str | None = None, **content: object) -> None:
        update_id = next(self.update_ids)
        payload = {
            "message_id": update_id,
            "date": 1_700_000_000,
            "from": self.user,
            "chat": CHAT,
            **content,
        }
        if text is not None:
            payload["text"] = text
            if text.startswith("/"):
                payload["entities"] = [
                    {"type": "bot_command", "offset": 0, "length": len(text.split()[0])}
                ]
        await self.dispatcher.feed_raw_update(
            self.bot, {"update_id": update_id, "message": payload}, db=self.db
        )

    async def callback(
        self, data: str, *, accessible: bool = True, chat: dict[str, object] | None = None
    ) -> None:
        update_id = next(self.update_ids)
        payload = {
            "id": str(update_id),
            "from": self.user,
            "chat_instance": "test chat",
            "data": data,
            "message": {
                "message_id": 1,
                "chat": CHAT if chat is None else chat,
                "date": 1_700_000_000 if accessible else 0,
            },
        }
        await self.dispatcher.feed_raw_update(
            self.bot, {"update_id": update_id, "callback_query": payload}, db=self.db
        )

    def last_message(self) -> SendMessage:
        return next(
            request for request in reversed(self.requests) if isinstance(request, SendMessage)
        )

    def last_display(self) -> SendMessage | EditMessageText:
        return next(
            request
            for request in reversed(self.requests)
            if isinstance(request, SendMessage | EditMessageText)
        )

    def inline_buttons(self) -> dict[str, InlineKeyboardButton]:
        markup = self.last_display().reply_markup
        assert isinstance(markup, InlineKeyboardMarkup)
        return {
            button.callback_data: button
            for row in markup.inline_keyboard
            for button in row
            if button.callback_data is not None
        }


@asynccontextmanager
async def telegram(
    db_path: Path, monkeypatch: pytest.MonkeyPatch, *, language_code: str | None = None
) -> AsyncIterator[TelegramHarness]:
    requests: list[TelegramMethod[Any]] = []

    async def capture(
        _session: AiohttpSession,
        _bot: Bot,
        method: TelegramMethod[Any],
        timeout: int | None = None,
    ) -> bool | User:
        requests.append(method)
        if isinstance(method, GetMe):
            return User(id=123, is_bot=True, first_name="Mentor", username="mentor_test_bot")
        return True

    monkeypatch.setattr(AiohttpSession, "make_request", capture)
    dispatcher = create_dispatcher()
    user: dict[str, object] = dict(USER)
    if language_code is not None:
        user["language_code"] = language_code
    async with Bot("123:offline-test") as bot, DatabaseManager(db_path) as db:
        yield TelegramHarness(bot, dispatcher, db, requests, user)


def test_start_and_lesson_navigation_keep_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.message("/start")
            assert "Python Mentor" in client.last_message().text
            assert DASHBOARD_ACTIONS <= client.inline_buttons().keys()

            await client.callback("topic:oop")
            assert any(isinstance(request, EditMessageText) for request in client.requests)

            await client.message("/start")
            await client.message("📊 Мой прогресс")
            assert "прогресс" in client.last_message().text.casefold()
            assert "0" in client.last_message().text
            assert await client.db.get_last_lesson(19) == "oop.intro"
            user = await client.db.get_user(19)
            assert user is not None
            assert user.current_topic == "oop"

    asyncio.run(scenario())


def test_help_and_nontext_do_not_become_questions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "bot.db"

    async def scenario() -> None:
        async with telegram(db_path, monkeypatch) as client:
            await client.message("/start")
            await client.message(QUESTION_MENU)
            await client.message("/help")
            assert "/help" in client.last_message().text

            await client.message("📚 Темы обучения")
            assert "Каталог уроков" in client.last_message().text
            await client.message(
                photo=[{"file_id": "photo", "file_unique_id": "unique", "width": 10, "height": 10}]
            )
            assert "текст" in client.last_message().text.casefold()
            await client.message("Как работает list?")

    asyncio.run(scenario())
    with closing(sqlite3.connect(db_path, autocommit=True)) as connection:
        rows = connection.execute("SELECT question FROM user_questions").fetchall()
    assert rows == [("Как работает list?",)]


def test_run_supports_arithmetic_and_keeps_the_active_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "bot.db"

    async def scenario() -> None:
        async with telegram(db_path, monkeypatch) as client:
            await client.message(QUESTION_MENU)
            await client.message("/run 2 ** 3")
            assert "<code>8</code>" in client.last_message().text
            await client.message("/run abs(-2)")
            assert "только числа и арифметические операции" in client.last_message().text
            await client.message("Как работает степень?")
            assert "Вопрос записан" in client.last_message().text

    asyncio.run(scenario())
    with closing(sqlite3.connect(db_path, autocommit=True)) as connection:
        rows = connection.execute("SELECT question FROM user_questions").fetchall()
    assert rows == [("Как работает степень?",)]


@pytest.mark.parametrize(
    ("data", "accessible"),
    [
        ("topic:oop:-1", True),
        ("page:oop:999", True),
        ("page:unknown:0", True),
        ("topic:oop:0:trailing", True),
        ("code:oop:x", True),
        ("topic:oop", False),
    ],
)
def test_stale_or_invalid_callback_is_acknowledged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: str, accessible: bool
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.callback(data, accessible=accessible)
            assert len(client.requests) == 1
            assert isinstance(client.requests[0], AnswerCallbackQuery)
            assert await client.db.get_user(19) is None

    asyncio.run(scenario())


def test_legacy_back_to_main_opens_the_dashboard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.callback("back_to_main")
            assert DASHBOARD_ACTIONS <= client.inline_buttons().keys()
            assert any(isinstance(request, AnswerCallbackQuery) for request in client.requests)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("locale", "topics_label"),
    [("en-US", "catalogue"), ("es-MX", "catálogo"), ("de-DE", "каталог"), (None, "каталог")],
)
def test_dashboard_has_styled_native_buttons_in_the_initial_locale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    locale: str | None,
    topics_label: str,
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code=locale) as client:
            await client.message("/start")
            buttons = client.inline_buttons()
            assert DASHBOARD_ACTIONS <= buttons.keys()
            assert topics_label in buttons["study:catalog"].text.casefold()
            assert all(1 <= len(payload.encode()) <= 64 for payload in buttons)
            assert any(
                button.style in {"primary", "success", "danger"} for button in buttons.values()
            )

    asyncio.run(scenario())


def test_dashboard_callbacks_open_each_learning_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.message("/start")
            await client.callback("dashboard:topics")
            assert {
                "study:catalog:python",
                "study:catalog:backend",
                "study:catalog:practice",
                "study:search",
            } <= client.inline_buttons().keys()

            await client.callback("dashboard:examples")
            assert any(payload.startswith("code:") for payload in client.inline_buttons())

            await client.callback("dashboard:install")
            assert "Windows" in client.last_display().text

            await client.callback("dashboard:progress")
            assert "прогресс" in client.last_display().text.casefold()

            await client.callback("dashboard:ask")
            assert "вопрос" in client.last_display().text.casefold()
            await client.message("Как открыть документацию?")
            assert "Вопрос записан" in client.last_message().text
            answers = [
                request for request in client.requests if isinstance(request, AnswerCallbackQuery)
            ]
            assert len(answers) == 5

    asyncio.run(scenario())


def test_explicit_language_selection_persists_across_process_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "bot.db"

    async def choose_language() -> None:
        async with telegram(db_path, monkeypatch, language_code="en-US") as client:
            await client.message("/start")
            await client.callback("languages")
            assert LANGUAGE_ACTIONS <= client.inline_buttons().keys()
            before_selection = len(client.requests)
            await client.callback("lang:es")
            assert "catálogo" in client.inline_buttons()["study:catalog"].text.casefold()
            assert any(
                isinstance(request, AnswerCallbackQuery)
                for request in client.requests[before_selection:]
            )

    async def reopen() -> None:
        async with telegram(db_path, monkeypatch, language_code="ru") as client:
            await client.message("/start")
            assert "catálogo" in client.inline_buttons()["study:catalog"].text.casefold()
            await client.callback("dashboard:progress")
            assert "progreso" in client.last_display().text.casefold()
            await client.message("/language")
            assert LANGUAGE_ACTIONS <= client.inline_buttons().keys()

    asyncio.run(choose_language())
    asyncio.run(reopen())


@pytest.mark.parametrize(("data", "accessible"), [("lang:fr", True), ("lang:es", False)])
def test_unavailable_language_choice_does_not_change_the_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: str, accessible: bool
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.message("/start")
            await client.callback("lang:en")
            client.requests.clear()

            await client.callback(data, accessible=accessible)

            assert len(client.requests) == 1
            assert isinstance(client.requests[0], AnswerCallbackQuery)
            assert client.requests[0].text
            assert await client.db.get_language(19) == "en"

    asyncio.run(scenario())


def test_english_topics_link_to_each_new_chapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.callback("study:catalog:backend")
            buttons = client.inline_buttons()
            assert "Web and APIs" in client.last_display().text
            for topic, title in (
                ("django", "Django"),
                ("drf", "Django REST Framework"),
                ("fastapi", "FastAPI"),
                ("pydantic", "Pydantic"),
            ):
                assert title in buttons[f"study:contents:{topic}"].text
                await client.callback(f"topic:{topic}")
                assert title in client.last_display().text
                assert isinstance(client.requests[-1], AnswerCallbackQuery)

    asyncio.run(scenario())


def test_group_language_choice_redirects_and_does_not_save_a_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch) as client:
            await client.callback(
                "lang:es", chat={"id": -123, "type": "group", "title": "Learners"}
            )
            display = client.last_display()
            assert isinstance(display, SendMessage)
            assert display.chat_id == -123
            assert isinstance(display.reply_markup, InlineKeyboardMarkup)
            assert display.reply_markup.inline_keyboard[0][0].url == (
                "https://t.me/mentor_test_bot?start=menu"
            )
            assert not any(isinstance(request, EditMessageText) for request in client.requests)
            assert await client.db.get_language(19) is None

    asyncio.run(scenario())


def test_private_study_flow_tracks_stable_ids_and_reveals_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def scenario() -> None:
        async with telegram(tmp_path / "bot.db", monkeypatch, language_code="en") as client:
            await client.message("/start")
            assert (
                "Start with the basics" in client.inline_buttons()["study:open:basics.intro"].text
            )
            await client.callback("study:open:basics.intro")
            assert "<pre><code" not in client.last_display().text
            await client.callback("code:basics:0")
            assert "<pre><code" in client.last_display().text
            await client.callback("study:complete:basics.intro")
            await client.callback("study:complete:basics.intro")
            await client.callback("study:bookmark:basics.intro:1")
            assert await client.db.list_completed_lessons(19) == ("basics.intro",)
            assert await client.db.list_bookmarks(19) == ("basics.intro",)
            await client.callback("study:bookmarks")
            assert "study:open:basics.intro" in client.inline_buttons()
            await client.callback("study:search")
            await client.message("Django")
            assert any(key.startswith("study:open:django.") for key in client.inline_buttons())
            await client.callback("study:quiz:basics.intro")
            assert any(
                key.startswith("study:quiz:basics.intro:") for key in client.inline_buttons()
            )
            await client.message("/start")
            assert "Continue lesson" in client.inline_buttons()["study:open:basics.intro"].text

    asyncio.run(scenario())
