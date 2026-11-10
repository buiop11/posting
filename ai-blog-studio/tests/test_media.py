"""미디어 변환 기능 테스트 (사진→GIF/MP4, 영상→GIF)."""

import pytest
from PIL import Image

from app.services.media_service import (
    MediaError,
    images_to_gif,
    images_to_video,
    video_to_gif,
)


@pytest.fixture
def sample_images(tmp_path):
    """크기와 비율이 서로 다른 테스트 이미지 3장."""
    paths = []
    for i, (size, color) in enumerate(
        [((400, 300), "red"), ((300, 400), "green"), ((500, 500), "blue")]
    ):
        path = tmp_path / f"img_{i}.png"
        Image.new("RGB", size, color).save(path)
        paths.append(str(path))
    return paths


class TestImagesToGif:
    def test_creates_animated_gif(self, sample_images, tmp_path):
        output = tmp_path / "out.gif"
        result = images_to_gif(sample_images, output, seconds_per_image=0.5, size=(320, 240))
        assert result.exists()
        with Image.open(result) as gif:
            assert gif.n_frames == 3
            assert gif.size == (320, 240)
            assert gif.info.get("duration") == 500

    def test_requires_two_images(self, sample_images, tmp_path):
        with pytest.raises(MediaError):
            images_to_gif(sample_images[:1], tmp_path / "out.gif")

    def test_bad_image_raises(self, tmp_path):
        bad = tmp_path / "bad.png"
        bad.write_text("이미지 아님")
        with pytest.raises(MediaError):
            images_to_gif([str(bad), str(bad)], tmp_path / "out.gif")


class TestImagesToVideo:
    def test_creates_mp4(self, sample_images, tmp_path):
        output = tmp_path / "out.mp4"
        result = images_to_video(sample_images, output, seconds_per_image=0.5, size=(640, 360))
        assert result.exists()
        assert result.stat().st_size > 1000

    def test_requires_two_images(self, sample_images, tmp_path):
        with pytest.raises(MediaError):
            images_to_video(sample_images[:1], tmp_path / "out.mp4")


class TestVideoToGif:
    def test_video_roundtrip_to_gif(self, sample_images, tmp_path):
        # 사진으로 MP4를 만든 뒤 그 영상을 GIF로 변환하는 전체 경로 검증
        video = images_to_video(
            sample_images, tmp_path / "src.mp4", seconds_per_image=0.5, size=(640, 360)
        )
        gif = video_to_gif(video, tmp_path / "out.gif", fps=5, width=160)
        assert gif.exists()
        with Image.open(gif) as img:
            assert img.format == "GIF"
            assert img.width == 160
            assert img.n_frames > 1

    def test_missing_video_raises(self, tmp_path):
        with pytest.raises(MediaError):
            video_to_gif(tmp_path / "없는파일.mp4", tmp_path / "out.gif")

    def test_trim_range(self, sample_images, tmp_path):
        video = images_to_video(
            sample_images, tmp_path / "src.mp4", seconds_per_image=1.0, size=(640, 360)
        )
        full = video_to_gif(video, tmp_path / "full.gif", fps=5, width=160)
        trimmed = video_to_gif(
            video, tmp_path / "trim.gif", fps=5, width=160,
            start_seconds=0.0, duration_seconds=1.0,
        )
        with Image.open(full) as f, Image.open(trimmed) as t:
            assert t.n_frames < f.n_frames
