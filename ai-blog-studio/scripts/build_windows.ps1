# AI Blog Studio — Windows EXE 빌드 스크립트
# 사용법: 프로젝트 루트에서  powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "[1/3] 의존성 설치" -ForegroundColor Cyan
python -m pip install -r requirements.txt pyinstaller

Write-Host "[2/3] 테스트 실행" -ForegroundColor Cyan
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "테스트 실패 — 빌드를 중단합니다." -ForegroundColor Red
    exit 1
}

Write-Host "[3/3] PyInstaller 빌드" -ForegroundColor Cyan
python -m PyInstaller build.spec --noconfirm --clean

if (Test-Path "dist\AI_Blog_Studio.exe") {
    Write-Host "빌드 완료: dist\AI_Blog_Studio.exe" -ForegroundColor Green
} else {
    Write-Host "빌드 실패: EXE 파일이 생성되지 않았습니다." -ForegroundColor Red
    exit 1
}
