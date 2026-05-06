# 05 · AUDITORÍA DE CAPACIDADES — 2026-05-03

**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Auditor:** Claude Code (sesión 2026-05-03)
**Propósito:** Inventario honesto del estado actual del proyecto `rockwell-comprehender` versus los criterios de "ingeniero senior + consultor experto Rockwell" definidos en `00_Vision_y_Roadmap.md`. Base para decidir próximas inversiones.

---

## TL;DR

Estado global: **~83%** de las capacidades del Vision construidas, operativas, y validadas empíricamente. Caso empalme cerrado 2026-05-03 (3 turnos efectivos).

**Lo que falta, en orden de impacto:**
1. **Cobertura general logix en `instruction_library`** — hoy 100% motion (17 entries) pero 0% scaffolding RLL (XIC/MOV/TON/EQU/etc.). Limita interpretación de código en ladder estándar.
2. **Composición motion (patterns nivel-2)** — átomos curados pero composiciones tipo "MAJ→MAS encadenado = control de empalme estilo Diatec" no detectables.
3. **Validación cruzada del tracer en AQL_M2** (TODO menor).

**Próximo paso:** decisión del owner entre Propuestas C/E o validación AQL_M2 (ver sec 7). v0.1 cerrado el 2026-05-03.

---

## 1. Inventario del paquete

### Módulos implementados (LOC = líneas de código)

| Módulo | LOC | Capa Vision | Estado |
|--------|----:|-------------|--------|
| `loader.py` | 949 | Carga + Modelo | ✅ Completo, validado contra 3 L5X |
| `model.py` | 1244 | Modelo canónico + Project class | ✅ Completo (incluye API tracer) |
| `mapamental.py` | 780 | Capa 1 (Mapa Mental) | ✅ Completo, validado |
| `tracer.py` | 551 | Capa 4 (trace causal v0.2) | ✅ Completo (writers_of, readers_of, trace_back/forward, find_causal_path) |
| `patterns.py` | 330 | Capa C v0.3 (dominios funcionales) | ✅ Completo (zonas, drives, safety, HMI) |
| `tokenizer/rll_tokenizer.py` | 252 | Soporte tracer RLL | ✅ Completo |
| `tokenizer/st_tokenizer.py` | 192 | Soporte tracer ST | ✅ Completo (closure de gap CPPIM) |
| `instruction_library/` | 910 | Capa D (knowledge curado) | ✅ 17 entries (3 safety + 14 motion = 100% parque motion) |
| `fault_code_library/` | 690 | Capa D extendida | ⏸ PARKED — 18 K5700 pilot, espera caso real |
| `reporters/markdown.py` | 304 | Output | ✅ Completo |
| `reporters/excel.py` | 307 | Output (BoM multi-sheet) | ✅ Completo |
| `reporters/mermaid.py` | 305 | Output (topology, iotree, tasks) | ✅ Completo |
| `reporters/html_explorer.py` | **1741** | Output visual (spec doc 06) | ✅ **CONSTRUIDO** — Controller Organizer interactivo |

**Total: ~9000 LOC sustanciales del paquete.** Mucho más de lo que el HANDOFF v0.1 originalmente describe — el proyecto avanzó a ~v0.3.x sin renumerar.

### Lo que NO existe (intencionalmente, per DT-009)

| Módulo planeado | Estado | Razón |
|----------------|--------|-------|
| `tokenizer/fbd_tokenizer.py` | ❌ Pendiente | Bajo uso en parque (CPPIM 2 FBD, otros 0). RLL+ST cubren >95% |
| `migration_library/` (K6000↔K5700) | ❌ Pendiente | Espera confirmación de N2 como caso activo |
| `tests/` formales (pytest) | ❌ Pendiente | Validación se hizo contra L5X reales |

### Stack actual (cumple DT-008)

```python
dependencies = ["openpyxl"]  # única dependencia más allá de stdlib
```

`l5x` library eliminada en DT-010. Sin torch, sin faiss, sin embeddings, sin servidores externos. ✅

---

## 2. Las 8 capacidades del Vision — score actual con evidencia

