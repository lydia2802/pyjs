"""
cli.py
======

Antarmuka command-line (CLI) untuk paket attck_kev_analyzer.

Cara pakai:

    # Tanpa instalasi, dijalankan langsung dari folder proyek:
    python -m attck_kev_analyzer --input-dir ./input --output ./output/report.json

    # Setelah `pip install -e .`, tersedia perintah pendek:
    attck-kev-analyzer --input-dir ./input --output ./output/report.json

Argumen yang didukung:
    --input-dir   Folder berisi file ATT&CK/KEV mentah (default: ./input)
    --output      Lokasi file laporan JSON hasil analisis (default: ./output/report.json)
    --quiet       Tidak menampilkan ringkasan ke console, hanya menulis file JSON
    --verbose     Menampilkan log proses secara lebih detail (debug)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .analyzers import build_full_report
from .exporters import print_console_report, write_json_report

logger = logging.getLogger("attck_kev_analyzer")


def build_parser() -> argparse.ArgumentParser:
    """Membuat dan mengonfigurasi parser argumen command-line."""
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
        help="Jangan tampilkan ringkasan ke console, hanya tulis file JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Tampilkan log proses secara lebih detail (untuk debugging).",
    )
    return parser


def configure_logging(verbose: bool) -> None:
    """Mengatur level dan format logging berdasarkan flag --verbose."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    """
    Entry point utama CLI. Mengembalikan exit code:
        0 -> sukses
        1 -> gagal (error sudah ditampilkan ke stderr/log)
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    logger.debug("Folder input  : %s", args.input_dir)
    logger.debug("File output   : %s", args.output)

    try:
        logger.info("Membaca dan menganalisis file dari folder: %s", args.input_dir)
        report = build_full_report(args.input_dir)
    except (FileNotFoundError, NotADirectoryError, ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Menulis laporan JSON ke: %s", args.output)
    write_json_report(report, args.output)

    if not args.quiet:
        print_console_report(report, args.output)

    logger.info("Selesai. Laporan tersimpan di '%s'.", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
