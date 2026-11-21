"""Check the capacity, expiry and idle access behavior of dialogue storage."""

import asyncio

import pytest
from aiogram.fsm.storage.base import StorageKey

from bot import dialogue
from bot.dialogue import DialogueStorage


def test_dialogue_expires_and_discards_oldest_at_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = 0.0
    monkeypatch.setattr(dialogue, "monotonic", lambda: now)

    async def scenario() -> None:
        nonlocal now
        storage = DialogueStorage(capacity=2, ttl=10)
        first = StorageKey(bot_id=123, chat_id=1, user_id=1)
        second = StorageKey(bot_id=123, chat_id=2, user_id=2)
        third = StorageKey(bot_id=123, chat_id=3, user_id=3)

        await storage.set_state(first, "waiting")
        now = 1.0
        await storage.set_state(second, "waiting")
        now = 2.0
        await storage.set_state(third, "waiting")
        assert await storage.get_state(first) is None
        assert await storage.get_state(second) == "waiting"
        assert await storage.get_state(third) == "waiting"

        now = 11.0
        assert await storage.get_state(second) is None
        assert await storage.get_state(third) == "waiting"
        now = 12.0
        assert await storage.get_state(third) is None
        await storage.close()

    asyncio.run(scenario())
