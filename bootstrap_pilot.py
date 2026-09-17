
from app.pilot_store import init, get_user, grant_project, ensure_user
from app.project_store import init as pinit, upsert_project

init();pinit()
prof=ensure_user("profesor@demo.local","Profesor SIPRAI","Profesor123!","professor")
est=ensure_user("estudiante@demo.local","Estudiante Demo","Estudiante123!","student")
upsert_project("PILOTO-001",{
 "title":"Proyecto piloto del semillero",
 "stage":"Descubrimiento",
 "question":"",
 "objective":"",
 "method":"",
 "next_action":"Completar T01 y T02"
})
grant_project("PILOTO-001",prof,"owner")
grant_project("PILOTO-001",est,"member")
print("Piloto creado: PILOTO-001")
print("Profesor: profesor@demo.local / Profesor123!")
print("Estudiante: estudiante@demo.local / Estudiante123!")
