# Analisis estatico: AQL_M2.L5X

## Metadatos

- **Path absoluto:** `c:\Master_Project\rockwell-comprehender\parque_l5x\AQL_M2.L5X`
- **Tamano:** 2.759 MB (2,892,574 bytes)
- **Controller (target_name):** `CPU_AQL_M2`
- **Processor type:** `1756-L61`
- **Studio 5000 SoftwareRevision:** `20.01`
- **L5X SchemaRevision:** `1.0`
- **Major/Minor rev:** `20.12`
- **Owner:** `Windows 用户, hch`
- **Project creation date:** `Fri Feb 15 12:45:57 2008`
- **Last modified date:** `Tue Jan 28 19:53:44 2025`
- **Export date:** `Sun Dec 21 10:19:38 2025`
- **t_load_ms:** 238
- **t_analysis_ms:** 41
- **t_total_agent_ms:** 307
- **timestamp_start:** 2026-05-03T19:57:14.987052+00:00
- **timestamp_end:** 2026-05-03T19:57:15.294348+00:00

## Inventario

| Categoria | Count |
| --- | --- |
| Modules (fisicos / red) | 44 |
| Tasks | 4 |
| Programs | 7 |
| Routines (totales en programas) | 29 |
|   - tipo RLL | 25 |
|   - tipo ST | 3 |
|   - tipo FBD | 1 |
|   - tipo SFC | 0 |
|   - otros tipos | 0 |
|   - rutinas protected (Source Protection) | 0 |
| AOIs definidos | 24 |
|   - AOIs protected | 0 |
| AOIs referenciados en codigo | 20 |
| AOIs definidos pero no referenciados | 4 |
| UDTs | 29 |
| Tags controllerScope | 775 |
| Tags programScope (todos los programas) | 626 |
| Tags totales | 1401 |
| Observaciones (loader) | 13 |
| Total rungs tokenizados | 936 |
| Total instrucciones tokenizadas | 6216 |

## Estructura de tasks

| Task | Type | Period (ms) | Priority | Watchdog (ms) | Programs |
| --- | --- | --- | --- | --- | --- |
| FastTask | PERIODIC | 20.0 | 10 | 500.0 | Reject |
| MainTask | CONTINUOUS | - | 10 | 500.0 | MainProgram |
| Motion | EVENT | - | 1 | 500.0 | Axis, ConsumeAxisAOI, Debo_Tela |
| Task500ms | PERIODIC | 555.0 | 15 | 500.0 | ReadPar |

### Programs

| Program | MainRoutine | FaultRoutine | Disabled |
| --- | --- | --- | --- |
| Axis | Ax | - | no |
| ConsumeAxisAOI | Main | - | no |
| Debo_Tela | R00_Main | - | no |
| MainProgram | MainRoutine | - | no |
| ReadPar | ReadPara | - | no |
| Reject | Reject_Control1 | - | no |
| Reject1 | Reject | - | no |

## Top-20 tokens (operadores RLL por frecuencia)

| # | Operador | Ocurrencias |
| --- | --- | --- |
| 1 | XIC | 1990 |
| 2 | XIO | 738 |
| 3 | MOV | 494 |
| 4 | OTE | 390 |
| 5 | OTU | 293 |
| 6 | OTL | 226 |
| 7 | CLR | 191 |
| 8 | CPT | 186 |
| 9 | ONS | 165 |
| 10 | EQU | 147 |
| 11 | GRT | 137 |
| 12 | TON | 127 |
| 13 | COP | 98 |
| 14 | LES | 93 |
| 15 | NEQ | 86 |
| 16 | ADD | 76 |
| 17 | SUB | 58 |
| 18 | MUL | 46 |
| 19 | CTU | 46 |
| 20 | DIV | 46 |

### Top-20 operandos por frecuencia (referencia complementaria)

