"""Localized static review diagnostics and trusted remediation examples."""

# ruff: noqa: RUF001
# Russian text intentionally includes Cyrillic letters and Python identifiers.

from dataclasses import dataclass
from enum import StrEnum

from bot.lesson_models import LocalizedText


class Rule(StrEnum):
    """Stable identifiers for reviewed patterns."""

    DYNAMIC_EXECUTION = "dynamic_execution"
    SHELL = "shell"
    DESERIALIZE = "deserialize"
    YAML = "yaml"
    SQL = "sql"
    TLS = "tls"
    CREDENTIAL = "credential"
    MUTABLE_DEFAULT = "mutable_default"
    BARE_EXCEPT = "bare_except"
    SWALLOWED_ERROR = "swallowed_error"
    BLOCKING_ASYNC = "blocking_async"
    HTTP_TIMEOUT = "http_timeout"
    MATERIALIZATION = "materialization"
    DETACHED_TASK = "detached_task"


class Category(StrEnum):
    """Priority categories shown in review output."""

    SECURITY = "security"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"


@dataclass(frozen=True, slots=True)
class Advice:
    category: Category
    title: LocalizedText
    explanation: LocalizedText
    example: str | None = None


ADVICE = {
    Rule.DYNAMIC_EXECUTION: Advice(
        Category.SECURITY,
        ("Динамическое выполнение", "Dynamic execution", "Ejecución dinámica"),
        (
            "Если аргумент приходит извне, используйте разбор данных или таблицу "
            "разрешённых операций. Ограничение словаря globals не создаёт песочницу.",
            "For external input, parse data or dispatch to a fixed set of operations. "
            "Restricting the globals dictionary does not isolate execution.",
            "Si el argumento viene de fuera, analiza los datos o usa un conjunto fijo "
            "de operaciones. Limitar el diccionario globals no aísla la ejecución.",
        ),
        "data = json.loads(payload)",
    ),
    Rule.SHELL: Advice(
        Category.SECURITY,
        ("Запуск через оболочку", "Shell invocation", "Invocación de la shell"),
        (
            "При shell=True оболочка интерпретирует аргумент. Используйте фиксированную "
            "программу и передавайте проверенные значения отдельными аргументами.",
            "With shell=True the shell interprets the argument. Use a fixed executable "
            "and pass validated values as separate arguments.",
            "Con shell=True la shell interpreta el argumento. Usa un ejecutable fijo "
            "y pasa los valores validados como argumentos separados.",
        ),
        'subprocess.run(["git", "status", "--short"], check=True)',
    ),
    Rule.DESERIALIZE: Advice(
        Category.SECURITY,
        ("Десериализация pickle", "Pickle deserialization", "Deserialización con pickle"),
        (
            "pickle может выполнить код при чтении данных. Для запросов, загрузок и других "
            "внешних данных используйте JSON и проверяйте его схему.",
            "Pickle can execute code while reading data. Use JSON with schema validation "
            "for requests, uploads and other external data.",
            "Pickle puede ejecutar código al leer los datos. Usa JSON con validación "
            "de esquema para solicitudes, cargas y otros datos externos.",
        ),
        "record = InputModel.model_validate_json(payload)",
    ),
    Rule.YAML: Advice(
        Category.SECURITY,
        ("Загрузчик YAML", "YAML loader", "Cargador YAML"),
        (
            "Для входных данных выбирайте безопасный загрузчик PyYAML и отдельно "
            "ограничивайте размер документа и проверяйте его поля.",
            "Use PyYAML's safe loader for input data. Limit the document size and "
            "validate the parsed fields separately.",
            "Usa el cargador seguro de PyYAML para los datos de entrada. Limita el "
            "tamaño del documento y valida los campos por separado.",
        ),
        "data = yaml.safe_load(document)",
    ),
    Rule.SQL: Advice(
        Category.SECURITY,
        ("Динамический текст SQL", "Dynamic SQL text", "Texto SQL dinámico"),
        (
            "Привязывайте значения параметрами драйвера. Для имён таблиц и столбцов "
            "выбирайте из известного списка. Пример использует синтаксис SQLite.",
            "Bind values through the driver. Select table and column names from an "
            "allowlist. This example uses SQLite placeholder syntax.",
            "Vincula los valores con el controlador. Elige nombres de tablas y columnas "
            "de una lista permitida. El ejemplo usa la sintaxis de SQLite.",
        ),
        'db.execute("SELECT name FROM users WHERE id = ?", (user_id,))',
    ),
    Rule.TLS: Advice(
        Category.SECURITY,
        ("Проверка сертификата отключена", "Certificate verification off", "TLS sin verificación"),
        (
            "Сохраните проверку сертификата. Для внутреннего сервиса настройте доверенный "
            "корневой сертификат вместо verify=False.",
            "Keep certificate verification enabled. Configure a trusted root certificate "
            "for an internal service instead of using verify=False.",
            "Mantén la verificación de certificados. Para un servicio interno configura "
            "una raíz de confianza en lugar de verify=False.",
        ),
        "client = httpx.Client(verify=trusted_ssl_context)",
    ),
    Rule.CREDENTIAL: Advice(
        Category.SECURITY,
        ("Строковый литерал в поле секрета", "Literal in a secret field", "Literal en un secreto"),
        (
            "Храните рабочий секрет в настройках среды или менеджере секретов. Если "
            "действующий секрет попал в Git или чат, замените его.",
            "Keep real secrets in environment configuration or a secret manager. "
            "Rotate a live secret if it was shared in Git or chat.",
            "Guarda los secretos reales en el entorno o en un gestor de secretos. "
            "Rota un secreto activo si se compartió en Git o en un chat.",
        ),
        'token = os.environ["SERVICE_TOKEN"]',
    ),
    Rule.MUTABLE_DEFAULT: Advice(
        Category.CORRECTNESS,
        ("Изменяемое значение по умолчанию", "Mutable default", "Valor mutable por defecto"),
        (
            "Значение по умолчанию создаётся один раз и может хранить данные между "
            "вызовами. Создавайте новый контейнер внутри функции.",
            "The default is created once and may retain data across calls. "
            "Create a fresh container inside the function.",
            "El valor se crea una sola vez y puede conservar datos entre llamadas. "
            "Crea un contenedor nuevo dentro de la función.",
        ),
        "def append_item(item, items=None):\n    if items is None:\n        items = []",
    ),
    Rule.BARE_EXCEPT: Advice(
        Category.CORRECTNESS,
        ("Обработчик без типа ошибки", "Bare exception handler", "Excepción sin tipo"),
        (
            "except без типа захватывает системные исключения и отмену. Укажите ошибки, "
            "для которых обработчик действительно умеет восстановить работу.",
            "A bare except catches system exceptions and cancellation. Catch the specific "
            "errors for which the handler can recover.",
            "Un except sin tipo captura excepciones del sistema y cancelaciones. "
            "Captura los errores concretos que sabes gestionar.",
        ),
        'except ValueError as exc:\n    raise InputError("Invalid value") from exc',
    ),
    Rule.SWALLOWED_ERROR: Advice(
        Category.CORRECTNESS,
        ("Ошибка игнорируется", "Exception is swallowed", "Se ignora la excepción"),
        (
            "Пустой обработчик скрывает сбой от вызывающего кода. Обработайте ожидаемую "
            "ошибку явно или сообщите о сбое без конфиденциальных данных.",
            "An empty handler hides failure from the caller. Handle expected failures "
            "explicitly or report the failure without sensitive data.",
            "Un manejador vacío oculta el fallo. Gestiona los errores esperados "
            "explícitamente o informa del fallo sin datos sensibles.",
        ),
    ),
    Rule.BLOCKING_ASYNC: Advice(
        Category.PERFORMANCE,
        (
            "Синхронная операция в async def",
            "Blocking operation in async def",
            "Bloqueo en async def",
        ),
        (
            "Длительная синхронная операция задерживает другие задачи цикла. "
            "Используйте асинхронный клиент или вынесите блокирующий ввод-вывод в поток.",
            "Long synchronous operations delay other tasks on the event loop. "
            "Use an async client or offload blocking I/O to a thread.",
            "Las operaciones síncronas lentas retrasan otras tareas del bucle. "
            "Usa un cliente asíncrono o lleva la E/S bloqueante a un hilo.",
        ),
        'text = await asyncio.to_thread(path.read_text, encoding="utf-8")',
    ),
    Rule.HTTP_TIMEOUT: Advice(
        Category.CORRECTNESS,
        (
            "HTTP без ограничения ожидания",
            "HTTP wait without a timeout",
            "HTTP sin tiempo de espera",
        ),
        (
            "Ограничьте соединение и чтение. Подберите значения под бюджет запроса "
            "и обработайте сетевой тайм-аут отдельно.",
            "Bound connection and read waits. Set limits within the request budget "
            "and handle network timeouts explicitly.",
            "Limita la espera de conexión y lectura. Ajusta los límites al presupuesto "
            "de la solicitud y gestiona los tiempos de espera.",
        ),
        "response = requests.get(url, timeout=(2, 5))",
    ),
    Rule.MATERIALIZATION: Advice(
        Category.PERFORMANCE,
        (
            "Лишний список перед свёрткой",
            "List built before reduction",
            "Lista previa a la reducción",
        ),
        (
            "Если вам нужен только результат свёртки, генератор экономит память. "
            "Для any и all он ещё и прекращает вычисления после решающего значения.",
            "If you only need the reduction result, a generator saves memory. "
            "For any and all it also stops when the result is known.",
            "Si solo necesitas el resultado de la reducción, un generador ahorra memoria. "
            "Para any y all también termina al conocer el resultado.",
        ),
        "total = sum(item.price for item in items)",
    ),
    Rule.DETACHED_TASK: Advice(
        Category.CORRECTNESS,
        ("Задача без владельца", "Untracked task", "Tarea sin seguimiento"),
        (
            "Связанные задачи объединяйте в TaskGroup. Для фоновой задачи храните "
            "ссылку, обрабатывайте сбой и завершайте задачу при остановке.",
            "Use a TaskGroup for related tasks. For background work, retain the task, "
            "handle failures and stop it on shutdown.",
            "Usa TaskGroup para tareas relacionadas. Para tareas en segundo plano, "
            "conserva la referencia, gestiona los fallos y cancélalas al cerrar.",
        ),
        "async with asyncio.TaskGroup() as tasks:\n    tasks.create_task(work())",
    ),
}
