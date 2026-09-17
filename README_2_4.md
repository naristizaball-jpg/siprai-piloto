# SIPRAI 2.4 — Profesor Integrado

Esta versión ejecuta el ciclo completo:

1. recibe una consulta;
2. aplica el router del Documento 00;
3. agrega controles de alto riesgo;
4. busca páginas relevantes en los 16 documentos;
5. activa plantillas T01–T30;
6. construye una orientación pedagógica;
7. asigna estado de decisión;
8. propone próxima acción;
9. guarda la traza en SQLite.

## Ejecutar
Windows: `run_windows.bat`

Luego:
`http://127.0.0.1:8000`

## Endpoints
- POST `/api/siprai/professor/{project_id}`
- GET `/api/siprai/trace/{project_id}`
- GET `/api/siprai/route?q=...`
- GET `/api/siprai/knowledge?q=...&docs=...`
- GET `/api/siprai/forms`
- GET `/api/siprai/forms/T28`
- POST `/api/siprai/readiness/t29`
- POST `/api/siprai/product-gates`

## Limitación deliberada
El generador de respuesta actual es determinista y pedagógico. La siguiente capa conecta un modelo de IA real usando exactamente el contexto recuperado, sin alterar router, evidencia, plantillas o trazabilidad.
