#!/usr/bin/env bash
# Checks prerequisites for CDIS on Linux/macOS.
# (Python venv + pip dependencies are handled automatically by run.py.)
set -e

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "$PYTHON_BIN tidak ditemukan. Install Python 3 lewat package manager distro Anda."
    exit 1
fi

echo "Python ditemukan ($("$PYTHON_BIN" --version))."
echo "Virtual environment dan dependency akan dipasang otomatis saat"
echo "pertama kali menjalankan: bash scripts/run_linux.sh"
