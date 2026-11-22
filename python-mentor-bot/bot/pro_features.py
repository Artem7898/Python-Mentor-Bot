"""Private Pro feature content and bounded analysis, independent of access checks."""

# ruff: noqa: RUF001
# Russian text intentionally includes Cyrillic letters and Python identifiers.

import ast
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from bot.formatting import escape_html, format_code
from bot.i18n import Locale
from bot.lesson_models import LocalizedText
from bot.pro_interview import (
    INTERVIEW_COUNT,
    MAX_INTERVIEW_ANSWER,
    interview_complete,
    interview_feedback,
    interview_question,
    valid_interview_answer,
)
from bot.pro_review_copy import ADVICE, Category, Rule
from bot.study_copy import localize

__all__ = [
    "INTERVIEW_COUNT",
    "MAX_INTERVIEW_ANSWER",
    "MAX_REVIEW_SOURCE",
    "analyze_code",
    "interview_complete",
    "interview_feedback",
    "interview_question",
    "review_code",
    "review_prompt",
    "valid_interview_answer",
]

MAX_REVIEW_SOURCE: Final = 4096
_MAX_NODES: Final = 1800
_MAX_DEPTH: Final = 64
_MAX_FINDINGS: Final = 6
_FENCES: Final = {"```", "```python", "```py", "```python3"}
_HTTP_METHODS: Final = frozenset({"get", "post", "put", "delete", "patch", "head", "request"})
_CREDENTIAL_NAMES: Final = frozenset(
    {"token", "bot_token", "access_token", "api_key", "password", "secret", "secret_key"}
)
_CATEGORY_TEXT: Final[dict[Category, LocalizedText]] = {
    Category.SECURITY: ("Безопасность", "Security", "Seguridad"),
    Category.CORRECTNESS: ("Корректность", "Correctness", "Corrección"),
    Category.PERFORMANCE: ("Производительность", "Performance", "Rendimiento"),
}
_PRIORITY = {category: position for position, category in enumerate(Category)}


class ReviewStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    TOO_LONG = "too_long"
    TOO_COMPLEX = "too_complex"
    SYNTAX = "syntax"


@dataclass(frozen=True, slots=True)
class Finding:
    line: int
    rule: Rule


@dataclass(frozen=True, slots=True)
class Review:
    status: ReviewStatus
    findings: tuple[Finding, ...] = ()
    syntax_line: int | None = None
    truncated: bool = False


def _snippet(source: str) -> str:
    lines = source.rstrip().splitlines(keepends=True)
    if len(lines) >= 2 and lines[0].strip().casefold() in _FENCES and lines[-1].strip() == "```":
        return "".join(lines[1:-1])
    return source


