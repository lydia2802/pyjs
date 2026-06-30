import pytest

from modules.database import Database

SAMPLE_ROWS = [
    {
        "cveID": "CVE-2021-44228",
        "vendorProject": "Apache",
        "product": "Log4j",
        "vulnerabilityName": "Log4Shell RCE",
        "dateAdded": "2021-12-10",
        "shortDescription": "desc",
        "requiredAction": "patch",
        "dueDate": "2021-12-24",
        "knownRansomwareCampaignUse": "Known",
        "notes": "",
        "cwes": ["CWE-502"],
    },
    {
        "cveID": "CVE-2023-1234",
        "vendorProject": "Microsoft",
        "product": "Windows",
        "vulnerabilityName": "Test Vuln",
        "dateAdded": "2023-01-01",
        "shortDescription": "desc2",
        "requiredAction": "patch",
        "dueDate": "2023-01-15",
        "knownRansomwareCampaignUse": "Unknown",
        "notes": "",
        "cwes": [],
    },
]


@pytest.fixture
def db(tmp_path):
    return Database(db_path=str(tmp_path / "test.db"))


def test_empty_db_starts_at_zero(db):
    assert db.count() == 0
    items, total = db.get_all()
    assert items == []
    assert total == 0


def test_replace_all_inserts_rows(db):
    db.replace_all(SAMPLE_ROWS)
    assert db.count() == 2
    assert db.get_meta("last_sync_count") == "2"
    assert db.get_meta("last_sync_at") is not None


def test_replace_all_is_atomic_replace_not_append(db):
    db.replace_all(SAMPLE_ROWS)
    db.replace_all(SAMPLE_ROWS[:1])
    assert db.count() == 1


def test_get_all_pagination(db):
    db.replace_all(SAMPLE_ROWS)
    items, total = db.get_all(limit=1, offset=0)
    assert total == 2
    assert len(items) == 1
    items2, total2 = db.get_all(limit=1, offset=1)
    assert total2 == 2
    assert len(items2) == 1
    assert items[0]["cveID"] != items2[0]["cveID"]


def test_search_matches_vendor_product_name(db):
    db.replace_all(SAMPLE_ROWS)
    items, total = db.search("log4j")
    assert total == 1
    assert items[0]["cveID"] == "CVE-2021-44228"

    items, total = db.search("microsoft")
    assert total == 1
    assert items[0]["cveID"] == "CVE-2023-1234"

    items, total = db.search("doesnotexist")
    assert total == 0
    assert items == []


def test_search_empty_keyword_falls_back_to_get_all(db):
    db.replace_all(SAMPLE_ROWS)
    items, total = db.search("")
    assert total == 2


def test_get_by_cve_case_insensitive(db):
    db.replace_all(SAMPLE_ROWS)
    result = db.get_by_cve("cve-2021-44228")
    assert result is not None
    assert result["vendorProject"] == "Apache"
    assert result["cwes"] == ["CWE-502"]


def test_get_by_cve_not_found(db):
    assert db.get_by_cve("CVE-0000-0000") is None


def test_stats(db):
    db.replace_all(SAMPLE_ROWS)
    stats = db.stats()
    assert stats["total"] == 2
    assert stats["ransomware_count"] == 1
    assert stats["latest_date_added"] == "2023-01-01"
    vendors = {v["vendor"] for v in stats["top_vendors"]}
    assert vendors == {"Apache", "Microsoft"}


def test_record_and_list_scans(db):
    db.record_scan("android", "/path/to/backup", "success", "all clean")
    db.record_scan("ios", "/path/to/other", "error", "mvt not found")
    scans = db.list_scans(limit=10)
    assert len(scans) == 2
    assert scans[0]["platform"] == "ios"  # most recent first
    assert scans[1]["platform"] == "android"


def test_export_rows_roundtrip(db):
    db.replace_all(SAMPLE_ROWS)
    rows = db.export_rows()
    assert len(rows) == 2
    cve_ids = {r["cveID"] for r in rows}
    assert cve_ids == {"CVE-2021-44228", "CVE-2023-1234"}


def test_migrate_legacy_csv(tmp_path, monkeypatch):
    import modules.database as database_module

    csv_path = tmp_path / "legacy.csv"
    csv_path.write_text(
        "cveID,vendorProject,product,vulnerabilityName,dateAdded,shortDescription,"
        "requiredAction,dueDate,knownRansomwareCampaignUse,notes,cwes\n"
        "CVE-1999-0001,OldVendor,OldProduct,Old Vuln,1999-01-01,d,r,1999-02-01,Unknown,,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(database_module, "KEV_CSV_PATH", str(csv_path))

    migrated_db = Database(db_path=str(tmp_path / "migrated.db"))
    assert migrated_db.count() == 1
    assert migrated_db.get_by_cve("CVE-1999-0001") is not None
