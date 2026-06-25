#!/usr/bin/env bash
set -e
pip install "Flask>=2.3"
python app.py --summary
python app.py --serve
