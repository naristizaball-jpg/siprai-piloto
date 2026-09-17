# SIPRAI 2.9 — Paso a paso para publicar el piloto

## Fase A — Hosting
1. Crear un servicio web Docker.
2. Montar almacenamiento persistente en `/data`.
3. Configurar HTTPS.
4. Definir secretos.

## Fase B — Secretos mínimos
- SIPRAI_SESSION_SECRET
- SIPRAI_ADMIN_EMAIL
- SIPRAI_ADMIN_PASSWORD
- SIPRAI_CREATE_DEMO_USERS=0
- SIPRAI_HTTPS_ONLY=1
- SIPRAI_DATA_DIR=/data

## Fase C — Primera entrada
1. Abrir la URL.
2. Ingresar con el profesor inicial.
3. Cambiar la contraseña.
4. Revisar `/health`.
5. Crear backup.
6. Crear 2–3 proyectos.
7. Crear 5–10 estudiantes.
8. Asignarlos.

## Fase D — Pilotaje
- No usar datos sensibles reales en la primera ronda.
- Usar T01–T05, literatura, T25 y T29 como núcleo.
- Revisión docente al menos cada 2–3 días.
- Registrar problemas de navegación y de orientación pedagógica.

## Fase E — Decisión
Al final de dos semanas:
- continuar;
- ajustar;
- ampliar;
- detener.
