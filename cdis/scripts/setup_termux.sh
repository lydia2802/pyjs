#!/data/data/com.termux/files/usr/bin/bash
# Installs OS-level prerequisites for CDIS inside Termux on Android.
# Usage: bash scripts/setup_termux.sh
# (Python venv + pip dependencies are handled automatically by run.py,
# you don't need to run this again after the first time unless Termux
# itself was reinstalled.)
set -e

echo "==> Updating Termux packages"
pkg update -y
pkg upgrade -y

echo "==> Installing python and git"
pkg install -y python git

echo "==> Allowing access to phone storage (needed to scan backups under /sdcard)"
termux-setup-storage || echo "termux-setup-storage not available, skip (install termux-api if you need it)"

echo
echo "Setup complete."
echo "Start CDIS with: bash scripts/run_termux.sh"
echo
echo "Optional - mobile scanning support (mvt-android works in Termux, mvt-ios does not):"
echo "  venv/bin/pip install -r backend/requirements-mvt.txt"
