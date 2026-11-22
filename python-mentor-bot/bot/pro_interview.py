"""Curated multilingual Python backend interview practice."""

# ruff: noqa: RUF001
# Russian text intentionally includes Cyrillic letters and Python identifiers.

import re
from dataclasses import dataclass
from typing import Final
from unicodedata import normalize

from bot.formatting import escape_html
from bot.i18n import Locale
from bot.lesson_models import LocalizedText
from bot.study_copy import localize

MAX_INTERVIEW_ANSWER: Final = 2048
_WORD = re.compile(r"\w+")


@dataclass(frozen=True, slots=True)
class Concept:
    """A rubric item and indicative terms in the supported answer languages."""

    label: LocalizedText
    terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Question:
    """One scenario with a model answer and an advisory rubric."""

    topic: str
    prompt: LocalizedText
    concepts: tuple[Concept, ...]
    model: LocalizedText


_QUESTIONS = (
    Question(
        "Python",
        (
            "Вы написали предикат TypeIs[str] для значения str | int. "
            "Почему проверка isinstance(value, str) and bool(value) нарушает контракт?",
            "A predicate TypeIs[str] narrows a value of type str | int. "
            "Why would isinstance(value, str) and bool(value) violate the contract?",
            "Un predicado TypeIs[str] refina un valor str | int. "
            "¿Por qué isinstance(value, str) and bool(value) incumple el contrato?",
        ),
        (
            Concept(
                (
                    "Сужение в обеих ветках",
                    "Narrowing in both branches",
                    "Refinamiento en ambas ramas",
                ),
                (
                    "both branches",
                    "false branch",
                    "negative branch",
                    "ветках",
                    "ложной",
                    "rama falsa",
                    "ambas ramas",
                ),
            ),
            Concept(
                (
                    "Пустая строка остаётся str",
                    "An empty string is still str",
                    "La cadena vacía es str",
                ),
                ("empty string", "empty str", "пустая строка", "пустую строку", "cadena vacía"),
            ),
            Concept(
                (
                    "Подходящая проверка или TypeGuard",
                    "Exact predicate or TypeGuard",
                    "Predicado exacto o TypeGuard",
                ),
                ("typeguard", "isinstance"),
            ),
        ),
        (
            "TypeIs сужает тип в обеих ветках. Пустая строка — str, хотя составная "
            "проверка возвращает False. Для TypeIs используйте isinstance(value, str). "
            "Для проверки непустой строки можно использовать TypeGuard[str].",
            "TypeIs narrows both branches. The empty string is str even though the "
            "combined check returns False. Use isinstance(value, str) for TypeIs, "
            "or TypeGuard[str] for a check that also requires nonempty text.",
            "TypeIs refina ambas ramas. Una cadena vacía es str, aunque la condición "
            "compuesta devuelva False. Usa isinstance(value, str) con TypeIs o "
            "TypeGuard[str] si también compruebas que el texto no esté vacío.",
        ),
    ),
    Question(
        "Python · asyncio",
        (
            "API параллельно загружает два обязательных ресурса. Как ограничить общее "
            "время, остановить соседнюю задачу при сбое и освободить ресурсы?",
            "An endpoint fetches two required resources concurrently. How do you bound "
            "the overall time, cancel sibling work on failure and release resources?",
            "Una ruta consulta dos recursos obligatorios en paralelo. ¿Cómo limitas el "
            "plazo total, cancelas la otra tarea ante un fallo y liberas recursos?",
        ),
        (
            Concept(
                (
                    "Связанные задачи в TaskGroup",
                    "Related work in TaskGroup",
                    "Tareas en TaskGroup",
                ),
                ("taskgroup", "structured concurrency", "estructurada"),
            ),
            Concept(
                ("Общий тайм-аут", "Overall deadline", "Plazo total"),
                ("asyncio timeout", "timeout", "deadline", "тайм-аут", "предел", "plazo"),
            ),
            Concept(
                (
                    "Отмена и освобождение ресурсов",
                    "Cancellation and cleanup",
                    "Cancelación y limpieza",
                ),
                (
                    "finally",
                    "cancelled",
                    "cancellederror",
                    "async with",
                    "отмена",
                    "отмену",
                    "cancelación",
                    "liberar",
                ),
            ),
        ),
        (
            "Оберните TaskGroup в asyncio.timeout. При сбое группа отменяет оставшиеся "
            "задачи и ждёт их завершения. Клиенты открывайте через async with, а очистку "
            "выполняйте в finally. После очистки распространяйте CancelledError дальше.",
            "Put the TaskGroup inside asyncio.timeout. If a child fails, the group cancels "
            "remaining work and waits for it. Use async with or finally for resource "
            "cleanup and let CancelledError propagate afterward.",
            "Coloca TaskGroup dentro de asyncio.timeout. Si una tarea falla, el grupo "
            "cancela las demás y espera su finalización. Usa async with o finally para "
            "liberar recursos y permite que se propague CancelledError.",
        ),
    ),
    Question(
        "Django · ORM",
        (
            "Список заказов читает customer для каждого заказа и items для каждой строки. "
            "Как убрать N+1 и убедиться, что исправление действует?",
            "An order list reads each order's customer and its related items. "
            "How do you remove N+1 queries and verify the improvement?",
            "Una lista de pedidos lee el cliente y los artículos de cada pedido. "
            "¿Cómo eliminas las consultas N+1 y verificas la mejora?",
        ),
        (
            Concept(
                (
                    "select_related для customer",
                    "select_related for customer",
                    "select_related para customer",
                ),
                ("select_related", "join"),
            ),
            Concept(
                (
                    "prefetch_related для items",
                    "prefetch_related for items",
                    "prefetch_related para items",
                ),
                ("prefetch_related", "prefetch"),
            ),
            Concept(
                ("Проверка числа запросов", "Query-count test", "Prueba del número de consultas"),
                (
                    "assertnumqueries",
                    "capturequeriescontext",
                    "query count",
                    "число запросов",
                    "количество запросов",
                    "número de consultas",
                ),
            ),
        ),
        (
            "select_related присоединит customer, если это ForeignKey. prefetch_related "
            "заранее загрузит коллекцию items отдельным запросом. Выполните представление "
            "с несколькими заказами в тесте и проверьте число SQL-запросов.",
            "Use select_related for the customer foreign key and prefetch_related for "
            "the items collection. Exercise the actual view with multiple orders and "
            "assert how many SQL queries it performs.",
            "Usa select_related para la clave foránea customer y prefetch_related para "
            "la colección items. Ejecuta la vista con varios pedidos y comprueba "
            "cuántas consultas SQL realiza.",
        ),
    ),
    Question(
        "Django · SQL",
        (
            "Два POST одновременно резервируют один и тот же остаток. Как избежать "
            "отрицательного количества и повторной брони при повторе запроса?",
            "Two POST requests reserve the same stock concurrently. How do you prevent "
            "negative stock and duplicate reservations on a retry?",
            "Dos POST reservan el mismo inventario a la vez. ¿Cómo evitas un stock "
            "negativo y reservas duplicadas al reintentar?",
        ),
        (
            Concept(
                (
                    "Условное обновление или блокировка строки",
                    "Conditional update or row lock",
                    "Actualización condicional o bloqueo de fila",
                ),
                (
                    "select_for_update",
                    "conditional update",
                    "stock__gte",
                    "условное обновление",
                    "блокировка строки",
                    "actualización condicional",
                    "bloqueo de fila",
                ),
            ),
            Concept(
                ("Одна транзакция", "One transaction", "Una transacción"),
                ("transaction", "atomic", "транзакция", "transacción"),
            ),
            Concept(
                (
                    "Уникальный ключ идемпотентности",
                    "Unique idempotency key",
                    "Clave única de idempotencia",
                ),
                ("idempotency", "idempotent", "идемпотентности", "idempotencia"),
            ),
        ),
        (
            "В одной transaction.atomic сделайте условный UPDATE с проверкой остатка и "
            "создайте бронь. Обработайте случай, когда UPDATE не изменил строку. Для повтора "
            "сохраняйте результат под ключом идемпотентности с ограничением UNIQUE.",
            "In one transaction.atomic, make a conditional UPDATE that checks stock and "
            "create the reservation. Handle zero updated rows. Store the result under an "
            "idempotency key backed by a UNIQUE constraint for retry handling.",
            "En una transaction.atomic ejecuta un UPDATE condicional que compruebe el "
            "stock y crea la reserva. Gestiona el caso de cero filas actualizadas. "
            "Guarda el resultado con una clave de idempotencia respaldada por UNIQUE.",
        ),
    ),
    Question(
        "FastAPI · ASGI",
        (
            "FastAPI запрашивает данные из внешнего HTTP API при каждом вызове. "
            "Где создавать клиент и как ограничивать влияние медленного ответа?",
            "A FastAPI endpoint calls an upstream HTTP service per request. "
            "Where do you create the client, and how do you contain a slow response?",
            "Una ruta de FastAPI llama a un servicio HTTP por solicitud. "
            "¿Dónde creas el cliente y cómo controlas el impacto de una respuesta lenta?",
        ),
        (
            Concept(
                (
                    "Lifespan управляет клиентом",
                    "Lifespan manages the client",
                    "Lifespan gestiona el cliente",
                ),
                ("lifespan", "asynccontextmanager"),
            ),
            Concept(
                (
                    "Асинхронный клиент и пул",
                    "Async client with pooling",
                    "Cliente asíncrono con pool",
                ),
                ("asyncclient", "pool", "пул", "asíncrono"),
            ),
            Concept(
                (
                    "Тайм-ауты и ограничение ответа",
                    "Timeouts and response limits",
                    "Plazos y límites de respuesta",
                ),
                ("timeout", "deadline", "stream", "тайм-аут", "размер ответа", "plazo"),
            ),
        ),
        (
            "Создайте httpx.AsyncClient с пулом в lifespan и закройте его при остановке. "
            "Переиспользуйте клиент через зависимость. Настройте сетевые тайм-ауты, "
            "общий бюджет операции и максимальный размер результата. Обработайте 502 и 504.",
            "Create one pooled httpx.AsyncClient in lifespan, close it on shutdown, "
            "and inject it as a dependency. Set network timeouts, an overall deadline "
            "and a response size limit. Map upstream failures and timeouts to 502 and 504.",
            "Crea un httpx.AsyncClient con pool en lifespan, ciérralo al apagar e inyéctalo "
            "como dependencia. Define tiempos de red, un plazo global y un tamaño máximo "
            "de respuesta. Gestiona los errores externos y los plazos con 502 y 504.",
        ),
    ),
    Question(
        "FastAPI · HTTP",
        (
            "Защищённый маршрут получает запрос без токена, с просроченным токеном и "
            "от пользователя без нужного разрешения. Какие ответы и проверки нужны?",
            "A protected route receives a request with no token, an expired token, "
            "and an authenticated caller without permission. What checks and responses fit?",
            "Una ruta protegida recibe solicitudes sin token, con un token caducado y "
            "de un usuario autenticado sin permiso. ¿Qué comprobaciones y respuestas corresponden?",
        ),
        (
            Concept(
                (
                    "401 при сбое аутентификации",
                    "401 for failed authentication",
                    "401 si falla la autenticación",
                ),
                ("401", "www authenticate"),
            ),
            Concept(
                (
                    "403 для отсутствующего разрешения",
                    "403 for missing permission",
                    "403 si faltan permisos",
                ),
                ("403", "forbidden"),
            ),
            Concept(
                (
                    "Проверка токена и полномочий",
                    "Token and permission validation",
                    "Validación del token y los permisos",
                ),
                ("signature", "expiry", "issuer", "подпись", "подписи", "scope", "firma", "emisor"),
            ),
        ),
        (
            "Для отсутствующего, недействительного или просроченного токена верните "
            "401 с WWW-Authenticate. Проверяйте подпись, срок, issuer и audience "
            "в соответствии со схемой. Для действительного токена без права верните 403.",
            "Return 401 with WWW-Authenticate for a missing, invalid or expired token. "
            "Validate signature, expiry, issuer and audience as required by the scheme. "
            "Return 403 when a valid identity lacks permission.",
            "Devuelve 401 con WWW-Authenticate si el token falta, es inválido o ha caducado. "
            "Valida firma, caducidad, emisor y audiencia según el esquema. Devuelve 403 "
            "si la identidad es válida, pero carece de permiso.",
        ),
    ),
    Question(
        "Django REST Framework",
        (
            "Пользователь должен видеть только свои задачи и не может назначить владельца "
            "через JSON. Где реализовать эти ограничения в ModelViewSet?",
            "Users may see only their own tasks and cannot assign the owner in JSON. "
            "Where do you enforce those rules in a ModelViewSet?",
            "Cada usuario solo puede ver sus tareas y no puede asignar un propietario "
            "desde JSON. ¿Dónde aplicas esas reglas en un ModelViewSet?",
        ),
        (
            Concept(
                ("Фильтр get_queryset", "Scoped get_queryset", "Filtrar get_queryset"),
                ("get_queryset", "queryset"),
            ),
            Concept(
                (
                    "Владелец в perform_create",
                    "Owner assigned in perform_create",
                    "Propietario desde perform_create",
                ),
                ("perform_create", "serializer save", "request user"),
            ),
            Concept(
                ("Поле owner только для чтения", "Read-only owner", "Propietario de solo lectura"),
                ("read_only_fields", "read only", "чтения", "solo lectura"),
            ),
        ),
        (
            "Ограничьте get_queryset владельцем из request.user для списка и доступа по ID. "
            "Объявите owner только для чтения и назначайте его в perform_create. "
            "Проверьте просмотр, изменение и удаление чужой записи отдельными тестами.",
            "Filter get_queryset by request.user for list and detail operations. Make "
            "owner read-only and assign it in perform_create. Test requests to read, "
            "modify or delete another user's record.",
            "Filtra get_queryset por request.user para listas y detalles. Define owner "
            "como solo lectura y asígnalo en perform_create. Prueba lectura, modificación "
            "y borrado de un registro que pertenece a otro usuario.",
        ),
    ),
    Question(
        "Django REST Framework · CSRF",
        (
            "DRF использует SessionAuthentication. Почему тест с force_authenticate "
            "не доказывает, что браузерный POST защищён от CSRF?",
            "A DRF endpoint uses SessionAuthentication. Why doesn't force_authenticate "
            "prove that browser POST requests are protected against CSRF?",
            "Una ruta de DRF usa SessionAuthentication. ¿Por qué force_authenticate "
            "no demuestra que las peticiones POST del navegador tengan protección CSRF?",
        ),
        (
            Concept(
                (
                    "force_authenticate обходит аутентификацию",
                    "force_authenticate bypasses auth",
                    "force_authenticate omite la autenticación",
                ),
                ("bypass", "bypasses", "обходит", "пропускает", "omite"),
            ),
            Concept(
                (
                    "Реальный вход и сессионная cookie",
                    "Real login and session cookie",
                    "Inicio de sesión y cookie",
                ),
                ("session", "login", "cookie", "вход", "сессия", "sesión"),
            ),
            Concept(
                (
                    "Проверки с CSRF-токеном и без",
                    "Tests with and without a CSRF token",
                    "Pruebas con y sin token CSRF",
                ),
                (
                    "enforce_csrf_checks",
                    "x csrf token",
                    "x csrftoken",
                    "csrf token",
                    "csrf-токен",
                    "token csrf",
                ),
            ),
        ),
        (
            "force_authenticate подставляет пользователя в тесте и обходит путь "
            "SessionAuthentication. Создайте APIClient(enforce_csrf_checks=True) и "
            "войдите обычным способом. Проверьте отказ без CSRF-токена и успех с ним.",
            "force_authenticate injects a user and bypasses the session authentication path. "
            "Use APIClient(enforce_csrf_checks=True) and create a real login session. "
            "Verify denial without a CSRF token and success with one.",
            "force_authenticate proporciona un usuario y omite la autenticación de sesión. "
            "Usa APIClient(enforce_csrf_checks=True) e inicia una sesión real. Verifica "
            "el rechazo sin token CSRF y el éxito con el token.",
        ),
    ),
)

