# CDIS - Cyber Defense Intelligence System

Dashboard + CLI untuk memantau katalog [CISA Known Exploited
Vulnerabilities (KEV)](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
dan memindai backup mobile dengan [MVT (Mobile Verification
Toolkit)](https://docs.mvt.re/) untuk mendeteksi indikator spyware.

Backend Flask yang sama jalan tanpa perubahan di **Android (Termux)**,
**Windows**, dan **Linux/macOS** - semua path dan konfigurasi memakai
`os.path` + environment variable, tidak ada yang di-hardcode per platform.
Satu perintah (`python run.py`) menangani pembuatan virtual environment,
instalasi dependency, menjalankan backend, dan membuka browser secara
otomatis di ketiga platform.

## Struktur folder

```
cdis/
├─ run.py                    Launcher universal: venv + deps + start + buka browser
├─ backend/
│  ├─ app.py                 Flask API + static file server
│  ├─ config.py              Konfigurasi terpusat (path, host, port, env override)
│  ├─ requirements.txt
│  ├─ requirements-dev.txt   Dependency untuk testing (pytest)
│  ├─ requirements-mvt.txt   Opsional: dependensi MVT untuk fitur scan
│  ├─ data/                  SQLite db, log, hasil scan (dibuat otomatis)
│  ├─ modules/
│  │  ├─ database.py         Penyimpanan SQLite: KEV, metadata, riwayat scan
│  │  ├─ sync_engine.py      Download katalog KEV dari CISA (retry + backoff)
│  │  └─ mvt_scanner.py      Wrapper mvt-ios / mvt-android
│  └─ static/                Dashboard web (HTML/CSS/JS, tanpa build step)
├─ cli/
│  └─ cdis.py                CLI: health/version/stats/sync/list/search/cve/scan/scans/export
├─ tests/                    pytest: database, sync engine, mvt scanner, semua endpoint API
└─ scripts/
   ├─ setup_termux.sh / run_termux.sh     Android (Termux)
   ├─ setup_windows.bat / run_windows.bat Windows
   └─ setup_linux.sh / run_linux.sh       Linux / macOS
```

## Cara cepat (semua platform)

```bash
python run.py
```

`run.py` otomatis:
1. Membuat virtual environment di `./venv` (sekali saja).
2. Install/update dependency hanya jika `requirements.txt` berubah.
3. Menjalankan backend Flask dan menunggu sampai siap.
4. Membuka browser ke dashboard (atau `termux-open-url` di Termux).

Opsi: `--port 8080`, `--host 0.0.0.0`, `--no-browser`, `--debug`, `--system`
(pakai interpreter Python yang sedang aktif, lewati pembuatan venv).

## Android (Termux)

1. Install [Termux](https://f-droid.org/packages/com.termux/) dari F-Droid
   (versi Play Store sudah tidak di-update).
2. Clone atau salin folder `cdis/` ke perangkat, lalu di Termux:

   ```bash
   cd cdis
   bash scripts/setup_termux.sh
   bash scripts/run_termux.sh
   ```

3. Buka browser di HP yang sama ke `http://localhost:5000`, atau dari
   CLI di sesi Termux lain:

   ```bash
   python cli/cdis.py health
   python cli/cdis.py sync
   python cli/cdis.py list --limit 20
   ```

`setup_termux.sh` otomatis menjalankan `termux-setup-storage` supaya CDIS
bisa mengakses file backup di `/sdcard` saat melakukan scan Android.

## Windows

1. Install Python 3 dari [python.org](https://www.python.org/downloads/)
   dan centang **"Add python.exe to PATH"** saat instalasi.
2. Buka Command Prompt di folder `cdis\`:

   ```bat
   scripts\setup_windows.bat
   scripts\run_windows.bat
   ```

3. Buka browser ke `http://localhost:5000`, atau gunakan CLI di terminal
   lain (setelah `run_windows.bat` membuat `venv\` di run pertama):

   ```bat
   venv\Scripts\python cli\cdis.py health
   venv\Scripts\python cli\cdis.py sync
   ```

## Linux / macOS

```bash
bash scripts/setup_linux.sh
bash scripts/run_linux.sh
```

## Mengakses dari perangkat lain di jaringan yang sama

Backend bind ke `0.0.0.0` secara default, jadi bisa diakses dari perangkat
lain di Wi-Fi yang sama via IP lokal (mis. `http://192.168.1.20:5000`).
Untuk CLI dari perangkat lain:

```bash
CDIS_API_URL=http://192.168.1.20:5000/api python cli/cdis.py health
```

## API

| Method | Path                  | Keterangan                                          |
|--------|-----------------------|------------------------------------------------------|
| GET    | `/api/health`         | Status backend, jumlah KEV, ketersediaan MVT          |
| GET    | `/api/version`        | Versi backend + versi Python                          |
| GET    | `/api/stats`          | Total CVE, jumlah ransomware-linked, top vendor, dll  |
| GET    | `/api/kev`            | List KEV (pagination `limit`/`offset`, filter `q`)    |
| GET    | `/api/kev/search`     | Cari KEV (`q`, `limit`, `offset`)                     |
| GET    | `/api/kev/cve/<id>`   | Detail satu CVE                                       |
| POST   | `/api/sync`           | Sync ulang katalog KEV dari CISA                       |
| POST   | `/api/scan/ios`       | Scan backup iOS dengan mvt-ios (`backup_path`)         |
| POST   | `/api/scan/android`   | Scan backup Android dengan mvt-android (`backup_path`) |
| GET    | `/api/scans`          | Riwayat scan terakhir (`limit`)                        |
| GET    | `/api/export`         | Export katalog KEV (`format=json` atau `csv`)          |

Endpoint list/search mengembalikan bentuk `{total, count, limit, offset, items}`.

## CLI

```bash
python cli/cdis.py health
python cli/cdis.py version
python cli/cdis.py stats
python cli/cdis.py sync
python cli/cdis.py list --limit 20 --offset 0
python cli/cdis.py search log4j
python cli/cdis.py cve CVE-2021-44228
python cli/cdis.py scan android /sdcard/backup
python cli/cdis.py scans
python cli/cdis.py export kev.json
python cli/cdis.py export kev.csv
```

## Konfigurasi (environment variables)

| Variable                      | Default                      | Keterangan                                           |
|--------------------------------|-------------------------------|--------------------------------------------------------|
| `CDIS_HOST`                   | `0.0.0.0`                    | Interface yang dipakai backend                          |
| `CDIS_PORT`                   | `5000`                       | Port backend (auto-fallback ke port berikutnya jika dipakai) |
| `CDIS_PORT_FALLBACK_ATTEMPTS` | `10`                         | Berapa port berikutnya yang dicoba jika port utama penuh |
| `CDIS_DEBUG`                  | `false`                      | Aktifkan Flask debug mode                                |
| `CDIS_DATA_DIR`               | `backend/data`               | Lokasi database, log, hasil scan                         |
| `CDIS_DB_PATH`                | `backend/data/cdis.db`       | Lokasi file SQLite                                       |
| `CDIS_AUTO_SYNC_ON_EMPTY`     | `true`                       | Sync otomatis dari CISA saat database kosong (non-blocking) |
| `CDIS_SYNC_MAX_RETRIES`       | `3`                          | Jumlah percobaan sync sebelum menyerah                   |
| `CDIS_SYNC_RETRY_BACKOFF`     | `2`                          | Detik backoff awal (exponential) antar percobaan sync     |
| `CDIS_PAGE_SIZE`               | `50`                          | Ukuran halaman default untuk `/api/kev`                  |
| `CDIS_MAX_PAGE_SIZE`           | `500`                         | Batas maksimum `limit` yang diterima API                  |
| `CDIS_CORS_ORIGINS`            | `*`                           | Origin yang diizinkan CORS (pisahkan koma untuk membatasi) |
| `CDIS_API_URL`                | `http://localhost:5000/api`  | Dipakai CLI untuk menghubungi backend (set ke IP HP/PC lain untuk akses remote) |

## Fitur scan mobile (opsional)

Fitur `/api/scan/ios` dan `/api/scan/android` butuh paket `mvt`:

```bash
pip install -r backend/requirements-mvt.txt
```

- `mvt-android` jalan di Android (Termux), Windows, dan Linux/macOS - butuh `adb`.
- `mvt-ios` butuh `libimobiledevice`, yang **tidak** punya build resmi untuk
  Windows. Di Windows, gunakan WSL untuk analisis backup iOS, atau jalankan
  backend di Linux/macOS/Termux untuk fitur ini.

Jika `mvt` belum terinstal, endpoint scan akan tetap merespons dengan pesan
error yang jelas, bukan crash.

## Testing

```bash
pip install -r backend/requirements-dev.txt
pytest tests/
```

Test suite mencakup penyimpanan SQLite (pagination, search, stats, riwayat
scan), retry/backoff `sync_engine`, deteksi binary MVT, dan semua endpoint
Flask (lewat Flask test client, tanpa perlu koneksi internet).

## Troubleshooting

- **"Backend tidak berjalan"** dari CLI: pastikan `run.py` (atau
  `run_termux.sh` / `run_windows.bat` / `run_linux.sh`) masih berjalan di
  terminal lain.
- **Port 5000 sudah dipakai**: backend otomatis pindah ke port berikutnya
  dan menampilkan pesan port mana yang dipakai; atau set
  `CDIS_PORT=8080` / `python run.py --port 8080` secara eksplisit.
- **Database kosong setelah instal baru**: backend mencoba auto-sync dari
  CISA saat pertama kali start. Jika gagal (mis. tidak ada internet),
  jalankan `python cli/cdis.py sync` manual begitu ada koneksi.
- **Termux: izin penyimpanan ditolak**: jalankan `termux-setup-storage`
  manual lalu beri izin di pop-up Android.