| # | Operando | Ocurrencias |
| --- | --- | --- |
| 1 | ? | 396 |
| 2 | 0 | 380 |
| 3 | 1 | 218 |
| 4 | 100 | 100 |
| 5 | % of Maximum | 95 |
| 6 | Units per sec2 | 89 |
| 7 | ResetAlarm | 86 |
| 8 | AxStart | 74 |
| 9 | AxEnabled | 71 |
| 10 | Loc_SplicePreparedA | 68 |
| 11 | Loc_SplicePreparedB | 68 |
| 12 | 2 | 52 |
| 13 | 50 | 47 |
| 14 | Disabled | 44 |
| 15 | None | 44 |
| 16 | IstFaultCode | 42 |
| 17 | Units per sec | 39 |
| 18 | 3 | 39 |
| 19 | PhysicalAx | 39 |
| 20 | StartMachine | 38 |

## Motion instructions (familia MA*)

| MA-instruccion | Count |
| --- | --- |
| MAM | 24 |
| MAG | 24 |
| MAS | 23 |
| MAJ | 20 |
| MAH | 7 |
| MASR | 3 |
| MAFR | 3 |
| MAOC | 1 |
| MAPC | 1 |

**Total invocaciones MA\*:** 106

### Axis tags (controllerScope, datatype AXIS_*)

| Tag | DataType | MotionModule |
| --- | --- | --- |
| Axis_CSTAid | AXIS_VIRTUAL | - |
| Ax_Spare | AXIS_SERVO_DRIVE | <NA> |
| S04N71_DEBOB_AQL_DERECHO | AXIS_SERVO_DRIVE | M1_501U1:Ch90 |
| S04N72_DEBO_AQL_IZQUIERDO | AXIS_SERVO_DRIVE | M2_502U1:Ch91 |
| S04N73_ROD_ARRASTRE_TNT | AXIS_SERVO_DRIVE | M3_504U1:Ch93 |
| S04N74_CORTE_APLIC_AQL | AXIS_SERVO_DRIVE | M4_503U1:Ch92 |
| S04N75_RODILLO_ESTAMPADOR | AXIS_SERVO_DRIVE | M5_505U1:Ch94 |
| S04N76_ROD_BAND_ALIM_AQL | AXIS_SERVO_DRIVE | M6_506U1:Ch95 |
| S04N77_DEBO_TNT_IZQUIERDO | AXIS_SERVO_DRIVE | M7_507U1:Ch96 |
| S04N78_DEBO_TNT_DERECHO | AXIS_SERVO_DRIVE | M8_508U1:Ch97 |
| S04N79_UNIDAD_CORTE_WB | AXIS_SERVO_DRIVE | M9_507U1:Ch20 |
| S04N80_WB_TAMBOR_TRANSF | AXIS_SERVO_DRIVE | M10_508U1:Ch21 |
| S04N81_DEBOB_WB_DERECHO | AXIS_SERVO_DRIVE | M12_509U1:Ch23 |
| S04N82_DEB_WB_IZQUIERDO | AXIS_SERVO_DRIVE | M11_510U1:Ch22 |
| S04N83_ROD_BAND_ALIM_WB | AXIS_SERVO_DRIVE | M13_511U1:Ch24 |
| S04N84_RODILLO_BARRERAS | AXIS_SERVO_DRIVE | M14_512U1:Ch25 |
| S04N85_RODILLO_TRACC_TNT | AXIS_SERVO_DRIVE | M15_513U1:Ch26 |
| S04N86_DANCER_DEBO_TNT | AXIS_SERVO_DRIVE | M16_514U1:Ch27 |
| Vmaster1 | AXIS_VIRTUAL | - |
| VM_Consumer_GrandMaster | AXIS_VIRTUAL | - |

## AOIs

- Defined: 24
- Protected: 0
- Referenced (invocados al menos una vez): 20
- Unreferenced (definidos pero nunca invocados): 4

**AOIs referenciados (invocaciones detectadas):**

AOI_CCCT, AxisBlockVM, AxisConsumeCIPSync_AOI, Axis_Faults_Sercos, Axis_Object_Sercos, Blink, C_U_Reg, CtcDiatecSplicer, CtcDiatecSplicerBuffer, DancerCorAndNewRadiusComputation, Dancer_Tension_Servo, FullSpeedSplicer, FullSpeedSplicer2, Full_Speed_Splicer, RadiusComputation, RejectFun, RejectFunctionLonger, Servo_Manager, Unwinder, VirtualAxisBlock

