"""공통 에디터 위젯.

AI 생성 모드와 직접 편집 모드가 동일하게 사용하는 제목/본문 에디터.
- 붙여넣기 (Ctrl+V), 붙여넣기 후 Markdown 정리 (Ctrl+Shift+V)
- 원본 보관 / 복구
- 실시간 글자 수 (공백 포함 / 제외)
- 굵게 / 기울임 / 밑줄 서식
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QTextCharFormat, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.export_service import char_counts, markdown_to_html
from app.services.markdown_cleanup import CleanupOptions, cleanup_markdown


class BodyTextEdit(QTextEdit):
    """Ctrl+Shift+V = 붙여넣기 후 Markdown 정리."""

    paste_clean_requested = Signal()

    def keyPressEvent(self, event):  # noqa: N802
        if (
            event.key() == Qt.Key.Key_V
            and event.modifiers()
            == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        ):
            self.paste_clean_requested.emit()
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):  # noqa: N802
        # 외부 서식이 문서를 흐트러뜨리지 않도록 일반 텍스트로 붙여넣는다
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)


class EditorWidget(QWidget):
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original: tuple[str, str] | None = None  # (제목, 본문) 원본

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_label = QLabel("제목")
        title_label.setObjectName("fieldLabel")
        layout.addWidget(title_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("제목 입력")
        layout.addWidget(self.title_edit)

        body_row = QHBoxLayout()
        body_label = QLabel("본문")
        body_label.setObjectName("fieldLabel")
        body_row.addWidget(body_label)
        body_row.addStretch()

        for text, slot, shortcut in (
            ("굵게", self._toggle_bold, "Ctrl+B"),
            ("기울임", self._toggle_italic, "Ctrl+I"),
            ("밑줄", self._toggle_underline, "Ctrl+U"),
        ):
            button = QPushButton(text)
            button.setShortcut(QKeySequence(shortcut))
            button.clicked.connect(slot)
            body_row.addWidget(button)
        layout.addLayout(body_row)

        self.body_edit = BodyTextEdit()
        self.body_edit.setPlaceholderText("자유롭게 글을 편집하세요")
        self.body_edit.setAcceptRichText(True)
        self.body_edit.paste_clean_requested.connect(self.paste_and_clean)
        layout.addWidget(self.body_edit, stretch=1)

        self.count_label = QLabel("글자 수: 0자 (공백 제외 0자)")
        self.count_label.setObjectName("statusLabel")
        layout.addWidget(self.count_label)

        self.title_edit.textChanged.connect(self._on_changed)
        self.body_edit.textChanged.connect(self._on_changed)

    # ---------- 내용 접근 ----------

    def title(self) -> str:
        return self.title_edit.text()

    def body_plain(self) -> str:
        return self.body_edit.toPlainText()

    def set_document(self, title: str, body: str, keep_as_original: bool = True) -> None:
        self.title_edit.setText(title)
        self.body_edit.setPlainText(body)
        if keep_as_original:
            self._original = (title, body)

    def clear_document(self) -> None:
        self.set_document("", "", keep_as_original=False)
        self._original = None

    # ---------- 원본 보관 / 복구 ----------

    def snapshot_original(self) -> None:
        self._original = (self.title(), self.body_plain())

    def has_original(self) -> bool:
        return self._original is not None

    def restore_original(self) -> bool:
        if self._original is None:
            return False
        title, body = self._original
        self.title_edit.setText(title)
        self.body_edit.setPlainText(body)
        return True

    # ---------- 붙여넣기 ----------

    def paste_from_clipboard(self) -> None:
        text = QGuiApplication.clipboard().text()
        if not text:
            return
        if not self.body_plain().strip():
            # 빈 문서에 붙여넣으면 원본으로 보관
            self.body_edit.setPlainText(text)
            self.snapshot_original()
        else:
            self.body_edit.insertPlainText(text)

    def paste_and_clean(self, options: CleanupOptions | None = None) -> None:
        self.paste_from_clipboard()
        self.apply_cleanup(options or CleanupOptions())

    # ---------- Markdown 정리 ----------

    def apply_cleanup(
        self,
        options: CleanupOptions,
        selection_only: bool = False,
        rich_mode: bool = False,
    ) -> None:
        """모드 A: 일반 텍스트 정리 / 모드 B(rich_mode): 서식 변환."""
        if self._original is None:
            self.snapshot_original()

        cursor = self.body_edit.textCursor()
        if selection_only and cursor.hasSelection():
            cleaned = cleanup_markdown(cursor.selectedText().replace("\u2029", "\n"), options)
            cursor.insertText(cleaned)
            return

        source = self.body_plain()
        if rich_mode:
            self.body_edit.setHtml(markdown_to_html(source))
        else:
            self.body_edit.setPlainText(cleanup_markdown(source, options))

    def has_selection(self) -> bool:
        return self.body_edit.textCursor().hasSelection()

    # ---------- 서식 ----------

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.body_edit.textCursor()
        cursor.mergeCharFormat(fmt)
        self.body_edit.mergeCurrentCharFormat(fmt)

    def _toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        is_bold = self.body_edit.fontWeight() > QFont.Weight.Normal
        fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        self._merge_format(fmt)

    def _toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.body_edit.fontItalic())
        self._merge_format(fmt)

    def _toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.body_edit.fontUnderline())
        self._merge_format(fmt)

    # ---------- 글자 수 ----------

    def _on_changed(self) -> None:
        with_spaces, without_spaces = char_counts(self.body_plain())
        self.count_label.setText(
            f"글자 수: {with_spaces:,}자 (공백 제외 {without_spaces:,}자)"
        )
        self.content_changed.emit()
