# Analisis estatico: CPPIM_BD800_1.L5X

## Metadatos

- Path absoluto: `c:\Master_Project\rockwell-comprehender\parque_l5x\CPPIM_BD800_1.L5X`
- Tamano: **13.839 MB** (14,511,078 bytes)
- Studio 5000 SoftwareRevision: `33.01`
- L5X SchemaRevision: `1.0`
- Controller: `CPPIM_BD800_1` / processor `1756-L83ES`
- ProjectCreationDate: `Wed Dec 11 19:38:57 2024`
- LastModifiedDate: `Sat May 02 23:55:03 2026`
- ExportDate: `Sat May 02 23:55:33 2026`
- Owner: `Automation, Amantrini Automação`
- t_load_ms: **318**
- t_analysis_ms: **74**
- t_total_agent_ms: **392**
- timestamp_start: `2026-05-03T19:57:12.244+00:00`
- timestamp_end: `2026-05-03T19:57:12.636+00:00`

## Inventario

| Categoria | Count |
|-----------|-------|
| Programas | 7 |
| Routines totales (de programas) | 53 |
| Routines protegidas (Source Protection) | 5 |
| AOIs definidos | 28 |
| AOIs protegidos (encriptados) | 1 |
| AOIs referenciados en codigo | 22 |
| Tags totales (todos los scopes) | 2460 |
| Tags controller-scoped | 1768 |
| Tags program-scoped | 252 |
| Tags locales de AOI | 440 |
| UDTs | 45 |
| Modulos | 410 |
| Tasks | 5 |
| Observaciones | 30 |

### Routines por tipo (RLL/ST/FBD/SFC)

| Tipo | Count |
|------|-------|
| RLL | 42 |
| ST | 9 |
| FBD | 2 |

### Routines por programa (top 10)

| Programa | Routines |
|----------|----------|
| MainProgram | 25 |
| AltaBluePlusControl | 12 |
| SafetyProgram | 5 |
| Reject | 4 |
| TemperatureControl | 3 |
| Unwinder | 3 |
| Fault | 1 |

### AOIs definidos vs referenciados

- **Definidos:** 28
- **Referenciados (al menos 1 invocacion en codigo RLL):** 22
- **Definidos pero no referenciados (RLL):** 6
  - Ejemplos (max 15): `AOI_AxisControl_CIP`, `Byte_Swap`, `Lubricuting_Pump`, `RejectFunction_ST`, `RejectMotor`, `RepositionServoUS`

Top 15 AOIs por numero de invocaciones:

| AOI | Invocaciones |
|-----|--------------|
| StationStatus | 44 |
| Servo_Homming | 25 |
| RepositionServoSpacing | 25 |
| GlueGunControlMAOC | 16 |
| AOI_UnwinderControl | 11 |
| raC_Opr_NetModbusTCPClient | 10 |
| AOI_AUXMotor_PF | 8 |
| Blink | 7 |
| DancerControl | 6 |
| raC_Tec_NetModbusTCPClient_ChkWrReply | 6 |
| MaterialCorrection_CD | 4 |
| PhaseAdjustment | 3 |
| MaterialCorrectionCAM_CD | 2 |
| raC_Tec_NetModbusTCPClient_RespStrBit | 2 |
| raC_Tec_NetModbusTCPClient_RespStrWord | 2 |

AOIs protegidos (source-protected, blob encriptado): 1

| AOI | Revision |
|-----|----------|
| AOI_ProductionData_ContScan | 1.0 |

## Estructura de tasks

| Task | Type | Period (ms) | Watchdog (ms) | Priority | Programs |
|------|------|-------------|---------------|----------|----------|
| MainTask | CONTINUOUS | - | 500.0 | 10 | MainProgram, AltaBluePlusControl |
| SafetyTask | PERIODIC | 200.0 | 200.0 | 2 | SafetyProgram |
| Temperature | PERIODIC | 1000.0 | 2000.0 | 11 | TemperatureControl |
| TimeScan_5ms | PERIODIC | 5.0 | 500.0 | 1 | Reject |
| UnwinderControl | PERIODIC | 10.0 | 500.0 | 10 | Unwinder |

