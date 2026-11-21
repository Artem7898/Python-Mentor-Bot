import pytest

from main import markdown_to_html, validate_markdown


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("**жирный**", "<b>жирный</b>"),
        ("*курсив*", "<i>курсив</i>"),
        ("`код`", "<code>код</code>"),
        ("```python\nprint()\n```", '<pre><code class="language-python">print()</code></pre>'),
        ("**жирный и *курсив***", "<b>жирный и <i>курсив</i></b>"),
        (r"\*шаблон\* <i>a & b</i>", "*шаблон* &lt;i&gt;a &amp; b&lt;/i&gt;"),
        ("`<b> **не жирный**`", "<code>&lt;b&gt; **не жирный**</code>"),
        ('```x" onclick="evil\n<>&\n```', "<pre>x&quot; onclick=&quot;evil\n&lt;&gt;&amp;</pre>"),
        ("**неправильно <script>", "**неправильно &lt;script&gt;"),
        ("**жирный** и `незакрытый <b>", "<b>жирный</b> и `незакрытый &lt;b&gt;"),
    ],
)
def test_markdown_to_html(source: str, expected: str) -> None:
    """Render supported formatting and escape plain and code text."""
    assert markdown_to_html(source) == expected


@pytest.mark.parametrize("source", ["**правильно**", "`**a`", "```python\n*\n```", r"\*шаблон"])
def test_validate_markdown_accepts_paired_delimiters(source: str) -> None:
    assert validate_markdown(source) == (True, "")


@pytest.mark.parametrize(
    ("source", "marker"),
    [("**неправильно", "**"), ("*неправильно", "*"), ("`код", "`"), ("```python\nx", "```")],
)
def test_validate_markdown_rejects_unpaired_delimiter(source: str, marker: str) -> None:
    assert validate_markdown(source) == (False, f"Непарные {marker}")
