# Integración de IA

## Diseño
El backend combina:
1. Prompt maestro de SIPRAI
2. Contexto estructurado del proyecto
3. Mensaje actual del estudiante

## Contexto recuperado
- datos del proyecto
- vacío / problema / pregunta
- objetivos
- metodología
- últimas búsquedas
- artículos registrados
- decisiones
- manuscrito

## Modo local
Si no hay API configurada, SIPRAI usa reglas pedagógicas.
Esto permite probar el flujo sin exponer claves.

## Modo IA real
El adaptador usa un endpoint compatible con Chat Completions.
La arquitectura puede reemplazarse por otro proveedor sin modificar la base de datos ni la interfaz.

## Recomendación para producción
- mover autenticación a un sistema robusto
- usar Postgres
- almacenar documentos en object storage
- usar RAG para recuperar fragmentos de artículos
- registrar auditoría de respuestas y decisiones
- aplicar cuotas y límites de uso
