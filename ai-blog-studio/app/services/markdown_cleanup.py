"""Markdown 정리 기능.

ChatGPT에서 복사한 글의 불필요한 Markdown 기호를 제거한다.
코드 블록 / URL / Windows 파일 경로 / 인라인 코드는 보호한다.
단순 문자 삭제가 아니라 문맥(보호 영역)을 고려해 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class CleanupOptions:
    """정리 옵션. 기본값은 기획서 7.3의 기본 활성화 항목과 동일."""

    remove_headings: bool = True        # ## 소제목 -> 소제목
    remove_bold: bool = True            # **중요** / __중요__ -> 중요
    remove_backslashes: bool = True     # \* -> *, 줄 끝 하드브레이크 \ 제거
    remove_italic: bool = False         # *강조* / _강조_ -> 강조
    remove_links: bool = False          # [링크](URL) -> 링크
    remove_blockquotes: bool = False    # > 인용문 -> 인용문
    remove_lists: bool = False          # - 항목 / 1. 항목 -> 항목
    collapse_blank_lines: bool = False  # 연속 빈 줄 -> 한 줄
    remove_all: bool = False            # 모든 서식 제거

    def effective(self) -> "CleanupOptions":
        if not self.remove_all:
            return self
        return CleanupOptions(
            remove_headings=True, remove_bold=True, remove_backslashes=True,
            remove_italic=True, remove_links=True, remove_blockquotes=True,
            remove_lists=True, collapse_blank_lines=True,
        )


# 보호 대상 패턴 (치환 전 플레이스홀더로 대피)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_URL_RE = re.compile(r"(?:https?|ftp)://[^\s<>\"')\]]+")
_WIN_PATH_RE = re.compile(r"[A-Za-z]:\\(?:[^\\\s/:*?\"<>|]+\\?)*[^\\\s/:*?\"<>|]*")
_FENCE_RE = re.compile(r"^(```|~~~)")

_PLACEHOLDER = "\x00PROTECT{}\x00"

# Markdown 이스케이프 가능 문자 (CommonMark ASCII punctuation)
_ESCAPABLE = r"\\`*_{}\[\]()#+\-.!<>|~\"'$%&,/:;=?@^"


def _protect(text: str) -> tuple[str, list[str]]:
    """인라인 코드, URL, Windows 경로를 플레이스홀더로 치환."""
    saved: list[str] = []

    def stash(match: re.Match) -> str:
        saved.append(match.group(0))
        return _PLACEHOLDER.format(len(saved) - 1)

    for pattern in (_INLINE_CODE_RE, _URL_RE, _WIN_PATH_RE):
        text = pattern.sub(stash, text)
    return text, saved


def _restore(text: str, saved: list[str]) -> str:
    for i, original in enumerate(saved):
        text = text.replace(_PLACEHOLDER.format(i), original)
    return text


def _clean_line(line: str, opt: CleanupOptions) -> str:
    if opt.remove_headings:
        line = re.sub(r"^(\s*)#{1,6}\s+", r"\1", line)

    if opt.remove_blockquotes:
        line = re.sub(r"^(\s*)(?:>\s?)+", r"\1", line)

    if opt.remove_lists:
        line = re.sub(r"^(\s*)[-*+]\s+", r"\1", line)
        line = re.sub(r"^(\s*)\d+[.)]\s+", r"\1", line)

    if opt.remove_links:
        # 이미지 ![alt](url) 와 링크 [text](url) 모두 텍스트만 남긴다
        line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)

    if opt.remove_bold:
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"__([^_]+)__", r"\1", line)

    if opt.remove_italic:
        line = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", line)
        line = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", line)

    if opt.remove_backslashes:
        # 줄 끝 하드브레이크용 백슬래시 제거
        line = re.sub(r"\\\s*$", "", line)
        # 이스케이프 문자 복원: \* -> *, \# -> # 등
        line = re.sub(rf"\\([{_ESCAPABLE}])", r"\1", line)

    return line


def cleanup_markdown(text: str, options: CleanupOptions | None = None) -> str:
    """Markdown 기호를 정리한 텍스트를 반환한다.

    코드 블록(``` / ~~~) 내부는 수정하지 않으며,
    URL · Windows 경로 · 인라인 코드는 보호된다.
    """
    opt = (options or CleanupOptions()).effective()
    lines = text.split("\n")
    result: list[str] = []
    in_fence = False
    fence_marker = ""

    for line in lines:
        fence = _FENCE_RE.match(line.strip())
        if fence:
            if not in_fence:
                in_fence = True
                fence_marker = fence.group(1)
            elif line.strip().startswith(fence_marker):
                in_fence = False
            result.append(line)
            continue

        if in_fence:
            result.append(line)
            continue

        protected, saved = _protect(line)
        cleaned = _clean_line(protected, opt)
        result.append(_restore(cleaned, saved))

    output = "\n".join(result)

    if opt.collapse_blank_lines:
        output = re.sub(r"\n{3,}", "\n\n", output)

    return output
