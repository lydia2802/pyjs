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

os.makedirs(DATA_DIR, exist_ok=True)

KEV_CSV_PATH = os.path.join(DATA_DIR, "known_exploited_vulnerabilities.csv")

# Flask config. 0.0.0.0 binds on every interface so the API is reachable
# both from "localhost" on the same machine (Windows) and from a browser
# on the same Wi-Fi network when running inside Termux on Android.
HOST = os.environ.get("CDIS_HOST", "0.0.0.0")
PORT = int(os.environ.get("CDIS_PORT", "5000"))
DEBUG = os.environ.get("CDIS_DEBUG", "false").lower() in ("1", "true", "yes")

# Output directory used by mvt when analyzing a backup.
SCAN_OUTPUT_DIR = os.environ.get("CDIS_SCAN_OUTPUT_DIR", os.path.join(DATA_DIR, "scan_output"))

KEV_JSON_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# Network timeouts (seconds). Mobile data / hotel wifi can be slow, so the
# sync timeout is generous.
SYNC_TIMEOUT = int(os.environ.get("CDIS_SYNC_TIMEOUT", "30"))
SCAN_TIMEOUT = int(os.environ.get("CDIS_SCAN_TIMEOUT", "300"))
