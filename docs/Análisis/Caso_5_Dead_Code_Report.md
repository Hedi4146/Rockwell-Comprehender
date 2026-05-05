# Caso #5 — Reporte de detección de código muerto

**Fecha:** 2026-05-04
**Script:** [docs/Test/_caso5_dead_code.py](../Test/_caso5_dead_code.py)
**Outputs raw:**
- [docs/Test/_caso5_dead_code_CINTA_output.txt](../Test/_caso5_dead_code_CINTA_output.txt)
- [docs/Test/_caso5_dead_code_AQL_output.txt](../Test/_caso5_dead_code_AQL_output.txt)

---

## Metodología

El script detecta 3 categorías clásicas de código muerto en proyectos Rockwell L5X usando exclusivamente la API ya construida del paquete `rockwell_comprehender` v0.1+ (sin código nuevo en el paquete):

### Categoría 1 — AOIs definidas pero no invocadas

Para cada AOI en `project.aois`, se busca el patrón `\b{AOI_name}\(` (regex con word boundary) en el `code` de TODAS las routines de programs y AOIs del proyecto. La routine self del AOI se excluye (un AOI no se cuenta como auto-invocador). Si ningún match: AOI marcado como no invocado.

**Por qué regex y no `project.search()`:** el `search()` v0.1 hace match case-insensitive substring, lo cual produce falsos positivos en nombres con prefijos compartidos (`FullSpeedSplicer` matcheando dentro de `FullSpeedSplicer2`). El regex con `\b...(` exige boundary + paréntesis abierta — solo hace match cuando el nombre aparece como invocación real.

### Categoría 2 — Routines no llamadas

Para cada routine de program (no de AOI), se considera *alcanzable* si:
- Es `main_routine` o `fault_routine` de su Program, o
- Aparece como target de `JSR(routine_name, …)` en el código de cualquier otra routine del **mismo program** (Studio 5000: JSR es intra-program; cross-program no existe).

Las routines de AOI siempre se consideran alcanzables — son invocadas implícitamente al invocar el AOI.

### Categoría 3 — Tags controller-scoped huérfanos

Para cada tag con `scope == "controller"`, se llama a `project.references_of(tag.name)` (tracer v0.2). Si la lista retornada es vacía, el tag no aparece como operando en ningún rung RLL ni línea ST.

**Filtros aplicados** (excluidos del análisis porque son referenciados por configuración, no por código):
- `datatype` empezando con: `AXIS_*`, `MOTION_GROUP`, `COORDINATE_SYSTEM`, `TASK`, `PROGRAM`, `ROUTINE`, `MODULE`, `MESSAGE`, `CONNECTION_STATUS`, `ALARM`
- Tags con `motion_module` no vacío (referenciados por motion module config)

---

## Hallazgos — CINTA_LAMINADA_M2_2024.L5X

**Proyecto:** CompactLogix 1768-L43, RSLogix 5000 v20.01, 4 ejes K6000 SERCOS.
**Inventario:** 4 programs, 17 routines, 26 AOIs, 209 tags controller.

### AOIs no invocadas (12 de 26 = **46%**)

```
AHT_DancerCorAndNewRadiusComputation
AHT_DriveFault_Decoding
AHT_Enable_Reject
AHT_ON_OFF_CounterValve
AHT_Reject_Block
AHT_SyncroAxis
AxisBlock
CtcDiatecSplicer
CtcDiatecSplicerBuffer
FullSpeedSplicer
FullSpeedSplicer2
Unwinder
```

**Lectura:** los 5 AOIs ya identificados durante el test del empalme (`CtcDiatecSplicer`, `CtcDiatecSplicerBuffer`, `FullSpeedSplicer`, `FullSpeedSplicer2`, `AHT_DancerCorAndNewRadiusComputation`, `Unwinder`) se confirman. Adicionalmente aparecen **6 AOIs más no invocadas** que NO eran obvias del análisis del empalme: `AHT_DriveFault_Decoding`, `AHT_Enable_Reject`, `AHT_ON_OFF_CounterValve`, `AHT_Reject_Block`, `AHT_SyncroAxis`, `AxisBlock`. La proporción 46% sugiere que CINTA es un proyecto altamente derivado por copy-paste de templates previos sin limpieza posterior.

### Routines no alcanzables (0 de 17 routines de program)

```
(ninguna)
```

