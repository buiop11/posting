"""Markdown 정리 기능 테스트 (기획서 17.3 완료 기준)."""

from app.services.markdown_cleanup import CleanupOptions, cleanup_markdown


class TestDefaultCleanup:
    def test_h2_removed(self):
        assert cleanup_markdown("## 소제목") == "소제목"

    def test_h3_removed(self):
        assert cleanup_markdown("### 소제목") == "소제목"

    def test_bold_removed(self):
        assert cleanup_markdown("**중요한 내용**") == "중요한 내용"

    def test_bold_underscore_removed(self):
        assert cleanup_markdown("__중요한 내용__") == "중요한 내용"

    def test_escaped_asterisk(self):
        assert cleanup_markdown(r"\*강조\*") == "*강조*"

    def test_trailing_backslash_hard_break(self):
        assert cleanup_markdown("보관하기 편해요.\\\n다음 줄") == "보관하기 편해요.\n다음 줄"

    def test_italic_kept_by_default(self):
        assert cleanup_markdown("*강조*") == "*강조*"

    def test_blockquote_kept_by_default(self):
        assert cleanup_markdown("> 인용문") == "> 인용문"

    def test_link_kept_by_default(self):
        text = "[링크](https://example.com)"
        assert cleanup_markdown(text) == text

    def test_spec_example(self):
        source = (
            "## 냉동 블루베리와 생블루베리 차이\n"
            "\n"
            "**냉동 블루베리**는 보관하기 편해요.\\\n"
            "그렇다면 영양 차이도 있을까요?\n"
            "\n"
            "### 영양 성분 비교\n"
            "\n"
            "**비타민과 항산화 성분**을 비교해볼게요."
        )
        expected = (
            "냉동 블루베리와 생블루베리 차이\n"
            "\n"
            "냉동 블루베리는 보관하기 편해요.\n"
            "그렇다면 영양 차이도 있을까요?\n"
            "\n"
            "영양 성분 비교\n"
            "\n"
            "비타민과 항산화 성분을 비교해볼게요."
        )
        assert cleanup_markdown(source) == expected


class TestProtection:
    def test_url_protected(self):
        text = "주소는 https://example.com/a_b_c**d 입니다"
        assert "https://example.com/a_b_c**d" in cleanup_markdown(text)

    def test_windows_path_protected(self):
        text = r"경로: C:\Users\test\문서\파일.txt 확인"
        assert r"C:\Users\test\문서\파일.txt" in cleanup_markdown(text)

    def test_code_block_protected(self):
        source = "```python\n# 주석\nprint('**굵게 아님**')\n```"
        assert cleanup_markdown(source) == source

    def test_inline_code_protected(self):
        text = "명령어 `pip install **package**` 를 실행"
        assert "`pip install **package**`" in cleanup_markdown(text)

    def test_heading_inside_code_block_kept(self):
        source = "```\n## 제목 아님\n```\n## 진짜 제목"
        assert cleanup_markdown(source) == "```\n## 제목 아님\n```\n진짜 제목"


class TestOptions:
    def test_italic_removed_when_enabled(self):
        opt = CleanupOptions(remove_italic=True)
        assert cleanup_markdown("*강조*", opt) == "강조"

    def test_link_removed_when_enabled(self):
        opt = CleanupOptions(remove_links=True)
        assert cleanup_markdown("[링크](https://example.com)", opt) == "링크"

    def test_blockquote_removed_when_enabled(self):
        opt = CleanupOptions(remove_blockquotes=True)
        assert cleanup_markdown("> 인용문", opt) == "인용문"

    def test_list_removed_when_enabled(self):
        opt = CleanupOptions(remove_lists=True)
        assert cleanup_markdown("- 항목\n1. 번호 항목", opt) == "항목\n번호 항목"

    def test_collapse_blank_lines(self):
        opt = CleanupOptions(collapse_blank_lines=True)
        assert cleanup_markdown("가\n\n\n\n나", opt) == "가\n\n나"

    def test_remove_all(self):
        opt = CleanupOptions(remove_all=True)
        result = cleanup_markdown("## 제목\n> *인용*\n- [링크](http://a.b)", opt)
        assert result == "제목\n인용\n링크"

    def test_heading_disabled(self):
        opt = CleanupOptions(remove_headings=False)
        assert cleanup_markdown("## 제목", opt) == "## 제목"


class TestIdempotency:
    """반복 정리 시 내용이 훼손되지 않아야 한다."""

    def test_double_cleanup_stable(self):
        source = "## 제목\n\n**굵게** 일반 텍스트 *기울임*\n[링크](https://example.com)"
        once = cleanup_markdown(source)
        twice = cleanup_markdown(once)
        assert once == twice

    def test_plain_text_unchanged(self):
        text = "그냥 평범한 문장입니다. 특수문자 없음."
        assert cleanup_markdown(text) == text

    def test_normal_special_chars_kept(self):
        text = "가격은 3,000원 (할인 10%) & 무료배송!"
        assert cleanup_markdown(text) == text
