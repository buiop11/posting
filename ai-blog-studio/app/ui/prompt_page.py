"""프롬프트 관리 페이지 — 보기 / 수정 / 추가."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services import prompt_service


class PromptPage(QWidget):
    prompts_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        page_title = QLabel("프롬프트 관리")
        page_title.setObjectName("pageTitle")
        layout.addWidget(page_title)

        hint = QLabel(
            "프롬프트는 Markdown 파일로 저장됩니다. "
            f"위치: {prompt_service.user_prompts_dir()}"
        )
        hint.setObjectName("statusLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        top = QHBoxLayout()
        self.prompt_combo = QComboBox()
        self.prompt_combo.currentTextChanged.connect(self._load_selected)
        top.addWidget(self.prompt_combo, stretch=1)

        new_btn = QPushButton("새 프롬프트")
        new_btn.clicked.connect(self._create_new)
        top.addWidget(new_btn)

        save_btn = QPushButton("저장")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        top.addWidget(save_btn)
        layout.addLayout(top)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("프롬프트 내용을 입력하세요")
        layout.addWidget(self.content_edit, stretch=1)

        self.refresh()

    def refresh(self) -> None:
        current = self.prompt_combo.currentText()
        self.prompt_combo.blockSignals(True)
        self.prompt_combo.clear()
        names = prompt_service.list_prompts()
        self.prompt_combo.addItems(names)
        if current in names:
            self.prompt_combo.setCurrentText(current)
        self.prompt_combo.blockSignals(False)
        self._load_selected(self.prompt_combo.currentText())

    def _load_selected(self, name: str) -> None:
        if not name:
            self.content_edit.clear()
            return
        try:
            self.content_edit.setPlainText(prompt_service.load_prompt(name))
        except FileNotFoundError:
            self.content_edit.clear()

    def _save(self) -> None:
        name = self.prompt_combo.currentText()
        if not name:
            return
        prompt_service.save_prompt(name, self.content_edit.toPlainText())
        QMessageBox.information(self, "프롬프트", f"'{name}' 프롬프트를 저장했습니다.")
        self.prompts_changed.emit()

    def _create_new(self) -> None:
        name, ok = QInputDialog.getText(
            self, "새 프롬프트", "프롬프트 이름 (파일명으로 사용):"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in prompt_service.list_prompts():
            QMessageBox.warning(self, "새 프롬프트", "같은 이름의 프롬프트가 이미 있습니다.")
            return
        prompt_service.save_prompt(name, "당신은 블로그 포스팅 전문 작가입니다.\n\n글쓰기 규칙:\n\n1. ")
        self.refresh()
        self.prompt_combo.setCurrentText(name)
        self.prompts_changed.emit()
