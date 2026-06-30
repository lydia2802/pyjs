"""Centralized configuration for CDIS backend.

Works unmodified on Windows, Linux, macOS and Android/Termux because all
paths are built with os.path / pathlib instead of hard-coded separators,
and every runtime knob can be overridden with an environment variable so
the same code runs in every environment without edits.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("CDIS_DATA_DIR", os.path.join(BASE_DIR, "data"))
STATIC_DIR = os.environ.get("CDIS_STATIC_DIR", os.path.join(BASE_DIR, "static"))
LOG_DIR = os.environ.get("CDIS_LOG_DIR", os.path.join(DATA_DIR, "logs"))

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Primary data store. SQLite is part of the Python standard library, so it
# adds no extra dependency and works identically on Termux, Windows and
# Linux/macOS - unlike a "real" database server it needs no install step.
DB_PATH = os.environ.get("CDIS_DB_PATH", os.path.join(DATA_DIR, "cdis.db"))

# Legacy CSV path, kept only as the default filename for the /api/export
# endpoint and for importing a hand-edited CSV via Database.import_csv().
KEV_CSV_PATH = os.environ.get("CDIS_CSV_PATH", os.path.join(DATA_DIR, "known_exploited_vulnerabilities.csv"))

LOG_FILE = os.path.join(LOG_DIR, "cdis.log")

# Flask config. 0.0.0.0 binds on every interface so the API is reachable
# both from "localhost" on the same machine (Windows) and from a browser
# on the same Wi-Fi network when running inside Termux on Android.
HOST = os.environ.get("CDIS_HOST", "0.0.0.0")
PORT = int(os.environ.get("CDIS_PORT", "5000"))
DEBUG = os.environ.get("CDIS_DEBUG", "false").lower() in ("1", "true", "yes")

# If the configured port is already taken, try the next N ports instead of
# crashing - very common on phones/PCs where something else is already
# bound to 5000.
PORT_FALLBACK_ATTEMPTS = int(os.environ.get("CDIS_PORT_FALLBACK_ATTEMPTS", "10"))

# Comma-separated list of allowed origins for CORS, or "*" for any origin
# (default - convenient for LAN/mobile use where the frontend may be
# opened from a different device on the same network).
CORS_ORIGINS = os.environ.get("CDIS_CORS_ORIGINS", "*")

# Automatically attempt one sync from CISA on startup if the local
# database is empty, so a fresh install shows real data without the user
# having to know to click "Sync" first. Always best-effort / non-blocking.
AUTO_SYNC_ON_EMPTY = os.environ.get("CDIS_AUTO_SYNC_ON_EMPTY", "true").lower() in ("1", "true", "yes")

# Output directory used by mvt when analyzing a backup.
SCAN_OUTPUT_DIR = os.environ.get("CDIS_SCAN_OUTPUT_DIR", os.path.join(DATA_DIR, "scan_output"))

KEV_JSON_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# Network timeouts (seconds) and retry policy. Mobile data / hotel wifi can
# be slow or flaky, so sync retries a few times with exponential backoff
# before giving up.
SYNC_TIMEOUT = int(os.environ.get("CDIS_SYNC_TIMEOUT", "30"))
SYNC_MAX_RETRIES = int(os.environ.get("CDIS_SYNC_MAX_RETRIES", "3"))
SYNC_RETRY_BACKOFF = float(os.environ.get("CDIS_SYNC_RETRY_BACKOFF", "2"))
SCAN_TIMEOUT = int(os.environ.get("CDIS_SCAN_TIMEOUT", "300"))

DEFAULT_PAGE_SIZE = int(os.environ.get("CDIS_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.environ.get("CDIS_MAX_PAGE_SIZE", "500"))
