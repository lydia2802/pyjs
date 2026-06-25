# attck-kev-analyzer

Utility untuk membaca dan menganalisis file ATT&CK (Pegasus Android/iOS) dan
data KEV (Known Exploited Vulnerabilities) CISA, lalu menghasilkan laporan
JSON ringkas.

## Setup

```bash
cd attck_kev_analyzer
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## File input yang dibutuhkan

Letakkan file berikut di dalam satu folder input (default `./input`):

- `pegasus_for_android_(s0316).json`
- `pegasus_for_ios_(s0289).json`
- `S0316-mobile-layer.json`
- `S0289-mobile-layer.json`
- `changelog.json`
- `known_exploited_vulnerabilities.csv`
- `pegasus_for_android_(s0316).xlsx`

## Menjalankan

```bash
attck-kev-analyzer --input-dir ./input --output ./output/report.json
```

Atau tanpa instalasi:

```bash
python -m attck_kev_analyzer --input-dir ./input --output ./output/report.json
```

Opsi:

- `--input-dir`: folder berisi file ATT&CK/KEV (default `./input`)
- `--output`: path file laporan JSON (default `./output/report.json`)
- `--quiet`: hanya tulis JSON, tanpa ringkasan ke console

## Struktur paket

- `attck_kev_analyzer/loaders.py` — membaca file JSON, CSV, dan XLSX
- `attck_kev_analyzer/analyzers.py` — meringkas & membandingkan data
- `attck_kev_analyzer/exporters.py` — menulis laporan JSON & ringkasan console
- `attck_kev_analyzer/cli.py` — antarmuka command line
