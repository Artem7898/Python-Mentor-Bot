#!/usr/bin/env python3
"""
Python Mentor Bot - образовательный бот для изучения Python
Объясняет работу с Python, предоставляет примеры кода для Windows и Linux
"""

from __future__ import annotations

import asyncio
import logging
import html
import re
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import ClassVar, Optional, List, Dict, Any

import aiosqlite
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from dotenv import dotenv_values
from pydantic import BaseModel, Field


# ---------- Состояния для диалогов ----------
class UserState(StatesGroup):
    """Состояния пользователя"""
    waiting_code_example = State()
    waiting_question = State()


# ---------- Утилиты форматирования ----------
def escape_html(text: str) -> str:
    """Экранирование HTML символов"""
    return html.escape(text)


def format_code(code: str) -> str:
    """Форматирование кода для Telegram"""
    return f"<pre><code class='python'>{escape_html(code)}</code></pre>"


def format_explanation(text: str) -> str:
    """Форматирование объяснения"""
    return f"<i>{escape_html(text)}</i>"


# ---------- ENUM тем ----------
class LessonTopic(str, Enum):
    BASICS = "basics"
    OOP = "oop"
    FILES = "files"
    TOOLS = "tools"
    FRAMEWORKS = "frameworks"
    DATASCIENCE = "datascience"
    SYNTAX = "syntax"
    ASYNC = "async"
    TEST = "test"
    INSTALL = "install"


# ---------- Конфигурация бота ----------
class BotConfig(BaseModel):
    """Конфигурация бота"""
    token: str
    admin_ids: List[int] = []
    debug: bool = False


