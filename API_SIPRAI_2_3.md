# SIPRAI 2.3 — API Integrada

## Enrutamiento
`GET /api/siprai/route?q=...`

Devuelve:
- intención
- documentos primarios/complementarios
- controles de riesgo

## Recuperación documental
`GET /api/siprai/knowledge?q=...&docs=03,14`

Devuelve hasta 8 páginas relevantes con:
- documento
- página
- archivo
- snippet
- score

## Plantillas
`GET /api/siprai/forms`
`GET /api/siprai/forms/T14`

## Readiness T29
`POST /api/siprai/readiness/t29`

Body JSON con cada control como clave y valor `SI`, `NA` o estado pendiente.

## Puertas P0–P11
`POST /api/siprai/product-gates`

Body:
```json
{"P0":"CUMPLE","P1":"CUMPLE","P2":"PENDIENTE"}
```

## Diagnóstico
`GET /api/siprai/diagnostic`
