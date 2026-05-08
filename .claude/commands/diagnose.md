---
description: Diagnóstico de un síntoma operativo (empalme, unwinder, dancer, safety, etc.) usando agent.ask determinístico
argument-hint: <síntoma> [L5X]
---

# /diagnose — Diagnóstico operativo determinístico

Síntoma a diagnosticar: **$ARGUMENTS**

Si el síntoma no incluye un L5X, usar `parque_l5x/CINTA_LAMINADA_M2_2024.L5X` por default. Si menciona L5X o nombre del proyecto, cargar ese L5X.

## Instrucciones

1. Cargar el L5X correspondiente con `load_project()`.
2. Invocar `project.ask("$ARGUMENTS")` — esto es el agent determinístico v0.7.
3. Mostrar al usuario:
   - El `pattern` reconocido por el agente
   - La `confidence`
   - El `answer` (markdown estructurado)
   - Lista de `tools_called` para trazabilidad
4. Si `confidence < 0.5`, notar al usuario que el agent no reconoció el patrón con alta confianza y ofrecer razonar manualmente con el toolkit.
5. Si el síntoma es de empalme y `confidence ≥ 0.7`, además ofrecer trazar la cadena causal con `find_causal_path` para los tags clave del patrón.

## Determinismo

Esta invocación es reproducible: misma `(L5X, síntoma)` retorna el mismo output. Para verificar, ejecutar 2 veces y comparar.

## Patrones reconocidos por el agent

- `splice_diagnosis` — empalme/splice/CTC
- `unwinder_diagnosis` — unwinder/debobinador
- `dancer_diagnosis` — dancer/danzarín/tensión
- `safety_overview` — safety/E-stop/GuardLogix
- `dead_code_audit` — código muerto/huérfanos
- `smell_audit` — smells/best practices
- `motion_overview` — motion/ejes
- `general_health` — salud general
