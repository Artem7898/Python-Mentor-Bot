"""Bounded in-memory state for short Telegram conversations."""

import asyncio
from collections import OrderedDict
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseEventIsolation, BaseStorage, StateType, StorageKey


@dataclass(slots=True)
class _Conversation:
    state: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    expires_at: float = 0.0


class DialogueStorage(BaseStorage):
    """Retain only active dialogue state, with expiry and a capacity limit."""

    def __init__(self, *, capacity: int = 4096, ttl: float = 1800) -> None:
        self._capacity = capacity
        self._ttl = ttl
        self._records: OrderedDict[StorageKey, _Conversation] = OrderedDict()

    def _read(self, key: StorageKey) -> _Conversation:
        now = monotonic()
        while self._records and next(iter(self._records.values())).expires_at <= now:
            self._records.popitem(last=False)
        return self._records.get(key) or _Conversation()

    def _write(self, key: StorageKey, entry: _Conversation) -> None:
        if entry.state is None and not entry.data:
            self._records.pop(key, None)
            return
        entry.expires_at = monotonic() + self._ttl
        self._records[key] = entry
        self._records.move_to_end(key)
        if len(self._records) > self._capacity:
            self._records.popitem(last=False)

    async def get_state(self, key: StorageKey) -> str | None:
        """Return the active state without adding an idle user."""
        return self._read(key).state

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """Update or clear the state."""
        entry = self._read(key)
        entry.state = state.state if isinstance(state, State) else state
        self._write(key, entry)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        """Read a copy of the data for an active dialogue."""
        return self._read(key).data.copy()

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        """Replace temporary dialogue data."""
        entry = self._read(key)
        entry.data = dict(data)
        self._write(key, entry)

    async def close(self) -> None:
        """Release stored dialogue state."""
        self._records.clear()


class DialogueIsolation(BaseEventIsolation):
    """Serialize updates per dialogue using a fixed number of locks."""

    def __init__(self) -> None:
        self._locks = tuple(asyncio.Lock() for _ in range(64))

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None]:
        """Hold the lock for the dialogue until its update completes."""
        async with self._locks[hash(key) % len(self._locks)]:
            yield

    async def close(self) -> None:
        """No resources require explicit shutdown."""
