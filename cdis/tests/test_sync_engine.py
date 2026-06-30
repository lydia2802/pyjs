from unittest.mock import MagicMock, patch

import pytest
import requests

from modules.database import Database
from modules.sync_engine import SyncEngine


@pytest.fixture
def db(tmp_path):
    return Database(db_path=str(tmp_path / "test.db"))


def _ok_response(payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    return resp


def test_sync_success_stores_data(db):
    payload = {
        "catalogVersion": "2024.01.01",
        "dateReleased": "2024-01-01T00:00:00Z",
        "vulnerabilities": [
            {"cveID": "CVE-2021-44228", "vendorProject": "Apache", "product": "Log4j",
             "vulnerabilityName": "Log4Shell", "dateAdded": "2021-12-10", "shortDescription": "d",
             "requiredAction": "patch", "dueDate": "2021-12-24", "knownRansomwareCampaignUse": "Known",
             "notes": "", "cwes": []},
        ],
    }
    with patch("modules.sync_engine.requests.get", return_value=_ok_response(payload)) as mocked_get:
        engine = SyncEngine(db)
        result = engine.sync()

    mocked_get.assert_called_once()
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["catalog_version"] == "2024.01.01"
    assert db.count() == 1


def test_sync_empty_catalog_is_an_error(db):
    payload = {"vulnerabilities": []}
    with patch("modules.sync_engine.requests.get", return_value=_ok_response(payload)):
        engine = SyncEngine(db)
        result = engine.sync()

    assert result["status"] == "error"
    assert db.count() == 0


def test_sync_retries_on_network_error_then_succeeds(db, monkeypatch):
    monkeypatch.setattr("modules.sync_engine.time.sleep", lambda *_: None)
    payload = {"vulnerabilities": [
        {"cveID": "CVE-2023-1234", "vendorProject": "MS", "product": "Win",
         "vulnerabilityName": "X", "dateAdded": "2023-01-01", "shortDescription": "d",
         "requiredAction": "patch", "dueDate": "2023-01-15", "knownRansomwareCampaignUse": "Unknown",
         "notes": "", "cwes": []},
    ]}
    side_effects = [requests.exceptions.ConnectionError("boom"), _ok_response(payload)]
    with patch("modules.sync_engine.requests.get", side_effect=side_effects) as mocked_get:
        engine = SyncEngine(db)
        result = engine.sync()

    assert mocked_get.call_count == 2
    assert result["status"] == "success"
    assert db.count() == 1


def test_sync_gives_up_after_max_retries(db, monkeypatch):
    monkeypatch.setattr("modules.sync_engine.time.sleep", lambda *_: None)
    with patch("modules.sync_engine.requests.get",
               side_effect=requests.exceptions.ConnectionError("down")) as mocked_get:
        engine = SyncEngine(db)
        result = engine.sync()

    assert mocked_get.call_count == 3  # SYNC_MAX_RETRIES default
    assert result["status"] == "error"
    assert "Network error" in result["message"]
    assert db.count() == 0


def test_sync_handles_malformed_json(db, monkeypatch):
    monkeypatch.setattr("modules.sync_engine.time.sleep", lambda *_: None)
    bad_response = MagicMock()
    bad_response.raise_for_status.return_value = None
    bad_response.json.side_effect = ValueError("not json")
    with patch("modules.sync_engine.requests.get", return_value=bad_response):
        engine = SyncEngine(db)
        result = engine.sync()

    assert result["status"] == "error"
    assert "Unexpected response" in result["message"]
