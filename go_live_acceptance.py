
import os,sys,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
tmp=ROOT/"_test_data_29"
if tmp.exists(): shutil.rmtree(tmp)
os.environ["SIPRAI_DATA_DIR"]=str(tmp)
os.environ["SIPRAI_CREATE_DEMO_USERS"]="1"
os.environ["SIPRAI_SESSION_SECRET"]="test-secret-29"
os.environ["SIPRAI_HTTPS_ONLY"]="0"
sys.path.insert(0,str(ROOT))

from app.pilot_store import init,authenticate,ensure_user,get_user,set_password,update_own_password,set_active,grant_project,revoke_project,can_access,project_members
from app.project_store import init as pinit,upsert_project
from app.professor_engine import init_trace_db,answer
from app.export_service import backup_databases,list_backups,backup_path

init();pinit();init_trace_db()
prof=authenticate("profesor@demo.local","Profesor123!")
stu=authenticate("estudiante@demo.local","Estudiante123!")
upsert_project("GL-001",{"title":"Go Live"})
grant_project("GL-001",stu["id"])
checks=[]
checks.append(("login",bool(prof and stu)))
checks.append(("acl_grant",can_access(stu,"GL-001")))
checks.append(("members",len(project_members("GL-001"))>=1))
set_password(stu["id"],"Temporal123!",must_change=True)
checks.append(("reset_pwd",bool(authenticate("estudiante@demo.local","Temporal123!"))))
ok=update_own_password(stu["id"],"Temporal123!","Definitiva123!")
checks.append(("change_pwd",ok and bool(authenticate("estudiante@demo.local","Definitiva123!"))))
set_active(stu["id"],False)
checks.append(("deactivate",authenticate("estudiante@demo.local","Definitiva123!") is None))
set_active(stu["id"],True)
revoke_project("GL-001",stu["id"])
checks.append(("acl_revoke",not can_access(get_user(stu["id"]),"GL-001")))
b=backup_databases()
checks.append(("backup",b.exists() and backup_path(b.name) is not None and len(list_backups())>=1))
r=answer("GL-001","Hazme conclusiones sin resultados.")
checks.append(("anti_fabrication",r["decision_state"]=="PENDIENTE / NO SUSTENTABLE"))
checks.append(("persistent_dir",(tmp/"siprai_pilot.db").exists()))
print(json.dumps({"passed":sum(int(v) for _,v in checks),"total":len(checks),"checks":checks},ensure_ascii=False))
