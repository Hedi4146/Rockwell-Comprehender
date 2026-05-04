# PLAN DE TRABAJO — Rockwell Comprehender

**Documento operativo. Lectura obligatoria al inicio de cada sesión.**

**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Última actualización:** 2026-05-03 (v2 — re-escrito como plan ejecutable real)

---

## 0. SCOREBOARD — estado de avance global

```
PHASE 1 · Validar v0.1 (caso empalme)         [░░░░░░░░░░]   0% (0/4 tasks)
PHASE 2 · Cobertura RLL (general logix)       [░░░░░░░░░░]   0% (0/5 tasks)
PHASE 3 · Composición motion                  [░░░░░░░░░░]   0% (0/5 tasks)
PHASE 4 · Inferencia funcional programas      [░░░░░░░░░░]   0% (0/4 tasks)
PHASE 5 · Migration K6000→K5700 (Pañalera N2) [░░░░░░░░░░]   0% (0/4 tasks) [pending owner]

WORK CONSTRUIDO PRE-PLAN (no contabilizado en phases — base instalada):
  Toolkit v0.1 + v0.2 + v0.3 (estructura + tracer + Capa C/D)
  Library motion 100% parque (17 entries)
  ST tokenizer (gap cerrado)
  Capa C Diatec extension (gap cerrado)
  Sub-módulo fault_code_library (parked tras pivote anti-deviation)

GLOBAL EJECUTABLE     [░░░░░░░░░░]   0% (0/22 tasks)
```

> Cada task vale 1/22 ≈ 4.5% del global. Una sesión típica cierra 1-3 tasks.

---

## 1. REGLAS DE COMMIT (decisión automática, NO preguntar cada vez)

**Trigger de commit:** una task tiene TODOS sus acceptance criteria cumplidos.

**Reglas:**
1. **1 task = 1 commit.** No batch. No mezclar tasks.
2. **Mensaje del commit está definido EN la task.** Usar el provisto.
3. **NO commitear trabajo en progreso.** Si una task está en T.X.Y y todavía no cumple acceptance → working tree, no commit.
4. **NO commitear si hay tests fallando.** Re-ejecutar tests siempre antes de commit.
5. **NO se requiere preguntar al owner por cada commit.** El owner ya autorizó el patrón al aprobar este plan.
6. **Excepción que SÍ requiere confirmación owner:**
   - Push a remote (regla absoluta global del usuario)
   - Cambios fuera del scope de la task actual (deviation)
   - Reverts, rebases, force operations
   - Modificación de archivos sensibles (settings.json, gitignore, pyproject.toml deps)

**Después de commit:**
- Marcar la task como `[x]` con timestamp y commit hash.
- Recalcular % del milestone, phase y global en sección 0.
- Update de Done Log (sección 8).

---

## 2. REGLAS ANTI-DEVIATION

### Antes de iniciar trabajo (5 preguntas obligatorias)

1. ¿La sesión está leyendo `docs/PLAN_DE_TRABAJO.md` (este doc)?
2. ¿La task que voy a hacer está EXPLÍCITAMENTE en el plan (sección 3-7)?
3. ¿No está marcada `[x]` ya completada?
4. ¿No está bloqueada por dependencias incompletas?
5. ¿No está en PARKED (sección 9)?

**Si CUALQUIER respuesta es "no" o "ambigua" → PARAR. Preguntar al owner.**

### Durante el trabajo

- **Si descubrís algo fuera del plan:** NO ejecutar. Anotar en sección 10 (Discovered) con 1 línea de justificación. Owner decide si entra al plan.
- **Si una task consume >2x su estimación:** parar, anotar en Discovered, recapitular.
- **Si encontrás un bug que no es la task actual:** NO arreglar inline. Anotar y seguir.

### Lección dura (2026-05-03)

Una sesión completa (~3 hrs, ~700K tokens) se desvió hacia curación de fault codes K5700. Útil pero TANGENCIAL al objetivo "comprender L5X con depth senior". El sub-módulo `fault_code_library/` queda como base instalada pero NO se sigue curando hasta que aparezca caso real de diagnóstico de drives. **NO repetir.**

---

