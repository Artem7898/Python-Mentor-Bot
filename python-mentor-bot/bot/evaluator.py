"""Interpret bounded arithmetic expressions from the Python grammar."""

import ast
import math
import operator
from collections.abc import Callable
from typing import TypeGuard

type Number = int | float
type BinaryOperation = Callable[[Number, Number], Number | complex]

MAX_SOURCE_LENGTH = 256
MAX_TREE_NODES = 64
MAX_TREE_DEPTH = 16
MAX_INT_BITS = 256
MAX_FLOAT_MAGNITUDE = 2.0**MAX_INT_BITS
MAX_EXPONENT = 64

_BINARY_OPERATIONS: dict[type[ast.operator], BinaryOperation] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


class EvaluationError(ValueError):
    """An expression cannot be evaluated within the supported rules."""


def _is_number(value: object) -> TypeGuard[Number]:
    return type(value) in (int, float)


def _checked_number(value: object) -> Number:
    if not _is_number(value):
        raise EvaluationError("Поддерживаются только целые и вещественные числа.")
    if isinstance(value, int):
        too_large = value.bit_length() > MAX_INT_BITS
    else:
        too_large = not math.isfinite(value) or abs(value) >= MAX_FLOAT_MAGNITUDE
    if too_large:
        raise EvaluationError("Число выходит за допустимый диапазон.")
    return value


def _evaluate(node: ast.expr, depth: int = 0) -> Number:
    if depth > MAX_TREE_DEPTH:
        raise EvaluationError("Слишком глубокая вложенность выражения.")

    match node:
        case ast.Constant(value=value):
            return _checked_number(value)
        case ast.UnaryOp(op=ast.UAdd(), operand=operand):
            return _evaluate(operand, depth + 1)
        case ast.UnaryOp(op=ast.USub(), operand=operand):
            return -_evaluate(operand, depth + 1)
        case ast.BinOp(left=left, op=op, right=right):
            operation = _BINARY_OPERATIONS.get(type(op))
            if operation is None:
                raise EvaluationError("Этот оператор не поддерживается.")
            first = _evaluate(left, depth + 1)
            second = _evaluate(right, depth + 1)
            if isinstance(op, ast.Pow) and abs(second) > MAX_EXPONENT:
                raise EvaluationError(f"Модуль показателя степени должен быть ≤ {MAX_EXPONENT}.")
            return _checked_number(operation(first, second))
        case _:
            raise EvaluationError("Разрешены только числа и арифметические операции.")


def evaluate_expression(source: str) -> Number:
    """Calculate a numeric Python expression with bounded time and memory.

    Args:
        source: A single expression containing numbers and arithmetic operators.

    Returns:
        The finite result of interpreting the expression.

    Raises:
        EvaluationError: The expression is invalid or exceeds a supported limit.
    """
    if len(source) > MAX_SOURCE_LENGTH:
        raise EvaluationError(f"Выражение должно содержать не более {MAX_SOURCE_LENGTH} символов.")
    source = source.strip()
    if not source:
        raise EvaluationError("Введите арифметическое выражение.")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError:
        raise EvaluationError("Некорректное арифметическое выражение.") from None
    if sum(1 for _ in ast.walk(tree)) > MAX_TREE_NODES:
        raise EvaluationError("Слишком много операций в выражении.")
    try:
        return _evaluate(tree.body)
    except ZeroDivisionError:
        raise EvaluationError("Деление на ноль.") from None
    except ArithmeticError:
        raise EvaluationError("Результат выходит за допустимый диапазон.") from None
