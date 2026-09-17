
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
FORMS=json.loads((BASE/"config"/"forms_T01_T30.json").read_text(encoding="utf-8"))
GATES=json.loads((BASE/"config"/"product_gates_P0_P11.json").read_text(encoding="utf-8"))

def evaluate_checklist(values:dict, checks:list):
    rows=[]
    blockers=[]
    for check in checks:
        v=values.get(check,"PENDIENTE")
        rows.append({"check":check,"status":v})
        if v not in ("SI","SÍ","NA","CUMPLE","TRUE",True):
            blockers.append(check)
    return {"rows":rows,"blockers":blockers,"ready":not blockers}

def evaluate_T29(values:dict):
    r=evaluate_checklist(values,FORMS["T29"]["checks"])
    if r["ready"]:
        r["decision"]="READY"
    elif len(r["blockers"])<=3:
        r["decision"]="REVISE"
    else:
        r["decision"]="HOLD"
    return r

def product_gate_status(gate_values:dict):
    out=[]
    blocked=False
    for g in GATES:
        status=gate_values.get(g["code"],"PENDIENTE")
        out.append({**g,"status":status})
        if status not in ("CUMPLE","NA"):
            blocked=True
    return {"gates":out,"internal_ready":not blocked,
            "notice":"Aprobación SIPRAI es interna y no equivale a aceptación editorial o validación externa."}