def _bounded(root: ast.AST) -> bool:
    pending = [(root, 1)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > _MAX_NODES or depth > _MAX_DEPTH:
            return False
        pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return True


def _imports(module: ast.Module) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for statement in module.body:
        if isinstance(statement, ast.Import):
            for item in statement.names:
                package = item.name.split(".", maxsplit=1)[0]
                bindings[item.asname or package] = item.name if item.asname else package
        elif isinstance(statement, ast.ImportFrom) and statement.module and not statement.level:
            for item in statement.names:
                bindings[item.asname or item.name] = f"{statement.module}.{item.name}"
    return bindings


def _keyword(node: ast.Call, name: str) -> ast.expr | None:
    return next((entry.value for entry in node.keywords if entry.arg == name), None)


def _is_dynamic_sql(expression: ast.expr) -> bool:
    match expression:
        case ast.JoinedStr(values=values):
            return any(isinstance(value, ast.FormattedValue) for value in values)
        case ast.BinOp(left=ast.Constant(value=str()), op=ast.Mod()):
            return True
        case ast.BinOp(
            left=ast.Constant(value=str()), op=ast.Add(), right=ast.Constant(value=str())
        ):
            return False
        case ast.BinOp(left=left, op=ast.Add(), right=right):
            return isinstance(left, ast.Constant | ast.JoinedStr) or isinstance(
                right, ast.Constant | ast.JoinedStr
            )
        case ast.Call(func=ast.Attribute(value=ast.Constant(value=str()), attr="format")):
            return True
        case _:
            return False


@dataclass(slots=True)
class _Analyzer(ast.NodeVisitor):
    bindings: dict[str, str]
    findings: set[Finding] = field(default_factory=set)
    in_async: bool = False

    def _name(self, expression: ast.expr) -> str:
        match expression:
            case ast.Name(id=name):
                return self.bindings.get(name, name)
            case ast.Attribute(value=receiver, attr=attribute):
                base = self._name(receiver)
                return f"{base}.{attribute}" if base else ""
            case _:
                return ""

    def _add(self, node: ast.expr | ast.stmt | ast.ExceptHandler, rule: Rule) -> None:
        self.findings.add(Finding(node.lineno, rule))

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, *, async_body: bool) -> None:
        prior = self.in_async
        for value in (*node.args.defaults, *node.args.kw_defaults):
            if isinstance(
                value, ast.List | ast.Dict | ast.Set | ast.ListComp | ast.DictComp | ast.SetComp
            ) or (
                isinstance(value, ast.Call)
                and self._name(value.func) in {"list", "set", "dict", "bytearray"}
            ):
                self._add(value, Rule.MUTABLE_DEFAULT)
            if value is not None:
                self.visit(value)
        self.in_async = async_body
        for statement in node.body:
            self.visit(statement)
        self.in_async = prior

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node, async_body=True)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node, async_body=False)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._name(node.func)
        module, _, member = name.rpartition(".")
        requests_call = module == "requests" and member in _HTTP_METHODS
        http_call = requests_call or module == "httpx"
        if name in {"eval", "exec", "builtins.eval", "builtins.exec"}:
            self._add(node, Rule.DYNAMIC_EXECUTION)
        if module == "subprocess":
            shell = _keyword(node, "shell")
            if isinstance(shell, ast.Constant) and shell.value is True:
                self._add(node, Rule.SHELL)
        if name in {"pickle.load", "pickle.loads"}:
            self._add(node, Rule.DESERIALIZE)
        if name == "yaml.load":
            loader = _keyword(node, "Loader")
            if loader is None and len(node.args) > 1:
                loader = node.args[1]
            if loader is None or self._name(loader) not in {"yaml.SafeLoader", "yaml.CSafeLoader"}:
                self._add(node, Rule.YAML)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"execute", "executemany", "executescript"}
            and node.args
            and _is_dynamic_sql(node.args[0])
        ):
            self._add(node, Rule.SQL)
        verify = _keyword(node, "verify")
        if http_call and isinstance(verify, ast.Constant) and verify.value is False:
            self._add(node, Rule.TLS)
        timeout = _keyword(node, "timeout")
        if (requests_call and timeout is None and all(kw.arg for kw in node.keywords)) or (
            http_call and isinstance(timeout, ast.Constant) and timeout.value is None
        ):
            self._add(node, Rule.HTTP_TIMEOUT)
        if self.in_async and (
            requests_call
            or (module == "httpx" and member in _HTTP_METHODS)
            or name in {"time.sleep", "open", "builtins.open"}
        ):
            self._add(node, Rule.BLOCKING_ASYNC)
        if name in {"all", "any", "sum"} and node.args and isinstance(node.args[0], ast.ListComp):
            self._add(node, Rule.MATERIALIZATION)
        self.generic_visit(node)

    def _credential(self, node: ast.Assign | ast.AnnAssign) -> None:
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            return
        if len(node.value.value.strip()) < 8:
            return
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
        for target in targets:
            name = (
                target.id
                if isinstance(target, ast.Name)
                else (target.attr if isinstance(target, ast.Attribute) else "")
            )
            if name.casefold() in _CREDENTIAL_NAMES:
                self._add(node, Rule.CREDENTIAL)
                break

    def visit_Assign(self, node: ast.Assign) -> None:
        self._credential(node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._credential(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add(node, Rule.BARE_EXCEPT)
        if node.body and all(isinstance(statement, ast.Pass) for statement in node.body):
            self._add(node, Rule.SWALLOWED_ERROR)
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        if (
            isinstance(node.value, ast.Call)
            and self._name(node.value.func) == "asyncio.create_task"
        ):
            self._add(node, Rule.DETACHED_TASK)
        self.generic_visit(node)


def analyze_code(source: str) -> Review:
    """Parse a bounded source excerpt and report heuristic findings without executing it."""
    if len(source) > MAX_REVIEW_SOURCE:
        return Review(ReviewStatus.TOO_LONG)
    source = _snippet(source)
    if not source.strip():
        return Review(ReviewStatus.EMPTY)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Review(ReviewStatus.SYNTAX, syntax_line=exc.lineno)
    except ValueError, RecursionError:
        return Review(ReviewStatus.TOO_COMPLEX)
    if not _bounded(tree):
        return Review(ReviewStatus.TOO_COMPLEX)
    analyzer = _Analyzer(_imports(tree))
    analyzer.visit(tree)
    findings = sorted(
        analyzer.findings,
        key=lambda finding: (_PRIORITY[ADVICE[finding.rule].category], finding.line, finding.rule),
    )
    return Review(
        ReviewStatus.OK,
        tuple(findings[:_MAX_FINDINGS]),
        truncated=len(findings) > _MAX_FINDINGS,
    )


_PROMPT: Final[LocalizedText] = (
    "🧑‍💻 <b>Ревью Python</b>\n\n"
    "Пришли до {limit} символов кода текстом. Бот проверит фрагмент статически. "
    "Удали из примера токены и личные данные. Для отмены используй /cancel.",
    "🧑‍💻 <b>Python code review</b>\n\n"
    "Send up to {limit} characters of code as text for static review. "
    "Remove tokens and personal data. Use /cancel to leave.",
    "🧑‍💻 <b>Revisión de código Python</b>\n\n"
    "Envía hasta {limit} caracteres de código como texto para revisión estática. "
    "Quita tokens y datos personales. Usa /cancel para salir.",
)
_REVIEW_TITLE: Final[LocalizedText] = (
    "🧑‍💻 <b>Ревью Python</b>",
    "🧑‍💻 <b>Python code review</b>",
    "🧑‍💻 <b>Revisión de código Python</b>",
)
_REVIEW_LINE: Final[LocalizedText] = ("Строка {line}", "Line {line}", "Línea {line}")
_REVIEW_SCOPE: Final[LocalizedText] = (
    "Статические подсказки по фрагменту. Проверь контекст и тесты перед исправлением.",
    "Static hints for this excerpt. Check its context and tests before making changes.",
    "Sugerencias estáticas. Comprueba el contexto y las pruebas antes de cambiar el fragmento.",
)
_REVIEW_ERRORS: Final[dict[ReviewStatus, LocalizedText]] = {
    ReviewStatus.EMPTY: ("Пришли фрагмент кода.", "Send a code excerpt.", "Envía un fragmento."),
    ReviewStatus.TOO_LONG: (
        "Сократи фрагмент до {limit} символов.",
        "Shorten the excerpt to {limit} characters.",
        "Reduce el fragmento a {limit} caracteres.",
    ),
    ReviewStatus.TOO_COMPLEX: (
        "Разбей фрагмент на несколько небольших примеров.",
        "Split the excerpt into several smaller examples.",
        "Divide el fragmento en ejemplos más pequeños.",
    ),
    ReviewStatus.SYNTAX: (
        "Фрагмент не разобран как Python. Проверь синтаксис и отступы.",
        "The excerpt could not be parsed as Python. Check syntax and indentation.",
        "No se pudo analizar como Python. Comprueba la sintaxis y la sangría.",
    ),
}
_NO_FINDINGS: Final[LocalizedText] = (
    "В этом фрагменте не обнаружены проверяемые шаблоны.",
    "This excerpt did not match the implemented checks.",
    "El fragmento no coincide con las comprobaciones implementadas.",
)
_TRUNCATED: Final[LocalizedText] = (
    "Показаны первые {limit} замечаний. Для деталей проверь участки по отдельности.",
    "Showing the first {limit} findings. Review individual sections for more detail.",
    "Se muestran los primeros {limit} hallazgos. Revisa cada sección por separado.",
)


def review_prompt(locale: Locale) -> str:
    """Request an excerpt and describe the scope of a code review."""
    return localize(locale, _PROMPT).format(limit=MAX_REVIEW_SOURCE)


def review_code(source: str, locale: Locale) -> str:
    """Render diagnostics and trusted examples, omitting the submitted source."""
    result = analyze_code(source)
    if result.status != ReviewStatus.OK:
        text = localize(locale, _REVIEW_ERRORS[result.status]).format(limit=MAX_REVIEW_SOURCE)
        if result.syntax_line is not None:
            line = localize(locale, _REVIEW_LINE).format(line=result.syntax_line)
            text = f"{line}. {text}"
        return text

    sections = [localize(locale, _REVIEW_TITLE), localize(locale, _REVIEW_SCOPE)]
    if not result.findings:
        sections.append(localize(locale, _NO_FINDINGS))
    for finding in result.findings:
        advice = ADVICE[finding.rule]
        line = localize(locale, _REVIEW_LINE).format(line=finding.line)
        category = localize(locale, _CATEGORY_TEXT[advice.category])
        title = escape_html(localize(locale, advice.title))
        explanation = escape_html(localize(locale, advice.explanation))
        example = f"\n{format_code(advice.example)}" if advice.example else ""
        sections.append(f"<b>{line} · {category} · {title}</b>\n{explanation}{example}")
    if result.truncated:
        sections.append(localize(locale, _TRUNCATED).format(limit=_MAX_FINDINGS))
    return "\n\n".join(sections)
