"""미디어 변환: 사진 → GIF/영상(MP4), 영상 → GIF.

- 사진 → GIF: Pillow로 직접 생성 (외부 의존 없음)
- 사진 → MP4, 영상 → GIF: imageio-ffmpeg가 번들하는 ffmpeg 실행 파일 사용
EXE 패키징 시에도 ffmpeg가 함께 번들되어 단독 실행이 유지된다.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv"}

IMAGE_DIALOG_FILTER = "이미지 (*.jpg *.jpeg *.png *.bmp *.webp *.gif);;모든 파일 (*.*)"
VIDEO_DIALOG_FILTER = "동영상 (*.mp4 *.mov *.avi *.mkv *.webm *.wmv);;모든 파일 (*.*)"

# (라벨, 너비, 높이) — H.264는 짝수 크기만 허용되므로 짝수로 유지
CANVAS_PRESETS = [
    ("가로 1280×720", 1280, 720),
    ("정방형 1080×1080", 1080, 1080),
    ("세로 720×1280", 720, 1280),
    ("가로 작게 854×480", 854, 480),
]


class MediaError(Exception):
    """사용자에게 표시할 한국어 메시지를 담는 예외."""


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise MediaError(f"ffmpeg를 찾을 수 없습니다: {exc}")


def _run_ffmpeg(args: list[str]) -> None:
    creationflags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    result = subprocess.run(
        [_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *args],
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        raise MediaError(
            "변환에 실패했습니다.\n" + "\n".join(detail[-3:] or ["알 수 없는 ffmpeg 오류"])
        )


def _load_frame(path: str | Path, size: tuple[int, int], bg: str = "#FFFFFF") -> Image.Image:
    """이미지를 캔버스 크기에 맞춰 축소하고 중앙 배치한다 (비율 유지, 여백 채움)."""
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", size, bg)
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            canvas.paste(img, offset)
            return canvas
    except (OSError, ValueError) as exc:
        raise MediaError(f"이미지를 열 수 없습니다: {path}\n{exc}")


def images_to_gif(
    image_paths: list[str],
    output_path: str | Path,
    seconds_per_image: float = 1.5,
    size: tuple[int, int] = (854, 480),
) -> Path:
    """사진 여러 장을 슬라이드쇼 GIF로 만든다."""
    if len(image_paths) < 2:
        raise MediaError("GIF를 만들려면 사진이 2장 이상 필요합니다.")
    frames = [_load_frame(p, size) for p in image_paths]
    output_path = Path(output_path)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(seconds_per_image * 1000),
        loop=0,
        optimize=True,
    )
    return output_path


def images_to_video(
    image_paths: list[str],
    output_path: str | Path,
    seconds_per_image: float = 1.5,
    size: tuple[int, int] = (1280, 720),
) -> Path:
    """사진 여러 장을 MP4 슬라이드쇼 영상으로 만든다."""
    if len(image_paths) < 2:
        raise MediaError("영상을 만들려면 사진이 2장 이상 필요합니다.")
    output_path = Path(output_path)

    with tempfile.TemporaryDirectory(prefix="aiblog_media_") as tmp:
        tmp_dir = Path(tmp)
        frame_files = []
        for i, path in enumerate(image_paths):
            frame_path = tmp_dir / f"frame_{i:04d}.png"
            _load_frame(path, size).save(frame_path)
            frame_files.append(frame_path)

        # concat demuxer: 장당 표시 시간 지정 (마지막 프레임은 한 번 더 적어야 시간이 적용됨)
        concat_lines = []
        for frame_path in frame_files:
            concat_lines.append(f"file '{frame_path.as_posix()}'")
            concat_lines.append(f"duration {seconds_per_image}")
        concat_lines.append(f"file '{frame_files[-1].as_posix()}'")
        concat_file = tmp_dir / "list.txt"
        concat_file.write_text("\n".join(concat_lines), encoding="utf-8")

        _run_ffmpeg([
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", "fps=30,format=yuv420p",
            "-c:v", "libx264",
            "-movflags", "+faststart",
            str(output_path),
        ])
    return output_path


def video_to_gif(
    video_path: str | Path,
    output_path: str | Path,
    fps: int = 10,
    width: int = 480,
    start_seconds: float = 0.0,
    duration_seconds: float | None = None,
) -> Path:
    """영상(구간)을 고품질 GIF로 변환한다 (2-pass 팔레트 방식)."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise MediaError(f"영상 파일을 찾을 수 없습니다: {video_path}")
    output_path = Path(output_path)

    args: list[str] = []
    if start_seconds > 0:
        args += ["-ss", str(start_seconds)]
    if duration_seconds and duration_seconds > 0:
        args += ["-t", str(duration_seconds)]
    filters = (
        f"fps={fps},scale={width}:-1:flags=lanczos,"
        "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
    )
    args += ["-i", str(video_path), "-vf", filters, str(output_path)]
    _run_ffmpeg(args)
    return output_path
