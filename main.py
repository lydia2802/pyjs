from __future__ import annotations

import argparse
from pathlib import Path

from src.analyzers import build_full_report
from src.exporters import print_console_report, write_json_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Membaca file ATT&CK / KEV lalu membuat ringkasan yang bisa dijalankan di Python."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input"),
        help="Folder tempat file JSON/CSV/XLSX berada. Default: ./input",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Folder hasil ringkasan. Default: ./output",
    )
    parser.add_argument(
        "--report-name",
        default="ringkasan_data.json",
        help="Nama file laporan JSON. Default: ringkasan_data.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    report = build_full_report(args.input_dir)
    output_file = args.output_dir / args.report_name
    write_json_report(report, output_file)
    print_console_report(report, output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
