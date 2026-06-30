#!/usr/bin/env python3
"""CDIS CLI - Cyber Defense Intelligence System.

Talks to the local (or remote) CDIS backend over HTTP, so it works the
same way whether the backend is running on the same Windows machine or
inside Termux on an Android phone. Point it at a different host with the
CDIS_API_URL environment variable, e.g.:

    CDIS_API_URL=http://192.168.1.20:5000/api python cli/cdis.py health
"""
import argparse
import json
import os
import sys

import requests

API_BASE = os.environ.get("CDIS_API_URL", "http://localhost:5000/api")


def check_backend():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False


def print_kev_rows(items, total=None):
    for item in items:
        print(f"{item.get('cveID', 'N/A')} | {item.get('vulnerabilityName', 'N/A')[:60]} | {item.get('vendorProject', 'N/A')}")
    if total is not None:
        print(f"\n{len(items)} of {total} shown")


def build_parser():
    parser = argparse.ArgumentParser(description="CDIS CLI - Cyber Defense Intelligence System")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("health", help="Cek status backend")
    subparsers.add_parser("version", help="Versi backend")
    subparsers.add_parser("stats", help="Statistik katalog KEV")
    subparsers.add_parser("sync", help="Sync data KEV dari CISA")

    list_parser = subparsers.add_parser("list", help="List KEV (urut terbaru)")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument("--offset", type=int, default=0)

    search_parser = subparsers.add_parser("search", help="Cari KEV")
    search_parser.add_argument("keyword", help="Kata kunci pencarian")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--offset", type=int, default=0)

    cve_parser = subparsers.add_parser("cve", help="Detail CVE")
    cve_parser.add_argument("cve_id", help="Contoh: CVE-2021-44228")

    scan_parser = subparsers.add_parser("scan", help="Scan backup mobile dengan MVT")
    scan_parser.add_argument("platform", choices=["ios", "android"])
    scan_parser.add_argument("backup_path", help="Path ke folder/file backup")

    subparsers.add_parser("scans", help="Riwayat scan terakhir")

    export_parser = subparsers.add_parser("export", help="Export katalog KEV ke file")
    export_parser.add_argument("output_path", help="Path file tujuan, mis. kev.json atau kev.csv")
    export_parser.add_argument("--format", choices=["json", "csv"], help="Default ditebak dari ekstensi file")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not check_backend():
        print(f"Backend tidak berjalan di {API_BASE}")
        print("Jalankan dulu: python run.py (atau scripts/run_termux.sh / scripts/run_windows.bat)")
        sys.exit(1)

    try:
        if args.command == "health":
            r = requests.get(f"{API_BASE}/health", timeout=10)
            print(json.dumps(r.json(), indent=2))

        elif args.command == "version":
            r = requests.get(f"{API_BASE}/version", timeout=10)
            print(json.dumps(r.json(), indent=2))

        elif args.command == "stats":
            r = requests.get(f"{API_BASE}/stats", timeout=10)
            print(json.dumps(r.json(), indent=2))

        elif args.command == "sync":
            print("Syncing data dari CISA...")
            r = requests.post(f"{API_BASE}/sync", timeout=60)
            print(json.dumps(r.json(), indent=2))

        elif args.command == "list":
            r = requests.get(f"{API_BASE}/kev", params={"limit": args.limit, "offset": args.offset}, timeout=10)
            data = r.json()
            print_kev_rows(data.get("items", []), data.get("total"))

        elif args.command == "search":
            r = requests.get(
                f"{API_BASE}/kev/search",
                params={"q": args.keyword, "limit": args.limit, "offset": args.offset},
                timeout=10,
            )
            data = r.json()
            print_kev_rows(data.get("items", []), data.get("total"))

        elif args.command == "cve":
            r = requests.get(f"{API_BASE}/kev/cve/{args.cve_id}", timeout=10)
            print(json.dumps(r.json(), indent=2))

        elif args.command == "scan":
            print(f"Scanning {args.platform} backup: {args.backup_path}")
            r = requests.post(
                f"{API_BASE}/scan/{args.platform}",
                json={"backup_path": args.backup_path},
                timeout=320,
            )
            print(json.dumps(r.json(), indent=2))

        elif args.command == "scans":
            r = requests.get(f"{API_BASE}/scans", timeout=10)
            for entry in r.json():
                print(f"#{entry['id']} {entry['platform']:7s} {entry['status']:8s} {entry['backup_path']}")

        elif args.command == "export":
            fmt = args.format or ("csv" if args.output_path.lower().endswith(".csv") else "json")
            r = requests.get(f"{API_BASE}/export", params={"format": fmt}, timeout=60)
            with open(args.output_path, "wb") as f:
                f.write(r.content)
            print(f"Tersimpan ke {args.output_path} ({len(r.content)} bytes)")

    except requests.exceptions.RequestException as e:
        print(f"Gagal menghubungi backend: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
