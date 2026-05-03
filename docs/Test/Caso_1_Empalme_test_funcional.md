# Test funcional — Caso #1 (empalme con velocidad excesiva)

**Caso:** Caso #1 del catálogo (`docs/03_Casos_de_Uso_Reales.md`) — el caso paradigma.
**Fecha:** 2026-05-02
**Proyecto L5X:** `parque_l5x/CINTA_LAMINADA_M2_2024.L5X`
**Versión del paquete:** `rockwell_comprehender` v0.1.0
**Modalidad:** Opción B (test ejecutado dentro de Claude Code, simulando turnos conversacionales del Claude virtual con skill cargado)
**Ejecutor:** Claude Code

---

## Resumen ejecutivo

✅ **Test pasa.** El caso se resuelve en **4 turnos conversacionales del Claude virtual** (T1, T3, T4, T6, descartando T2 y T5 que son intervención del usuario y verificación API respectivamente). Bajo el techo de ≤6 turnos definido en el catálogo de casos.

La causa raíz se identificó: el operador carga `Data.HmiNewDiameter` desde el HMI; ese valor propaga vía dos AOIs hasta el cálculo del transitorio Pre-Start, donde un valor pequeño infla el setpoint inicial del eje y produce el arranque rápido reportado.

**Hallazgo importante sobre la predicción del HANDOFF:** la fórmula `V_new = V_master × (D_master / D_new)` mencionada en `HANDOFF_v01_to_N2.md` y en `SKILL.md` como ejemplo del cálculo es una **idealización pedagógica**, no la fórmula real del proyecto. La fórmula real del transitorio es híbrida (basada en `MaxRadius - ReelRadius` y posición del dancer), pero el **principio causal predicho se cumple**: el input HMI alimenta el setpoint inicial. Vale la pena anotar esto en futuras versiones de los docs para no inducir expectativa errónea.

---

## Conteo de turnos vs criterio

| Turno | Actor | Acción | Cuenta |
|-------|-------|--------|:--:|
| T1 | Claude (virtual) | Carga proyecto, busca AOIs `Splice`/`Unwinder`, identifica que solo `AHT_CtcSplicer` y `AHT_Unwinder` están instanciados, pregunta aclaración | ✓ |
| T2 | Hedi (simulado) | "Solo en empalme con máquina andando" | — |
| T3 | Claude | Lee `AHT_Unwinder/Logic`, `AHT_CtcSplicer/Logic`, `DancerCorAndNewRadiusComputation/Logic`. Identifica que el cálculo del transitorio está en el último, no en el splicer | ✓ |
| T4 | Claude | Trace manual: `search("HmiNewDiameter")`, `search("ReelRadiusA")`, lee `RadiusComputation/Logic`. Identifica el camino HMI→setpoint | ✓ |
| T5 | Claude | (verificación API: parameters del AOI para mapeo args↔params — meta, no conversacional) | — |
| T6 | Claude | Presenta hipótesis y recomendaciones | ✓ |

**Total turnos del Claude virtual: 4.** Criterio v0.1 (≤6): cumplido.

---

## Trace causal completo (verificado contra el código)

```
[1] Operador HMI → Data.HmiNewDiameter
        (input REAL del operador; rango esperado en mm o décimas)
            │
            ▼
[2] AHT_Unwinder/Logic Rung 10
        DIV(Data.HmiNewDiameter, 2, LocHmiNewRadius)
            │
            ▼
[3] AHT_Unwinder/Logic Rung 20
        MOV(LocHmiNewRadius, LocNewRadius)
            │
            ▼
[4] AHT_Unwinder/Logic Rung 13 (invocación a RadiusComputation)
        arg8=LocNewRadius → param 9 InitRadius (Input REAL)
        arg14=Data.ReelRadiusA → param 15 RadiusComputation (InOut REAL)
            │
            ▼
[5] RadiusComputation/Logic Rung 0
        [XIC(CutterA) ,XIC(CutterB) ,XIC(Start)] ONS(Aux4)
            MOV(InitRadius, RadiusComputation_actual)
            MOV(InitRadius, RadiusComputation_Avg)
            MOV(InitRadius, RadiusComputation)
        → escribe a Data.ReelRadiusA vía pin InOut
            │
            ▼
[6] AHT_Unwinder/Logic Rung 17 (invocación a DancerCorAndNewRadiusComputation)
        arg con Data.ReelRadiusA → param ReelRadius
            │
            ▼
[7] DancerCorAndNewRadiusComputation/Logic Rung 4 (Pre-Start)
        XIO(AxStart) XIO(AutocalcRaduisRunning) XIC(EnablePreStart)
        [XIC(AutoCalcRadiusDone), XIO(EnableInitRadiusAutocalc)]
        CPT(LocCorrection,
            (((1200 - ReelRadius) / Kp1DancerCorreection)
              × ((20 - DancerPosition) / 2)) / 2)
            │
            ▼
[8] DancerCorAndNewRadiusComputation/Logic Rung 9
        MAJ(Ax, LocMAJ1, Direction, LocCorrection1, ...)
        → comando de movimiento al eje físico
            │
            ▼
[9] Eje físico arranca con velocidad proporcional a LocCorrection
```

