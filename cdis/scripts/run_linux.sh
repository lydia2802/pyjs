#!/usr/bin/env bash
# Starts CDIS on Linux/macOS (auto venv + deps + browser via run.py).
# Usage: bash scripts/run_linux.sh [run.py args...]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$CDIS_ROOT"
exec "$PYTHON_BIN" run.py "$@"
