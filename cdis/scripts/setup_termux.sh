#!/data/data/com.termux/files/usr/bin/bash
# Sets up CDIS to run inside Termux on Android.
# Usage: bash scripts/setup_termux.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDIS_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> Updating Termux packages"
pkg update -y
pkg upgrade -y

echo "==> Installing python and git"
pkg install -y python git

echo "==> Allowing access to phone storage (needed to scan backups under /sdcard)"
termux-setup-storage || echo "termux-setup-storage not available, skip (install termux-api if you need it)"

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing backend dependencies"
pip install -r "$CDIS_ROOT/backend/requirements.txt"

echo
echo "Setup complete."
echo "Start the backend with: bash scripts/run_termux.sh"
echo "Then in another Termux session use the CLI: python cli/cdis.py health"
echo
echo "Optional - mobile scanning support (mvt-android works in Termux, mvt-ios does not):"
echo "  pip install -r backend/requirements-mvt.txt"
