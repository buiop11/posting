"""내보내기 및 프롬프트 처리 테스트."""

from app.services.export_service import (
    char_counts,
    combined_text,
    export_html,
    markdown_to_html,
)
from app.services.prompt_service import split_title_body


class TestExport:
    def test_markdown_to_html(self):
        html = markdown_to_html("**굵게** 그리고 일반")
        assert "<strong>굵게</strong>" in html

    def test_export_html_document(self):
        html = export_html("제목입니다", "본문 내용")
        assert "<!DOCTYPE html>" in html
        assert "<h1>제목입니다</h1>" in html
        assert "본문 내용" in html

    def test_export_html_escapes_title(self):
        html = export_html("<script>주의</script>", "본문")
        assert "<script>" not in html.split("<body>")[0].replace(
            "&lt;script&gt;", ""
        )
        assert "&lt;script&gt;" in html

    def test_combined_text(self):
        assert combined_text("제목", "본문") == "제목\n\n본문"
        assert combined_text("", "본문") == "본문"
        assert combined_text("  ", "본문") == "본문"


class TestCharCounts:
    def test_with_and_without_spaces(self):
        with_spaces, without_spaces = char_counts("가나 다라\n마")
        assert with_spaces == 7  # 공백·줄바꿈 포함
        assert without_spaces == 5

    def test_empty(self):
        assert char_counts("") == (0, 0)


class TestSplitTitleBody:
    def test_title_marker(self):
        title, body = split_title_body("제목: 블루베리 이야기\n\n본문 시작")
        assert title == "블루베리 이야기"
        assert body == "본문 시작"

    def test_heading_marker(self):
        title, body = split_title_body("# 제목입니다\n본문")
        assert title == "제목입니다"
        assert body == "본문"

    def test_no_marker(self):
        title, body = split_title_body("그냥 본문만 있는 글")
        assert title == ""
        assert body == "그냥 본문만 있는 글"
