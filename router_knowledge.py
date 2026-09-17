
import json,re,unicodedata
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
ROUTER=json.loads((BASE/'config'/'router_00.json').read_text(encoding='utf-8'))

def _norm(s):
    s=unicodedata.normalize("NFD",s.lower())
    return "".join(c for c in s if unicodedata.category(c)!="Mn")

def _hit(text, signal):
    t=_norm(text); s=_norm(signal)
    if s in ("entrevist","bibliometr","cualitativ","mixt"):
        return s in t
    if len(s)<=3 or " " not in s:
        return re.search(r'(?<!\w)'+re.escape(s)+r'(?!\w)',t) is not None
    return s in t

def route_message(message:str):
    t=_norm(message)
    # Explicit product/readiness cases
    if any(x in t for x in ["conclusion","conclusiones","manuscrito","someter","publicar","readiness","producto final"]):
        selected=next(r for r in ROUTER["intent_routes"] if r["intent"]=="producto_aprobacion")
    else:
        matches=[]
        for r in ROUTER["intent_routes"]:
            score=sum(1 for s in r["signals"] if _hit(message,s))
            if score:
                matches.append((score,r))
        matches.sort(key=lambda x:x[0],reverse=True)
        selected=matches[0][1] if matches else next(r for r in ROUTER["intent_routes"] if r["intent"]=="formulacion")

    docs=[]
    for d in selected["primary"]+selected.get("complements",[]):
        if d not in docs: docs.append(d)

    risks=[]
    if any(x in t for x in ["estudiante","subordinado","comunidad","participante"]):
        risks.append("personas")
        for d in ["02","11","15"]:
            if d not in docs: docs.append(d)
    if any(x in t for x in ["dato personal","datos personales","sensible","reidentific"]):
        risks.append("datos_sensibles")
        for d in ["02","11"]:
            if d not in docs: docs.append(d)
    has_ai=any(re.search(r'(?<!\w)'+x+r'(?!\w)',t) for x in ["ia","gpt","rag","agente"])
    if has_ai and any(x in t for x in ["herramienta","memoria","correo","autonomia"]):
        risks.append("agente_ia")
        for d in ["13","02","11","15"]:
            if d not in docs: docs.append(d)
    return {"intent":selected["intent"],"documents":docs,"risks":risks}
