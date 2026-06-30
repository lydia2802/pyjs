import subprocess
from unittest.mock import MagicMock, patch

from modules.mvt_scanner import MVTScanner


def test_scanner_reports_unavailable_when_binaries_missing():
    with patch("modules.mvt_scanner.shutil.which", return_value=None):
        scanner = MVTScanner()

    assert scanner.mvt_ios_available is False
    assert scanner.mvt_android_available is False
    assert scanner.mvt_available is False


def test_scanner_reports_available_when_binary_runs():
    ok_result = MagicMock(returncode=0)
    with patch("modules.mvt_scanner.shutil.which", return_value="/usr/bin/mvt-android"), \
         patch("modules.mvt_scanner.subprocess.run", return_value=ok_result):
        scanner = MVTScanner()

    assert scanner.mvt_android_available is True
    assert scanner.mvt_available is True


def test_scanner_treats_version_check_timeout_as_unavailable():
    with patch("modules.mvt_scanner.shutil.which", return_value="/usr/bin/mvt-ios"), \
         patch("modules.mvt_scanner.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="mvt-ios", timeout=15)):
        scanner = MVTScanner()

    assert scanner.mvt_ios_available is False


def test_scan_android_errors_when_binary_not_available(tmp_path):
    with patch("modules.mvt_scanner.shutil.which", return_value=None):
        scanner = MVTScanner()

    result = scanner.scan_android(str(tmp_path))
    assert result["status"] == "error"
    assert "tidak terinstal" in result["message"]


def test_scan_android_errors_when_backup_path_missing():
    with patch("modules.mvt_scanner.shutil.which", return_value="/usr/bin/mvt-android"), \
         patch("modules.mvt_scanner.subprocess.run", return_value=MagicMock(returncode=0)):
        scanner = MVTScanner()

    result = scanner.scan_android("/path/does/not/exist")
    assert result["status"] == "error"
    assert "tidak ditemukan" in result["message"]


def test_scan_android_success_runs_check_backup(tmp_path):
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    completed = MagicMock(returncode=0, stdout="ok", stderr="")
    with patch("modules.mvt_scanner.shutil.which", return_value="/usr/bin/mvt-android"), \
         patch("modules.mvt_scanner.subprocess.run", return_value=MagicMock(returncode=0)) as run_check:
        scanner = MVTScanner()
        run_check.return_value = completed
        result = scanner.scan_android(str(backup_dir))

    assert result["status"] == "success"
    assert result["stdout"] == "ok"


def test_scan_times_out_gracefully(tmp_path):
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    with patch("modules.mvt_scanner.shutil.which", return_value="/usr/bin/mvt-android"), \
         patch("modules.mvt_scanner.subprocess.run") as run_mock:
        run_mock.return_value = MagicMock(returncode=0)
        scanner = MVTScanner()
        run_mock.side_effect = subprocess.TimeoutExpired(cmd="mvt-android", timeout=300)
        result = scanner.scan_android(str(backup_dir))

    assert result["status"] == "error"
    assert "timed out" in result["message"]
