
import json, sqlite3, zipfile, io
from pathlib import Path
from .project_store import get_project, decisions
from .professor_engine import get_trace
from .pilot_store import list_uploads

from .paths import DATA_DIR, BACKUPS_DIR
BASE=Path(__file__).resolve().parent.parent

def project_export(project_id):
    return {
      "project":get_project(project_id),
      "decisions":decisions(project_id,500),
      "trace":get_trace(project_id,500),
      "uploads":list_uploads(project_id)
    }

def project_export_bytes(project_id):
    return json.dumps(project_export(project_id),ensure_ascii=False,indent=2).encode("utf-8")

def backup_databases():
    bdir=BACKUPS_DIR; bdir.mkdir(parents=True,exist_ok=True)
    import datetime, shutil
    stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out=bdir/f"siprai_backup_{stamp}.zip"
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for n in ["siprai_project.db","siprai_trace.db","siprai_pilot.db"]:
            p=DATA_DIR/n
            if p.exists():z.write(p,n)
    return out


def list_backups():
    rows=[]
    for p in sorted(BACKUPS_DIR.glob("siprai_backup_*.zip"), reverse=True):
        rows.append({"name":p.name,"size_bytes":p.stat().st_size,"modified":p.stat().st_mtime})
    return rows

def backup_path(name):
    safe=Path(name).name
    p=BACKUPS_DIR/safe
    return p if p.exists() and p.is_file() and safe.startswith("siprai_backup_") and safe.endswith(".zip") else None
