# 04 · INVESTIGACIÓN PREVIA

Resumen de toda la investigación técnica realizada antes de iniciar la construcción y de los hallazgos consolidados durante el desarrollo de v0.1.

---

## Contenido

1. Ecosistema de herramientas Studio 5000 + automatización
2. Evaluación de librerías Python para parsing
3. Generaciones de software RSLogix 5000 / Studio 5000
4. Pilotos de validación realizados
5. Hallazgos sustantivos del proyecto CINTA TWIN
6. Hallazgos sustantivos del proyecto AQL_M2
7. Aprendizajes meta del sprint v0.1

---

## 1 · Ecosistema de herramientas Studio 5000

### Herramientas oficiales de Rockwell

| Herramienta | Capacidad | Limitación clave para nosotros |
|-------------|-----------|--------------------------------|
| **Logix Designer SDK** v2.01+ | Automatización de UI, scripting de proyectos, descargas a PLC | Solo Windows, Python 3.12 estricto, requiere Studio 5000 v36+ + licencia Professional |
| **FactoryTalk Logix Echo V2** | PLC virtual, simulación con motion (Axis-Test Mode K5700) | Licencia separada |
| **Export L5X / L5K / ACD** | Formatos de proyecto | L5X = XML legible (preferido); L5K = legacy; ACD = binario propietario |

### Proyectos comunitarios open-source evaluados

**Bibliotecas de parsing:**

| Proyecto | Lenguaje | Función | Veredicto final v0.1 |
|----------|----------|---------|----------------------|
| `l5x` (jvalenzuela) | Python | API pythónica para L5X | ❌ **Eliminada** (DT-010) — validación práctica mostró que xml.etree es suficiente |
| `acd-tools` (hutcheb) | Python | Parser ACD binario | ❌ Diferida (bugs en v20) |
| `L5Sharp` (tnunnink) | .NET 8 | API tipada para L5X | ❌ Estamos en Python |
| `Allen-Bradley-Toolkit` (cmseaton42) | Python | Wrapper lxml para L5X | ❌ Redundante con `l5x` |
| `L5X-Parsing` (alphabet5) | Python | Script puntual para IO trees | ❌ Cubierto |

**Generación de código:**

| Proyecto | Función | Veredicto |
|----------|---------|-----------|
| `studio5000-AI-Assistant` (rivie13) | MCP server con FAISS + SDK Rockwell + generación L5X | ❌ **No integrar** (DT-003). Filosofía opuesta, stack pesado |
| `l5x2c` (alairjunior) | Transcompila ladder a C para verificación CBMC | ⚠️ Inspiración técnica (tokenizer), no reuso de código |

---

## 2 · Generaciones de software (RSLogix 5000 / Studio 5000)

| Generación | Versiones | Marca | Hito técnico | CPUs principales |
|------------|:---------:|-------|--------------|------------------|
| **G1** | v10–v19 | RSLogix 5000 | L5X import/export desde v17 | L6x, L4x, L3x legacy |
| **transición** | v20 | mixto | v20.04 = RSLogix / v20.05+ = Studio 5000 | L6x, L7x |
| **G2** | v21–v27 | Studio 5000 | Rebrand completo. v22 nunca liberada. v25-v27 raras en campo | L7x, L3x recientes |
| **G3** | v28+ | Studio 5000 | Soporte L8x (5580) | L8x, L7x, L8xES Guard |
| **G3+** | v33+ | Studio 5000 | FactoryTalk Logix Echo integrado, SDK desde v35 | L8x dominante |

**Distribución del parque Softys (estimación de Hedi):**
- 25% en G1 (RSLogix 5000)
- 75% en G2 (Studio 5000 clásico)
- ~25% del G2 migrando a G3 (en curso)

**Validación en v0.1:** Probado contra v20.01 (CINTA_TWIN con 1768-L43) y v20.12 (AQL_M2 con 1756-L61). Cobertura uniforme. Versiones G3+ pendientes de probar pero esperadas funcionales por estabilidad del schema L5X.

---

## 3 · Piloto inicial — comparación ACD vs L5X (2026-05-01)

### Setup

- **Archivo de prueba:** `CINTA_LAMINADA_M2_2024.ACD` (1.04 MB) y `CINTA_LAMINADA_M2_2024.L5X` (1.21 MB)
- **Versión:** RSLogix 5000 V20.01.00 build 3489 (creado 2014, modificado 2024)
- **Identificación:** CINTA TWIN del proyecto Pañalera 2 — 4 ejes K6000 SERCOS

### Resultado

**Vía `acd-tools`:** ❌ Bugs reproducibles — Comments parsing falla, ControllerBuilder error, módulos I/O no extraíbles, AOIs ausentes (0 vs 26 reales), código con hashes sin resolver.

