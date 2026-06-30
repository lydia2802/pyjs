import logging
import time

import requests

from config import KEV_JSON_URL, SYNC_MAX_RETRIES, SYNC_RETRY_BACKOFF, SYNC_TIMEOUT

logger = logging.getLogger("cdis.sync")


class SyncEngine:
    """Downloads the latest CISA KEV catalog and stores it in the database.

    Retries with exponential backoff because this is meant to run over
    mobile data / unstable Wi-Fi (Termux on a phone) just as much as over
    a wired PC connection.
    """

    def __init__(self, db):
        self.db = db

    def sync(self):
        last_error = None
        for attempt in range(1, SYNC_MAX_RETRIES + 1):
            try:
                response = requests.get(KEV_JSON_URL, timeout=SYNC_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])

                if not vulnerabilities:
                    return {"status": "error", "message": "No data from CISA"}

                self.db.replace_all(vulnerabilities)
                logger.info("Synced %d KEV entries", len(vulnerabilities))
                return {
                    "status": "success",
                    "count": len(vulnerabilities),
                    "catalog_version": data.get("catalogVersion"),
                    "date_released": data.get("dateReleased"),
                }
            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {e}"
            except (ValueError, KeyError) as e:
                last_error = f"Unexpected response from CISA: {e}"
            except Exception as e:
                last_error = str(e)

            if attempt < SYNC_MAX_RETRIES:
                wait = SYNC_RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning("Sync attempt %d/%d failed (%s), retrying in %.0fs", attempt, SYNC_MAX_RETRIES, last_error, wait)
                time.sleep(wait)

        logger.error("Sync failed after %d attempts: %s", SYNC_MAX_RETRIES, last_error)
        return {"status": "error", "message": last_error}
