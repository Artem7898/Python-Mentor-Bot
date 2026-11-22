"""Localized projects for Python fundamentals, syntax, objects and files."""

# Russian lesson prose intentionally mixes Cyrillic and programming terms.
# ruff: noqa: RUF001

from typing import Final

from bot.lesson_models import LessonLevel, LessonPage, LessonTopic, LocalizedPage, localize_pages

CORE_PAGES: Final[dict[LessonTopic, dict[str, tuple[LessonPage, ...]]]] = {
    LessonTopic.BASICS: localize_pages(
        LocalizedPage(
            title=("Чек за покупку", "Calculate a receipt", "Calcular un recibo"),
            explanation=(
                "Ввод из терминала приходит строкой. int преобразует запись целого числа "
                "или вызывает ValueError. Для простого расчёта цены в одной валюте "
                "храните цену в целых копейках. Остаток от деления задаёт дробную часть.",
                "Terminal input is text. int converts an integer representation or raises "
                "ValueError. For a simple single-currency calculation, keep prices in "
                "integer cents and use the remainder for the fractional part.",
                "La terminal entrega texto. int convierte una representación entera o "
                "lanza ValueError. Para un cálculo sencillo en una moneda, guarda los "
                "precios en céntimos enteros y usa el resto para la parte fraccionaria.",
            ),
            example_code="""price_cents = 249

for raw_quantity in ("3", "zero", "-2"):
    try:
        quantity = int(raw_quantity)
        if quantity <= 0:
            raise ValueError("Choose a positive quantity")
    except ValueError:
        print(f"Invalid quantity: {raw_quantity!r}")
        continue
    units, cents = divmod(price_cents * quantity, 100)
    print(f"Total: {units}.{cents:02d}")""",
            steps=(
                (
                    "Замените пробные строки на input и проверьте ввод числа, пробела и нуля.",
                    "Replace the sample strings with input and try a number, a space and zero.",
                    "Sustituye los ejemplos por input y prueba un número, un espacio y cero.",
                ),
            ),
            level=LessonLevel.BEGINNER,
        ),
        LocalizedPage(
            title=("Расходы по категориям", "Group expenses", "Agrupar gastos"),
            explanation=(
                "Кортеж группирует поля одной записи, а словарь хранит сумму по категории. "
                "dict.get задаёт начальное значение для новой категории. sorted упорядочивает "
                "ключи и делает вывод предсказуемым.",
                "A tuple groups the fields of one expense and a dictionary stores the total "
                "per category. dict.get provides a starting value for a new category. sorted "
                "orders the keys for predictable output.",
                "Una tupla agrupa los campos de cada gasto y un diccionario acumula el total "
                "por categoría. dict.get da un valor inicial para una categoría nueva. "
                "sorted ordena las claves para que la salida sea predecible.",
            ),
            example_code="""expenses = [("food", 550), ("travel", 250), ("food", 175)]
totals: dict[str, int] = {}

for category, cents in expenses:
    totals[category] = totals.get(category, 0) + cents

for category in sorted(totals):
    print(f"{category}: {totals[category]} cents")

assert totals == {"food": 725, "travel": 250}""",
            steps=(
                (
                    "Для пустого списка проверьте условие assert not totals.",
                    "For an empty expense list, replace the assertion with assert not totals.",
                    "Con una lista vacía, cambia la comprobación a assert not totals.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Функция расчёта доставки", "A shipping fee function", "Función de envío"),
            explanation=(
                "Чистая функция вычисляет результат по аргументам и не трогает ввод-вывод. "
                "Звёздочка требует передавать следующие параметры по имени. Отдельно "
                "проверьте значение на пороге бесплатной доставки.",
                "A pure function computes a result from its arguments without doing I/O. "
                "The star makes the following parameters keyword-only. Check the exact "
                "free-shipping threshold separately.",
                "Una función pura calcula el resultado a partir de sus argumentos sin "
                "hacer operaciones de E/S. El asterisco obliga a nombrar los parámetros "
                "siguientes. Comprueba por separado el límite exacto de envío gratuito.",
            ),
            example_code="""def shipping_fee(subtotal_cents: int, *, express: bool = False) -> int:
    if subtotal_cents < 0:
        raise ValueError("Subtotal cannot be negative")
    if express:
        return 799
    return 0 if subtotal_cents >= 5_000 else 399


assert shipping_fee(4_999) == 399
assert shipping_fee(5_000) == 0
assert shipping_fee(5_000, express=True) == 799
print(shipping_fee(3_200, express=True))""",
            steps=(
                (
                    "Добавьте проверку нулевой суммы и отрицательной суммы.",
                    "Add checks for a zero subtotal and a negative subtotal.",
                    "Añade comprobaciones con un subtotal de cero y uno negativo.",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
    LessonTopic.SYNTAX: localize_pages(
        LocalizedPage(
            title=(
                "Разбор заявки через match",
                "Match a request shape",
                "Descomponer una solicitud",
            ),
            explanation=(
                "Структурное сопоставление по PEP 634 проверяет форму словаря и связывает "
                "имена. Условие после if проверяет диапазон. Шаблон int() также принимает "
                "bool, поэтому для идентификатора проверяем точный тип.",
                "Structural pattern matching (PEP 634) checks the shape of a dictionary "
                "and binds names. A guard checks the value range. An int() pattern also "
                "matches bool, so the identifier check requires the exact type.",
                "La coincidencia estructural (PEP 634) comprueba la forma del diccionario "
                "y asigna nombres. La guarda valida el rango. El patrón int() también "
                "acepta bool, por eso se exige el tipo exacto del identificador.",
            ),
            example_code="""def request_label(payload: object) -> str:
    match payload:
        case {"action": "pickup", "order": int(order)} if type(order) is int and order > 0:
            return f"Pickup #{order}"
        case {"action": "cancel", "order": int(order)} if type(order) is int and order > 0:
            return f"Cancel #{order}"
        case _:
            return "Unsupported request"


assert request_label({"action": "pickup", "order": True}) == "Unsupported request"
print(request_label({"action": "pickup", "order": 17}))""",
            steps=(
                (
                    "Проверьте заявки без поля order и с order в виде строки.",
                    "Try requests with no order field and with order supplied as a string.",
                    "Prueba solicitudes sin el campo order y con order como cadena.",
                ),
            ),
            level=LessonLevel.BEGINNER,
        ),
        LocalizedPage(
            title=(
                "Обобщённый выбор первого элемента",
                "A generic first item",
                "Primer elemento genérico",
            ),
            explanation=(
                "Запись first[T] по PEP 695 (Python 3.12+) объявляет параметр типа. "
                "Анализатор выводит тип результата по аргументу. Iterable позволяет "
                "обработать и список, и генератор, прочитав только первый элемент.",
                "The first[T] syntax from PEP 695 (Python 3.12+) declares a type parameter. "
                "The type checker infers the result type from the argument. Iterable "
                "accepts a list or a generator while reading just the first item.",
                "La sintaxis first[T] de PEP 695 (Python 3.12+) declara un parámetro de "
                "tipo. El analizador deduce el tipo devuelto del argumento. Iterable "
                "acepta listas y generadores y permite leer solo el primer elemento.",
            ),
            example_code="""from collections.abc import Iterable


def first[T](items: Iterable[T]) -> T | None:
    return next(iter(items), None)


first_stop = first(name for name in ("Central", "Park"))
first_fee = first([399, 799])
print(first_stop, first_fee)
assert first(()) is None""",
            steps=(
                (
                    "Проверьте типы first_stop и first_fee в редакторе с анализатором типов.",
                    "Inspect the types of first_stop and first_fee in a type-aware editor.",
                    "Inspecciona los tipos de first_stop y first_fee en un editor con analizador.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=(
                "Сужение типов с TypeIs",
                "Narrow types with TypeIs",
                "Refinar tipos con TypeIs",
            ),
            explanation=(
                "TypeIs из PEP 742 доступен в typing с Python 3.13. При истинной "
                "проверке анализатор уточняет тип до str, при ложной исключает str "
                "из объединения. Проверка должна точно соответствовать заявленному типу.",
                "TypeIs from PEP 742 is in typing since Python 3.13. A true check narrows "
                "to str and a false check removes str from the union. The predicate "
                "must recognize exactly the declared type.",
                "TypeIs de PEP 742 está en typing desde Python 3.13. Si la comprobación "
                "es verdadera, el tipo se reduce a str. Si es falsa, str se excluye de "
                "la unión. El predicado debe reconocer exactamente el tipo declarado.",
            ),
            example_code="""from typing import TypeIs


def is_address(value: int | str) -> TypeIs[str]:
    return isinstance(value, str)


def display_destination(value: int | str) -> str:
    if is_address(value):
        return value.strip()
    return f"Locker {value:03d}"


assert display_destination(12) == "Locker 012"
assert display_destination("  Main Street  ") == "Main Street"
print(display_destination(12))""",
            steps=(
                (
                    "Замените тело is_address проверкой непустой строки и объясните, "
                    "почему такая функция нарушает контракт TypeIs[str].",
                    "Replace the body with a nonempty-string check and explain why it would "
                    "violate the TypeIs[str] contract.",
                    "Cambia el cuerpo por una comprobación de cadena no vacía y explica por "
                    "qué rompería el contrato de TypeIs[str].",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
    LessonTopic.OOP: localize_pages(
        LocalizedPage(
            title=(
                "Билет как объект-значение",
                "A ticket as a value object",
                "Billete como objeto de valor",
            ),
            explanation=(
                "dataclass создаёт конструктор и сравнение по полям. frozen запрещает "
                "обычное присваивание атрибутов, slots убирает обычный словарь атрибутов "
                "экземпляра. __post_init__ проверяет условия, которые аннотации не проверяют.",
                "A dataclass generates the constructor and field-based equality. frozen "
                "prevents regular attribute assignment and slots removes the instance's "
                "usual attribute dictionary. __post_init__ checks rules beyond annotations.",
                "dataclass genera el constructor y la igualdad por campos. frozen impide "
                "la asignación normal de atributos y slots elimina el diccionario usual "
                "de la instancia. __post_init__ valida reglas que la anotación no verifica.",
            ),
            example_code="""from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ticket:
    event: str
    seat: int

    def __post_init__(self) -> None:
        if not self.event.strip() or self.seat < 1:
            raise ValueError("Expected an event name and a positive seat number")


ticket = Ticket("Concert", 12)
assert ticket == Ticket("Concert", 12)
print(ticket)""",
            steps=(
                (
                    "Попробуйте создать билет с нулевым местом и с пустым названием.",
                    "Try creating a ticket with seat zero and with an empty event name.",
                    "Intenta crear un billete con asiento cero y un evento sin nombre.",
                ),
            ),
            level=LessonLevel.BEGINNER,
        ),
        LocalizedPage(
            title=(
                "Фабрика объекта с Self",
                "A factory returning Self",
                "Fábrica que devuelve Self",
            ),
            explanation=(
                "Фабрика разбирает текст и возвращает экземпляр cls. Self по PEP 673 "
                "(Python 3.11+) выражает зависимость результата от класса вызова. "
                "Поэтому унаследованная фабрика сохраняет тип подкласса.",
                "The factory parses text and returns an instance of cls. Self from "
                "PEP 673 (Python 3.11+) ties the result to the calling class. "
                "An inherited factory therefore retains the subclass type.",
                "La fábrica analiza texto y devuelve una instancia de cls. Self de "
                "PEP 673 (Python 3.11+) vincula el resultado a la clase que llama. "
                "La fábrica heredada conserva el tipo de la subclase.",
            ),
            example_code="""from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Parcel:
    label: str
    grams: int

    @classmethod
    def from_label(cls, text: str) -> Self:
        label, separator, raw_grams = text.partition(":")
        if not separator or not label.strip():
            raise ValueError("Expected label:grams")
        grams = int(raw_grams)
        if grams <= 0:
            raise ValueError("Weight must be positive")
        return cls(label.strip(), grams)


class ExpressParcel(Parcel):
    pass


parcel = ExpressParcel.from_label("books:1200")
assert isinstance(parcel, ExpressParcel)
print(parcel.grams)""",
            steps=(
                (
                    "Добавьте проверку метки без двоеточия и метки с отрицательным весом.",
                    "Check a label without a colon and one with a negative weight.",
                    "Comprueba una etiqueta sin dos puntos y otra con peso negativo.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=("Композиция и Protocol", "Composition and Protocol", "Composición y Protocol"),
            explanation=(
                "Protocol по PEP 544 описывает, какие операции нужны клиенту. "
                "Разные классы подходят, если имеют совместимый метод. Передача "
                "избранной стратегии явно позволяет тестировать расчёт без сервисов.",
                "A Protocol (PEP 544) describes the operations a caller needs. Separate "
                "classes can satisfy it with compatible methods. Passing the strategy "
                "explicitly lets you test the calculation without services.",
                "Protocol (PEP 544) describe las operaciones que necesita el consumidor. "
                "Clases distintas cumplen el contrato con un método compatible. Pasar "
                "la estrategia explícitamente permite probar el cálculo sin servicios.",
            ),
            example_code="""from typing import Protocol


class Delivery(Protocol):
    def fee(self, weight_kg: int) -> int: ...


class Pickup:
    def fee(self, weight_kg: int) -> int:
        return 0


class Courier:
    def fee(self, weight_kg: int) -> int:
        return 250 + 40 * weight_kg


def checkout(cents: int, weight_kg: int, delivery: Delivery) -> int:
    return cents + delivery.fee(weight_kg)


assert checkout(1_000, 3, Pickup()) == 1_000
assert checkout(1_000, 3, Courier()) == 1_370""",
            steps=(
                (
                    "Добавьте класс для фиксированного тарифа и передайте его в checkout.",
                    "Add a flat-rate class and pass it to checkout.",
                    "Añade una clase de tarifa plana y pásala a checkout.",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
    LessonTopic.FILES: localize_pages(
        LocalizedPage(
            title=("Текст с pathlib", "Handle text with pathlib", "Trabajar con texto y pathlib"),
            explanation=(
                "Path объединяет части пути через /. Для небольших файлов read_text и "
                "write_text сами открывают и закрывают файл. Укажите кодировку явно. "
                "Временный каталог позволяет повторять пример без побочных файлов.",
                "Path joins components with /. For small files, read_text and write_text "
                "open and close the file themselves. Specify the encoding explicitly. "
                "A temporary directory keeps the example repeatable without leftover files.",
                "Path une segmentos con /. Para archivos pequeños, read_text y write_text "
                "abren y cierran el archivo por sí mismos. Especifica la codificación. "
                "El directorio temporal permite repetir el ejemplo sin dejar archivos.",
            ),
            example_code=r"""from pathlib import Path
from tempfile import TemporaryDirectory


with TemporaryDirectory() as directory:
    notes = Path(directory) / "notes.txt"
    notes.write_text("Coffee\nCafé\nЧай\n", encoding="utf-8")
    for number, line in enumerate(notes.read_text(encoding="utf-8").splitlines(), 1):
        print(f"{number}: {line}")""",
            steps=(
                (
                    "Добавьте строку с эмодзи и убедитесь, что она читается без искажений.",
                    "Add a line with an emoji and verify it reads back correctly.",
                    "Añade una línea con un emoji y comprueba que se lee correctamente.",
                ),
            ),
            level=LessonLevel.BEGINNER,
        ),
        LocalizedPage(
            title=("Потоковое чтение CSV", "Stream a CSV report", "Leer un informe CSV por filas"),
            explanation=(
                "csv.DictReader возвращает строки по одной, поэтому не нужно загружать "
                "весь файл. newline='' оставляет обработку переводов строк модулю csv. "
                "Номер строки в исключении помогает исправить исходный файл.",
                "csv.DictReader yields one row at a time, so you can avoid loading the "
                "whole file. newline='' delegates newline handling to csv. A line number "
                "in the exception helps locate invalid data.",
                "csv.DictReader entrega una fila a la vez y evita cargar el archivo completo. "
                "newline='' delega los saltos de línea a csv. Un número de línea en la "
                "excepción ayuda a localizar los datos inválidos.",
            ),
            example_code=r"""import csv
from pathlib import Path
from tempfile import TemporaryDirectory


def total_sales(path: Path) -> int:
    total = 0
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            try:
                cents = int(row.get("cents") or "")
                if cents < 0:
                    raise ValueError("Negative sale")
            except ValueError as error:
                raise ValueError(f"Invalid sale ending at line {reader.line_num}") from error
            total += cents
    return total


with TemporaryDirectory() as directory:
    report = Path(directory) / "sales.csv"
    report.write_text("item,cents\ncoffee,350\ntea,175\n", encoding="utf-8")
    assert total_sales(report) == 525
    print(total_sales(report))""",
            steps=(
                (
                    "Замените 175 на текст и проверьте номер строки в исключении.",
                    "Replace 175 with text and check the line number in the exception.",
                    "Sustituye 175 por texto y comprueba el número de línea en la excepción.",
                ),
            ),
            level=LessonLevel.INTERMEDIATE,
        ),
        LocalizedPage(
            title=(
                "Атомарная замена JSON",
                "Replace a JSON file atomically",
                "Reemplazar un JSON de forma atómica",
            ),
            explanation=(
                "Запишите JSON во временный файл рядом с целевым, закройте его и "
                "вызовите Path.replace. При атомарной замене читатель увидит целую "
                "старую или новую версию. Эта техника сама по себе не гарантирует "
                "сохранность при отключении питания.",
                "Write JSON to a temporary file next to the destination, close it and "
                "call Path.replace. With atomic replacement, readers see the complete "
                "old or new version. This technique alone does not guarantee durability "
                "if power fails.",
                "Escribe el JSON en un archivo temporal junto al destino, ciérralo y "
                "llama a Path.replace. Un reemplazo atómico permite que los lectores "
                "vean la versión anterior o la nueva completa. Esta técnica por sí sola "
                "no garantiza la persistencia si se pierde la alimentación eléctrica.",
            ),
            example_code="""import json
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory


def save_settings(path: Path, settings: dict[str, str]) -> None:
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        working_file = Path(temporary.name)
    try:
        working_file.write_text(
            json.dumps(settings, ensure_ascii=False),
            encoding="utf-8",
        )
        working_file.replace(path)
    finally:
        working_file.unlink(missing_ok=True)


with TemporaryDirectory() as directory:
    config = Path(directory) / "settings.json"
    save_settings(config, {"theme": "light"})
    save_settings(config, {"theme": "dark"})
    assert json.loads(config.read_text(encoding="utf-8")) == {"theme": "dark"}""",
            steps=(
                (
                    "Откройте файл до и после второй записи и сравните содержимое.",
                    "Read the file before and after the second save and compare the contents.",
                    "Lee el archivo antes y después del segundo guardado y compara los datos.",
                ),
            ),
            level=LessonLevel.PROFESSIONAL,
        ),
    ),
}
