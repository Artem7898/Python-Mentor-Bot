"""Exercise concurrency, validation and compatibility at the SQLite boundary."""

import asyncio
import os
import sqlite3
import stat
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.lesson_models import LessonLevel, LessonTopic
from bot.storage import DatabaseManager, OpenQuestionLimitError, QuestionStatus, StorageError
from bot.storage_files import prepare_database_files


def test_registration_and_progress_are_independent_writes(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "data" / "bot.db") as db:
            registrations = await asyncio.gather(
                *(db.get_or_create_user(100, "first") for _ in range(12))
            )
            registration_date = registrations[0].created_at
            assert all(user.created_at == registration_date for user in registrations)
            updated, _ = await asyncio.gather(
                db.update_user_progress(100, LessonTopic.OOP, 1),
                db.get_or_create_user(100, "renamed"),
            )
            assert updated
            user = await db.get_user(100)
            assert user is not None
            assert user.username == "renamed"
            assert user.current_topic == LessonTopic.OOP
            assert user.current_page == 1
            assert user.created_at == registration_date
            assert not await db.update_user_progress(101, LessonTopic.OOP)

    asyncio.run(scenario())


def test_question_is_validated_and_stored_as_data(tmp_path: Path) -> None:
    db_path = tmp_path / "bot.db"
    question = "'); DROP TABLE users; --"

    async def scenario() -> None:
        async with DatabaseManager(db_path) as db:
            await db.get_or_create_user(100)
            with pytest.raises(ValidationError):
                await db.save_question(100, "  ")
            with pytest.raises(ValidationError):
                await db.update_user_progress(100, LessonTopic.OOP, -1)
            with pytest.raises(StorageError):
                await db.save_question(101, "No corresponding student")
            await db.save_question(100, " " + question + " ")
            assert await db.get_user(100) is not None

    asyncio.run(scenario())
    with closing(sqlite3.connect(db_path)) as connection:
        assert connection.execute("SELECT question FROM user_questions").fetchall() == [(question,)]