**Vía L5X (xml.etree directo):** ✅ Cobertura completa — 12 modules, 26 AOIs, 17 rutinas, código limpio con nombres legibles, comentarios por rung.

**Veredicto:** L5X gana 21-0 en categorías diferenciadoras. La diferencia es categórica, no incremental.

→ Resultó en DT-001 (L5X como fuente principal).

---

## 4 · Hallazgos sustantivos del proyecto CINTA TWIN

Durante el piloto y la construcción de v0.1, además de validar la herramienta, se descubrió información concreta sobre la máquina real:

### Topología hardware (coincide con Red_MQ2.pdf)

```
1768-L43 (CompactLogix Major 20.13)
├─ Slot 1 [1768-L43] ─ Controlador
├─ Slot 2 [1768-M04SE] ─ Módulo SERCOS
│  ├─ Addr 1: M1 (2094-BC02-M02 — drive principal con bus power)
│  ├─ Addr 2: M2 (2094-BM01 — extension axis)
│  ├─ Addr 3: M3 (2094-BM01 — extension axis)
│  └─ Addr 4: M4 (2094-BM01 — extension axis)
└─ 1768-ENBT/A @ 192.168.3.40
   └─ NODE_Z1 (1734-AENT/B @ 192.168.3.41)
```

### Arquitectura de scheduling

| Task | Tipo | Rate | Programa |
|------|------|:----:|----------|
| MainTask | Continuous | — | MainProgram (proceso) |
| Motion | Event (Motion Group) | 10 ms | Axis (motion) |
| FastTask | Periodic | 8 ms | Reject (rechazo crítico) |
| Task1000ms | Periodic | 1000 ms | ReadPar (parámetros) |

### Framework Andritz/AHT detectado

15 UDTs con prefijo `AHT_` indicando framework reusable de Andritz.

### Hallazgos de v0.1

- ✅ **AOIs duplicadas detectadas automáticamente:** `Unwinder` ↔ `AHT_Unwinder`, `DancerCorAndNewRadiusComputation` ↔ `AHT_DancerCorAndNewRadiusComputation` (refactoring incompleto detectable por la herramienta)
- ✅ **Master tiene canal virtual:** la asociación `motion_module` reveló que Master está en `M2:Ch130` — un canal virtual del módulo M2. Información que la heurística vieja por nombre nunca hubiera detectado.
- ✅ **Bloques de control identificados:** `AB_Virtual1` (controller-scope) + 4 program-scope (`AB_M2`, `AB_M3`, `AB_M71`, `AB_Virtual2` en programa Axis)

---

## 5 · Hallazgos sustantivos del proyecto AQL_M2 (validación generalización)

### Setup

- **Archivo de prueba:** `AQL_M2.L5X` (2.9 MB)
- **Versión:** Studio 5000 v20.12 con ControlLogix 1756-L61
- **Arquitectura compleja:** 3 redes (Ethernet + SERCOS + ControlNet) + 2 EN2TR ring (SynchLink)

### Topología destacada

```
1756-L61 (ControlLogix Major 20.12)
├─ 1756-ENBT/A → 1794-AENT (DEBO_TNT) → 3 módulos POINT I/O
├─ 1756-M16SE (Sercos) → 16 drives Kinetix
├─ 1756-CNB/E (ControlNet) → 2 NODE_* (1734-ACNR/A) → 12 módulos POINT I/O
├─ 1756-IB32/B (Dinput) — controller-local
├─ 1756-OB16E — controller-local
├─ 1756-EN2TR (Anillo_SynchLink_Consumido)
│  └─ 1756-EN2TR (Anillo_SynchLink_Producido)
│     └─ 1756-L61 (Side_Panel_M2 — eje virtual maestro consumido vía SynchLink)
└─ 1756-IB32/B (DInPut_7)
```

### Arquitectura de scheduling

| Task | Tipo | Rate | Programa(s) |
|------|------|:----:|-------------|
| MainTask | Continuous | — | MainProgram |
| Motion | Event | — | Axis, ConsumeAxisAOI, Debo_Tela |
| FastTask | Periodic | 20 ms | Reject |
| Task500ms | Periodic | 555 ms | ReadPar |

### Hallazgos de v0.1