## 3. PHASE 1 · Validar v0.1 con CASO EMPALME (tests funcional)

**Objetivo:** Cerrar el último criterio v0.1 abierto desde el commit inicial. Sin esto, no sabemos si el toolkit RESUELVE casos reales — solo que es código que corre.

**Criterio de éxito de la phase:** El caso empalme se resuelve en ≤6 turnos contra `CINTA_LAMINADA_M2_2024.L5X`.

**Estimación total:** 1-2 sesiones (~1-2 hrs).

---

### M1.1 · Setup del test harness

- [ ] **T1.1.1** — Re-leer `docs/03_Casos_de_Uso_Reales.md` Caso #1 (empalme) para confirmar el síntoma exacto y el diagnóstico esperado.
  - **Output:** comprensión clara de los 5 niveles de profundidad descendente del caso.
  - **Acceptance:** documento `docs/Test/Caso_1_Empalme_test_funcional_v2.md` creado con sección "Síntoma + diagnóstico esperado".
  - **Commit:** `docs(test): scaffolding test caso empalme v2`

- [ ] **T1.1.2** — Crear el script de simulación del test (`docs/Test/_caso_empalme_runner.py`) que carga CINTA + ejecuta cada turno como una API call al toolkit, contando turnos.
  - **Output:** script ejecutable, idempotente, instrumentado.
  - **Acceptance:** `python docs/Test/_caso_empalme_runner.py` corre sin errores y emite turn-by-turn log.
  - **Commit:** `test(empalme): runner ejecutable para test caso empalme`

---

### M1.2 · Ejecutar test contra CINTA

- [ ] **T1.2.1** — Ejecutar el runner del test contra CINTA. Cada turno simula una pregunta del owner. Documentar qué API calls del toolkit se usan en cada turno y qué información devuelven.
  - **Output:** `docs/Test/Caso_1_Empalme_test_funcional_v2.md` actualizado con turn log + count.
  - **Acceptance:** test ejecutado de extremo a extremo, count de turnos registrado, conclusión causal documentada.
  - **Commit:** `test(empalme): ejecutado contra CINTA — N turnos`

---

### M1.3 · Cierre del criterio v0.1 + lecciones

- [ ] **T1.3.1** — Comparar contra el criterio (≤6 turnos). Si pasa: documentar como criterio v0.1 cerrado. Si no pasa: identificar gaps específicos del toolkit que prolongaron el test.
  - **Output:** sección "Veredicto v0.1" en el doc del test + actualización de `docs/00_Vision_y_Roadmap.md` (criterio).
  - **Acceptance:** veredicto explícito (passed / failed con razones específicas) + (si failed) tasks de mejora añadidas a sección 10 Discovered.
  - **Commit:** `docs(v0.1): veredicto criterio caso empalme + lecciones`

---

## 4. PHASE 2 · Cobertura RLL — curar general logix top-frequency parque

**Objetivo:** Subir capacidad #3 (interpretación de instrucciones) de 60% → 85%. Hoy el library cubre motion 100% pero 0% del scaffolding RLL (XIC/XIO/OTE/MOV/TON/MSG/...).

**Criterio de éxito:** 14 instrucciones general logix curadas, validadas en CINTA/AQL/CPPIM cubren ≥80% de los operadores top-20 de cada L5X.

**Estimación total:** 3 sesiones (3 batches de 5 vía NotebookLM, ~5-10 min cada uno).

---

### M2.1 · Batch 1 — Lógica booleana base

- [ ] **T2.1.1** — Curar batch NotebookLM strict para 5 instrucciones: **XIC, XIO, OTE, OTL, OTU**.
  - **Output:** 5 entries nuevas en `rockwell_comprehender/instruction_library/__init__.py`.
  - **Acceptance:** smoke test pasa (`get_instruction_metadata("XIC")` returns FaultCode con pins/notes/references); `len(list_instructions(category="logic"))` retorna ≥5.
  - **Commit:** `feat(library): batch 5 logic base (XIC/XIO/OTE/OTL/OTU)`

---

### M2.2 · Batch 2 — Movimiento de datos + timers

