"""AI 글 작성 페이지."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.platforms import PLATFORM_LABELS
from app.services import ai_service, prompt_service
from app.services.ai_service import AIServiceError
from app.utils.settings import Settings


class GenerateWorker(QThread):
    """API 호출을 백그라운드에서 수행 (UI 블로킹 방지)."""

    finished_ok = Signal(str, str)   # (생성 결과, 토큰 사용량)
    failed = Signal(str)

    def __init__(self, messages: list[dict], model: str, timeout: float, parent=None):
        super().__init__(parent)
        self._messages = messages
        self._model = model
        self._timeout = timeout

    def run(self) -> None:
        try:
            content, usage = ai_service.generate_post(
                self._messages, model=self._model, timeout=self._timeout
            )
            self.finished_ok.emit(content, usage)
        except AIServiceError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"알 수 없는 오류: {exc}")


class GeneratorPage(QWidget):
    # (제목, 본문) — 메인 윈도우가 받아 공통 에디터에 싣는다
    post_generated = Signal(str, str)

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._worker: GenerateWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        page_title = QLabel("새로운 포스팅")
        page_title.setObjectName("pageTitle")
        outer.addWidget(page_title)

        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        def field_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setObjectName("fieldLabel")
            return label

        row = QHBoxLayout()
        platform_col = QVBoxLayout()
        platform_col.addWidget(field_label("플랫폼"))
        self.platform_combo = QComboBox()
        for key, label in PLATFORM_LABELS.items():
            self.platform_combo.addItem(label, key)
        default_platform = settings.get("default_platform")
        index = self.platform_combo.findData(default_platform)
        if index >= 0:
            self.platform_combo.setCurrentIndex(index)
        platform_col.addWidget(self.platform_combo)
        row.addLayout(platform_col)

        prompt_col = QVBoxLayout()
        prompt_col.addWidget(field_label("프롬프트"))
        self.prompt_combo = QComboBox()
        prompt_col.addWidget(self.prompt_combo)
        row.addLayout(prompt_col)
        layout.addLayout(row)

        layout.addWidget(field_label("카테고리 (선택)"))
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("예: 건강, 요리, 여행")
        layout.addWidget(self.category_edit)

        layout.addWidget(field_label("포스팅 주제"))
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("주제를 입력하세요")
        layout.addWidget(self.topic_edit)

        layout.addWidget(field_label("추가 작성 조건 (선택)"))
        self.conditions_edit = QTextEdit()
        self.conditions_edit.setPlaceholderText(
            "추가 조건을 입력하세요 (핵심 키워드, 분량, 참고 자료 등)"
        )
        self.conditions_edit.setMaximumHeight(120)
        layout.addWidget(self.conditions_edit)

        button_row = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        button_row.addWidget(self.status_label)
        button_row.addStretch()

        self.generate_btn = QPushButton("✦ AI 글 생성하기")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.clicked.connect(self._generate)
        button_row.addWidget(self.generate_btn)
        layout.addLayout(button_row)

        outer.addWidget(card)
        outer.addStretch()

        self.refresh_prompts()

    def refresh_prompts(self) -> None:
        current = self.prompt_combo.currentText()
        self.prompt_combo.clear()
        names = prompt_service.list_prompts()
        self.prompt_combo.addItems(names)
        preferred = current or self.settings.get("default_prompt")
        if preferred in names:
            self.prompt_combo.setCurrentText(preferred)

    def _generate(self) -> None:
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "AI 글 생성", "포스팅 주제를 입력해 주세요.")
            return
        prompt_name = self.prompt_combo.currentText()
        if not prompt_name:
            QMessageBox.warning(self, "AI 글 생성", "사용할 프롬프트가 없습니다.")
            return

        try:
            messages = prompt_service.build_messages(
                prompt_name=prompt_name,
                platform_label=self.platform_combo.currentText(),
                topic=topic,
                category=self.category_edit.text(),
                extra_conditions=self.conditions_edit.toPlainText(),
            )
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "AI 글 생성", str(exc))
            return

        self.generate_btn.setEnabled(False)
        self.status_label.setText("AI가 글을 작성하는 중입니다…")

        self._worker = GenerateWorker(
            messages,
            model=self.settings.get("openai_model"),
            timeout=float(self.settings.get("request_timeout")),
            parent=self,
        )
        self._worker.finished_ok.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def _on_success(self, content: str, usage: str) -> None:
        self.generate_btn.setEnabled(True)
        self.status_label.setText(usage or "생성 완료")
        title, body = prompt_service.split_title_body(content)
        self.post_generated.emit(title, body)

    def _on_failure(self, message: str) -> None:
        self.generate_btn.setEnabled(True)
        self.status_label.setText("")
        # 오류가 나도 기존 편집 내용은 그대로 보존된다 (에디터를 건드리지 않음)
        QMessageBox.critical(self, "AI 글 생성 실패", message)