- ✅ **17/17 ejes productivos con motion_module asociado** correctamente al drive físico
- ✅ **Anti-patrón de naming detectado:** los axis tags son `S04N79_UNIDAD_CORTE_WB` y `S04N80_WB_TAMBOR_TRANSF`, pero los drives correspondientes son `M9_507U1:Ch20` y `M10_508U1:Ch21`. **La numeración del eje (N79, N80) no se corresponde con la del drive (M9, M10)** — anti-patrón estructural relevante para mantenimiento que el Mapa Mental ahora expone explícitamente.
- ✅ **Framework distinto al de CINTA TWIN:** AOIs sin prefijo `AHT_`, predominio de `Axis*`, `AOI_*`, `*_Splicer`
- ✅ **Naming semántico funciona:** la inferencia funcional por sustring (`*DANCER*`, `*DEBOB*`, `*CORTE*`, `*ESTAMP*`, etc.) reconoce 19/20 ejes correctamente
- ✅ **CIPSync/SynchLink architecture detected:** EN2TR ring con master consumido desde otro chassis (Side_Panel_M2)

---

## 6 · Aprendizajes meta del sprint v0.1

### 6.1 Validación empírica antes de comprometer dependencias (DT-010)

**Aprendizaje:** una librería puede pasar el test de "no falla" y aún así ser deuda neta. El test real es "¿qué hace por mí que yo no haría con stdlib?".

**Caso concreto:** la librería `l5x` se incluyó en DT-002 con razonamiento aparentemente sólido. Durante implementación se descubrió que xml.etree directo cubría 100% de las necesidades. La librería estuvo en el código como dead weight hasta DT-010.

**Regla operativa derivada:** importar en una rama de exploración, ejercitar las APIs concretas que pensamos usar contra el caso real más complejo disponible, y solo entonces decidir si entra al `pyproject.toml`.

### 6.2 Validación contra archivos reales > diseño en abstracto

**Aprendizaje:** la validación contra **dos** L5X de arquitecturas distintas (CINTA_TWIN y AQL_M2) reveló problemas que un solo proyecto nunca hubiera mostrado:

- Heurística de matching eje↔módulo por nombre falla con naming semántico
- Inferencia funcional por AOI principal genera falsos positivos cuando el AOI es genérico
- Detección de duplicados AOI por prefijo no captura colisiones por underscore/numeración

**Regla operativa derivada:** ningún componente se considera "validado" hasta que se ejercita contra al menos dos casos reales de arquitectura distinta.

### 6.3 Distinción artefactos físicos vs documentación arquitectónica (DT-009 + addendum)

**Aprendizaje:** principios técnicos como YAGNI/DT-009 aplican a artefactos físicos en el repositorio, no a documentación arquitectónica que describe la visión integrada del paquete a través de versiones.

**Caso concreto:** `tracer.py` no se crea como stub vacío en v0.1 (cumple DT-009), pero sí se documenta en `02_Arquitectura_Skill.md` como módulo planeado en una sección clara de "Módulos planeados (v0.2+)".

### 6.4 Documentación como subproducto, no como tarea separada

**Aprendizaje:** la bitácora `01_Decisiones_Tecnicas.md` se mantuvo viva durante todo el desarrollo. Cada vez que aparecía una decisión técnica importante, se documentó inmediatamente. Esto permitió que la otra instancia de Claude (en code review cruzado) tuviera contexto suficiente para razonar al nivel de un ingeniero senior, no solo verificar mecánicamente.

**Regla operativa derivada:** una decisión sin razón documentada es una decisión que se va a cuestionar después sin contexto. Documentar mientras se decide tiene costo bajo y beneficio alto a futuro.

---

## 7 · Limitaciones honestas conocidas (post v0.1)

Cosas que sabemos de antemano que tendrán fricción en uso real:

1. **Generación de código ladder importable es frágil** y no es prioridad del proyecto.

2. **El skill no se ejecuta directamente sobre Studio 5000.** Opera sobre archivos exportados.

3. **Schema L5X cambia ligeramente entre versiones.** v17 a v37 funciona razonablemente uniforme, pero pueden aparecer bordes con configuraciones específicas (Safety encriptado, FactoryTalk Alarms avanzados).

4. **Cifrado `.sk` de rutinas Safety.** Si el L5X exportado tiene rutinas encriptadas, el skill no las descifra.

5. **Proyectos muy grandes** (>10 MB de L5X) no se han probado. Pueden requerir estrategias de segmentación que aún no diseñamos.

6. **Trace causal automático no existe en v0.1.** Preguntas tipo "¿de dónde viene el valor X?" requieren navegación manual con guía del modelo.

7. **Detección de dominios funcionales no existe.** El skill no sabe qué partes del código son "el subsistema de empalme" — el usuario tiene que indicarlo o el modelo lo infiere conversacionalmente.

8. **Detección de colisiones AOI por underscore/numeración** no implementada (diferida a v0.2). Casos como `Full_Speed_Splicer` vs `FullSpeedSplicer` vs `FullSpeedSplicer2` no se detectan.

---

*Esta investigación es la base sobre la que se construyó v0.1 y el punto de partida para v0.2.*

*Última actualización: 2026-05-02 (cierre v0.1)*
