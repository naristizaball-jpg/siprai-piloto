
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
    elif re.search(r"\b(ia|agentes?|gpt|rag)\b|inteligencia artificial",low):
        guidance="Si la IA participa materialmente, deben documentarse tarea, modelo/proveedor, datos, permisos, evaluación, supervisión, monitoreo y retiro."
        next_action="Completar T28 y revisar ética/datos antes de avanzar."
    else:
        guidance="Avance solo hasta donde la evidencia permita sostener la decisión. No convierta una propuesta bien redactada en una decisión sustentada sin soporte."
        next_action="Completar la plantilla sugerida con evidencia verificable y registrar la siguiente puerta."

    parts.append("**Orientación del profesor:** " + guidance)
    parts.append("**Estado de la decisión:** " + state + ".")
    parts.append("**Próxima acción:** " + next_action)
    return "\n\n".join(parts), state, next_action

def evidence_followup(messages):
    """Recognize explicit mentions, not semantic adequacy or verified facts."""
    import unicodedata
    fields=(
        ('fuentes', r'trabajos? de clase|entrevist|encuest|documentos?|observacion|bases? de datos',
         '¿Qué fuente concreta consultarás para responder tu pregunta?'),
        ('datos por registrar', r'registr|anot|comparaciones? de cifras|revision(?:es)? de calculos',
         '¿Qué datos concretos registrarás de esas fuentes?'),
        ('acceso o consentimiento', r'autoriz|consentimiento|permiso',
         '¿Cómo solicitarás autorización o consentimiento para acceder a la información?'),
        ('protección de identidad', r'identidad|anonim|seudonim|confidencial|nombres',
         '¿Cómo protegerás la identidad de los participantes en tus registros?'),
        ('instrumento de registro', r'matriz|ficha|guion|guia de entrevista|formulario|tabla de registro',
         '¿Qué instrumento usarás para registrar la información: una matriz de revisión, un guion de entrevista u otro?'),
    )
    status={}
    for message in messages:
        t=''.join(c for c in unicodedata.normalize('NFD',message.lower()) if unicodedata.category(c)!='Mn')
        for clause in re.split(r'[.;\n]+',t):
            for label,pattern,_ in fields:
                if re.search(pattern,clause):
                    # Explicit absence/correction supersedes earlier mentions.
                    negative=bool(re.search(r'\b(no|sin|nunca|todavia no|aun no)\b',clause))
                    status[label]=not negative
    mentioned=[label for label,_,_ in fields if status.get(label)]
    missing=[(label,q) for label,_,q in fields if not status.get(label)]
    recognized=('Aspectos mencionados en tus mensajes: '+', '.join(mentioned)+'.' if mentioned
                else 'Todavía no identifiqué una propuesta concreta de fuentes o registro.')
    if missing:
        label,q=missing[0]
        return (recognized+'\n\nPor precisar: '+label+'.\n'+q,
                'Precisar '+label+' para revisión docente.')
    return (recognized+'\n\nYa mencionaste los cinco aspectos de esta guía. '
            'Reúne tu pregunta y el plan de evidencia en un borrador para revisión docente. '
            'No equivale a aprobar su pertinencia, su suficiencia ni la autorización para recoger datos.',
            'Revisar con el docente la pregunta y el plan de evidencia.')