- [ ] **T2.2.1** — Curar batch NotebookLM para 5 instrucciones: **MOV, COP, CPS, TON, ONS**.
  - **Output:** 5 entries nuevas en library.
  - **Acceptance:** smoke test (`get_instruction_metadata("MOV")` válido); count motion+logic ≥10.
  - **Commit:** `feat(library): batch 5 data+timer (MOV/COP/CPS/TON/ONS)`

---

### M2.3 · Batch 3 — Comparators + math + control flow

- [ ] **T2.3.1** — Curar batch NotebookLM para 4 instrucciones: **EQU/NEQ/GRT/LES** (los 4 comparators dominantes en parque).
  - **Output:** 4 entries en library.
  - **Acceptance:** smoke test válido para los 4.
  - **Commit:** `feat(library): batch 4 comparators (EQU/NEQ/GRT/LES)`

---

### M2.4 · Cobertura validation contra parque

- [ ] **T2.4.1** — Para cada L5X (CINTA, AQL, CPPIM): obtener top-20 operadores RLL, calcular qué % está curado en library. Producir tabla.
  - **Output:** sección en `docs/Test/coverage_general_logix.md` con tabla por L5X.
  - **Acceptance:** los 3 L5X muestran ≥80% de top-20 operadores curados.
  - **Commit:** `docs(coverage): validación general logix coverage 80%+ parque`

---

### M2.5 · Update capacidad %

- [ ] **T2.5.1** — Actualizar capacidad #3 de la sección 2 del Plan: 60% → ~85%. Recalcular global.
  - **Output:** edit del Plan + commit.
  - **Acceptance:** sección 0 scoreboard refleja Phase 2 = 100%.
  - **Commit:** `docs(plan): cierre Phase 2 — RLL general logix coverage 80%+`

---

## 5. PHASE 3 · Composición motion (semantic patterns)

**Objetivo:** Subir capacidad #4 de 50% → 75%. Hoy curamos átomos (MAJ, MAG, MAS individualmente) pero no composiciones ("MAG + MCD + dancer = control empalme estilo Diatec").

**Criterio de éxito:** Detector de 5 patrones composicionales motion del parque, funcional contra los 3 L5X.

**Estimación total:** 2-3 sesiones.

---

### M3.1 · Identificación de los 5 patrones

- [ ] **T3.1.1** — Analizar los 3 L5X del parque para identificar 5 patrones composicionales motion recurrentes. Inputs: reports L5X existentes + lectura directa de routines motion.
  - **Output:** `docs/Análisis/motion_composition_patterns.md` con 5 patrones documentados (nombre, set de instrucciones, contexto típico, L5X en los que aparece).
  - **Acceptance:** 5 patrones identificados con evidencia (citas a routines reales del parque).
  - **Commit:** `docs(motion): identificación 5 patrones composicionales motion parque`

---

### M3.2 · Diseño del módulo de detección

- [ ] **T3.2.1** — Decidir arquitectura: nuevo `rockwell_comprehender/motion_pattern_library/` vs extensión de `patterns.py`. Documentar decisión en `docs/01_Decisiones_Tecnicas.md` como DT-011.
  - **Output:** DT-011 documentada con rationale.
  - **Acceptance:** decisión firmada por owner (acuerdo explícito).
  - **Commit:** `docs(arch): DT-011 — arquitectura motion patterns library`

---

### M3.3 · Implementación

- [ ] **T3.3.1** — Implementar el módulo según DT-011. Estructura mínima: dataclass `MotionPattern(name, instructions_required, context_hints, ...)`, API `detect_motion_patterns(project) -> list[MotionPattern]`.
  - **Output:** módulo nuevo con los 5 patterns codificados.
  - **Acceptance:** smoke test contra los 3 L5X — patterns esperados se detectan en cada uno.
  - **Commit:** `feat(motion): library motion patterns + detector funcional`

---

### M3.4 · Validación contra parque

- [ ] **T3.4.1** — Ejecutar detector contra los 3 L5X del parque, documentar matches detectados, false positives, false negatives.
  - **Output:** `docs/Test/motion_patterns_validation.md`.
  - **Acceptance:** ≥80% de los patterns esperados se detectan correctamente; documentar gaps.
  - **Commit:** `test(motion): validación detector contra 3 L5X parque`

