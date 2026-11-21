"""Asynchronous SQLite storage for students' progress, preferences and questions."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Error as SQLiteError
from sqlite3 import Row
from types import TracebackType
from typing import Annotated, Literal, Self

import aiosqlite
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, ValidationError

from bot.config import DEFAULT_DATABASE_PATH
from bot.lessons import LessonTopic

type UserId = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]
type PageNumber = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]
type QuestionText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=4096)
]
type Parameters = tuple[int | str | None, ...]
type Language = Literal["ru", "en", "es"]

_USER_ID = TypeAdapter(UserId)
_PAGE = TypeAdapter(PageNumber)
_QUESTION = TypeAdapter(QuestionText, config=ConfigDict(hide_input_in_errors=True))
_LANGUAGE = TypeAdapter(Language, config=ConfigDict(hide_input_in_errors=True))
_USER_COLUMNS = "user_id, username, current_topic, current_page, created_at"


class StorageError(RuntimeError):
    """Raised when student data cannot be persisted or read."""


class UserProgress(BaseModel):
    """Record a student's current lesson and registration time."""

    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    user_id: UserId
    username: str | None = None
    current_topic: LessonTopic = LessonTopic.BASICS
    current_page: PageNumber = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class _LanguagePreference(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    language: Language | None


class DatabaseManager:
    """Reuse one SQLite worker connection for the lifetime of the bot."""

    def __init__(self, db_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.path = Path(db_path)
        self._connection: aiosqlite.Connection | None = None
        self._resources: AsyncExitStack | None = None

    async def __aenter__(self) -> Self:
        if self._resources is not None:
            raise RuntimeError("Database context is already open.")
        resources = self._resources = AsyncExitStack()
        try:
            self._connection = await resources.enter_async_context(self._open(initialize=True))
        except BaseException:
            self._resources = None
            await resources.aclose()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._resources is not None:
            self._connection = None
            resources, self._resources = self._resources, None
            await resources.aclose()

    @asynccontextmanager
    async def _open(self, *, initialize: bool = False) -> AsyncGenerator[aiosqlite.Connection]:
        try:
            await asyncio.to_thread(self.path.parent.mkdir, mode=0o700, parents=True, exist_ok=True)
            async with aiosqlite.connect(self.path, isolation_level=None, timeout=5) as db:
                db.row_factory = Row
                await db.execute_fetchall("PRAGMA foreign_keys = ON")
                if initialize:
                    await self._initialize(db)
                yield db
        except (OSError, SQLiteError) as exc:
            raise StorageError("SQLite operation failed.") from exc

    @asynccontextmanager
    async def _using_connection(self) -> AsyncGenerator[aiosqlite.Connection]:
        try:
            if self._connection is None:
                async with self._open() as db:
                    yield db
            else:
                yield self._connection
        except SQLiteError as exc:
            raise StorageError("SQLite operation failed.") from exc

    async def init_db(self) -> None:
        """Initialize tables and migrate a database created by an older release."""
        if self._connection is None:
            async with self._open(initialize=True):
                pass

    @staticmethod
    async def _initialize(db: aiosqlite.Connection) -> None:
        await db.execute_fetchall("BEGIN IMMEDIATE")
        try:
            await db.execute_fetchall("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    current_topic TEXT NOT NULL,
                    current_page INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """)
            table_columns = await db.execute_fetchall("PRAGMA table_xinfo(users)")
            columns = {row["name"] for row in table_columns}
            if "current_page" not in columns:
                await db.execute_fetchall(
                    "ALTER TABLE users ADD COLUMN current_page INTEGER NOT NULL DEFAULT 0"
                )
            if "language" not in columns:
                await db.execute_fetchall(
                    "ALTER TABLE users ADD COLUMN language TEXT "
                    "CHECK (language IN ('ru', 'en', 'es'))"
                )
            legacy_keys = await db.execute_fetchall("PRAGMA foreign_key_list(questions)")
            if "id" not in columns and any(
                row["table"] == "users" and row["to"] == "id" for row in legacy_keys
            ):
                # The old initializer referenced users.id. Keep its rows and schema intact.
                await db.execute_fetchall(
                    "ALTER TABLE users ADD COLUMN id INTEGER GENERATED ALWAYS AS (user_id) VIRTUAL"
                )
                await db.execute_fetchall(
                    "CREATE UNIQUE INDEX legacy_questions_user_id ON users(id)"
                )
            await db.execute_fetchall("""
                CREATE TABLE IF NOT EXISTS user_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users (user_id),
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
            await db.commit()
        except BaseException:
            await db.rollback()
            raise

    async def _read_one[Model: BaseModel](
        self, model: type[Model], sql: str, parameters: Parameters
    ) -> Model | None:
        async with self._using_connection() as db:
            row = next(iter(await db.execute_fetchall(sql, parameters)), None)
        try:
            return model.model_validate(dict(row)) if row is not None else None
        except ValidationError as exc:
            raise StorageError("Invalid data in SQLite record.") from exc

    async def get_user(self, user_id: int) -> UserProgress | None:
        """Read a student's progress by Telegram ID."""
        return await self._read_one(
            UserProgress,
            f"SELECT {_USER_COLUMNS} FROM users WHERE user_id = ?",
            (_USER_ID.validate_python(user_id),),
        )

    async def get_or_create_user(self, user_id: int, username: str | None = None) -> UserProgress:
        """Register a student atomically and refresh their current Telegram name."""
        user = UserProgress(user_id=user_id, username=username)
        saved = await self._read_one(
            UserProgress,
            f"""
            INSERT INTO users ({_USER_COLUMNS}) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id) DO UPDATE SET username = excluded.username
            RETURNING {_USER_COLUMNS}
            """,
            (
                user.user_id,
                user.username,
                user.current_topic.value,
                user.current_page,
                user.created_at.isoformat(),
            ),
        )
        if saved is None:
            raise StorageError("SQLite did not return the registered student.")
        return saved

    async def update_user_progress(self, user_id: int, topic: LessonTopic, page: int = 0) -> bool:
        """Update lesson coordinates without overwriting profile or registration data."""
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                "UPDATE users SET current_topic = ?, current_page = ? WHERE user_id = ? "
                "RETURNING user_id",
                (topic.value, _PAGE.validate_python(page), _USER_ID.validate_python(user_id)),
            )
        return next(iter(rows), None) is not None

    async def get_language(self, user_id: int) -> str | None:
        """Return the requested locale, or None if the learner has not chosen one."""
        preference = await self._read_one(
            _LanguagePreference,
            "SELECT language FROM users WHERE user_id = ?",
            (_USER_ID.validate_python(user_id),),
        )
        return preference.language if preference is not None else None

    async def set_language(self, user_id: int, language: str) -> None:
        """Persist a supported locale for an already registered learner."""
        parameters = (_LANGUAGE.validate_python(language), _USER_ID.validate_python(user_id))
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                "UPDATE users SET language = ? WHERE user_id = ? RETURNING user_id", parameters
            )
        if next(iter(rows), None) is None:
            raise StorageError("Register the student before saving a language preference.")

    async def save_user(self, user: UserProgress) -> None:
        """Save a complete student record while retaining its related questions."""
        async with self._using_connection() as db:
            await db.execute_fetchall(
                f"""
                INSERT INTO users ({_USER_COLUMNS}) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = excluded.username,
                    current_topic = excluded.current_topic,
                    current_page = excluded.current_page,
                    created_at = excluded.created_at
                """,
                (
                    user.user_id,
                    user.username,
                    user.current_topic.value,
                    user.current_page,
                    user.created_at.isoformat(),
                ),
            )

    async def save_question(self, user_id: int, question: str, answer: str = "") -> None:
        """Record a registered student's nonempty question."""
        content = _QUESTION.validate_python(question)
        validated_id = _USER_ID.validate_python(user_id)
        async with self._using_connection() as db:
            await db.execute_fetchall(
                "INSERT INTO user_questions (user_id, question, answer, created_at) "
                "VALUES (?, ?, ?, ?)",
                (validated_id, content, answer, datetime.now(UTC).isoformat()),
            )
