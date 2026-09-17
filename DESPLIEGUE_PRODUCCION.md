# SIPRAI 2.0 — Guía de despliegue

## Opción A — Docker Compose
Adecuada para un servidor propio o VPS.

1. Instale Docker.
2. Copie `.env.production.example` a `.env`.
3. Cambie todas las contraseñas y secretos.
4. Ajuste `DATABASE_URL` para que coincida con Postgres.
5. Ejecute:
   `docker compose up -d --build`
6. Pruebe:
   `http://IP_DEL_SERVIDOR:8000/health`

## Opción B — Render
El repositorio incluye `render.yaml`.

1. Suba el proyecto a GitHub.
2. Cree un Blueprint en Render desde el repositorio.
3. Configure secretos de IA en el panel, nunca en Git.
4. Verifique `/health`.
5. Desactive usuarios demo.

## Opción C — Fly.io
Se incluye `fly.toml` como base.
Debe crear una base Postgres administrada o proporcionar `DATABASE_URL`.

## Base de datos
Producción: PostgreSQL.
Desarrollo local: SQLite sigue funcionando si `DATABASE_URL` no está definido.

## IA
Empiece el piloto con `SIPRAI_AI_PROVIDER=mock`.
Cuando la arquitectura pedagógica esté validada, active un proveedor de IA en entorno privado.

## Dominio
Cuando el sitio esté estable:
- cree subdominio del semillero, por ejemplo `siprai.<dominio-institucional>`
- configure DNS
- active TLS/HTTPS
- publique una política de privacidad y términos de uso académicos

## Backups
Configure backup diario de Postgres y pruebe restauración antes del piloto.
