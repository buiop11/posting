"""설정 페이지 — OpenAI API · 모델 · 테마 · 글꼴 · 기본 플랫폼."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.platforms import PLATFORM_LABELS
from app.services import ai_service
from app.services.ai_service import AIServiceError
from app.utils import security
from app.utils.settings import Settings


class SettingsPage(QWidget):
    theme_changed = Signal()

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        page_title = QLabel("설정")
        page_title.setObjectName("pageTitle")
        outer.addWidget(page_title)

        def field_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setObjectName("fieldLabel")
            return label

        def card() -> tuple[QFrame, QVBoxLayout]:
            frame = QFrame()
            frame.setObjectName("card")
            inner = QVBoxLayout(frame)
            inner.setContentsMargins(24, 20, 24, 20)
            inner.setSpacing(10)
            return frame, inner

        # ----- OpenAI API 카드 -----
        api_card, api_layout = card()
        api_layout.addWidget(field_label("OpenAI API 키"))

        key_row = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText(
            "저장된 키 있음" if security.load_api_key() else "sk-..."
        )
        key_row.addWidget(self.api_key_edit, stretch=1)

        save_key_btn = QPushButton("키 저장")
        save_key_btn.clicked.connect(self._save_key)
        key_row.addWidget(save_key_btn)

        test_btn = QPushButton("연결 테스트")
        test_btn.clicked.connect(self._test_connection)
        key_row.addWidget(test_btn)

        delete_btn = QPushButton("키 삭제")
        delete_btn.clicked.connect(self._delete_key)
        key_row.addWidget(delete_btn)
        api_layout.addLayout(key_row)

        note = QLabel("API 키는 Windows 자격 증명 관리자에 안전하게 저장됩니다.")
        note.setObjectName("statusLabel")
        api_layout.addWidget(note)

        model_row = QHBoxLayout()
        model_col = QVBoxLayout()
        model_col.addWidget(field_label("기본 모델"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(ai_service.AVAILABLE_MODELS)
        self.model_combo.setCurrentText(settings.get("openai_model"))
        self.model_combo.currentTextChanged.connect(
            lambda value: self.settings.set("openai_model", value)
        )
        model_col.addWidget(self.model_combo)
        model_row.addLayout(model_col)

        timeout_col = QVBoxLayout()
        timeout_col.addWidget(field_label("요청 타임아웃 (초)"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setValue(int(settings.get("request_timeout")))
        self.timeout_spin.valueChanged.connect(
            lambda value: self.settings.set("request_timeout", value)
        )
        timeout_col.addWidget(self.timeout_spin)
        model_row.addLayout(timeout_col)
        api_layout.addLayout(model_row)
        outer.addWidget(api_card)

        # ----- 화면 카드 -----
        ui_card, ui_layout = card()
        ui_row = QHBoxLayout()

        theme_col = QVBoxLayout()
        theme_col.addWidget(field_label("테마"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("라이트", "light")
        self.theme_combo.addItem("다크", "dark")
        index = self.theme_combo.findData(settings.get("theme"))
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_col.addWidget(self.theme_combo)
        ui_row.addLayout(theme_col)

        font_col = QVBoxLayout()
        font_col.addWidget(field_label("글꼴 크기"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(int(settings.get("font_size")))
        self.font_spin.valueChanged.connect(self._on_font_changed)
        font_col.addWidget(self.font_spin)
        ui_row.addLayout(font_col)

        platform_col = QVBoxLayout()
        platform_col.addWidget(field_label("기본 플랫폼"))
        self.platform_combo = QComboBox()
        for key, label in PLATFORM_LABELS.items():
            self.platform_combo.addItem(label, key)
        index = self.platform_combo.findData(settings.get("default_platform"))
        if index >= 0:
            self.platform_combo.setCurrentIndex(index)
        self.platform_combo.currentIndexChanged.connect(
            lambda _: self.settings.set("default_platform", self.platform_combo.currentData())
        )
        platform_col.addWidget(self.platform_combo)
        ui_row.addLayout(platform_col)

        ui_layout.addLayout(ui_row)
        outer.addWidget(ui_card)
        outer.addStretch()

    # ----- API 키 -----

    def _save_key(self) -> None:
        key = self.api_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "API 키", "API 키를 입력해 주세요.")
            return
        security.save_api_key(key)
        self.api_key_edit.clear()
        self.api_key_edit.setPlaceholderText("저장된 키 있음")
        QMessageBox.information(self, "API 키", "API 키를 저장했습니다.")

    def _test_connection(self) -> None:
        try:
            message = ai_service.test_connection()
            QMessageBox.information(self, "연결 테스트", message)
        except AIServiceError as exc:
            QMessageBox.critical(self, "연결 테스트", str(exc))

    def _delete_key(self) -> None:
        security.delete_api_key()
        self.api_key_edit.setPlaceholderText("sk-...")
        QMessageBox.information(self, "API 키", "저장된 API 키를 삭제했습니다.")

    # ----- 화면 -----

    def _on_theme_changed(self) -> None:
        self.settings.set("theme", self.theme_combo.currentData())
        self.theme_changed.emit()

    def _on_font_changed(self, value: int) -> None:
        self.settings.set("font_size", value)
        self.theme_changed.emit()