# ---------- Уроки с подробными объяснениями ----------
class LessonManager:
    """Менеджер уроков с детальными объяснениями"""

    lessons: ClassVar[Dict[str, Dict]] = {
        LessonTopic.BASICS: {
            "title": "📚 Основы Python",
            "content": [
                {
                    "title": "Введение в Python",
                    "explanation": (
                        "Python - интерпретируемый язык программирования высокого уровня.\n"
                        "Используется для веб-разработки, анализа данных, машинного обучения, автоматизации и многого другого.\n\n"
                        "<b>Особенности:</b>\n"
                        "• Простой и понятный синтаксис\n"
                        "• Динамическая типизация\n"
                        "• Большая стандартная библиотека\n"
                        "• Кроссплатформенность (работает на Windows, Linux, macOS)\n\n"
                        "<b>Первый запуск Python:</b>"
                    ),
                    "windows_code": """# Для Windows:
1. Скачайте Python с python.org
2. Установите с галочкой "Add Python to PATH"
3. Откройте командную строку (cmd)
4. Введите: python --version
5. Чтобы запустить интерпретатор: python""",
                    "linux_code": """# Для Linux:
1. Обычно Python уже установлен
2. Проверьте версию: python3 --version
3. Если нет Python: sudo apt install python3
4. Запуск интерпретатора: python3""",
                    "example_code": """# Ваша первая программа на Python
print("Привет, мир!")

# Переменные
name = "Алексей"
age = 25
print(f"Меня зовут {name}, мне {age} лет")

# Типы данных
number = 42                 # Целое число
pi = 3.14159               # Число с плавающей точкой
text = "Python"            # Строка
is_true = True             # Булево значение
numbers = [1, 2, 3, 4, 5]  # Список

# Ввод данных
user_input = input("Введите ваше имя: ")
print(f"Привет, {user_input}!")"""
                },
                {
                    "title": "Основные конструкции",
                    "explanation": "Условные операторы и циклы - основа программирования",
                    "example_code": """# Условный оператор if
age = 18

if age < 13:
    print("Ребенок")
elif 13 <= age < 18:
    print("Подросток")
else:
    print("Взрослый")

# Цикл for
for i in range(5):  # От 0 до 4
    print(f"Итерация {i}")

# Цикл while
count = 0
while count < 3:
    print(f"Счетчик: {count}")
    count += 1

# Функции
def greet(name="Гость"):
    '''Функция приветствия'''
    return f"Привет, {name}!"

print(greet("Мария"))
print(greet())"""
                }
            ]
        },
        LessonTopic.SYNTAX: {
            "title": "🧠 Синтаксис Python",
            "content": [
                {
                    "title": "Современный синтаксис",
                    "explanation": "Python постоянно развивается, добавляя новые возможности синтаксиса",
                    "example_code": """# F-строки (Python 3.6+)
name = "Анна"
age = 30
height = 1.75
message = f"{name}, {age} лет, рост {height:.2f} м"
print(message)  # Анна, 30 лет, рост 1.75 м

# Оператор := (моржовый оператор, Python 3.8+)
# Позволяет присваивать значения в выражениях
if (n := len([1, 2, 3])) > 2:
    print(f"Длина списка: {n}")

# Match-case (Python 3.10+)
def handle_http_status(code: int) -> str:
    match code:
        case 200:
            return "Успех"
        case 404:
            return "Не найдено"
        case 500:
            return "Ошибка сервера"
        case _:
            return "Неизвестный статус"

print(handle_http_status(200))

# Аннотации типов
def add_numbers(a: int, b: int) -> int:
    return a + b

# Генераторы списков и словарей
squares = [x**2 for x in range(10) if x % 2 == 0]
print(squares)  # [0, 4, 16, 36, 64]"""
                }
            ]
        },
        LessonTopic.OOP: {
            "title": "🏛️ Объектно-ориентированное программирование",
            "content": [
                {
                    "title": "Основы ООП",
                    "explanation": (
                        "ООП позволяет организовать код в виде объектов, "
                        "которые объединяют данные и методы для работы с ними\n\n"
                        "<b>4 основных принципа ООП:</b>\n"
                        "1. <b>Инкапсуляция</b> - сокрытие деталей реализации\n"
                        "2. <b>Наследование</b> - создание новых классов на основе существующих\n"
                        "3. <b>Полиморфизм</b> - возможность объектов с одинаковым интерфейсом иметь разную реализацию\n"
                        "4. <b>Абстракция</b> - работа на уровне понятий, а не деталей"
                    ),
                    "example_code": """# Базовый пример класса
class Person:
    '''Класс, представляющий человека'''

    def __init__(self, name: str, age: int):
        '''Конструктор класса'''
        self.name = name  # Публичный атрибут
        self._age = age   # Защищенный атрибут (соглашение)
        self.__secret = "секрет"  # Приватный атрибут

    def introduce(self) -> str:
        '''Метод для представления'''
        return f"Меня зовут {self.name}, мне {self._age} лет"

    # Свойства (property)
    @property
    def age(self) -> int:
        '''Getter для возраста'''
        return self._age

    @age.setter
    def age(self, value: int):
        '''Setter для возраста с проверкой'''
        if value < 0 or value > 150:
            raise ValueError("Некорректный возраст")
        self._age = value

# Создание объекта
person1 = Person("Иван", 25)
print(person1.introduce())
person1.age = 30  # Используем setter
print(f"Новый возраст: {person1.age}")

# Наследование
class Student(Person):
    '''Класс Студент, наследуется от Person'''

    def __init__(self, name: str, age: int, student_id: str):
        super().__init__(name, age)  # Вызов конструктора родителя
        self.student_id = student_id

    def study(self):
        return f"{self.name} учится"

# Полиморфизм
class Teacher(Person):
    def work(self):
        return "Учит студентов"

class Engineer(Person):
    def work(self):
        return "Строит мосты"

def show_work(person):
    '''Функция работает с любым объектом, у которого есть метод work()'''
    if hasattr(person, 'work'):
        return person.work()
    return "Неизвестная профессия"

teacher = Teacher("Анна", 40)
engineer = Engineer("Петр", 35)

print(show_work(teacher))   # Учит студентов
print(show_work(engineer))  # Строит мосты"""
                }
            ]
        },
        LessonTopic.FILES: {
            "title": "📁 Работа с файлами",
            "content": [
                {
                    "title": "Чтение и запись файлов",
                    "explanation": (
                        "Работа с файлами необходима для:\n"
                        "• Сохранения данных между запусками программы\n"
                        "• Конфигурации приложений\n"
                        "• Обработки больших объемов данных\n"
                        "• Логирования событий"
                    ),
                    "example_code": """# Открытие файла на чтение
with open('example.txt', 'r', encoding='utf-8') as file:
    content = file.read()
    print("Содержимое файла:")
    print(content)

# Построчное чтение
with open('example.txt', 'r', encoding='utf-8') as file:
    for line_num, line in enumerate(file, 1):
        print(f"Строка {line_num}: {line.strip()}")

# Запись в файл
with open('output.txt', 'w', encoding='utf-8') as file:
    file.write("Первая строка\\n")
    file.write("Вторая строка\\n")
    print("Файл записан")

# Добавление в существующий файл
with open('output.txt', 'a', encoding='utf-8') as file:
    file.write("Добавленная строка\\n")

# Работа с JSON файлами
import json

data = {
    "name": "Алексей",
    "age": 30,
    "skills": ["Python", "JavaScript", "SQL"]
}

# Запись в JSON
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Чтение из JSON
with open('data.json', 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
    print(f"Имя: {loaded_data['name']}")
    print(f"Навыки: {', '.join(loaded_data['skills'])}")

# Работа с CSV файлами
import csv

# Запись CSV
with open('users.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Имя', 'Возраст', 'Город'])
    writer.writerow(['Анна', 25, 'Москва'])
    writer.writerow(['Иван', 30, 'Санкт-Петербург'])

# Чтение CSV
with open('users.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)"""
                }
            ]
        },
        LessonTopic.FRAMEWORKS: {
            "title": "🚀 Веб-фреймворки",
            "content": [
                {
                    "title": "Flask - микрофреймворк",
                    "explanation": "Flask - простой и легковесный фреймворк для создания веб-приложений",
                    "windows_install": """# Установка Flask на Windows:
1. Откройте командную строку (cmd)
2. Создайте виртуальное окружение:
   python -m venv venv
3. Активируйте его:
   venv\\Scripts\\activate
4. Установите Flask:
   pip install flask
5. Проверьте установку:
   python -c "import flask; print(flask.__version__)" """,
                    "linux_install": """# Установка Flask на Linux:
1. Откройте терминал
2. Создайте виртуальное окружение:
   python3 -m venv venv
3. Активируйте его:
   source venv/bin/activate
4. Установите Flask:
   pip install flask
5. Проверьте установку:
   python3 -c "import flask; print(flask.__version__)" """,
                    "example_code": """# Пример простого Flask приложения
# app.py
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Главная страница
@app.route('/')
def home():
    return '<h1>Добро пожаловать!</h1>'

# Страница с параметром
@app.route('/user/<username>')
def show_user(username):
    return f'<h1>Профиль пользователя {username}</h1>'

# API endpoint
@app.route('/api/data')
def get_data():
    data = {
        'users': ['Алексей', 'Мария', 'Иван'],
        'count': 3,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(data)

# HTML форма
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        return f'Спасибо, {name}! Ваше сообщение получено.'
    return '''
        <form method="POST">
            <input type="text" name="name" placeholder="Ваше имя">
            <button type="submit">Отправить</button>
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Запуск приложения:
# Windows: python app.py
# Linux: python3 app.py"""
                },
                {
                    "title": "Django - полноценный фреймворк",
                    "explanation": "Django - мощный фреймворк для создания сложных веб-приложений",
                    "windows_install": """# Установка Django на Windows:
1. python -m venv venv
2. venv\\Scripts\\activate
3. pip install django
4. django-admin --version""",
                    "linux_install": """# Установка Django на Linux:
1. python3 -m venv venv
2. source venv/bin/activate
3. pip install django
4. django-admin --version""",
                    "example_code": """# Создание проекта Django:
# Windows/Linux: django-admin startproject myproject
# cd myproject

# Создание приложения:
# python manage.py startapp myapp

# models.py - определение моделей данных
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# views.py - обработка запросов
from django.shortcuts import render
from .models import Product

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})

# Запуск сервера:
# python manage.py runserver"""
                }
            ]
        },
        LessonTopic.TOOLS: {
            "title": "🛠️ Инструменты разработчика",
            "content": [
                {
                    "title": "pip - менеджер пакетов",
                    "explanation": "pip устанавливает и управляет Python пакетами",
                    "windows_code": """# Основные команды pip на Windows:

# Установка пакета
pip install requests

# Установка конкретной версии
pip install django==4.2.0

# Установка из requirements.txt
pip install -r requirements.txt

# Обновление пакета
pip install --upgrade package_name

# Просмотр установленных пакетов
pip list

# Удаление пакета
pip uninstall package_name

# Поиск пакета
pip search "web framework" """,
                    "linux_code": """# На Linux используйте pip3:

pip3 install requests
pip3 list
pip3 uninstall package_name""",
                    "example_code": """# Файл requirements.txt содержит зависимости проекта
# requirements.txt
django==4.2.0
requests>=2.28.0
pandas
numpy
matplotlib

# Установка всех зависимостей
pip install -r requirements.txt"""
                },
                {
                    "title": "Git - система контроля версий",
                    "explanation": "Git отслеживает изменения в коде и позволяет работать в команде",
                    "windows_install": """# Установка Git на Windows:
1. Скачайте с git-scm.com
2. Запустите установщик
3. Используйте Git Bash или командную строку""",
                    "linux_install": """# Установка Git на Linux:
sudo apt update
sudo apt install git
git --version""",
                    "example_code": """# Основные команды Git:

# Инициализация репозитория
git init

# Проверка статуса
git status

# Добавление файлов
git add .              # Все файлы
git add file.py        # Конкретный файл

# Коммит изменений
git commit -m "Добавлен новый функционал"

# Просмотр истории
git log
git log --oneline

# Работа с ветками
git branch                    # Список веток
git branch feature-new        # Создание ветки
git checkout feature-new      # Переключение на ветку
git checkout -b feature-new   # Создать и переключиться

# Слияние веток
git merge feature-new

# Работа с удаленным репозиторием
git remote add origin https://github.com/user/repo.git
git push -u origin main      # Первая отправка
git push                     # Отправка изменений
git pull                     # Загрузка изменений
git clone https://github.com/user/repo.git

# .gitignore - файл для исключения файлов
__pycache__/
*.pyc
.env
venv/
*.log"""
                }
            ]
        },
        LessonTopic.DATASCIENCE: {
            "title": "📊 Data Science",
            "content": [
                {
                    "title": "NumPy и Pandas",
                    "explanation": "Библиотеки для научных вычислений и анализа данных",
                    "install_code": """# Установка библиотек для Data Science
pip install numpy pandas matplotlib seaborn scikit-learn""",
                    "example_code": """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# NumPy - работа с массивами
arr = np.array([1, 2, 3, 4, 5])
matrix = np.array([[1, 2, 3], [4, 5, 6]])

print("Массив:", arr)
print("Матрица:\\n", matrix)
print("Среднее:", np.mean(arr))
print("Сумма:", np.sum(arr))

# Pandas - анализ данных
data = {
    'Имя': ['Алексей', 'Мария', 'Иван', 'Ольга'],
    'Возраст': [25, 30, 22, 28],
    'Зарплата': [70000, 85000, 60000, 75000],
    'Город': ['Москва', 'СПб', 'Москва', 'Казань']
}

df = pd.DataFrame(data)
print("\\nDataFrame:")
print(df)
print("\\nИнформация о данных:")
print(df.info())
print("\\nСтатистика:")
print(df.describe())

# Фильтрация
print("\\nЛюди старше 25:")
print(df[df['Возраст'] > 25])

# Группировка
print("\\nСредняя зарплата по городам:")
print(df.groupby('Город')['Зарплата'].mean())

# Визуализация
plt.figure(figsize=(10, 6))
plt.bar(df['Имя'], df['Зарплата'], color='skyblue')
plt.title('Зарплаты сотрудников')
plt.xlabel('Имя')
plt.ylabel('Зарплата')
plt.grid(True, alpha=0.3)
plt.show()"""
                },
                {
                    "title": "Машинное обучение",
                    "explanation": "Базовый пример машинного обучения с scikit-learn",
                    "example_code": """from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Загрузка данных
iris = load_iris()
X = iris.data
y = iris.target

print(f"Количество образцов: {X.shape[0]}")
print(f"Количество признаков: {X.shape[1]}")
print(f"Названия признаков: {iris.feature_names}")
print(f"Классы: {iris.target_names}")

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Обучение модели
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Предсказания
y_pred = model.predict(X_test)

# Оценка модели
accuracy = accuracy_score(y_test, y_pred)
print(f"\\nТочность модели: {accuracy:.2%}")

# Важность признаков
importances = model.feature_importances_
for name, importance in zip(iris.feature_names, importances):
    print(f"{name}: {importance:.3f}")"""
                }
            ]
        },
        LessonTopic.ASYNC: {
            "title": "⚡ Асинхронное программирование",
            "content": [
                {
                    "title": "async/await",
                    "explanation": (
                        "Асинхронное программирование позволяет эффективно работать с I/O операциями:\n"
                        "• Сетевые запросы\n"
                        "• Работа с базами данных\n"
                        "• Файловые операции\n"
                        "• Веб-серверы"
                    ),
                    "example_code": """import asyncio
import aiohttp
import time

# Синхронная функция
def sync_fetch(url):
    time.sleep(1)  # Имитация долгой операции
    return f"Данные с {url}"

# Асинхронная функция
async def async_fetch(url):
    await asyncio.sleep(1)  # Асинхронная задержка
    return f"Данные с {url}"

# Основной синхронный подход
def main_sync():
    start = time.time()
    results = []
    for i in range(3):
        results.append(sync_fetch(f"site-{i}.com"))
    print(f"Синхронно: {time.time() - start:.2f} сек")
    return results

# Основной асинхронный подход
async def main_async():
    start = time.time()
    tasks = []
    for i in range(3):
        task = asyncio.create_task(async_fetch(f"site-{i}.com"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    print(f"Асинхронно: {time.time() - start:.2f} сек")
    return results

# Запуск
if __name__ == "__main__":
    # Синхронный запуск
    print("Синхронный запуск:")
    main_sync()

    # Асинхронный запуск
    print("\\nАсинхронный запуск:")
    asyncio.run(main_async())

# Пример с реальными HTTP запросами
async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_multiple_urls():
    urls = [
        'https://api.github.com',
        'https://httpbin.org/get',
        'https://jsonplaceholder.typicode.com/posts/1'
    ]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Асинхронный веб-сервер на FastAPI
# from fastapi import FastAPI
# import asyncio

# app = FastAPI()

# @app.get("/")
# async def read_root():
#     await asyncio.sleep(1)
#     return {"message": "Hello World"}

# @app.get("/items/{item_id}")
# async def read_item(item_id: int):
#     return {"item_id": item_id}"""
                }
            ]
        },
        LessonTopic.INSTALL: {
            "title": "📥 Установка Python",
            "content": [
                {
                    "title": "Windows",
                    "explanation": "Пошаговая установка Python на Windows",
                    "steps": [
                        "1. Скачайте Python с официального сайта: python.org",
                        "2. Запустите установщик",
                        "3. ВНИМАНИЕ: Отметьте галочку 'Add Python to PATH'",
                        "4. Выберите 'Install Now'",
                        "5. После установки откройте командную строку (cmd)",
                        "6. Проверьте установку: python --version",
                        "7. Запустите Python: python"
                    ]
                },
                {
                    "title": "Linux",
                    "explanation": "Установка Python на Linux",
                    "steps": [
                        "1. Откройте терминал",
                        "2. Проверьте установлен ли Python: python3 --version",
                        "3. Если Python не установлен:",
                        "   Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip",
                        "   Fedora: sudo dnf install python3",
                        "   Arch: sudo pacman -S python",
                        "4. Установите pip: sudo apt install python3-pip",
                        "5. Проверьте: python3 --version && pip3 --version"
                    ]
                }
            ]
        }
    }

    @classmethod
    def get_topic_content(cls, topic: LessonTopic, page: int = 0) -> Dict[str, Any]:
        """Получить контент темы"""
        lesson = cls.lessons.get(topic)
        if not lesson or page >= len(lesson["content"]):
            return {}
        return lesson["content"][page]

    @classmethod
    def get_topic_title(cls, topic: LessonTopic) -> str:
        """Получить заголовок темы"""
        lesson = cls.lessons.get(topic)
        return lesson.get("title", "") if lesson else ""

    @classmethod
    def get_total_pages(cls, topic: LessonTopic) -> int:
        """Получить количество страниц в теме"""
        lesson = cls.lessons.get(topic)
        return len(lesson.get("content", [])) if lesson else 0


