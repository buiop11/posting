"""내보내기: HTML 변환, 블로그용 복사 텍스트 구성."""

from __future__ import annotations

from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"breaks": True})

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<meta charset="utf-8">
<title>{title}</title>
<body>
<h1>{title}</h1>
{body}
</body>
</html>
"""


def markdown_to_html(markdown_text: str) -> str:
    """Markdown 본문을 HTML 조각으로 변환한다."""
    return _md.render(markdown_text)


def export_html(title: str, body_markdown: str) -> str:
    """제목 + 본문을 완전한 HTML 문서로 만든다."""
    return _HTML_TEMPLATE.format(
        title=_escape(title) or "제목 없음",
        body=markdown_to_html(body_markdown),
    )


def combined_text(title: str, body: str) -> str:
    """전체 복사용: 제목 + 빈 줄 + 본문."""
    title = title.strip()
    return f"{title}\n\n{body}" if title else body


def char_counts(body: str) -> tuple[int, int]:
    """(공백 포함, 공백 제외) 글자 수."""
    with_spaces = len(body)
    without_spaces = len("".join(body.split()))
    return with_spaces, without_spaces


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
