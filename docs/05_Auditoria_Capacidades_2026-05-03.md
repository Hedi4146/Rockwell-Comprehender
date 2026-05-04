# 05 · AUDITORÍA DE CAPACIDADES — 2026-05-03

**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Auditor:** Claude Code (sesión 2026-05-03)
**Propósito:** Inventario honesto del estado actual del proyecto `rockwell-comprehender` versus los criterios de "ingeniero senior + consultor experto Rockwell" definidos en `00_Vision_y_Roadmap.md`. Base para decidir próximas inversiones.

---

## TL;DR

**Estado global: ~80% de las capacidades del Vision están construidas y operativas.** Eso es ~13 puntos arriba del baseline pre-plan (~67%) que el Vision sec 12 estimaba.

**Lo que falta, en orden de impacto:**
1. **Test funcional del Caso #1 (empalme)** — único criterio v0.1 abierto. Sin esto NO podemos declarar v0.1 cerrado.
2. **Cobertura general logix en `instruction_library`** — hoy 100% motion (17 entries) pero 0% scaffolding RLL (XIC/MOV/TON/EQU/etc.). Limita interpretación de código en ladder estándar.
3. **Composición motion (patterns nivel-2)** — átomos curados pero composiciones tipo "MAJ→MAS encadenado = control de empalme estilo Diatec" no detectables.
4. **Validación empírica del tracer (v0.2 implementado pero no probado contra caso real)** — `writers_of/readers_of/trace_back/find_causal_path` están construidos pero el caso paradigma no los ha ejercido.

**Recomendación de próximo paso (UNO solo):** ejecutar el test funcional del caso empalme contra CINTA. Eso valida 3 capacidades a la vez (mapa mental, búsqueda, tracer) y cierra v0.1.

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
| #5 | **Trazar dependencias** | 75% | **90%** | `tracer.py` implementa: `writers_of`, `readers_of`, `references_of`, `trace_back` (BFS hacia atrás), `trace_forward`, `find_causal_path`. Tokenizer RLL + ST. **Construido pero no validado contra caso paradigma todavía** — gap de validación, no de implementación |
| #6 | **Roles de tags** | 70% | **80%** | Capa C detecta `HMI_*`, `*_Setpoint`, `*_Limit`, `*_Enable*`, `*_Reset`, `*_Cmd`. Mapeo eje→AOI principal. UDTs estructurados por entidad (`M*Data`) reconocidos |
| #7 | **Estructura programa (semántica funcional)** | 80% | **85%** | Mapa Mental describe programs + routines + main_routine + AOIs + UDTs por programa. Inferencia per-program (qué tipo de role tiene cada Program: motion_control / safety / sequence_logic / etc.) NO está automatizada |
| #8 | **Síntesis diagnóstica end-to-end (caso empalme)** | 50% | **70%** (probable) | TODOS los building blocks existen: mapa mental, search, get_aoi, tracer.find_causal_path, instruction_library para entender los operadores. **Sin test empírico, el % es estimación.** ESTE es el criterio v0.1 abierto |

### (auxiliar) Migration K6000→K5700

| Aspecto | Pre-plan | Actual | Evidencia |
|---------|---------:|-------:|-----------|
| Inventario de ejes con datos de migración | 25% | **70%** | `to_excel()` produce hoja `Axes` con `motion_module`, catálogo, canal, función inferida. Directamente usable como BoM K6000→K5700 |
| Mapping K6000↔K5700 detallado | 0% | **0%** | `migration_library/` no existe. No es del scope core del Vision (es auxiliar). Espera caso activo |

### Promedios

- **Pre-plan estimate:** ~67%
- **Actual (sin Phase 5):** **~80%**
- **Con caso empalme cerrado:** ~83%

Avance real desde pre-plan: **+13 puntos**, mayoría concentrada en capacidades #5 (trace), #3 (instructions), #2 (dominios).

---

## 3. Casos de uso 1-6 — estado de cumplimiento

| # | Caso | v0.1 esperado | **Estado actual** |
|---|------|---------------|-------------------|
| 1 | **Empalme con velocidad excesiva** (CASO PARADIGMA) | 5-7 turnos manual | 🟡 **NO PROBADO** — único criterio v0.1 abierto |
| 2 | Auditoría rápida proyecto desconocido | <30s | ✅ Logrado: Mapa Mental en <1s contra CINTA + AQL + CPPIM |
| 3 | Comparación entre proyectos | Manual guiado | ⚠️ Manual disponible (carga 2 `Project` paralelos). Diff automático no existe |
| 4 | Plan migración K6000→K5700 | BoM | ✅ Logrado: hoja `Axes` Excel multi-sheet con motion_module + catálogo + canal + función |
| 5 | Detección código muerto | Manual con queries | ⚠️ Parcial: AOIs duplicadas detectadas automáticamente (`aoi_naming_collision`). Tags huérfanos / routines vacías / AOIs no invocadas: ahora **factibles** vía `tracer.references_of()` (no lo intentamos aún) |
| 6 | Documentación técnica TDR | MD generado | ✅ Logrado: `to_markdown()` produce reporte ~200-500 KB completo |

