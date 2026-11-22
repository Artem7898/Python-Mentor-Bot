"""Localized exercises for tools, data, async I/O, setup, and validation."""

# The curriculum contains Russian prose.
# ruff: noqa: RUF001

from typing import Final

from bot.lesson_models import LessonLevel, LessonPage, LessonTopic, LocalizedPage, localize_pages

WORKFLOW_PAGES: Final[dict[LessonTopic, dict[str, tuple[LessonPage, ...]]]] = {
    LessonTopic.TOOLS: localize_pages(
        LocalizedPage(
            title=(
                "Воспроизводимое окружение с uv",
                "Reproducible environments with uv",
                "Entornos reproducibles con uv",
            ),
            explanation=(
                "pyproject.toml задаёт прямые зависимости. uv.lock фиксирует результат "
                "разрешения версий, включая транзитивные зависимости. Команда uv sync --locked "
                "сообщает об ошибке, если файл блокировки нужно обновить.",
                "pyproject.toml declares direct dependencies. uv.lock records resolved "
                "versions, including transitive dependencies. uv sync --locked fails if "
                "the lockfile needs an update.",
                "pyproject.toml declara las dependencias directas. uv.lock registra "
                "las versiones resueltas, incluidas las dependencias transitivas. "
                "uv sync --locked falla si hay que actualizar el archivo de bloqueo.",
            ),
            install_code="""uv init --bare --python 3.14
uv python pin 3.14
uv add "httpx>=0.28,<1"
uv add --dev "pytest>=9,<10" "ruff>=0.15,<1"
uv sync --locked
uv run --locked python url_example.py""",
            example_code="""# url_example.py
from httpx import URL

url = URL("https://example.org/catalog", params={"q": "data science"})
assert url.params["q"] == "data science"
print(url)""",
            steps=(
                (
                    "Установите uv по инструкции docs.astral.sh/uv и откройте пустой каталог.",
                    "Install uv using docs.astral.sh/uv and open an empty directory.",
                    "Instala uv siguiendo docs.astral.sh/uv y abre un directorio vacío.",
                ),
                (
                    "Сохраните пример как url_example.py перед запуском последней команды.",
                    "Save the example as url_example.py before running the final command.",
                    "Guarda el ejemplo como url_example.py antes del último comando.",
                ),
                (
                    "Добавьте в Git pyproject.toml и uv.lock, а .venv оставьте локально.",
                    "Track pyproject.toml and uv.lock in Git and keep .venv local.",
                    "Incluye pyproject.toml y uv.lock en Git y deja .venv en el equipo.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.INTERMEDIATE,
            title=(
                "Линтинг, форматирование и тесты",
                "Linting, formatting, and tests",
                "Análisis estático, formato y pruebas",
            ),
            explanation=(
                "Ruff проверяет правила кода и форматирование. pytest проверяет "
                "поведение программы. Параметризация запускает одну проверку на нескольких "
                "наборах данных, в том числе на пустой строке.",
                "Ruff checks source rules and formatting. pytest checks what the program "
                "does. Parametrization runs the same assertion with several inputs, "
                "including the empty string.",
                "Ruff comprueba las reglas de código y el formato. pytest comprueba el "
                "comportamiento. La parametrización repite una aserción con varias entradas, "
                "incluida una cadena vacía.",
            ),
            install_code="""uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked python -m pytest -q""",
            example_code="""# text_utils.py
def words(text: str) -> tuple[str, ...]:
    return tuple(text.casefold().split())


# test_text_utils.py
import pytest

from text_utils import words


@pytest.mark.parametrize(
    ("text", "expected"),
    [("  Hello WORLD  ", ("hello", "world")), ("", ())],
)
def test_words(text: str, expected: tuple[str, ...]) -> None:
    assert words(text) == expected""",
            steps=(
                (
                    "Используйте окружение предыдущей страницы. Разделите код на два файла.",
                    "Use the previous page's environment and split the code into two files.",
                    "Usa el entorno de la página anterior y divide el código en dos archivos.",
                ),
                (
                    "Уберите casefold() и убедитесь, что один тест выявляет регрессию.",
                    "Remove casefold() and confirm that one test catches the regression.",
                    "Quita casefold() y comprueba que una prueba detecta la regresión.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.PROFESSIONAL,
            title=(
                "Единая команда проверки для разработки и CI",
                "One verification command for development and CI",
                "Un comando de verificación para desarrollo y CI",
            ),
            explanation=(
                "Объедините проверки в один скрипт с предсказуемым кодом выхода. "
                "Передача исполняемого файла и списка аргументов запускает команды "
                "без интерпретации оболочкой. Локально и в CI вызывайте один скрипт.",
                "Put checks behind a script with a predictable exit status. Passing an "
                "executable and arguments runs each command without shell interpretation. "
                "Invoke the same script locally and in CI.",
                "Agrupa las comprobaciones en un script con un código de salida predecible. "
                "Pasar el ejecutable y los argumentos evita la interpretación por la shell. "
                "Usa el mismo script en local y en CI.",
            ),
            install_code="""uv sync --locked
uv run --locked python check.py""",
            example_code="""# check.py
import subprocess
import sys


def main() -> int:
    commands = (
        ("ruff", "check", "."),
        ("ruff", "format", "--check", "."),
        ("pytest", "-q"),
    )
    for module, *args in commands:
        result = subprocess.run([sys.executable, "-m", module, *args], check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())""",
            steps=(
                (
                    "Сохраните check.py рядом с pyproject.toml и добавьте команды в ваш CI.",
                    "Save check.py beside pyproject.toml and add the commands to your CI.",
                    "Guarda check.py junto a pyproject.toml y añade los comandos a tu CI.",
                ),
                (
                    "Сломайте тест и проверьте, что команда завершилась с ненулевым кодом.",
                    "Break one test and check that the command exits with a nonzero status.",
                    "Rompe una prueba y verifica que la salida sea distinta de cero.",
                ),
            ),
        ),
    ),
    LessonTopic.DATASCIENCE: localize_pages(
        LocalizedPage(
            title=(
                "Проверка схемы при чтении CSV",
                "Checking a schema when reading CSV",
                "Comprobar el esquema al leer CSV",
            ),
            explanation=(
                "Укажите типы колонок заранее. Это сохраняет нули в идентификаторах "
                "и отличает пропуск от нулевого количества. Явно проверьте обязательные "
                "поля перед расчётом.",
                "Declare column types upfront. This preserves leading zeroes in identifiers "
                "and gives missing quantities a distinct representation. Check required "
                "values before calculating.",
                "Declara de antemano los tipos de las columnas. Así conservas los ceros "
                "iniciales en los identificadores y distingues las cantidades ausentes. "
                "Comprueba los valores obligatorios antes de calcular.",
            ),
            install_code='python -m pip install "pandas>=3,<4"',
            example_code=r"""from io import StringIO

import pandas as pd

csv = StringIO("sku,units,price\n001,2,3.5\n002,,5.0\n003,5,1.0\n")
df = pd.read_csv(csv, dtype={"sku": "string", "units": "Int64", "price": "Float64"})
complete = df.dropna(subset=["sku", "units", "price"]).copy()
complete["revenue"] = complete["units"] * complete["price"]

assert complete["sku"].tolist() == ["001", "003"]
assert len(df) - len(complete) == 1
print(complete[["sku", "revenue"]])""",
            steps=(
                (
                    "В реальном отчёте сохраните отброшенные строки для проверки источника.",
                    "In a real report, retain the rejected rows for source-data review.",
                    "En un informe real, conserva las filas descartadas para revisar el origen.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.INTERMEDIATE,
            title=(
                "Векторные расчёты и пропуски с NumPy",
                "Vectorized computations and missing data with NumPy",
                "Cálculos vectorizados y datos ausentes con NumPy",
            ),
            explanation=(
                "Булева маска выбирает пригодные элементы массива сразу. Проверяйте, "
                "что после фильтрации остались данные. Среднее для пустой выборки "
                "требует явной политики обработки.",
                "A Boolean mask selects usable array values in one operation. Check that "
                "some values remain after filtering. An empty sample needs an explicit "
                "policy before taking its mean.",
                "Una máscara booleana selecciona los valores válidos de una vez. "
                "Comprueba que queden valores tras el filtrado. Define cómo actuar con una "
                "muestra vacía antes de calcular su media.",
            ),
            install_code='python -m pip install "numpy>=2.4,<3"',
            example_code="""import numpy as np


def summarize(values: list[float]) -> tuple[int, float]:
    measurements = np.asarray(values, dtype=np.float64)
    usable = measurements[np.isfinite(measurements) & (measurements >= 0)]
    if usable.size == 0:
        raise ValueError("No usable measurements")
    return usable.size, float(usable.mean())


count, mean = summarize([2.0, float("nan"), 4.0, float("inf"), -1.0])
assert (count, mean) == (2, 3.0)
print(f"{count=}, {mean=}")""",
            steps=(
                (
                    "Проверьте пустой массив и массив только с пропусками.",
                    "Exercise the empty array and an array containing only missing values.",
                    "Prueba un array vacío y otro que solo contenga valores ausentes.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.PROFESSIONAL,
            title=(
                "Оценка модели без утечки данных",
                "Evaluating a model without data leakage",
                "Evaluar un modelo sin fuga de datos",
            ),
            explanation=(
                "Разделите данные до обучения. Pipeline обучает масштабирование только "
                "на тренировочной части и применяет те же параметры при прогнозе. "
                "Macro F1 одинаково учитывает каждый класс.",
                "Split the data before fitting. The pipeline learns scaling from the "
                "training partition and reuses it for predictions. Macro F1 gives each "
                "class equal weight.",
                "Separa los datos antes del entrenamiento. El pipeline aprende el "
                "escalado solo con la partición de entrenamiento y lo aplica al predecir. "
                "El F1 macro da el mismo peso a cada clase.",
            ),
            install_code='python -m pip install "scikit-learn>=1.8,<2"',
            example_code="""from sklearn.datasets import load_wine
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

features, labels = load_wine(return_X_y=True)
train_x, test_x, train_y, test_y = train_test_split(
    features, labels, test_size=0.25, stratify=labels, random_state=42,
)

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
model.fit(train_x, train_y)
prediction = model.predict(test_x)
print(f"Macro F1: {f1_score(test_y, prediction, average='macro'):.3f}")""",
            steps=(
                (
                    "Сравните с DummyClassifier и подбирайте параметры на тренировочной части.",
                    "Compare with DummyClassifier and tune only on the training partition.",
                    "Compara con DummyClassifier y ajusta solo con datos de entrenamiento.",
                ),
            ),
        ),
    ),
    LessonTopic.ASYNC: localize_pages(
        LocalizedPage(
            title=(
                "Параллельное ожидание с TaskGroup",
                "Concurrent waiting with TaskGroup",
                "Esperas concurrentes con TaskGroup",
            ),
            explanation=(
                "Создавайте связанные задачи внутри TaskGroup. Группа дожидается задач "
                "перед выходом из контекста, поэтому результат считывается после блока. "
                "asyncio.sleep имитирует ожидание ввода-вывода.",
                "Create related tasks inside a TaskGroup. The group waits for its tasks "
                "before exiting the context, so you can read results after the block. "
                "asyncio.sleep simulates waiting for I/O.",
                "Crea tareas relacionadas dentro de TaskGroup. El grupo espera a que "
                "terminen antes de salir del contexto, por lo que los resultados se leen "
                "después del bloque. asyncio.sleep simula una espera de entrada/salida.",
            ),
            example_code="""import asyncio


async def fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name.upper()


async def main() -> None:
    async with asyncio.TaskGroup() as tasks:
        first = tasks.create_task(fetch("alpha", 0.04))
        second = tasks.create_task(fetch("beta", 0.02))
    assert (first.result(), second.result()) == ("ALPHA", "BETA")


if __name__ == "__main__":
    asyncio.run(main())""",
            steps=(
                (
                    "Замените одну задержку на собственную асинхронную операцию без блокировки.",
                    "Replace one simulated delay with your own nonblocking I/O operation.",
                    "Sustituye una espera simulada por una operación de E/S no bloqueante.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.INTERMEDIATE,
            title=(
                "Очередь с ограниченной ёмкостью",
                "A queue with bounded capacity",
                "Una cola con capacidad limitada",
            ),
            explanation=(
                "Очередь с maxsize приостанавливает производителя, когда буфер заполнен. "
                "Фиксированное число воркеров ограничивает одновременные операции. "
                "task_done() в finally поддерживает счётчик очереди даже при ошибке.",
                "A queue with maxsize pauses the producer when its buffer fills. A fixed "
                "number of workers limits concurrency. Calling task_done() in finally "
                "maintains queue accounting even when an operation fails.",
                "Una cola con maxsize detiene al productor cuando se llena el búfer. Un "
                "número fijo de workers limita la concurrencia. Llama a task_done() en "
                "finally para mantener el contador aun cuando falle una operación.",
            ),
            example_code="""import asyncio


async def worker(queue: asyncio.Queue[int | None], results: dict[int, int]) -> None:
    while True:
        value = await queue.get()
        try:
            if value is None:
                return
            await asyncio.sleep(0.01)
            results[value] = value * value
        finally:
            queue.task_done()


async def main() -> None:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=4)
    results: dict[int, int] = {}
    worker_count = 2
    async with asyncio.TaskGroup() as tasks:
        for _ in range(worker_count):
            tasks.create_task(worker(queue, results))
        for value in range(8):
            await queue.put(value)
        await queue.join()
        for _ in range(worker_count):
            await queue.put(None)
    assert results == {value: value * value for value in range(8)}


if __name__ == "__main__":
    asyncio.run(main())""",
            steps=(
                (
                    "Уменьшите maxsize до 1 и убедитесь, что набор результатов тот же.",
                    "Reduce maxsize to 1 and check that the result set stays the same.",
                    "Reduce maxsize a 1 y comprueba que los resultados se mantienen.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.PROFESSIONAL,
            title=(
                "Дедлайны, отмена и группы исключений",
                "Deadlines, cancellation, and exception groups",
                "Plazos, cancelación y grupos de excepciones",
            ),
            explanation=(
                "asyncio.timeout ограничивает время операции. Если задача завершается "
                "ошибкой, TaskGroup отменяет соседние задачи и объединяет ошибки в "
                "ExceptionGroup. except* обрабатывает выбранный тип ошибки.",
                "asyncio.timeout bounds the time for an operation. If one task fails, "
                "TaskGroup cancels its siblings and groups failures in an ExceptionGroup. "
                "Use except* to handle a selected exception type.",
                "asyncio.timeout limita el tiempo de una operación. Si una tarea falla, "
                "TaskGroup cancela las tareas hermanas y agrupa los errores en un "
                "ExceptionGroup. except* permite tratar un tipo de error concreto.",
            ),
            example_code="""import asyncio


async def limited_request() -> None:
    async with asyncio.timeout(0.02):
        await asyncio.sleep(1)


async def other_request(closed: asyncio.Event) -> None:
    try:
        await asyncio.sleep(10)
    finally:
        closed.set()


async def main() -> None:
    closed = asyncio.Event()
    try:
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(limited_request())
            tasks.create_task(other_request(closed))
    except* TimeoutError as errors:
        print(f"{len(errors.exceptions)} request timed out")

    assert closed.is_set()


if __name__ == "__main__":
    asyncio.run(main())""",
            steps=(
                (
                    "Проверьте, что тайм-аут отменяет соседнюю задачу и её finally срабатывает.",
                    "Check that a timeout cancels the sibling task and runs its finally block.",
                    "Comprueba que el plazo cancela la otra tarea y ejecuta su bloque finally.",
                ),
            ),
        ),
    ),
    LessonTopic.INSTALL: localize_pages(
        LocalizedPage(
            title=(
                "Проверка версии и сборки Python",
                "Check the Python version and build",
                "Comprobar la versión y la compilación de Python",
            ),
            explanation=(
                "Проверьте расположение интерпретатора и версию встроенной SQLite. "
                "Стандартная сборка CPython подходит для большинства проектов. "
                "У свободнопоточной сборки могут отличаться требования к колёсам зависимостей. "
                "Команды показывают базовую версию 3.14. Для 3.15 проверьте "
                "совместимость зависимостей проекта.",
                "Check the interpreter location and bundled SQLite version. A regular "
                "CPython build suits most projects. A free-threaded build can require "
                "different dependency wheels. The commands use the 3.14 baseline. "
                "Check project dependency compatibility before using 3.15.",
                "Comprueba la ubicación del intérprete y la versión de SQLite. Una "
                "compilación estándar de CPython sirve para la mayoría de proyectos. "
                "Una compilación sin GIL puede necesitar paquetes binarios distintos. "
                "Los comandos usan la versión base 3.14. Comprueba la compatibilidad "
                "de las dependencias antes de usar 3.15.",
            ),
            install_code="""python3.14 --version
python3.14 diagnose.py""",
            example_code="""# diagnose.py
import sqlite3
import sys
import sysconfig

print("Version:", sys.version.split()[0])
print("Executable:", sys.executable)
print("SQLite:", sqlite3.sqlite_version)
print("Free-threaded build:", bool(sysconfig.get_config_var("Py_GIL_DISABLED")))
print("Virtual environment:", sys.prefix != sys.base_prefix)""",
            steps=(
                (
                    "Установите поддерживаемый CPython по инструкции python.org/downloads.",
                    "Install a supported CPython build using python.org/downloads.",
                    "Instala una versión compatible de CPython desde python.org/downloads.",
                ),
                (
                    "Сохраните код как diagnose.py. В Windows запустите py -3.14 diagnose.py.",
                    "Save as diagnose.py. On Windows, run py -3.14 diagnose.py.",
                    "Guarda el código como diagnose.py. En Windows, ejecuta py -3.14 diagnose.py.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.INTERMEDIATE,
            title=(
                "Изолированное окружение для проекта",
                "An isolated project environment",
                "Un entorno aislado para el proyecto",
            ),
            explanation=(
                "Создайте .venv внутри проекта. Запуск pip через интерпретатор этого "
                "окружения устанавливает пакеты в нужное место даже без активации "
                "оболочки. pip check проверяет совместимость установленных зависимостей.",
                "Create .venv within the project. Run pip through that environment's "
                "interpreter to install packages to the right place without activating "
                "the shell. pip check verifies installed dependency compatibility.",
                "Crea .venv en el proyecto. Ejecuta pip con el intérprete de ese entorno "
                "para instalar paquetes en el lugar correcto sin activar la shell. "
                "pip check comprueba que las dependencias instaladas sean compatibles.",
            ),
            install_code="""python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check""",
            steps=(
                (
                    "Сохраните зависимости проекта в requirements.txt перед установкой.",
                    "List your project's dependencies in requirements.txt before installing.",
                    "Enumera las dependencias en requirements.txt antes de instalarlas.",
                ),
                (
                    r"В Windows используйте py -3.14 -m venv .venv и .venv\Scripts\python.exe.",
                    r"On Windows, use py -3.14 -m venv .venv and .venv\Scripts\python.exe.",
                    r"En Windows, usa py -3.14 -m venv .venv y .venv\Scripts\python.exe.",
                ),
                (
                    "Повторите проверку из предыдущей страницы через интерпретатор .venv.",
                    "Repeat the previous page's diagnostic using the .venv interpreter.",
                    "Repite el diagnóstico de la página anterior con el intérprete de .venv.",
                ),
            ),
        ),
    ),
    LessonTopic.PYDANTIC: localize_pages(
        LocalizedPage(
            title=(
                "Вложенные модели и список объектов",
                "Nested models and object lists",
                "Modelos anidados y listas de objetos",
            ),
            explanation=(
                "TypeAdapter валидирует тип контейнера без дополнительной модели-обёртки. "
                "Проверьте JSON на границе приложения. loc укажет индекс элемента "
                "и поле, где произошла ошибка.",
                "TypeAdapter validates a container type without a wrapper model. Validate "
                "JSON at the application boundary. The loc entry identifies the item "
                "index and field where validation failed.",
                "TypeAdapter valida un tipo contenedor sin un modelo auxiliar. Valida "
                "el JSON en el límite de la aplicación. El campo loc indica el índice "
                "del elemento y el campo donde falló la validación.",
            ),
            install_code='python -m pip install "pydantic>=2.11,<3"',
            example_code="""from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


class Item(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    sku: Annotated[str, Field(min_length=1, max_length=40)]
    units: Annotated[int, Field(gt=0, le=100)]


BATCH = TypeAdapter(list[Item])
items = BATCH.validate_json('[{"sku":"P01","units":3}]')
assert items[0].units == 3

try:
    BATCH.validate_json('[{"sku":"P01","units":"3"}]')
except ValidationError as exc:
    error = exc.errors(include_input=False)[0]
    assert error["loc"] == (0, "units")
    print(error["loc"], error["type"])""",
            steps=(
                (
                    "Добавьте второй элемент с лишним полем и проверьте индекс ошибки.",
                    "Add a second item with an extra field and check the error's item index.",
                    "Añade un segundo elemento con un campo extra y comprueba su índice.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.INTERMEDIATE,
            title=(
                "Модели событий с дискриминатором",
                "Event models with discriminators",
                "Modelos de eventos con discriminadores",
            ),
            explanation=(
                "Укажите поле kind с Literal в каждой модели события. Дискриминатор "
                "выбирает нужную схему по этому полю. Проверка берёт только "
                "поля выбранного варианта.",
                "Give each event model a kind field with a Literal tag. The discriminator "
                "selects the corresponding schema from that tag. Validation then checks "
                "the fields for the selected variant.",
                "Da a cada modelo de evento un campo kind con una etiqueta Literal. "
                "El discriminador selecciona el esquema correspondiente. La validación "
                "comprueba los campos de la variante elegida.",
            ),
            example_code="""from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class Added(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    kind: Literal["added"]
    sku: str


class Removed(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    kind: Literal["removed"]
    item_id: Annotated[int, Field(gt=0)]


type Event = Annotated[Added | Removed, Field(discriminator="kind")]

events = TypeAdapter(list[Event])
parsed = events.validate_python(
    [{"kind": "added", "sku": "P01"}, {"kind": "removed", "item_id": 7}],
)
assert isinstance(parsed[1], Removed)
print(events.dump_json(parsed).decode())""",
            steps=(
                (
                    "Передайте неизвестный kind и проверьте отклонение до обработки события.",
                    "Supply an unknown kind and check that it is rejected before processing.",
                    "Pasa un kind desconocido y comprueba que se rechaza antes de procesarlo.",
                ),
            ),
        ),
        LocalizedPage(
            level=LessonLevel.PROFESSIONAL,
            title=(
                "Секреты, публичные модели и диагностика",
                "Secrets, public models, and diagnostics",
                "Secretos, modelos públicos y diagnósticos",
            ),
            explanation=(
                "SecretStr маскирует значение в представлении модели. Для ответа API "
                "создайте отдельную публичную модель только с разрешёнными полями. "
                "В диагностике выводите коды ошибок вместо данных запроса.",
                "SecretStr masks its value in the model representation. Use a separate "
                "public model with approved fields for an API response. Log validation "
                "error codes without the original request data.",
                "SecretStr oculta el valor al mostrar el modelo. Usa un modelo público "
                "separado con los campos permitidos para la respuesta de la API. "
                "Registra los códigos de validación sin los datos originales.",
            ),
            example_code="""from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    service: str
    secret: SecretStr


class PublicService(BaseModel):
    service: str


credentials = Credentials(service="catalog", secret=SecretStr("example"))
response = PublicService(service=credentials.service)
assert response.model_dump() == {"service": "catalog"}

try:
    Credentials.model_validate({"service": "catalog", "secret": []})
except ValidationError as exc:
    print([error["type"] for error in exc.errors(include_input=False)])""",
            steps=(
                (
                    "Проверьте, что публичный JSON вообще не содержит ключ secret.",
                    "Check that the public JSON omits the secret key entirely.",
                    "Comprueba que el JSON público omite por completo la clave secret.",
                ),
            ),
        ),
    ),
}
