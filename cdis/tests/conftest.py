import os
import sys
import tempfile

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Must be set before any test imports `config` / `app`, since config.py
# reads these env vars once at import time and app.py builds its
# module-level Database()/SyncEngine()/MVTScanner() from them.
_test_data_dir = tempfile.mkdtemp(prefix="cdis_test_")
os.environ["CDIS_DATA_DIR"] = _test_data_dir
os.environ["CDIS_DB_PATH"] = os.path.join(_test_data_dir, "test_cdis.db")
os.environ["CDIS_AUTO_SYNC_ON_EMPTY"] = "false"
