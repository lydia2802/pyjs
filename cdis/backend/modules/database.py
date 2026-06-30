import csv
import json
import os
import sqlite3
import time
from contextlib import closing

from config import DB_PATH, KEV_CSV_PATH

# Columns persisted from the CISA KEV catalog. `cwes` is a JSON-encoded
# list because SQLite has no native array type.
KEV_COLUMNS = [
    "cveID",
    "vendorProject",
    "product",
    "vulnerabilityName",
    "dateAdded",
    "shortDescription",
    "requiredAction",
    "dueDate",
    "knownRansomwareCampaignUse",
    "notes",
    "cwes",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS kev (
    cveID TEXT PRIMARY KEY,
    vendorProject TEXT,
    product TEXT,
    vulnerabilityName TEXT,
    dateAdded TEXT,
    shortDescription TEXT,
    requiredAction TEXT,
    dueDate TEXT,
    knownRansomwareCampaignUse TEXT,
    notes TEXT,
    cwes TEXT
);
CREATE INDEX IF NOT EXISTS idx_kev_vendor ON kev(vendorProject);
CREATE INDEX IF NOT EXISTS idx_kev_date_added ON kev(dateAdded);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    backup_path TEXT,
    status TEXT NOT NULL,
    message TEXT,
    created_at TEXT NOT NULL
);
"""


def _row_to_dict(row):
    d = dict(row)
    if d.get("cwes"):
        try:
            d["cwes"] = json.loads(d["cwes"])
        except (TypeError, ValueError):
            d["cwes"] = []
    else:
        d["cwes"] = []
    return d


class Database:
    """SQLite-backed store for the CISA KEV catalog.

    SQLite is part of the Python standard library, so this adds zero new
    dependencies and behaves identically on Termux, Windows and
    Linux/macOS. A fresh connection is opened per call instead of being
    held open for the process lifetime - at this data size (a few
    thousand rows, single local user) the overhead is negligible and it
    sidesteps any cross-thread sqlite3 connection-sharing pitfalls when
    Flask serves the CLI and the web dashboard concurrently.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_schema()
        self._migrate_legacy_csv()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self):
        with closing(self._connect()) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def _migrate_legacy_csv(self):
        """One-time import of data/known_exploited_vulnerabilities.csv from
        the previous CSV-only version of CDIS, so upgrading doesn't lose
        data that was already synced."""
        if self.count() > 0:
            return
        if not os.path.exists(KEV_CSV_PATH):
            return
        try:
            with open(KEV_CSV_PATH, "r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            if rows:
                self.replace_all(rows)
        except (OSError, csv.Error):
            pass

    # ---------- writes ----------

    def replace_all(self, rows):
        """Atomically replace the whole KEV table with `rows` (list of
        dicts as returned by the CISA JSON feed). Using a single
        transaction means readers never see a half-empty table."""
        normalized = []
        for row in rows:
            cwes = row.get("cwes") or []
            if isinstance(cwes, str):
                cwes_json = cwes
            else:
                cwes_json = json.dumps(cwes)
            normalized.append(
                tuple(
                    row.get(col, "") if col != "cwes" else cwes_json
                    for col in KEV_COLUMNS
                )
            )

        placeholders = ", ".join("?" for _ in KEV_COLUMNS)
        columns = ", ".join(KEV_COLUMNS)

        with closing(self._connect()) as conn:
            with conn:
                conn.execute("DELETE FROM kev")
                conn.executemany(
                    f"INSERT INTO kev ({columns}) VALUES ({placeholders})",
                    normalized,
                )
        self.set_meta("last_sync_at", str(int(time.time())))
        self.set_meta("last_sync_count", str(len(normalized)))

    def import_csv(self, csv_path):
        """Load a hand-edited / manually downloaded CSV into the database."""
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.replace_all(rows)
        return len(rows)

    def set_meta(self, key, value):
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    "INSERT INTO meta (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, str(value)),
                )

    def get_meta(self, key, default=None):
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def record_scan(self, platform, backup_path, status, message=""):
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    "INSERT INTO scans (platform, backup_path, status, message, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (platform, backup_path, status, message[:2000], str(int(time.time()))),
                )

    # ---------- reads ----------

    def count(self):
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM kev").fetchone()
            return row["n"] if row else 0

    def get_all(self, limit=50, offset=0):
        with closing(self._connect()) as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM kev").fetchone()["n"]
            rows = conn.execute(
                "SELECT * FROM kev ORDER BY dateAdded DESC, cveID DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [_row_to_dict(r) for r in rows], total

    def search(self, keyword, limit=50, offset=0):
        keyword = (keyword or "").strip()
        if not keyword:
            return self.get_all(limit=limit, offset=offset)

        like = f"%{keyword}%"
        where = (
            "cveID LIKE ? OR vendorProject LIKE ? OR product LIKE ? OR "
            "vulnerabilityName LIKE ? OR shortDescription LIKE ? OR notes LIKE ?"
        )
        params = [like] * 6

        with closing(self._connect()) as conn:
            total = conn.execute(f"SELECT COUNT(*) AS n FROM kev WHERE {where}", params).fetchone()["n"]
            rows = conn.execute(
                f"SELECT * FROM kev WHERE {where} ORDER BY dateAdded DESC, cveID DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            return [_row_to_dict(r) for r in rows], total

    def get_by_cve(self, cve_id):
        cve_id = (cve_id or "").upper()
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM kev WHERE upper(cveID) = ?", (cve_id,)).fetchone()
            return _row_to_dict(row) if row else None

    def stats(self):
        with closing(self._connect()) as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM kev").fetchone()["n"]
            ransomware = conn.execute(
                "SELECT COUNT(*) AS n FROM kev WHERE lower(knownRansomwareCampaignUse) = 'known'"
            ).fetchone()["n"]
            latest = conn.execute("SELECT MAX(dateAdded) AS d FROM kev").fetchone()["d"]
            top_vendors = conn.execute(
                "SELECT vendorProject AS vendor, COUNT(*) AS n FROM kev "
                "WHERE vendorProject != '' GROUP BY vendorProject ORDER BY n DESC LIMIT 10"
            ).fetchall()
            return {
                "total": total,
                "ransomware_count": ransomware,
                "latest_date_added": latest,
                "top_vendors": [{"vendor": r["vendor"], "count": r["n"]} for r in top_vendors],
                "last_sync_at": self.get_meta("last_sync_at"),
                "last_sync_count": self.get_meta("last_sync_count"),
            }

    def list_scans(self, limit=20):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def export_rows(self):
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM kev ORDER BY dateAdded DESC, cveID DESC").fetchall()
            return [_row_to_dict(r) for r in rows]
