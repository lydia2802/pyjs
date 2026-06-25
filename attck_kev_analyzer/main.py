from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzers import build_full_report
from .exporters import print_console_report, write_json_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisis file ATT&CK (Pegasus) dan KEV dari sebuah folder input."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder yang berisi file-file ATT&CK / KEV yang akan dianalisis.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("report.json"),
        help="Path file JSON output (default: report.json).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        report = build_full_report(args.input_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    write_json_report(report, args.output)
    print_console_report(report, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
