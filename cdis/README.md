# CDIS - Cyber Defense Intelligence System

Dashboard + CLI untuk memantau katalog [CISA Known Exploited
Vulnerabilities (KEV)](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
dan memindai backup mobile dengan [MVT (Mobile Verification
Toolkit)](https://docs.mvt.re/) untuk mendeteksi indikator spyware.

Backend Flask yang sama jalan tanpa perubahan di **Android (Termux)**,
**Windows**, dan **Linux/macOS** - semua path dan konfigurasi memakai
`os.path` + environment variable, tidak ada yang di-hardcode per platform.

## Struktur folder

```
cdis/
├─ backend/
│  ├─ app.py                 Flask API + static file server
│  ├─ config.py              Konfigurasi terpusat (path, host, port, env override)
│  ├─ requirements.txt
│  ├─ requirements-mvt.txt   Opsional: dependensi MVT untuk fitur scan
│  ├─ data/                  CSV KEV hasil sync (dibuat otomatis)
│  ├─ modules/
│  │  ├─ database.py         Load & search data KEV dari CSV
│  │  ├─ sync_engine.py      Download katalog KEV terbaru dari CISA
│  │  └─ mvt_scanner.py      Wrapper mvt-ios / mvt-android
│  └─ static/                Dashboard web (HTML/CSS/JS, tanpa build step)
├─ cli/
│  └─ cdis.py                CLI untuk health/sync/list/search/cve/scan
└─ scripts/
   ├─ setup_termux.sh / run_termux.sh     Android (Termux)
   ├─ setup_windows.bat / run_windows.bat Windows
   └─ setup_linux.sh / run_linux.sh       Linux / macOS
```

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
   lain (setelah `scripts\setup_windows.bat` membuat `venv\`):

   ```bat
   venv\Scripts\python cli\cdis.py health
   venv\Scripts\python cli\cdis.py sync
   ```

## Linux / macOS

```bash
bash scripts/setup_linux.sh
bash scripts/run_linux.sh
```

## Konfigurasi (environment variables)

| Variable             | Default                                    | Keterangan                              |
|-----------------------|---------------------------------------------|------------------------------------------|
| `CDIS_HOST`           | `0.0.0.0`                                  | Interface yang dipakai backend           |
| `CDIS_PORT`           | `5000`                                     | Port backend                             |
| `CDIS_DEBUG`          | `false`                                    | Aktifkan Flask debug mode                |
| `CDIS_DATA_DIR`       | `backend/data`                             | Lokasi penyimpanan CSV KEV               |
| `CDIS_API_URL`        | `http://localhost:5000/api`                | Dipakai CLI untuk menghubungi backend (set ke IP HP/PC lain untuk akses remote) |

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

## Troubleshooting

- **"Backend tidak berjalan"** dari CLI: pastikan `run_termux.sh` /
  `run_windows.bat` / `run_linux.sh` masih berjalan di terminal lain.
- **Port 5000 sudah dipakai**: jalankan dengan `CDIS_PORT=8080` sebelum
  memanggil script run.
- **Termux: izin penyimpanan ditolak**: jalankan `termux-setup-storage`
  manual lalu beri izin di pop-up Android.
