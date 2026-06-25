# Pegasus / ATT&CK Threat Intel Dashboard

Contoh aplikasi yang menggabungkan **Python**, **JavaScript**, dan **Node.js** dalam satu pipeline, dibangun di atas framework `pyjs` (Python → JavaScript transpiler) yang ada di repo ini.

Data sumber: entri MITRE ATT&CK untuk teknik mobile malware "Pegasus" (S0316 - Android, S0289 - iOS) dan daftar Known Exploited Vulnerabilities milik CISA. Ini adalah data threat-intelligence publik untuk riset/analisis pertahanan, bukan perangkat lunak mata-mata.

## Bagaimana ketiga bahasa berperan

| Tahap | Bahasa | File |
|---|---|---|
| 1. Olah data (JSON/CSV/XLSX -> ringkasan) | **Python** | `analyzer/`, `generate_report.py` |
| 2. UI dashboard ditulis dengan Python, di-transpile `pyjs` jadi **JavaScript** asli | Python -> JS | `dashboard.py` -> `dist/dashboard.main.js` |
| 3. CSS dihasilkan oleh Tailwind CLI lewat shim **Node.js** | Node.js | `bin/tailwindcss` |
| 4. Build & rakit file statis (html/js/css) | Python | `build.py` |
| 5. Sajikan hasilnya | **Node.js** (atau server dev Python `pyjs.server`) | `server.js` / `dashboard.py` |

## Struktur folder

```
pegasus_dashboard/
├── input/                  # data mentah ATT&CK / KEV (JSON, CSV, XLSX)
├── analyzer/                # loaders.py + analyzers.py (port dari python_app asli)
├── generate_report.py      # Python: input/* -> output/ringkasan_data.json
├── report_args.py          # Python: ratakan JSON jadi argumen str/int/list[str]
├── dashboard.py            # UI pyjs (Python, di-transpile ke JS oleh pyjs)
├── build.py                 # Python: panggil pyjs.transpiler.bundle() + tulis dist/
├── bin/tailwindcss          # shim Node.js: jembatan pyjs <-> Tailwind CLI asli
├── server.js                 # server statis Node.js untuk folder dist/
└── package.json              # dependency Tailwind CLI utk Node
```

## Langkah-langkah menjalankan

### 1. Siapkan Python (>= 3.12, dibutuhkan oleh `pyjs`)

```bash
cd examples/pegasus_dashboard
python3.12 -m venv .venv      # atau python3.13
source .venv/bin/activate
pip install -e ../..          # install paket pyjs dari root repo
pip install -r requirements.txt
```

### 2. Olah data mentah jadi ringkasan JSON (Python)

```bash
python generate_report.py
# -> menulis output/ringkasan_data.json
```

### 3. Siapkan Node.js (Tailwind CLI + server statis)

```bash
npm install
export PATH="$PWD/bin:$PATH"   # supaya `tailwindcss` di PATH memanggil shim Node.js
```

### 4. Build situs statis (Python menjalankan transpiler pyjs, JS dihasilkan)

```bash
python build.py
# -> dist/index.html, dist/dashboard.main.js, dist/dashboard.main.css
```

### 5. Jalankan server Node.js dan buka di browser

```bash
node server.js
# atau: npm run serve
# buka http://localhost:5173
```

### Alternatif: mode pengembangan langsung dengan Python (tanpa build statis)

`pyjs` juga punya dev server bawaan (murni Python, auto-reload saat file berubah):

```bash
export PATH="$PWD/bin:$PATH"   # tetap perlu Tailwind CLI utk hitung CSS
python dashboard.py
# buka http://localhost:8000
```

## Catatan teknis

- `pyjs` (lihat `pyjs/transpiler/utils.py`) memanggil binari bernama `tailwindcss` dan mengirim HTML lewat stdin (`tailwindcss --content -`). CLI Tailwind v3+ yang asli hanya menerima path glob di `--content`, bukan stdin — karena itu `bin/tailwindcss` ditulis sebagai shim Node.js: menampung stdin ke file sementara lalu memanggil CLI asli di `node_modules/.bin/tailwindcss`.
- `dashboard.py` hanya menerima parameter primitif (`str`/`int`/`list[str]`) karena transpiler `pyjs` hanya mendukung subset kecil dari Python (lihat `pyjs/transpiler/_builtins.py`) — operasi seperti `str.join`, slicing, atau `dict` kompleks tidak didukung di kode yang ditranspile. Semua perataan/format data (gabung daftar platform, ambil top-5 vendor, dst.) dilakukan di Python biasa lewat `report_args.py` sebelum dipanggilkan ke `dashboard.main(...)`.
- File `input/changelog.json` adalah versi terpangkas (5 item per daftar) dari changelog resmi MITRE CTI, supaya ukuran repo tetap kecil. Jumlah pada bagian "Changelog" karena itu hanya bersifat contoh, bukan angka resmi MITRE.
