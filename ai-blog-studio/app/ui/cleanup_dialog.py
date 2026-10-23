"""Markdown 정리 옵션 다이얼로그."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

from app.services.markdown_cleanup import CleanupOptions


class CleanupDialog(QDialog):
    def __init__(self, parent=None, has_selection: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Markdown 정리")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        # 정리 규칙
        rules_box = QGroupBox("정리 규칙")
        rules_layout = QVBoxLayout(rules_box)
        self.chk_headings = QCheckBox("제목 기호 제거 (## 소제목 → 소제목)")
        self.chk_bold = QCheckBox("굵게 기호 제거 (**중요** → 중요)")
        self.chk_backslash = QCheckBox("불필요한 백슬래시 제거")
        self.chk_italic = QCheckBox("기울임 기호 제거 (*강조* → 강조)")
        self.chk_links = QCheckBox("링크 문법 제거 ([링크](URL) → 링크)")
        self.chk_quotes = QCheckBox("인용 기호 제거 (> 인용문 → 인용문)")
        self.chk_lists = QCheckBox("목록 기호 제거 (- 항목 → 항목)")
        self.chk_blank = QCheckBox("연속 빈 줄 정리")
        self.chk_all = QCheckBox("모든 서식 제거")

        for chk, checked in (
            (self.chk_headings, True), (self.chk_bold, True), (self.chk_backslash, True),
            (self.chk_italic, False), (self.chk_links, False), (self.chk_quotes, False),
            (self.chk_lists, False), (self.chk_blank, False), (self.chk_all, False),
        ):
            chk.setChecked(checked)
            rules_layout.addWidget(chk)
        layout.addWidget(rules_box)

        # 정리 모드
        mode_box = QGroupBox("정리 모드")
        mode_layout = QVBoxLayout(mode_box)
        self.radio_plain = QRadioButton("모드 A — 일반 텍스트 정리 (기호 제거)")
        self.radio_rich = QRadioButton("모드 B — 서식 변환 (**중요** → 굵은 글씨)")
        self.radio_plain.setChecked(True)
        mode_layout.addWidget(self.radio_plain)
        mode_layout.addWidget(self.radio_rich)
        layout.addWidget(mode_box)

        # 적용 범위
        scope_box = QGroupBox("적용 범위")
        scope_layout = QVBoxLayout(scope_box)
        self.radio_whole = QRadioButton("전체 문서")
        self.radio_selection = QRadioButton("선택 영역")
        self.radio_whole.setChecked(True)
        self.radio_selection.setEnabled(has_selection)
        if has_selection:
            self.radio_selection.setChecked(True)
        scope_layout.addWidget(self.radio_whole)
        scope_layout.addWidget(self.radio_selection)
        layout.addWidget(scope_box)

        note = QLabel("코드 블록 · URL · 파일 경로는 자동으로 보호됩니다.")
        note.setObjectName("statusLabel")
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("정리 실행")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def options(self) -> CleanupOptions:
        return CleanupOptions(
            remove_headings=self.chk_headings.isChecked(),
            remove_bold=self.chk_bold.isChecked(),
            remove_backslashes=self.chk_backslash.isChecked(),
            remove_italic=self.chk_italic.isChecked(),
            remove_links=self.chk_links.isChecked(),
            remove_blockquotes=self.chk_quotes.isChecked(),
            remove_lists=self.chk_lists.isChecked(),
            collapse_blank_lines=self.chk_blank.isChecked(),
            remove_all=self.chk_all.isChecked(),
        )

    def rich_mode(self) -> bool:
        return self.radio_rich.isChecked()

    def selection_only(self) -> bool:
        return self.radio_selection.isChecked()
