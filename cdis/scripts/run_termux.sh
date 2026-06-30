#!/data/data/com.termux/files/usr/bin/bash
# Starts the CDIS backend inside Termux on Android.
# Usage: bash scripts/run_termux.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$CDIS_ROOT/backend"
exec python app.py