## Top-20 tokens (operadores + tags-operandos combinados)

| # | Token | Frecuencia |
|---|-------|------------|
| 1 | `XIC` | 2244 |
| 2 | `XIO` | 1095 |
| 3 | `MOV` | 815 |
| 4 | `OTL` | 625 |
| 5 | `OTE` | 527 |
| 6 | `EQU` | 329 |
| 7 | `CPT` | 295 |
| 8 | `ONS` | 267 |
| 9 | `COP` | 244 |
| 10 | `OTU` | 222 |
| 11 | `TON` | 203 |
| 12 | `HotmeltGramWeight` | 176 |
| 13 | `NEQ` | 170 |
| 14 | `MachineActualSpeed` | 168 |
| 15 | `Wrk_MSGStep` | 154 |
| 16 | `MSG` | 143 |
| 17 | `MotorSelect` | 138 |
| 18 | `GRT` | 123 |
| 19 | `AFI` | 122 |
| 20 | `LES` | 120 |

### Desglose: top 20 operadores (instrucciones)

| # | Operador | Count |
|---|----------|-------|
| 1 | `XIC` | 2244 |
| 2 | `XIO` | 1095 |
| 3 | `MOV` | 815 |
| 4 | `OTL` | 625 |
| 5 | `OTE` | 527 |
| 6 | `EQU` | 329 |
| 7 | `CPT` | 295 |
| 8 | `ONS` | 266 |
| 9 | `COP` | 244 |
| 10 | `OTU` | 222 |
| 11 | `TON` | 203 |
| 12 | `NEQ` | 170 |
| 13 | `MSG` | 143 |
| 14 | `GRT` | 123 |
| 15 | `AFI` | 122 |
| 16 | `LES` | 120 |
| 17 | `GEQ` | 118 |
| 18 | `ADD` | 110 |
| 19 | `LEQ` | 75 |
| 20 | `CLR` | 73 |

### Desglose: top 20 tag-operandos

| # | Tag | Apariciones |
|---|-----|-------------|
| 1 | `HotmeltGramWeight` | 176 |
| 2 | `MachineActualSpeed` | 168 |
| 3 | `Wrk_MSGStep` | 154 |
| 4 | `MotorSelect` | 138 |
| 5 | `MachineStatus.2` | 74 |
| 6 | `Servo_CorrectCoefficient` | 50 |
| 7 | `StationSelect` | 48 |
| 8 | `MachineStatus.4` | 41 |
| 9 | `Wrk_TempInt` | 40 |
| 10 | `AlwaysOff` | 36 |
| 11 | `InibirAlarms` | 33 |
| 12 | `Axis` | 30 |
| 13 | `Transaction.TransType` | 30 |
| 14 | `UnwinderRightServoClutch` | 29 |
| 15 | `Yes` | 28 |
| 16 | `MachineStatus.23` | 28 |
| 17 | `ServoPositionRead_cmd` | 28 |
| 18 | `Disabled` | 27 |
| 19 | `No` | 26 |
| 20 | `MachineStatus.20` | 25 |

## Motion instructions (MA*)

Total invocaciones MA*: **83** distribuidas en **10** tipos.

| Instruccion | Count |
|-------------|-------|
| MAS | 25 |
| MAM | 12 |
| MAH | 8 |
| MAJ | 8 |
| MAG | 7 |
| MAPC | 7 |
| MAR | 5 |
| MASR | 5 |
| MAFR | 4 |
| MAOC | 2 |

## Patterns detectados (Capa C)

- Zonas detectadas: **43**
- Zonas por tipo: `{'panel_drives': 7, 'safety_adapter': 14, 'safety_status': 16, 'unwinder': 6}`
- Naming matches totales: **295**
- Naming matches por categoria: `{'drive': 124, 'safety': 171}`
- Tag roles inferidos: **51**
- Tag roles por rol: `{'hmi_reset_command': 20, 'hmi_command': 21, 'hmi_limit': 7, 'hmi_setpoint': 2, 'hmi_enable_command': 1}`

