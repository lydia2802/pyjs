#!/usr/bin/env python3
"""CDIS backend: Flask API + static file server.

Runs unmodified on Windows (python app.py) and on Android via Termux
(python app.py) - all configuration comes from config.py / environment
variables, there are no platform-specific paths in this file.
"""
import os
import sys

# Allow `from config import ...` / `from modules... import ...` to work
# regardless of the directory this script was launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from config import DEBUG, HOST, PORT, STATIC_DIR
from modules.database import Database
from modules.mvt_scanner import MVTScanner
from modules.sync_engine import SyncEngine

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

db = Database()
sync = SyncEngine()
scanner = MVTScanner()

# ========== API ROUTES ==========


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "mvt_available": scanner.mvt_available,
        "mvt_ios_available": scanner.mvt_ios_available,
        "mvt_android_available": scanner.mvt_android_available,
        "kev_count": len(db.get_all()),
    })


@app.route("/api/kev", methods=["GET"])
def get_all_kev():
    return jsonify(db.get_all())


@app.route("/api/kev/search", methods=["GET"])
def search_kev():
    keyword = request.args.get("q", "")
    return jsonify(db.search(keyword))


@app.route("/api/kev/cve/<cve_id>", methods=["GET"])
def get_cve(cve_id):
    results = db.get_by_cve(cve_id)
    if not results:
        return jsonify({"error": "Not found"}), 404
    return jsonify(results[0])


@app.route("/api/sync", methods=["POST"])
def sync_data():
    result = sync.sync()
    if result["status"] == "success":
        db.load()  # Reload database setelah sync
    return jsonify(result)


@app.route("/api/scan/ios", methods=["POST"])
def scan_ios():
    data = request.get_json(silent=True) or {}
    backup_path = data.get("backup_path")
    if not backup_path or not os.path.exists(backup_path):
        return jsonify({"status": "error", "message": "Backup path tidak valid"}), 400
    return jsonify(scanner.scan_ios(backup_path))


@app.route("/api/scan/android", methods=["POST"])
def scan_android():
    data = request.get_json(silent=True) or {}
    backup_path = data.get("backup_path")
    if not backup_path or not os.path.exists(backup_path):
        return jsonify({"status": "error", "message": "Backup path tidak valid"}), 400
    return jsonify(scanner.scan_android(backup_path))


# ========== STATIC FILES ==========


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


if __name__ == "__main__":
    print(f"CDIS Backend running at http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