---

### M3.5 · Update capacidad %

- [ ] **T3.5.1** — Actualizar capacidad #4: 50% → ~75%. Recalcular global.
  - **Acceptance:** sección 0 refleja Phase 3 = 100%.
  - **Commit:** `docs(plan): cierre Phase 3 — composición motion`

---

## 6. PHASE 4 · Inferencia funcional de programas

**Objetivo:** Subir capacidad #7 de 80% → 95%. Hoy sabemos qué tasks/programs/routines existen estructuralmente, pero no QUÉ HACE cada programa semánticamente.

**Criterio de éxito:** Clasificador funcional de programas con confianza ≥0.8 contra los 3 L5X del parque.

**Estimación total:** 1-2 sesiones.

---

### M4.1 · Diseño de heurísticas

- [ ] **T4.1.1** — Definir taxonomía mínima viable de tipos de programa: `motion_control`, `safety`, `communication`, `hmi_interface`, `init_setup`, `sequence_logic`, `data_processing`, `unknown`. Definir heurísticas por tipo (instrucciones presentes, namespaces de tags, AOIs invocadas).
  - **Output:** `docs/01_Decisiones_Tecnicas.md` DT-012 con taxonomía + heurísticas.
  - **Acceptance:** DT-012 firmada por owner.
  - **Commit:** `docs(arch): DT-012 — taxonomía + heurísticas inferencia funcional programas`

---

### M4.2 · Implementación

- [ ] **T4.2.1** — Implementar `infer_program_role(program) -> ProgramRole` en `rockwell_comprehender/patterns.py` (o módulo separado según DT-012).
  - **Output:** función + dataclass `ProgramRole(name, role, confidence, evidence)`.
  - **Acceptance:** smoke test devuelve role+confidence para cada program de los 3 L5X.
  - **Commit:** `feat(patterns): inferencia funcional de programas`

---

### M4.3 · Validación

- [ ] **T4.3.1** — Ejecutar inferencia contra los 3 L5X. Owner valida manualmente las clasificaciones (acceptance manual, no automática — porque no hay ground truth).
  - **Output:** tabla program × role × confidence en `docs/Test/program_role_inference.md`.
  - **Acceptance:** owner aprueba ≥80% de las clasificaciones (cumplir con confianza ≥0.8).
  - **Commit:** `test(patterns): validación inferencia funcional programs`

---

### M4.4 · Update capacidad %

- [ ] **T4.4.1** — Actualizar capacidad #7: 80% → ~95%. Recalcular global.
  - **Commit:** `docs(plan): cierre Phase 4 — inferencia funcional programas`

---

## 7. PHASE 5 · Migration K6000→K5700 (Pañalera N2 specific)

**⚠️ Pre-requisito:** Owner confirma que el proyecto Pañalera N2 (migración K6000→K5700) sigue siendo caso real activo. Si es legacy/cancelado → esta phase se mueve a PARKED.

**Objetivo:** Crear `migration_library/` con tabla de mappings K6000 ↔ K5700 (atributos de eje, AOIs, parámetros, instrucciones específicas).

**Estimación total:** 1-2 sesiones (cruce de manuales 2094-UM001/UM002 vs 2198-UM002 vía NotebookLM).

---

### M5.1 · Confirmación de scope con owner

- [ ] **T5.1.1** — Owner confirma activo / inactivo del caso Pañalera N2. Si activo: continuar M5.2. Si inactivo: mover Phase 5 a PARKED, recalcular global (denominador baja de 22 a 18).
  - **Acceptance:** decisión documentada en este doc.

---

### M5.2 · Diseño + estructura de la migration table

- [ ] **T5.2.1** — Diseñar dataclass `MigrationMapping(k6000_aspect, k5700_equivalent, transformation_notes, citation_origin, citation_destination)` y módulo `rockwell_comprehender/migration_library/`.
  - **Output:** estructura del módulo + dataclass + API básica.
  - **Acceptance:** smoke test (módulo importable, dataclass usable).
  - **Commit:** `feat(migration): scaffolding K6000→K5700 migration library`

---

### M5.3 · Curación batch via NotebookLM