# ---------- Пользователь ----------
class UserProgress(BaseModel):
    user_id: int
    username: Optional[str] = None
    current_topic: str = LessonTopic.BASICS.value
    current_page: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

    def update_topic(self, topic: LessonTopic, page: int = 0):
        """Обновить текущую тему и страницу"""
        self.current_topic = topic.value
        self.current_page = page


# ---------- БД ----------
class DatabaseManager:
    def __init__(self, db_path: str = "python_mentor.db"):
        self.path = Path(db_path)
        self.path.parent.mkdir(exist_ok=True)

    @asynccontextmanager
    async def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def init_db(self):
        """Инициализация базы данных"""
        async with self.get_connection() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    current_topic TEXT,
                    current_page INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question TEXT,
                    answer TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[UserProgress]:
        """Получить пользователя"""
        async with self.get_connection() as db:
            async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UserProgress(
                        user_id=row["user_id"],
                        username=row["username"],
                        current_topic=row["current_topic"],
                        current_page=row["current_page"],
                        created_at=datetime.fromisoformat(row["created_at"])
                    )
        return None

    async def save_user(self, user: UserProgress):
        """Сохранить пользователя"""
        async with self.get_connection() as db:
            await db.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, current_topic, current_page, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.username,
                user.current_topic,
                user.current_page,
                user.created_at.isoformat()
            ))
            await db.commit()

    async def save_question(self, user_id: int, question: str, answer: str = ""):
        """Сохранить вопрос пользователя"""
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO user_questions (user_id, question, answer, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                question,
                answer,
                datetime.now().isoformat()
            ))
            await db.commit()


