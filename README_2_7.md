# SIPRAI 2.7 — Piloto Académico

## Qué agrega
- inicio de sesión
- roles profesor/estudiante
- control de acceso por proyecto
- creación de estudiantes por el profesor
- asignación de proyectos
- carga controlada de archivos
- expediente exportable JSON
- panel docente
- auditoría de acciones
- backup de bases SQLite
- sesiones firmadas

## Primera ejecución
Windows: `run_windows.bat`

Luego abra:
`http://127.0.0.1:8000`

### Cuentas locales de demostración
Profesor:
`profesor@demo.local` / `Profesor123!`

Estudiante:
`estudiante@demo.local` / `Estudiante123!`

Proyecto:
`PILOTO-001`

## Importante
Estas credenciales son exclusivamente para un piloto local. Antes de desplegar en Internet:
- desactive usuarios demo;
- cambie `SIPRAI_SESSION_SECRET`;
- active HTTPS;
- use una base de datos y backups de producción;
- revise privacidad y tratamiento de datos;
- implemente recuperación de contraseña y protección CSRF/rate limiting si se abre públicamente.
