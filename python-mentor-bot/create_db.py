#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime


def create_database():
    """Создание новой базы данных."""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            current_topic TEXT DEFAULT 'basics',
            completed_lessons TEXT DEFAULT '[]',
            test_scores TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Создаем таблицу для логирования команд
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Создаем таблицу вопросов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        question_text TEXT NOT NULL,
        answer_text TEXT,
        asked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        answered_date TIMESTAMP,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Создаем таблицу настроек
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # Вставляем начальные настройки
    cursor.execute('''
    INSERT OR IGNORE INTO settings (key, value) VALUES
    ('bot_version', '1.0.0'),
    ('maintenance_mode', 'false')
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных создана успешно!")


if __name__ == "__main__":
    create_database()