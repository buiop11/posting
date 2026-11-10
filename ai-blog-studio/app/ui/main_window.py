"""메인 윈도우 — 사이드바 + 페이지 전환 + 파일 메뉴."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.export_service import export_html
from app.ui.editor_page import EditorPage
from app.ui.generator_page import GeneratorPage
from app.ui.media_page import MediaPage
from app.ui.prompt_page import PromptPage
from app.ui.settings_page import SettingsPage
from app.ui.theme import stylesheet
from app.utils.file_utils import FILE_DIALOG_FILTER, read_document, write_document
from app.utils.settings import Settings

APP_TITLE = "AI Blog Studio"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self._current_file: Path | None = None
        self._dirty = False

        self.setWindowTitle(APP_TITLE)
        self.resize(1100, 760)

        # ----- 페이지 -----
        self.generator_page = GeneratorPage(self.settings)
        self.editor_page = EditorPage()
        self.media_page = MediaPage()
        self.prompt_page = PromptPage()
        self.settings_page = SettingsPage(self.settings)

        self.generator_page.post_generated.connect(self._on_post_generated)
        self.editor_page.editor.content_changed.connect(self._mark_dirty)
        self.prompt_page.prompts_changed.connect(self.generator_page.refresh_prompts)
        self.settings_page.theme_changed.connect(self.apply_theme)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.generator_page)   # 0
        self.stack.addWidget(self.editor_page)      # 1
        self.stack.addWidget(self.media_page)       # 2
        self.stack.addWidget(self.prompt_page)      # 3
        self.stack.addWidget(self.settings_page)    # 4

        # ----- 사이드바 -----
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 16)
        side_layout.setSpacing(4)

        app_title = QLabel("✦ AI Blog Studio")
        app_title.setObjectName("appTitle")
        side_layout.addWidget(app_title)

        self._nav_buttons: list[QPushButton] = []
        for index, (icon, text) in enumerate(
            (
                ("✦", "AI 글 작성"),
                ("✎", "직접 편집"),
                ("▶", "미디어 도구"),
                ("≡", "프롬프트"),
                ("⚙", "설정"),
            )
        ):
            button = QPushButton(f"{icon}  {text}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, i=index: self._switch_page(i))
            side_layout.addWidget(button)
            self._nav_buttons.append(button)
        side_layout.addStretch()

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(sidebar)
        root.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central)

        self._build_menu()
        self.statusBar().showMessage("준비 완료 — API 키 없이도 직접 편집을 사용할 수 있습니다.", 6000)
        self._switch_page(0)
        self.apply_theme()

    # ---------- 메뉴 / 단축키 ----------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("파일(&F)")

        def add_action(text: str, shortcut: str, slot) -> None:
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(slot)
            file_menu.addAction(action)

        add_action("새 문서", "Ctrl+N", self.new_document)
        add_action("파일 열기…", "Ctrl+O", self.open_file)
        file_menu.addSeparator()
        add_action("저장", "Ctrl+S", self.save_file)
        add_action("다른 이름으로 저장…", "Ctrl+Shift+S", self.save_file_as)
        file_menu.addSeparator()
        quit_action = QAction("끝내기", self)
        quit_action.setShortcut(QKeySequence("Alt+F4"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    # ---------- 페이지 전환 ----------

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self._nav_buttons):
            button.setChecked(i == index)

    def _on_post_generated(self, title: str, body: str) -> None:
        editor = self.editor_page.editor
        if editor.body_plain().strip() and not self._confirm_discard(
            "생성된 글을 에디터에 불러오면 현재 편집 중인 내용이 바뀝니다."
        ):
            return
        editor.set_document(title, body, keep_as_original=True)
        self._current_file = None
        self._switch_page(1)
        self.statusBar().showMessage("AI 글 생성 완료 — 에디터에서 수정하세요.", 5000)

    # ---------- 더티 상태 ----------

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._update_title()

    def _update_title(self) -> None:
        name = self._current_file.name if self._current_file else "새 문서"
        mark = " ●" if self._dirty else ""
        self.setWindowTitle(f"{APP_TITLE} — {name}{mark}")

    def _confirm_discard(self, message: str) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "저장되지 않은 변경 사항",
            f"{message}\n\n저장하지 않은 변경 사항이 있습니다. 계속할까요?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        return answer == QMessageBox.StandardButton.Discard

    # ---------- 파일 ----------

    def new_document(self) -> None:
        if not self._confirm_discard("새 문서를 만들면 현재 내용이 지워집니다."):
            return
        self.editor_page.editor.clear_document()
        self._current_file = None
        self._dirty = False
        self._update_title()
        self._switch_page(1)

    def open_file(self) -> None:
        if not self._confirm_discard("다른 파일을 열면 현재 내용이 바뀝니다."):
            return
        path_str, _ = QFileDialog.getOpenFileName(
            self, "파일 열기", "", FILE_DIALOG_FILTER
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            content = read_document(path)
        except (OSError, UnicodeDecodeError) as exc:
            QMessageBox.critical(self, "파일 열기", f"파일을 열 수 없습니다:\n{exc}")
            return
        self.editor_page.editor.set_document(path.stem, content, keep_as_original=True)
        self._current_file = path
        self._dirty = False
        self._update_title()
        self._switch_page(1)
        self.statusBar().showMessage(f"열기 완료: {path}", 5000)

    def save_file(self) -> bool:
        if self._current_file is None:
            return self.save_file_as()
        return self._write_to(self._current_file)

    def save_file_as(self) -> bool:
        editor = self.editor_page.editor
        default_name = (editor.title().strip() or "새 문서") + "." + str(
            self.settings.get("default_export_format")
        )
        path_str, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 저장", default_name, FILE_DIALOG_FILTER
        )
        if not path_str:
            return False
        path = Path(path_str)
        if self._write_to(path):
            self._current_file = path
            self._update_title()
            return True
        return False

    def _write_to(self, path: Path) -> bool:
        editor = self.editor_page.editor
        title, body = editor.title(), editor.body_plain()
        if path.suffix.lower() == ".html":
            content = export_html(title, body)
        elif path.suffix.lower() == ".md":
            content = f"# {title}\n\n{body}" if title.strip() else body
        else:
            content = f"{title}\n\n{body}" if title.strip() else body
        try:
            write_document(path, content)
        except OSError as exc:
            QMessageBox.critical(self, "저장", f"저장에 실패했습니다:\n{exc}")
            return False
        self._dirty = False
        self._update_title()
        self.statusBar().showMessage(f"저장 완료: {path}", 5000)
        return True

    # ---------- 테마 ----------

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(
            stylesheet(
                theme=self.settings.get("theme"),
                font_size=int(self.settings.get("font_size")),
            )
        )

    # ---------- 종료 ----------

    def closeEvent(self, event):  # noqa: N802
        if self._confirm_discard("프로그램을 종료합니다."):
            event.accept()
        else:
            event.ignore()
