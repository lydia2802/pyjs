"""
attck_kev_analyzer
===================

Paket utilitas untuk membaca dan menganalisis data MITRE ATT&CK
(khususnya layer Pegasus for Android/iOS) serta data KEV (Known
Exploited Vulnerabilities) dari CISA.

Struktur paket:
    loaders.py    -> membaca file mentah (JSON, CSV, XLSX) dari disk
    analyzers.py  -> mengolah data mentah menjadi ringkasan/statistik
    exporters.py  -> menulis hasil ke file JSON atau menampilkannya ke console
    cli.py        -> antarmuka command-line (entry point)

Contoh pemakaian sebagai library:

    from pathlib import Path
    from attck_kev_analyzer import build_full_report, write_json_report

    report = build_full_report(Path("./input"))
    write_json_report(report, Path("./output/report.json"))
"""

from .analyzers import build_full_report
from .exporters import print_console_report, write_json_report
from .loaders import list_input_files, load_csv_rows, load_json, load_xlsx_rows

__version__ = "1.0.0"

__all__ = [
    "build_full_report",
    "print_console_report",
    "write_json_report",
    "list_input_files",
    "load_csv_rows",
    "load_json",
    "load_xlsx_rows",
]