| # | Capacidad | Pre-plan | **Actual** | Evidencia |
|---|-----------|---------:|-----------:|-----------|
| #1 | **Lectura estructural L5X** | 85% | **95%** | Loader + model maduros. Validado contra CINTA (1.2 MB v20.01), AQL (2.9 MB v20.12), CPPIM (~15 MB v33). 12-44 modules, 26-57 AOIs, 17-47 routines parseados sin fallo |
| #2 | **Localizar por dominio funcional** | 70% | **80%** | `patterns.py` Capa C detecta zonas (UWM01, MDP01, etc.), categorías de drives, dual-channel safety (CROUT/DCS_*), roles HMI. `mapamental` infiere función de ejes vía tag/AOI naming |
| #3 | **Interpretar instrucciones individuales** | 60% | **75%** | `instruction_library` con 17 entries: 3 safety (CROUT, DCI_STOP, DCI_STOP_TEST_LOCK) + 14 motion (MAJ/MAG/MAS/MAH/MAOC/MAM/MSO/MSF/MAFR/MASR/MAPC/MAR/MCCP/MCSV). **Cubre 100% del motion del parque actual.** Falta general logix RLL (XIC/XIO/OTE/MOV/TON/EQU/etc.) |
| #4 | **Semántica composicional motion** | 50% | **55%** | Átomos curados (cada motion instr individual), pero **composiciones no**. Ejemplo: "MAJ + MAS encadenado = transición controlada" no es detectable. Plan v2 (revertido) Phase 3 apuntaba a 75% |
| #5 | **Trazar dependencias** | 75% | **92%** | `tracer.py` implementa: `writers_of`, `readers_of`, `references_of`, `trace_back` (BFS hacia atrás), `trace_forward`, `find_causal_path`. Tokenizer RLL + ST. **Validado contra caso paradigma 2026-05-03** (cross-AOI traversal de find_causal_path funcional en 3 steps contra CINTA — ver Caso #1) |
| #6 | **Roles de tags** | 70% | **80%** | Capa C detecta `HMI_*`, `*_Setpoint`, `*_Limit`, `*_Enable*`, `*_Reset`, `*_Cmd`. Mapeo eje→AOI principal. UDTs estructurados por entidad (`M*Data`) reconocidos |
| #7 | **Estructura programa (semántica funcional)** | 80% | **85%** | Mapa Mental describe programs + routines + main_routine + AOIs + UDTs por programa. Inferencia per-program (qué tipo de role tiene cada Program: motion_control / safety / sequence_logic / etc.) NO está automatizada |
| #8 | **Síntesis diagnóstica end-to-end (caso empalme)** | 50% | **85%** (validado) | Validado empíricamente 2026-05-03 contra CINTA — 3 turnos efectivos. Cross-AOI traversal de find_causal_path funcional. Pendiente solo: validación cruzada en AQL_M2 (TODO menor) |

### (auxiliar) Migration K6000→K5700

| Aspecto | Pre-plan | Actual | Evidencia |
|---------|---------:|-------:|-----------|
| Inventario de ejes con datos de migración | 25% | **70%** | `to_excel()` produce hoja `Axes` con `motion_module`, catálogo, canal, función inferida. Directamente usable como BoM K6000→K5700 |
| Mapping K6000↔K5700 detallado | 0% | **0%** | `migration_library/` no existe. No es del scope core del Vision (es auxiliar). Espera caso activo |

### Promedios

- **Pre-plan estimate:** ~67%
- **Actual (sin Phase 5):** **~83%** (caso empalme cerrado 2026-05-03; v0.1 oficialmente cumplido)

Avance real desde pre-plan: **+13 puntos**, mayoría concentrada en capacidades #5 (trace), #3 (instructions), #2 (dominios).

---

## 3. Casos de uso 1-6 — estado de cumplimiento

| # | Caso | v0.1 esperado | **Estado actual** |
|---|------|---------------|-------------------|
| 1 | **Empalme con velocidad excesiva** (CASO PARADIGMA) | 5-7 turnos manual | ✅ Validado 2026-05-03 contra CINTA — 3 turnos efectivos (criterio v0.1 ≤6 cumplido con margen, promesa v0.2 3-4 cumplida exacta) |
| 2 | Auditoría rápida proyecto desconocido | <30s | ✅ Logrado: Mapa Mental en <1s contra CINTA + AQL + CPPIM |
| 3 | Comparación entre proyectos | Manual guiado | ⚠️ Manual disponible (carga 2 `Project` paralelos). Diff automático no existe |
| 4 | Plan migración K6000→K5700 | BoM | ✅ Logrado: hoja `Axes` Excel multi-sheet con motion_module + catálogo + canal + función |
| 5 | Detección código muerto | Manual con queries | ✅ Cerrado 2026-05-03: docs/Test/_caso5_dead_code.py detecta tags huérfanos + AOIs no invocadas + routines no llamadas usando project.references_of() del tracer v0.2. Validado contra CINTA + AQL. Reporte: docs/Análisis/Caso_5_Dead_Code_Report.md |
| 6 | Documentación técnica TDR | MD generado | ✅ Logrado: `to_markdown()` produce reporte ~200-500 KB completo |

### Caso #5 — oportunidad mediante tracer

Antes de v0.2, decir "tag X no se usa" requería búsqueda manual. Ahora con `project.references_of(tag)` retorna lista vacía → tag huérfano. Lo mismo para AOIs no invocadas. **Es una capacidad gratis de v0.2 que no se ha conectado al caso #5 todavía**. ~30 min de trabajo cierra esta brecha.

**Status 2026-05-03: ✅ cerrado.** Script operativo en docs/Test/_caso5_dead_code.py.

---

## 4. Criterios v0.1 / v0.2 / v0.3 — qué está cerrado

### v0.1 (per Vision sec 8)

- ✅ Cargar L5X arbitrario y producir Mapa Mental coherente sin intervención
- ✅ Responder preguntas estructurales sin fallar
- ✅ Generar reportes Markdown / Excel / Mermaid
- ✅ Plus: Explorer HTML (doc 06) — **bonus no en criterios originales**
- 🟡 **Caso de empalme se resuelve en ≤6 turnos de conversación** ← PENDIENTE

### v0.2 (per Vision sec 7)

- ✅ Grafos de dependencias bidireccionales — `trace_back` + `trace_forward` implementados
- ✅ "¿De dónde viene este valor?" — `find_causal_path(target_tag)` con BFS sobre xref
- ✅ "¿Qué afecta este tag?" — `trace_forward(tag)` implementado
- 🟡 **Validación empírica contra caso real** ← PENDIENTE (pero código existe)

