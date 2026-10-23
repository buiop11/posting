"""파일 저장/불러오기 및 설정 테스트."""

import json

from app.utils.file_utils import read_document, write_document
from app.utils import settings as settings_module
from app.utils.settings import DEFAULT_SETTINGS, Settings


class TestFileIO:
    def test_write_and_read_md(self, tmp_path):
        path = tmp_path / "문서.md"
        content = "# 제목\n\n한글 본문입니다."
        write_document(path, content)
        assert read_document(path) == content

    def test_write_and_read_txt(self, tmp_path):
        path = tmp_path / "doc.txt"
        write_document(path, "일반 텍스트")
        assert read_document(path) == "일반 텍스트"

    def test_utf8_encoding(self, tmp_path):
        path = tmp_path / "doc.md"
        content = "한글 😀 émoji ★"
        write_document(path, content)
        assert path.read_text(encoding="utf-8") == content


class TestSettings:
    def test_defaults_and_persistence(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "app_data_dir", lambda: tmp_path)
        monkeypatch.setattr(
            settings_module, "settings_path", lambda: tmp_path / "settings.json"
        )

        settings = Settings()
        assert settings.get("theme") == DEFAULT_SETTINGS["theme"]

        settings.set("theme", "dark")
        stored = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        assert stored["theme"] == "dark"

        reloaded = Settings()
        assert reloaded.get("theme") == "dark"

    def test_corrupted_settings_fall_back(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "app_data_dir", lambda: tmp_path)
        monkeypatch.setattr(
            settings_module, "settings_path", lambda: tmp_path / "settings.json"
        )
        (tmp_path / "settings.json").write_text("{잘못된 JSON", encoding="utf-8")

        settings = Settings()
        assert settings.get("theme") == DEFAULT_SETTINGS["theme"]

    def test_api_key_never_in_settings_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "app_data_dir", lambda: tmp_path)
        monkeypatch.setattr(
            settings_module, "settings_path", lambda: tmp_path / "settings.json"
        )
        settings = Settings()
        settings.save()
        raw = (tmp_path / "settings.json").read_text(encoding="utf-8")
        assert "api_key" not in raw
        assert "sk-" not in raw
