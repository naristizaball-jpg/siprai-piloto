# SIPRAI 2.0 — Seguridad mínima para producción

Antes de permitir acceso a estudiantes reales:

1. Desactive usuarios demo:
   `SIPRAI_CREATE_DEMO_USERS=false`
2. Use PostgreSQL, no SQLite.
3. Configure HTTPS obligatorio.
4. Use un secreto largo y aleatorio.
5. Nunca incluya claves API en el repositorio.
6. Añada recuperación/cambio de contraseña.
7. Añada CSRF para formularios sensibles.
8. Añada límites de intentos de login.
9. Registre auditoría de cambios críticos.
10. Configure backups automáticos de Postgres.
11. Defina política de retención y eliminación de datos.
12. No cargue información personal sensible innecesaria.
13. Revise requisitos institucionales de protección de datos aplicables en Colombia antes del piloto.
14. Para archivos de investigación, use almacenamiento de objetos con permisos por proyecto.
15. Implemente cuotas de IA y búsqueda externa para evitar abuso/costos inesperados.

## Autenticación
La autenticación incluida es suficiente para demostración técnica, NO para producción institucional.
Para un piloto real conviene usar un proveedor robusto de identidad o implementar sesiones firmadas y recuperación segura de credenciales.
