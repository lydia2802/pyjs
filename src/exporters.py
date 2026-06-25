from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_report(report: dict[str, Any], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)


def print_console_report(report: dict[str, Any], output_file: Path) -> None:
    android = report["pegasus"]["android_full"]
    ios = report["pegasus"]["ios_full"]
    comparison = report["pegasus"]["comparison"]
    kev = report["kev"]

    print("=" * 72)
    print("RINGKASAN DATA ATT&CK / KEV")
    print("=" * 72)
    print(f"File output : {output_file}")
    print()

    print("[Pegasus Android]")
    print(f"- Nama                 : {android['name']}")
    print(f"- Total teknik         : {android['technique_count']}")
    print(f"- Teknik bersubteknik  : {android['subtechnique_count']}")
    print(f"- Platform             : {', '.join(android['platforms']) or '-'}")
    print()

    print("[Pegasus iOS]")
    print(f"- Nama                 : {ios['name']}")
    print(f"- Total teknik         : {ios['technique_count']}")
    print(f"- Teknik bersubteknik  : {ios['subtechnique_count']}")
    print(f"- Platform             : {', '.join(ios['platforms']) or '-'}")
    print()

    print("[Perbandingan Pegasus Android vs iOS]")
    print(f"- Teknik sama          : {comparison['shared_count']}")
    print(f"- Hanya Android        : {comparison['android_only_count']}")
    print(f"- Hanya iOS            : {comparison['ios_only_count']}")
    print()

    print("[Known Exploited Vulnerabilities]")
    print(f"- Jumlah record        : {kev['record_count']}")
    print(f"- Kolom                : {', '.join(kev['columns'])}")
    print()

    print("[Changelog]")
    for domain, detail in report["changelog"].items():
        if domain == "new-contributors":
            print(f"- {domain}: {detail['count']}")
        else:
            section_count = len(detail)
            print(f"- {domain}: {section_count} section")
    print("=" * 72)
