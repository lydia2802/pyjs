import os
import shutil
import subprocess

from config import SCAN_OUTPUT_DIR, SCAN_TIMEOUT


class MVTScanner:
    """Thin wrapper around the Mobile Verification Toolkit (mvt) CLI tools.

    mvt-ios depends on libimobiledevice, which has no official Windows
    build, so on Windows only mvt-android (pure Python + adb) is
    realistically available. Both tools install the same way on Termux
    (Android) and Linux/macOS via `pip install mvt`. shutil.which() is
    used instead of a raw subprocess call so the same code resolves
    mvt-ios.exe / mvt-android.exe on Windows without changes.
    """

    def __init__(self):
        self.mvt_ios_available = self._check("mvt-ios")
        self.mvt_android_available = self._check("mvt-android")

    @property
    def mvt_available(self):
        return self.mvt_ios_available or self.mvt_android_available

    def _check(self, binary_name):
        if shutil.which(binary_name) is None:
            return False
        try:
            subprocess.run(
                [binary_name, "--version"],
                capture_output=True,
                check=True,
                timeout=15,
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _run_scan(self, binary_name, backup_path):
        output_dir = SCAN_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        try:
            result = subprocess.run(
                [binary_name, "check-backup", "-o", output_dir, backup_path],
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT,
            )
            return {
                "status": "success" if result.returncode == 0 else "warning",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_dir": output_dir,
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Scan timed out after {SCAN_TIMEOUT}s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def scan_ios(self, backup_path):
        if not self.mvt_ios_available:
            return {
                "status": "error",
                "message": "mvt-ios tidak terinstal atau tidak ditemukan di PATH. Install: pip install mvt "
                "(catatan: mvt-ios butuh libimobiledevice, tidak tersedia native di Windows).",
            }
        if not os.path.exists(backup_path):
            return {"status": "error", "message": "Backup path tidak ditemukan"}
        return self._run_scan("mvt-ios", backup_path)

    def scan_android(self, backup_path):
        if not self.mvt_android_available:
            return {
                "status": "error",
                "message": "mvt-android tidak terinstal atau tidak ditemukan di PATH. Install: pip install mvt",
            }
        if not os.path.exists(backup_path):
            return {"status": "error", "message": "Backup path tidak ditemukan"}
        return self._run_scan("mvt-android", backup_path)
