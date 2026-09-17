
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import json, os, secrets

from .router_knowledge import route_message
from .knowledge_search import search as knowledge_search
from .quality_engine import evaluate_T29, product_gate_status
from .professor_engine import answer as professor_answer, get_trace, init_trace_db
from .project_store import init as init_projects, upsert_project, get_project, add_decision, decisions as project_decisions, save_template
from .pilot_store import init as init_pilot, authenticate, get_user, list_users, create_user, grant_project, revoke_project, project_members, can_access, projects_for_user, audit, store_upload, list_uploads, audit_log, ensure_user, set_password, set_active, update_own_password
from .export_service import project_export_bytes, backup_databases, list_backups, backup_path
from .security import csrf_token, require_csrf, rate_limit, SECURITY_HEADERS
from .paths import DATA_DIR

BASE=Path(__file__).resolve().parent.parent
FORMS=json.loads((BASE/"config"/"forms_T01_T30.json").read_text(encoding="utf-8"))

app=FastAPI(title="SIPRAI 2.8 Despliegue Web")
app.add_middleware(SessionMiddleware,
    secret_key=os.getenv("SIPRAI_SESSION_SECRET","CHANGE-ME"),
    same_site="lax",
    https_only=os.getenv("SIPRAI_HTTPS_ONLY","1")=="1",
    max_age=60*60*8)

@app.middleware("http")
async def security_middleware(request:Request,call_next):
    rate_limit(request)
    response=await call_next(request)
    for k,v in SECURITY_HEADERS.items():
        response.headers[k]=v
    if os.getenv("SIPRAI_HTTPS_ONLY","1")=="1":
        response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
    return response

@app.on_event("startup")
def startup():
    if os.getenv("SIPRAI_SESSION_SECRET","CHANGE-ME")=="CHANGE-ME":
        # Allowed locally, but production health exposes warning.
        pass
    init_trace_db(); init_projects(); init_pilot()
    # Optional initial professor, only from explicit env
    email=os.getenv("SIPRAI_ADMIN_EMAIL","").strip()
    pw=os.getenv("SIPRAI_ADMIN_PASSWORD","")
    name=os.getenv("SIPRAI_ADMIN_NAME","Profesor SIPRAI").strip()
    if email and pw:
        ensure_user(email,name,pw,"professor")

def current_user(request:Request):
    uid=request.session.get("uid")
    return get_user(uid) if uid else None

def require_user(request:Request):
    u=current_user(request)
    if not u: raise HTTPException(401,"Inicie sesión")
    return u

def require_professor(request:Request):
    u=require_user(request)
    if u["role"]!="professor": raise HTTPException(403,"Acceso docente requerido")
    return u

def require_project(request:Request,project_id:str):
    u=require_user(request)
    if not can_access(u,project_id): raise HTTPException(403,"Sin acceso a este proyecto")
    return u

def mutating(request:Request):
    require_csrf(request)

@app.get("/health")
def health():
    secret_ok=os.getenv("SIPRAI_SESSION_SECRET","CHANGE-ME")!="CHANGE-ME"
    return {"status":"ok","version":"2.8","documents":16,"templates":30,
            "persistent_data":str(DATA_DIR),"security_secret_configured":secret_ok,
            "demo_users":os.getenv("SIPRAI_CREATE_DEMO_USERS","0")=="1"}

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    return (BASE/"SIPRAI_2_9_GO_LIVE.html").read_text(encoding="utf-8")

@app.get("/api/auth/csrf")
def csrf(request:Request):
    return {"csrf":csrf_token(request)}

@app.post("/api/auth/login")
async def login(request:Request):
    require_csrf(request)
    b=await request.json(); u=authenticate(b.get("email",""),b.get("password",""))
    if not u: raise HTTPException(401,"Credenciales inválidas")
    request.session["uid"]=u["id"]; audit(u["id"],"LOGIN")
    return {"ok":True,"user":{"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"]}}

@app.post("/api/auth/logout")
def logout(request:Request):
    mutating(request)
    u=current_user(request)
    if u:audit(u["id"],"LOGOUT")
    request.session.clear(); return {"ok":True}

@app.get("/api/auth/me")
def me(request:Request):
    return {"user":require_user(request)}

@app.get("/api/my/projects")
def my_projects(request:Request):
    u=require_user(request); return {"projects":projects_for_user(u)}

@app.get("/api/project/{project_id}")
def project_get(project_id:str,request:Request):
    require_project(request,project_id)
    return {"project":get_project(project_id),"decisions":project_decisions(project_id),"uploads":list_uploads(project_id)}

