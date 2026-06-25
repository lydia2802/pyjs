"""
analyzers.py
============

Modul ini bertanggung jawab untuk SEMUA proses analisis/ringkasan data
yang sudah dibaca oleh loaders.py. Tidak ada operasi baca file langsung
di sini KECUALI lewat fungsi-fungsi yang sudah disediakan loaders.py.

Data yang dianalisis:

1. Pegasus for Android (S0316) -> file JSON ATT&CK Navigator + layer-nya
2. Pegasus for iOS (S0289)     -> file JSON ATT&CK Navigator + layer-nya
3. Perbandingan teknik MITRE ATT&CK antara Android vs iOS
4. KEV (Known Exploited Vulnerabilities) dari CISA -> file CSV
5. changelog.json -> riwayat perubahan data MITRE ATT&CK
6. pegasus_for_android_(s0316).xlsx -> data tabular pendukung

Fungsi utama yang dipanggil dari luar modul ini adalah
`build_full_report()`, yang menggabungkan semua hasil analisis
menjadi satu laporan (dict) siap diekspor.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .loaders import list_input_files, load_csv_rows, load_json, load_xlsx_rows


# ---------------------------------------------------------------------------
# Nama-nama file input yang WAJIB ada di dalam folder input.
# Disusun sebagai konstanta agar mudah diubah/di-maintain di satu tempat.
# ---------------------------------------------------------------------------
PEGASUS_ANDROID_JSON = "pegasus_for_android_(s0316).json"
PEGASUS_IOS_JSON = "pegasus_for_ios_(s0289).json"
PEGASUS_ANDROID_LAYER = "S0316-mobile-layer.json"
PEGASUS_IOS_LAYER = "S0289-mobile-layer.json"
CHANGELOG_JSON = "changelog.json"
KEV_CSV = "known_exploited_vulnerabilities.csv"
ANDROID_XLSX = "pegasus_for_android_(s0316).xlsx"

REQUIRED_INPUT_FILES = {
    PEGASUS_ANDROID_JSON,
    PEGASUS_IOS_JSON,
    PEGASUS_ANDROID_LAYER,
    PEGASUS_IOS_LAYER,
    CHANGELOG_JSON,
    KEV_CSV,
    ANDROID_XLSX,
}


def summarize_pegasus_file(data: dict[str, Any], source_name: str) -> dict[str, Any]:
    """
    Meringkas satu file ATT&CK Navigator (format Pegasus Android/iOS)
    menjadi statistik singkat: jumlah teknik, jumlah sub-teknik,
    distribusi tactic, dan metadata umum (nama, deskripsi, platform).

    Parameter
    ---------
    data : dict[str, Any]
        Isi file JSON ATT&CK Navigator (hasil dari loaders.load_json()).
    source_name : str
        Nama file asal, dipakai sebagai label pada hasil ringkasan.

    Return
    ------
    dict[str, Any]
        Ringkasan statistik dari file tersebut.
    """
    techniques = data.get("techniques", [])

    # Ambil semua techniqueID yang valid (tidak kosong/None).
    technique_ids = [item.get("techniqueID") for item in techniques if item.get("techniqueID")]

    # Hitung jumlah teknik per tactic (mis. "collection", "exfiltration", dst).
    tactic_counts = Counter(item.get("tactic", "unknown") for item in techniques)

    # Hitung teknik yang punya komentar/anotasi tambahan dari analis.
    commented_items = sum(1 for item in techniques if item.get("comment"))

    # Sub-teknik MITRE ATT&CK selalu memiliki format "Txxxx.xxx" (mengandung titik).
    subtechniques = [
        item.get("techniqueID")
        for item in techniques
        if "." in str(item.get("techniqueID", ""))
    ]

    return {
        "source_file": source_name,
        "name": data.get("name"),
        "description": data.get("description"),
        "domain": data.get("domain"),
        "versions": data.get("versions", {}),
        "platforms": data.get("filters", {}).get("platforms", []),
        "technique_count": len(technique_ids),
        "commented_technique_count": commented_items,
        "subtechnique_count": len(subtechniques),
        "tactic_counts": dict(tactic_counts),
        "technique_ids": technique_ids,
    }


def compare_pegasus_sets(android_data: dict[str, Any], ios_data: dict[str, Any]) -> dict[str, Any]:
    """
    Membandingkan daftar techniqueID antara versi Android dan iOS,
    untuk melihat teknik mana yang dipakai bersama, dan mana yang
    eksklusif hanya pada satu platform saja.

    Parameter
    ---------
    android_data : dict[str, Any]
        Isi file JSON ATT&CK Navigator untuk Pegasus Android.
    ios_data : dict[str, Any]
        Isi file JSON ATT&CK Navigator untuk Pegasus iOS.

    Return
    ------
    dict[str, Any]
        Hasil perbandingan: teknik yang sama, hanya-Android, hanya-iOS,
        beserta jumlah masing-masing kategori.
    """
    android_ids = {
        item.get("techniqueID")
        for item in android_data.get("techniques", [])
        if item.get("techniqueID")
    }
    ios_ids = {
        item.get("techniqueID")
        for item in ios_data.get("techniques", [])
        if item.get("techniqueID")
    }

    shared = android_ids & ios_ids
    android_only = android_ids - ios_ids
    ios_only = ios_ids - android_ids

    return {
        "shared_techniques": sorted(shared),
        "android_only": sorted(android_only),
        "ios_only": sorted(ios_only),
        "shared_count": len(shared),
        "android_only_count": len(android_only),
        "ios_only_count": len(ios_only),
    }


def summarize_kev(rows: list[dict[str, str]]) -> dict[str, Any]:
    """
    Meringkas data KEV (Known Exploited Vulnerabilities) dari CISA:
    vendor/produk paling sering muncul, status penggunaan ransomware,
    dan beberapa contoh baris data mentah.

    Parameter
    ---------
    rows : list[dict[str, str]]
        Daftar baris data KEV, hasil dari loaders.load_csv_rows().

    Return
    ------
    dict[str, Any]
        Ringkasan statistik data KEV.
    """
    vendors = Counter(row.get("vendorProject", "Unknown") for row in rows)
    products = Counter(row.get("product", "Unknown") for row in rows)
    ransomware_use = Counter(row.get("knownRansomwareCampaignUse", "Unknown") for row in rows)

    return {
        "record_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "top_vendors": dict(vendors.most_common(10)),
        "top_products": dict(products.most_common(10)),
        "ransomware_usage_counts": dict(ransomware_use),
        "sample_records": rows[:5],
    }


def summarize_changelog(data: dict[str, Any]) -> dict[str, Any]:
    """
    Meringkas changelog.json MITRE ATT&CK. Struktur asli file ini
    berbeda-beda tergantung domain (mobile-attack, enterprise-attack,
    dst), sehingga fungsi ini menangani beberapa kemungkinan bentuk:

    - key "new-contributors"  -> berupa list nama kontributor baru.
    - key domain lain (dict)  -> berisi beberapa section (mis. "techniques",
      "groups", dst), masing-masing section berisi list perubahan
      (mis. "additions", "changes", "deprecations").
    - key dengan value bukan dict -> dicatat tipe datanya saja.

    Parameter
    ---------
    data : dict[str, Any]
        Isi file changelog.json (hasil dari loaders.load_json()).

    Return
    ------
    dict[str, Any]
        Ringkasan jumlah perubahan per domain/section.
    """
    summary: dict[str, Any] = {}

    for domain_name, domain_value in data.items():
        if domain_name == "new-contributors":
            summary[domain_name] = {
                "count": len(domain_value),
                "sample": domain_value[:10],
            }
            continue

        if not isinstance(domain_value, dict):
            summary[domain_name] = {"type": type(domain_value).__name__}
            continue

        domain_summary: dict[str, Any] = {}
        for section_name, section_value in domain_value.items():
            if isinstance(section_value, dict):
                domain_summary[section_name] = {
                    key: len(value) if isinstance(value, list) else 0
                    for key, value in section_value.items()
                }
        summary[domain_name] = domain_summary

    return summary


def summarize_xlsx(sheets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """
    Meringkas isi file Excel (.xlsx) per sheet: jumlah baris, daftar
    kolom, dan contoh beberapa baris pertama.

    Parameter
    ---------
    sheets : dict[str, list[dict[str, Any]]]
        Hasil dari loaders.load_xlsx_rows().

    Return
    ------
    dict[str, Any]
        Ringkasan jumlah sheet dan statistik per sheet.
    """
    return {
        "sheet_count": len(sheets),
        "sheets": {
            sheet_name: {
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
                "sample_rows": rows[:3],
            }
            for sheet_name, rows in sheets.items()
        },
    }


def build_full_report(input_dir: Path) -> dict[str, Any]:
    """
    Fungsi utama (entry point) modul analyzers.py.

    Langkah kerja:
    1. Validasi bahwa semua file wajib (REQUIRED_INPUT_FILES) tersedia
       di dalam folder input.
    2. Membaca seluruh file mentah lewat loaders.py.
    3. Menjalankan setiap fungsi summarize_*/compare_* untuk
       menghasilkan ringkasan masing-masing dataset.
    4. Menggabungkan semua ringkasan menjadi satu dict laporan akhir.

    Parameter
    ---------
    input_dir : Path
        Folder yang berisi seluruh file input mentah.

    Return
    ------
    dict[str, Any]
        Laporan lengkap, siap diekspor ke JSON atau ditampilkan
        ke console lewat exporters.py.

    Exception
    ---------
    FileNotFoundError
        Jika folder input tidak ada, atau ada file wajib yang belum
        lengkap di dalamnya.
    ValueError
        Jika salah satu file JSON/CSV tidak valid/rusak.
    RuntimeError
        Jika library 'openpyxl' belum terpasang untuk membaca file xlsx.
    """
    files = list_input_files(input_dir)
    file_names = {path.name for path in files}

    missing = sorted(REQUIRED_INPUT_FILES - file_names)
    if missing:
        raise FileNotFoundError(f"File wajib belum lengkap: {', '.join(missing)}")

    # --- Tahap 1: baca semua file mentah ---------------------------------
    android_json = load_json(input_dir / PEGASUS_ANDROID_JSON)
    ios_json = load_json(input_dir / PEGASUS_IOS_JSON)
    android_layer = load_json(input_dir / PEGASUS_ANDROID_LAYER)
    ios_layer = load_json(input_dir / PEGASUS_IOS_LAYER)
    kev_rows = load_csv_rows(input_dir / KEV_CSV)
    changelog = load_json(input_dir / CHANGELOG_JSON)
    xlsx_sheets = load_xlsx_rows(input_dir / ANDROID_XLSX)

    # --- Tahap 2: jalankan analisis/ringkasan untuk setiap dataset ------
    report = {
        "input_directory": str(input_dir.resolve()),
        "files_detected": sorted(file_names),
        "pegasus": {
            "android_full": summarize_pegasus_file(android_json, PEGASUS_ANDROID_JSON),
            "ios_full": summarize_pegasus_file(ios_json, PEGASUS_IOS_JSON),
            "android_layer": summarize_pegasus_file(android_layer, PEGASUS_ANDROID_LAYER),
            "ios_layer": summarize_pegasus_file(ios_layer, PEGASUS_IOS_LAYER),
            "comparison": compare_pegasus_sets(android_json, ios_json),
        },
        "kev": summarize_kev(kev_rows),
        "changelog": summarize_changelog(changelog),
        "xlsx": summarize_xlsx(xlsx_sheets),
    }

    return report
