"""Russian, English and Spanish copy for the learning dashboard."""

# ruff: noqa: RUF001
# Russian words in the visible interface intentionally use Cyrillic.

from dataclasses import dataclass
from typing import Final

from bot.i18n import Locale
from bot.lesson_models import LocalizedText

_LOCALE_INDEX: Final = {Locale.RU: 0, Locale.EN: 1, Locale.ES: 2}

_COPY: Final[dict[str, LocalizedText]] = {
    "dashboard": ("Главная", "Dashboard", "Inicio"),
    "welcome": (
        "<b>Python Mentor Bot</b>\n\nНачни с первого урока или выбери тему в каталоге.",
        "<b>Python Mentor Bot</b>\n\nStart with the first lesson or choose a catalogue topic.",
        "<b>Python Mentor Bot</b>\n\nEmpieza por la primera lección o elige un tema del catálogo.",
    ),
    "resume_position": (
        "Урок {page} из {total}",
        "Lesson {page} of {total}",
        "Lección {page} de {total}",
    ),
    "get_started": ("▶ Начать с основ", "▶ Start with the basics", "▶ Empezar por lo básico"),
    "resume": ("▶ Продолжить урок", "▶ Continue lesson", "▶ Continuar lección"),
    "catalog": ("Каталог", "Catalogue", "Catálogo"),
    "catalog_intro": (
        "<b>Каталог уроков</b>\n\nВыбери раздел или найди урок по названию.",
        "<b>Lesson catalogue</b>\n\nChoose a section or search by title.",
        "<b>Catálogo de lecciones</b>\n\nElige una sección o busca por título.",
    ),
    "group_python": ("Python", "Python", "Python"),
    "group_backend": ("Веб и API", "Web and APIs", "Web y API"),
    "group_practice": ("Практика и инструменты", "Practice and tools", "Práctica y herramientas"),
    "group_description": ("Выбери тему.", "Choose a topic.", "Elige un tema."),
    "settings": ("Настройки", "Settings", "Ajustes"),
    "settings_intro": (
        "Фильтр сложности действует в каталоге и поиске. Короткий режим сворачивает примеры.",
        "The level filters the catalogue and search. Compact mode hides examples initially.",
        "El nivel filtra el catálogo y la búsqueda. El modo compacto oculta los ejemplos.",
    ),
    "language": ("Язык", "Language", "Idioma"),
    "level": ("Сложность", "Difficulty", "Dificultad"),
    "level_all": ("Все уровни", "All levels", "Todos los niveles"),
    "compact_on": ("Короткий режим ✓", "Compact mode ✓", "Modo compacto ✓"),
    "compact_off": ("Короткий режим выключен", "Compact mode off", "Modo compacto desactivado"),
    "compact_hint": (
        "Примеры доступны по кнопке «Код».",
        "Use the Code button to view examples.",
        "Pulsa Código para ver los ejemplos.",
    ),
    "search": ("Поиск уроков", "Search lessons", "Buscar lecciones"),
    "search_prompt": (
        "Напиши часть названия урока или темы. Для отмены используй /cancel.",
        "Enter part of a lesson or topic title. Use /cancel to leave.",
        "Escribe parte del título de una lección o tema. Para salir, usa /cancel.",
    ),
    "search_invalid": (
        "Введи название длиной до 100 символов.",
        "Enter a title of up to 100 characters.",
        "Escribe un título de hasta 100 caracteres.",
    ),
    "search_matches": (
        "Найдено: {count}",
        "Matches: {count}",
        "Coincidencias: {count}",
    ),
    "search_more": (
        "Показаны первые {shown}. Уточни название, чтобы найти остальные.",
        "Showing the first {shown}. Refine the title to see other matches.",
        "Se muestran las primeras {shown}. Escribe un título más específico.",
    ),
    "nothing_found": (
        "Подходящих уроков нет. Попробуй другой запрос или уровень.",
        "No matching lessons. Try another title or level.",
        "No hay coincidencias. Prueba otro título o nivel.",
    ),
    "empty_group": (
        "На выбранном уровне уроков в этой теме нет.",
        "This topic has no lessons at the selected level.",
        "Este tema no tiene lecciones para el nivel elegido.",
    ),
    "contents": ("Содержание темы", "Topic contents", "Contenido del tema"),
    "progress": ("Прогресс", "Progress", "Progreso"),
    "completion": (
        "Завершено {done} из {total} ({percent}%)",
        "{done} of {total} complete ({percent}%)",
        "{done} de {total} completadas ({percent} %)",
    ),
    "bookmarks": ("Избранное", "Bookmarks", "Favoritos"),
    "no_bookmarks": (
        "Добавь урок в избранное, чтобы быстро вернуться к нему.",
        "Bookmark any lesson to return to it quickly.",
        "Guarda una lección en favoritos para volver a ella rápidamente.",
    ),
    "bookmark_add": ("☆ В избранное", "☆ Bookmark", "☆ Guardar"),
    "bookmark_remove": ("★ Убрать из избранного", "★ Remove bookmark", "★ Quitar de favoritos"),
    "bookmark_saved": ("Урок добавлен.", "Lesson bookmarked.", "Lección guardada."),
    "bookmark_removed": ("Урок убран.", "Bookmark removed.", "Favorito eliminado."),
    "mark_complete": ("Отметить пройденным", "Mark complete", "Marcar como completada"),
    "completed": ("✓ Пройдено", "✓ Complete", "✓ Completada"),
    "quiz": ("Проверка знаний", "Knowledge check", "Comprobar conocimientos"),
    "quiz_right": ("✓ Верно", "✓ Correct", "✓ Correcto"),
    "quiz_wrong": ("Попробуй ещё раз", "Try again", "Inténtalo de nuevo"),
    "quiz_retry": ("Ответить заново", "Answer again", "Responder otra vez"),
    "lesson": ("К уроку", "Back to lesson", "Volver a la lección"),
    "private_only": (
        "Открой личный чат с ботом, чтобы увидеть свои данные и настройки.",
        "Open a private chat with the bot to see your data and settings.",
        "Abre un chat privado con el bot para ver tus datos y ajustes.",
    ),
    "page_range": (
        "Уроки {first}–{last} из {total}",
        "Lessons {first}–{last} of {total}",
        "Lecciones {first}–{last} de {total}",
    ),
}