Todas las routines son `main_routine`, `fault_routine`, o tienen al menos un `JSR(target, …)` que las invoca dentro del mismo program.

### Tags controller huérfanos (55 de 201 analizados = **27%**)

55 tags sin referencias en código tras filtrar tipos especiales (8 tags excluidos por filtros AXIS_*/etc.).

Categorías observables a ojo:
- **Constantes/legacy:** `ON`, `OFF`, `SAVE_SIZE_ON`, `LimitGlueValve`, `EnableAuxCam` — patrón clásico de tags definidos por convención que nunca se referenciaron
- **Auxiliares de scratchpad:** `aux35`–`aux38`, `Timer_step1`, `Timer_step2`, `TIMER_ACQL` — variables de uso temporal nunca consumidas
- **HMI legacy:** `HmiOldSize`, `HmiManualEnabled`, `HmiSizeConfirm`, `HmiSizeSelector`, `HmiProductLengthJunior/Maxi/Midi/Mini` — variantes de HMI quizá deprecadas
- **Per-axis dead:** `M1Data`, `M2Data` (tipo `Data` — UDT), `M1_FaultCode`, `M2_FaultCode`, `M3_FaultCode`, `M4_FaultCode` — ⚠️ ver caveat #1 abajo
- **Motion instructions sin usar:** `MDOC1`, `VirtualMRP` — tipo `MOTION_INSTRUCTION`
- **Backing tag obsoleto:** `UNW_NW` (tipo `Unwinder`, el AOI legacy también muerto)

---

## Hallazgos — AQL_M2.L5X

**Proyecto:** ControlLogix 1756-L61, Studio 5000 v20.01, 17 ejes productivos, 3 redes.
**Inventario:** 7 programs, 29 routines, 24 AOIs, 775 tags controller.

### AOIs no invocadas (4 de 24 = **17%**)

```
AxisBlock
Axis_Faults_CIP
Axis_ObjectCIP
Radius_Computation
```

**Lectura:** AQL es notablemente más limpio que CINTA en ratio de AOIs no invocadas (17% vs 46%). Hallazgo cruzado interesante: **`AxisBlock` aparece como dead-code en AMBOS proyectos** — es probablemente un AOI template que se incluye por convención de empresa/integrador pero nunca se invoca. Vale la pena confirmar con el equipo si es legacy borrable o template intencional.

### Routines no alcanzables (3 de 29 = **10%**)

```
Axis/R001_A_Corte_AQL
Axis/R001_B_Estampador_AQL
Axis/R002_Corte_WB
```

**Hallazgo importante:** estas tres routines del program `Axis` tienen nombres con prefijos `R001`/`R002` que sugieren un orden numerado de ejecución, pero **no aparecen como JSR target en ninguna routine del program Axis**. Posibles explicaciones (no decididas, requieren confirmación con Hedi/equipo de planta):
- Features comentadas/deshabilitadas que se dejaron en el L5X por si se reactivan
- Routines preparadas para una futura extensión de la máquina
- Migración incompleta (nombres sugieren un patrón de organización numerada que se abandonó)

### Tags controller huérfanos (55 de 735 analizados = **7,5%**)

55 tags sin referencias tras filtros (40 excluidos — significativamente más que CINTA por la mayor cantidad de tags AXIS_* en una arquitectura con 17 ejes).

Categorías observables a ojo:
- **Array template paralelo:** `HmiTempM1` … `HmiTempM16` — 16 tags consecutivos tipo INT con sufijo numérico, patrón de copy-paste de un template que define 16 slots aunque no todos se usen
- **Homing legacy:** `Homing_Direction_M4`/`M9`, `Homing_Speed_M4`/`M5`/`M9`, `Start_Homing_M4`, `MAM_HOME_M4`/`M5`/`M9` — secuencia de homing definida pero no consumida (posible feature deshabilitada en producción)
- **Sizing per-station:** `S04N74_DeltaPos_Size_L/M/S/XL`, `S04N75_DeltaPos_Size_*`, `S04N79_DeltaPos_Size_*` — tags de delta-position por tamaño de producto, definidos pero nunca leídos
- **Constantes legacy:** `ON`, `OFF`, `MDOC1` — los mismos nombres aparecen también en CINTA (template común)
- **Motion sin usar:** `MAM_HOME_M4`/`M5`/`M9` — motion instructions probablemente preparadas para un homing automático que se reemplazó por homing manual

---