INTERVIEW_COUNT: Final = len(_QUESTIONS)
_HEADING: Final[LocalizedText] = (
    "🎙 <b>Собеседование · {index}/{total}</b>",
    "🎙 <b>Interview · {index}/{total}</b>",
    "🎙 <b>Entrevista · {index}/{total}</b>",
)
_INSTRUCTIONS: Final[LocalizedText] = (
    "Ответь своими словами. Для отмены используй /cancel.",
    "Answer in your own words. Use /cancel to leave.",
    "Responde con tus propias palabras. Usa /cancel para salir.",
)
_INVALID: Final[LocalizedText] = (
    "Введи ответ текстом до {limit} символов.",
    "Enter a text answer of up to {limit} characters.",
    "Escribe una respuesta de hasta {limit} caracteres.",
)
_FEEDBACK: Final[LocalizedText] = (
    "🔎 <b>Разбор ответа</b>",
    "🔎 <b>Answer review</b>",
    "🔎 <b>Revisión de la respuesta</b>",
)
_MATCHED: Final[LocalizedText] = (
    "Упомянутые темы",
    "Topics mentioned",
    "Temas mencionados",
)
_MISSING: Final[LocalizedText] = (
    "Что стоит раскрыть подробнее",
    "What to cover in more detail",
    "Qué conviene abordar con más detalle",
)
_SCOPE: Final[LocalizedText] = (
    "Подсказка опирается на термины в тексте. Сравни аргументы с примером ответа.",
    "This check uses terms in your text. Compare your reasoning with the sample answer.",
    "La comprobación usa términos de tu texto. Compara tu argumento con la respuesta de ejemplo.",
)
_MODEL: Final[LocalizedText] = ("Пример ответа", "Sample answer", "Respuesta de ejemplo")
_COMPLETE: Final[LocalizedText] = (
    "✅ <b>Собеседование завершено.</b>\nПовтори темы, которые стоит раскрыть подробнее.",
    "✅ <b>Interview complete.</b>\nRevisit the topics you wanted to cover in more detail.",
    "✅ <b>Entrevista completada.</b>\nRepasa los temas que quieras ampliar.",
)


