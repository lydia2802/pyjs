#!/usr/bin/env python3
import csv
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, abort

BASE_DIR = Path(__file__).resolve().parent
CSV_FILENAME = BASE_DIR / "known_exploited_vulnerabilities.csv"
OUTPUT_DIR = BASE_DIR / "output"
DB_PATH = OUTPUT_DIR / "kev.sqlite3"
EXPORT_JSON_PATH = OUTPUT_DIR / "kev_export.json"
EXPORT_CSV_PATH = OUTPUT_DIR / "kev_export.csv"
LOG_PATH = OUTPUT_DIR / "app.log"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

FIELDNAMES = [
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

DATE_FIELDS = {"dateAdded", "dueDate"}


def parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    if len(value) == 4 and value.isdigit():
        return f"{value}-01-01"

    return None


def split_cwes(value: Optional[str]) -> List[str]:
    if not value:
        return []
    raw = str(value).replace(";", ",").split(",")
    return [x.strip() for x in raw if x.strip()]


def clean_text(value: Optional[str]) -> str:
    return str(value).strip() if value is not None else ""


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    item = {k: clean_text(row.get(k, "")) for k in FIELDNAMES}
    for k in DATE_FIELDS:
        item[k] = parse_date(item.get(k))
    item["cwes"] = split_cwes(item.get("cwes"))
    if item.get("shortDescription"):
        item["shortDescription"] = item["shortDescription"][:2000]
    if item.get("notes"):
        item["notes"] = item["notes"][:5000]
    return item


def read_csv_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            try:
                rows.append(normalize_row(row))
            except Exception as exc:
                logger.exception("row %s failed: %s", idx, exc)

    logger.info("loaded %s rows", len(rows))
    return rows


def top_counts(data: List[Dict[str, Any]], key: str, limit: int = 10) -> List[Tuple[str, int]]:
    counts: Dict[str, int] = {}
    for row in data:
        val = clean_text(row.get(key)) or "Unknown"
        counts[val] = counts.get(val, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]


def in_range(date_str: Optional[str], start: Optional[str], end: Optional[str]) -> bool:
    if not date_str:
        return False
    try:
        d = datetime.fromisoformat(date_str).date()
    except ValueError:
        return False

    if start:
        s = datetime.fromisoformat(start).date()
        if d < s:
            return False
    if end:
        e = datetime.fromisoformat(end).date()
        if d > e:
            return False

    return True


def filter_data(
    data: List[Dict[str, Any]],
    vendor: Optional[str] = None,
    product: Optional[str] = None,
    cwe: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    ransomware: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    results = data

    if vendor:
        results = [
            r for r in results
            if clean_text(r.get("vendorProject")).lower() == vendor.lower()
        ]
    if product:
        results = [
            r for r in results
            if product.lower() in clean_text(r.get("product")).lower()
        ]
    if cwe:
        results = [
            r for r in results
            if any(cwe.lower() == x.lower() for x in r.get("cwes", []))
        ]
    if start or end:
        results = [r for r in results if in_range(r.get("dateAdded"), start, end)]
    if ransomware:
        results = [
            r for r in results
            if clean_text(r.get("knownRansomwareCampaignUse")).lower() == ransomware.lower()
        ]
    if search:
        q = search.lower()
        results = [r for r in results if q in json.dumps(r, ensure_ascii=False).lower()]

    return results


def summary_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total": len(data),
        "missing_dateAdded": sum(1 for r in data if not r.get("dateAdded")),
        "missing_dueDate": sum(1 for r in data if not r.get("dueDate")),
        "top_vendors": top_counts(data, "vendorProject", 10),
        "top_products": top_counts(data, "product", 10),
        "top_cwes": top_counts(
            [{"cwes": cwe} for row in data for cwe in row.get("cwes", [])],
            "cwes",
            10,
        ),
    }


def export_json(data: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("exported json: %s", out_path)


def export_csv(data: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in data:
            out = dict(row)
            out["cwes"] = ", ".join(out.get("cwes", []))
            writer.writerow(out)
    logger.info("exported csv: %s", out_path)


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
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
        )
        """
    )
    conn.commit()
    return conn


def upsert_db(conn: sqlite3.Connection, data: List[Dict[str, Any]]) -> None:
    conn.execute("DELETE FROM kev")
    conn.executemany(
        """
        INSERT OR REPLACE INTO kev
        (cveID, vendorProject, product, vulnerabilityName, dateAdded, shortDescription,
         requiredAction, dueDate, knownRansomwareCampaignUse, notes, cwes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r.get("cveID"),
                r.get("vendorProject"),
                r.get("product"),
                r.get("vulnerabilityName"),
                r.get("dateAdded"),
                r.get("shortDescription"),
                r.get("requiredAction"),
                r.get("dueDate"),
                r.get("knownRansomwareCampaignUse"),
                r.get("notes"),
                ", ".join(r.get("cwes", [])),
            )
            for r in data
        ],
    )
    conn.commit()