**AOIs definidos sin referencias en codigo:**

AxisBlock, Axis_Faults_CIP, Axis_ObjectCIP, Radius_Computation

## Patterns detectados (rockwell_comprehender.patterns)

**Resumen:**

- Zonas detectadas: 2 -> {'io_node': 2}
- Naming matches totales: 16 -> {'drive': 16}
- Tag roles inferidos: 97 -> {'hmi_command': 75, 'hmi_reset_command': 3, 'hmi_enable_command': 10, 'hmi_actual_value': 1, 'hmi_limit': 3, 'hmi_setpoint': 1, 'hmi_diameter': 4}

### Zonas

| Zona | Kind | #Modules | #Tags |
| --- | --- | --- | --- |
| Z1 | io_node | 8 | 0 |
| Z3 | io_node | 6 | 0 |

### Naming matches

| Pattern | Categoria | Regex | #Matches |
| --- | --- | --- | --- |
| drive_complex_module | drive | `^M\d+_\d+U\d+` | 16 |

## Observaciones del loader

| Categoria | Count |
| --- | --- |
| module_without_name | 13 |

**Detalle (primeras 30):**

- `[info/module_without_name]` Módulo 1734-OB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-OB8/C)#1'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-OB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-OB8/C)#2'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-IB8/C)#1'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-IB8/C)#2'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-IB8/C)#3'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IE2V/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-IE2V/C)'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-IB8/C)#4'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-OB8/C bajo NODE_Z3 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z3:port1(1734-OB8/C)#1'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-OB8/C bajo NODE_Z3 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z3:port1(1734-OB8/C)#2'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z3 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z3:port1(1734-IB8/C)#1'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IB8/C bajo NODE_Z3 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z3:port1(1734-IB8/C)#2'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1734-IE2V/C bajo NODE_Z3 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z3:port1(1734-IE2V/C)'. Esto es normal para POINT I/O y similares.
- `[info/module_without_name]` Módulo 1756-OB16E bajo Local no tiene atributo Name. Se le asigna identificador sintético 'Local:port1(1756-OB16E)'. Esto es normal para POINT I/O y similares.

## Hallazgos

- L5X de **2.759 MB**, controller `1756-L61` sobre Studio 5000 v20.01 (schema 1.0).
- Carga + persist SQLite en 238 ms; analisis estatico (tokenize 936 rungs / 6216 instrucciones + patterns) en 41 ms.
- 7 programas, 29 rutinas (RLL=25, ST=3, FBD=1, SFC=0); 4 tasks; 44 modulos.
- 24 AOIs definidos (0 protected); 20 efectivamente invocados; 4 definidos sin uso (potencial dead code o libreria).
- Motion present: 106 invocaciones MA\*; top tipos: MAM=24, MAG=24, MAS=23.
- 20 tags AXIS\_\* a nivel controller (motion infrastructure declarada en data type).
- Tag mix: 775 controller-scoped vs 626 program-scoped (ratio 0.81x).
- Patterns detecto 2 zonas fisicas (kinds: ['io_node']).
- Operadores dominantes: XIC=1990, XIO=738, MOV=494. Esto da color sobre el estilo de codigo (ladder-heavy, math-heavy, etc.).

### Notas tecnicas / gaps respecto al spec

- **"Top-20 tokens"** del spec se interpreto como top-20 operadores RLL (la unidad lexica con mayor valor semantico). Se incluye una tabla complementaria con top-20 operandos crudos.
- El spec menciona `tokenizer/` para tokens; el toolkit expone `tokenize_rll(code) -> list[Rung]` por rutina, no un counter global, asi que el agente agrega frecuencias on-the-fly.
- Motion: se conto solo familia MA\* (re `^MA[A-Z]{1,3}$`) tal como pide el spec. Otras familias (MS\*, MD\*, MC\*) NO incluidas.
- Patterns capa C es un detector conservador basado en regex de naming (zonas/drives/safety/HMI). No hace inferencia semantica de codigo.
- AOI 'referenced' = aparece como `operator` en al menos un rung tokenizado (programas + AOIs internos). No incluye uso indirecto vienen FBD/SFC.