@app.post("/api/project/{project_id}")
async def project_save(project_id:str,request:Request):
    mutating(request); u=require_project(request,project_id)
    b=await request.json(); upsert_project(project_id,b); audit(u["id"],"PROJECT_SAVE",project_id)
    return {"ok":True,"project":get_project(project_id)}

@app.post("/api/project/{project_id}/decision")
async def project_decision(project_id:str,request:Request):
    mutating(request); u=require_project(request,project_id)
    code=add_decision(project_id,await request.json()); audit(u["id"],"DECISION_SAVE",project_id,code)
    return {"ok":True,"code":code}

@app.post("/api/project/{project_id}/template/{code}")
async def template_save(project_id:str,code:str,request:Request):
    mutating(request); u=require_project(request,project_id); code=code.upper()
    if code not in FORMS: raise HTTPException(404,"Plantilla no encontrada")
    b=await request.json(); v=save_template(project_id,code,b.get("payload",b),b.get("status","EN CONSTRUCCIÓN"))
    audit(u["id"],"TEMPLATE_SAVE",project_id,f"{code} v{v}")
    return {"ok":True,"template":code,"version":v}

@app.post("/api/project/{project_id}/upload")
async def upload(project_id:str,request:Request,file:UploadFile=File(...)):
    mutating(request); u=require_project(request,project_id); data=await file.read()
    try: rec=store_upload(project_id,u["id"],file.filename,data,file.content_type)
    except ValueError as e: raise HTTPException(400,str(e))
    audit(u["id"],"FILE_UPLOAD",project_id,file.filename); return {"ok":True,"file":rec}

@app.get("/api/project/{project_id}/export")
def export(project_id:str,request:Request):
    u=require_project(request,project_id); audit(u["id"],"PROJECT_EXPORT",project_id)
    data=project_export_bytes(project_id)
    return Response(content=data,media_type="application/json",
      headers={"Content-Disposition":f'attachment; filename="{project_id}_expediente.json"'})

@app.post("/api/siprai/professor/{project_id}")
async def professor(project_id:str,request:Request):
    mutating(request); u=require_project(request,project_id)
    b=await request.json(); msg=(b.get("message") or "").strip()
    if not msg: raise HTTPException(400,"Mensaje vacío")
    audit(u["id"],"SIPRAI_QUERY",project_id,msg[:250])
    return professor_answer(project_id,msg)

@app.get("/api/siprai/trace/{project_id}")
def trace(project_id:str,request:Request,limit:int=50):
    require_project(request,project_id); return {"project_id":project_id,"trace":get_trace(project_id,limit)}

@app.get("/api/siprai/forms")
def api_forms(request:Request):
    require_user(request)
    return [{"code":k,"name":v["name"],"gate":v["gate"],"purpose":v["purpose"]} for k,v in FORMS.items()]

@app.get("/api/siprai/forms/{code}")
def api_form(code:str,request:Request):
    require_user(request); code=code.upper()
    if code not in FORMS: raise HTTPException(404,"Plantilla no encontrada")
    return {"code":code,**FORMS[code]}

@app.get("/api/siprai/knowledge")
def api_knowledge(q:str,request:Request,docs:str=""):
    require_user(request); allowed=[x.strip() for x in docs.split(",") if x.strip()] or None
    return {"results":knowledge_search(q,allowed_docs=allowed,top_k=8)}

@app.post("/api/siprai/readiness/t29")
async def t29(request:Request):
    mutating(request); require_user(request); return evaluate_T29(await request.json())

@app.post("/api/siprai/product-gates")
async def gates(request:Request):
    mutating(request); require_user(request); return product_gate_status(await request.json())

@app.get("/api/admin/users")
def admin_users(request:Request):
    require_professor(request); return {"users":list_users()}

@app.post("/api/admin/users")
async def admin_create_user(request:Request):
    mutating(request); u=require_professor(request); b=await request.json()
    try: uid=create_user(b["email"],b["name"],b["password"],b.get("role","student"))
    except Exception as e: raise HTTPException(400,str(e))
    audit(u["id"],"USER_CREATE",detail=b["email"]); return {"ok":True,"user_id":uid}

@app.post("/api/admin/project/{project_id}/grant/{user_id}")
def admin_grant(project_id:str,user_id:int,request:Request):
    mutating(request); u=require_professor(request); grant_project(project_id,user_id); audit(u["id"],"PROJECT_GRANT",project_id,str(user_id))
    return {"ok":True}

