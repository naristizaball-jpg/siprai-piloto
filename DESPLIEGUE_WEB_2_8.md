# SIPRAI 2.8 — Despliegue web del piloto

## Opción recomendada para el primer piloto
Un único servidor/contenedor con disco persistente.

La aplicación usa SQLite de forma deliberada para esta cohorte inicial. No escalar horizontalmente a varias instancias todavía.

## Variables obligatorias
- `SIPRAI_SESSION_SECRET`
- `SIPRAI_ADMIN_EMAIL`
- `SIPRAI_ADMIN_PASSWORD`
- `SIPRAI_DATA_DIR=/data`
- `SIPRAI_HTTPS_ONLY=1`
- `SIPRAI_CREATE_DEMO_USERS=0`

## Render
El paquete incluye `render.yaml`.
1. Crear nuevo servicio desde repositorio.
2. Adjuntar disco persistente `/data`.
3. Cargar correo y contraseña inicial del profesor como secretos.
4. Verificar `/health`.
5. Ingresar como profesor.
6. Crear estudiantes y proyectos.

## Docker local
1. Copiar `.env.example` a `.env`.
2. Completar secretos.
3. `docker compose up --build`
4. Abrir `http://localhost:8000`.

## Seguridad incorporada
- cookies de sesión firmadas
- `Secure` cuando HTTPS está activo
- CSRF para operaciones de escritura
- limitador básico por IP
- cabeceras de seguridad
- control de acceso por proyecto
- auditoría
- límite de 10 MB y lista permitida de extensiones
- usuarios demo desactivables
- datos persistentes fuera del código

## Límites del piloto
- Rate limit en memoria: adecuado a una sola instancia.
- SQLite: adecuado a cohorte pequeña y una instancia.
- No existe recuperación de contraseña por correo.
- No existe SSO institucional.
- Antes de uso institucional amplio: PostgreSQL, almacenamiento de objetos, SSO, backup externo, observabilidad y revisión formal de privacidad.
