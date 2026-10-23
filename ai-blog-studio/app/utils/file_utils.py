"""문서 파일 저장 / 불러오기 (MD · TXT · HTML)."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".txt", ".html"}

FILE_DIALOG_FILTER = (
    "Markdown (*.md);;텍스트 (*.txt);;HTML (*.html);;모든 파일 (*.*)"
)


def read_document(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_document(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")
