
import os,sys,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ["SIPRAI_CREATE_DEMO_USERS"]="1"

from app.pilot_store import init,authenticate,get_user,ensure_user,grant_project,can_access,store_upload
from app.project_store import init as pinit,upsert_project
from app.export_service import project_export
from app.professor_engine import answer

init();pinit()
prof=authenticate("profesor@demo.local","Profesor123!")
stu=authenticate("estudiante@demo.local","Estudiante123!")
upsert_project("TEST-PILOT",{"title":"Test pilot","stage":"Descubrimiento"})
grant_project("TEST-PILOT",stu["id"])
other=ensure_user("otro@demo.local","Otro Estudiante","OtraClave123!","student")
checks=[]
checks.append(("login_prof",bool(prof)))
checks.append(("login_student",bool(stu)))
checks.append(("prof_access",can_access(prof,"TEST-PILOT")))
checks.append(("student_access",can_access(stu,"TEST-PILOT")))
checks.append(("deny_other",not can_access(get_user(other),"TEST-PILOT")))
rec=store_upload("TEST-PILOT",stu["id"],"nota.txt",b"evidencia piloto","text/plain")
checks.append(("upload",rec["size_bytes"]>0))
ans=answer("TEST-PILOT","Hazme las conclusiones, todavía no tengo resultados.")
checks.append(("anti_fabrication",ans["decision_state"]=="PENDIENTE / NO SUSTENTABLE"))
exp=project_export("TEST-PILOT")
checks.append(("export",exp["project"]["id"]=="TEST-PILOT"))
print(json.dumps({"passed":sum(1 for _,x in checks if x),"total":len(checks),"checks":checks},ensure_ascii=False))
