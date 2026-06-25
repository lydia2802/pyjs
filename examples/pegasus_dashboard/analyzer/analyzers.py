from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .loaders import list_input_files, load_csv_rows, load_json, load_xlsx_rows


PEGASUS_ANDROID_JSON = "pegasus_for_android_(s0316).json"
PEGASUS_IOS_JSON = "pegasus_for_ios_(s0289).json"
PEGASUS_ANDROID_LAYER = "S0316-mobile-layer.json"
PEGASUS_IOS_LAYER = "S0289-mobile-layer.json"
CHANGELOG_JSON = "changelog.json"
KEV_CSV = "known_exploited_vulnerabilities.csv"
ANDROID_XLSX = "pegasus_for_android_(s0316).xlsx"


def summarize_pegasus_file(data: dict[str, Any], source_name: str) -> dict[str, Any]:
    techniques = data.get("techniques", [])
    technique_ids = [item.get("techniqueID") for item in techniques if item.get("techniqueID")]
    tactic_counts = Counter(item.get("tactic", "unknown") for item in techniques)
    commented_items = sum(1 for item in techniques if item.get("comment"))
    subtechniques = [item.get("techniqueID") for item in techniques if "." in str(item.get("techniqueID", ""))]

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
    android_ids = {item.get("techniqueID") for item in android_data.get("techniques", []) if item.get("techniqueID")}
    ios_ids = {item.get("techniqueID") for item in ios_data.get("techniques", []) if item.get("techniqueID")}

    return {
        "shared_techniques": sorted(android_ids & ios_ids),
        "android_only": sorted(android_ids - ios_ids),
        "ios_only": sorted(ios_ids - android_ids),
        "shared_count": len(android_ids & ios_ids),
        "android_only_count": len(android_ids - ios_ids),
        "ios_only_count": len(ios_ids - android_ids),
    }


def summarize_kev(rows: list[dict[str, str]]) -> dict[str, Any]:
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
    files = list_input_files(input_dir)
    file_names = {path.name for path in files}

    required = {
        PEGASUS_ANDROID_JSON,
        PEGASUS_IOS_JSON,
        PEGASUS_ANDROID_LAYER,
        PEGASUS_IOS_LAYER,
        CHANGELOG_JSON,
        KEV_CSV,
        ANDROID_XLSX,
    }
    missing = sorted(required - file_names)
    if missing:
        raise FileNotFoundError(f"Missing required input files: {', '.join(missing)}")

    android_json = load_json(input_dir / PEGASUS_ANDROID_JSON)
    ios_json = load_json(input_dir / PEGASUS_IOS_JSON)
    android_layer = load_json(input_dir / PEGASUS_ANDROID_LAYER)
    ios_layer = load_json(input_dir / PEGASUS_IOS_LAYER)
    kev_rows = load_csv_rows(input_dir / KEV_CSV)
    changelog = load_json(input_dir / CHANGELOG_JSON)
    xlsx_sheets = load_xlsx_rows(input_dir / ANDROID_XLSX)

    return {
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
