
import json, re, os, sqlite3
from pathlib import Path
from .router_knowledge import route_message
from .knowledge_search import search as knowledge_search
from .llm_adapter import complete as llm_complete
from .project_store import get_project, decisions as get_decisions

BASE=Path(__file__).resolve().parent.parent
FORMS=json.loads((BASE/"config"/"forms_T01_T30.json").read_text(encoding="utf-8"))
ACT=json.loads((BASE/"config"/"template_activation.json").read_text(encoding="utf-8"))
from .paths import DATA_DIR
DB=DATA_DIR/"siprai_trace.db"

def init_trace_db():
    con=sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS trace(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        message TEXT,
        intent TEXT,
        documents TEXT,
        pages TEXT,
        templates TEXT,
        decision_state TEXT,
        answer TEXT
    )""")
    con.commit(); con.close()

def activate_templates(message):
    import unicodedata
    def norm(s):
        s=unicodedata.normalize("NFD",s.lower())
        return "".join(c for c in s if unicodedata.category(c)!="Mn")
    t=norm(message)
    out=[]
    for key,codes in ACT.items():
        k=norm(key)
        # Word boundary for normal nouns; prefix for methodological stems
        if k in ("ia","gpt","rag"):
            hit=re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',t) is not None
        elif k in ("entrevista","bibliometr","cualitativ","mixt"):
            hit=k in t
        else:
            hit=re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',t) is not None if " " not in k else k in t
        if hit:
            out.extend(codes)
    if any(x in t for x in ["conclusion","conclusiones","manuscrito","someter","publicar"]):
        out.append("T29")
    return list(dict.fromkeys(out))

def decision_state(message, evidence_results):
    import unicodedata
    t=unicodedata.normalize("NFD",message.lower())
    t="".join(c for c in t if unicodedata.category(c)!="Mn")
    unsupported_patterns=[
        "inventa","inventame","sin articulos","no tenga articulos","no tengo articulos",
        "sin resultados","no tengo resultados","todavia no tengo resultados"
    ]
    if any(x in t for x in unsupported_patterns):
        return "PENDIENTE / NO SUSTENTABLE"
    if evidence_results:
        return "EN VALIDACIÓN"
    return "EN CONSTRUCCIÓN"

def citation_label(result):
    return f"Documento {result['doc']}, p. {result['page']}"

def build_answer(message, route, evidence, templates):
    state=decision_state(message,evidence)
    parts=[]
    parts.append(f"**Ruta SIPRAI:** {route['intent']}.")
    parts.append("**Documentos activados:** " + ", ".join(route["documents"]) + ".")
    if route.get("risks"):
        parts.append("**Controles transversales:** " + ", ".join(route["risks"]) + ".")
    if templates:
        parts.append("**Plantillas sugeridas:** " + ", ".join(templates) + ".")
    if evidence:
        ev=[]
        for r in evidence[:3]:
            sn=re.sub(r"\s+"," ",r["snippet"]).strip()
            if len(sn)>330: sn=sn[:327]+"..."
            ev.append(f"- {citation_label(r)}: {sn}")
        parts.append("**Base documental recuperada:**\n" + "\n".join(ev))
    else:
        parts.append("**Base documental recuperada:** no se encontró un pasaje suficientemente coincidente; la recomendación queda pendiente de verificación documental.")

    low=message.lower()
    if "conclus" in low and ("no tengo resultados" in low or "sin resultados" in low):
        guidance="No corresponde construir conclusiones científicas sin resultados trazables. Primero deben existir resultados vinculados con objetivos y evidencia."
        next_action="Registrar o analizar resultados antes de trabajar conclusiones."
    elif ("vacío" in low or "vacio" in low) and not evidence:
        guidance="No debe declararse un vacío solo por intuición o por una búsqueda limitada. Primero documente búsqueda, literatura cercana y qué permanece abierto."
        next_action="Completar búsqueda reproducible y T02 con evidencia."
    elif "metod" in low:
        guidance="La metodología debe derivarse de la pregunta y de la evidencia necesaria, no elegirse por etiqueta o preferencia."
        next_action="Definir qué evidencia respondería la pregunta y activar la ruta metodológica correspondiente."
    elif "revista" in low or "publicar" in low or "someter" in low:
        guidance="La revista puede orientar desde temprano, pero el readiness interno no equivale a aceptación editorial externa."
        next_action="Revisar T29 y requisitos vigentes de la revista objetivo."
    elif "ia" in low or "agente" in low or "gpt" in low or "rag" in low:
        guidance="Si la IA participa materialmente, deben documentarse tarea, modelo/proveedor, datos, permisos, evaluación, supervisión, monitoreo y retiro."
        next_action="Completar T28 y revisar ética/datos antes de avanzar."
    else:
        guidance="Avance solo hasta donde la evidencia permita sostener la decisión. No convierta una propuesta bien redactada en una decisión sustentada sin soporte."
        next_action="Completar la plantilla sugerida con evidencia verificable y registrar la siguiente puerta."

    parts.append("**Orientación del profesor:** " + guidance)
    parts.append("**Estado de la decisión:** " + state + ".")
    parts.append("**Próxima acción:** " + next_action)
    return "\n\n".join(parts), state, next_action

def answer(project_id, message):
    route=route_message(message)
    allowed=[d for d in route["documents"] if re.fullmatch(r"\d{2}",str(d))]
    evidence=knowledge_search(message, allowed_docs=allowed or None, top_k=6)
    templates=activate_templates(message)
    deterministic,state,next_action=build_answer(message,route,evidence,templates)
    project=get_project(project_id)
    decision_rows=get_decisions(project_id,20)
    grounded_context={
        "route":route,
        "templates":templates,
        "project":project,
        "decisions":decision_rows,
        "evidence":[
            {"citation":f"[D{r['doc']} p.{r['page']}]","doc":r["doc"],"page":r["page"],"snippet":r["snippet"]}
            for r in evidence[:6]
        ],
        "required_decision_state":state,
        "required_next_action":next_action
    }
    ai=llm_complete(message,grounded_context)
    ans=ai if ai else deterministic

    init_trace_db()
    con=sqlite3.connect(DB)
    con.execute(
        "INSERT INTO trace(project_id,message,intent,documents,pages,templates,decision_state,answer) VALUES(?,?,?,?,?,?,?,?)",
        (str(project_id),message,route["intent"],json.dumps(route["documents"],ensure_ascii=False),
         json.dumps([{"doc":r["doc"],"page":r["page"]} for r in evidence],ensure_ascii=False),
         json.dumps(templates,ensure_ascii=False),state,ans)
    )
    con.commit(); con.close()
    return {
        "answer":ans,
        "route":route,
        "templates":templates,
        "evidence":[{"doc":r["doc"],"page":r["page"],"file":r["file"],"snippet":r["snippet"],"score":r["score"]} for r in evidence],
        "decision_state":state,
        "next_action":next_action
    }

def get_trace(project_id,limit=50):
    init_trace_db()
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    rows=con.execute("SELECT * FROM trace WHERE project_id=? ORDER BY id DESC LIMIT ?",(str(project_id),limit)).fetchall()
    con.close()
    out=[]
    for r in rows:
        d=dict(r)
        for k in ("documents","pages","templates"):
            try:d[k]=json.loads(d[k])
            except:pass
        out.append(d)
    return out
