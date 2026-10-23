"""프로그램 설정 관리 (JSON, %APPDATA%/AIBlogStudio/settings.json)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_NAME = "AIBlogStudio"

DEFAULT_SETTINGS = {
    "theme": "light",
    "default_platform": "naver",
    "default_prompt": "nblog1",
    "font_size": 14,
    "default_export_format": "md",
    "openai_model": "gpt-4o-mini",
    "request_timeout": 120,
}


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def resource_path(relative: str) -> Path:
    """PyInstaller 번들 내부/개발 환경 양쪽에서 리소스 경로를 해석한다."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    # app/utils/settings.py -> 프로젝트 루트
    return Path(__file__).resolve().parent.parent.parent / relative


class Settings:
    def __init__(self) -> None:
        self._data: dict = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        path = settings_path()
        if path.exists():
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass  # 손상된 설정은 기본값으로 대체

    def save(self) -> None:
        settings_path().write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default=None):
        return self._data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()