- [ ] **T5.3.1** — Curar 30 mappings críticos K6000→K5700 (axis attributes, motion AOIs equivalents, parameter renames). Batches de 5-10.
  - **Output:** 30 entries en migration_library.
  - **Acceptance:** smoke test (`get_mapping("K6000.MotorType")` retorna equivalente K5700 con citation a manuales fuente).
  - **Commit:** `feat(migration): 30 mappings K6000→K5700 curados`

---

### M5.4 · Validación contra CINTA (caso real)

- [ ] **T5.4.1** — Aplicar el migration library contra CINTA (4 ejes K6000) para producir un "migration report" simulando los axis equivalentes en K5700.
  - **Output:** `docs/Análisis/CINTA_migration_simulation.md`.
  - **Acceptance:** report cubre los 4 ejes con mappings explícitos.
  - **Commit:** `test(migration): aplicación CINTA → simulación K5700`

---

## 8. DONE LOG (append-only)

> Cada commit cerrado se anota acá con: fecha, task ID, commit hash, outcome 1 línea.

### Pre-plan (trabajo construido antes del Plan v2)

| Fecha | Asset/Capacidad | Notas |
|-------|-----------------|-------|
| ... | Toolkit v0.1 (loader/mapamental/lupa/reporters) | base instalada |
| ... | Toolkit v0.2 (tracer + RLL tokenizer) | DT-010 cumplido |
| ... | Toolkit v0.3 (Capa C + Capa D inicial) | 8 instructions iniciales |
| 2026-05-03 | feat(library): MAM + persiste MAOC (commit `38fe694`) | 8→9 entries |
| 2026-05-03 | feat(library): batch 5 motion (commit `1783c67`) | 9→14 entries |
| 2026-05-03 | docs(backlog): 4 items (commit `f6b3d5d`) | Backlog formalizado |
| 2026-05-03 | feat(library): batch 3 motion (commit `b280a67`) | 14→17 = 100% motion parque |
| 2026-05-03 | feat(fault-codes): pilot 8 K5700 (commit `96c91f5`) | Sub-módulo arch B validada |

### Working tree pendiente de commit (al cierre de sesión 2026-05-03)

| Archivo | Cambio | Commit message propuesto |
|---------|--------|--------------------------|
| `rockwell_comprehender/fault_code_library/__init__.py` | +10 entries (8→18 K5700) | `feat(fault-codes): +10 K5700 cubriendo categorías y prefixes (PARKED después de esto)` |
| `rockwell_comprehender/patterns.py` | +57 líneas Diatec extension | `feat(patterns): Capa C Diatec extension — function domains + axis control (cierra Backlog #1)` |
| `rockwell_comprehender/tokenizer/__init__.py` | +1 línea export ST | (parte del commit ST tokenizer) |
| `rockwell_comprehender/tokenizer/st_tokenizer.py` | +172 líneas nuevo | `feat(tokenizer): ST tokenizer — captura motion + AOI calls de routines ST` |
| `docs/PLAN_DE_TRABAJO.md` | nuevo (este doc v2) + CLAUDE.md ref | `docs(governance): plan de trabajo v2 ejecutable + CLAUDE.md anti-deviation` |

### Phase 1+ tasks (se llenan a medida que se cierran)

_(vacío — phase 1 todavía no arrancada)_

---

## 9. PARKED (explícitamente NO se hace ahora)

