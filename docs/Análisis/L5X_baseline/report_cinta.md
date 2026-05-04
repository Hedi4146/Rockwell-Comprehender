# Análisis estático: CINTA_LAMINADA_M2_2024.L5X

## Metadatos

| Campo | Valor |
|---|---|
| Path absoluto | `c:\Master_Project\rockwell-comprehender\parque_l5x\CINTA_LAMINADA_M2_2024.L5X` |
| Tamaño | 1.15 MB (1 205 463 bytes) |
| Target name | `CPU1` |
| Processor type | `1768-L43` (CompactLogix L43) |
| Software revision (Studio 5000) | `20.01` |
| Schema L5X | `1.0` |
| Owner (export) | `Windows 用户, hch` |
| Project creation date | `Sun Jul 06 14:02:47 2014` |
| Last modified date | `Tue Dec 24 13:11:06 2024` |
| Export date | `Sun Dec 21 10:40:53 2025` |
| **t_load_ms** | **87** |
| **t_analysis_ms** | **48** |
| **t_total_agent_ms** | **164** |
| **timestamp_start** | `2026-05-03T19:56:27.813659+00:00` |
| **timestamp_end** | `2026-05-03T19:56:27.978008+00:00` |

> Toolkit: `rockwell_comprehender` v0.1.0 (`load_project` + `tokenizer.tokenize_rll` + `project.detected_patterns`). Python 3.13.13, system interpreter (no venv en repo). `PYTHONUTF8=1` activo (necesario por presencia de chars CJK en metadata `owner`).

## Inventario

| Categoría | Count | Notas |
|---|---:|---|
| Programas | 4 | `Axis`, `MainProgram`, `ReadPar`, `Reject` |
| Routines (total) | 17 | RLL=15, ST=2, FBD=0, SFC=0 |
| Routines protected (Source Protection) | 0 | — |
| AOIs definidos | 26 | 0 protected |
| AOIs referenciados en código | 14 | 12 definidos sin uso (ver "Hallazgos") |
| Tags totales | 1 027 | sumando los tres scopes |
| Tags scope `controller` | 209 | |
| Tags scope `program` (sumados) | 240 | `Axis`=188, `MainProgram`=52 |
| Tags locales de AOI | 578 | |
| UDTs definidos | 10 | |
| Módulos físicos | 12 | rack 1768 + POINT I/O remoto + 4 servos SERCOS |
| Motion instructions (MA*/MS*/MC*) | 70 | 13 tipos distintos — ver tabla aparte |
| Tasks | 4 | 1 CONTINUOUS + 2 PERIODIC + 1 EVENT |
| Observations parser | 6 | 4 info (POINT I/O sin Name) + 2 warning AOI naming collision |

### Routines por programa

| Programa | # Routines |
|---|---:|
| `MainProgram` | 9 |
| `Axis` | 4 |
| `ReadPar` | 3 |
| `Reject` | 1 |

## Estructura de tasks

| Task | Type | Period (ms) | Priority | Watchdog (ms) | Programs |
|---|---|---:|---:|---:|---|
| `MainTask` | CONTINUOUS | — | 10 | 500 | `MainProgram` |
| `FastTask` | PERIODIC | 8 | 10 | 500 | `Reject` |
| `Motion` | EVENT | 10 (trigger) | 10 | 500 | `Axis` |
| `Task1000ms` | PERIODIC | 1000 | 15 | 2000 | `ReadPar` |

> El Reject corre en task rápida de 8 ms (lógica de expulsión sensible al timing); el Axis en task de evento disparada por motion (10 ms ciclo de motion planner SERCOS); el lazo lento `ReadPar` (1 s) lee parámetros HMI sin presión temporal.

## Top-20 tokens

> Ranking sobre el corpus completo de RLL (programas + AOIs). Se separan operadores (instrucciones) de operandos tipo `tag` para evitar mezclar dos vocabularios distintos.

### Top-20 operadores (instrucciones RLL)

| # | Operador | Count |
|---:|---|---:|
| 1 | `XIC` | 1063 |
| 2 | `XIO` | 425 |
| 3 | `MOV` | 227 |
| 4 | `OTU` | 215 |
| 5 | `OTE` | 202 |
| 6 | `CPT` | 170 |
| 7 | `CLR` | 115 |
| 8 | `OTL` | 97 |
| 9 | `ONS` | 88 |
| 10 | `EQU` | 62 |
| 11 | `JMP` | 48 |
| 12 | `NEQ` | 43 |
| 13 | `LES` | 42 |
| 14 | `TON` | 28 |
| 15 | `GRT` | 25 |
| 16 | `MAG` | 24 |
| 17 | `LBL` | 15 |
| 18 | `MAS` | 15 |
| 19 | `ADD` | 14 |
| 20 | `DIV` | 13 |

