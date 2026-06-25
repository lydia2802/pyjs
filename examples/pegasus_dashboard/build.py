"""Builds a static, self-contained site: dashboard.main.js, dashboard.main.css and index.html.

Run after generate_report.py. The resulting dist/ folder can be served by any
static file server, including the Node.js one in server.js.
"""
import json
from pathlib import Path

from pyjs.transpiler import bundle
from pyjs.server import page

import dashboard
from report_args import build_main_args

ROOT = Path(__file__).resolve().parent
REPORT_FILE = ROOT / "output" / "ringkasan_data.json"
DIST_DIR = ROOT / "dist"


def main() -> int:
    with REPORT_FILE.open("r", encoding="utf-8") as file:
        report = json.load(file)
    args = build_main_args(report)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    js, css = bundle(dashboard.main, include_main=True)
    (DIST_DIR / "dashboard.main.js").write_text(js, encoding="utf-8")
    (DIST_DIR / "dashboard.main.css").write_text(css, encoding="utf-8")

    html = page(dashboard.main(*args), "dashboard.main.js", "dashboard.main.css", "text/javascript")
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")

    print(f"Static site written to {DIST_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