**Mecanismo de la falla:**

Si el operador introduce un `HmiNewDiameter` menor al diámetro real del rollo cargado:

- `LocHmiNewRadius = HmiNewDiameter / 2` → pequeño
- En el evento de splice (`CutterA` activo), `Data.ReelRadiusA` se inicializa con ese valor pequeño (vía `InitRadius` → `RadiusComputation_actual`)
- En el Rung 4 del Pre-Start: `(1200 - ReelRadius)` ← grande (porque `ReelRadius` es chico)
- `LocCorrection` resultante: inflado
- `MAJ` arranca el eje con velocidad mayor a la apropiada
- El rollo (que físicamente es más grande de lo cargado) acelera más rápido de lo que el sistema esperaba → enredo del material.

**Constante hard-coded relevante:** `1200` en la fórmula del Rung 4 — probablemente representa el radio máximo del rollo (en décimas de mm o unidades equivalentes). Vale la pena confirmar con Hedi si ese valor es coherente con el rollo físico máximo del debobinador.

---

## Recomendaciones (lo que el Claude virtual le diría a Hedi en T6)

1. **Validar procedimiento de carga del `HmiNewDiameter`.** El sistema confía 100% en el valor del operador para el setpoint inicial. Una validación de rango (`HmiMinDiameter ≤ HmiNewDiameter ≤ HmiMaxDiameter`) en la pantalla HMI antes de aceptar el valor reduciría drásticamente el riesgo.

2. **Default inteligente.** Considerar que `HmiNewDiameter` por defecto sea el último radio actualizado de la corrida anterior (`Data.ReelRadiusA × 2` previo al splice) o `HmiManualDiameter`, en lugar del último valor introducido por el operador (que puede estar obsoleto).

3. **Clamp del transitorio Pre-Start.** En `DancerCorAndNewRadiusComputation/Logic Rung 4`, agregar un `LIM` o saturación al `LocCorrection` para que no exceda un valor máximo seguro hasta que el dancer estabilice (timer `T1.DN`). El Rung 3 ya divide por `GainCorrectionSplicer` durante el splice — un mecanismo similar de amortiguamiento aplicado al Pre-Start cubriría el escenario.

4. **Revisar la constante `1200`.** Verificar si corresponde al radio físico máximo del rollo en este debobinador. Si el rollo máximo real es distinto, la fórmula está desafinada y la corrección puede ser estructuralmente excesiva o insuficiente.

5. **Telemetría/log.** Si el HMI puede registrarlo, loguear el `HmiNewDiameter` cargado en cada splice junto con el `Data.ReelRadiusA` real medido posteriormente — un delta sistemático grande indicaría operador con error recurrente.

> Estas recomendaciones son a nivel **diagnóstico desde el código**. La validación final (probar en máquina, ver datos de operación reales) está fuera del alcance del paquete y queda en el equipo de mantenimiento.

---

## Hallazgos meta — sobre el paquete v0.1

### Lo que funcionó bien

- **Carga rápida.** `load_project()` < 1 segundo, Mapa Mental completo y útil para acotar dominios desde el primer turno.
- **`AOIDetail.parameters` expuesto.** Permitió mapear posicionalmente los argumentos de invocación contra la firma del AOI sin abrir el L5X manualmente. Crítico para el trace causal del Turno 4.
- **`search()` distingue location.** Filtrar hits por prefijo `AOIs/<name>/` permitió identificar fácilmente cuáles AOIs son **definidos vs instanciados** (4 de 5 splicers son código muerto en este proyecto — ver hallazgo bonus abajo).
- **`get_aoi(name)` con `routines` dict.** Acceso directo al código de cada rutina del AOI (`Logic`, `EnableInFalse`).
- **Categoría `aoi_naming_collision` en observations** (vista en HANDOFF, validada aquí): el proyecto define `Unwinder` y `AHT_Unwinder` (este último el activo), `DancerCorAndNewRadiusComputation` y `AHT_DancerCorAndNewRadiusComputation` (sin-prefijo el activo). La detección automática es valiosa.

### Limitaciones encontradas (input para v0.2)

1. **`search()` es plano y poco contextual.**
   - Los hits muestran `snippet` truncado a ~90-120 chars; el rung completo se obtiene cargando todo el routine.
   - **Sugerencia v0.2:** `SearchHit.rung_full` con el rung completo tal cual aparece en código.

2. **`search()` no distingue writers de readers.**
   - Para identificar quién escribe `Data.ReelRadiusA` tuve que leer la definición de `RadiusComputation` y mirar el InOut pin manualmente. Esto NO escala — proyectos grandes harían el flujo intratable.
   - **Sugerencia v0.2:** `project.writers_of(tag)` y `project.readers_of(tag)` con análisis del tipo de operador (OTE/OTL/OTU/MOV/CPT como writers; XIC/XIO/GRT/LES como readers; pin Input/Output/InOut como writer condicional).

