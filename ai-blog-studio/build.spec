# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 빌드 스펙 — AI_Blog_Studio.exe

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('prompts', 'prompts'),  # 기본 프롬프트 번들 (최초 실행 시 AppData로 복사)
    ],
    hiddenimports=[
        'keyring.backends.Windows',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore',
        'PySide6.QtCharts',
        'PySide6.QtMultimedia',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        # 전역 site-packages에 설치된 무관한 대형 패키지 차단
        'numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib', 'sympy',
        'torch', 'torchaudio', 'torchvision', 'tensorflow', 'transformers',
        'numba', 'llvmlite', 'pyarrow', 'librosa', 'soundfile',
        'PIL', 'cv2', 'IPython', 'jedi', 'parso', 'pytest', 'py',
        'zmq', 'uvicorn', 'fastapi', 'psutil', 'fsspec', 'win32com',
        'pythoncom', 'notebook', 'jupyter', 'sqlite3',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AI_Blog_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