| Item | Razón parked | Trigger para des-parkear |
|------|--------------|--------------------------|
| **Más fault codes K5700** (faltan ~180) | Tangencial al objetivo "comprender L5X depth senior". El sub-módulo está instalado como base; curar más NO mueve la aguja del caso empalme. | Aparece caso real de diagnóstico de drives específico. |
| **Fault codes K6000, GuardLogix safety, ControlLogix** | Misma razón ↑ | Idem |
| **Hardware module specs library curada offline** | Ya consultable vía NotebookLM. ROI bajo para visión. | Necesidad offline / distribución a usuarios sin NotebookLM Pro. |
| **PDF Extractor pipeline** (Backlog #4) | Diferida hasta library >25 entries OR aparece necesidad CI/offline. | Ver Backlog #4 para triggers explícitos. |
| **Tokenizer FBD + SFC** | Bajo uso en parque (CPPIM 2 FBD, 0 SFC). RLL+ST cubren >95%. | Aparece L5X con uso intensivo de FBD/SFC. |
| **Ruflo Intelligence layer fixes** | Backlog #2/#3 — esperar respuesta upstream. | Respuesta upstream del repo Ruflo. |
| **More function_domains en Capa C** (transport, accumulator, vacuum, blowing) | No hay caso real que los justifique en parque actual. | Aparece L5X con esa lógica. |

---

## 10. DISCOVERED (cosas fuera del plan que aparecen — NO ejecutar, solo registrar)

> Append-only. Owner revisa periódicamente y decide si entra al plan, va a PARKED, o se descarta.

_(vacío al momento de creación del plan v2)_

---

## 11. RECURSOS PARA EL OWNER (referencia rápida)

### Cómo medir avance entre sesiones

1. Abrir este doc.
2. Sección 0 (Scoreboard): ver % de cada phase.
3. Sección 8 (Done Log): ver qué se cerró desde la última revisión.
4. Sección 10 (Discovered): ver si hay decisiones pendientes de owner.

### Cómo arrancar una sesión

1. Sesión lee este doc (CLAUDE.md fuerza esto).
2. Sesión identifica próxima task NO marcada `[x]`, no bloqueada, no en PARKED.
3. Sesión confirma con owner solo si la task tiene ambigüedad o si descubre algo no planeado.
4. Ejecuta. Cuando cumple acceptance: commitea automáticamente con el mensaje provisto.
5. Marca `[x]` + recalcula scoreboard.

### Cómo coordinar 2 chats en paralelo

- Cada chat marca su task como `[~]` (in progress) en lugar de `[ ]` antes de empezar.
- Al cerrar, marca `[x]`.
- Otro chat ve `[~]` y elige otra task.
- **Recursos NO paralelizables:** NotebookLM (1 chat solo), `instruction_library/__init__.py` (1 chat editor a la vez), memoria persistente.
- **Patrón recomendado para split:** chat A toma una phase entera (ej. Phase 2), chat B toma otra (ej. Phase 4). Phases son ortogonales.

### Cómo agregar nueva task al plan

NO se agrega unilateralmente. Owner aprueba. Insertar en la phase correspondiente con ID T.X.Y, Output, Acceptance, Commit message. Recalcular denominador del scoreboard.

---

## 12. APÉNDICE — capacidades del proyecto (mapeo a phases)

> Ya no son métricas separadas; cada capacidad sube cuando una phase la mueve.

| Capacidad (visión) | Estado pre-plan | Cubierta por phase |
|--------------------|----------------|---------------------|
| #1 Lectura estructural L5X | 85% | (base instalada — phases nuevas mantienen) |
| #2 Localizar por dominio funcional | 70% | Phase 3 mejora indirectamente |
| #3 Interpretar instrucciones individuales | 60% | **Phase 2** sube a ~85% |
| #4 Semántica composicional motion | 50% | **Phase 3** sube a ~75% |
| #5 Trazar dependencias | 75% | (ya cubierta con ST tokenizer) |
| #6 Roles de tags | 70% | (ya cubierta con Capa C ext) |
| #7 Estructura programa (semántica funcional) | 80% | **Phase 4** sube a ~95% |
| #8 Síntesis diagnóstica end-to-end | 50% | **Phase 1** valida + cierra v0.1 |
| (auxiliar) Migration K6000→K5700 | 25% | **Phase 5** sube a ~70% (si owner activa) |

**Promedio post-plan completo (sin Phase 5):** ~80% (vs ~67% actual).
**Con Phase 5 activa:** ~83%.

---

## 13. CIERRE

Este documento es la fuente de verdad operativa. Su valor está en ser **leído al inicio de cada sesión** y **actualizado al final**.

**Si está desactualizado, está roto.** Es responsabilidad de la sesión activa mantenerlo.

**Si una sesión ignora el plan, el owner tiene derecho a parar el trabajo y rehacer.**

**Reviewer:** Hedi Vásquez Mayor.