def valid_interview_answer(answer: str) -> bool:
    """Check conversational bounds before changing the interview state."""
    return len(answer) <= MAX_INTERVIEW_ANSWER and bool(answer.strip())


def _words(text: str) -> str:
    return " ".join(_WORD.findall(normalize("NFKC", text).casefold()))


def _mentions(concept: Concept, normalized_answer: str) -> bool:
    return any(f" {_words(term)} " in normalized_answer for term in concept.terms)


def interview_question(index: int, locale: Locale) -> str | None:
    """Render the current scenario without exposing its model answer."""
    if not 0 <= index < INTERVIEW_COUNT:
        return None
    question = _QUESTIONS[index]
    heading = localize(locale, _HEADING).format(index=index + 1, total=INTERVIEW_COUNT)
    prompt = escape_html(localize(locale, question.prompt))
    return f"{heading}\n<b>{escape_html(question.topic)}</b>\n\n{prompt}\n\n" + localize(
        locale, _INSTRUCTIONS
    )


def interview_feedback(index: int, answer: str, locale: Locale) -> str | None:
    """Compare salient terms with an advisory rubric and render a model answer."""
    if not 0 <= index < INTERVIEW_COUNT:
        return None
    if not valid_interview_answer(answer):
        return localize(locale, _INVALID).format(limit=MAX_INTERVIEW_ANSWER)
    question = _QUESTIONS[index]
    normalized = f" {_words(answer)} "
    mentioned: list[str] = []
    missing: list[str] = []
    for concept in question.concepts:
        items = mentioned if _mentions(concept, normalized) else missing
        items.append(escape_html(localize(locale, concept.label)))
    sections = [localize(locale, _FEEDBACK), localize(locale, _SCOPE)]
    for title, items in ((_MATCHED, mentioned), (_MISSING, missing)):
        if items:
            sections.append(
                f"<b>{localize(locale, title)}</b>\n" + "\n".join(f"• {item}" for item in items)
            )
    sections.append(
        f"<b>{localize(locale, _MODEL)}</b>\n{escape_html(localize(locale, question.model))}"
    )
    return "\n\n".join(sections)


def interview_complete(locale: Locale) -> str:
    """Render the end of the interview."""
    return localize(locale, _COMPLETE)
