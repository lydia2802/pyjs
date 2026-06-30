#!/usr/bin/env python3
"""CDIS backend: Flask API + static file server.

Runs unmodified on Windows (python app.py), inside Termux on Android, and
on Linux/macOS - all configuration comes from config.py / environment
variables, there are no platform-specific paths in this file. Prefer
`python run.py` from the project root for a one-command start (auto venv
+ dependency install + browser launch); this file can also be run
directly once dependencies are installed.
"""
import csv
import io
import json
import logging
import logging.handlers
import os
import socket
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, Response, jsonify, request, send_from_directory

from config import (
    AUTO_SYNC_ON_EMPTY,
    CORS_ORIGINS,
    DEBUG,
    DEFAULT_PAGE_SIZE,
    HOST,
    LOG_FILE,
    MAX_PAGE_SIZE,
    PORT,
    PORT_FALLBACK_ATTEMPTS,
    STATIC_DIR,
)
from modules.database import KEV_COLUMNS, Database
from modules.mvt_scanner import MVTScanner
from modules.sync_engine import SyncEngine

VERSION = "1.0.0"

# ---------- logging ----------
logger = logging.getLogger("cdis")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logger.addHandler(_console)
try:
    _file = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    _file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_file)
except OSError as e:
    logger.warning("Could not open log file %s: %s", LOG_FILE, e)

# ---------- app + dependencies ----------
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")

if CORS_ORIGINS == "*":
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        logger.warning("flask_cors not installed, CORS disabled")
else:
    try:
        from flask_cors import CORS
        CORS(app, origins=[o.strip() for o in CORS_ORIGINS.split(",") if o.strip()])
    except ImportError:
        logger.warning("flask_cors not installed, CORS disabled")

db = Database()
sync = SyncEngine(db)
scanner = MVTScanner()


# ---------- helpers ----------

def _pagination_params():
    try:
        limit = int(request.args.get("limit", DEFAULT_PAGE_SIZE))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return None, None, jsonify({"error": "limit dan offset harus berupa angka"}), 400
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    offset = max(0, offset)
    return limit, offset, None, None


# ---------- API ROUTES ----------


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "mvt_available": scanner.mvt_available,
        "mvt_ios_available": scanner.mvt_ios_available,
        "mvt_android_available": scanner.mvt_android_available,
        "kev_count": db.count(),
        "last_sync_at": db.get_meta("last_sync_at"),
    })


@app.route("/api/version", methods=["GET"])
def version():
    return jsonify({"version": VERSION, "python": sys.version.split()[0]})


@app.route("/api/kev", methods=["GET"])
def get_all_kev():
    limit, offset, err, code = _pagination_params()
    if err:
        return err, code
    keyword = request.args.get("q", "")
    items, total = db.search(keyword, limit=limit, offset=offset) if keyword else db.get_all(limit=limit, offset=offset)
    return jsonify({"total": total, "count": len(items), "limit": limit, "offset": offset, "items": items})


@app.route("/api/kev/search", methods=["GET"])
def search_kev():
    limit, offset, err, code = _pagination_params()
    if err:
        return err, code
    keyword = request.args.get("q", "")
    items, total = db.search(keyword, limit=limit, offset=offset)
    return jsonify({"total": total, "count": len(items), "limit": limit, "offset": offset, "items": items})


@app.route("/api/kev/cve/<cve_id>", methods=["GET"])
def get_cve(cve_id):
    result = db.get_by_cve(cve_id)
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(db.stats())


@app.route("/api/sync", methods=["POST"])
def sync_data():
    result = sync.sync()
    status_code = 200 if result["status"] == "success" else 502
    return jsonify(result), status_code


@app.route("/api/scan/ios", methods=["POST"])
def scan_ios():
    data = request.get_json(silent=True) or {}
    backup_path = data.get("backup_path")
    if not backup_path or not os.path.exists(backup_path):
        return jsonify({"status": "error", "message": "Backup path tidak valid"}), 400
    result = scanner.scan_ios(backup_path)
    db.record_scan("ios", backup_path, result.get("status", "error"), result.get("message", ""))
    return jsonify(result)


@app.route("/api/scan/android", methods=["POST"])
def scan_android():
    data = request.get_json(silent=True) or {}
    backup_path = data.get("backup_path")
    if not backup_path or not os.path.exists(backup_path):
        return jsonify({"status": "error", "message": "Backup path tidak valid"}), 400
    result = scanner.scan_android(backup_path)
    db.record_scan("android", backup_path, result.get("status", "error"), result.get("message", ""))
    return jsonify(result)


@app.route("/api/scans", methods=["GET"])
def scan_history():
    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 200))
    except ValueError:
        return jsonify({"error": "limit harus berupa angka"}), 400
    return jsonify(db.list_scans(limit=limit))


@app.route("/api/export", methods=["GET"])
def export_data():
    fmt = request.args.get("format", "json").lower()
    rows = db.export_rows()

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=KEV_COLUMNS)
        writer.writeheader()
        for row in rows:
            r = dict(row)
            r["cwes"] = ",".join(r.get("cwes") or [])
            writer.writerow(r)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=cdis_kev_export.csv"},
        )

    return Response(
        json.dumps(rows, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=cdis_kev_export.json"},
    )


# ---------- error handlers (JSON for API, default Flask page for the rest) ----------


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return e.get_response()


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled error on %s", request.path)
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return e.get_response()


# ---------- STATIC FILES ----------


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


# ---------- startup helpers ----------


def _find_open_port(host, start_port, attempts):
    port = start_port
    for _ in range(attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host if host != "0.0.0.0" else "", port))
                return port
            except OSError:
                port += 1
    return None


def _maybe_auto_sync():
    if not AUTO_SYNC_ON_EMPTY:
        return
    if db.count() > 0:
        return

    def _run():
        logger.info("Database kosong, mencoba auto-sync awal dari CISA...")
        result = sync.sync()
        if result["status"] == "success":
            logger.info("Auto-sync berhasil: %d entri", result.get("count", 0))
        else:
            logger.warning("Auto-sync gagal (tidak masalah, bisa di-sync manual nanti): %s", result.get("message"))

    threading.Thread(target=_run, daemon=True).start()


def main():
    port = _find_open_port(HOST, PORT, PORT_FALLBACK_ATTEMPTS)
    if port is None:
        print(f"Tidak ada port kosong di sekitar {PORT} (sudah coba {PORT_FALLBACK_ATTEMPTS}x). "
              f"Set CDIS_PORT ke port lain.")
        sys.exit(1)
    if port != PORT:
        print(f"Port {PORT} sedang dipakai, menggunakan port {port} sebagai gantinya.")

    _maybe_auto_sync()

    display_host = "localhost" if HOST in ("0.0.0.0", "127.0.0.1") else HOST
    print(f"CDIS Backend v{VERSION} running at http://{display_host}:{port}")
    app.run(host=HOST, port=port, debug=DEBUG, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