### v0.3 (per Vision sec 7)

- ✅ Detección automática de dominios funcionales — `patterns.py` Capa C (zonas, safety, HMI, drives)
- ⚠️ Diccionario semántico (HmiRollDiameter → "diámetro de rollo, input operador") — patterns infiere via regex de nombres, pero no produce una tabla "tag → traducción semántica" navegable. Implementable en ~1-2 horas si se necesita
- ⚠️ Cadenas causales pre-construidas — `find_causal_path` las construye on-demand. "Pre-construidas" implicaría cache, no se ha hecho

**Veredicto:** v0.2 + v0.3 están ~85% implementados a nivel de capacidad técnica. La **distinción real** entre versiones se vuelve débil porque el código avanzó sin ceremonia de versionado formal.

---

## 5. Gaps identificados — priorizados

### Gap 1 (CERRADO 2026-05-03) — Test funcional del caso empalme ✅

**Status:** ✅ Cerrado. Test ejecutado contra `CINTA_LAMINADA_M2_2024.L5X` el 2026-05-03 — resuelto en **3 turnos efectivos** del Claude virtual (criterio ≤6 cumplido con margen).

**Hito técnico:** cross-AOI traversal de `find_causal_path` validado empíricamente por primera vez contra caso paradigma.

**Output entregado:** `docs/Test/Caso_1_Empalme_test_funcional.md` (turn log + veredicto + gaps menores como input para v0.2.x).

**Gaps menores revelados (NO bloqueantes — input para v0.2.x):**
- `search()` no indexa nombres de AOIs (workaround: substring de código)
- `trace_back` puede ser ruidoso para hipótesis dirigidas (uso correcto: `find_causal_path` para hipótesis dirigidas, `trace_back` para exploración exhaustiva)

### Gap 2 (HIGH) — Cobertura general logix RLL en `instruction_library`

**Impacto:** el toolkit interpreta motion bien (100%) pero ladder estándar (XIC/XIO/OTE/MOV/TON/EQU) sigue siendo zona ciega. La mayoría del código del parque es ladder genérico, no motion.

**Costo:** 3 sesiones × ~30 min vía NotebookLM (5 instrucciones por batch). Total ~1.5 hrs.

**Output:** ~14 entries adicionales en `instruction_library`. De 17 → 31 entries cubre ~80% del top-20 RLL del parque.

### Gap 3 (MEDIUM) — Composición motion (patterns nivel-2)

**Impacto:** detectar "esto es un splice estilo Diatec" o "esto es un drive roll con dancer encadenado" en lugar de solo identificar las instrucciones individuales. Sería la capacidad #4 subiendo de 55% → 75%.

**Costo:** 2-3 sesiones (identificar 5 patrones del parque + diseñar arquitectura módulo + implementar + validar).

**Output:** módulo nuevo `motion_pattern_library/` con 5 patterns codificados.

**Caveat:** este gap solo se justifica si el test del empalme (Gap 1) revela que la composición es el cuello de botella real. Si el empalme se resuelve sin necesidad de patterns nivel-2, este gap baja a LOW.

### Gap 4 (MEDIUM) — Validar tracer contra caso paradigma

Ligado a Gap 1. El tracer está implementado pero no se ha probado contra el caso empalme. Si el test (Gap 1) lo ejercita y funciona, queda cerrado simultáneamente.

### Gap 5 (LOW) — Patterns Capa C cobertura Diatec legacy

**Impacto:** patterns detecta 43 zonas en CPPIM (Amantrini moderno) pero solo 1-2 en CINTA/AQL (Diatec). Si el use case dominante son PLCs legacy Diatec, las heurísticas no detectan estructura.

**Costo:** investigación + extensión heurísticas. ~2 sesiones.

**Tracker:** `docs/Backlog.md` #1.

### Gap 6 (LOW) — Inferencia funcional automática de programs

**Impacto:** mapa mental describe programs estructuralmente, pero no infiere automáticamente "este program es safety-handler" vs "este es motion-control". Capacidad #7 subiría de 85% → 95%.

**Costo:** 1-2 sesiones.

**Aplicabilidad:** marginal — el usuario humano puede inferir esto del nombre del program y de las AOIs invocadas en <1 minuto.

---

## 6. Capacidades adicionales a considerar — propuestas críticas

Esta sección es **propositiva** — capacidades NO en el Vision original que merecen evaluación. Cada una con costo/beneficio honesto.

### Propuesta A — Test Functional Suite (`tests/`)

**Qué es:** módulo `tests/` con pytest que valida los 6 casos de uso contra los 3 L5X del parque. Sería el cierre formal de cada versión.

**Por qué considerar:** hoy la validación es manual + documental. No hay regresión automática. Si tocamos `patterns.py` o `tracer.py`, no sabemos si rompimos un caso ya logrado.

**Costo:** 2-3 hrs build-out + ~30 min/release después.

**ROI:** **alto** — disciplina de proyecto, previene regresiones, valida cierres de versión.

**Recomendación:** ✅ **construir cuando se cierre el test del empalme** (Gap 1). El primer test del suite ES el test del empalme.

### Propuesta B — Senior Tutor Mode (combinar toolkit + NotebookLM)

**Qué es:** un modo conversacional donde el toolkit no solo responde "qué", sino **explica el porqué** citando manuales (vía NotebookLM) y mostrando alternativas. Combina: instruction_library (qué hace MAJ) + tracer (en qué contexto se usa aquí) + NotebookLM (cuál es la práctica recomendada por Rockwell).