def query_db(conn: sqlite3.Connection, where: str = "", params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM kev"
    if where:
        sql += " WHERE " + where
    cur = conn.execute(sql, params)
    rows = []
    for row in cur.fetchall():
        item = dict(row)
        item["cwes"] = split_cwes(item.get("cwes"))
        rows.append(item)
    return rows


def create_app(data_store: List[Dict[str, Any]], conn: sqlite3.Connection) -> Flask:
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "total": len(data_store)})

    @app.route("/summary")
    def summary():
        return jsonify(summary_stats(data_store))

    @app.route("/cves")
    def cves():
        vendor = request.args.get("vendor")
        product = request.args.get("product")
        cwe = request.args.get("cwe")
        start = request.args.get("start")
        end = request.args.get("end")
        ransomware = request.args.get("ransomware")
        search = request.args.get("search")
        limit = int(request.args.get("limit") or 0)
        offset = int(request.args.get("offset") or 0)
        source = request.args.get("source", "memory")

        if source == "db":
            results = query_db(conn)
            results = filter_data(results, vendor, product, cwe, start, end, ransomware, search)
        else:
            results = filter_data(data_store, vendor, product, cwe, start, end, ransomware, search)

        total = len(results)
        if offset:
            results = results[offset:]
        if limit:
            results = results[:limit]

        return jsonify({"count": len(results), "total": total, "items": results})

    @app.route("/cves/<cve_id>")
    def cve_detail(cve_id: str):
        for row in data_store:
            if clean_text(row.get("cveID")).lower() == cve_id.lower():
                return jsonify(row)
        abort(404, description="CVE not found")

    @app.route("/export", methods=["POST"])
    def export_route():
        payload = request.get_json(force=True, silent=True) or {}
        filters = payload.get("filters", {})
        out_json = Path(payload.get("json_out", str(EXPORT_JSON_PATH)))
        out_csv = Path(payload.get("csv_out", str(EXPORT_CSV_PATH)))

        results = filter_data(
            data_store,
            vendor=filters.get("vendor"),
            product=filters.get("product"),
            cwe=filters.get("cwe"),
            start=filters.get("start"),
            end=filters.get("end"),
            ransomware=filters.get("ransomware"),
            search=filters.get("search"),
        )
        export_json(results, out_json)
        export_csv(results, out_csv)

        return jsonify({
            "status": "ok",
            "count": len(results),
            "json_out": str(out_json),
            "csv_out": str(out_csv),
        })

    @app.route("/db/reload", methods=["POST"])
    def db_reload():
        upsert_db(conn, data_store)
        return jsonify({"status": "ok", "db": str(DB_PATH), "count": len(data_store)})

    @app.route("/db/query")
    def db_query():
        vendor = request.args.get("vendor")
        cwe = request.args.get("cwe")
        where = []
        params: List[Any] = []

        if vendor:
            where.append("lower(vendorProject) = lower(?)")
            params.append(vendor)
        if cwe:
            where.append("lower(cwes) LIKE ?")
            params.append(f"%{cwe.lower()}%")

        sql_where = " AND ".join(where)
        rows = query_db(conn, sql_where, tuple(params))
        return jsonify({"count": len(rows), "items": rows})

    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": str(err)}), 404

    @app.errorhandler(500)
    def server_error(err):
        return jsonify({"error": "internal server error"}), 500

    return app


def write_requirements():
    req = BASE_DIR / "requirements.txt"
    req.write_text("Flask>=2.3\n", encoding="utf-8")
    logger.info("wrote %s", req)


def write_dockerfile():
    dockerfile = BASE_DIR / "Dockerfile"
    dockerfile.write_text(
        """FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/app.py
COPY known_exploited_vulnerabilities.csv /app/known_exploited_vulnerabilities.csv
RUN pip install --no-cache-dir "Flask>=2.3"
EXPOSE 5000
CMD ["python", "app.py", "--serve", "--host", "0.0.0.0", "--port", "5000"]
""",
        encoding="utf-8",
    )
    logger.info("wrote %s", dockerfile)


def write_compose():
    compose = BASE_DIR / "docker-compose.yml"
    compose.write_text(
        """services:
  kev-app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./:/app
""",
        encoding="utf-8",
    )
    logger.info("wrote %s", compose)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KEV app: CSV processor + API + SQLite + export tools")
    parser.add_argument("--csv", default=str(CSV_FILENAME))
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--export-json", default=None)
    parser.add_argument("--export-csv", default=None)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--db-init", action="store_true")
    parser.add_argument("--make-docker", action="store_true")
    parser.add_argument("--make-requirements", action="store_true")
    args = parser.parse_args()

    data = read_csv_file(Path(args.csv))

    if args.summary:
        print(json.dumps(summary_stats(data), indent=2, ensure_ascii=False))

    if args.export_json:
        export_json(data, Path(args.export_json))
    if args.export_csv:
        export_csv(data, Path(args.export_csv))

    conn = init_db(DB_PATH)
    upsert_db(conn, data)

    if args.db_init:
        print(json.dumps({"status": "ok", "db": str(DB_PATH), "rows": len(data)}, indent=2, ensure_ascii=False))

    if args.make_requirements:
        write_requirements()
    if args.make_docker:
        write_dockerfile()
        write_compose()

    if args.serve:
        app = create_app(data, conn)
        logger.info("serving on http://%s:%s", args.host, args.port)
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