def localize(locale: Locale, text: LocalizedText) -> str:
    """Get translated copy ordered Russian, English and Spanish."""
    return text[_LOCALE_INDEX[locale]]


def study_tr(locale: Locale, key: str) -> str:
    """Look up a dashboard string in the selected language."""
    return localize(locale, _COPY[key])


@dataclass(frozen=True, slots=True)
class Quiz:
    """One localized practice question and instructional feedback."""

    question: LocalizedText
    options: tuple[LocalizedText, LocalizedText, LocalizedText]
    correct: int
    explanation: LocalizedText


QUIZZES: Final[dict[str, Quiz]] = {
    "basics.intro": Quiz(
        question=(
            "Как Python определяет тип значения переменной?",
            "How does Python determine the type of a variable's value?",
            "¿Cómo determina Python el tipo del valor de una variable?",
        ),
        options=(
            (
                "По объекту, присвоенному переменной.",
                "From the assigned object.",
                "A partir del objeto asignado.",
            ),
            ("По имени переменной.", "From the variable name.", "A partir del nombre."),
            (
                "По объявлению перед запуском.",
                "From a declaration before execution.",
                "A partir de una declaración previa.",
            ),
        ),
        correct=0,
        explanation=(
            "Тип принадлежит объекту. Имя можно связать с объектом другого типа.",
            "Objects have types. A name can be rebound to an object of a different type.",
            "El objeto tiene un tipo. Un nombre puede asociarse con un objeto de otro tipo.",
        ),
    ),
    "syntax.generics": Quiz(
        question=(
            "Что описывает T в функции def first[T](items: list[T]) -> T?",
            "What does T describe in def first[T](items: list[T]) -> T?",
            "¿Qué describe T en def first[T](items: list[T]) -> T?",
        ),
        options=(
            ("Фиксированный тип int.", "A fixed int type.", "Un tipo int fijo."),
            (
                "Связь типа элемента и результата.",
                "The link between item and result types.",
                "La relación entre el elemento y el resultado.",
            ),
            ("Длину списка.", "The length of the list.", "La longitud de la lista."),
        ),
        correct=1,
        explanation=(
            "T связывает аннотации. Для list[str] средство проверки типов выведет результат str.",
            "T connects the annotations. With list[str], a type checker infers a str result.",
            "T conecta las anotaciones. Con list[str], el comprobador infiere un resultado str.",
        ),
    ),
    "async.taskgroup": Quiz(
        question=(
            "Когда блок async with TaskGroup завершается при успешном выполнении?",
            "When does an async with TaskGroup block exit on success?",
            "¿Cuándo termina con éxito un bloque async with TaskGroup?",
        ),
        options=(
            (
                "Сразу после запуска задач.",
                "Immediately after tasks start.",
                "En cuanto comienzan las tareas.",
            ),
            (
                "При завершении первой задачи.",
                "When the first task ends.",
                "Cuando acaba la primera tarea.",
            ),
            (
                "После завершения всех задач.",
                "After every task finishes.",
                "Al terminar todas las tareas.",
            ),
        ),
        correct=2,
        explanation=(
            "TaskGroup ждёт дочерние задачи при выходе, поэтому они не остаются без контроля.",
            "TaskGroup waits for child tasks on exit, keeping them within the group lifetime.",
            "TaskGroup espera a las tareas hijas al salir, dentro del ciclo de vida del grupo.",
        ),
    ),
    "django.n-plus-one": Quiz(
        question=(
            "Как заранее загрузить category для всех товаров одним SQL-запросом?",
            "How can you fetch category for all products in one SQL query?",
            "¿Cómo cargas category para todos los productos en una consulta SQL?",
        ),
        options=(
            (
                'select_related("category")',
                'select_related("category")',
                'select_related("category")',
            ),
            ('defer("category")', 'defer("category")', 'defer("category")'),
            ('order_by("category")', 'order_by("category")', 'order_by("category")'),
        ),
        correct=0,
        explanation=(
            "select_related добавляет JOIN для внешнего ключа. Сортировка не загружает объект.",
            "select_related adds a join for the foreign key. Ordering does not fetch the object.",
            "select_related agrega un JOIN para la clave foránea. Ordenar no carga el objeto.",
        ),
    ),
    "fastapi.routes": Quiz(
        question=(
            "Что вернёт пример FastAPI для /items/0, если для item_id задано gt=0?",
            "What does the FastAPI example return for /items/0 if item_id requires gt=0?",
            "¿Qué devuelve el ejemplo FastAPI para /items/0 si item_id exige gt=0?",
        ),
        options=(
            ("HTTP 201", "HTTP 201", "HTTP 201"),
            ("HTTP 422", "HTTP 422", "HTTP 422"),
            ("HTTP 500", "HTTP 500", "HTTP 500"),
        ),
        correct=1,
        explanation=(
            "Ноль нарушает условие gt=0. Запрос отклоняется во время валидации параметров.",
            "Zero violates gt=0. FastAPI rejects the request during parameter validation.",
            "Cero incumple gt=0. FastAPI rechaza la solicitud al validar los parámetros.",
        ),
    ),
    "drf.serializers": Quiz(
        question=(
            "Что возвращает APIView при ошибке is_valid(raise_exception=True)?",
            "What does APIView return when is_valid(raise_exception=True) fails?",
            "¿Qué devuelve APIView si falla is_valid(raise_exception=True)?",
        ),
        options=(
            ("HTTP 200", "HTTP 200", "HTTP 200"),
            ("HTTP 403", "HTTP 403", "HTTP 403"),
            ("HTTP 400", "HTTP 400", "HTTP 400"),
        ),
        correct=2,
        explanation=(
            "DRF преобразует ValidationError сериализатора в ответ 400 с ошибками полей.",
            "DRF turns the serializer's ValidationError into a 400 response with field errors.",
            "DRF convierte el ValidationError del serializador en una respuesta 400 con errores.",
        ),
    ),
    "pydantic.strict": Quiz(
        question=(
            'Что произойдёт при передаче строки "2" в строгое поле quantity: int?',
            'What happens if you pass the string "2" into a strict quantity: int field?',
            '¿Qué ocurre al pasar la cadena "2" a un campo estricto quantity: int?',
        ),
        options=(
            ("ValidationError.", "ValidationError.", "ValidationError."),
            ("Строка превращается в 2.", "The string is converted to 2.", "Se convierte en 2."),
            ("Поле остаётся строкой.", "The field remains a string.", "El campo sigue como texto."),
        ),
        correct=0,
        explanation=(
            "Строгий режим не преобразует строку в целое число. Передайте числовое значение 2.",
            "Strict mode does not convert strings to integers. Provide the numeric value 2.",
            "El modo estricto no convierte cadenas en enteros. Proporciona el valor numérico 2.",
        ),
    ),
}
