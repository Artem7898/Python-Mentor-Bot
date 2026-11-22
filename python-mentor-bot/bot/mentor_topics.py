"""Reviewed answers for recognizable questions from the course."""

# ruff: noqa: RUF001
# The answers contain intentional Cyrillic and localized instructional text.

import re
from dataclasses import dataclass
from typing import Final

from bot.i18n import Locale
from bot.lesson_models import LessonTopic, LocalizedText
from bot.lessons import LessonManager
from bot.study_copy import localize

_TRANSLATION: Final = str.maketrans("áéíóúüё’`", "aeiouuе' ")
_ASK = (
    r"(?:(?:что такое|что делает|объясни(?:те)?|зачем (?:нужен|нужна|нужно|нужны)|как работает|"
    r"what (?:is|are)|explain|how (?:does|do)|que es|que son|que hace|explica|"
    r"para que sirve|como funciona)\s+(?:(?:a|an|the|un|una|el|la|las|los)\s+)?)?"
)
_COMPARE = (
    r"(?:(?:в чем разница(?: между)?|разница(?: между)?|чем отлича(?:ется|ются)|"
    r"compare|difference between|what(?: is|'s) the difference between|"
    r"how (?:does|do)|cual es la diferencia entre|diferencia entre|compara)\s+)?"
)
_SEPARATOR = r"\s*(?:vs\.?|versus|и|от|and|from|differ from|different from|y|o|/)\s*"


def _describe(term: str) -> str:
    return rf"{_ASK}(?:{term})"


def _difference(first: str, second: str) -> str:
    article = r"(?:(?:a|an|the|un|una|el|la|las|los)\s+)?"
    item_a, item_b = rf"{article}(?:{first})", rf"{article}(?:{second})"
    return rf"{_COMPARE}(?:{item_a}{_SEPARATOR}{item_b}|{item_b}{_SEPARATOR}{item_a})"


@dataclass(frozen=True, slots=True)
class _Answer:
    pattern: re.Pattern[str]
    lesson: tuple[LessonTopic, int]
    text: LocalizedText


def _answer(pattern: str, topic: LessonTopic, page: int, text: LocalizedText) -> _Answer:
    return _Answer(re.compile(pattern), (topic, page), text)