**Por qué considerar:** es lo más cercano al "consultor experto" del Vision. Hoy el toolkit responde a nivel descriptivo; un consultor explica trade-offs.

**Costo:** ~3-4 hrs + iteración con casos reales.

**ROI:** **muy alto** si el objetivo es asesor senior. Bajo si solo se quiere análisis estático.

**Recomendación:** ⚠️ **diferir hasta tener 2-3 casos reales documentados donde se haya usado el toolkit**. Sin ese feedback, sería diseño especulativo. El test del empalme genera el primer caso.

### Propuesta C — Architecture Smell Detection extendido

**Qué es:** ampliar `project.observations` automáticas con:
- Tags huérfanos (sin readers ni writers, vía tracer)
- AOIs declaradas no invocadas
- Routines vacías o stubs
- Programs sin tasks asignados
- Code patterns anti-best-practice (uso de OTL/OTU sin pareja, retentive misuse, etc.)

**Por qué considerar:** alimenta directamente el Caso #5 (detección código muerto). Y hace al toolkit **proactivo** — sugiere mejoras sin que el usuario las pida.

**Costo:** ~2-3 hrs (la mayoría son consultas al tracer ya implementado).

**ROI:** **alto** — capacidad emergente del trabajo ya hecho. Cierra Caso #5 con poco esfuerzo.

**Recomendación:** ✅ **considerar tras el test del empalme**. Si el test revela que detección de "tags huérfanos" es relevante, esto es la próxima inversión.

### Propuesta D — Migration Diff Engine K6000↔K5700

**Qué es:** módulo que cruza manuales 2094 (K6000) vs 2198 (K5700) vía NotebookLM y produce tabla de mappings (atributos de eje renombrados, AOIs equivalentes, parámetros que cambian).

**Por qué considerar:** si Pañalera N2 es caso real activo, esto es el deliverable más directamente útil. Mover de "BoM Excel" a "plan ejecutable de migración".

**Costo:** 2-3 sesiones (curación NotebookLM + módulo + validación contra CINTA 4 ejes K6000).

**ROI:** **muy alto si N2 es activo, cero si no lo es**. Requiere confirmación de scope.

**Recomendación:** ⏸ **esperar confirmación de Pañalera N2 como caso activo**. Si se confirma, esta sube a HIGH priority.

### Propuesta E — Explorer HTML extension con tracer integrado

**Qué es:** el Explorer ya muestra estructura. La spec doc 06 indica "Trace de uso disponible en v0.2". v0.2 ya está implementado. Conectar `find_causal_path` al panel del tag.

**Por qué considerar:** convierte el Explorer en herramienta de diagnóstico para técnicos de planta a las 3 AM.

**Costo:** ~2-3 hrs (modificar `html_explorer.py` panel del tag para llamar a tracer).

**ROI:** **alto** — el Explorer ya existe; agregar trace lo convierte de "visualizador" a "asistente diagnóstico real".

**Recomendación:** ✅ **considerar después del test del empalme**. Si el test usa el tracer y funciona, integrar al Explorer es el siguiente paso natural.

### Lo que NO recomiendo añadir

| Propuesta | Razón rechazo |
|-----------|---------------|
| Más fault codes (Kinetix 6000, GuardLogix safety) | Parked legítimamente. Sin caso real, no mueve la aguja |
| ACD direct parsing | DT-001 lo descarta con razón |
| Code generation (L5X output) | DT-003 lo descarta. Toda la industria falla aquí |
| Embeddings vectoriales / FAISS | DT-008 lo prohíbe. Tamaño del parque actual no lo necesita |
| MCP server, agent orchestration framework | DT-003 + DT-008. Lección dura 2026-05-03 |
| FBD tokenizer | Bajo uso parque. RLL+ST cubren >95% |
| Multi-proyecto / multi-usuario | Nivel 3 del Vision, prematuro |

---

## 7. Plan ejecutable post-v0.1 — 5 sprints, 12 subtareas trazables

> **Reorganizado 2026-05-05:** el plan original (10 tasks en Fases A/B/C/D) se reagrupa en 5 sprints temáticos. Los IDs originales (C.3, A.1, A.1.1…, A.2, A.3, B.1, B.2, C.1, C.2, D.1, D.2) se conservan para trazabilidad histórica. Subtarea = unidad de commit; sprint = unidad de cierre con entregable verificable.
>
> **Chat ejecutor:** ejecutás la próxima subtarea `[ ]` desbloqueada del sprint activo. NO re-decidir prioridades ni saltar de sprint. Hallazgos fuera del plan → 7.4 Discovered.
>
> **Owner:** confirmás OKs de commit subtarea-por-subtarea. Al cerrar la última subtarea de un sprint, valido cierre del sprint y recalculo el scoreboard.

### 7.0 Scoreboard

```
SPRINT 1 · Foundation              [█░░░] 1/4 subtasks  (~2.5 hr)   ← activo
SPRINT 2 · Universalidad           [░░]   0/2           (~3-4 hr)
SPRINT 3 · Validación cruzada      [░░]   0/2           (~3 hr)
SPRINT 4 · Asesor proactivo        [░░]   0/2           (~5-6 hr)   paralelizable post-S1
SPRINT 5 · Visual operativo        [░░]   0/2           (~4-5 hr)
SPRINT 6 · Postponed (FASE E)      (futuro — triggers DT-005)

GLOBAL                             [█░░░░░░░░░░░]  8% (1/12)  ~18-21 hr total
```

