
import os,sys,json,tempfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
tmp=ROOT/"_test_data"
if tmp.exists():
    import shutil; shutil.rmtree(tmp)
os.environ["SIPRAI_DATA_DIR"]=str(tmp)
os.environ["SIPRAI_CREATE_DEMO_USERS"]="1"
os.environ["SIPRAI_SESSION_SECRET"]="test-secret-long-enough"
os.environ["SIPRAI_HTTPS_ONLY"]="0"
sys.path.insert(0,str(ROOT))

from app.pilot_store import init,authenticate,grant_project,ensure_user,get_user,can_access
from app.project_store import init as pinit,upsert_project
from app.professor_engine import init_trace_db,answer
from app.export_service import backup_databases
from app.security import SECURITY_HEADERS

init();pinit();init_trace_db()
prof=authenticate("profesor@demo.local","Profesor123!")
stu=authenticate("estudiante@demo.local","Estudiante123!")
upsert_project("WEB-TEST",{"title":"Web test"})
grant_project("WEB-TEST",stu["id"])
other=ensure_user("webotro@demo.local","Otro","OtraClave123!","student")
checks=[
 ("prof_login",bool(prof)),
 ("student_login",bool(stu)),
 ("acl_member",can_access(stu,"WEB-TEST")),
 ("acl_denied",not can_access(get_user(other),"WEB-TEST")),
 ("security_headers","Content-Security-Policy" in SECURITY_HEADERS),
]
r=answer("WEB-TEST","Hazme las conclusiones, todavía no tengo resultados.")
checks.append(("anti_fabrication",r["decision_state"]=="PENDIENTE / NO SUSTENTABLE"))
b=backup_databases()
checks.append(("backup_exists",b.exists()))
dbs=list(tmp.glob("*.db"))
checks.append(("persistent_dir",len(dbs)>=2))
print(json.dumps({"passed":sum(int(v) for _,v in checks),"total":len(checks),"checks":checks},ensure_ascii=False))
