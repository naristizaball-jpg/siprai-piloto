
import json,re,unicodedata,math
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
PAGES=json.loads((BASE/"knowledge"/"knowledge_pages.json").read_text(encoding="utf-8"))

STOP={"de","la","el","y","en","a","un","una","para","con","que","del","los","las","por","se","o","al","es","como","su","sus"}

def norm(s):
    s=unicodedata.normalize("NFD",s.lower())
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.findall(r"[a-z0-9]{3,}",s)

def search(query, allowed_docs=None, top_k=6):
    qt=[x for x in norm(query) if x not in STOP]
    results=[]
    for p in PAGES:
        if allowed_docs and p["doc"] not in allowed_docs: continue
        toks=norm(p["text"])
        if not toks: continue
        freq={t:toks.count(t) for t in set(qt)}
        hit=sum((1+math.log(freq[t])) if freq[t] else 0 for t in qt)
        phrase=2.0 if query.lower() in p["text"].lower() else 0
        score=hit+phrase
        if score>0:
            snippet=p["text"][:900].replace("\n"," ")
            results.append({"score":round(score,3),"doc":p["doc"],"page":p["page"],"file":p["file"],"snippet":snippet})
    return sorted(results,key=lambda x:x["score"],reverse=True)[:top_k]
