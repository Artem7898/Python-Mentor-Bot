"""Localized bot copy and Telegram locale resolution."""

from enum import StrEnum


class Locale(StrEnum):
    """Supported interface and curriculum languages."""

    RU = "ru"
    EN = "en"
    ES = "es"


LANGUAGE_NAMES = {Locale.RU: "🇷🇺 Русский", Locale.EN: "🇬🇧 English", Locale.ES: "🇪🇸 Español"}


def resolve_locale(code: str | None) -> Locale:
    """Resolve regional Telegram locale codes, defaulting to Russian."""
    primary = (code or "").lower().replace("_", "-").partition("-")[0]
    return Locale(primary) if primary in Locale else Locale.RU


# Every row is ordered Russian, English, Spanish.
_COPY = {
    "home": (
        "👋 <b>Привет! Я Python Mentor Bot</b>\n\n"
        "Открой урок, посмотри пример или продолжи обучение.",
        "👋 <b>Welcome to Python Mentor Bot</b>\n\n"
        "Open a lesson, browse examples or resume learning.",
        "👋 <b>Bienvenido a Python Mentor Bot</b>\n\n"
        "Abre una lección, consulta ejemplos o sigue estudiando.",
    ),
    "topics": ("📚 Темы обучения", "📚 Lessons", "📚 Lecciones"),
    "examples": ("💻 Примеры кода", "💻 Code examples", "💻 Ejemplos de código"),
    "ask": ("❓ Задать вопрос", "❓ Ask a question", "❓ Hacer una pregunta"),
    "progress": ("📊 Мой прогресс", "📊 My progress", "📊 Mi progreso"),
    "resume": ("▶️ Продолжить урок", "▶️ Resume lesson", "▶️ Continuar lección"),
    "install": ("📥 Установка Python", "📥 Install Python", "📥 Instalar Python"),
    "language": ("🌐 Язык", "🌐 Language", "🌐 Idioma"),
    "picker": (
        "<b>🌐 Выбери язык</b>\n\nОн будет использоваться в меню и уроках.",
        "<b>🌐 Choose your language</b>\n\nIt will be used in menus and lessons.",
        "<b>🌐 Elige tu idioma</b>\n\nSe usará en los menús y las lecciones.",
    ),
    "saved": ("Язык сохранён.", "Language saved.", "Idioma guardado."),
    "unsupported": ("Язык недоступен.", "Language unavailable.", "Idioma no disponible."),
    "choose_topic": (
        "<b>📚 Выбери тему для изучения:</b>",
        "<b>📚 Choose a lesson topic:</b>",
        "<b>📚 Elige un tema:</b>",
    ),
    "choose_example": (
        "<b>💻 Выбери тему для просмотра примеров:</b>",
        "<b>💻 Choose a topic to see its examples:</b>",
        "<b>💻 Elige un tema para ver ejemplos:</b>",
    ),
    "back": ("⬅️ Назад", "⬅️ Back", "⬅️ Atrás"),
    "next": ("Вперёд ➡️", "Next ➡️", "Siguiente ➡️"),
    "dashboard": ("🏠 Главное меню", "🏠 Dashboard", "🏠 Inicio"),
    "full_lesson": ("📖 Полный урок", "📖 Full lesson", "📖 Lección completa"),
    "example": ("💻 Пример кода", "💻 Code example", "💻 Ejemplo de código"),
    "install_code": ("📦 Установка", "📦 Installation", "📦 Instalación"),
    "windows_install": (
        "💻 Установка на Windows",
        "💻 Install on Windows",
        "💻 Instalar en Windows",
    ),
    "linux_install": ("🐧 Установка на Linux", "🐧 Install on Linux", "🐧 Instalar en Linux"),
    "invalid_page": ("Страница недоступна.", "This page is unavailable.", "Página no disponible."),
    "invalid_message": (
        "Сообщение недоступно. Открой меню через /start.",
        "This message is unavailable. Open the menu with /start.",
        "El mensaje no está disponible. Abre el menú con /start.",
    ),
    "ask_prompt": (
        "Напиши вопрос по Python текстом. Для отмены отправь /cancel.",
        "Send your Python question as text. To cancel, use /cancel.",
        "Envía tu pregunta de Python como texto. Usa /cancel para cancelar.",
    ),
    "ask_validation": (
        "Отправь непустой вопрос текстом до 4096 символов.",
        "Send a nonempty text question of up to 4096 characters.",
        "Envía una pregunta de texto de hasta 4096 caracteres.",
    ),
    "ask_saved": ("✅ Вопрос записан.", "✅ Question saved.", "✅ Pregunta guardada."),
    "cancelled": ("Действие отменено.", "Action cancelled.", "Acción cancelada."),
    "no_progress": (
        "Отправь /start, чтобы начать отслеживать прогресс.",
        "Send /start to begin tracking progress.",
        "Envía /start para comenzar a guardar tu progreso.",
    ),
    "learner": ("Пользователь", "Learner", "Estudiante"),
    "anonymous": ("Аноним", "Anonymous", "Anónimo"),
    "current_topic": ("Текущая тема", "Current topic", "Tema actual"),
    "page": ("Страница", "Page", "Página"),
    "joined": ("Зарегистрирован", "Joined", "Registro"),
    "start_cmd": ("Открыть главное меню", "Open the dashboard", "Abrir el menú principal"),
    "help_cmd": ("Показать справку", "Show help", "Mostrar ayuda"),
    "language_cmd": ("Выбрать язык", "Choose a language", "Elegir idioma"),
    "cancel_cmd": (
        "Отменить ожидание вопроса",
        "Cancel a pending question",
        "Cancelar una pregunta",
    ),
    "run_cmd": (
        "Вычислить арифметическое выражение",
        "Evaluate an arithmetic expression",
        "Calcular una expresión aritmética",
    ),
    "help_title": ("📋 Команды", "📋 Commands", "📋 Comandos"),
    "run_prompt": (
        "Введи арифметическое выражение, например <code>/run 2 ** 3</code>.",
        "Enter an arithmetic expression, for example <code>/run 2 ** 3</code>.",
        "Introduce una expresión aritmética, por ejemplo <code>/run 2 ** 3</code>.",
    ),
    "run_invalid": (
        "Проверь выражение и попробуй снова.",
        "Check your expression. Use numbers and arithmetic operators within the limits.",
        "Revisa la expresión. Usa números y operadores aritméticos dentro de los límites.",
    ),
    "result": ("Результат", "Result", "Resultado"),
    "fallback": (
        "Выбери действие в меню или отправь /help.",
        "Choose an action from the dashboard or send /help.",
        "Elige una opción del menú o envía /help.",
    ),
    "failure": (
        "Не удалось выполнить действие. Попробуй ещё раз.",
        "Could not complete that action. Try again.",
        "No se pudo completar la acción. Inténtalo de nuevo.",
    ),
}
_LOCALE_INDEX = {Locale.RU: 0, Locale.EN: 1, Locale.ES: 2}

COMMANDS = (
    ("start", "start_cmd"),
    ("help", "help_cmd"),
    ("language", "language_cmd"),
    ("cancel", "cancel_cmd"),
    ("run", "run_cmd"),
)


def tr(locale: Locale, key: str) -> str:
    """Return the catalog entry in the requested locale."""
    return _COPY[key][_LOCALE_INDEX[locale]]