3. **El mapeo argumento↔parámetro es manual.**
   - Para mapear `arg8 (LocNewRadius)` → `param 9 (InitRadius)` tuve que contar posiciones a mano. Útil para AOIs con 5 parámetros, doloroso para AOIs con 30+ como `AHT_CtcSplicer`.
   - **Sugerencia v0.2:** `project.resolve_invocation(location, rung)` que devuelva un dict `{param_name: argument_expression}` completo.

4. **Trace de variables locales requiere lectura completa del routine.**
   - `LocHmiNewRadius → LocNewRadius` lo encontré leyendo todo `AHT_Unwinder/Logic`. En proyectos grandes con routines de 100+ rungs no escala.
   - **Sugerencia v0.2:** `project.trace_back(tag, scope=routine_or_aoi, depth=N)` que retorne la cadena causal hacia atrás.

5. **Encoding console (no es del paquete, es de Windows pero relevante para uso real).**
   - `print(p.mapa_mental)` en la consola por defecto de Windows truena con `UnicodeEncodeError` en caracteres no-ASCII (p.ej. el campo Owner del L5X CINTA tiene "用户"). Workaround: `PYTHONIOENCODING=utf-8` o redireccionar a archivo. El paquete genera correctamente; el `print` es el que falla.
   - **Sugerencia:** documentar este punto en el README o agregar guard en el reporter de markdown que escape caracteres no-codificables si va a stdout.

---

## Hallazgos sobre el L5X CINTA_LAMINADA_M2_2024 (no del paquete)

### Código muerto (Caso #5 indirectamente cubierto)

De los 26 AOIs definidos:

- **5 splicers definidos, 1 usado:** solo `AHT_CtcSplicer` se instancia (desde `AHT_Unwinder/Rung 11`). Los otros 4 (`CtcDiatecSplicer`, `CtcDiatecSplicerBuffer`, `FullSpeedSplicer`, `FullSpeedSplicer2`) están definidos pero ningún programa o AOI los invoca.
- **2 unwinders definidos, 1 usado:** `AHT_Unwinder` se invoca desde `Programs/Axis/Routines/Unwinders`; `Unwinder` standalone no aparece en código de programas.
- **2 dancer-radius-computation, 1 usado:** `DancerCorAndNewRadiusComputation` (sin prefijo) se usa; `AHT_DancerCorAndNewRadiusComputation` está definido pero no invocado.

Esto es código muerto candidato a limpieza si el equipo confirma que las versiones no-usadas son legacy de proyectos previos (común en Rockwell — los AOIs se copian entre proyectos y a veces se quedan como respaldo).

### Estructura de empalme embebida

El empalme está **anidado dentro del AOI del debobinador** (`AHT_Unwinder` invoca `AHT_CtcSplicer` en su Rung 11), no en un programa separado. Eso es una decisión arquitectónica válida (mantiene el comportamiento de cada debobinador encapsulado) pero significa que para entender la lógica de splice **hay que leer el AOI del unwinder primero** — el nombre del AOI no lo sugiere obviamente. Esta organización es un patrón de proyecto que el Mapa Mental podría ayudar a destacar (p.ej. "AOI X invoca AOI Y, Z").

---

## Status del Caso #1 después de este test

- En `docs/03_Casos_de_Uso_Reales.md`, la sección "Validación" del Caso #1 dice "Pendiente — caso a probar contra v0.1 cuando esté construida y validada en arquitecturas distintas".
- Con este test, el caso queda **✅ Validado en CINTA_LAMINADA_M2_2024 dentro del techo de turnos.**
- Pendiente para validación cruzada en `AQL_M2.L5X` (la otra arquitectura de validación, ControlLogix 1756-L61 con 17 ejes) — útil para confirmar que el flujo no depende de la estructura específica de CINTA. Sugerencia: ejecutar el mismo test sobre AQL_M2 buscando su empalme equivalente, **si AQL_M2 tiene debobinador con empalme** (puede no tenerlo — es de otro proceso).

---

## Conclusión

El paquete `rockwell_comprehender` v0.1.0 **resuelve el caso paradigma dentro del criterio de éxito**, validando empíricamente la arquitectura "Mapa Mental + Lupa" y la utilidad práctica del skill como herramienta de diagnóstico real (no solo como código).

Las limitaciones encontradas durante el flujo manual (search plano, sin writers/readers, mapeo args↔params manual) son **exactamente las capacidades que v0.2 está pensada para cubrir** — el test funcional ratifica el roadmap. Si Hedi decide arrancar v0.2, este reporte tiene una lista de issues concretos y priorizados para el diseño del módulo `tracer.py`.

Si en cambio decide seguir con v0.1.x (Camino A del HANDOFF) o batch del parque (Camino C), el paquete cumple su contrato actual.