### Top-20 tag-operandos

| # | Tag | Count |
|---:|---|---:|
| 1 | `Loc_SplicePreparedA` | 84 |
| 2 | `Loc_SplicePreparedB` | 84 |
| 3 | `AxEnabled` | 74 |
| 4 | `AxStart` | 73 |
| 5 | `IstFaultCode` | 56 |
| 6 | `OFF` | 41 |
| 7 | `PhysicalAx` | 41 |
| 8 | `LocMemManSplice` | 38 |
| 9 | `Data.Input.AxPar.HmiOpMode` | 38 |
| 10 | `StartB` | 37 |
| 11 | `Enable` | 37 |
| 12 | `label200` | 34 |
| 13 | `DriveFaultBits_Code` | 33 |
| 14 | `StartA` | 32 |
| 15 | `Disabled` | 30 |
| 16 | `Data.Motion.GearRatio` | 30 |
| 17 | `CS[2].Master` | 29 |
| 18 | `EN` | 28 |
| 19 | `StartForSplice` | 27 |
| 20 | `EVSpliceA` | 26 |

## Motion instructions

> Total: **70** instrucciones motion en RLL. Familia dominante: gearing (`MAG`) + state machine (`MAS`/`MAM`/`MAJ`) + servo on/off (`MSO`/`MSF`).

| Instrucción | Count | Categoría |
|---|---:|---|
| `MAG` | 24 | Motion Axis Gearing (sincronía electrónica eje-a-eje) |
| `MAS` | 15 | Motion Axis Stop |
| `MAM` | 11 | Motion Axis Move (move absoluto/incremental) |
| `MAJ` | 8 | Motion Axis Jog |
| `MAFR` | 3 | Motion Axis Fault Reset |
| `MAH` | 2 | Motion Axis Home |
| `MAOC` | 1 | Motion Arm Output Cam |
| `MASR` | 1 | Motion Apply Shutdown Reset |
| `MSO` | 1 | Motion Servo On |
| `MSF` | 1 | Motion Servo Off |
| `MCCP` | 1 | Motion Calculate Cam Profile |
| `MCSV` | 1 | Motion Calculate Slave Values |
| `MAPC` | 1 | Motion Axis Position Cam |

## Patterns detectados (Capa C)

Resultado de `project.detected_patterns` (`rockwell_comprehender.patterns.detect_patterns`).

### Resumen

| Métrica | Valor |
|---|---:|
| Zonas físicas detectadas | 1 |
| Naming matches | 4 |
| Tag roles inferidos | 61 |

### Zonas físicas

| Zona | Kind | Miembros |
|---|---|---|
| `Z1` | `io_node` | `NODE_Z1` + 4 cards POINT I/O (1734-IB8/C, 1734-IE2V/C, 1734-OB8/C, 1734-OE2V/C) |

### Naming matches

| Pattern | Categoría | Regex | Matches |
|---|---|---|---|
| `drive_simple` | drive | `^M\d+$` | `M1`, `M2`, `M3`, `M4` (4) |

### Tag roles (sample)

61 roles inferidos, distribuidos así:

| Rol | Count |
|---|---:|
| `hmi_command` | 53 |
| `hmi_diameter` | 4 |
| `hmi_enable_command` | 3 |
| `hmi_setpoint` | 1 |

Sample (primeros 15): `HmiActualSize`, `HmiDryRun`, `HmiEnableSimulation`, `HmiManualEnabled`, `HmiOldSize`, `HmiProductLength`, `HmiProductLengthJunior`, `HmiProductLengthMaxi`, `HmiProductLengthMidi`, `HmiProductLengthMini`, `HmiResetAlarm`, `HmiSimulatedSpeed`, `HmiSizeConfirm`, `HmiSizeSelector`, `HmiStartMotor`.

## Observations del parser

| Severity | Categoría | Count |
|---|---|---:|
| info | `module_without_name` | 4 |
| warning | `aoi_naming_collision` | 2 |

Los 4 `module_without_name` son cards POINT I/O bajo `NODE_Z1` — esperado, el toolkit les asigna nombre sintético tipo `NODE_Z1:port1(1734-OB8/C)`.

Las 2 colisiones de naming AOI son interesantes (ver "Hallazgos").

## Hallazgos