### Zonas (top 15)

| Zona | Tipo | #modules | #tags |
|------|------|----------|-------|
| MPAUX05 | safety_status | 24 | 0 |
| UWM031 | safety_status | 23 | 0 |
| UWM031 | unwinder | 9 | 10 |
| MPHM01 | safety_status | 17 | 0 |
| UWM04 | unwinder | 7 | 10 |
| UWM04 | safety_status | 16 | 0 |
| UWM05 | unwinder | 5 | 10 |
| MDP001 | panel_drives | 8 | 5 |
| MDP003 | panel_drives | 8 | 5 |
| DRP01 | safety_status | 13 | 0 |
| MDP002 | panel_drives | 7 | 5 |
| MDP004 | panel_drives | 7 | 5 |
| MDP005 | panel_drives | 7 | 5 |
| MDP007 | panel_drives | 7 | 5 |
| DRP06 | safety_status | 12 | 0 |

### Naming matches (drives + safety)

| Pattern | Categoria | Matches |
|---------|-----------|---------|
| drive_servo_SD | drive | 124 |
| safety_estop_dual | safety | 25 |
| safety_gate_lock | safety | 27 |
| safety_crout_sto | safety | 6 |
| safety_ChA | safety | 43 |
| safety_ChB | safety | 43 |
| safety_feedback | safety | 27 |

## Hallazgos

Observaciones del loader (total 30):

| Categoria | Count |
|-----------|-------|
| module_without_name | 24 |
| protected_routine | 5 |
| protected_aoi | 1 |

### Resumen narrativo

- Hay **1 AOI(s) source-protected** — solo el header (nombre + revision) se conoce. La toolkit los registra como `protected=True` y no extrae parameters / routines / local tags. Esto es esperable en proyectos integrados con IP de terceros (Amantrini / Xu-Jin / etc.).
- Hay **5 rutinas protegidas** dentro de programas o AOIs no-protegidos. El L5X las trae como `<EncodedData EncryptionConfig=9>` con cuerpo encriptado. Quedan registradas con `code=""` y `protected=True`.
- Presencia fuerte de motion: **83** invocaciones MA* sobre **10** instrucciones distintas — coherente con un equipo Kinetix multi-eje.
- **6 AOIs definidos no son referenciados en RLL parseable** — probable que esten invocados desde rutinas FBD/ST (no tokenizadas) o desde AOIs protegidos, o sean codigo muerto. Conviene cross-checkear.
- El parseo cubre 53 routines de programas + routines de los 28 AOIs definidos. La distribucion por tipo es: {'RLL': 42, 'ST': 9, 'FBD': 2}.

### Brechas frente a la spec

- La spec pide "AOIs defined vs. referenced". Aqui se cubren los AOIs referenciados **desde codigo RLL** (programa + AOIs no-protegidos). Las invocaciones desde FBD/SFC/ST no se tokenizan (la toolkit solo tiene `tokenize_rll`); las desde AOIs `protected=True` tampoco son visibles. Considerar este conteo como **lower bound**.
- Top-20 tokens: la toolkit no tiene un "tokens by frequency" preconstruido a nivel global, asi que se construyo combinando frecuencia de operadores + tag-operandos via `tokenize_rll`. Se incluye un desglose separado para que sea inspeccionable.
- Tasks: se reporta `Rate` como periodo (la toolkit lo expone asi en `Task.rate`).
- ST routines: la toolkit tiene un parser ST separado que devuelve el codigo linea-por-linea pero no lo tokeniza para operadores (`tokenize_st` no existe en v0.3). Las rutinas ST se cuentan en "Routines por tipo" pero no contribuyen al token count.
- ProtectedRoutine handling: confirmado que el loader lo soporta nativamente (observation category `protected_routine` o `protected_aoi`). El reporte agrega los totales arriba.
