"""OpenAI API 연동.

API 키가 없어도 프로그램의 다른 기능은 정상 동작해야 하므로
이 모듈은 호출 시점에만 키를 확인한다.
"""

from __future__ import annotations

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

from app.utils.security import load_api_key


class AIServiceError(Exception):
    """사용자에게 표시할 한국어 메시지를 담는 예외."""


AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4.1",
]


def _client(timeout: float) -> OpenAI:
    api_key = load_api_key()
    if not api_key:
        raise AIServiceError(
            "OpenAI API 키가 설정되지 않았습니다.\n설정 화면에서 API 키를 입력해 주세요."
        )
    return OpenAI(api_key=api_key, timeout=timeout)


def test_connection(timeout: float = 15.0) -> str:
    """API 연결 테스트. 성공 시 안내 문구 반환."""
    try:
        client = _client(timeout)
        models = client.models.list()
        count = len(models.data)
        return f"연결 성공 — 사용 가능한 모델 {count}개 확인"
    except AIServiceError:
        raise
    except AuthenticationError:
        raise AIServiceError("인증 실패: API 키가 올바르지 않습니다.")
    except APIConnectionError:
        raise AIServiceError("네트워크 오류: 인터넷 연결을 확인해 주세요.")
    except Exception as exc:  # noqa: BLE001
        raise AIServiceError(f"연결 테스트 실패: {exc}")


def generate_post(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    timeout: float = 120.0,
) -> tuple[str, str]:
    """포스팅 생성. (본문 텍스트, 토큰 사용량 안내) 반환."""
    client = _client(timeout)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except AuthenticationError:
        raise AIServiceError("인증 오류: API 키가 올바르지 않습니다.")
    except RateLimitError:
        raise AIServiceError("사용량 한도 초과: OpenAI 결제 한도 또는 요청 빈도를 확인해 주세요.")
    except APITimeoutError:
        raise AIServiceError("요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
    except NotFoundError:
        raise AIServiceError(f"모델 접근 오류: '{model}' 모델을 사용할 수 없습니다.")
    except APIConnectionError:
        raise AIServiceError("네트워크 오류: 인터넷 연결을 확인해 주세요.")
    except Exception as exc:  # noqa: BLE001
        raise AIServiceError(f"API 호출 실패: {exc}")

    content = response.choices[0].message.content or ""
    usage = response.usage
    usage_text = ""
    if usage:
        usage_text = (
            f"토큰 사용량 — 입력 {usage.prompt_tokens:,} / "
            f"출력 {usage.completion_tokens:,} / 합계 {usage.total_tokens:,}"
        )
    return content, usage_text
