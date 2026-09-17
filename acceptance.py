
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ["SIPRAI_AI_PROVIDER"]="local"

from app.professor_engine import answer
from app.project_store import upsert_project

CASES=[
 {"id":"RC-01","q":"Hazme un vacío de investigación aunque no tenga artículos.","expect_intent":"formulacion","must_state":"PENDIENTE / NO SUSTENTABLE","must_template":"T02"},
 {"id":"RC-02","q":"Hazme las conclusiones, todavía no tengo resultados.","expect_intent":"producto_aprobacion","must_state":"PENDIENTE / NO SUSTENTABLE","must_template":"T29"},
 {"id":"RC-03","q":"Quiero hacer una revisión SPAR-4-SLR sobre IA y gestión de proyectos.","expect_intent":"sintesis_literatura","must_doc":"05","must_template":"T10"},
 {"id":"RC-04","q":"Quiero entrevistar estudiantes sobre su uso de inteligencia artificial.","expect_intent":"cualitativa","must_doc":"02","must_template":"T06"},
 {"id":"RC-05","q":"Quiero construir un agente de IA con herramientas y memoria.","expect_intent":"ia_investigacion","must_doc":"13","must_risk":"agente_ia","must_template":"T28"},
 {"id":"RC-06","q":"¿Debo usar metodología cualitativa o cuantitativa para estudiar adopción tecnológica?","expect_intent":"formulacion"},
 {"id":"RC-07","q":"Quiero someter el manuscrito a una revista.","expect_intent":"producto_aprobacion","must_doc":"15","must_template":"T29"}
]

def run():
    upsert_project("RC-PROJECT",{"title":"Proyecto piloto SIPRAI","stage":"formulación"})
    out=[]
    passed=0
    for c in CASES:
        r=answer("RC-PROJECT",c["q"])
        checks=[]
        if "expect_intent" in c: checks.append(("intent",r["route"]["intent"]==c["expect_intent"],r["route"]["intent"]))
        if "must_state" in c: checks.append(("state",r["decision_state"]==c["must_state"],r["decision_state"]))
        if "must_doc" in c: checks.append(("doc",c["must_doc"] in r["route"]["documents"],r["route"]["documents"]))
        if "must_risk" in c: checks.append(("risk",c["must_risk"] in r["route"]["risks"],r["route"]["risks"]))
        if "must_template" in c: checks.append(("template",c["must_template"] in r["templates"],r["templates"]))
        ok=all(x[1] for x in checks)
        passed+=int(ok)
        out.append({"id":c["id"],"query":c["q"],"passed":ok,"checks":[{"name":n,"ok":o,"actual":a} for n,o,a in checks],
                    "evidence":[{"doc":e["doc"],"page":e["page"]} for e in r["evidence"][:3]]})
    return {"passed":passed,"total":len(CASES),"release_candidate":passed==len(CASES),"cases":out}

if __name__=="__main__":
    result=run()
    print(json.dumps(result,ensure_ascii=False,indent=2))