# ---------- Клавиатуры ----------
def create_main_keyboard() -> ReplyKeyboardMarkup:
    """Создать основную клавиатуру"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📚 Темы обучения"))
    builder.add(KeyboardButton(text="💻 Пример кода"))
    builder.add(KeyboardButton(text="❓ Задать вопрос"))
    builder.add(KeyboardButton(text="📊 Мой прогресс"))
    builder.add(KeyboardButton(text="📥 Установка Python"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def create_topics_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с темами"""
    topics = [
        (LessonTopic.BASICS, "📚 Основы Python"),
        (LessonTopic.SYNTAX, "🧠 Синтаксис"),
        (LessonTopic.OOP, "🏛️ ООП"),
        (LessonTopic.FILES, "📁 Файлы"),
        (LessonTopic.FRAMEWORKS, "🚀 Фреймворки"),
        (LessonTopic.TOOLS, "🛠️ Инструменты"),
        (LessonTopic.DATASCIENCE, "📊 Data Science"),
        (LessonTopic.ASYNC, "⚡ Асинхронность"),
    ]

    builder = InlineKeyboardBuilder()
    for topic, title in topics:
        builder.button(text=title, callback_data=f"topic:{topic.value}")

    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(2)
    return builder.as_markup()


def create_lesson_navigation(topic: LessonTopic, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру навигации по уроку"""
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    if current_page > 0:
        builder.button(text="⬅️ Назад", callback_data=f"page:{topic.value}:{current_page - 1}")

    builder.button(text=f"{current_page + 1}/{total_pages}", callback_data="current_page")

    if current_page < total_pages - 1:
        builder.button(text="Вперед ➡️", callback_data=f"page:{topic.value}:{current_page + 1}")

    # Дополнительные кнопки
    builder.button(text="📚 Все темы", callback_data="show_topics")
    builder.button(text="💻 Пример кода", callback_data=f"code:{topic.value}:{current_page}")
    builder.button(text="🏠 Главная", callback_data="back_to_main")

    builder.adjust(3, 2, 1)
    return builder.as_markup()


# ---------- Бот ----------
router = Router()
db_manager = DatabaseManager()
lesson_manager = LessonManager()


@router.message(CommandStart())
async def start_command(message: Message):
    """Обработчик команды /start"""
    user = await db_manager.get_user(message.from_user.id)
    if not user:
        user = UserProgress(
            user_id=message.from_user.id,
            username=message.from_user.username,
        )
        await db_manager.save_user(user)

    welcome_text = (
        "👋 <b>Привет! Я Python Mentor Bot</b>\n\n"
        "Я помогу тебе изучить Python от основ до продвинутых тем!\n\n"
        "<b>Что я умею:</b>\n"
        "• 📚 Объяснять основы Python\n"
        "• 💻 Показывать примеры кода\n"
        "• 🏛️ Рассказывать про ООП\n"
        "• 📁 Учить работать с файлами\n"
        "• 🚀 Показывать фреймворки (Flask, Django)\n"
        "• 🛠️ Знакомить с инструментами разработчика\n"
        "• 📊 Объяснять Data Science\n"
        "• ⚡ Рассказывать про асинхронность\n\n"
        "<b>Выбери действие:</b>"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=create_main_keyboard()
    )


@router.message(F.text == "📚 Темы обучения")
async def show_topics(message: Message):
    """Показать все темы"""
    await message.answer(
        "<b>📚 Выбери тему для изучения:</b>",
        parse_mode="HTML",
        reply_markup=create_topics_keyboard()
    )


@router.message(F.text == "💻 Пример кода")
async def show_code_examples(message: Message, state: FSMContext):
    """Показать примеры кода"""
    await message.answer(
        "<b>💻 Примеры кода</b>\n\n"
        "Выбери тему для которой хочешь увидеть пример кода:",
        parse_mode="HTML",
        reply_markup=create_topics_keyboard()
    )


@router.message(F.text == "📥 Установка Python")
async def show_installation(message: Message):
    """Показать инструкцию по установке Python"""
    topic = LessonTopic.INSTALL
    content = lesson_manager.get_topic_content(topic, 0)

    text = f"<b>{lesson_manager.get_topic_title(topic)}</b>\n\n"
    text += f"<b>{content['title']}</b>\n\n"
    text += f"{content['explanation']}\n\n"

    if 'steps' in content:
        text += "<b>Шаги установки:</b>\n"
        for step in content['steps']:
            text += f"• {step}\n"

    # Кнопка для Linux установки
    builder = InlineKeyboardBuilder()
    builder.button(text="🐧 Установка на Linux", callback_data=f"topic:{LessonTopic.INSTALL.value}:1")
    builder.button(text="📚 Все темы", callback_data="show_topics")
    builder.button(text="🏠 Главная", callback_data="back_to_main")
    builder.adjust(1)

    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.message(F.text == "❓ Задать вопрос")
async def ask_question(message: Message, state: FSMContext):
    """Задать вопрос"""
    await message.answer(
        "<b>❓ Задай свой вопрос по Python</b>\n\n"
        "Напиши свой вопрос, и я постараюсь на него ответить:",
        parse_mode="HTML"
    )
    await state.set_state(UserState.waiting_question)


@router.message(UserState.waiting_question)
async def handle_question(message: Message, state: FSMContext):
    """Обработка вопроса пользователя"""
    question = message.text
    await db_manager.save_question(message.from_user.id, question)

    # Здесь можно добавить логику ответа на вопросы
    # Пока просто подтверждаем получение
    await message.answer(
        "<b>✅ Вопрос получен!</b>\n\n"
        "Я записал твой вопрос и скоро на него отвечу.\n"
        "А пока можешь изучить другие темы:",
        parse_mode="HTML",
        reply_markup=create_main_keyboard()
    )
    await state.clear()


@router.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message):
    """Показать прогресс пользователя"""
    user = await db_manager.get_user(message.from_user.id)
    if user:
        topic = LessonTopic(user.current_topic)
        topic_title = lesson_manager.get_topic_title(topic)

        progress_text = (
            f"<b>📊 Твой прогресс</b>\n\n"
            f"👤 Пользователь: {escape_html(user.username or 'Аноним')}\n"
            f"🎯 Текущая тема: {topic_title}\n"
            f"📄 Страница: {user.current_page + 1}\n"
            f"📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            f"<i>Продолжай изучать Python! 🚀</i>"
        )

        await message.answer(
            progress_text,
            parse_mode="HTML",
            reply_markup=create_main_keyboard()
        )


@router.callback_query(F.data.startswith("topic:"))
async def handle_topic_selection(callback: CallbackQuery):
    """Обработка выбора темы"""
    try:
        data_parts = callback.data.split(":")
        topic_value = data_parts[1]
        page = int(data_parts[2]) if len(data_parts) > 2 else 0

        topic = LessonTopic(topic_value)
        content = lesson_manager.get_topic_content(topic, page)

        if not content:
            await callback.answer("Контент не найден")
            return

        # Формируем текст сообщения
        text = f"<b>{lesson_manager.get_topic_title(topic)}</b>\n\n"
        text += f"<b>{content['title']}</b>\n\n"
        text += format_explanation(content['explanation']) + "\n\n"

        # Добавляем код для Windows и Linux если есть
        if 'windows_code' in content:
            text += "<b>💻 Windows:</b>\n"
            text += format_code(content['windows_code']) + "\n\n"

        if 'linux_code' in content:
            text += "<b>🐧 Linux:</b>\n"
            text += format_code(content['linux_code']) + "\n\n"

        if 'install_code' in content:
            text += "<b>📦 Установка:</b>\n"
            text += format_code(content['install_code']) + "\n\n"

        if 'example_code' in content:
            text += "<b>📝 Пример кода:</b>\n"
            text += format_code(content['example_code'])

        if 'steps' in content:
            text += "<b>📋 Шаги:</b>\n"
            for step in content['steps']:
                text += f"• {step}\n"

        # Обновляем пользователя
        user = await db_manager.get_user(callback.from_user.id)
        if user:
            user.update_topic(topic, page)
            await db_manager.save_user(user)

        # Создаем клавиатуру навигации
        total_pages = lesson_manager.get_total_pages(topic)
        keyboard = create_lesson_navigation(topic, page, total_pages)

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("page:"))
async def handle_page_navigation(callback: CallbackQuery):
    """Обработка навигации по страницам"""
    try:
        _, topic_value, page_str = callback.data.split(":")
        page = int(page_str)
        topic = LessonTopic(topic_value)

        # Обрабатываем как выбор темы с указанной страницей
        await handle_topic_selection(callback)

    except Exception as e:
        await callback.answer(f"Ошибка навигации: {str(e)}")


@router.callback_query(F.data.startswith("code:"))
async def handle_code_example(callback: CallbackQuery):
    """Показать только код без объяснений"""
    try:
        _, topic_value, page_str = callback.data.split(":")
        page = int(page_str)
        topic = LessonTopic(topic_value)

        content = lesson_manager.get_topic_content(topic, page)
        if not content or 'example_code' not in content:
            await callback.answer("Пример кода не найден")
            return

        text = f"<b>💻 Пример кода: {content['title']}</b>\n\n"
        text += format_code(content['example_code'])

        # Кнопка для возврата к полному уроку
        builder = InlineKeyboardBuilder()
        builder.button(text="📖 Полный урок", callback_data=f"topic:{topic.value}:{page}")
        builder.button(text="📚 Все темы", callback_data="show_topics")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await callback.answer()

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")


@router.callback_query(F.data == "show_topics")
async def handle_show_topics(callback: CallbackQuery):
    """Показать все темы"""
    await callback.message.edit_text(
        "<b>📚 Выбери тему для изучения:</b>",
        parse_mode="HTML",
        reply_markup=create_topics_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.message.edit_text(
        "<b>🏠 Главное меню</b>\n\n"
        "Выбери действие:",
        parse_mode="HTML",
        reply_markup=create_main_keyboard()
    )
    await callback.answer()


@router.message(F.text)
async def handle_text_message(message: Message):
    """Обработка текстовых сообщений"""
    text = message.text.lower()

    # Простые ответы на частые вопросы
    responses = {
        "привет": "👋 Привет! Я Python Mentor Bot. Используй кнопки меню для навигации.",
        "help": "📋 Используй кнопки меню:\n• 📚 Темы обучения - выбрать тему\n• 💻 Пример кода - посмотреть код\n• ❓ Задать вопрос - получить помощь",
        "python": "🐍 Python - отличный выбор! Начни изучение с раздела 📚 Основы Python",
        "спасибо": "😊 Пожалуйста! Рад помочь в изучении Python!",
        "код": "💻 Примеры кода доступны в каждой теме. Выбери тему и нажми 'Пример кода'",
        "ооп": "🏛️ Объектно-ориентированное программирование - важная тема! Изучи ее в соответствующем разделе.",
        "файлы": "📁 Работа с файлами - основа многих программ. Узнай больше в разделе 'Файлы'",
    }

    if text in responses:
        await message.answer(responses[text], parse_mode="HTML")
    else:
        await message.answer(
            "🤔 Я не совсем понял ваш вопрос.\n"
            "Используй кнопки меню или напиши 'help' для помощи.",
            parse_mode="HTML"
        )


@router.message(Command("help"))
async def help_command(message: Message):
    """Команда помощи"""
    help_text = (
        "<b>📋 Помощь по командам:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Эта справка\n\n"
        "<b>Основные функции:</b>\n"
        "• 📚 Темы обучения - изучение Python от основ до продвинутых тем\n"
        "• 💻 Пример кода - примеры кода для каждой темы\n"
        "• ❓ Задать вопрос - получить помощь по Python\n"
        "• 📊 Мой прогресс - отслеживать прогресс обучения\n"
        "• 📥 Установка Python - инструкция по установке\n\n"
        "<b>Темы обучения:</b>\n"
        "• Основы Python - переменные, типы данных, функции\n"
        "• Синтаксис - современные возможности Python\n"
        "• ООП - объектно-ориентированное программирование\n"
        "• Файлы - работа с файлами и данными\n"
        "• Фреймворки - Flask, Django, FastAPI\n"
        "• Инструменты - pip, git, виртуальные окружения\n"
        "• Data Science - NumPy, Pandas, машинное обучение\n"
        "• Асинхронность - async/await, asyncio\n\n"
        "<i>Используй кнопки для удобной навигации! 🚀</i>"
    )

    await message.answer(help_text, parse_mode="HTML")


async def set_bot_commands(bot: Bot):
    """Установить команды бота"""
    commands = [
        BotCommand(command="start", description="🚀 Начать работу с ботом"),
        BotCommand(command="help", description="📋 Помощь и справка"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """Основная функция запуска бота"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Загрузка конфигурации
    env_config = dotenv_values(".env")
    token = env_config.get("BOT_TOKEN")

    if not token:
        logging.error("Токен бота не найден. Создайте файл .env с BOT_TOKEN=ваш_токен")
        return

    config = BotConfig(
        token=token,
        debug=env_config.get("DEBUG", "false").lower() == "true"
    )

    # Инициализация базы данных
    await db_manager.init_db()

    # Создание бота
    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Установка команд бота
    await set_bot_commands(bot)

    logging.info("🤖 Python Mentor Bot запущен!")
    print("=" * 50)
    print("Python Mentor Bot успешно запущен!")
    print("Бот готов к работе и ждет ваших вопросов!")
    print("=" * 50)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())