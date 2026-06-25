from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzers import build_full_report
from .exporters import print_console_report, write_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="attck-kev-analyzer",
        description="Analisis file ATT&CK (Pegasus) dan KEV, lalu hasilkan laporan JSON.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input"),
        help="Folder berisi file ATT&CK/KEV (default: ./input)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/report.json"),
        help="Path file laporan JSON yang dihasilkan (default: ./output/report.json)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Jangan tampilkan ringkasan ke console.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = build_full_report(args.input_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    write_json_report(report, args.output)

    if not args.quiet:
        print_console_report(report, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
