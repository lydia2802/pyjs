"""
Entry point untuk menjalankan paket langsung lewat:

    python -m attck_kev_analyzer [argumen...]

tanpa perlu melakukan instalasi (pip install) terlebih dahulu.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