@app.post("/api/admin/project/{project_id}/create")
async def admin_create_project(project_id:str,request:Request):
    mutating(request); u=require_professor(request); b=await request.json()
    upsert_project(project_id,b); grant_project(project_id,u["id"],"owner"); audit(u["id"],"PROJECT_CREATE",project_id)
    return {"ok":True,"project":get_project(project_id)}

@app.get("/api/admin/dashboard")
def admin_dashboard(request:Request):
    u=require_professor(request)
    projects=projects_for_user(u); rows=[]
    for pid in projects:
        p=get_project(pid)
        rows.append({"id":pid,"title":p.get("title",""),"stage":p.get("stage",""),
                     "question":p.get("question",""),"next_action":p.get("next_action",""),
                     "decisions":len(project_decisions(pid)),"uploads":len(list_uploads(pid)),
                     "trace":len(get_trace(pid,500))})
    return {"projects":rows,"users":len(list_users())}

@app.get("/api/admin/audit")
def admin_audit(request:Request,project_id:str|None=None):
    require_professor(request); return {"audit":audit_log(200,project_id)}

@app.post("/api/admin/backup")
def admin_backup(request:Request):
    mutating(request); u=require_professor(request); p=backup_databases(); audit(u["id"],"BACKUP",detail=p.name)
    return {"ok":True,"backup":p.name}


@app.post("/api/auth/change-password")
async def change_password(request:Request):
    mutating(request); u=require_user(request); b=await request.json()
    try:
        ok=update_own_password(u["id"],b.get("current_password",""),b.get("new_password",""))
    except ValueError as e:
        raise HTTPException(400,str(e))
    if not ok: raise HTTPException(400,"Contraseña actual incorrecta")
    audit(u["id"],"PASSWORD_CHANGE")
    return {"ok":True}

@app.post("/api/admin/users/{user_id}/reset-password")
async def admin_reset_password(user_id:int,request:Request):
    mutating(request); u=require_professor(request); b=await request.json()
    new_password=b.get("password") or secrets.token_urlsafe(10)
    try: set_password(user_id,new_password,must_change=True)
    except ValueError as e: raise HTTPException(400,str(e))
    audit(u["id"],"PASSWORD_RESET",detail=str(user_id))
    return {"ok":True,"temporary_password":new_password}

@app.post("/api/admin/users/{user_id}/active")
async def admin_set_active(user_id:int,request:Request):
    mutating(request); u=require_professor(request); b=await request.json()
    set_active(user_id,bool(b.get("active",True)))
    audit(u["id"],"USER_ACTIVE_CHANGE",detail=f"{user_id}:{bool(b.get('active',True))}")
    return {"ok":True}

@app.get("/api/admin/project/{project_id}/members")
def admin_members(project_id:str,request:Request):
    require_professor(request)
    return {"members":project_members(project_id)}

@app.post("/api/admin/project/{project_id}/revoke/{user_id}")
def admin_revoke(project_id:str,user_id:int,request:Request):
    mutating(request); u=require_professor(request); revoke_project(project_id,user_id)
    audit(u["id"],"PROJECT_REVOKE",project_id,str(user_id))
    return {"ok":True}

@app.get("/api/admin/backups")
def admin_backups(request:Request):
    require_professor(request); return {"backups":list_backups()}

@app.get("/api/admin/backups/{name}")
def admin_backup_download(name:str,request:Request):
    require_professor(request)
    p=backup_path(name)
    if not p: raise HTTPException(404,"Backup no encontrado")
    return Response(content=p.read_bytes(),media_type="application/zip",
        headers={"Content-Disposition":f'attachment; filename="{p.name}"'})

@app.get("/api/admin/system-status")
def admin_system_status(request:Request):
    require_professor(request)
    import shutil
    du=shutil.disk_usage(DATA_DIR)
    return {
      "version":"2.9",
      "data_dir":str(DATA_DIR),
      "disk_total_gb":round(du.total/1024**3,2),
      "disk_free_gb":round(du.free/1024**3,2),
      "users":len(list_users()),
      "projects":len(projects_for_user(current_user(request))),
      "backups":len(list_backups()),
      "ai_provider":os.getenv("SIPRAI_AI_PROVIDER","local"),
      "https_only":os.getenv("SIPRAI_HTTPS_ONLY","1")=="1",
      "demo_users":os.getenv("SIPRAI_CREATE_DEMO_USERS","0")=="1",
      "session_secret_configured":os.getenv("SIPRAI_SESSION_SECRET","CHANGE-ME")!="CHANGE-ME"
    }