### 1. Doble familia de AOIs co-existiendo (vendor mix)

El proyecto contiene **dos generaciones de AOIs en paralelo**:

- **Familia "AHT_*"** (Diatec): `AHT_Unwinder`, `AHT_DancerCorAndNewRadiusComputation`, `AHT_DriveRoll_withDancer`, `AHT_DriveRoll_withoutDancer`, `AHT_CtcSplicer`, etc.
- **Familia "legacy"** (probablemente original Softys/Diatec antigua): `Unwinder`, `DancerCorAndNewRadiusComputation`, `RadiusComputation`, `CtcDiatecSplicer`, `FullSpeedSplicer`, etc.

El parser detecta esto como `aoi_naming_collision`: pares `Unwinder`/`AHT_Unwinder` y `DancerCorAndNewRadiusComputation`/`AHT_DancerCorAndNewRadiusComputation`. Cruzando con la lista de **AOIs unused**, las versiones legacy (`Unwinder`, `CtcDiatecSplicer`, `FullSpeedSplicer`, `FullSpeedSplicer2`, `AxisBlock`, `AHT_DancerCorAndNewRadiusComputation`) están **definidas pero NO referenciadas** — son código zombie heredado de versiones anteriores que se quedó por compatibilidad o por no auditarse. Candidatos a limpieza.

### 2. AOIs activamente usados (top por count de invocaciones)

| AOI | Invocaciones |
|---|---:|
| `Servo_Manager` | 6 |
| `AHT_DriveFaultBit_Decoding` | 5 |
| `AHT_Enable_DriveAxis` | 3 |
| `AHT_MotionAxisError` | 3 |
| `RadiusComputation` | 2 |
| `DancerCorAndNewRadiusComputation` | 2 |

Notar que `RadiusComputation` y `DancerCorAndNewRadiusComputation` (familia legacy) **sí** están en uso, mientras que sus contrapartes `AHT_DancerCorAndNewRadiusComputation` no — patrón de migración incompleta o de mezcla intencional.

### 3. Hardware footprint pequeño

12 módulos totales:
- 1× CompactLogix L43 (`Local`)
- 1× ENBT/A para Ethernet/IP
- 1× SERCOS module `1768-M04SE` con 4 servos Kinetix `2094-BC02-M02` + `2094-BM01` (M1, M2, M3, M4)
- 1× POINT I/O AENT remoto con 4 cards (DI, DO, AI, AO)

Coherente con una máquina de cinta laminada con 4 ejes servo gobernados por sincronía electrónica vía `MAG` (24 instancias). La estrategia de control es **gearing-based** (no posición pura): los ejes se enganchan/desenganchan a un master y se mueven `MAJ`/`MAM` para corrección.

### 4. Splicer logic dominante en las top-tags

Los dos tags más frecuentes (`Loc_SplicePreparedA` / `Loc_SplicePreparedB`, 84 references c/u) más `StartA/StartB`, `EVSpliceA`, `LocMemManSplice`, `StartForSplice` indican que el **núcleo de la máquina es el empalme (splicer)** — máquina de bobinado con cambio automático de bobina A↔B. Coincide con el dominio "cinta laminada" tipo papel/film con dos rollos para producción continua.

### 5. Métricas de timing — toolkit muy rápido

- `t_load = 87 ms` para 1.15 MB de XML + construcción de SQLite + observations es excelente.
- `t_analysis = 48 ms` incluye iteración completa del corpus tokenizado dos veces (una para AOIs referenced, otra para tokens/motion). Cero presión.
- Total agent: 164 ms desde `import` hasta antes de escribir el reporte.

### 6. Gaps del toolkit detectados (no bloqueantes)

- `routines_by_type` solo trae `RLL` y `ST` (los únicos presentes en este L5X). El toolkit soporta nominalmente `FBD`/`SFC` por contrato (`Routine.type` en model.py) pero acá no se ejercita.
- `tokenizer/` solo expone `tokenize_rll`; las 2 rutinas ST (en `Axis` program) NO se tokenizan, por lo que **los tokens reportados son solo del corpus RLL**. Si el ST tuviera motion calls, se perderían en este conteo (en este L5X específico no parecen tenerlas — los counts de motion ya cuadran con el total de RLL).
- `Capa C / patterns` reporta solo 1 zona física (`Z1` = el AENT POINT I/O). No identificó zona para los 4 servos `M1..M4` porque el regex `panel_drives` busca `MDP\d+` (convención CPPIM/Amantrini), no aplica a este integrador. No es bug — la capa es conservadora por diseño (DT-010).
