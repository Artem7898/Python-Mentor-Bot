"""Render the bot's supported formatting as safe Telegram HTML."""

import html
import re

_MARKER = re.compile(r"\\[\\*`]|```|`|\*+")
_LANGUAGE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_+.-]{0,31}")
_EMPHASIS_TAGS = {1: ("<i>", "</i>"), 2: ("<b>", "</b>")}


def escape_html(text: str) -> str:
    """Escape plain text before inserting it into Telegram HTML."""
    return html.escape(text)


def format_code(code: str, language: str | None = "python") -> str:
    """Render a fenced code example without interpreting any of its contents."""
    escaped = escape_html(code)
    if language and _LANGUAGE.fullmatch(language):
        return f'<pre><code class="language-{language}">{escaped}</code></pre>'
    return f"<pre>{escaped}</pre>"


def format_explanation(text: str) -> str:
    """Escape and italicize a plain-text lesson explanation."""
    return f"<i>{escape_html(text)}</i>"


def _format_fence(payload: str) -> str:
    header, line_break, code = payload.partition("\n")
    language = header.removesuffix("\r")
    if line_break and (not language or _LANGUAGE.fullmatch(language)):
        return format_code(code.removesuffix("\n").removesuffix("\r"), language)
    return format_code(payload.removesuffix("\n").removesuffix("\r"), None)


def _apply_emphasis(
    width: int,
    parts: list[str],
    openings: list[tuple[int, int]],
) -> None:
    while width:
        if openings and (width == openings[-1][0] or width == 3):
            closing_width, index = openings.pop()
            parts[index], closing_tag = _EMPHASIS_TAGS[closing_width]
            parts.append(closing_tag)
            width -= closing_width
        else:
            opening_width = min(width, 2)
            openings.append((opening_width, len(parts)))
            parts.append("*" * opening_width)
            width -= opening_width


def _render_markdown(text: str) -> tuple[str, list[str]]:
    parts: list[str] = []
    openings: list[tuple[int, int]] = []
    unmatched: list[str] = []
    cursor = 0

    while match := _MARKER.search(text, cursor):
        parts.append(escape_html(text[cursor : match.start()]))
        marker = match[0]
        cursor = match.end()

        if marker.startswith("\\"):
            parts.append(escape_html(marker[1:]))
        elif marker.startswith("*"):
            if len(marker) <= 3:
                _apply_emphasis(len(marker), parts, openings)
            else:
                parts.append(marker)
        else:
            end = text.find(marker, cursor)
            if end == -1:
                unmatched.append(marker)
                cursor = match.start()
                break

            content = text[cursor:end]
            cursor = end + len(marker)
            if not content.strip():
                parts.append(escape_html(text[match.start() : cursor]))
            elif marker == "```":
                parts.append(_format_fence(content))
            else:
                parts.append(f"<code>{escape_html(content)}</code>")

    parts.append(escape_html(text[cursor:]))
    unmatched.extend("*" * width for width, _ in openings)
    return "".join(parts), unmatched


def markdown_to_html(text: str) -> str:
    """Render emphasis, inline code and fenced code with optional language tags."""
    rendered, _ = _render_markdown(text)
    return rendered


def validate_markdown(text: str) -> tuple[bool, str]:
    """Return whether all supported delimiters are paired, plus an error message."""
    _, unmatched = _render_markdown(text)
    if unmatched:
        return False, ", ".join(f"Непарные {marker}" for marker in dict.fromkeys(unmatched))
    return True, ""
