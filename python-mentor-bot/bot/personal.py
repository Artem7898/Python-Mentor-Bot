"""Private learner data and role-checked mentor and editorial workflows."""

import logging
from secrets import token_urlsafe

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.access import ChatEvent, Roles, telegram_user
from bot.formatting import escape_html
from bot.i18n import Locale
from bot.mentor_answers import MentorAnswerer
from bot.monetization import MentorReplies
from bot.presentation import is_accessible, present, require_private
from bot.storage import DatabaseManager, OpenQuestionLimitError, Question, QuestionStatus

logger = logging.getLogger(__name__)
RETENTION_DAYS = 90
MAX_OPEN = 5
_PAGE_SIZE = 10
_QUESTION_CHUNK = 1400

_COPY = {
    "privacy": (
        "🔒 <b>Мои данные</b>\n\n"
        "Бот хранит идентификатор и имя Telegram, язык, прогресс, закладки и вопросы. "
        "Вопросы доступны вам и наставникам и удаляются через {days} дней. "
        "Здесь можно удалить учебный профиль. Платёжные записи хранятся отдельно. "
        "Управление продлением подписки — в /pro.",
        "🔒 <b>My data</b>\n\n"
        "The bot stores your Telegram ID and name, language, progress, bookmarks and questions. "
        "Questions are visible to you and mentors and expire after {days} days. "
        "You can delete your learning profile here. Billing records are kept separately. "
        "Use /pro to manage renewal.",
        "🔒 <b>Mis datos</b>\n\n"
        "El bot guarda tu ID y nombre de Telegram, idioma, progreso, marcadores y preguntas. "
        "Tú y los mentores podéis ver las preguntas. Se borran después de {days} días. "
        "Aquí puedes borrar tu perfil de aprendizaje. Los pagos se registran por separado. "
        "Consulta /pro para gestionar la renovación.",
    ),
    "notice": (
        "Напиши вопрос по Python текстом. Если его передадим наставнику, вопрос сохраняется "
        "до {days} дней. Не включай токены или личные данные. "
        "Отмена — /cancel.",
        "Send your Python question as text. Questions sent to mentors are kept for {days} days. "
        "Keep tokens and personal data out. Use /cancel to exit.",
        "Envía tu pregunta de Python como texto. Las preguntas para mentores se guardan "
        "durante {days} días. Evita tokens y datos personales. Usa /cancel para salir.",
    ),
    "question_limit": (
        "У вас уже {limit} открытых вопросов. Можно удалить один или дождаться ответа.",
        "You already have {limit} open questions. Delete one or wait for an answer.",
        "Ya tienes {limit} preguntas abiertas. Borra una o espera una respuesta.",
    ),
    "invalid_text": (
        "Отправь непустой вопрос текстом до 4096 символов.",
        "Send nonempty text of up to 4096 characters.",
        "Envía texto de hasta 4096 caracteres.",
    ),
    "external_choice": (
        "Для этого вопроса можно получить ответ через OpenAI. Если выберешь этот вариант, "
        "бот отправит текст вопроса в OpenAI. Можно вместо этого выбрать наставника.",
        "OpenAI can help answer this question. If you choose that option, the bot sends "
        "the question text to OpenAI. You can choose a human mentor instead.",
        "OpenAI puede ayudar con esta pregunta. Si eliges esa opción, el bot envía el texto "
        "a OpenAI. También puedes elegir un mentor.",
    ),
    "external_unavailable": (
        "Автоматический ответ сейчас недоступен. Можно отправить вопрос наставнику.",
        "An automated answer is unavailable right now. You can send the question to a mentor.",
        "La respuesta automática no está disponible. Puedes enviar la pregunta a un mentor.",
    ),
    "external": ("Получить ответ через OpenAI", "Get an OpenAI answer", "Consultar a OpenAI"),
    "human": ("Спросить наставника", "Ask a mentor", "Consultar a un mentor"),
    "payment_prompt": (
        "Опиши вопрос об оплате. Его увидит команда поддержки. "
        "Не включай токены или реквизиты. Отмена — /cancel.",
        "Describe the payment issue for the support team. Keep tokens and financial details out. "
        "Use /cancel to exit.",
        "Describe el problema de pago al equipo de soporte. Evita tokens y datos financieros. "
        "Usa /cancel para salir.",
    ),
    "saved": ("✅ Вопрос записан.", "✅ Question saved.", "✅ Pregunta guardada."),
    "questions": ("📬 Мои вопросы", "📬 My questions", "📬 Mis preguntas"),
    "mentor": ("🗂 Очередь наставника", "🗂 Mentor queue", "🗂 Cola del mentor"),
    "editor": (
        "📝 <b>Редактура курса</b>\n\n"
        "Предложите изменения в Git. Перед публикацией CI проверяет переводы, примеры и Telegram.",
        "📝 <b>Course editing</b>\n\n"
        "Propose edits in Git. CI checks translations, examples and Telegram limits.",
        "📝 <b>Edición del curso</b>\n\n"
        "Propón cambios en Git. CI comprueba traducciones, ejemplos y límites de Telegram.",
    ),
    "denied": ("Недостаточно прав.", "Access denied.", "Acceso denegado."),
    "empty": ("Пока пусто.", "Nothing here yet.", "Aún no hay elementos."),
    "gone": ("Вопрос недоступен.", "Question unavailable.", "Pregunta no disponible."),
    "new": ("Новый", "New", "Nueva"),
    "in_review": ("В работе", "In review", "En revisión"),
    "answered": ("Отвечен", "Answered", "Respondida"),
    "review": ("Взять в работу", "Start review", "Empezar revisión"),
    "reply": ("Ответить", "Answer", "Responder"),
    "answer_prompt": (
        "Отправь текст ответа. Он будет виден ученику. Отмена — /cancel.",
        "Send the answer as text. The learner can view it. Use /cancel to exit.",
        "Envía tu respuesta como texto. El estudiante podrá verla. Usa /cancel para salir.",
    ),
    "answer_saved": ("Ответ сохранён.", "Answer saved.", "Respuesta guardada."),
    "question": ("Вопрос", "Question", "Pregunta"),
    "answer": ("Ответ", "Answer", "Respuesta"),
    "back": ("⬅️ Назад", "⬅️ Back", "⬅️ Atrás"),
    "home": ("🏠 Главная", "🏠 Dashboard", "🏠 Inicio"),
    "next": ("Далее ➡️", "Next ➡️", "Siguiente ➡️"),
    "remove_profile": ("Удалить профиль", "Delete my profile", "Borrar mi perfil"),
    "remove_question": ("Удалить вопрос", "Delete question", "Borrar pregunta"),
    "confirm_profile": (
        "Удалить профиль, прогресс, настройки, закладки и все вопросы?",
        "Delete your profile, progress, settings, bookmarks and all questions?",
        "¿Borrar el perfil, el progreso, los ajustes, los marcadores y todas las preguntas?",
    ),
    "confirm_question": ("Удалить этот вопрос?", "Delete this question?", "¿Borrar esta pregunta?"),
    "confirm": ("Да, удалить", "Yes, delete", "Sí, borrar"),
    "cancel": ("Отмена", "Cancel", "Cancelar"),
    "deleted": ("Данные удалены.", "Data deleted.", "Datos borrados."),
    "cancelled": ("Действие отменено.", "Action cancelled.", "Acción cancelada."),
    "stale": ("Подтверждение устарело.", "Confirmation expired.", "La confirmación caducó."),
}
_INDEX = {Locale.RU: 0, Locale.EN: 1, Locale.ES: 2}


