"""미디어 도구 페이지 — 사진 → GIF/영상, 영상 → GIF."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.services import media_service
from app.services.media_service import (
    CANVAS_PRESETS,
    IMAGE_DIALOG_FILTER,
    VIDEO_DIALOG_FILTER,
    MediaError,
)


class MediaWorker(QThread):
    """변환 작업을 백그라운드에서 수행 (UI 블로킹 방지)."""

    finished_ok = Signal(str)   # 결과 파일 경로
    failed = Signal(str)

    def __init__(self, func, kwargs: dict, parent=None):
        super().__init__(parent)
        self._func = func
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._func(**self._kwargs)
            self.finished_ok.emit(str(result))
        except MediaError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"알 수 없는 오류: {exc}")


class MediaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: MediaWorker | None = None
        self._video_path: Path | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        page_title = QLabel("미디어 도구")
        page_title.setObjectName("pageTitle")
        layout.addWidget(page_title)

        layout.addWidget(self._build_slideshow_card())
        layout.addWidget(self._build_video_card())
        layout.addStretch()

    # ================= 사진 → GIF / 영상 =================

    def _build_slideshow_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("사진 → GIF / 영상 만들기")
        title.setObjectName("fieldLabel")
        layout.addWidget(title)

        hint = QLabel("사진 2장 이상을 추가하면 슬라이드쇼 GIF 또는 MP4 영상을 만듭니다.")
        hint.setObjectName("statusLabel")
        layout.addWidget(hint)

        body = QHBoxLayout()
        self.image_list = QListWidget()
        self.image_list.setMinimumHeight(140)
        body.addWidget(self.image_list, stretch=1)

        side = QVBoxLayout()
        for text, slot in (
            ("사진 추가", self._add_images),
            ("선택 제거", self._remove_selected_image),
            ("위로 ↑", lambda: self._move_image(-1)),
            ("아래로 ↓", lambda: self._move_image(1)),
        ):
            button = QPushButton(text)
            button.clicked.connect(slot)
            side.addWidget(button)
        side.addStretch()
        body.addLayout(side)
        layout.addLayout(body)

        options = QHBoxLayout()
        options.addWidget(QLabel("장당 시간"))
        self.seconds_spin = QDoubleSpinBox()
        self.seconds_spin.setRange(0.2, 10.0)
        self.seconds_spin.setSingleStep(0.1)
        self.seconds_spin.setValue(1.5)
        self.seconds_spin.setSuffix(" 초")
        options.addWidget(self.seconds_spin)

        options.addWidget(QLabel("크기"))
        self.canvas_combo = QComboBox()
        for label, width, height in CANVAS_PRESETS:
            self.canvas_combo.addItem(label, (width, height))
        options.addWidget(self.canvas_combo)
        options.addStretch()

        self.gif_btn = QPushButton("GIF 만들기")
        self.gif_btn.setObjectName("primaryButton")
        self.gif_btn.clicked.connect(self._make_gif)
        options.addWidget(self.gif_btn)

        self.video_btn = QPushButton("영상(MP4) 만들기")
        self.video_btn.setObjectName("primaryButton")
        self.video_btn.clicked.connect(self._make_video)
        options.addWidget(self.video_btn)
        layout.addLayout(options)

        self.slideshow_status = QLabel("")
        self.slideshow_status.setObjectName("statusLabel")
        layout.addWidget(self.slideshow_status)
        return card

    def _add_images(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "사진 추가", "", IMAGE_DIALOG_FILTER)
        for path in paths:
            self.image_list.addItem(path)

    def _remove_selected_image(self) -> None:
        for item in self.image_list.selectedItems():
            self.image_list.takeItem(self.image_list.row(item))

    def _move_image(self, delta: int) -> None:
        row = self.image_list.currentRow()
        if row < 0:
            return
        new_row = row + delta
        if 0 <= new_row < self.image_list.count():
            item = self.image_list.takeItem(row)
            self.image_list.insertItem(new_row, item)
            self.image_list.setCurrentRow(new_row)

    def _image_paths(self) -> list[str]:
        return [self.image_list.item(i).text() for i in range(self.image_list.count())]

    def _make_gif(self) -> None:
        self._make_slideshow("GIF (*.gif)", "slideshow.gif", media_service.images_to_gif)

    def _make_video(self) -> None:
        self._make_slideshow("MP4 영상 (*.mp4)", "slideshow.mp4", media_service.images_to_video)

    def _make_slideshow(self, file_filter: str, default_name: str, func) -> None:
        paths = self._image_paths()
        if len(paths) < 2:
            QMessageBox.warning(self, "미디어 도구", "사진을 2장 이상 추가해 주세요.")
            return
        output, _ = QFileDialog.getSaveFileName(self, "저장 위치", default_name, file_filter)
        if not output:
            return
        self._start_worker(
            func,
            {
                "image_paths": paths,
                "output_path": output,
                "seconds_per_image": self.seconds_spin.value(),
                "size": self.canvas_combo.currentData(),
            },
            self.slideshow_status,
            (self.gif_btn, self.video_btn),
        )

    # ================= 영상 → GIF =================

    def _build_video_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("영상 → GIF 변환")
        title.setObjectName("fieldLabel")
        layout.addWidget(title)

        pick_row = QHBoxLayout()
        pick_btn = QPushButton("영상 선택")
        pick_btn.clicked.connect(self._pick_video)
        pick_row.addWidget(pick_btn)
        self.video_label = QLabel("선택된 영상 없음")
        self.video_label.setObjectName("statusLabel")
        pick_row.addWidget(self.video_label, stretch=1)
        layout.addLayout(pick_row)

        options = QHBoxLayout()
        options.addWidget(QLabel("시작"))
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0.0, 36000.0)
        self.start_spin.setSuffix(" 초")
        options.addWidget(self.start_spin)

        options.addWidget(QLabel("길이"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.0, 600.0)
        self.duration_spin.setValue(0.0)
        self.duration_spin.setSuffix(" 초")
        self.duration_spin.setSpecialValueText("전체")
        options.addWidget(self.duration_spin)

        options.addWidget(QLabel("초당 프레임"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 30)
        self.fps_spin.setValue(10)
        options.addWidget(self.fps_spin)

        options.addWidget(QLabel("너비"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(120, 1920)
        self.width_spin.setSingleStep(40)
        self.width_spin.setValue(480)
        self.width_spin.setSuffix(" px")
        options.addWidget(self.width_spin)
        options.addStretch()

        self.convert_btn = QPushButton("GIF로 변환")
        self.convert_btn.setObjectName("primaryButton")
        self.convert_btn.clicked.connect(self._convert_video)
        options.addWidget(self.convert_btn)
        layout.addLayout(options)

        hint = QLabel(
            "팁: 블로그용 GIF는 너비 480px, 10fps, 2~6초 구간이 용량 대비 보기 좋습니다."
        )
        hint.setObjectName("statusLabel")
        layout.addWidget(hint)

        self.video_status = QLabel("")
        self.video_status.setObjectName("statusLabel")
        layout.addWidget(self.video_status)
        return card

    def _pick_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "영상 선택", "", VIDEO_DIALOG_FILTER)
        if path:
            self._video_path = Path(path)
            self.video_label.setText(path)

    def _convert_video(self) -> None:
        if self._video_path is None:
            QMessageBox.warning(self, "미디어 도구", "먼저 영상을 선택해 주세요.")
            return
        default_name = self._video_path.stem + ".gif"
        output, _ = QFileDialog.getSaveFileName(self, "저장 위치", default_name, "GIF (*.gif)")
        if not output:
            return
        duration = self.duration_spin.value()
        self._start_worker(
            media_service.video_to_gif,
            {
                "video_path": str(self._video_path),
                "output_path": output,
                "fps": self.fps_spin.value(),
                "width": self.width_spin.value(),
                "start_seconds": self.start_spin.value(),
                "duration_seconds": duration if duration > 0 else None,
            },
            self.video_status,
            (self.convert_btn,),
        )

    # ================= 공통 =================

    def _start_worker(self, func, kwargs: dict, status_label: QLabel, buttons) -> None:
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(self, "미디어 도구", "이미 변환이 진행 중입니다.")
            return
        for button in buttons:
            button.setEnabled(False)
        status_label.setText("변환 중입니다… 잠시만 기다려 주세요.")

        self._worker = MediaWorker(func, kwargs, parent=self)

        def on_done(result_path: str) -> None:
            for button in buttons:
                button.setEnabled(True)
            size_mb = Path(result_path).stat().st_size / (1024 * 1024)
            status_label.setText(f"완료: {result_path} ({size_mb:.1f}MB)")

        def on_fail(message: str) -> None:
            for button in buttons:
                button.setEnabled(True)
            status_label.setText("")
            QMessageBox.critical(self, "변환 실패", message)

        self._worker.finished_ok.connect(on_done)
        self._worker.failed.connect(on_fail)
        self._worker.start()
