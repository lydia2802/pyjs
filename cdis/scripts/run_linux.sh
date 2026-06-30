#!/usr/bin/env bash
# Starts the CDIS backend on Linux/macOS.
# Usage: bash scripts/run_linux.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -x "$CDIS_ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$CDIS_ROOT/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

cd "$CDIS_ROOT/backend"
exec "$PYTHON_BIN" app.py