### Caso #5 — oportunidad mediante tracer

Antes de v0.2, decir "tag X no se usa" requería búsqueda manual. Ahora con `project.references_of(tag)` retorna lista vacía → tag huérfano. Lo mismo para AOIs no invocadas. **Es una capacidad gratis de v0.2 que no se ha conectado al caso #5 todavía**. ~30 min de trabajo cierra esta brecha.

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

### Gap 1 (HIGH) — Test funcional del caso empalme NO ejecutado

**Impacto:** sin esto no podemos afirmar empíricamente que el toolkit cumple su propósito. Todos los building blocks existen. La incógnita es **cuántos turnos** + **qué fricción aparece**.

**Costo:** 1-2 hrs (1 sesión dedicada a simular la conversación contra CINTA, contar turnos, anotar gaps).

**Output:** doc en `docs/Test/Caso_1_Empalme_test_funcional.md` con turn-by-turn + veredicto + gaps revelados.

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

## 7. Recomendación de próximo paso

**UNO solo. No diez.**

### Recomendación: Test funcional del Caso #1 (empalme) contra `CINTA_LAMINADA_M2_2024.L5X`

**Por qué:**
1. Es el **único criterio v0.1 abierto** del Vision. Cierra una promesa pendiente desde hace semanas.
2. Ejercita **3 capacidades clave** simultáneamente: mapa mental (capacidad #1, #2, #7), búsqueda + lupa (capacidad #3), tracer (capacidad #5, #8).
3. **Genera datos empíricos** sobre cuántos turnos toma resolver el caso paradigma — sin esto las % de la sec 2 son estimación.
4. **Identifica los gaps reales** que merecen siguiente inversión, en lugar de adivinar.

**Cómo:**
- Una sesión dedicada (~1-2 hrs).
- Simular la conversación: "Hedi reporta síntoma → Claude carga proyecto → navega capa por capa → llega a hipótesis".
- Documentar turn-by-turn en `docs/Test/Caso_1_Empalme_test_funcional.md` (que ya existe — actualizar).
- Output: veredicto (≤6 turnos / >6 turnos) + lista de gaps específicos revelados.

**Después del test, los siguientes pasos se autorientan:**
- Si pasa con margen → cerrar v0.1 oficialmente. Próximo: Propuesta C (architecture smells) o Propuesta E (Explorer + tracer).
- Si pasa apretado → identificar los 1-2 gaps que estiraron el conteo, atacar.
- Si no pasa → diagnosticar específicamente qué del paquete falló (probable: composición motion, capacidad #4).

---

## Apéndice A — Lecciones del proceso (para próximas sesiones)

1. **El proyecto avanzó más de lo que el HANDOFF refleja.** El HANDOFF describe v0.1.0 con 4 reporters básicos. El estado real es ~v0.3.x con tracer + patterns + instruction_library + html_explorer. Los docs no se actualizaron al ritmo del código. Esta auditoría es el primer correctivo.

2. **DT-008 + DT-003 son ley.** La sesión del 2026-05-03 que instaló Ruflo (claude-flow Phase 2 con vector embeddings + 96 agents + 14 hooks) violó sistemáticamente esas decisiones. Fue revertida. Lección registrada en `~/.claude/projects/.../memory/feedback_deviation_2026-05-03.md`.

3. **Validación empírica antes de comprometer (DT-010).** El 2026-05-03 también instaló Agent Teams nativo + Ruflo "para tener capacidades extra". Sin caso de uso del proyecto que lo justifique, fue infraestructura especulativa. La regla: **antes de instalar cualquier framework externo, validar contra al menos 2 L5X del parque que aporta valor concreto**. Si la respuesta es "ninguno o trivial", no instalar.

4. **El paquete YA es senior-comprehender de L5X.** No necesita una capa de orquestación LLM encima. Lo que aporta valor de "asesor senior" es **el conocimiento curado** (instruction_library + manuals via NotebookLM) + **el toolkit de análisis** (tracer + patterns + mapa mental). No frameworks de agents.

5. **Cuando dudás del scope, leer el Vision (`00_*.md`) y los DTs (`01_*.md`).** Son ley del proyecto, no sugerencias. Cada decisión nueva debe coexistir o supersede explícitamente las anteriores, no ignorarlas.

---

*Auditoría ejecutada por Claude Code el 2026-05-03 tras desvío que se revirtió en la misma sesión. Próxima auditoría sugerida: tras cerrar Gap 1 (test empalme).*
