
import os,time,secrets,collections
from fastapi import Request, HTTPException

WINDOW=60
LIMIT=int(os.getenv("SIPRAI_RATE_LIMIT_PER_MINUTE","120"))
_hits=collections.defaultdict(collections.deque)

def csrf_token(request:Request):
    token=request.session.get("csrf")
    if not token:
        token=secrets.token_urlsafe(32)
        request.session["csrf"]=token
    return token

def require_csrf(request:Request):
    expected=request.session.get("csrf")
    supplied=request.headers.get("X-CSRF-Token")
    if not expected or not supplied or not secrets.compare_digest(expected,supplied):
        raise HTTPException(403,"CSRF token inválido")

def rate_limit(request:Request):
    # Single-instance pilot limiter. For multi-instance production use Redis/gateway.
    ip=request.client.host if request.client else "unknown"
    now=time.time()
    q=_hits[ip]
    while q and q[0] < now-WINDOW:
        q.popleft()
    if len(q)>=LIMIT:
        raise HTTPException(429,"Demasiadas solicitudes; intente de nuevo en un minuto")
    q.append(now)

SECURITY_HEADERS={
    "X-Content-Type-Options":"nosniff",
    "X-Frame-Options":"DENY",
    "Referrer-Policy":"same-origin",
    "Permissions-Policy":"camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy":"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
}
