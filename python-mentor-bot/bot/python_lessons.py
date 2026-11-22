"""Hands-on lessons for Python 3.14, Python 3.15 and automated testing."""

from typing import Final

from bot.lesson_models import (
    Lesson,
    LessonLevel,
    LessonTopic,
    LocalizedPage,
    localize_lesson,
    localize_pages,
)

PYTHON_LESSONS: Final[dict[LessonTopic, dict[str, Lesson]]] = {
    LessonTopic.PYTHON_314: localize_lesson(
        ("🐍 Python 3.14", "🐍 Python 3.14", "🐍 Python 3.14"),
        LocalizedPage(
            title=("Проверка интерпретатора", "Check your interpreter", "Comprueba el intérprete"),
            explanation=(
                "Проверьте интерпретатор из виртуального окружения перед запуском. "
                "Пример выводит версию и реализацию Python. Это пригодится и в CI.",
                "Check your virtual environment's interpreter before running examples. "
                "The exercise prints the Python version and implementation for local use and CI.",
                "Comprueba el intérprete del entorno virtual antes de ejecutar ejemplos. "
                "El ejercicio muestra la versión y la implementación para tu equipo y CI.",
            ),
            example_code="""import platform
import sys

if sys.version_info < (3, 14):
    raise SystemExit("Python 3.14 or later is required")
print(platform.python_implementation(), platform.python_version())
print(sys.executable)""",
            steps=(
                (
                    "Сверьте список изменений в docs.python.org/3.14/whatsnew/3.14.html.",
                    "Read the change list at docs.python.org/3.14/whatsnew/3.14.html.",
                    "Consulta los cambios en docs.python.org/3.14/whatsnew/3.14.html.",
                ),
            ),
        ),
        LocalizedPage(
            title=("Шаблоны t-строк", "Template strings", "Cadenas de plantilla"),
            explanation=(
                "t-строка возвращает Template с литералами и интерполяциями. В этом примере "
                "рендерер экранирует подстановки для HTML-текста. Сам синтаксис этого не делает.",
                "A t-string produces a Template with literals and interpolations. This renderer "
                "escapes substitutions for HTML text. The syntax alone performs no escaping.",
                "Una cadena t produce un Template con literales e interpolaciones. "
                "Este renderizador escapa los valores para texto HTML. La sintaxis no los escapa.",
            ),
            example_code="""from html import escape
from string.templatelib import Interpolation, Template


def render_text(template: Template) -> str:
    return "".join(
        escape(str(part.value)) if isinstance(part, Interpolation) else part
        for part in template
    )


name = "<Ada>"
assert render_text(t"<strong>{name}</strong>") == "<strong>&lt;Ada&gt;</strong>"
""",
            steps=(
                (
                    "Используйте только простые подстановки. Этот пример относится к PEP 750.",
                    "Use plain interpolations for this renderer. See PEP 750.",
                    "Usa interpolaciones simples con este renderizador. Consulta PEP 750.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=(
                "Отложенные аннотации",
                "Deferred annotations",
                "Anotaciones diferidas",
            ),
            explanation=(
                "В 3.14 аннотации по умолчанию вычисляются при обращении к ним. "
                "annotationlib позволяет выбрать формат VALUE или STRING. "
                "PEP 649 и 749 описывают механизм.",
                "On 3.14, annotations are evaluated on demand by default. "
                "annotationlib lets tooling choose VALUE or STRING output. See PEPs 649 and 749.",
                "En 3.14, las anotaciones se evalúan bajo demanda. "
                "annotationlib permite elegir el formato VALUE o STRING. Consulta PEP 649 y 749.",
            ),
            example_code="""from annotationlib import Format, get_annotations


def find_product(product_id: int) -> Product:
    return Product(product_id)


class Product:
    def __init__(self, product_id: int) -> None:
        self.id = product_id


assert get_annotations(find_product)["return"] is Product
assert get_annotations(find_product, format=Format.STRING)["return"] == "Product"
""",
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Сжатие Zstandard", "Zstandard compression", "Compresión Zstandard"),
            explanation=(
                "В стандартной библиотеке 3.14 есть compression.zstd. Для маленького "
                "доверенного блока используйте compress/decompress. Для крупных файлов "
                "пишите и читайте потоками и учитывайте размер распаковки.",
                "Python 3.14 includes compression.zstd. Use compress/decompress for small "
                "trusted payloads. Stream large files and bound the decompressed size.",
                "Python 3.14 incluye compression.zstd. Usa compress/decompress para bloques "
                "pequeños y de confianza. Procesa archivos grandes por flujo y limita la salida.",
            ),
            example_code="""from compression import zstd

payload = b"python mentor lesson 1" * 100
compressed = zstd.compress(payload)
assert zstd.decompress(compressed) == payload
print(len(payload), len(compressed))""",
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=(
                "Изолированные интерпретаторы",
                "Isolated interpreters",
                "Intérpretes aislados",
            ),
            explanation=(
                "InterpreterPoolExecutor запускает задачи в отдельных интерпретаторах. "
                "Проверьте стоимость сериализации перед применением к CPU-задачам. "
                "Free-threaded сборка CPython 3.14 официально поддерживается "
                "как отдельный вариант.",
                "InterpreterPoolExecutor runs workers in separate interpreters. Measure "
                "serialization cost before using it for CPU workloads. The free-threaded "
                "CPython 3.14 build is officially supported as an optional build.",
                "InterpreterPoolExecutor ejecuta tareas en intérpretes separados. Mide el "
                "coste de serialización antes de usarlo para trabajo de CPU. "
                "CPython 3.14 con ejecución libre de hilos es una compilación opcional compatible.",
            ),
            example_code="""from concurrent.futures import InterpreterPoolExecutor
from math import isqrt

if __name__ == "__main__":
    with InterpreterPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(isqrt, [16, 81, 100]))
    assert result == [4, 9, 10]
""",
            steps=(
                (
                    "Сравните время с обычным циклом на реальном объёме данных.",
                    "Compare against a plain loop with a realistic workload.",
                    "Compara con un bucle normal usando una carga representativa.",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
    LessonTopic.PYTHON_315: localize_lesson(
        ("✨ Что нового в 3.15", "✨ What's new in 3.15", "✨ Novedades de 3.15"),
        LocalizedPage(
            title=("Релиз 3.15 и UTF-8", "Python 3.15 and UTF-8", "Python 3.15 y UTF-8"),
            explanation=(
                "Python 3.15.0 вышел 9 октября 2026 года. PEP 686 включает режим UTF-8 "
                "по умолчанию. Для совместимости и ясности продолжайте явно задавать "
                "кодировку файловых форматов.",
                "Python 3.15.0 was released on October 9, 2026. PEP 686 enables UTF-8 mode "
                "by default. Keep file encodings explicit for portability and clarity.",
                "Python 3.15.0 se publicó el 9 de octubre de 2026. PEP 686 activa el modo UTF-8 "
                "por defecto. Sigue especificando la codificación de los formatos de archivo.",
            ),
            example_code="""from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    path = Path(directory) / "greeting.txt"
    path.write_text("Привет · Hello · Hola", encoding="utf-8")
    assert path.read_bytes().decode("utf-8") == path.read_text(encoding="utf-8")
""",
            steps=(
                (
                    "Список новшеств приведён в docs.python.org/3.15/whatsnew/3.15.html.",
                    "Find the full list at docs.python.org/3.15/whatsnew/3.15.html.",
                    "Consulta la lista completa en docs.python.org/3.15/whatsnew/3.15.html.",
                ),
            ),
        ),
        LocalizedPage(
            title=(
                "Распаковка в включениях",
                "Unpacking in comprehensions",
                "Desempaquetado en comprensiones",
            ),
            explanation=(
                "PEP 798 добавляет * и ** в comprehension. Списки разворачиваются "
                "в порядке обхода. При слиянии словарей последнее значение ключа побеждает.",
                "PEP 798 adds * and ** to comprehensions. Lists flatten in iteration order. "
                "When merging dictionaries, the last value for a duplicate key wins.",
                "PEP 798 añade * y ** a las comprensiones. Las listas se aplanan en orden. "
                "Al combinar diccionarios, prevalece el último valor de una clave repetida.",
            ),
            example_code="""batches = [[1, 2], [3], [4, 5]]
assert [*batch for batch in batches] == [1, 2, 3, 4, 5]

layers = [{"timeout": 3}, {"retry": 2}, {"timeout": 5}]
assert {**layer for layer in layers} == {"timeout": 5, "retry": 2}

assert [item for batch in batches for item in batch] == [1, 2, 3, 4, 5]
""",
            steps=(
                (
                    "Последняя строка показывает эквивалент, работающий на 3.14.",
                    "The last assertion shows an equivalent that runs on 3.14.",
                    "La última comprobación muestra un equivalente que funciona en 3.14.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Настройки с frozendict", "Settings with frozendict", "Ajustes con frozendict"),
            explanation=(
                "frozendict из PEP 814 запрещает изменение связей ключ—значение. "
                "Вложенные объекты не замораживаются. Для ключа кеша все компоненты "
                "должны быть хешируемыми.",
                "PEP 814's frozendict prevents changing key-value bindings. It does not freeze "
                "nested objects. Cache keys require all components to be hashable.",
                "frozendict de PEP 814 impide cambiar los pares clave-valor. No congela los "
                "objetos internos. Para usarlo como clave de caché, todos los elementos deben "
                "admitir hash.",
            ),
            example_code="""from collections.abc import Mapping


def render_theme(settings: Mapping[str, str]) -> str:
    return f"theme:{settings['theme']}"


theme = frozendict(theme="dark", locale="en")
cache = {theme: render_theme(theme)}
assert cache[frozendict(locale="en", theme="dark")] == "theme:dark"
""",
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Отсутствующее значение", "Missing values", "Valores ausentes"),
            explanation=(
                "sentinel из PEP 661 различает пропущенный аргумент и явный None. "
                "Это удобно для частичных обновлений, где None очищает значение.",
                "PEP 661's sentinel separates an omitted argument from explicit None. "
                "This is useful for partial updates where None clears a value.",
                "sentinel de PEP 661 distingue un argumento omitido de None explícito. "
                "Sirve para actualizaciones parciales donde None borra un valor.",
            ),
            example_code="""MISSING = sentinel("MISSING")


def update_nickname(
    current: str | None,
    value: str | None | MISSING = MISSING,
) -> str | None:
    if value is MISSING:
        return current
    return value


assert update_nickname("Ada") == "Ada"
assert update_nickname("Ada", None) is None
assert update_nickname(None, "Grace") == "Grace"
""",
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Ленивые импорты", "Lazy imports", "Importaciones diferidas"),
            explanation=(
                "PEP 810 позволяет отложить загрузку модуля до первого обращения к имени. "
                "Добавляйте lazy на уровне модуля, если импорт нужен лишь редкому сценарию. "
                "Ошибки импорта тоже проявятся позже.",
                "PEP 810 allows a module to load on first use. Use lazy at module level for "
                "imports that only uncommon code paths need. Import errors are delayed too.",
                "PEP 810 permite cargar un módulo cuando se usa por primera vez. Añade lazy "
                "en el módulo para rutas poco frecuentes. Los errores también se aplazan.",
            ),
            example_code="""lazy import json


def render(data: dict[str, int], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(data, sort_keys=True)
    return ", ".join(f"{key}={value}" for key, value in sorted(data.items()))


assert render({"count": 3}, as_json=False) == "count=3"
assert render({"count": 3}, as_json=True) == '{"count": 3}'
""",
            level=LessonLevel.PROFESSIONAL,
        ),
        LocalizedPage(
            title=("Профилирование на 3.15", "Profiling on 3.15", "Perfilado en 3.15"),
            explanation=(
                "PEP 799 группирует профилировщики в пакете profiling. tracing считает "
                "вызовы и их время. sampling периодически снимает стеки. "
                "Сравнивайте результаты на одинаковой нагрузке.",
                "PEP 799 groups profilers in profiling. tracing records calls and timings. "
                "sampling periodically observes stack frames. Compare runs on the same workload.",
                "PEP 799 agrupa perfiladores en profiling. tracing registra llamadas y tiempos. "
                "sampling observa pilas de forma periódica. Compara con la misma carga.",
            ),
            install_code="python3.15 -m profiling.tracing -s cumulative profile_demo.py",
            example_code="""# profile_demo.py
def workload() -> int:
    return sum(value ** 2 for value in range(400_000))


if __name__ == "__main__":
    for _ in range(10):
        workload()
""",
            steps=(
                (
                    "На поддерживаемой сборке сравните с "
                    "python3.15 -m profiling.sampling run profile_demo.py.",
                    "On a supported build, compare with "
                    "python3.15 -m profiling.sampling run profile_demo.py.",
                    "En una compilación compatible, compara con "
                    "python3.15 -m profiling.sampling run profile_demo.py.",
                ),
                (
                    "Если sampling не может читать процесс, используйте результат tracing.",
                    "If sampling cannot inspect the process, use the tracing result.",
                    "Si sampling no puede inspeccionar el proceso, usa el resultado de tracing.",
                ),
                (
                    "Увеличьте число повторов, если семплов мало. Найдите горячую функцию.",
                    "Increase the repeat count if samples are sparse. Find the hot function.",
                    "Aumenta las repeticiones si hay pocas muestras. Busca la función más costosa.",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
    LessonTopic.TEST: localize_lesson(
        ("✅ Тестирование", "✅ Testing", "✅ Pruebas"),
        LocalizedPage(
            title=(
                "Первые автотесты",
                "Your first automated tests",
                "Tus primeras pruebas automáticas",
            ),
            explanation=(
                "Начните с чистой функции и двух проверок. Первая фиксирует обычный случай, "
                "вторая — ошибку на границе допустимых данных.",
                "Start with a pure function and two checks. One locks in normal behavior, "
                "the other covers an invalid boundary value.",
                "Empieza con una función pura y dos comprobaciones. Una cubre el caso normal "
                "y la otra un valor límite no válido.",
            ),
            install_code="python -m unittest -v test_shipping.py",
            example_code="""# test_shipping.py
import unittest


def shipping_cents(units: int) -> int:
    if units < 1:
        raise ValueError("units must be positive")
    return 300 + 25 * units


class ShippingTests(unittest.TestCase):
    def test_normal_order(self) -> None:
        self.assertEqual(shipping_cents(4), 400)

    def test_empty_order(self) -> None:
        with self.assertRaises(ValueError):
            shipping_cents(0)
""",
        ),
        LocalizedPage(
            title=("Параметры и фикстуры", "Parameters and fixtures", "Parámetros y fixtures"),
            explanation=(
                "В pytest параметризация проверяет несколько границ без копирования теста. "
                "tmp_path создаёт отдельный каталог для каждой проверки.",
                "In pytest, parametrization covers multiple boundaries without copying test "
                "code. tmp_path gives each test a separate temporary directory.",
                "En pytest, la parametrización cubre varios límites sin duplicar pruebas. "
                "tmp_path ofrece un directorio temporal independiente.",
            ),
            install_code="""python -m pip install pytest
python -m pytest -q test_export.py""",
            example_code="""# test_export.py
from pathlib import Path

import pytest


@pytest.mark.parametrize("labels", [[], ["alpha"], ["café", "東京"]])
def test_export_round_trip(tmp_path: Path, labels: list[str]) -> None:
    path = tmp_path / "labels.txt"
    path.write_text("\\n".join(labels), encoding="utf-8")
    assert path.read_text(encoding="utf-8").splitlines() == labels
""",
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=(
                "Контракт и проверка ошибки",
                "A contract and its failure path",
                "Un contrato y su ruta de error",
            ),
            explanation=(
                "Проверяйте публичный результат, форму ошибки и сохранность данных. "
                "Этот интеграционный тест проверяет контракт ограничения в настоящей SQLite.",
                "Test the public result, failure type and saved state. This integration "
                "test checks a constraint against a real SQLite engine.",
                "Comprueba el resultado público, el tipo de error y los datos guardados. "
                "Esta prueba de integración verifica una restricción en SQLite real.",
            ),
            install_code="""python -m pip install pytest
python -m pytest -q test_store.py""",
            example_code="""# test_store.py
from contextlib import closing
from sqlite3 import IntegrityError, connect

import pytest


def test_unique_title_is_atomic() -> None:
    with closing(connect(":memory:")) as db:
        db.execute("CREATE TABLE item (title TEXT UNIQUE NOT NULL)")
        with db:
            db.execute("INSERT INTO item VALUES (?)", ("first",))
        with pytest.raises(IntegrityError), db:
            db.execute("INSERT INTO item VALUES (?)", ("second",))
            db.execute("INSERT INTO item VALUES (?)", ("first",))
        assert db.execute("SELECT title FROM item").fetchall() == [("first",)]
""",
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
}


FRAMEWORK_PAGES: Final = localize_pages(
    LocalizedPage(
        title=(
            "Логика приложения отдельно от HTTP",
            "Application logic outside HTTP",
            "Lógica de aplicación fuera de HTTP",
        ),
        explanation=(
            "Храните расчёты отдельно от представлений. Django, FastAPI и Flask могут "
            "вызывать одну чистую функцию. Тест функции выполняется без сервера.",
            "Keep calculations outside views. Django, FastAPI and Flask can all call "
            "the same pure function. Its tests run without starting a server.",
            "Separa los cálculos de las vistas. Django, FastAPI y Flask pueden llamar "
            "a la misma función pura. Sus pruebas no necesitan un servidor.",
        ),
        example_code="""from decimal import Decimal


def invoice_total(price: Decimal, quantity: int) -> Decimal:
    if price < 0 or quantity < 1:
        raise ValueError("invalid order")
    return price * quantity


assert invoice_total(Decimal("19.99"), 2) == Decimal("39.98")
""",
        level=LessonLevel.INTERMEDIATE,
    ),
    LocalizedPage(
        title=(
            "Проверяем HTTP-контракт",
            "Test the HTTP contract",
            "Comprueba el contrato HTTP",
        ),
        explanation=(
            "Фреймворк меняется, а контракт клиента остаётся. Зафиксируйте статус "
            "и поля ответа в тесте с in-process клиентом FastAPI, Django или Flask. "
            "Функцию из примера можно переиспользовать для разных таких клиентов.",
            "Frameworks change while client contracts remain. Verify response status and "
            "fields using an in-process client for FastAPI, Django or Flask. "
            "The helper below works with the responses of those clients.",
            "Los frameworks cambian y los contratos del cliente se mantienen. Verifica "
            "el estado y los campos con un cliente interno de FastAPI, Django o Flask. "
            "La función del ejemplo admite las respuestas de estos clientes.",
        ),
        example_code="""from collections.abc import Callable
from typing import Protocol


class Response(Protocol):
    @property
    def status_code(self) -> int: ...


def assert_readiness(response: Response, read_json: Callable[[], object]) -> None:
    assert response.status_code == 200
    assert read_json() == {"status": "ok"}


# Pass client.get("/health/") and its .json method for FastAPI or Django.
# For Flask, pass its .get_json method instead.
""",
        level=LessonLevel.PROFESSIONAL,
    ),
)
