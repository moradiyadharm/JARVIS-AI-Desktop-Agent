# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller --noconfirm JARVIS.spec
# Output: dist\JARVIS\JARVIS.exe (onedir). Copy the voices folder and .env
# into dist\JARVIS\ before running the .exe.
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for package in ("customtkinter", "faster_whisper", "piper", "onnxruntime", "google.genai"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += [
    "pyautogui", "pyscreeze", "pymsgbox", "pytweening", "pyperclip",
    "psutil", "sounddevice", "numpy", "pydantic", "dotenv",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX often breaks ONNX and audio DLLs
    console=True,       # first build: keep the console to see errors. Set False later.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JARVIS",
)
