#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
python bootstrap_pilot.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
