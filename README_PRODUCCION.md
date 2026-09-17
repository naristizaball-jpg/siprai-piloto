# SIPRAI 2.0 — Paquete de Producción

Esta versión está preparada para pasar de demo local a despliegue en internet.

Incluye:
- Dockerfile
- Docker Compose
- PostgreSQL por variable de entorno
- endpoint `/health`
- configuración base para Render
- configuración base para Fly.io
- ejemplo de variables de producción
- lista de seguridad
- plan de piloto con estudiantes

## Importante
Esto es una base de producción, no una certificación de seguridad institucional.
Antes de usar datos reales de estudiantes deben implementarse autenticación robusta, recuperación de contraseña, CSRF, auditoría y política institucional de privacidad.
