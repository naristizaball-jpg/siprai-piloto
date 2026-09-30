
import sqlite3, os, hashlib, hmac, secrets, json, re
from pathlib import Path
from datetime import datetime

from .paths import DATA_DIR, UPLOADS_DIR
BASE=Path(__file__).resolve().parent.parent
DB=DATA_DIR/"siprai_pilot.db"
UPLOADS=UPLOADS_DIR
UPLOADS.mkdir(parents=True,exist_ok=True)

def connect():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def hash_password(password, salt=None):
    salt=salt or secrets.token_hex(16)
    dk=hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000)
    return salt+":"+dk.hex()

def verify_password(password, stored):
    try:
        salt,expected=stored.split(":",1)
        actual=hash_password(password,salt).split(":",1)[1]
        return hmac.compare_digest(actual,expected)
    except Exception:
        return False

def init():
    con=connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('professor','student')),
      active INTEGER NOT NULL DEFAULT 1,
      must_change_password INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS teams(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      created_by INTEGER,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS team_members(
      team_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      PRIMARY KEY(team_id,user_id)
    );
    CREATE TABLE IF NOT EXISTS project_acl(
      project_id TEXT NOT NULL,
      user_id INTEGER NOT NULL,
      access TEXT NOT NULL DEFAULT 'member',
      PRIMARY KEY(project_id,user_id)
    );
    CREATE TABLE IF NOT EXISTS uploads(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT NOT NULL,
      user_id INTEGER NOT NULL,
      original_name TEXT NOT NULL,
      stored_name TEXT NOT NULL,
      size_bytes INTEGER NOT NULL,
      mime TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      action TEXT NOT NULL,
      project_id TEXT,
      detail TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    con.commit()
    # Lightweight schema migration for earlier pilot databases
    cols=[r["name"] for r in con.execute("PRAGMA table_info(users)").fetchall()]
    if "must_change_password" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
        con.commit()
    # Local pilot demo accounts, only created when explicitly enabled (default on for local package)
    if os.getenv("SIPRAI_CREATE_DEMO_USERS","1")=="1":
        ensure_user("profesor@demo.local","Profesor SIPRAI","Profesor123!","professor")
        ensure_user("estudiante@demo.local","Estudiante Demo","Estudiante123!","student")
    con.close()

def ensure_user(email,name,password,role):
    con=connect()
    r=con.execute("SELECT id FROM users WHERE lower(email)=lower(?)",(email,)).fetchone()
    if r:
        con.close(); return r["id"]
    cur=con.execute("INSERT INTO users(email,name,password_hash,role) VALUES(?,?,?,?)",
                    (email.strip().lower(),name.strip(),hash_password(password),role))
    con.commit(); uid=cur.lastrowid; con.close(); return uid

def authenticate(email,password):
    con=connect()
    r=con.execute("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1",(email.strip(),)).fetchone()
    con.close()
    return dict(r) if r and verify_password(password,r["password_hash"]) else None

def get_user(uid):
    con=connect(); r=con.execute("SELECT id,email,name,role,active,must_change_password,created_at FROM users WHERE id=?",(uid,)).fetchone(); con.close()
    return dict(r) if r else None

def list_users():
    con=connect(); rows=con.execute("SELECT id,email,name,role,active,must_change_password,created_at FROM users ORDER BY role,name").fetchall(); con.close()
    return [dict(r) for r in rows]

def create_user(email,name,password,role):
    if role not in ("professor","student"): raise ValueError("Rol inválido")
    if len(password)<10: raise ValueError("La contraseña debe tener al menos 10 caracteres")
    return ensure_user(email,name,password,role)

def audit(uid,action,project_id=None,detail=None):
    con=connect(); con.execute("INSERT INTO audit(user_id,action,project_id,detail) VALUES(?,?,?,?)",
                              (uid,action,project_id,detail)); con.commit(); con.close()

def grant_project(project_id,user_id,access="member"):
    con=connect(); con.execute("INSERT OR REPLACE INTO project_acl(project_id,user_id,access) VALUES(?,?,?)",
                              (project_id,user_id,access)); con.commit(); con.close()

def can_access(user,project_id):
    if not user:return False
    if user["role"]=="professor":return True
    con=connect(); r=con.execute("SELECT 1 FROM project_acl WHERE project_id=? AND user_id=?",(project_id,user["id"])).fetchone(); con.close()
    return bool(r)

def projects_for_user(user):
    if user["role"]=="professor":
        con=connect(); rows=con.execute("SELECT DISTINCT project_id FROM project_acl ORDER BY project_id").fetchall(); con.close()
        return [r["project_id"] for r in rows]
    con=connect(); rows=con.execute("SELECT project_id FROM project_acl WHERE user_id=? ORDER BY project_id",(user["id"],)).fetchall(); con.close()
    return [r["project_id"] for r in rows]

def safe_project_id(pid):
    return re.sub(r"[^A-Za-z0-9_.-]","_",pid)[:80]

def store_upload(project_id,user_id,filename,data,mime,max_bytes=10*1024*1024):
    allowed={".pdf",".docx",".xlsx",".csv",".txt",".md",".json"}
    ext=Path(filename).suffix.lower()
    if ext not in allowed: raise ValueError("Tipo de archivo no permitido")
    if len(data)>max_bytes: raise ValueError("Archivo supera 10 MB")
    pid=safe_project_id(project_id)
    folder=UPLOADS/pid; folder.mkdir(parents=True,exist_ok=True)
    stored=secrets.token_hex(12)+ext
    path=folder/stored; path.write_bytes(data)
    con=connect()
    cur=con.execute("""INSERT INTO uploads(project_id,user_id,original_name,stored_name,size_bytes,mime)
                       VALUES(?,?,?,?,?,?)""",(project_id,user_id,filename,stored,len(data),mime))
    con.commit(); rid=cur.lastrowid; con.close()
    return {"id":rid,"original_name":filename,"size_bytes":len(data),"mime":mime}

def list_uploads(project_id):
    con=connect(); rows=con.execute("""SELECT uploads.id,uploads.original_name,uploads.size_bytes,uploads.mime,
       uploads.created_at,users.name uploader FROM uploads JOIN users ON users.id=uploads.user_id
       WHERE project_id=? ORDER BY uploads.id DESC""",(project_id,)).fetchall(); con.close()
    return [dict(r) for r in rows]

def audit_log(limit=100,project_id=None):
    con=connect()
    if project_id:
        rows=con.execute("""SELECT audit.*,users.name,user_email.email FROM audit
            LEFT JOIN users ON users.id=audit.user_id
            LEFT JOIN users user_email ON user_email.id=audit.user_id
            WHERE project_id=? ORDER BY audit.id DESC LIMIT ?""",(project_id,limit)).fetchall()
    else:
        rows=con.execute("""SELECT audit.*,users.name,users.email FROM audit
            LEFT JOIN users ON users.id=audit.user_id ORDER BY audit.id DESC LIMIT ?""",(limit,)).fetchall()
    con.close(); return [dict(r) for r in rows]


def set_password(user_id,new_password,must_change=False):
    if len(new_password)<10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres")
    con=connect()
    con.execute("UPDATE users SET password_hash=?, must_change_password=? WHERE id=?",
                (hash_password(new_password),1 if must_change else 0,user_id))
    con.commit(); con.close()

def set_active(user_id,active:bool):
    con=connect()
    con.execute("UPDATE users SET active=? WHERE id=?",(1 if active else 0,user_id))
    con.commit(); con.close()

def require_password_change(user_id):
    con=connect()
    con.execute("UPDATE users SET must_change_password=1 WHERE id=?",(user_id,))
    con.commit(); con.close()

def update_own_password(user_id,current_password,new_password):
    con=connect()
    r=con.execute("SELECT password_hash FROM users WHERE id=?",(user_id,)).fetchone()
    if not r or not verify_password(current_password,r["password_hash"]):
        con.close(); return False
    if len(new_password)<10:
        con.close(); raise ValueError("La nueva contraseña debe tener al menos 10 caracteres")
    con.execute("UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?",
                (hash_password(new_password),user_id))
    con.commit(); con.close(); return True

def revoke_project(project_id,user_id):
    con=connect()
    con.execute("DELETE FROM project_acl WHERE project_id=? AND user_id=?",(project_id,user_id))
    con.commit(); con.close()

def project_members(project_id):
    con=connect()
    rows=con.execute("""SELECT users.id,users.name,users.email,users.role,project_acl.access
                        FROM project_acl JOIN users ON users.id=project_acl.user_id
                        WHERE project_id=? ORDER BY users.role,users.name""",(project_id,)).fetchall()
    con.close(); return [dict(r) for r in rows]

def get_upload(project_id,upload_id):
    con=connect()
    try:
        row=con.execute("SELECT * FROM uploads WHERE project_id=? AND id=?",
                        (project_id,upload_id)).fetchone()
    finally:
        con.close()
    if not row:
        return None
    record=dict(row)
    folder=(UPLOADS/safe_project_id(project_id)).resolve()
    root=UPLOADS.resolve()
    path=(folder/record["stored_name"]).resolve()
    # Require a file inside the uploads directory and its project folder.
    if folder==root or root not in folder.parents or path.parent!=folder or not path.is_file():
        return None
    return record,path
