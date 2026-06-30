@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python tidak ditemukan di PATH. Install Python 3 dari https://www.python.org/downloads/
    echo dan centang "Add python.exe to PATH" saat instalasi.
    exit /b 1
)

echo Python ditemukan. Virtual environment dan dependency akan dipasang
echo otomatis saat pertama kali menjalankan scripts\run_windows.bat.

endlocal
