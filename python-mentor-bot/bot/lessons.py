"""Встроенные учебные материалы Python Mentor Bot."""

from dataclasses import replace
from typing import Final

from bot.advanced_lessons import ADVANCED_LESSONS
from bot.lesson_models import Lesson, LessonPage, LessonTopic
from bot.lesson_translations import TRANSLATIONS, PageTranslation

__all__ = ["LessonManager", "LessonPage", "LessonTopic"]


_LESSONS: Final[dict[LessonTopic, Lesson]] = {
    LessonTopic.BASICS: Lesson(
        title="📚 Основы Python",
        pages=(
            LessonPage(
                title="Введение в Python",
                explanation=(
                    "Python - интерпретируемый язык программирования высокого уровня.\n"
                    "Используется для веб-разработки, анализа данных, машинного обучения, "
                    "автоматизации и многого другого.\n\n"
                    "<b>Особенности:</b>\n"
                    "• Простой и понятный синтаксис\n"
                    "• Динамическая типизация\n"
                    "• Большая стандартная библиотека\n"
                    "• Кроссплатформенность (работает на Windows, Linux, macOS)\n\n"
                    "<b>Первый запуск Python:</b>"
                ),
                windows_code="""# Для Windows:
1. Скачайте Python с python.org
2. Установите с галочкой "Add Python to PATH"
3. Откройте командную строку (cmd)
4. Введите: python --version
5. Чтобы запустить интерпретатор: python""",
                linux_code="""# Для Linux:
1. Обычно Python уже установлен
2. Проверьте версию: python3 --version
3. Если нет Python: sudo apt install python3
4. Запуск интерпретатора: python3""",
                example_code="""# Ваша первая программа на Python
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
print(f"Привет, {user_input}!")""",
            ),
            LessonPage(
                title="Основные конструкции",
                explanation="Условные операторы и циклы - основа программирования",
                example_code="""# Условный оператор if
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
print(greet())""",
            ),
        ),
    ),
    LessonTopic.SYNTAX: Lesson(
        title="🧠 Синтаксис Python",
        pages=(
            LessonPage(
                title="Современный синтаксис",
                explanation="Python постоянно развивается, добавляя новые возможности синтаксиса",
                example_code="""# F-строки (Python 3.6+)
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
print(squares)  # [0, 4, 16, 36, 64]""",
            ),
        ),
    ),
    LessonTopic.OOP: Lesson(
        title="🏛️ Объектно-ориентированное программирование",
        pages=(
            LessonPage(
                title="Основы ООП",
                explanation="ООП позволяет организовать код в виде объектов, "
                "которые объединяют данные и методы для работы с ними\n\n"
                "<b>4 основных принципа ООП:</b>\n"
                "1. <b>Инкапсуляция</b> - сокрытие деталей реализации\n"
                "2. <b>Наследование</b> - создание новых классов на основе существующих\n"
                "3. <b>Полиморфизм</b> - возможность объектов с одинаковым "
                "интерфейсом иметь разную реализацию\n"
                "4. <b>Абстракция</b> - работа на уровне понятий, а не деталей",
                example_code="""# Базовый пример класса
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
print(show_work(engineer))  # Строит мосты""",
            ),
        ),
    ),
    LessonTopic.FILES: Lesson(
        title="📁 Работа с файлами",
        pages=(
            LessonPage(
                title="Чтение и запись файлов",
                explanation="Работа с файлами необходима для:\n"
                "• Сохранения данных между запусками программы\n"
                "• Конфигурации приложений\n"
                "• Обработки больших объемов данных\n"
                "• Логирования событий",
                example_code="""# Открытие файла на чтение
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
        print(row)""",
            ),
        ),
    ),
    LessonTopic.FRAMEWORKS: Lesson(
        title="🚀 Веб-фреймворки",
        pages=(
            LessonPage(
                title="Flask - микрофреймворк",
                explanation="Flask - простой и легковесный фреймворк для создания веб-приложений",
                windows_install="""# Установка Flask на Windows:
1. Откройте командную строку (cmd)
2. Создайте виртуальное окружение:
   python -m venv venv
3. Активируйте его:
   venv\\Scripts\\activate
4. Установите Flask:
   pip install flask
5. Проверьте установку:
   python -m flask --version""",
                linux_install="""# Установка Flask на Linux:
1. Откройте терминал
2. Создайте виртуальное окружение:
   python3 -m venv venv
3. Активируйте его:
   source venv/bin/activate
4. Установите Flask:
   pip install flask
5. Проверьте установку:
   python3 -m flask --version""",
                example_code="""# Пример простого Flask приложения
# app.py
from datetime import UTC, datetime

from flask import Flask, jsonify, request
from markupsafe import escape

app = Flask(__name__)

# Главная страница
@app.route('/')
def home():
    return '<h1>Добро пожаловать!</h1>'

# Страница с параметром
@app.route('/user/<username>')
def show_user(username):
    return f'<h1>Профиль пользователя {escape(username)}</h1>'

# API endpoint
@app.route('/api/data')
def get_data():
    data = {
        'users': ['Алексей', 'Мария', 'Иван'],
        'count': 3,
        'timestamp': datetime.now(UTC).isoformat()
    }
    return jsonify(data)

# HTML форма
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '')
        return f'Спасибо, {escape(name)}! Ваше сообщение получено.'
    return '''
        <form method="POST">
            <input type="text" name="name" placeholder="Ваше имя">
            <button type="submit">Отправить</button>
        </form>
    '''

if __name__ == '__main__':
    app.run(port=5000)

# Запуск приложения:
# Windows: python app.py
# Linux: python3 app.py""",
            ),
            LessonPage(
                title="Django - полноценный фреймворк",
                explanation="Django - мощный фреймворк для создания сложных веб-приложений",
                windows_install="""# Установка Django на Windows:
1. python -m venv venv
2. venv\\Scripts\\activate
3. pip install django
4. django-admin --version""",
                linux_install="""# Установка Django на Linux:
1. python3 -m venv venv
2. source venv/bin/activate
3. pip install django
4. django-admin --version""",
                example_code="""# Создание проекта Django:
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
# python manage.py runserver""",
            ),
        ),
    ),
    LessonTopic.TOOLS: Lesson(
        title="🛠️ Инструменты разработчика",
        pages=(
            LessonPage(
                title="pip - менеджер пакетов",
                explanation="pip устанавливает и управляет Python пакетами",
                windows_code="""# Основные команды pip на Windows:

# Установка пакета
pip install requests

# Установка пакета с ограничением совместимой версии
pip install "Django~=5.2.8"

# Установка из requirements.txt
pip install -r requirements.txt

# Обновление пакета
pip install --upgrade package_name

# Просмотр установленных пакетов
pip list

# Удаление пакета
pip uninstall package_name

# Поиск пакета доступен на https://pypi.org/search/""",
                linux_code="""# На Linux используйте pip3:

pip3 install requests
pip3 list
pip3 uninstall package_name""",
                example_code="""# Файл requirements.txt содержит зависимости проекта
# requirements.txt
Django~=5.2.8
requests>=2.28.0
pandas
numpy
matplotlib

# Установка всех зависимостей
pip install -r requirements.txt""",
            ),
            LessonPage(
                title="Git - система контроля версий",
                explanation="Git отслеживает изменения в коде и позволяет работать в команде",
                windows_install="""# Установка Git на Windows:
1. Скачайте с git-scm.com
2. Запустите установщик
3. Используйте Git Bash или командную строку""",
                linux_install="""# Установка Git на Linux:
sudo apt update
sudo apt install git
git --version""",
                example_code="""# Основные команды Git:

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
*.log""",
            ),
        ),
    ),
    LessonTopic.DATASCIENCE: Lesson(
        title="📊 Data Science",
        pages=(
            LessonPage(
                title="NumPy и Pandas",
                explanation="Библиотеки для научных вычислений и анализа данных",
                install_code="""# Установка библиотек для Data Science
pip install numpy pandas matplotlib seaborn scikit-learn""",
                example_code="""import numpy as np
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
plt.show()""",
            ),
            LessonPage(
                title="Машинное обучение",
                explanation="Базовый пример машинного обучения с scikit-learn",
                example_code="""from sklearn.datasets import load_iris
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
    print(f"{name}: {importance:.3f}")""",
            ),
        ),
    ),
    LessonTopic.ASYNC: Lesson(
        title="⚡ Асинхронное программирование",
        pages=(
            LessonPage(
                title="async/await",
                explanation=(
                    "Асинхронное программирование позволяет эффективно работать с I/O операциями:\n"
                    "• Сетевые запросы\n"
                    "• Работа с базами данных\n"
                    "• Файловые операции\n"
                    "• Веб-серверы"
                ),
                example_code="""import asyncio
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
#     return {"item_id": item_id}""",
            ),
        ),
    ),
    LessonTopic.INSTALL: Lesson(
        title="📥 Установка Python",
        pages=(
            LessonPage(
                title="Windows",
                explanation="Пошаговая установка Python на Windows",
                steps=(
                    "1. Скачайте Python с официального сайта: python.org",
                    "2. Запустите установщик",
                    "3. ВНИМАНИЕ: Отметьте галочку 'Add Python to PATH'",
                    "4. Выберите 'Install Now'",
                    "5. После установки откройте командную строку (cmd)",
                    "6. Проверьте установку: python --version",
                    "7. Запустите Python: python",
                ),
            ),
            LessonPage(
                title="Linux",
                explanation="Установка Python на Linux",
                steps=(
                    "1. Откройте терминал",
                    "2. Проверьте установлен ли Python: python3 --version",
                    "3. Если Python не установлен:",
                    "   Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip",
                    "   Fedora: sudo dnf install python3",
                    "   Arch: sudo pacman -S python",
                    "4. Установите pip: sudo apt install python3-pip",
                    "5. Проверьте: python3 --version && pip3 --version",
                ),
            ),
        ),
    ),
}


