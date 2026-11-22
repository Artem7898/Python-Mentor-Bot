"""Встроенные учебные материалы Python Mentor Bot."""

from dataclasses import replace
from typing import Final

from bot.advanced_lessons import ADVANCED_LESSONS
from bot.api_lessons import API_LESSON_PAGES
from bot.core_lessons import CORE_PAGES
from bot.django_lessons import DJANGO_LESSONS
from bot.lesson_models import LESSON_LANGUAGES, Lesson, LessonPage, LessonTopic
from bot.lesson_translations import TRANSLATIONS, PageTranslation
from bot.python_lessons import FRAMEWORK_PAGES, PYTHON_LESSONS
from bot.workflow_lessons import WORKFLOW_PAGES

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
                windows_code="""# Python Install Manager (Windows):
py -3.14 --version
py -3.14""",
                linux_code="""# Linux/macOS:
python3.14 --version
python3.14""",
                example_code="""name = "Ada"
completed = 2
total = 5
topics = ["syntax", "files", "web"]

progress = completed / total
print(f"{name}: {progress:.0%} complete")
print(f"Next topic: {topics[completed]}")

assert progress == 0.4""",
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
                example_code="""def status_label(status: int) -> str:
    match status:
        case 200 | 201:
            return "success"
        case 404:
            return "not found"
        case 500 | 503:
            return "server error"
        case _:
            return "other"


statuses = [200, 201, 404, 503]
counts = {status: statuses.count(status) for status in set(statuses)}
if (successful := sum(counts.get(code, 0) for code in (200, 201))) > 0:
    print(f"Successful responses: {successful}")
assert status_label(404) == "not found"
""",
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
                example_code="""from typing import override


class Device:
    def __init__(self, name: str) -> None:
        if not name.strip():
            raise ValueError("name cannot be blank")
        self.name = name.strip()

    def status(self) -> str:
        return f"{self.name}: ready"


class Sensor(Device):
    @override
    def status(self) -> str:
        return f"{self.name}: measuring"


def report(devices: list[Device]) -> list[str]:
    return [device.status() for device in devices]


assert report([Device("gateway"), Sensor("thermometer")]) == [
    "gateway: ready",
    "thermometer: measuring",
]""",
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
                example_code="""import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

records = [{"name": "Ada", "course": "Python"}, {"name": "Grace", "course": "Django"}]

with TemporaryDirectory() as directory:
    root = Path(directory)
    json_path = root / "students.json"
    json_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    assert json.loads(json_path.read_text(encoding="utf-8")) == records

    csv_path = root / "students.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["name", "course"])
        writer.writeheader()
        writer.writerows(records)
    with csv_path.open(encoding="utf-8", newline="") as stream:
        assert list(csv.DictReader(stream)) == records""",
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
   python -m pip install flask
5. Проверьте установку:
   python -m flask --version""",
                linux_install="""# Установка Flask на Linux:
1. Откройте терминал
2. Создайте виртуальное окружение:
   python3 -m venv venv
3. Активируйте его:
   source venv/bin/activate
4. Установите Flask:
   python -m pip install flask
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
3. python -m pip install "Django>=5.2.8,<5.3"
4. django-admin --version""",
                linux_install="""# Установка Django на Linux:
1. python3 -m venv venv
2. source venv/bin/activate
3. python -m pip install "Django>=5.2.8,<5.3"
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
python -m pip install requests

# Установка пакета с ограничением совместимой версии
python -m pip install "Django~=5.2.8"

# Установка из requirements.txt
python -m pip install -r requirements.txt

# Обновление пакета
python -m pip install --upgrade package_name

# Просмотр установленных пакетов
python -m pip list

# Удаление пакета
python -m pip uninstall package_name

