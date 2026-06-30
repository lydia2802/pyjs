import pytest

import app as app_module

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
        "cwes": [],
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
def client():
    app_module.app.testing = True
    app_module.db.replace_all([])
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def seeded_client(client):
    app_module.db.replace_all(SAMPLE_ROWS)
    return client


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "kev_count" in data


def test_version(client):
    res = client.get("/api/version")
    assert res.status_code == 200
    assert "version" in res.get_json()


def test_kev_list_empty(client):
    res = client.get("/api/kev")
    data = res.get_json()
    assert data["total"] == 0
    assert data["items"] == []


def test_kev_list_pagination(seeded_client):
    res = seeded_client.get("/api/kev?limit=1&offset=0")
    data = res.get_json()
    assert data["total"] == 2
    assert data["count"] == 1
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1


def test_kev_list_invalid_pagination_params(seeded_client):
    res = seeded_client.get("/api/kev?limit=abc")
    assert res.status_code == 400


def test_kev_list_clamps_limit_to_max(seeded_client):
    res = seeded_client.get("/api/kev?limit=999999")
    data = res.get_json()
    assert data["limit"] <= 500


def test_kev_search(seeded_client):
    res = seeded_client.get("/api/kev/search?q=log4j")
    data = res.get_json()
    assert data["total"] == 1
    assert data["items"][0]["cveID"] == "CVE-2021-44228"


def test_kev_via_q_param_on_main_route(seeded_client):
    res = seeded_client.get("/api/kev?q=microsoft")
    data = res.get_json()
    assert data["total"] == 1
    assert data["items"][0]["cveID"] == "CVE-2023-1234"


def test_get_cve_found(seeded_client):
    res = seeded_client.get("/api/kev/cve/CVE-2021-44228")
    assert res.status_code == 200
    assert res.get_json()["vendorProject"] == "Apache"


def test_get_cve_not_found(seeded_client):
    res = seeded_client.get("/api/kev/cve/CVE-0000-0000")
    assert res.status_code == 404


def test_stats(seeded_client):
    res = seeded_client.get("/api/stats")
    data = res.get_json()
    assert data["total"] == 2
    assert data["ransomware_count"] == 1


def test_sync_success(client, monkeypatch):
    monkeypatch.setattr(
        app_module.sync, "sync",
        lambda: {"status": "success", "count": 1, "catalog_version": "x", "date_released": "y"},
    )
    res = client.post("/api/sync")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"


def test_sync_failure_returns_502(client, monkeypatch):
    monkeypatch.setattr(
        app_module.sync, "sync",
        lambda: {"status": "error", "message": "no network"},
    )
    res = client.post("/api/sync")
    assert res.status_code == 502
    assert res.get_json()["status"] == "error"


def test_scan_android_invalid_path(client):
    res = client.post("/api/scan/android", json={"backup_path": "/path/does/not/exist"})
    assert res.status_code == 400
    assert res.get_json()["status"] == "error"


def test_scan_android_missing_body(client):
    res = client.post("/api/scan/android", json={})
    assert res.status_code == 400


def test_scan_android_success_records_history(client, monkeypatch, tmp_path):
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    monkeypatch.setattr(
        app_module.scanner, "scan_android",
        lambda path: {"status": "success", "stdout": "clean", "stderr": "", "output_dir": "x"},
    )
    res = client.post("/api/scan/android", json={"backup_path": str(backup_dir)})
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"

    history = client.get("/api/scans").get_json()
    assert len(history) >= 1
    assert history[0]["platform"] == "android"
    assert history[0]["status"] == "success"


def test_scan_ios_success_records_history(client, monkeypatch, tmp_path):
    backup_dir = tmp_path / "ios_backup"
    backup_dir.mkdir()
    monkeypatch.setattr(
        app_module.scanner, "scan_ios",
        lambda path: {"status": "warning", "stdout": "", "stderr": "", "output_dir": "x"},
    )
    res = client.post("/api/scan/ios", json={"backup_path": str(backup_dir)})
    assert res.status_code == 200
    assert res.get_json()["status"] == "warning"


def test_scans_endpoint_invalid_limit(client):
    res = client.get("/api/scans?limit=notanumber")
    assert res.status_code == 400


def test_export_json(seeded_client):
    res = seeded_client.get("/api/export?format=json")
    assert res.status_code == 200
    assert res.mimetype == "application/json"
    assert "attachment" in res.headers["Content-Disposition"]


def test_export_csv(seeded_client):
    res = seeded_client.get("/api/export?format=csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    body = res.get_data(as_text=True)
    assert "cveID" in body
    assert "CVE-2021-44228" in body


def test_unknown_api_route_returns_json_404(client):
    res = client.get("/api/does-not-exist")
    assert res.status_code == 404
    assert res.is_json


def test_static_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"CDIS" in res.data


def test_unknown_static_route_returns_html_404(client):
    res = client.get("/this-page-does-not-exist")
    assert res.status_code == 404
    assert not res.is_json
