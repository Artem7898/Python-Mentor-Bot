"""Transactional SQLite schema creation and additive legacy migrations."""

import aiosqlite


async def initialize_schema(db: aiosqlite.Connection) -> None:
    """Add current columns and indexes while retaining the previous data."""
    try:
        await db.execute_fetchall("BEGIN IMMEDIATE")
        await db.execute_fetchall("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                current_topic TEXT NOT NULL,
                current_page INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """)
        await _migrate_users(db)
        await db.execute_fetchall("""
            CREATE TABLE IF NOT EXISTS user_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users (user_id),
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
        await _migrate_questions(db)
        await db.execute_fetchall("""
            CREATE TABLE IF NOT EXISTS lesson_completions (
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                lesson_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (user_id, lesson_id)
            )
            """)
        await db.execute_fetchall("""
            CREATE TABLE IF NOT EXISTS lesson_bookmarks (
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                lesson_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (user_id, lesson_id)
            )
            """)
        await db.commit()
    except BaseException:
        await db.rollback()
        raise


async def _migrate_users(db: aiosqlite.Connection) -> None:
    columns = {row["name"] for row in await db.execute_fetchall("PRAGMA table_xinfo(users)")}
    additions = {
        "current_page": "current_page INTEGER NOT NULL DEFAULT 0",
        "language": "language TEXT CHECK (language IN ('ru', 'en', 'es'))",
        "lesson_level": "lesson_level TEXT CHECK (lesson_level IN "
        "('beginner', 'intermediate', 'professional'))",
        "compact": "compact INTEGER NOT NULL DEFAULT 1 CHECK (compact IN (0, 1))",
        "last_lesson_id": "last_lesson_id TEXT",
    }
    for name, definition in additions.items():
        if name not in columns:
            await db.execute_fetchall(f"ALTER TABLE users ADD COLUMN {definition}")

    legacy_keys = await db.execute_fetchall("PRAGMA foreign_key_list(questions)")
    if "id" not in columns and any(
        row["table"] == "users" and row["to"] == "id" for row in legacy_keys
    ):
        # Keep the earlier initializer's questions and repair its reference to users.id.
        await db.execute_fetchall(
            "ALTER TABLE users ADD COLUMN id INTEGER GENERATED ALWAYS AS (user_id) VIRTUAL"
        )
        await db.execute_fetchall("CREATE UNIQUE INDEX legacy_questions_user_id ON users(id)")


async def _migrate_questions(db: aiosqlite.Connection) -> None:
    question_columns = await db.execute_fetchall("PRAGMA table_info(user_questions)")
    columns = {row["name"] for row in question_columns}
    if "status" not in columns:
        await db.execute_fetchall(
            "ALTER TABLE user_questions ADD COLUMN status TEXT NOT NULL DEFAULT 'new' "
            "CHECK (status IN ('new', 'in_review', 'answered'))"
        )
        await db.execute_fetchall(
            "UPDATE user_questions SET status = 'answered' WHERE trim(answer) <> ''"
        )
    if "updated_at" not in columns:
        await db.execute_fetchall("ALTER TABLE user_questions ADD COLUMN updated_at TEXT")
        await db.execute_fetchall("UPDATE user_questions SET updated_at = created_at")
    if "source_message" not in columns:
        await db.execute_fetchall("ALTER TABLE user_questions ADD COLUMN source_message TEXT")

    for index in (
        "CREATE UNIQUE INDEX IF NOT EXISTS questions_source_message "
        "ON user_questions(user_id, source_message)",
        "CREATE INDEX IF NOT EXISTS questions_by_user ON user_questions(user_id, id DESC)",
        "CREATE INDEX IF NOT EXISTS open_questions_by_user ON user_questions(user_id) "
        "WHERE status IN ('new', 'in_review')",
        "CREATE INDEX IF NOT EXISTS open_questions_by_id ON user_questions(id) "
        "WHERE status IN ('new', 'in_review')",
        "CREATE INDEX IF NOT EXISTS questions_by_creation ON user_questions(unixepoch(created_at))",
    ):
        await db.execute_fetchall(index)