# Поиск пакета доступен на https://pypi.org/search/""",
                linux_code="""# На Linux используйте pip3:

python3 -m pip install requests
python3 -m pip list
python3 -m pip uninstall package_name""",
                example_language="text",
                example_code="""# requirements.txt
ruff>=0.15,<1
pytest>=9,<10""",
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
                example_language="bash",
                example_code="""git init
git status --short
git switch -c feature/lesson-notes
git add README.md
git diff --cached
git commit -m "Add lesson notes"
git log -1 --oneline""",
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
python -m pip install numpy pandas scikit-learn""",
                example_code="""import numpy as np
import pandas as pd

frame = pd.DataFrame(
    {"city": ["Madrid", "Madrid", "Oslo"], "minutes": [30, 60, 45]}
)
mean_by_city = frame.groupby("city")["minutes"].mean()
assert mean_by_city.loc["Madrid"] == 45

values = frame["minutes"].to_numpy()
assert np.mean(values) == 45
print(mean_by_city.to_string())""",
            ),
            LessonPage(
                title="Машинное обучение",
                explanation="Базовый пример машинного обучения с scikit-learn",
                install_code="python -m pip install scikit-learn",
                example_code="""from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split

features, labels = load_iris(return_X_y=True)
train_x, test_x, train_y, test_y = train_test_split(
    features, labels, test_size=0.25, stratify=labels, random_state=42
)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(train_x, train_y)
score = balanced_accuracy_score(test_y, model.predict(test_x))
print(f"Balanced accuracy: {score:.2%}")""",
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


async def load_section(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name.upper()


async def main() -> None:
    sections = await asyncio.gather(
        load_section("syntax", 0.02),
        load_section("async", 0.01),
    )
    assert sections == ["SYNTAX", "ASYNC"]


if __name__ == "__main__":
    asyncio.run(main())""",
            ),
        ),
    ),
    LessonTopic.INSTALL: Lesson(
        title="📥 Установка Python",
        pages=(
            LessonPage(
                title="Windows",
                explanation="Установите Python 3.14 с помощью официального Python Install Manager.",
                steps=(
                    "Установите Python Install Manager с python.org/downloads/windows.",
                    "Откройте PowerShell и выполните py install 3.14.",
                    "Проверьте версию командой py -3.14 --version.",
                    "Создайте окружение проекта командой py -3.14 -m venv .venv.",
                ),
            ),
            LessonPage(
                title="Linux и macOS",
                explanation="Установите Python 3.14 рядом с системным интерпретатором.",
                steps=(
                    "Возьмите Python 3.14 из доверенного источника или uv python install 3.14.",
                    "Проверьте интерпретатор командой python3.14 --version.",
                    "Создайте окружение командой python3.14 -m venv .venv.",
                    "Выполните .venv/bin/python -m pip --version для проверки pip.",
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


_ADDITIONS = (
    CORE_PAGES | API_LESSON_PAGES | WORKFLOW_PAGES | {LessonTopic.FRAMEWORKS: FRAMEWORK_PAGES}
)
_NEW_LESSONS = PYTHON_LESSONS | {LessonTopic.DJANGO: DJANGO_LESSONS}


def _build_catalogue(language: str) -> dict[LessonTopic, Lesson]:
    catalogue = (_LESSONS if language == "ru" else _LOCALIZED[language]) | {
        topic: localized[language] for topic, localized in ADVANCED_LESSONS.items()
    }
    for topic, additions in _ADDITIONS.items():
        lesson = catalogue[topic]
        # Keep existing page indices valid for stored progress and Telegram buttons.
        catalogue[topic] = Lesson(lesson.title, lesson.pages + additions[language])
    return catalogue | {topic: localized[language] for topic, localized in _NEW_LESSONS.items()}


_CATALOGUE = {language: _build_catalogue(language) for language in LESSON_LANGUAGES}


def _get_lesson(topic: LessonTopic, language: str) -> Lesson | None:
    return _CATALOGUE.get(language, _CATALOGUE["ru"]).get(topic)


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
