import csv
import os

import requests

from config import KEV_CSV_PATH, KEV_JSON_URL, SYNC_TIMEOUT


class SyncEngine:
    """Downloads the latest CISA KEV catalog and writes it to disk as CSV."""

    def __init__(self, csv_path=None):
        self.csv_path = csv_path or KEV_CSV_PATH

    def sync(self):
        try:
            response = requests.get(KEV_JSON_URL, timeout=SYNC_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])

            if not vulnerabilities:
                return {"status": "error", "message": "No data from CISA"}

            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=vulnerabilities[0].keys())
                writer.writeheader()
                writer.writerows(vulnerabilities)

            return {"status": "success", "count": len(vulnerabilities)}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Network error: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
