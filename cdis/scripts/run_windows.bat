@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "CDIS_ROOT=%SCRIPT_DIR%.."

where python >nul 2>nul
if errorlevel 1 (
    echo Python tidak ditemukan di PATH. Install Python 3 dari https://www.python.org/downloads/
    echo dan centang "Add python.exe to PATH" saat instalasi.
    exit /b 1
)

cd /d "%CDIS_ROOT%"
python run.py %*

endlocal