def _translate_page(page: LessonPage, copy: PageTranslation) -> LessonPage:
    return replace(
        page,
        title=copy.title,
        explanation=copy.explanation,
        steps=copy.steps if copy.steps is not None else page.steps,
        windows_code=copy.windows_code or page.windows_code,
        linux_code=copy.linux_code or page.linux_code,
        windows_install=copy.windows_install or page.windows_install,
        linux_install=copy.linux_install or page.linux_install,
        install_code=copy.install_code or page.install_code,
    )


def _translate_topic(topic: LessonTopic, title: str, pages: tuple[PageTranslation, ...]) -> Lesson:
    localized = tuple(
        _translate_page(page, copy) for page, copy in zip(_LESSONS[topic].pages, pages, strict=True)
    )
    return Lesson(title, localized)


_LOCALIZED: Final[dict[str, dict[LessonTopic, Lesson]]] = {
    language: {
        topic: _translate_topic(topic, title, pages)
        for topic_id, (title, pages) in topics.items()
        if (topic := LessonTopic(topic_id)) in _LESSONS
    }
    for language, topics in TRANSLATIONS.items()
}


def _get_lesson(topic: LessonTopic, language: str) -> Lesson | None:
    if localized := ADVANCED_LESSONS.get(topic):
        return localized.get(language, localized["ru"])
    return _LOCALIZED.get(language, _LESSONS).get(topic) or _LESSONS.get(topic)


class LessonManager:
    """Предоставляет доступ к страницам каталога."""

    @staticmethod
    def get_topic_content(
        topic: LessonTopic, page: int = 0, language: str = "ru"
    ) -> LessonPage | None:
        """Возвращает страницу для допустимого индекса, иначе None."""
        lesson = _get_lesson(topic, language)
        if lesson is None or not 0 <= page < len(lesson.pages):
            return None
        return lesson.pages[page]

    @staticmethod
    def get_topic_title(topic: LessonTopic, language: str = "ru") -> str:
        """Возвращает заголовок темы, если она есть в каталоге."""
        lesson = _get_lesson(topic, language)
        return lesson.title if lesson is not None else ""

    @staticmethod
    def get_total_pages(topic: LessonTopic, language: str = "ru") -> int:
        """Возвращает число страниц в теме."""
        lesson = _get_lesson(topic, language)
        return len(lesson.pages) if lesson is not None else 0