## Comparativa CINTA vs AQL

| Categoría | CINTA | AQL |
|-----------|------:|----:|
| AOIs no invocadas | **46%** (12/26) | 17% (4/24) |
| Routines no alcanzables | 0% (0/17) | 10% (3/29) |
| Tags controller huérfanos | 27% (55/201) | 7,5% (55/735) |
| AOI común dead-code en ambos | `AxisBlock` ← template empresa | `AxisBlock` ← idem |

**Lectura cruzada:** AQL está mejor mantenido que CINTA en términos de proporción de tags huérfanos (~3,6× menos). CINTA tiene más AOIs muertas — coherente con el hallazgo del test del empalme de que el proyecto contiene varios splicers legacy. AQL muestra el patrón opuesto: pocos AOIs muertos, pero algunas routines del program Axis quedaron desconectadas (potencial WIP/feature flag).

---

## Caveats — limitaciones honestas del análisis

1. **`M1Data`/`M2Data` en CINTA pueden ser falsos positivos.** Estos tags (tipo `Data` — UDT) aparecen como huérfanos según `references_of`, pero podrían usarse como **backing tags de instancias de AOI** (e.g. `AHT_Unwinder(M1Data, …)`). Si el tracer v0.2 actual no instrumenta backing tags de AOI invocations en su xref, los tags de instance data se reportan erróneamente como huérfanos. **Acción sugerida (input para v0.2.x):** verificar si `references_of` captura backing tags. Si no, agregar instrumentación al `_get_aoi_invocations` para emitir un xref entry con `usage="both"` para `args[0]` (la convención del tracer marca `args[0]` como backing).

2. **AOI "no invocada" puede estar referenciada por nombre sin invocación directa.** Una AOI puede aparecer en código como tipo de tag (`MyTag : MyAOI`) sin tener una invocación `MyAOI(...)`. El script no detecta este caso. En la práctica, una AOI que solo se usa como tipo (sin invocación de ejecución) sí es código efectivamente muerto desde el punto de vista del runtime: nadie ejecuta su lógica. El reporte es por tanto correcto en intención.

3. **JSR cross-program no se detecta.** Studio 5000 históricamente impone JSR intra-program, pero algunas variantes recientes permiten ScopeRef. El script asume convención clásica. Si en algún proyecto futuro hay JSR cross-program, podría producir falsos positivos en categoría 2. **Mitigación:** documentado aquí; cuando aparezca el caso real, ampliar el scan.

4. **Routines protected (Source Protection).** Si una AOI o routine está protegida (`protected=True`), su `code=""` y por tanto no se puede saber qué invoca. En CINTA y AQL no hay protected routines significativas; en CPPIM sí (Amantrini integraciones). En tales proyectos el reporte tendría falsos positivos: AOIs invocadas dentro de routines protected aparecerían como "no invocadas". **Mitigación:** agregar warning explícito al output cuando hay protected routines significativas; lo dejamos como TODO menor.

5. **Tags constantes/literales nunca se reportan.** El script analiza tags declarados; constantes inline en código (`100`, `True`, etc.) no son tags. Esto NO es una limitación del script — es la naturaleza del concepto "tag huérfano".

6. **No detecta inconsistencias semánticas.** El script no sabe si `M1_FaultCode` es semánticamente equivalente a `Data.M1FaultCode` (campo de UDT) — los trata como tags distintos. Esto también es correcto: son entidades distintas en el L5X.

---

## Conclusión

El Caso #5 del catálogo de casos de uso queda **✅ accionable mediante este script**. Las 3 categorías clásicas de código muerto se detectan automáticamente con la API ya construida del paquete (sin código nuevo, cumpliendo DT-008 stack mínimo y DT-009 no-stubs).

Los hallazgos contra los 2 L5X de validación generan **insights reales y accionables** para el equipo de planta: AOIs templates legacy candidatas a limpieza, routines del Axis program de AQL probablemente deshabilitadas que merecen confirmación, tags huérfanos que indican código históricamente derivado por copy-paste.

El caveat #1 (backing tags de AOI invocations posiblemente no capturados por `references_of`) es la mejora más relevante a anotar como input para v0.2.x.

---

*Generado 2026-05-04 por Claude Code Opus 4.7 sobre el paquete `rockwell_comprehender` v0.1.0 con extensiones v0.2 (tracer + xref). Stack mínimo per DT-008 mantenido.*
