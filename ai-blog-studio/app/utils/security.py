"""OpenAI API 키 보관 — Windows Credential Manager (keyring) 사용.

API 키는 JSON 설정 파일에 저장하지 않는다.
"""

from __future__ import annotations

import keyring

_SERVICE = "AIBlogStudio"
_USERNAME = "openai_api_key"


def save_api_key(api_key: str) -> None:
    keyring.set_password(_SERVICE, _USERNAME, api_key)


def load_api_key() -> str | None:
    try:
        return keyring.get_password(_SERVICE, _USERNAME)
    except keyring.errors.KeyringError:
        return None


def delete_api_key() -> None:
    try:
        keyring.delete_password(_SERVICE, _USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass
