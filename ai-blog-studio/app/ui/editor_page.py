"""직접 편집 페이지 — 공통 에디터 + 정리/복구/내보내기 도구."""

from __future__ import annotations

import webbrowser

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.platforms import naver, tistory
from app.services.export_service import combined_text, export_html
from app.ui.cleanup_dialog import CleanupDialog
from app.ui.editor_widget import EditorWidget


class PreviewDialog(QDialog):
    def __init__(self, title: str, body: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("미리보기")
        self.resize(720, 640)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(export_html(title, body))
        layout.addWidget(browser)


class EditorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        page_title = QLabel("직접 편집")
        page_title.setObjectName("pageTitle")
        layout.addWidget(page_title)

        # 상단 도구 버튼
        toolbar = QHBoxLayout()
        paste_btn = QPushButton("붙여넣기")
        paste_btn.setToolTip("클립보드의 글을 붙여넣습니다 (Ctrl+V)")
        paste_btn.clicked.connect(self._paste)

        cleanup_btn = QPushButton("Markdown 정리")
        cleanup_btn.setToolTip("불필요한 Markdown 기호를 제거합니다")
        cleanup_btn.clicked.connect(self._cleanup)

        restore_btn = QPushButton("원본 복구")
        restore_btn.setToolTip("정리/수정 전 원본으로 되돌립니다")
        restore_btn.clicked.connect(self._restore)

        for btn in (paste_btn, cleanup_btn, restore_btn):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 공통 에디터
        self.editor = EditorWidget()
        layout.addWidget(self.editor, stretch=1)

        # 하단 버튼
        bottom = QHBoxLayout()
        preview_btn = QPushButton("미리보기")
        preview_btn.clicked.connect(self._preview)
        bottom.addWidget(preview_btn)

        open_naver_btn = QPushButton("네이버 글쓰기 열기")
        open_naver_btn.clicked.connect(lambda: webbrowser.open(naver.WRITE_URL))
        bottom.addWidget(open_naver_btn)

        open_tistory_btn = QPushButton("티스토리 글쓰기 열기")
        open_tistory_btn.clicked.connect(lambda: webbrowser.open(tistory.WRITE_URL))
        bottom.addWidget(open_tistory_btn)

        bottom.addStretch()

        copy_btn = QPushButton("블로그용 복사 ▾")
        copy_btn.setObjectName("primaryButton")
        copy_menu = QMenu(copy_btn)
        copy_menu.addAction("제목 복사", self._copy_title)
        copy_menu.addAction("본문 복사", self._copy_body)
        copy_menu.addAction("전체 복사 (제목+본문)", self._copy_all)
        copy_btn.setMenu(copy_menu)
        bottom.addWidget(copy_btn)

        layout.addLayout(bottom)

    # ---------- 동작 ----------

    def _paste(self) -> None:
        self.editor.paste_from_clipboard()

    def _cleanup(self) -> None:
        dialog = CleanupDialog(self, has_selection=self.editor.has_selection())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.editor.apply_cleanup(
                dialog.options(),
                selection_only=dialog.selection_only(),
                rich_mode=dialog.rich_mode(),
            )

    def _restore(self) -> None:
        if not self.editor.restore_original():
            QMessageBox.information(self, "원본 복구", "복구할 원본이 없습니다.")

    def _preview(self) -> None:
        PreviewDialog(self.editor.title(), self.editor.body_plain(), self).exec()

    # ---------- 복사 ----------

    def _copy(self, text: str, what: str) -> None:
        if not text.strip():
            QMessageBox.information(self, "복사", f"{what}이(가) 비어 있습니다.")
            return
        QGuiApplication.clipboard().setText(text)
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(f"{what} 복사 완료 — 블로그 에디터에 붙여넣으세요.", 4000)

    def _copy_title(self) -> None:
        self._copy(self.editor.title(), "제목")

    def _copy_body(self) -> None:
        self._copy(self.editor.body_plain(), "본문")

    def _copy_all(self) -> None:
        self._copy(combined_text(self.editor.title(), self.editor.body_plain()), "전체 내용")
