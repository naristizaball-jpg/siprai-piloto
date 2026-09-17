
import os,json,urllib.request,urllib.error

SYSTEM = """Eres SIPRAI 2.5, profesor digital universitario del semillero.
Debes responder SOLO con base en:
1) evidencia documental recuperada de los Documentos 00–15;
2) expediente estructurado del proyecto;
3) decisiones registradas.
No inventes autores, DOI, datos, resultados ni políticas.

REGLAS:
- Conserva la terminología SIPRAI.
- Distingue VERIFICADO, EVIDENCIA DEL PROYECTO, INFERENCIA, HIPÓTESIS y PENDIENTE DE VERIFICACIÓN.
- No declares una puerta superada sin evidencia.
- No confundas aprobación interna SIPRAI con validación editorial/externa.
- Cuando cites evidencia documental, usa exactamente [Dxx p.yy].
- Si la evidencia recuperada no basta, dilo.
- Responde como profesor: explica lo mínimo necesario, identifica faltantes y termina con una próxima acción verificable.
"""

def enabled():
    return os.getenv("SIPRAI_AI_PROVIDER","local").lower()=="openai_compatible" and bool(os.getenv("SIPRAI_AI_API_KEY")) and bool(os.getenv("SIPRAI_AI_MODEL"))

def complete(user_message, context):
    if not enabled():
        return None
    base=os.getenv("SIPRAI_AI_BASE_URL","").rstrip("/")
    if not base:return None
    payload={
      "model":os.getenv("SIPRAI_AI_MODEL"),
      "messages":[
        {"role":"system","content":SYSTEM},
        {"role":"system","content":"CONTEXTO SIPRAI:\n"+json.dumps(context,ensure_ascii=False)},
        {"role":"user","content":user_message}
      ],
      "temperature":0.15
    }
    req=urllib.request.Request(
      base+"/chat/completions",
      data=json.dumps(payload).encode("utf-8"),
      headers={"Authorization":"Bearer "+os.getenv("SIPRAI_AI_API_KEY",""),"Content-Type":"application/json"},
      method="POST"
    )
    try:
        with urllib.request.urlopen(req,timeout=int(os.getenv("SIPRAI_AI_TIMEOUT","60"))) as r:
            d=json.loads(r.read().decode("utf-8"))
        return d["choices"][0]["message"]["content"]
    except Exception:
        return None
