
import os
from pathlib import Path

APP_ROOT=Path(__file__).resolve().parent.parent
DATA_DIR=Path(os.getenv("SIPRAI_DATA_DIR", str(APP_ROOT/"data"))).resolve()
UPLOADS_DIR=DATA_DIR/"uploads"
BACKUPS_DIR=DATA_DIR/"backups"
DATA_DIR.mkdir(parents=True,exist_ok=True)
UPLOADS_DIR.mkdir(parents=True,exist_ok=True)
BACKUPS_DIR.mkdir(parents=True,exist_ok=True)
