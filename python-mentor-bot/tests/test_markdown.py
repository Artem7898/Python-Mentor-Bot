# tests/test_markdown.py
import pytest
from main import markdown_to_html, validate_markdown


def test_markdown_to_html():
    """Тест конвертации Markdown в HTML."""
    test_cases = [
        ("**жирный**", "<b>жирный</b>"),
        ("*курсив*", "<i>курсив</i>"),
        ("`код`", "<code>код</code>"),
        ("```python\nprint()\n```", '<pre><code class="language-python">print()</code></pre>'),
    ]

    for input_text, expected in test_cases:
        result = markdown_to_html(input_text)
        assert result == expected, f"Failed for: {input_text}"


def test_validate_markdown():
    """Тест валидации Markdown."""
    assert validate_markdown("**правильно**")[0] == True
    assert validate_markdown("**неправильно")[0] == False
    assert "Непарные **" in validate_markdown("**неправильно")[1]