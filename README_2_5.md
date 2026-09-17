# SIPRAI 2.5 — IA Grounded

## Ciclo
Mensaje → Router 00 → documentos → recuperación por página → expediente → decisiones → plantillas → profesor → traza.

## Modos
### `local`
No requiere API. Usa el profesor determinista construido en SIPRAI.

### `openai_compatible`
Usa un endpoint Chat Completions compatible configurado por variables de entorno.
El modelo recibe solo contexto estructurado y evidencia recuperada.

## Citación interna
La evidencia se identifica como `[Dxx p.yy]`.

## Base de proyecto
SQLite:
- proyecto
- decisiones
- versiones de plantillas
- trazas de conversación

## Principio
El modelo de IA no es la fuente de verdad; es la capa pedagógica encima de la base documental y del expediente.