> Cada subtarea = 1/12 (~8.3%) del global. Marcar `[x]` tras commit aceptado por owner; recalcular scoreboard.

### 7.1 Reglas operativas (no negociables)

1. Una subtarea = uno o más commits relacionados; `[x]` cuando todos sus acceptance pasan.
2. `[ ]` pending → `[~]` in progress (al empezar) → `[x]` done (al cerrar).
3. NO empezar subtarea con dependencias `[ ]`.
4. NO commit sin OK explícito del owner. La estructura por sprints NO anula esta regla — es por commit, cada vez.
5. Hallazgos fuera del plan → 7.4 Discovered, NO ejecutar unilateral.
6. **Cierre formal de sprint:** al marcar `[x]` la última subtarea del sprint, agregar fila resumen en Done Log (7.3) con outcome del sprint completo + recalcular scoreboard.
7. **No saltar sprints** salvo paralelización explícita autorizada por owner (Sprint 4 puede correr en paralelo con Sprints 2/3 si owner lo decide).
8. **Bloqueo durante subtarea** → marcar `[~]` con nota del bloqueo, parar, reportar al owner.
9. DTs vigentes (DT-001 a DT-010); lección 2026-05-03 vigente (no instalar infra especulativa).

### 7.2 Sprints y subtareas

---

#### SPRINT 1 · Foundation — cobertura xref ST + RLL stdlib

- **Objetivo:** que el tracer y la `instruction_library` cubran el caso base de un proyecto Rockwell promedio (RLL + ST + instrucciones logic core).
- **Dependencias externas:** ninguna. Sprint activo desde 2026-05-05.
- **Estimación total:** ~2.5 hr (4 commits separados).
- **Entregable de cierre:** un L5X arbitrario que mezcla RLL+ST se instrumenta completo en xref; instruction_library reconoce ≥31 entries (17 motion previas + 14 logic/data/timer/comparator nuevas).
- **Criterio de cumplimiento (sprint cerrado):** acceptance de las 4 subtareas pasan + audit en Done Log con resumen consolidado.

