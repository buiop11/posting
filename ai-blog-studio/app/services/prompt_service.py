"""프롬프트 관리.

프롬프트는 외부 Markdown 파일로 관리한다.
최초 실행 시 번들된 기본 프롬프트를 사용자 폴더
(%APPDATA%/AIBlogStudio/prompts/)로 복사하여 사용자가 수정할 수 있게 한다.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.utils.settings import app_data_dir, resource_path


def user_prompts_dir() -> Path:
    path = app_data_dir() / "prompts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_default_prompts() -> None:
    """번들 프롬프트를 사용자 폴더로 복사 (이미 있으면 건너뜀)."""
    bundled = resource_path("prompts")
    target = user_prompts_dir()
    if not bundled.exists():
        return
    for source in bundled.glob("*.md"):
        dest = target / source.name
        if not dest.exists():
            shutil.copy2(source, dest)


def list_prompts() -> list[str]:
    """사용 가능한 프롬프트 이름 목록 (확장자 제외)."""
    ensure_default_prompts()
    return sorted(p.stem for p in user_prompts_dir().glob("*.md"))


def load_prompt(name: str) -> str:
    path = user_prompts_dir() / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {path}")
    return path.read_text(encoding="utf-8")


def save_prompt(name: str, content: str) -> None:
    (user_prompts_dir() / f"{name}.md").write_text(content, encoding="utf-8")


def build_messages(
    prompt_name: str,
    platform_label: str,
    topic: str,
    category: str = "",
    extra_conditions: str = "",
) -> list[dict]:
    """OpenAI API 호출용 메시지를 구성한다."""
    system_prompt = load_prompt(prompt_name)

    user_parts = [f"플랫폼: {platform_label}", f"포스팅 주제: {topic}"]
    if category.strip():
        user_parts.append(f"카테고리: {category.strip()}")
    if extra_conditions.strip():
        user_parts.append(f"추가 작성 조건:\n{extra_conditions.strip()}")
    user_parts.append(
        "위 조건에 맞는 블로그 포스팅을 작성해 주세요. "
        "첫 줄에 '제목: <추천 제목>' 형식으로 제목을 쓰고, "
        "빈 줄 뒤에 본문을 작성해 주세요. "
        "본문 마지막에 해시태그 후보를 추가해 주세요."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]


def split_title_body(generated: str) -> tuple[str, str]:
    """생성 결과에서 '제목: ...' 첫 줄을 분리한다."""
    text = generated.strip()
    lines = text.split("\n", 1)
    first = lines[0].strip()
    rest = lines[1].lstrip("\n") if len(lines) > 1 else ""

    for marker in ("제목:", "제목 :", "Title:", "# "):
        if first.startswith(marker):
            return first[len(marker):].strip().strip('"'), rest
    return "", text