def local_delimitation(project_id, message):
    """Guided local dialogue; student statements are not verified evidence."""
    import unicodedata
    low=''.join(c for c in unicodedata.normalize('NFD',message.lower())
                if unicodedata.category(c)!='Mn')
    is_question=('?' in message or '¿' in message or re.match(
        r'^\s*(?:(?:mi pregunta(?: de investigacion)?|pregunta)\s*[:：]\s*)?(como|que|cual|cuales|por que|en que medida)\b',low) is not None)
    start=any(x in low for x in ('delimitar','comenzar','empezar')) and ('investig' in low or 'preguntas' in low)
    questions=('1. ¿A quiénes estudiarás y cómo delimitarás ese grupo (por ejemplo, programa, semestre e institución)?\n'
               '2. ¿Qué fenómeno o uso concreto quieres estudiar y qué dificultad o resultado deseas comprender?\n'
               '3. ¿En qué lugar y período harás el estudio, y a qué participantes o trabajos puedes acceder?')
    waiting='DELIMITACIÓN: ESPERANDO RESPUESTAS'
    if start:
        return questions, waiting, 'Responder con 1, 2 y 3 en líneas separadas.'
    if 'salir de delimitacion' in low:
        return ('Has salido de la delimitación. Puedes escribir una nueva consulta.', 'EN CONSTRUCCIÓN', 'Escribir una nueva consulta.')
    history=get_trace(project_id,50)
    draft='DELIMITACIÓN: BORRADOR'
    review='DELIMITACIÓN: REVISIÓN DE PREGUNTA'
    context=None
    if history and history[0]['decision_state'] in (draft,review):
        context=history[0]
    elif (len(history)>1 and history[1]['decision_state']==draft
          and ('?' in message or 'pregunta' in low)):
        # Recover the one-turn interruption caused by the previous version.
        context=history[1]
    if context:
        summary=context['answer'].split('Delimitación preliminar según tus respuestas:\n\n')[-1].split('\n\n')[0]
        if context['decision_state']==review:
            summary=context['answer'].split('Contexto propuesto por ti:\n')[1].split('\n\n')[0]
            if not is_question:
                previous=[]
                for row in history:
                    if row['decision_state']!=review:
                        break
                    # Stop at the latest proposed/reformulated research question.
                    if row['answer'].startswith('Pregunta propuesta para revisión:'):
                        break
                    previous.append(row['message'])
                guidance,next_action=evidence_followup(list(reversed(previous))+[message])
                return ('Evidencia o aclaración propuesta por ti:\n'+message.strip()+
                        '\n\nContexto propuesto por ti:\n'+summary+
                        '\n\n'+guidance+
                        '\n\nEl reconocimiento local se basa en menciones explícitas; confirma si refleja lo que propusiste. '
                        'Todo sigue siendo una propuesta, sin evidencia verificada. '
                        'Para reformular, escribe la pregunta completa. Para cambiar de tema, escribe «salir de delimitación».',
                        review,next_action)
        if not is_question:
            return ('Seguimos revisando tu pregunta de investigación. Escribe la pregunta completa para contrastarla con esta delimitación:\n\n'
                    'Delimitación preliminar según tus respuestas:\n\n'+summary,
                    draft,'Escribir la pregunta completa o «salir de delimitación».')
        verification_guidance=''
        if (re.search(r'\bia\b|inteligencia artificial',low)
                and re.search(r'\b(?:verific\w*|contrast\w*|comprob\w*|comprueb\w*|valid\w*)\b',low)):
            verification_guidance=(
                'Para precisar qué significa verificar los datos y las respuestas de la IA, '
                'puedes observar si se consultan fuentes originales, se comparan cifras o se revisan cálculos. '
                'Son ejemplos de posibles criterios, no resultados del estudio.\n\n')
        return ('Pregunta propuesta para revisión:\n'+message.strip()+
                '\n\nContexto propuesto por ti:\n'+summary+
                '\n\nRevisión orientada en modo local: contrasta tu pregunta con los participantes, el fenómeno, el lugar y el período que propusiste. '
                'Esta guía no comprueba automáticamente la coherencia semántica ni aprueba la pregunta. '
                'Si cambiaste alguno de esos elementos, explica el cambio antes de avanzar.\n\n'+
                verification_guidance+
                '¿Qué evidencia concreta necesitarías recoger para responder tu pregunta? '
                'Puedes reformular la pregunta en otro mensaje. Para cambiar de tema, escribe «salir de delimitación».',
                review,'Precisar la evidencia necesaria y revisar la pregunta con el docente.')
    if not history or history[0]['decision_state']!=waiting:
        return None
    matches=list(re.finditer(r'(?:^|\n)\s*([123])[.)]\s*',message))
    responses={}
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(message)
        responses[m.group(1)]=message[m.end():end].strip()
    if len(matches)!=3 or set(responses)!={'1','2','3'} or any(not x for x in responses.values()):
        return ('Para continuar, responde las tres preguntas en un solo mensaje, con 1, 2 y 3 en líneas separadas. '
                'Para cambiar de tema, escribe «salir de delimitación».\n\n'+questions,
                waiting, 'Completar las tres respuestas numeradas.')
    summary='\n'.join(label+responses[n] for n,label in (
        ('1','Participantes propuestos: '),('2','Uso y dificultad por estudiar: '),
        ('3','Lugar, período y acceso propuestos: ')))
    return ('Delimitación preliminar según tus respuestas:\n\n'+summary+
            '\n\nEstos datos son propuestas tuyas; todavía no constituyen evidencia verificada. '
            'Antes de elegir metodología, redacta una pregunta que vincule los participantes, '
            'el uso concreto y el contexto indicado. Si algún aspecto sigue sin definir, indícalo.\n\n'
            '¿Cuál sería tu pregunta de investigación con esta delimitación?',
            'DELIMITACIÓN: BORRADOR', 'Redactar la pregunta para revisión docente.')

def answer(project_id, message):
    route=route_message(message)
    allowed=[d for d in route["documents"] if re.fullmatch(r"\d{2}",str(d))]
    evidence=knowledge_search(message, allowed_docs=allowed or None, top_k=6)
    templates=activate_templates(message)
    deterministic,state,next_action=build_answer(message,route,evidence,templates)
    local=local_delimitation(project_id,message) if os.getenv('SIPRAI_AI_PROVIDER','local')=='local' else None
    if local:
        deterministic,state,next_action=local
        templates=[]
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
