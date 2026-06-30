#!/data/data/com.termux/files/usr/bin/bash
# Starts CDIS inside Termux on Android (auto venv + deps + browser via run.py).
# Usage: bash scripts/run_termux.sh [run.py args...]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$CDIS_ROOT"
exec python run.py "$@"
