from __future__ import annotations

import json
from pathlib import Path

from analyzer.analyzers import build_full_report

INPUT_DIR = Path(__file__).resolve().parent / "input"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "ringkasan_data.json"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_full_report(INPUT_DIR)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    print(f"Report written to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
