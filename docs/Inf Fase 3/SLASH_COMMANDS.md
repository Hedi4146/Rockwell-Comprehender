# Slash Commands — Claude Code (v0.7.2 Sprint 10)

**Fecha:** 2026-05-07
**Sprint:** 10 (Formalización del agente)
**Subtarea:** v0.7.2

---

## Resumen

Cinco slash commands disponibles en Claude Code dentro de este repo. Cada uno formaliza un **flujo conversacional reproducible** sobre el toolkit `rockwell_comprehender`, invocando el agente determinístico (`agent.ask`) y/o las APIs directas según corresponda.

Los archivos están en `.claude/commands/<name>.md`. Se invocan con `/<name>` desde Claude Code dentro de la raíz del proyecto.

---

## Comandos disponibles

### `/diagnose <síntoma> [L5X]`

Diagnóstico operativo determinístico. El síntoma se mapea automáticamente a uno de 8 patrones del agente (`splice_diagnosis`, `unwinder_diagnosis`, `dancer_diagnosis`, `safety_overview`, `dead_code_audit`, `smell_audit`, `motion_overview`, `general_health`).

**Ejemplos:**
- `/diagnose problema en empalme`
- `/diagnose falla del unwinder`
- `/diagnose código muerto en parque_l5x/AQL_M2.L5X`

**Output:** `pattern` reconocido, `confidence`, `answer` consolidado, `tools_called` para trazabilidad.

---

### `/audit [L5X]`

Auditoría completa de un L5X. Combina:
- Identidad + KPIs
- Mapa Mental (primeras 60 líneas)
- Program inference (roles funcionales)
- Smells por severidad + top 10 reglas
- Motion patterns + top high-conf
- Tag dictionary (distribución por rol)

**Ejemplos:**
- `/audit` (default CINTA)
- `/audit parque_l5x/CPPIM_BD800_1.L5X`

**Output:** informe estructurado consolidado. Opcional: exportar a TDR HTML / Explorer HTML.

---

### `/compare <L5X_old> <L5X_new>`

Comparación automática entre 2 proyectos via `diff_projects`. Reporta added/removed/changed por categoría (modules, AOIs, UDTs, programs, routines, tags, tasks).

**Ejemplos:**
- `/compare parque_l5x/CINTA_LAMINADA_M2_2024.L5X parque_l5x/AQL_M2.L5X`
- `/compare` (asistente pide los 2 paths)

**Output:** summary `+N/-M/~K` por categoría + tabla detallada. Si diff es grande, opción de exportar a Markdown.

---

### `/explain <target> [L5X]`

Explicación de un tag, AOI o program específico. El agente decide automáticamente el tipo de identifier y aplica el handler correspondiente.

**Ejemplos:**
- `/explain AHT_CtcSplicer`
- `/explain Data.HmiNewDiameter`
- `/explain MainProgram parque_l5x/CINTA_LAMINADA_M2_2024.L5X`

**Output:** ficha técnica con datatype/scope (tags), parameters/routines (AOIs), role inferido + evidence (programs).

---

### `/health [L5X]`

Reporte de salud general (`general_health` del agente).

**Ejemplos:**
- `/health`
- `/health parque_l5x/AQL_M2.L5X`

**Output:** KPIs + smells por severidad + motion overview + program roles. Resalta críticos (smells high, programs sin task).

---

## Determinismo

Los 5 commands invocan APIs determinísticas del toolkit (no LLM). Misma `(L5X, args)` retorna mismo output. Verificable con `agent.ask` retornando el mismo `AgentResponse` en runs sucesivos.

## Auditabilidad

Cuando se ejecutan via Claude Code, las herramientas que Claude llama quedan registradas en el transcript. Para trazabilidad estructurada (JSONL persistente), activar audit logger v0.7.3 vía `ROCKWELL_AUDIT=1` o `load_project(..., audit=True)`.

## Stack mínimo

Estos commands NO requieren librerías nuevas — son archivos `.md` con prompt template que invoca el toolkit existente (DT-008 preservado).
