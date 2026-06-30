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

echo ==^> Membuat virtual environment
python -m venv "%CDIS_ROOT%\venv"

echo ==^> Mengaktifkan virtual environment
call "%CDIS_ROOT%\venv\Scripts\activate.bat"

echo ==^> Upgrade pip
python -m pip install --upgrade pip

echo ==^> Install dependencies backend
pip install -r "%CDIS_ROOT%\backend\requirements.txt"

echo.
echo Setup selesai.
echo Jalankan backend dengan: scripts\run_windows.bat
echo Lalu gunakan CLI di terminal lain: python cli\cdis.py health
echo.
echo Opsional - dukungan scan mobile (mvt-android jalan di Windows, mvt-ios butuh WSL/Linux):
echo   pip install -r backend\requirements-mvt.txt

endlocal
