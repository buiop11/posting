# AI Blog Studio

네이버 블로그·티스토리 포스팅을 AI로 생성하거나, ChatGPT에서 복사한 글을 정리·편집할 수 있는 Windows 데스크톱 프로그램입니다.

- 서버·데이터베이스 없이 EXE 단독 실행
- OpenAI API 키 없이도 직접 편집 기능 사용 가능 (오프라인 동작)
- API 키는 Windows 자격 증명 관리자에 안전하게 저장

## 주요 기능

| 기능 | 설명 |
|---|---|
| AI 글 작성 | 주제 입력 → Nblog1 스타일 프롬프트로 OpenAI API 글 생성 |
| 직접 편집 | ChatGPT에서 복사한 글 붙여넣기 후 편집 |
| Markdown 정리 | `##`, `**`, `\` 등 불필요한 기호 제거 (코드 블록·URL·파일 경로 보호) |
| 원본 복구 | 정리/수정 전 원본으로 복원 |
| 글자 수 | 공백 포함/제외 실시간 표시 |
| 파일 | MD / TXT / HTML 저장 및 불러오기 |
| 블로그용 복사 | 제목·본문·전체 복사, 네이버/티스토리 글쓰기 페이지 열기 |
| 테마 | 라이트(기본) / 다크 모드 |

## 실행 방법

### 방법 1 — EXE 실행 (권장)

`dist\AI_Blog_Studio.exe` 를 더블클릭합니다. Python 설치가 필요 없습니다.

### 방법 2 — 소스 실행 (개발용)

```powershell
python -m pip install -r requirements.txt
python main.py
```

## EXE 빌드

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

빌드 결과: `dist\AI_Blog_Studio.exe`

## 테스트

```powershell
python -m pip install pytest
python -m pytest tests -q
```

## AI 기능 사용 준비

1. https://platform.openai.com 에서 API 키 발급 (ChatGPT Plus 구독과 별개이며 사용량에 따라 과금됩니다)
2. 프로그램 → 설정 → OpenAI API 키 입력 → **키 저장**
3. **연결 테스트**로 확인 후 "AI 글 작성" 탭 사용

## Nblog1 프롬프트 교체

기본 제공되는 프롬프트는 자리표시용입니다. 실제 사용하던 Nblog1 프롬프트 원문으로 교체하세요.

- 프로그램 안에서: **프롬프트** 탭 → `nblog1` 선택 → 내용 교체 → 저장
- 또는 파일 직접 수정: `%APPDATA%\AIBlogStudio\prompts\nblog1.md`

## 단축키

| 단축키 | 기능 |
|---|---|
| Ctrl+N / Ctrl+O / Ctrl+S / Ctrl+Shift+S | 새 문서 / 열기 / 저장 / 다른 이름으로 저장 |
| Ctrl+V | 붙여넣기 |
| Ctrl+Shift+V | 붙여넣기 후 Markdown 자동 정리 |
| Ctrl+Z / Ctrl+Y | 실행 취소 / 다시 실행 |
| Ctrl+B / Ctrl+I / Ctrl+U | 굵게 / 기울임 / 밑줄 |

## 데이터 저장 위치

- 설정: `%APPDATA%\AIBlogStudio\settings.json` (API 키는 저장되지 않음)
- 프롬프트: `%APPDATA%\AIBlogStudio\prompts\*.md`
- API 키: Windows 자격 증명 관리자
- 문서: 사용자가 직접 선택한 경로

## 프로젝트 구조

```
ai-blog-studio/
├── main.py                  # 진입점
├── build.spec               # PyInstaller 스펙
├── prompts/                 # 기본 프롬프트 (번들)
├── app/
│   ├── ui/                  # PySide6 화면 (메인/생성/편집/프롬프트/설정)
│   ├── services/            # AI·프롬프트·Markdown 정리·내보내기
│   ├── platforms/           # 네이버 / 티스토리
│   └── utils/               # 설정·파일·API 키 보안
├── tests/                   # pytest 테스트
└── scripts/build_windows.ps1
```