_ANSWERS: Final = (
    _answer(
        _difference(r"lists?|спис(?:ок|ки|ком|ка)|listas?", r"tuples?|кортеж(?:и|ем|а)?|tuplas?"),
        LessonTopic.BASICS,
        0,
        (
            "Список можно менять после создания: добавлять элементы и заменять их по индексу. "
            "Кортеж хранит фиксированную последовательность ссылок. Если внутри лежит список, "
            "его содержимое всё ещё можно изменить.\n\n"
            "Пример: values = ([1], 2). Вызов values[0].append(3) допустим. "
            "Присваивание values[0] = [] вызовет TypeError. "
            "Для изменяемой коллекции выбирай list, для фиксированной записи — tuple.",
            "A list allows insertion and replacement after construction. A tuple holds a fixed "
            "sequence of references. A referenced mutable object can still change.\n\n"
            "Example: values = ([1], 2). Calling values[0].append(3) works. Assigning "
            "values[0] = [] raises TypeError. Use a list for a changing collection and a "
            "tuple for a fixed record.",
            "Una lista permite insertar y sustituir elementos. Una tupla contiene una "
            "secuencia fija de referencias. Un objeto mutable referenciado puede cambiar.\n\n"
            "Ejemplo: values = ([1], 2). values[0].append(3) funciona. Asignar "
            "values[0] = [] provoca TypeError. Usa list para una colección que cambia y "
            "tuple para un registro fijo.",
        ),
    ),
    _answer(
        _difference("is", "=="),
        LessonTopic.BASICS,
        1,
        (
            "Оператор == сравнивает значения по правилам их типов. is проверяет, "
            "указывают ли обе ссылки на один объект.\n\n"
            "a, b = [1], [1]: a == b истинно, a is b ложно. Используй value is None "
            "для проверки None и == для сравнения строк и чисел. "
            "Совпадение объектов для некоторых строк или малых целых — деталь реализации.",
            "== compares values according to their types. is checks whether the two references "
            "point to the same object.\n\n"
            "For a, b = [1], [1], a == b is true, and a is b is false. Use value is None "
            "for None and == for strings or numbers. Reuse of some string or integer objects "
            "is an implementation detail.",
            "== compara valores según sus tipos. is comprueba si ambas referencias apuntan "
            "al mismo objeto.\n\n"
            "Con a, b = [1], [1], a == b es verdadero y a is b es falso. Usa value is None "
            "para None y == para cadenas o números. La reutilización de ciertos objetos es "
            "un detalle de implementación.",
        ),
    ),
    _answer(
        _describe(
            r"mutable defaults?|mutable default arguments?|изменяемые аргументы по умолчанию|"
            r"argumentos mutables por defecto"
        )
        + r"|why (?:are|avoid) mutable defaults?(?: (?:bad|dangerous))?"
        r"|почему (?:нельзя|опасно) использовать \[\] по умолчанию",
        LessonTopic.BASICS,
        1,
        (
            "Значение аргумента по умолчанию вычисляется при определении функции. "
            "Один и тот же список будет использоваться повторно при вызовах без аргумента.\n\n"
            "def append_value(value, items=None):\n"
            "    if items is None:\n"
            "        items = []\n"
            "    items.append(value)\n"
            "    return items\n\n"
            "Так каждый вызов без списка получает новый объект.",
            "A default argument is evaluated when Python defines the function. Calls that omit "
            "a list default share the same list.\n\n"
            "def append_value(value, items=None):\n"
            "    if items is None:\n"
            "        items = []\n"
            "    items.append(value)\n"
            "    return items\n\n"
            "A fresh list is allocated for every call that omits it.",
            "Python evalúa el valor por defecto al definir la función. Las llamadas que "
            "omiten una lista por defecto comparten esa misma lista.\n\n"
            "def append_value(value, items=None):\n"
            "    if items is None:\n"
            "        items = []\n"
            "    items.append(value)\n"
            "    return items\n\n"
            "Cada llamada sin lista obtiene un objeto nuevo.",
        ),
    ),
    _answer(
        _describe(r"python generators?|generators?(?: in python)?|генератор(?:ы)? python")
        + r"|(?:что такое|как работает) генератор(?:ы)?(?: в python)?"
        r"|(?:que (?:es|son)|como funciona) (?:un |los )?generador(?:es)?(?: en python)?",
        LessonTopic.FILES,
        2,
        (
            "Функция с yield возвращает генератор. При next() она выполняется до следующего "
            "yield и приостанавливается с сохранённым состоянием. Это позволяет обрабатывать "
            "поток по одному элементу.\n\n"
            "squares = (n * n for n in range(3))\n"
            "list(squares)  # [0, 1, 4]\n"
            "list(squares)  # []\n\n"
            "Генератор исчерпывается. Для второго прохода создай новый или сохрани результаты.",
            "A function containing yield returns a generator. Each next() runs up to the "
            "next yield, then suspends with its state intact. You can process a stream "
            "one item at a time.\n\n"
            "squares = (n * n for n in range(3))\n"
            "list(squares)  # [0, 1, 4]\n"
            "list(squares)  # []\n\n"
            "A generator is exhausted after consumption. Recreate it or keep the results.",
            "Una función con yield devuelve un generador. Cada next() avanza hasta el "
            "siguiente yield y suspende la ejecución manteniendo su estado. Así se procesa "
            "un flujo elemento a elemento.\n\n"
            "squares = (n * n for n in range(3))\n"
            "list(squares)  # [0, 1, 4]\n"
            "list(squares)  # []\n\n"
            "El generador se agota tras consumirlo. Créalo de nuevo o conserva los resultados.",
        ),
    ),
    _answer(
        _describe(r"(?:asyncio\.)?taskgroup")
        + "|"
        + _difference(r"(?:asyncio\.)?taskgroup", r"(?:asyncio\.)?gather(?:\(\))?"),
        LessonTopic.ASYNC,
        1,
        (
            "TaskGroup задаёт общий срок жизни задач. При выходе из блока он ждёт "
            "дочерние задачи. Если одна завершилась обычным исключением, "
            "группа отменяет остальные и объединяет ошибки в ExceptionGroup.\n\n"
            "async with asyncio.TaskGroup() as group:\n"
            "    first = group.create_task(fetch_first())\n"
            "    second = group.create_task(fetch_second())\n\n"
            "После выхода доступны first.result() и second.result(). gather удобен "
            "для упорядоченного списка результатов. По умолчанию ошибка одной задачи "
            "в gather не отменяет остальные.",
            "TaskGroup scopes child tasks to a block. It waits for them on exit. "
            "If one raises a regular exception, it cancels the siblings "
            "and groups failures in an ExceptionGroup.\n\n"
            "async with asyncio.TaskGroup() as group:\n"
            "    first = group.create_task(fetch_first())\n"
            "    second = group.create_task(fetch_second())\n\n"
            "Read first.result() and second.result() after the block. gather provides an "
            "ordered results list. By default one failing task does not cancel its peers.",
            "TaskGroup limita la vida de las tareas hijas al bloque y las espera al salir. "
            "Si una lanza una excepción ordinaria, cancela las demás y "
            "agrupa los fallos en ExceptionGroup.\n\n"
            "async with asyncio.TaskGroup() as group:\n"
            "    first = group.create_task(fetch_first())\n"
            "    second = group.create_task(fetch_second())\n\n"
            "Lee first.result() y second.result() después del bloque. gather devuelve "
            "resultados ordenados. Por defecto, un fallo no cancela las demás tareas.",
        ),
    ),
    _answer(
        _describe(
            r"(?:django |problem |проблема |problema )?(?:n\+1|n \+ 1)"
            r"(?: (?:problem|queries|in django|в django|en django))?"
        )
        + r"|(?:как (?:решить|устранить)|how to (?:fix|avoid)|como (?:resolver|evitar)) "
        r"(?:the |проблему |el problema )?(?:n\+1|n \+ 1)(?: (?:in django|в django|en django))?"
        + "|"
        + _difference(r"select_related(?:\(\))?", r"prefetch_related(?:\(\))?"),
        LessonTopic.DJANGO,
        3,
        (
            "N+1 возникает, когда сначала загружается список объектов, а затем цикл "
            "запрашивает связанную запись для каждого объекта.\n\n"
            "Для внешнего ключа: Product.objects.select_related('category') загрузит "
            "товар и категорию через JOIN. Для обратной связи: "
            "Category.objects.prefetch_related('product_set') сделает отдельный "
            "запрос и свяжет результаты в Python. Проверь число запросов через "
            "assertNumQueries или CaptureQueriesContext.",
            "N+1 happens when one query loads a list and a loop fetches a related record "
            "for each row.\n\n"
            "For a foreign key, Product.objects.select_related('category') joins the "
            "product and category. For the reverse relation, "
            "Category.objects.prefetch_related('product_set') fetches the related rows "
            "separately and matches them in Python. Verify query counts with "
            "assertNumQueries or CaptureQueriesContext.",
            "N+1 ocurre cuando una consulta carga una lista y cada vuelta del bucle "
            "consulta su relación.\n\n"
            "Para una clave foránea, Product.objects.select_related('category') une "
            "producto y categoría con JOIN. Para la relación inversa, "
            "Category.objects.prefetch_related('product_set') realiza otra consulta y "
            "agrupa sus resultados en Python. Mide las consultas con assertNumQueries "
            "o CaptureQueriesContext.",
        ),
    ),
    _answer(
        _difference("makemigrations", "migrate") + r"(?: (?:in django|в django|en django))?",
        LessonTopic.DJANGO,
        1,
        (
            "makemigrations сравнивает модели с состоянием миграций и создаёт файлы "
            "изменений. migrate применяет ещё не выполненные миграции к выбранной базе.\n\n"
            "После изменения models.py выполни python manage.py makemigrations, "
            "проверь файл и затем вызови python manage.py migrate. В Git храни и "
            "изменения модели, и соответствующую миграцию.",
            "makemigrations compares models with migration state and writes migration files. "
            "migrate applies pending migrations to the selected database.\n\n"
            "After changing models.py, run python manage.py makemigrations, review the "
            "generated file and then run python manage.py migrate. Commit the model "
            "change and its migration together.",
            "makemigrations compara los modelos con el estado de migraciones y escribe "
            "archivos. migrate aplica las migraciones pendientes en la base elegida.\n\n"
            "Tras cambiar models.py, ejecuta python manage.py makemigrations, revisa "
            "el archivo y ejecuta python manage.py migrate. Registra el cambio del "
            "modelo y su migración juntos.",
        ),
    ),
    _answer(
        _describe(r"(?:ошибк[аи] |http |error )?(?:fastapi 422|422 (?:in |в |en )?fastapi)")
        + r"|(?:почему fastapi возвращает|why does fastapi return|por que fastapi devuelve) "
        r"(?:http |error |ошибку )?422(?: при post| on post| en un post)?",
        LessonTopic.FASTAPI,
        0,
        (
            "FastAPI обычно возвращает 422, когда входные данные не проходят валидацию. "
            "В JSON-ответе проверь detail[].loc, msg и type. loc показывает, где ошибка: "
            "path, query или body.\n\n"
            "Если item_id задан как Annotated[int, Path(gt=0)], то /items/0 нарушит "
            "условие, а /items/1 пройдёт. Для JSON проверь имена и типы полей и "
            "Content-Type: application/json.",
            "FastAPI generally returns 422 when request data fails validation. Inspect "
            "detail[].loc, msg and type in the JSON response. loc indicates the source: "
            "path, query or body.\n\n"
            "If item_id is Annotated[int, Path(gt=0)], /items/0 fails and /items/1 "
            "passes this check. For JSON, verify field names, types and "
            "Content-Type: application/json.",
            "FastAPI suele devolver 422 cuando falla la validación de la solicitud. Revisa "
            "detail[].loc, msg y type en la respuesta JSON. loc indica path, query o body.\n\n"
            "Con item_id: Annotated[int, Path(gt=0)], /items/0 falla y /items/1 supera "
            "esa condición. Para JSON, verifica los nombres, tipos y "
            "Content-Type: application/json.",
        ),
    ),
    _answer(
        _describe(r"(?:drf |django rest framework )?(?:serializers?|сериализатор(?:ы)?)")
        + r"(?: (?:in drf|в drf|en drf))?",
        LessonTopic.DRF,
        0,
        (
            "Сериализатор DRF преобразует объекты в данные ответа и проверяет вход. "
            "Передай request.data в ItemSerializer(data=request.data), затем вызови "
            "serializer.is_valid(raise_exception=True). Проверенные поля доступны в "
            "serializer.validated_data.\n\n"
            "При ошибке валидации DRF формирует HTTP 400. Для сохранения нужен "
            "serializer.save() и реализация create/update либо ModelSerializer.",
            "A DRF serializer represents objects in responses and validates input. "
            "Instantiate ItemSerializer(data=request.data), call "
            "serializer.is_valid(raise_exception=True), then read serializer.validated_data.\n\n"
            "DRF turns a validation failure into HTTP 400. To persist data, call "
            "serializer.save() with create/update methods or a ModelSerializer.",
            "Un serializador DRF representa objetos en respuestas y valida la entrada. "
            "Usa ItemSerializer(data=request.data) y llama a "
            "serializer.is_valid(raise_exception=True). Lee serializer.validated_data.\n\n"
            "DRF devuelve HTTP 400 ante un error de validación. Para guardar datos, "
            "llama a serializer.save() con los métodos create/update o un ModelSerializer.",
        ),
    ),
    _answer(
        _describe(
            r"pydantic(?: v2)? strict(?: mode)?|strict mode(?: in pydantic(?: v2)?)?|"
            r"строгий режим(?: pydantic| в pydantic)?|modo estricto(?: de pydantic| en pydantic)?"
        ),
        LessonTopic.PYDANTIC,
        0,
        (
            "Строгий режим Pydantic ограничивает автоматическое приведение типов. "
            "Например, строка '2' не пройдёт проверку поля int, а число 2 пройдёт.\n\n"
            "Для модели укажи model_config = ConfigDict(strict=True). Для отдельного "
            "поля можно использовать Annotated[int, Field(strict=True)]. Ошибку "
            "проверяй через ValidationError. При чтении JSON у ряда типов есть "
            "дополнительные допустимые представления, например дата в виде строки.",
            "Pydantic strict mode restricts automatic type conversion. The string '2' "
            "fails an int field while the integer 2 passes.\n\n"
            "Set model_config = ConfigDict(strict=True) on the model or use "
            "Annotated[int, Field(strict=True)] on a field. Catch ValidationError "
            "when needed. Some types accept extra JSON representations, such as dates as strings.",
            "El modo estricto de Pydantic limita la conversión automática de tipos. "
            "La cadena '2' falla en un campo int y el entero 2 pasa.\n\n"
            "Usa model_config = ConfigDict(strict=True) para la clase o "
            "Annotated[int, Field(strict=True)] para un campo. Captura ValidationError "
            "si es necesario. En JSON algunos tipos admiten formatos adicionales, como "
            "fechas en cadenas.",
        ),
    ),
    _answer(
        _describe(
            r"pytest (?:fixtures?|фикстуры?)|fixtures?(?: (?:in |en )?pytest)?|"
            r"фикстур[аы](?: (?:в )?pytest)?"
        )
        + "|"
        + _difference(r"fixtures?|фикстур[ауыой]", r"parametrize"),
        LessonTopic.TEST,
        1,
        (
            "Фикстура подготавливает зависимости теста и при необходимости освобождает "
            "ресурс после yield. Pytest передаёт её по имени параметра теста. "
            "parametrize запускает одну проверку с несколькими наборами входов.\n\n"
            "Например, fixture создаёт временную базу, а "
            "@pytest.mark.parametrize('quantity', [0, -1]) проверяет, что оба "
            "некорректных количества отклоняются. Эти приёмы можно сочетать.",
            "A fixture supplies a test dependency and can clean up after yield. Pytest "
            "injects it by matching the test parameter name. parametrize runs the "
            "same check with multiple inputs.\n\n"
            "For example, a fixture creates a temporary database, while "
            "@pytest.mark.parametrize('quantity', [0, -1]) exercises two invalid quantities. "
            "You can use both in the same test.",
            "Una fixture prepara una dependencia y puede liberar recursos después de yield. "
            "Pytest la inyecta por el nombre del parámetro. parametrize repite una "
            "prueba con distintas entradas.\n\n"
            "Por ejemplo, una fixture crea una base temporal y "
            "@pytest.mark.parametrize('quantity', [0, -1]) prueba dos cantidades inválidas. "
            "Ambos mecanismos se pueden combinar.",
        ),
    ),
    _answer(
        _describe(
            r"(?:python )?venv|virtual environments?(?: in python)?|"
            r"виртуальн(?:ое окружение|ые окружения)(?: python)?|entornos? virtual(?:es)?"
        )
        + r"|(?:как создать|how to create|como crear) "
        r"(?:a |un )?(?:venv|virtual environment|виртуальное окружение|entorno virtual)",
        LessonTopic.INSTALL,
        3,
        (
            "venv создаёт окружение для зависимостей конкретного проекта. "
            "Сначала выполни python -m venv .venv. Затем активируй окружение или "
            "вызови его интерпретатор напрямую.\n\n"
            "На Linux/macOS: .venv/bin/python -m pip install -r requirements.txt\n"
            "В PowerShell: ./.venv/Scripts/python.exe -m pip install -r requirements.txt\n\n"
            "Проверь путь интерпретатора с python -c 'import sys; print(sys.executable)' "
            "после активации.",
            "venv creates an isolated set of project dependencies. Run "
            "python -m venv .venv, then activate it or invoke its interpreter directly.\n\n"
            "Linux/macOS: .venv/bin/python -m pip install -r requirements.txt\n"
            "PowerShell: ./.venv/Scripts/python.exe -m pip install -r requirements.txt\n\n"
            "After activation, verify the interpreter path with "
            "python -c 'import sys; print(sys.executable)'.",
            "venv aísla las dependencias de un proyecto. Ejecuta python -m venv .venv "
            "y activa el entorno o llama a su intérprete directamente.\n\n"
            "Linux/macOS: .venv/bin/python -m pip install -r requirements.txt\n"
            "PowerShell: ./.venv/Scripts/python.exe -m pip install -r requirements.txt\n\n"
            "Tras activar, comprueba la ruta con "
            "python -c 'import sys; print(sys.executable)'.",
        ),
    ),
)


def local_answer(question: str, locale: Locale) -> str | None:
    """Answer a recognized question without disclosing it to any outside service."""
    if len(question) > 240 or "\n" in question.strip():
        return None
    normalized = " ".join(question.casefold().translate(_TRANSLATION).split())
    normalized = normalized.strip(" ?!¿¡.")
    for card in _ANSWERS:
        if card.pattern.fullmatch(normalized):
            topic, page = card.lesson
            answer = localize(locale, card.text)
            lesson = LessonManager.get_topic_content(topic, page, locale)
            if lesson is None:
                return answer
            heading = localize(locale, ("Урок по теме", "Related lesson", "Lección relacionada"))
            return f"{answer}\n\n{heading} — {lesson.title}."
    return None