def _text(locale: Locale, key: str) -> str:
    return _COPY[key][_INDEX[locale]]


class PersonalState(StatesGroup):
    """Bounded private conversational tasks."""

    question = State()
    question_choice = State()
    payment_support = State()
    mentor_answer = State()
    confirmation = State()


def _buttons(locale: Locale, *buttons: tuple[str, str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, callback in buttons:
        builder.button(text=_text(locale, label), callback_data=callback)
    builder.adjust(1)
    return builder.as_markup()


async def _authorized(
    event: ChatEvent, bot: Bot, locale: Locale, roles: Roles, *, editorial: bool = False
) -> bool:
    if not await require_private(event, locale, bot):
        return False
    user = telegram_user(event)
    if user and (roles.can_edit(user.id) if editorial else roles.can_mentor(user.id)):
        return True
    notice = _text(locale, "denied")
    if isinstance(event, CallbackQuery):
        await event.answer(notice)
    else:
        await event.answer(notice)
    return False


async def ask_question(event: ChatEvent, state: FSMContext, locale: Locale, bot: Bot) -> None:
    """Show the data notice before accepting a private learner question."""
    if not await require_private(event, locale, bot):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    await state.clear()
    await state.set_state(PersonalState.question)
    await present(
        event,
        _text(locale, "notice").format(days=RETENTION_DAYS),
        _buttons(locale, ("questions", "study:questions"), ("home", "dashboard:home")),
    )


async def _queue_question(
    event: ChatEvent,
    question: str,
    message_id: int,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
) -> None:
    sender = telegram_user(event)
    if sender is None:
        return
    await db.get_or_create_user(sender.id, sender.username)
    try:
        await db.submit_question(sender.id, question, message_id=str(message_id), max_open=MAX_OPEN)
    except OpenQuestionLimitError:
        await present(
            event,
            _text(locale, "question_limit").format(limit=MAX_OPEN),
            _buttons(locale, ("questions", "study:questions"), ("home", "dashboard:home")),
        )
        return
    await state.clear()
    await present(
        event,
        _text(locale, "saved"),
        _buttons(locale, ("questions", "study:questions"), ("home", "dashboard:home")),
    )


async def record_question(
    message: Message,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    answerer: MentorAnswerer,
    replies: MentorReplies,
    command: CommandObject | None = None,
) -> None:
    """Answer in private when possible, otherwise use the mentor workflow."""
    if not await require_private(message, locale, bot):
        return
    if command is not None and not command.args:
        await ask_question(message, state, locale, bot)
        return
    question = ((message.text if command is None else command.args) or "").strip()
    if not question or len(question) > 4096:
        await message.answer(_text(locale, "invalid_text"))
        return
    answer = await answerer.answer(question, locale)
    if answer:
        await state.clear()
        await replies.send(message, answer, locale, db)
        return
    if answerer.external_enabled:
        consent_id = token_urlsafe(12)
        await state.clear()
        await state.set_state(PersonalState.question_choice)
        await state.set_data(
            {
                "question": question,
                "question_message_id": message.message_id,
                "consent_id": consent_id,
            }
        )
        await present(
            message,
            _text(locale, "external_choice"),
            _buttons(
                locale, ("external", f"ask:ai:{consent_id}"), ("human", f"ask:mentor:{consent_id}")
            ),
        )
        return
    await _queue_question(message, question, message.message_id, state, db, locale)


async def answer_choice(
    callback: CallbackQuery,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    answerer: MentorAnswerer,
    replies: MentorReplies,
) -> None:
    """Send this question externally only after an explicit private choice."""
    if not await require_private(callback, locale, bot):
        return
    data = await state.get_data()
    question, message_id = data.get("question"), data.get("question_message_id")
    _, _, action = (callback.data or "").partition(":")
    choice, _, consent_id = action.partition(":")
    sender = telegram_user(callback)
    if (
        await state.get_state() != PersonalState.question_choice.state
        or not isinstance(question, str)
        or type(message_id) is not int
        or not consent_id
        or consent_id != data.get("consent_id")
        or sender is None
        or not is_accessible(callback.message)
    ):
        await callback.answer(_text(locale, "stale"))
        return
    await callback.answer()
    if choice == "mentor":
        await _queue_question(callback, question, message_id, state, db, locale)
        return
    answer = await answerer.answer(question, locale, allow_external=True)
    if answer:
        await state.clear()
        await replies.send(callback.message, answer, locale, db, user_id=sender.id)
    else:
        await present(
            callback,
            _text(locale, "external_unavailable"),
            _buttons(locale, ("human", f"ask:mentor:{consent_id}")),
        )


async def ask_payment_question(
    callback: CallbackQuery, state: FSMContext, locale: Locale, bot: Bot
) -> None:
    """Open the human support queue for a payment issue."""
    if not await require_private(callback, locale, bot):
        return
    await callback.answer()
    await state.clear()
    await state.set_state(PersonalState.payment_support)
    await present(callback, _text(locale, "payment_prompt"))


async def record_payment_question(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Queue payment support privately without forwarding it to an AI provider."""
    if not await require_private(message, locale, bot):
        return
    issue = (message.text or "").strip()
    label = "[XTR] "
    if not issue or len(issue) + len(label) > 4096:
        await message.answer(_text(locale, "invalid_text"))
        return
    await _queue_question(message, label + issue, message.message_id, state, db, locale)


async def show_privacy(event: ChatEvent, locale: Locale, bot: Bot) -> None:
    """Explain the privacy policy and offer confirmed removal."""
    if not await require_private(event, locale, bot):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    await present(
        event,
        _text(locale, "privacy").format(days=RETENTION_DAYS),
        _buttons(locale, ("remove_profile", "privacy:delete"), ("home", "dashboard:home")),
    )


async def _list_questions(
    event: ChatEvent,
    questions: tuple[Question, ...],
    locale: Locale,
    *,
    mentor: bool,
    page: int,
) -> None:
    title = _text(locale, "mentor" if mentor else "questions")
    view = "mentor" if mentor else "questions"
    builder = InlineKeyboardBuilder()
    for item in questions[:_PAGE_SIZE]:
        status = _text(locale, item.status.value)
        preview = " ".join(item.question.split())[:42]
        builder.button(
            text=f"#{item.id} · {status} · {preview}", callback_data=f"{view}:view:{item.id}"
        )
    if page:
        builder.button(text=_text(locale, "back"), callback_data=f"{view}:page:{page - 1}")
    if len(questions) > _PAGE_SIZE:
        builder.button(text=_text(locale, "next"), callback_data=f"{view}:page:{page + 1}")
    builder.button(text=_text(locale, "home"), callback_data="dashboard:home")
    builder.adjust(1)
    text = f"<b>{title}</b>" if questions else f"<b>{title}</b>\n\n{_text(locale, 'empty')}"
    await present(event, text, builder.as_markup())


def _page(event: ChatEvent) -> int:
    data = event.data or "" if isinstance(event, CallbackQuery) else ""
    prefix, _, index = data.rpartition(":")
    if prefix in {"mentor:page", "questions:page"} and len(index) <= 6:
        if index.isascii() and index.isdecimal():
            return int(index)
    return 0


async def learner_questions(
    event: ChatEvent, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Show only the current learner's private question history."""
    if not await require_private(event, locale, bot):
        return
    sender = telegram_user(event)
    if sender is None:
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    page = _page(event)
    questions = await db.list_questions(sender.id, limit=_PAGE_SIZE + 1, offset=page * _PAGE_SIZE)
    await _list_questions(event, questions, locale, mentor=False, page=page)


async def mentor_queue(
    event: ChatEvent, db: DatabaseManager, locale: Locale, bot: Bot, roles: Roles
) -> None:
    """Show open questions to an authorized mentor or owner."""
    if not await _authorized(event, bot, locale, roles):
        return
    if isinstance(event, CallbackQuery):
        await event.answer()
    page = _page(event)
    questions = await db.list_open_questions(limit=_PAGE_SIZE + 1, offset=page * _PAGE_SIZE)
    await _list_questions(event, questions, locale, mentor=True, page=page)


async def editor_panel(event: ChatEvent, locale: Locale, bot: Bot, roles: Roles) -> None:
    """Expose the Git-based publishing workflow only to editors and owners."""
    if await _authorized(event, bot, locale, roles, editorial=True):
        await present(event, _text(locale, "editor"), _buttons(locale, ("home", "dashboard:home")))


def _id(value: str) -> int | None:
    if not value.isascii() or not value.isdecimal() or len(value) > 19:
        return None
    result = int(value)
    return result if 0 < result <= 2**63 - 1 else None


def _question_view(
    item: Question, locale: Locale, *, mentor: bool, section: str = "q", page: int = 0
) -> tuple[str, InlineKeyboardMarkup] | None:
    view = "mentor" if mentor else "questions"
    content = item.answer if section == "a" else item.question
    if page * _QUESTION_CHUNK >= len(content):
        return None
    chunk = content[page * _QUESTION_CHUNK : (page + 1) * _QUESTION_CHUNK]
    title = _text(locale, "answer" if section == "a" else "question")
    body = f"<b>{title} #{item.id} · {_text(locale, item.status.value)}</b>\n\n{escape_html(chunk)}"
    buttons: list[tuple[str, str]] = []
    if page:
        buttons.append(("back", f"{view}:read:{item.id}:{section}:{page - 1}"))
    if len(content) > (page + 1) * _QUESTION_CHUNK:
        buttons.append(("next", f"{view}:read:{item.id}:{section}:{page + 1}"))
    if section == "a":
        buttons.append(("question", f"{view}:view:{item.id}"))
    elif item.answer:
        buttons.append(("answer", f"{view}:read:{item.id}:a:0"))
    if mentor and item.status != QuestionStatus.ANSWERED:
        if item.status == QuestionStatus.NEW:
            buttons.append(("review", f"mentor:review:{item.id}"))
        buttons.append(("reply", f"mentor:reply:{item.id}"))
    if not mentor:
        buttons.append(("remove_question", f"privacy:question:{item.id}"))
    buttons.append(("back", "mentor:queue" if mentor else "study:questions"))
    return body, _buttons(locale, *buttons)


async def question_action(
    callback: CallbackQuery,
    state: FSMContext,
    db: DatabaseManager,
    locale: Locale,
    bot: Bot,
    roles: Roles,
    replies: MentorReplies,
) -> None:
    """Authorize every question callback again before accessing its record."""
    view, action, *values = (callback.data or "").split(":")
    mentor = view == "mentor"
    if mentor:
        if not await _authorized(callback, bot, locale, roles):
            return
    elif not await require_private(callback, locale, bot):
        return

    question_id = _id(values[0]) if values else None
    item = await db.get_question(question_id) if question_id is not None else None
    sender = telegram_user(callback)
    if item is None or sender is None or (not mentor and item.user_id != sender.id):
        await callback.answer(_text(locale, "gone"))
        return

    if action == "reply" and mentor and item.status != QuestionStatus.ANSWERED:
        await state.clear()
        await state.set_state(PersonalState.mentor_answer)
        await state.set_data({"question_id": item.id})
        await callback.answer()
        await present(
            callback, _text(locale, "answer_prompt"), _buttons(locale, ("back", "mentor:queue"))
        )
        return
    if action == "review" and mentor:
        updated = await db.set_question_status(item.id, QuestionStatus.IN_REVIEW)
        if updated is not None:
            item = updated
            logger.info("Mentor marked a question in review.")
    if (
        action == "read"
        and len(values) == 3
        and values[1] in {"q", "a"}
        and values[2] in {"0", "1", "2"}
    ):
        rendered = _question_view(
            item, locale, mentor=mentor, section=values[1], page=int(values[2])
        )
    elif action in {"view", "review"}:
        rendered = _question_view(item, locale, mentor=mentor)
    else:
        rendered = None
    if rendered is None:
        await callback.answer(_text(locale, "gone"))
        return
    if (
        not mentor
        and action == "read"
        and values[1] == "a"
        and len(item.answer) <= (int(values[2]) + 1) * _QUESTION_CHUNK
    ):
        footer = await replies.footer_for(sender.id, locale, db)
        if footer:
            rendered = f"{rendered[0]}\n\n{escape_html(footer)}", rendered[1]
    await callback.answer()
    await present(callback, *rendered)


async def save_mentor_answer(
    message: Message, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot, roles: Roles
) -> None:
    """Store a mentor answer once without replacing a published answer."""
    if not await _authorized(message, bot, locale, roles):
        await state.clear()
        return
    answer = (message.text or "").strip()
    if not answer or len(answer) > 4096:
        await message.answer(_text(locale, "invalid_text"))
        return
    question_id = (await state.get_data()).get("question_id")
    if not isinstance(question_id, int):
        await state.clear()
        return
    answer_record = await db.set_question_status(
        question_id, QuestionStatus.ANSWERED, answer=answer
    )
    await state.clear()
    if answer_record is not None:
        logger.info("Mentor answered a question.")
    await present(
        message,
        _text(locale, "answer_saved" if answer_record is not None else "gone"),
        _buttons(locale, ("back", "mentor:queue")),
    )


async def confirm_removal(
    callback: CallbackQuery, state: FSMContext, db: DatabaseManager, locale: Locale, bot: Bot
) -> None:
    """Require a fresh, owner-scoped confirmation before deleting any data."""
    if not await require_private(callback, locale, bot):
        return
    sender = telegram_user(callback)
    if sender is None:
        return
    action = (callback.data or "").removeprefix("privacy:")
    if action == "cancel":
        await state.clear()
        await callback.answer(_text(locale, "cancelled"))
        await present(
            callback, _text(locale, "cancelled"), _buttons(locale, ("home", "dashboard:home"))
        )
        return
    if action == "delete" or action.startswith("question:"):
        expected = "confirm-delete"
        question_id = None
        if action.startswith("question:"):
            question_id = _id(action.removeprefix("question:"))
            item = await db.get_question(question_id) if question_id is not None else None
            if item is None or item.user_id != sender.id:
                await callback.answer(_text(locale, "gone"))
                return
            expected = f"confirm-question:{question_id}"
        await state.clear()
        await state.set_state(PersonalState.confirmation)
        await state.set_data({"confirm": expected, "question_id": question_id})
        await callback.answer()
        await present(
            callback,
            _text(locale, "confirm_profile" if question_id is None else "confirm_question"),
            _buttons(locale, ("confirm", f"privacy:{expected}"), ("cancel", "privacy:cancel")),
        )
        return

    data = await state.get_data()
    if (
        await state.get_state() != PersonalState.confirmation.state
        or not action.startswith("confirm-")
        or action != data.get("confirm")
    ):
        await callback.answer(_text(locale, "stale"))
        return
    question_id = data.get("question_id")
    if isinstance(question_id, int):
        await db.delete_question(sender.id, question_id)
    else:
        await db.delete_user_data(sender.id)
    await state.clear()
    await callback.answer(_text(locale, "deleted"))
    await present(callback, _text(locale, "deleted"), _buttons(locale, ("home", "dashboard:home")))


def register_personal_routes(router: Router) -> None:
    """Register personal commands before generic conversational handlers."""
    router.message.register(show_privacy, Command("privacy"))
    router.message.register(learner_questions, Command("questions"))
    router.message.register(mentor_queue, Command("mentor"))
    router.message.register(editor_panel, Command("editor"))
    router.message.register(record_question, Command("ask"))
    router.message.register(record_question, PersonalState.question)
    router.message.register(record_payment_question, PersonalState.payment_support)
    router.message.register(save_mentor_answer, PersonalState.mentor_answer)
    router.callback_query.register(learner_questions, F.data == "study:questions")
    router.callback_query.register(learner_questions, F.data.startswith("questions:page:"))
    router.callback_query.register(mentor_queue, F.data == "mentor:queue")
    router.callback_query.register(mentor_queue, F.data.startswith("mentor:page:"))
    router.callback_query.register(show_privacy, F.data == "privacy:show")
    router.callback_query.register(answer_choice, F.data.startswith(("ask:ai:", "ask:mentor:")))
    router.callback_query.register(ask_payment_question, F.data == "payment:human")
    router.callback_query.register(confirm_removal, F.data.startswith("privacy:"))
    router.callback_query.register(question_action, F.data.startswith(("questions:", "mentor:")))