def test_migration_preserves_legacy_profiles_and_questions(tmp_path: Path) -> None:
    db_path = tmp_path / "bot_data.db"
    with closing(sqlite3.connect(db_path)) as connection:
        connection.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                current_topic TEXT DEFAULT 'basics',
                completed_lessons TEXT DEFAULT '[]',
                test_scores TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                question_text TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            INSERT INTO users (user_id, username, current_topic, completed_lessons)
            VALUES (100, 'old_name', 'oop', '["basics"]');
            INSERT INTO questions (user_id, question_text) VALUES (100, 'Preserved');
            """)

    async def scenario() -> None:
        db = DatabaseManager(db_path)
        await db.init_db()
        async with db:
            student = await db.get_or_create_user(100, "new_name")
            assert student.current_topic == LessonTopic.OOP
            assert student.current_page == 0
            assert await db.get_language(student.user_id) is None
            await db.set_language(student.user_id, "es")
            await db.save_question(student.user_id, "New")
        async with db:
            assert await db.get_user(100) == student
            assert await db.get_language(100) == "es"

    asyncio.run(scenario())
    with closing(sqlite3.connect(db_path)) as connection:
        assert connection.execute("SELECT completed_lessons FROM users").fetchone() == (
            '["basics"]',
        )
        assert connection.execute("SELECT question_text FROM questions").fetchone() == (
            "Preserved",
        )
        assert connection.execute("SELECT question FROM user_questions").fetchone() == ("New",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_language_is_separate_from_progress_and_validated(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "bot.db") as db:
            assert await db.get_language(100) is None
            with pytest.raises(StorageError):
                await db.set_language(100, "en")
            await db.get_or_create_user(100, "student")
            await db.get_or_create_user(101, "another")
            assert await db.get_language(100) is None
            for language in ("ru", "en", "es"):
                await db.set_language(100, language)
                assert await db.get_language(100) == language
            with pytest.raises(ValidationError):
                await db.set_language(100, "fr")
            await db.get_or_create_user(100, "renamed")
            assert await db.update_user_progress(100, LessonTopic.OOP)
            assert await db.get_language(100) == "es"
            assert await db.get_language(101) is None

    asyncio.run(scenario())


def test_question_quota_and_replay_across_connections(tmp_path: Path) -> None:
    db_path = tmp_path / "queue.db"

    async def scenario() -> None:
        async with DatabaseManager(db_path) as first, DatabaseManager(db_path) as second:
            await first.get_or_create_user(100)
            workers = (first, second)

            async def offer(index: int) -> bool:
                try:
                    await workers[index % 2].submit_question(
                        100, "Course question", message_id=str(index), max_open=2
                    )
                except OpenQuestionLimitError:
                    return False
                return True

            inserted = await asyncio.gather(*(offer(index) for index in range(12)))
            assert sum(inserted) == 2
            replay = str(inserted.index(True))
            original = await first.submit_question(100, "Altered replay", message_id=replay)
            assert original.question == "Course question"
            assert len(await first.list_questions(100)) == 2
            assert await first.list_open_questions(limit=1, offset=1) == (
                (await first.list_open_questions())[1],
            )

    asyncio.run(scenario())


def test_mentor_transitions_are_forward_and_answers_are_write_once(tmp_path: Path) -> None:
    async def scenario() -> None:
        async with DatabaseManager(tmp_path / "queue.db") as db:
            await db.get_or_create_user(100)
            question = await db.submit_question(100, "How does this work?")
            assert question.status is QuestionStatus.NEW
            reviewing = await db.set_question_status(question.id, QuestionStatus.IN_REVIEW)
            assert reviewing is not None and reviewing.status is QuestionStatus.IN_REVIEW
            with pytest.raises(ValueError, match="answer is required"):
                await db.set_question_status(question.id, QuestionStatus.ANSWERED)
            with pytest.raises(ValidationError):
                await db.set_question_status(question.id, QuestionStatus.ANSWERED, answer=" ")
            results = await asyncio.gather(
                db.set_question_status(question.id, QuestionStatus.ANSWERED, answer="First"),
                db.set_question_status(question.id, QuestionStatus.ANSWERED, answer="Second"),
            )
            saved = [result for result in results if result is not None]
            assert len(saved) == 1
            assert (await db.get_question(question.id)) == saved[0]
            assert not await db.list_open_questions()
            await db.submit_question(100, "Another question", max_open=1)
            assert await db.list_questions(100, limit=1, offset=1) == (saved[0],)

    asyncio.run(scenario())


def test_study_state_and_owner_scoped_deletion_survive_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "study.db"
    lesson_id = "basics.receipt"

    async def scenario() -> None:
        async with DatabaseManager(db_path) as db:
            assert (await db.get_preferences(100)).compact
            await db.get_or_create_user(100)
            await db.get_or_create_user(101)
            assert await db.record_lesson_visit(100, lesson_id, LessonTopic.BASICS, 1)
            assert await db.complete_lesson(100, lesson_id)
            assert not await db.complete_lesson(100, lesson_id)
            assert await db.set_bookmark(100, lesson_id, bookmarked=True)
            assert not await db.set_bookmark(100, lesson_id, bookmarked=True)
            await db.set_level(100, LessonLevel.INTERMEDIATE)
            await db.set_compact(100, False)
            owned = await db.submit_question(100, "Mine")
            another = await db.submit_question(101, "Theirs")
            assert not await db.delete_question(100, another.id)
            assert await db.delete_question(100, owned.id)
            assert not await db.delete_question(100, owned.id)
            await db.submit_question(100, "Delete this from my profile")

        async with DatabaseManager(db_path) as reopened:
            preferences = await reopened.get_preferences(100)
            assert preferences.level is LessonLevel.INTERMEDIATE
            assert not preferences.compact
            assert await reopened.get_last_lesson(100) == lesson_id
            assert await reopened.list_completed_lessons(100) == (lesson_id,)
            assert await reopened.list_bookmarks(100) == (lesson_id,)
            assert await reopened.set_bookmark(100, lesson_id, bookmarked=False)
            assert not await reopened.list_bookmarks(100)
            await reopened.set_bookmark(100, lesson_id, bookmarked=True)
            assert await reopened.delete_user_data(100)
            assert not await reopened.delete_user_data(100)
            assert await reopened.get_user(100) is None
            assert await reopened.get_last_lesson(100) is None
            assert not await reopened.list_completed_lessons(100)
            assert not await reopened.list_bookmarks(100)
            assert not await reopened.list_questions(100)
            assert await reopened.get_question(another.id) == another

    asyncio.run(scenario())


def test_retention_and_profile_deletion_cover_legacy_question_records(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    old_date = (datetime.now(UTC) - timedelta(days=91)).isoformat()
    fresh_date = datetime.now(UTC).isoformat()

    async def setup_profile() -> int:
        async with DatabaseManager(db_path) as db:
            await db.get_or_create_user(100)
            old_question = await db.submit_question(100, "Old question")
            await db.submit_question(100, "Recent question")
            return old_question.id

    old_question_id = asyncio.run(setup_profile())
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            "CREATE TABLE questions (user_id INTEGER REFERENCES users(id), asked_date TEXT)"
        )
        connection.execute("CREATE TABLE command_logs (user_id INTEGER)")
        connection.executemany(
            "INSERT INTO questions VALUES (?, ?)", [(100, old_date), (100, fresh_date)]
        )
        connection.execute("INSERT INTO command_logs VALUES (100)")
        connection.execute(
            "UPDATE user_questions SET created_at = ? WHERE id = ?", (old_date, old_question_id)
        )

    async def scenario() -> None:
        async with DatabaseManager(db_path) as db:
            assert await db.purge_expired_questions() == 2
            assert await db.get_question(old_question_id) is None
            assert len(await db.list_questions(100)) == 1
            assert await db.delete_user_data(100)

    asyncio.run(scenario())
    with closing(sqlite3.connect(db_path)) as connection:
        assert not connection.execute("SELECT 1 FROM questions").fetchall()
        assert not connection.execute("SELECT 1 FROM command_logs").fetchall()


def test_old_queue_migrates_status_without_changing_question_content(tmp_path: Path) -> None:
    db_path = tmp_path / "old-runtime.db"
    with closing(sqlite3.connect(db_path)) as connection:
        connection.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                current_topic TEXT,
                current_page INTEGER DEFAULT 0,
                created_at TEXT
            );
            CREATE TABLE user_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                question TEXT,
                answer TEXT,
                created_at TEXT
            );
            INSERT INTO users VALUES (100, NULL, 'basics', 0, '2026-01-01T00:00:00');
            INSERT INTO user_questions (user_id, question, answer, created_at) VALUES
                (100, 'Archived answered question', 'Saved reply', '2026-01-01T00:00:00'),
                (100, 'Archived pending question', NULL, '2026-01-02T00:00:00');
            """)

    async def scenario() -> None:
        async with DatabaseManager(db_path) as db:
            pending, answered = await db.list_questions(100)
            assert pending.status is QuestionStatus.NEW and pending.answer == ""
            assert answered.status is QuestionStatus.ANSWERED and answered.answer == "Saved reply"
            assert answered.created_at == answered.updated_at
            assert await db.list_open_questions() == (pending,)
            assert await db.set_question_status(answered.id, QuestionStatus.IN_REVIEW) is None

    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "posix", reason="POSIX ownership and mode bits")
def test_sqlite_files_get_private_modes(tmp_path: Path) -> None:
    database = tmp_path / "data" / "custom.db"
    previous_umask = os.umask(0)
    try:
        prepare_database_files(database)
    finally:
        os.umask(previous_umask)
    assert stat.S_IMODE(database.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(database.stat().st_mode) == 0o600

    database.chmod(0o644)
    sidecar = database.with_name("custom.db-wal")
    sidecar.touch(mode=0o644)
    sidecar.chmod(0o644)
    prepare_database_files(database)
    assert stat.S_IMODE(database.stat().st_mode) == 0o600
    assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="POSIX link checks and mode bits")
def test_shared_directory_and_symbolic_links_are_rejected(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o777)
    with pytest.raises(StorageError, match="private, writable SQLite directory"):
        asyncio.run(DatabaseManager(shared / "unsafe.db").init_db())

    original = tmp_path / "original.db"
    original.write_bytes(b"untouched")
    linked = tmp_path / "linked.db"
    linked.symlink_to(original)
    with pytest.raises(StorageError, match="private, writable SQLite directory"):
        asyncio.run(DatabaseManager(linked).init_db())
    assert original.read_bytes() == b"untouched"
