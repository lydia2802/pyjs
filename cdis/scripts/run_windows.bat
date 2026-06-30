@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "CDIS_ROOT=%SCRIPT_DIR%.."

if exist "%CDIS_ROOT%\venv\Scripts\activate.bat" (
    call "%CDIS_ROOT%\venv\Scripts\activate.bat"
)

cd /d "%CDIS_ROOT%\backend"
python app.py

endlocal
