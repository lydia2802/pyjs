import csv
import os

from config import KEV_CSV_PATH


class Database:
    """In-memory view of the CISA Known Exploited Vulnerabilities CSV."""

    def __init__(self, csv_path=None):
        self.csv_path = csv_path or KEV_CSV_PATH
        self.data = []
        self.load()

    def load(self):
        if not os.path.exists(self.csv_path):
            self.data = []
            return
        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.data = list(reader)

    def search(self, keyword):
        keyword = (keyword or "").lower()
        if not keyword:
            return self.data
        return [row for row in self.data if keyword in str(row).lower()]

    def get_by_cve(self, cve_id):
        cve_id = (cve_id or "").upper()
        return [row for row in self.data if row.get("cveID", "").upper() == cve_id]

    def get_all(self):
        return self.data
