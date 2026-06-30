#!/usr/bin/env bash
# Sets up CDIS on Linux/macOS.
# Usage: bash scripts/setup_linux.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Creating virtual environment"
"$PYTHON_BIN" -m venv "$CDIS_ROOT/venv"

echo "==> Installing backend dependencies"
"$CDIS_ROOT/venv/bin/pip" install --upgrade pip
"$CDIS_ROOT/venv/bin/pip" install -r "$CDIS_ROOT/backend/requirements.txt"

echo
echo "Setup complete."
echo "Start the backend with: bash scripts/run_linux.sh"
echo "Then use the CLI: venv/bin/python cli/cdis.py health"