**`[x]` C.3 — fix(tracer): `build_xref` procesa código ST además de RLL** · ~30-45 min · cerrada 2026-05-05 (commit `c251d18`)
- Dependencias: ninguna
- Contexto: reformulada 2026-05-05 tras hallazgo en sec 7.4 (descubierto durante intento de ejecución del enunciado original). Investigación empírica reveló que (a) backing tags AOI YA se instrumentan correctamente — verificado con `AHT_Unwinder(UNW_TAPE, ...)`; (b) el gap real es que `build_xref` filtra `r.type != "RLL"` (tracer.py L444 y L453), por lo que ignora todo código ST. Por eso `M1Data`/`M2Data`/`M3Data`/`M4Data` aparecen como huérfanos en el reporte Caso_5 — falsos positivos por ST no procesado, no por backing tags AOI no cubiertos.
- Output: patch a `tracer.py` (`build_xref` + helper `_xref_rows_from_st_routine` o equivalente, reusando `tokenize_st` ya existente en `tokenizer/st_tokenizer.py`).
- Acceptance:
  1. `project.references_of("M1Data")` en CINTA retorna ≥1 hit en `Programs/MainProgram/Routines/InitAxis` (asignación `M1Data.Input.AxPar.HmiRollDiameter := 1`).
  2. No regresión: `references_of("UNW_TAPE")` en CINTA sigue retornando ≥1 hit (backing tag de la invocación `AHT_Unwinder` en `Programs/Axis/Routines/Unwinders/Rung_0`).
  3. Smoke contra AQL_M2 (HANDOFF antipatrón #2 — validar 2 L5X): `references_of` sobre cualquier tag con asignación ST en AQL retorna ≥1 hit; conteo total de rows en xref aumenta ≥0 vs antes (al menos no rompe).
- Commit: `fix(tracer): build_xref procesa código ST — cierra falso positivo M*Data en Caso #5`
- Constraints: sin dependencias nuevas (DT-008); reusar `st_tokenizer` existente; mantener tag_root indexing para tags estructurados; idempotencia de `build_xref` preservada (drop+recreate xref).

**`[ ]` A.1.1 — feat(library): batch 5 logic base (XIC/XIO/OTE/OTL/OTU)** · ~30 min
- Dependencias: ninguna (paralelizable con C.3 pero recomiendo serial para mantener foco)
- Output: 5 nuevas `InstructionMetadata` en `rockwell_comprehender/instruction_library/__init__.py` siguiendo patrón motion (ver MAJ/MAS/MAH como referencia).
- Acceptance: `len(list_instructions(category="logic")) ≥ 5`; smoke por instrucción `get_instruction_metadata("XIC") is not None` válido.
- Curación: NotebookLM serial estricto — query template en Apéndice B. Una query por instrucción, delay 2-3s entre llamadas.
- Commit: `feat(library): batch 5 logic base (XIC/XIO/OTE/OTL/OTU)`

**`[ ]` A.1.2 — feat(library): batch 5 data+timer (MOV/COP/CPS/TON/ONS)** · ~30 min
- Dependencias: A.1.1 `[x]` (orden por categoría, no técnica)
- Output: 5 entries adicionales (MOV, COP, CPS — data movement; TON, ONS — timer).
- Acceptance: smoke por instrucción válido; total instruction_library ≥27 entries tras este commit.
- Curación: NotebookLM serial — Apéndice B.
- Commit: `feat(library): batch 5 data+timer (MOV/COP/CPS/TON/ONS)`

**`[ ]` A.1.3 — feat(library): batch 4 comparators (EQU/NEQ/GRT/LES)** · ~25 min
- Dependencias: A.1.2 `[x]`
- Output: 4 entries comparators.
- Acceptance: total instruction_library ≥31 entries; smoke válido por instrucción.
- Curación: NotebookLM serial — Apéndice B.
- Commit: `feat(library): batch 4 comparators (EQU/NEQ/GRT/LES)`

---

#### SPRINT 2 · Universalidad — ST coverage + dominio síntoma→código

- **Objetivo:** cerrar formalmente criterio v0.3 (lexicón síntoma→código) y completar cobertura ST de la instruction_library.
- **Dependencias:** Sprint 1 cerrado.
- **Estimación total:** ~3-4 hr (2 commits).
- **Entregable de cierre:** `project.identify_domain("problema en empalme")` en CINTA retorna AOIs candidatos correctos con confidence ≥0.7. Criterio v0.3 del Vision sec 8 marcado ✅ en `docs/00_Vision_y_Roadmap.md`.

**`[ ]` A.2 — feat(library): cobertura ST mínima** · ~1 hr
- Dependencias: A.1.3 `[x]`
- Output: 6-8 entries para constructos ST comunes (IF, CASE, FOR, WHILE, REPEAT, asignación `:=`, function-style call) + audit en `docs/Test/_st_coverage_audit.md`.
- Acceptance: cobertura ≥80% de constructos detectados en el parque (medido por audit); smoke contra `st_tokenizer` no rompe.
- Curación: NotebookLM serial — Apéndice B (template adaptado a constructos ST).
- Commit: `feat(library): cobertura ST básica — N constructos`

**`[ ]` A.3 — feat(domain): lexicón síntoma→código (criterio v0.3)** · ~2-3 hr
- Dependencias: A.1.3 `[x]`
- Output: módulo nuevo `rockwell_comprehender/domain_lexicon.py` con `identify_domain(project, query: str) -> list[DomainHit]`. Heurísticas: regex sobre tag/AOI/routine names + tabla síntomas→keywords.
- Acceptance: `project.identify_domain("problema en empalme")` en CINTA retorna `AHT_CtcSplicer + AHT_Unwinder + DancerCorAndNewRadiusComputation` con confidence ≥0.7. Tras cierre, marcar criterio v0.3 ✅ en `docs/00_Vision_y_Roadmap.md` sec 8.
- Commit: `feat(domain): lexicón síntoma→código — cierra criterio v0.3`
- Constraints: sin dependencias nuevas; usar `re` + estructuras del modelo.

---

#### SPRINT 3 · Validación cruzada — regresión contra parque

- **Objetivo:** demostrar empíricamente que el toolkit generaliza a 3 L5X de arquitecturas distintas (CINTA Diatec v20.01, AQL Diatec v20.12, CPPIM Amantrini v33).
- **Dependencias:** Sprint 2 cerrado.
- **Estimación total:** ~3 hr (2 commits).
- **Entregable de cierre:** los 6 casos del catálogo ejercitados contra los 3 L5X con veredicto explícito (✅/⚠️/❌) por caso×proyecto. Cierra antipatrón #2 del HANDOFF (mínimo 2 L5X validados) — ahora con margen de 3.

**`[ ]` B.1 — test(empalme): validación cruzada contra AQL_M2** · ~1 hr
- Dependencias: A.1.3 `[x]`, A.3 `[x]`
- Output: parametrizar `_caso1_test_runner.py` por L5X; sección "Re-ejecución contra AQL_M2" en `docs/Test/Caso_1_Empalme_test_funcional.md`.
- Acceptance: veredicto explícito (✅ generaliza / ⚠️ falla en X / ❌ rompe). Si AQL no tiene empalme análogo: validar `find_causal_path` cross-AOI contra otro flujo causal del proyecto (ej. tensión, sincronización).
- Commit: `test(empalme): validación cruzada contra AQL_M2`

**`[ ]` B.2 — test(cppim): casos 1-6 contra Amantrini v33** · ~2 hr
- Dependencias: B.1 `[x]`
- Output: `docs/Análisis/CPPIM_caso_audit.md` con resultado por caso.
- Acceptance: casos 2/4/5/6 ejecutan sin error contra CPPIM_BD800_1.L5X; gaps Amantrini específicos (raC libraries, ProtectedRoutine) documentados; degradación de loader vs CINTA documentada.
- Commit: `test(cppim): validación casos 1-6 contra Amantrini v33`

---

#### SPRINT 4 · Asesor proactivo — smell detection (paralelizable post-Sprint 1)

- **Objetivo:** convertir el toolkit de "responde lo que pregunto" a "sugiere lo que debo revisar".
- **Dependencias:** Sprint 1 cerrado. **Independiente de Sprints 2/3** — owner puede autorizar paralelización.
- **Estimación total:** ~5-6 hr (2 commits).
- **Entregable de cierre:** `project.detect_smells()` retorna ≥15 reglas activadas, sin falsos positivos sistemáticos, contra los 3 L5X.

**`[ ]` C.1 — feat(smells): architecture smell detector** · ~2-3 hr
- Dependencias: A.1.3 `[x]` (necesita reconocer operadores para razonar OTL/OTU pairing)
- Output: módulo `rockwell_comprehender/smells.py` con `detect_smells(project)` y 5 reglas iniciales:
  1. OTL/OTU sin pareja (latch sin unlatch o viceversa)
  2. AOIs con >30 parameters (smell de god-object)
  3. Routines vacías (`code` vacío o solo NOP/AFI)
  4. Programs sin task asignado
  5. Tags scope mismatch (controller-scope cuando podría ser program-local)
- Acceptance: smoke contra CINTA+AQL detecta ≥3 smells reales sin falsos positivos por regla; reporte `docs/Análisis/<L5X>_smells.md` legible.
- Commit: `feat(smells): architecture smell detector — 5 reglas iniciales`

**`[ ]` C.2 — feat(smells): best practices auditor** · ~3 hr
- Dependencias: C.1 `[x]`
- Output: extensión de `smells.py` con ≥10 reglas curadas vía NotebookLM (mejores prácticas Rockwell):
  - UDTs vs tags planos
  - Naming conventions (PascalCase para AOIs, snake/camel para tags)
  - Scope correcto por uso
  - Motion error handling (uso de motion_status sin chequeo de error)
  - etc. (curación NotebookLM define lista final)
- Acceptance: smoke válido contra los 3 L5X.
- Commit: `feat(smells): best practices auditor — 10+ reglas Rockwell`

---

#### SPRINT 5 · Visual operativo — Explorer + TDR

- **Objetivo:** entregar herramientas de campo usables por técnicos no-Hedi (Explorer interactivo + TDR ejecutivo).
- **Dependencias:** Sprint 2 cerrado (necesita A.3 / lexicón para enriquecer Explorer y TDR).
- **Estimación total:** ~4-5 hr (2 commits).
- **Entregable de cierre:** HTMLs de los 3 L5X navegables por terceros sin curva de aprendizaje; PDF del TDR exportable; cierra Vision criterio Nivel 3 parcial ("otro ingeniero usa la herramienta sin curva significativa").

**`[ ]` D.1 — feat(explorer): tracer integrado en panel del tag (Propuesta E)** · ~2-3 hr
- Dependencias: A.3 `[x]`
- Output: modificación de `reporters/html_explorer.py` para que el panel del tag (doc 06 sec 5.3.7) llame `find_causal_path` y muestre trace embebido.
- Acceptance: HTMLs de CINTA+AQL: click en tag → muestra writers_of; click en "trace back" → path BFS hasta inputs externos.
- Commit: `feat(explorer): tracer v0.2 integrado en panel del tag (cierra spec doc 06 v0.2)`
- Constraints: sin librerías JS externas; CSS+JS inline (doc 06 sec 4).

**`[ ]` D.2 — feat(reporter): TDR HTML ejecutivo** · ~2 hr
- Dependencias: D.1 `[x]`
- Output: `reporters/tdr_html.py` — combina mapa mental + smells + cadenas causales + recomendaciones del asesor en un único HTML ejecutivo.
- Acceptance: TDR generado contra CINTA+AQL es coherente, navegable, exportable a PDF (Print to PDF del browser).
- Commit: `feat(reporter): TDR HTML ejecutivo`

---

#### SPRINT 6 · Postponed — emergente N2→N3 (FASE E original)

> NO construir hasta cumplir Vision sec 7 *"Futuro Nivel 3 — solo si el uso valida la inversión"*. Triggers documentados; sin trabajo activo.

- **E.1** Cross-project pattern recognition (trigger: corpus ≥5 L5X de máquinas distintas analizadas).
- **E.2** Migration support library K6000↔K5700 (trigger: caso real activo de migración hardware/firmware en calendario del owner — ej. Pañalera N2 confirmada).
- **E.3** Best-practices benchmark cross-parque (trigger: parque entero analizado y consolidado).

### 7.3 Done Log (append-only)

| Fecha cierre | Task ID | Commit hash | Outcome (1 línea) |
|--------------|---------|-------------|-------------------|
| 2026-05-05 | C.3 (Sprint 1) | `c251d18` | `build_xref` procesa código ST; CINTA xref +38 rows operator=`:=`; M*Data dejan de ser falsos positivos en Caso #5; backing tags AOI sin regresión; AQL_M2 5/5 ST roots validados |

### 7.4 Discovered (fuera del plan, append-only)

| Fecha | Hallazgo | Decisión owner |
|-------|----------|----------------|
| 2026-05-05 | **C.3 — acceptance criteria no se sostiene contra CINTA real.** Empíricamente: (a) backing tags de invocaciones AOI **YA se instrumentan correctamente** como `kind=tag, usage=write` en xref (verificado con `AHT_Unwinder(UNW_TAPE, ...)` en Programs/Axis/Routines/Unwinders/Rung_0 — UNW_TAPE aparece en xref). (b) El invoke `AHT_Unwinder` en CINTA Rung_0 **NO recibe M1Data como argumento**; pasa `UNW_TAPE`, `M1`, `M2` (no `M1Data`). (c) `M1Data` SÍ aparece en código pero solo en routine ST `Programs/MainProgram/Routines/InitAxis` (asignaciones tipo `M1Data.Input.AxPar.HmiRollDiameter := 1`). **Gap real identificado:** `build_xref` filtra `r.type != "RLL"` (tracer.py L444, L453), por lo que NO procesa código ST. Esto es el verdadero motivo de que `references_of("M1Data")` retorne 0 hits, no los backing tags AOI. | **2026-05-05 — Resuelto:** C.3 reformulada en sec 7.2 (camino a: apuntar al gap real "build_xref procesa ST"). Acceptance ajustada a la asignación ST real en `Programs/MainProgram/Routines/InitAxis` + no-regresión sobre backing tags AOI. Caveat #1 del Caso_5 report quedará obsoleto al cerrar C.3. |

### 7.5 Cómo retomar en sesión nueva (chat ejecutor)

1. Abrir esta auditoría sec 7.0 (scoreboard) — identificar **sprint activo** (el de menor índice con subtareas `[ ]` o `[~]`).
2. Dentro del sprint activo: identificar próxima subtarea `[ ]` desbloqueada (todas sus dependencias `[x]`).
3. Si encontrás `[~]` (in progress de sesión previa): leer la nota de bloqueo en el ítem; decidir si continuar la subtarea o, si está realmente bloqueada, reportar al owner antes de cambiar.
4. Marcar la subtarea elegida `[~]`.
5. Ejecutar siguiendo los acceptance criteria + constraints. NotebookLM queries por Apéndice B (serial estricto).
6. Al cerrar: pedir OK explícito del owner para commit. Tras OK aceptado y commit hecho: marcar `[x]`, agregar fila al Done Log (7.3), recalcular scoreboard.
7. **Si la subtarea cerrada es la última del sprint:** validar entregable de cierre del sprint, agregar fila resumen en Done Log (7.3) marcando "SPRINT N cerrado" con outcome consolidado, recalcular scoreboard global.
8. Hallazgos fuera del plan → fila en Discovered (7.4), NO ejecutar unilateral.
9. NO saltar de sprint salvo paralelización autorizada por owner (Sprint 4 puede correr en paralelo con Sprints 2/3 si lo decide).

### Apéndice B — Pattern de query NotebookLM (para A.1, A.2, C.2)

Skill operativa, auth Google Pro Softys válida, notebook activo `studio-5000---logix-&-kinetix-motion-reference`.

```powershell
$env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"
cd "$env:USERPROFILE\.claude\skills\notebooklm"
python scripts/run.py ask_question.py --question "..."
```

Plantilla de query (validada con las 17 motion entries actuales):

```
Para la instrucción <NAME> de Studio 5000 (publicación 1756-RM003), proporcioname:
1. nombre completo (e.g., "Examine If Closed")
2. categoría (logic | data movement | timer | comparator | math | safety | motion)
3. resumen 1-line
4. lista de pins/operandos: nombre, dirección (input/output/inout/config), datatype, descripción semántica, required (sí/no)
5. config attributes si aplica
6. modos de fallo conocidos
7. referencias bibliográficas (publication + sección)
8. notas operativas relevantes (gotchas, mejores prácticas)

Devolveme la respuesta en formato estructurado fácil de parsear.
```

Tras query: editar `rockwell_comprehender/instruction_library/__init__.py` con `InstructionMetadata` siguiendo patrón motion (ver MAJ/MAS/MAH). Smoke test: `from rockwell_comprehender.instruction_library import get_instruction_metadata; assert get_instruction_metadata("<NAME>") is not None`.

---

## Apéndice A — Lecciones del proceso (para próximas sesiones)

1. **El proyecto avanzó más de lo que el HANDOFF refleja.** El HANDOFF describe v0.1.0 con 4 reporters básicos. El estado real es ~v0.3.x con tracer + patterns + instruction_library + html_explorer. Los docs no se actualizaron al ritmo del código. Esta auditoría es el primer correctivo.

2. **DT-008 + DT-003 son ley.** La sesión del 2026-05-03 que instaló Ruflo (claude-flow Phase 2 con vector embeddings + 96 agents + 14 hooks) violó sistemáticamente esas decisiones. Fue revertida. Lección registrada en `~/.claude/projects/.../memory/feedback_deviation_2026-05-03.md`.

3. **Validación empírica antes de comprometer (DT-010).** El 2026-05-03 también instaló Agent Teams nativo + Ruflo "para tener capacidades extra". Sin caso de uso del proyecto que lo justifique, fue infraestructura especulativa. La regla: **antes de instalar cualquier framework externo, validar contra al menos 2 L5X del parque que aporta valor concreto**. Si la respuesta es "ninguno o trivial", no instalar.

4. **El paquete YA es senior-comprehender de L5X.** No necesita una capa de orquestación LLM encima. Lo que aporta valor de "asesor senior" es **el conocimiento curado** (instruction_library + manuals via NotebookLM) + **el toolkit de análisis** (tracer + patterns + mapa mental). No frameworks de agents.

5. **Cuando dudás del scope, leer el Vision (`00_*.md`) y los DTs (`01_*.md`).** Son ley del proyecto, no sugerencias. Cada decisión nueva debe coexistir o supersede explícitamente las anteriores, no ignorarlas.

---

*Auditoría ejecutada por Claude Code el 2026-05-03 tras desvío que se revirtió en la misma sesión. Próxima auditoría sugerida: tras cerrar Gap 1 (test empalme).*
