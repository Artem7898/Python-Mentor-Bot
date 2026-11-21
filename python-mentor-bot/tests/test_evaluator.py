import pytest

from bot.evaluator import MAX_SOURCE_LENGTH, EvaluationError, evaluate_expression


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (" 2 + 3 * 4 ", 14),
        ("(-2 + 5) ** 2", 9),
        ("1 / 4", 0.25),
        ("-7 // 2", -4),
        ("-7 % 2", 1),
        ("+0xF - 0b11", 12),
        ("2 ** -1", 0.5),
        ("9 ** 0.5", 3.0),
        ("1_000 + 2.5", 1002.5),
    ],
)
def test_arithmetic(source: str, expected: int | float) -> None:
    assert evaluate_expression(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "True",
        "3j",
        "'1'",
        "print(1)",
        "x + 1",
        "x = 1",
        "(x := 1)",
        "(1).__class__",
        "[1, 2][0]",
        "[n for n in ()]",
        "2 << 4",
        "1 < 2",
    ],
)
def test_disallowed_syntax(source: str) -> None:
    with pytest.raises(EvaluationError):
        evaluate_expression(source)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (" ", "Введите"),
        ("1 +", "Некорректное"),
        ("1 / 0", "Деление на ноль"),
        ("1 // 0", "Деление на ноль"),
        ("1 % 0", "Деление на ноль"),
        ("0 ** -1", "Деление на ноль"),
        ("2 ** 65", "показателя степени"),
        ("2 ** -65", "показателя степени"),
        ("1e1000", "допустимый диапазон"),
        ("(2 ** 64) ** 4", "допустимый диапазон"),
        ("1e77 ** 64", "допустимый диапазон"),
        ("(-4) ** 0.5", "целые и вещественные"),
        ("-" * 17 + "1", "вложенность"),
        ("+".join(["1"] * 24), "много операций"),
        ("1".rjust(MAX_SOURCE_LENGTH + 1), "символов"),
    ],
)
def test_limits(source: str, message: str) -> None:
    with pytest.raises(EvaluationError, match=message):
        evaluate_expression(source)
