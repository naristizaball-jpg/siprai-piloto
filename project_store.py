
import sqlite3,json
from pathlib import Path
from .paths import DATA_DIR
BASE=Path(__file__).resolve().parent.parent
DB=DATA_DIR/"siprai_project.db"

def init():
    con=sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS projects(
      id TEXT PRIMARY KEY,
      title TEXT DEFAULT '',
      stage TEXT DEFAULT '',
      journal TEXT DEFAULT '',
      question TEXT DEFAULT '',
      objective TEXT DEFAULT '',
      method TEXT DEFAULT '',
      next_action TEXT DEFAULT '',
      state_json TEXT DEFAULT '{}'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS decisions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT,
      code TEXT,
      type TEXT,
      content TEXT,
      evidence TEXT,
      status TEXT,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS template_records(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id TEXT,
      template_code TEXT,
      version INTEGER DEFAULT 1,
      payload TEXT,
      status TEXT DEFAULT 'EN CONSTRUCCIÓN',
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit();con.close()

def upsert_project(pid,data):
    init(); con=sqlite3.connect(DB)
    row=con.execute("SELECT id FROM projects WHERE id=?",(pid,)).fetchone()
    fields=["title","stage","journal","question","objective","method","next_action"]
    vals=[str(data.get(f,"")) for f in fields]
    state_json=json.dumps(data.get("state",{}),ensure_ascii=False)
    if row:
        con.execute("""UPDATE projects SET title=?,stage=?,journal=?,question=?,objective=?,method=?,next_action=?,state_json=? WHERE id=?""",(*vals,state_json,pid))
    else:
        con.execute("""INSERT INTO projects(id,title,stage,journal,question,objective,method,next_action,state_json) VALUES(?,?,?,?,?,?,?,?,?)""",(pid,*vals,state_json))
    con.commit();con.close()

def get_project(pid):
    init();con=sqlite3.connect(DB);con.row_factory=sqlite3.Row
    r=con.execute("SELECT * FROM projects WHERE id=?",(pid,)).fetchone()
    con.close()
    if not r:return {"id":pid}
    d=dict(r)
    try:d["state"]=json.loads(d.pop("state_json") or "{}")
    except:d["state"]={}
    return d

def add_decision(pid,d):
    init();con=sqlite3.connect(DB)
    n=con.execute("SELECT COUNT(*) FROM decisions WHERE project_id=?",(pid,)).fetchone()[0]+1
    code=d.get("code") or f"DEC-{n:03d}"
    con.execute("INSERT INTO decisions(project_id,code,type,content,evidence,status) VALUES(?,?,?,?,?,?)",
        (pid,code,d.get("type",""),d.get("content",""),d.get("evidence",""),d.get("status","EN CONSTRUCCIÓN")))
    con.commit();con.close();return code

def decisions(pid,limit=20):
    init();con=sqlite3.connect(DB);con.row_factory=sqlite3.Row
    rows=con.execute("SELECT * FROM decisions WHERE project_id=? ORDER BY id DESC LIMIT ?",(pid,limit)).fetchall()
    con.close();return [dict(x) for x in rows]

def save_template(pid,code,payload,status="EN CONSTRUCCIÓN"):
    init();con=sqlite3.connect(DB)
    v=con.execute("SELECT COALESCE(MAX(version),0)+1 FROM template_records WHERE project_id=? AND template_code=?",(pid,code)).fetchone()[0]
    con.execute("INSERT INTO template_records(project_id,template_code,version,payload,status) VALUES(?,?,?,?,?)",
                (pid,code,v,json.dumps(payload,ensure_ascii=False),status))
    con.commit();con.close();return v
