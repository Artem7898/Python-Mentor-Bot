"""Exercise concurrency, validation and compatibility at the SQLite boundary."""

import asyncio
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from pydantic import ValidationError

from bot.lessons import LessonTopic
from bot.storage import DatabaseManager, StorageError


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
