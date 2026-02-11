"""
Portable packaging script for Particle Process Interface.

Copies the Poetry virtual environment (with symlink resolution) and project
files into a self-contained distributable folder.

Usage:
    python build.py

Output:
    dist/ParticleApp/          - the portable folder
"""

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DIST_DIR = PROJECT_ROOT / "dist"
APP_DIR = DIST_DIR / "ParticleApp"
VENV_SRC = Path(sys.prefix)  # Poetry venv location

# Directories to copy from the project
PROJECT_DIRS = [
    "boxmot",
    "tracking",
    "new",
    "weights",
]

# Individual files to copy
PROJECT_FILES = [
    "app.py",
    "config.json",
    "yolov8-particle-best.pt",
    "yolov8_best.pt",
    "best_model_new_eff1.pth",
    "osnet_x0_25_msmt17.pt",
]

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".pytest_cache")


def main():
    print("=" * 60)
    print("Packaging Particle Process Interface")
    print("=" * 60)
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Venv source  : {VENV_SRC}")
    print(f"Output       : {APP_DIR}")
    print("=" * 60)

    # Clean previous build
    if APP_DIR.exists():
        print("Removing previous build...")
        shutil.rmtree(APP_DIR)
    APP_DIR.mkdir(parents=True)

    # 1. Copy virtual environment (symlinks=False resolves all symlinks to real files)
    venv_dst = APP_DIR / "venv"
    print("\n[1/3] Copying virtual environment -> venv/ ...")
    shutil.copytree(VENV_SRC, venv_dst, symlinks=False, ignore=IGNORE)
    # Verify python.exe was copied
    python_exe = venv_dst / "Scripts" / "python.exe"
    if python_exe.exists():
        print(f"  python.exe OK ({python_exe.stat().st_size / 1024:.0f} KB)")
    else:
        print("  WARNING: python.exe not found in copied venv!")

    # 2. Copy project directories and files
    print("\n[2/3] Copying project directories and files ...")
    for d in PROJECT_DIRS:
        src = PROJECT_ROOT / d
        if src.exists():
            print(f"  {d}/")
            shutil.copytree(src, APP_DIR / d, symlinks=False, ignore=IGNORE, dirs_exist_ok=True)
        else:
            print(f"  WARNING: {d}/ not found, skipping")

    for f in PROJECT_FILES:
        src = PROJECT_ROOT / f
        if src.exists():
            print(f"  {f}  ({src.stat().st_size / 1024 / 1024:.1f} MB)")
            shutil.copy2(src, APP_DIR / f)
        else:
            print(f"  WARNING: {f} not found, skipping")

    # 3. Create startup script
    print("\n[3/3] Creating start.bat ...")
    bat_content = r"""@echo off
chcp 65001 >nul
title Particle Process Interface
cd /d "%~dp0"

echo ============================================================
echo   Particle Process Interface
echo ============================================================
echo.

set "PYTHON=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Please ensure the venv folder is intact.
    pause
    exit /b 1
)

echo Starting application...
echo Once the server is running, open the URL shown below in your browser.
echo Press Ctrl+C to stop the server.
echo.

"%PYTHON%" app.py

pause
"""
    (APP_DIR / "start.bat").write_text(bat_content, encoding="utf-8")

    # Summary
    total_size = sum(f.stat().st_size for f in APP_DIR.rglob("*") if f.is_file())
    print("\n" + "=" * 60)
    print("Packaging complete!")
    print(f"Output folder : {APP_DIR}")
    print(f"Total size    : {total_size / 1024 / 1024:.0f} MB")
    print("=" * 60)
    print("\nTo distribute:")
    print(f"  1. Copy the entire '{APP_DIR}' folder to the target machine")
    print("  2. Double-click 'start.bat' to launch")
    print("  3. Open the Gradio URL shown in the console")
    print("=" * 60)


if __name__ == "__main__":
    main()
