@echo off
REM =========================================================
REM build_exe.bat  –  Build ZimAgent Desktop .exe (Windows)
REM Requires:  pip install pyinstaller
REM =========================================================

echo [ZimAgent] Building Windows .exe with PyInstaller...

REM Clean previous builds
if exist build\   rmdir /s /q build
if exist dist\    rmdir /s /q dist

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ZimAgent" ^
    --icon "zimagent\resources\icons\logo.ico" ^
    --add-data "zimagent\resources;zimagent\resources" ^
    --add-data "models;models" ^
    --hidden-import "PyQt5.QtWebEngineWidgets" ^
    --hidden-import "PyQt5.sip" ^
    --hidden-import "psutil" ^
    run_app.py

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed.
    exit /b 1
)

echo [ZimAgent] Build complete: dist\ZimAgent.exe
pause
