#!/usr/bin/env python3
"""Universal CDIS launcher - works the same way on Android (Termux),
Windows, Linux and macOS.

What it does, every time you run `python run.py`:
  1. Creates a virtual environment in ./venv if one doesn't exist yet
     (falls back to a `--user` install if venv creation isn't possible).
  2. Installs/updates backend dependencies only when requirements.txt
     actually changed (fast on every subsequent run).
  3. Re-executes itself inside that venv so the Flask app always runs
     with the right interpreter and packages.
  4. Starts the backend, waits for it to report it is ready, then opens
     a browser tab automatically (or runs `termux-open-url` on Android).

Usage:
    python run.py                  # normal start
    python run.py --port 8080      # custom port
    python run.py --no-browser     # don't auto-open a browser
    python run.py --system         # skip venv, use current interpreter as-is
"""
import argparse
import hashlib
import os
import platform
import re
import subprocess
import sys
import threading
import time
import urllib.request

CDIS_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CDIS_ROOT, "backend")
VENV_DIR = os.path.join(CDIS_ROOT, "venv")
REQUIREMENTS = os.path.join(BACKEND_DIR, "requirements.txt")
DEPS_HASH_FILE = os.path.join(VENV_DIR, ".deps_hash")

IS_WINDOWS = platform.system() == "Windows"
IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "") or "TERMUX_VERSION" in os.environ


def venv_python_path():
    if IS_WINDOWS:
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def _requirements_hash():
    with open(REQUIREMENTS, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _run(cmd, **kwargs):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def ensure_venv_and_deps():
    """Create the venv (if missing) and install deps (if they changed).
    Returns the python executable to re-exec with, or None if the caller
    should just continue with the current interpreter (--system / venv
    creation not possible)."""
    py = venv_python_path()

    if not os.path.exists(py):
        print("==> Membuat virtual environment di ./venv ...")
        try:
            _run([sys.executable, "-m", "venv", VENV_DIR])
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"Gagal membuat virtual environment ({e}).")
            print("Lanjut tanpa venv, install dependency langsung untuk user saat ini...")
            try:
                _run([sys.executable, "-m", "pip", "install", "--user", "-r", REQUIREMENTS])
            except subprocess.CalledProcessError:
                print("Gagal install dependency. Install manual dengan:")
                print(f"  {sys.executable} -m pip install -r {REQUIREMENTS}")
                sys.exit(1)
            return None

    current_hash = _requirements_hash()
    stored_hash = None
    if os.path.exists(DEPS_HASH_FILE):
        with open(DEPS_HASH_FILE, "r", encoding="utf-8") as f:
            stored_hash = f.read().strip()

    if current_hash != stored_hash:
        print("==> Menginstall/memperbarui dependency backend...")
        try:
            _run([py, "-m", "pip", "install", "--upgrade", "pip"])
            _run([py, "-m", "pip", "install", "-r", REQUIREMENTS])
        except subprocess.CalledProcessError:
            print("Gagal install dependency. Cek koneksi internet lalu coba lagi,")
            print(f"atau install manual dengan: {py} -m pip install -r {REQUIREMENTS}")
            sys.exit(1)
        with open(DEPS_HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("==> Dependency sudah up to date, lewati instalasi.")

    return py


def open_browser(url):
    if IS_TERMUX:
        try:
            subprocess.run(["termux-open-url", url], check=True, timeout=5)
            return
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"Tidak bisa membuka browser otomatis. Buka manual: {url}")
            return
    try:
        import webbrowser
        if not webbrowser.open(url):
            raise RuntimeError("no browser handler")
    except Exception:
        print(f"Tidak bisa membuka browser otomatis. Buka manual: {url}")


READY_RE = re.compile(r"running at (http://\S+)")


def stream_and_launch_browser(proc, open_browser_flag):
    opened = False
    for line in proc.stdout:
        print(line, end="")
        if not opened:
            m = READY_RE.search(line)
            if m:
                opened = True
                if open_browser_flag:
                    threading.Thread(target=open_browser, args=(m.group(1),), daemon=True).start()


def run_backend(python_exe, extra_env, open_browser_flag):
    env = os.environ.copy()
    env.update(extra_env)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [python_exe, "app.py"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    reader = threading.Thread(target=stream_and_launch_browser, args=(proc, open_browser_flag), daemon=True)
    reader.start()

    try:
        while proc.poll() is None:
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nMenghentikan CDIS...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    reader.join(timeout=2)
    return proc.returncode or 0


def main():
    parser = argparse.ArgumentParser(description="Jalankan CDIS - bekerja di Android (Termux), Windows, Linux, macOS")
    parser.add_argument("--port", type=int, help="Port backend (default 5000, override CDIS_PORT)")
    parser.add_argument("--host", help="Host bind backend (default 0.0.0.0, override CDIS_HOST)")
    parser.add_argument("--no-browser", action="store_true", help="Jangan buka browser otomatis")
    parser.add_argument("--debug", action="store_true", help="Aktifkan Flask debug mode")
    parser.add_argument("--system", action="store_true", help="Pakai interpreter Python saat ini, lewati venv")
    args = parser.parse_args()

    extra_env = {}
    if args.port:
        extra_env["CDIS_PORT"] = str(args.port)
    if args.host:
        extra_env["CDIS_HOST"] = args.host
    if args.debug:
        extra_env["CDIS_DEBUG"] = "true"

    if IS_TERMUX:
        print("Terdeteksi Termux di Android.")

    if args.system or os.environ.get("CDIS_IN_VENV") == "1":
        python_exe = sys.executable
    else:
        python_exe = ensure_venv_and_deps() or sys.executable
        if python_exe != sys.executable:
            extra_env["CDIS_IN_VENV"] = "1"

    code = run_backend(python_exe, extra_env, open_browser_flag=not args.no_browser)
    sys.exit(code)


if __name__ == "__main__":
    main()
