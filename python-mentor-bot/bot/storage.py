"""Asynchronous SQLite storage for students' progress, preferences and questions."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from sqlite3 import Error as SQLiteError
from sqlite3 import Row
from types import TracebackType
from typing import Annotated, Literal, Self

import aiosqlite
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter, ValidationError

from bot.config import DEFAULT_DATABASE_PATH
from bot.lesson_models import LessonLevel, LessonTopic
from bot.storage_files import prepare_database_files
from bot.storage_schema import initialize_schema

type UserId = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]
type PageNumber = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]
type QuestionText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=4096)
]
type Parameters = tuple[int | str | None, ...]
type Language = Literal["ru", "en", "es"]
type LessonId = Annotated[
    str, StringConstraints(strict=True, pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
]
type SourceMessage = Annotated[
    str, StringConstraints(strict=True, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
]
type QueryLimit = Annotated[int, Field(strict=True, gt=0, le=100)]
type RetentionDays = Annotated[int, Field(strict=True, gt=0, le=36_525)]

_USER_ID = TypeAdapter(UserId)
_PAGE = TypeAdapter(PageNumber)
_QUESTION = TypeAdapter(QuestionText, config=ConfigDict(hide_input_in_errors=True))
_LANGUAGE = TypeAdapter(Language, config=ConfigDict(hide_input_in_errors=True))
_LESSON_ID = TypeAdapter(LessonId)
_SOURCE_MESSAGE = TypeAdapter(SourceMessage | None)
_LIMIT = TypeAdapter(QueryLimit)
_RETENTION_DAYS = TypeAdapter(RetentionDays)
_COMPACT = TypeAdapter(bool, config=ConfigDict(strict=True))
_USER_COLUMNS = "user_id, username, current_topic, current_page, created_at"
_QUESTION_COLUMNS = (
    "id, user_id, question, COALESCE(answer, '') AS answer, status, created_at, updated_at"
)


class StorageError(RuntimeError):
    """Raised when student data cannot be persisted or read."""


class OpenQuestionLimitError(StorageError):
    """The learner has reached the maximum pending question count."""


class QuestionStatus(StrEnum):
    """Lifecycle of a submitted question."""

    NEW = "new"
    IN_REVIEW = "in_review"
    ANSWERED = "answered"


class Question(BaseModel):
    """An item in the learner or mentor question queue."""

    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    id: int
    user_id: UserId
    question: str = Field(repr=False)
    answer: str = Field(repr=False)
    status: QuestionStatus
    created_at: datetime
    updated_at: datetime


class LearnerPreferences(BaseModel):
    """Curriculum level and display preferences."""

    model_config = ConfigDict(frozen=True)

    level: LessonLevel | None = None
    compact: bool = True


type LessonRecordTable = Literal["lesson_completions", "lesson_bookmarks"]


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
        self._operation_lock = asyncio.Lock()

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
            await asyncio.to_thread(prepare_database_files, self.path)
            async with aiosqlite.connect(self.path, isolation_level=None, timeout=5) as db:
                db.row_factory = Row
                await db.execute_fetchall("PRAGMA foreign_keys = ON")
                await db.execute_fetchall("PRAGMA trusted_schema = OFF")
                await db.execute_fetchall("PRAGMA secure_delete = ON")
                if initialize:
                    await initialize_schema(db)
                yield db
        except PermissionError as exc:
            raise StorageError("Use a private, writable SQLite directory.") from exc
        except (OSError, SQLiteError) as exc:
            raise StorageError("SQLite operation failed.") from exc

    @asynccontextmanager
    async def _using_connection(self) -> AsyncGenerator[aiosqlite.Connection]:
        try:
            async with self._operation_lock:
                if self._connection is None:
                    async with self._open() as db:
                        yield db
                else:
                    yield self._connection
        except SQLiteError as exc:
            raise StorageError("SQLite operation failed.") from exc

    @asynccontextmanager
    async def _transaction(self) -> AsyncGenerator[aiosqlite.Connection]:
        async with self._using_connection() as db:
            try:
                await db.execute_fetchall("BEGIN IMMEDIATE")
                yield db
                await db.commit()
            except BaseException:
                await db.rollback()
                raise

    async def init_db(self) -> None:
        """Initialize tables and migrate a database created by an older release."""
        if self._connection is None:
            async with self._open(initialize=True):
                pass

    async def _read_one[Model: BaseModel](
        self, model: type[Model], sql: str, parameters: Parameters
    ) -> Model | None:
        return next(iter(await self._read_all(model, sql, parameters)), None)

    async def _read_all[Model: BaseModel](
        self, model: type[Model], sql: str, parameters: Parameters
    ) -> tuple[Model, ...]:
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(sql, parameters)
        try:
            return tuple(model.model_validate(dict(row)) for row in rows)
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

    async def get_preferences(self, user_id: int) -> LearnerPreferences:
        """Read the learner's presentation settings with defaults for a fresh account."""
        preferences = await self._read_one(
            LearnerPreferences,
            "SELECT lesson_level AS level, compact FROM users WHERE user_id = ?",
            (_USER_ID.validate_python(user_id),),
        )
        return preferences if preferences is not None else LearnerPreferences()

    async def set_level(self, user_id: int, level: LessonLevel | None) -> None:
        """Select a level for a registered learner or remove the level filter."""
        value = LessonLevel(level).value if level is not None else None
        await self._set_preference(user_id, "lesson_level", value)

    async def set_compact(self, user_id: int, compact: bool) -> None:
        """Set the registered learner's compact rendering preference."""
        await self._set_preference(user_id, "compact", int(_COMPACT.validate_python(compact)))

    async def _set_preference(
        self, user_id: int, column: Literal["lesson_level", "compact"], value: str | int | None
    ) -> None:
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                f"UPDATE users SET {column} = ? WHERE user_id = ? RETURNING user_id",
                (value, _USER_ID.validate_python(user_id)),
            )
        if next(iter(rows), None) is None:
            raise StorageError("Register the student before changing a preference.")

    async def record_lesson_visit(
        self, user_id: int, lesson_id: str, topic: LessonTopic, page: int
    ) -> bool:
        """Save the stable lesson ID and its current coordinates in a single write."""
        parameters = (
            _LESSON_ID.validate_python(lesson_id),
            topic.value,
            _PAGE.validate_python(page),
            _USER_ID.validate_python(user_id),
        )
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                "UPDATE users SET last_lesson_id = ?, current_topic = ?, current_page = ? "
                "WHERE user_id = ? RETURNING user_id",
                parameters,
            )
        return next(iter(rows), None) is not None

    async def get_last_lesson(self, user_id: int) -> str | None:
        """Return the last recorded stable lesson ID if one has been saved."""
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                "SELECT last_lesson_id FROM users WHERE user_id = ?",
                (_USER_ID.validate_python(user_id),),
            )
        row = next(iter(rows), None)
        return row["last_lesson_id"] if row is not None else None

    async def complete_lesson(self, user_id: int, lesson_id: str) -> bool:
        """Mark the lesson complete and return whether a new entry was recorded."""
        return await self._save_lesson_record("lesson_completions", user_id, lesson_id)

    async def set_bookmark(self, user_id: int, lesson_id: str, *, bookmarked: bool) -> bool:
        """Set the selected bookmark state and return whether it changed."""
        if bookmarked:
            return await self._save_lesson_record("lesson_bookmarks", user_id, lesson_id)
        async with self._using_connection() as db:
            return bool(
                await _delete_rows(
                    db,
                    "DELETE FROM lesson_bookmarks WHERE user_id = ? AND lesson_id = ?",
                    (_USER_ID.validate_python(user_id), _LESSON_ID.validate_python(lesson_id)),
                )
            )

    async def _save_lesson_record(
        self, table: LessonRecordTable, user_id: int, lesson_id: str
    ) -> bool:
        parameters = (
            _USER_ID.validate_python(user_id),
            _LESSON_ID.validate_python(lesson_id),
            datetime.now(UTC).isoformat(),
        )
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                f"INSERT INTO {table} (user_id, lesson_id, recorded_at) VALUES (?, ?, ?) "
                "ON CONFLICT (user_id, lesson_id) DO NOTHING RETURNING lesson_id",
                parameters,
            )
        return next(iter(rows), None) is not None

    async def list_completed_lessons(self, user_id: int) -> tuple[str, ...]:
        """Return the learner's completed lesson IDs, newest first."""
        return await self._list_lesson_records("lesson_completions", user_id)

    async def list_bookmarks(self, user_id: int) -> tuple[str, ...]:
        """Return the learner's bookmarked lesson IDs, newest first."""
        return await self._list_lesson_records("lesson_bookmarks", user_id)

    async def _list_lesson_records(self, table: LessonRecordTable, user_id: int) -> tuple[str, ...]:
        async with self._using_connection() as db:
            rows = await db.execute_fetchall(
                f"SELECT lesson_id FROM {table} WHERE user_id = ? "
                "ORDER BY recorded_at DESC, lesson_id",
                (_USER_ID.validate_python(user_id),),
            )
        return tuple(row["lesson_id"] for row in rows)

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
        """Store a question, optionally importing an already prepared answer."""
        if not answer:
            await self.submit_question(user_id, question)
            return
        now = datetime.now(UTC).isoformat()
        parameters = (
            _USER_ID.validate_python(user_id),
            _QUESTION.validate_python(question),
            _QUESTION.validate_python(answer),
            now,
            now,
        )
        async with self._using_connection() as db:
            await db.execute_fetchall(
                "INSERT INTO user_questions (user_id, question, answer, status, created_at, "
                "updated_at) VALUES (?, ?, ?, 'answered', ?, ?)",
                parameters,
            )

    async def submit_question(
        self,
        user_id: int,
        question: str,
        *,
        message_id: str | None = None,
        max_open: int = 5,
    ) -> Question:
        """Insert under the open-question quota or return the already received message."""
        parameters = (
            _USER_ID.validate_python(user_id),
            _QUESTION.validate_python(question),
            _SOURCE_MESSAGE.validate_python(message_id),
            datetime.now(UTC).isoformat(),
            _LIMIT.validate_python(max_open),
        )
        saved = await self._read_one(
            Question,
            f"""
            WITH incoming(user_id, question, message_id, received_at, max_open) AS (
                VALUES (?, ?, ?, ?, ?)
            )
            INSERT INTO user_questions
                (user_id, question, answer, created_at, updated_at, status, source_message)
            SELECT incoming.user_id, question, '', received_at, received_at, 'new', message_id
            FROM incoming
            WHERE EXISTS (
                SELECT 1 FROM user_questions AS existing
                WHERE existing.user_id = incoming.user_id
                  AND existing.source_message = incoming.message_id
            ) OR (
                SELECT count(*) FROM user_questions AS pending
                WHERE pending.user_id = incoming.user_id
                  AND pending.status IN ('new', 'in_review')
            ) < incoming.max_open
            ON CONFLICT (user_id, source_message) DO UPDATE SET
                source_message = excluded.source_message
            RETURNING {_QUESTION_COLUMNS}
            """,
            parameters,
        )
        if saved is None:
            raise OpenQuestionLimitError("The student has reached the open-question limit.")
        return saved

    async def list_questions(
        self, user_id: int, *, limit: int = 10, offset: int = 0
    ) -> tuple[Question, ...]:
        """Return the learner's most recent questions in any status."""
        return await self._read_all(
            Question,
            f"SELECT {_QUESTION_COLUMNS} FROM user_questions WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (
                _USER_ID.validate_python(user_id),
                _LIMIT.validate_python(limit),
                _PAGE.validate_python(offset),
            ),
        )

    async def list_open_questions(
        self, *, limit: int = 10, offset: int = 0
    ) -> tuple[Question, ...]:
        """Return the oldest pending entries in the mentor review queue."""
        return await self._read_all(
            Question,
            f"SELECT {_QUESTION_COLUMNS} FROM user_questions "
            "WHERE status IN ('new', 'in_review') ORDER BY id LIMIT ? OFFSET ?",
            (_LIMIT.validate_python(limit), _PAGE.validate_python(offset)),
        )

    async def get_question(self, question_id: int) -> Question | None:
        """Read a question by ID for an authorized caller."""
        return await self._read_one(
            Question,
            f"SELECT {_QUESTION_COLUMNS} FROM user_questions WHERE id = ?",
            (_USER_ID.validate_python(question_id),),
        )

    async def set_question_status(
        self, question_id: int, status: QuestionStatus, *, answer: str | None = None
    ) -> Question | None:
        """Admit valid forward transitions without overwriting an answered question."""
        target = QuestionStatus(status)
        if target is QuestionStatus.ANSWERED:
            if answer is None:
                raise ValueError("An answer is required to close a question.")
            answer = _QUESTION.validate_python(answer)
        elif answer is not None:
            raise ValueError("An answer is only saved when closing a question.")
        allowed = "('new', 'in_review')" if target is QuestionStatus.ANSWERED else "('new')"
        return await self._read_one(
            Question,
            f"UPDATE user_questions SET status = ?, answer = COALESCE(?, answer), updated_at = ? "
            f"WHERE id = ? AND status IN {allowed} AND status <> ? "
            f"RETURNING {_QUESTION_COLUMNS}",
            (
                target.value,
                answer,
                datetime.now(UTC).isoformat(),
                _USER_ID.validate_python(question_id),
                target.value,
            ),
        )

    async def delete_question(self, user_id: int, question_id: int) -> bool:
        """Delete a question only when it belongs to the authenticated learner."""
        async with self._using_connection() as db:
            return bool(
                await _delete_rows(
                    db,
                    "DELETE FROM user_questions WHERE user_id = ? AND id = ?",
                    (_USER_ID.validate_python(user_id), _USER_ID.validate_python(question_id)),
                )
            )

    async def delete_user_data(self, user_id: int) -> bool:
        """Atomically delete the specified learner's current and known legacy records."""
        parameters = (_USER_ID.validate_python(user_id),)
        async with self._transaction() as db:
            deleted = await _delete_rows(
                db, "DELETE FROM user_questions WHERE user_id = ?", parameters
            )
            for table, sql in (
                ("questions", "DELETE FROM questions WHERE user_id = ?"),
                ("command_logs", "DELETE FROM command_logs WHERE user_id = ?"),
            ):
                tables = await db.execute_fetchall(
                    "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?", (table,)
                )
                if next(iter(tables), None) is not None:
                    deleted += await _delete_rows(db, sql, parameters)
            # Cascading foreign keys remove completions and bookmarks.
            deleted += await _delete_rows(db, "DELETE FROM users WHERE user_id = ?", parameters)
        return deleted > 0

    async def purge_expired_questions(self, retention_days: int = 90) -> int:
        """Delete questions older than the given age, including known legacy records."""
        days = _RETENTION_DAYS.validate_python(retention_days)
        cutoff = int((datetime.now(UTC) - timedelta(days=days)).timestamp())
        async with self._transaction() as db:
            deleted = await _delete_rows(
                db, "DELETE FROM user_questions WHERE unixepoch(created_at) < ?", (cutoff,)
            )
            columns = await db.execute_fetchall("PRAGMA table_info(questions)")
            if any(row["name"] == "asked_date" for row in columns):
                deleted += await _delete_rows(
                    db, "DELETE FROM questions WHERE unixepoch(asked_date) < ?", (cutoff,)
                )
        return deleted


async def _delete_rows(db: aiosqlite.Connection, sql: str, parameters: Parameters) -> int:
    """Count deleted rows without loading them into memory."""
    async with db.execute(sql, parameters) as cursor:
        return cursor.rowcount
