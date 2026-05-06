# Tag Dictionary — CPU1

**Total tags:** 1027
**Roles distintos detectados:** 16

## Distribución por rol

| Rol | Count | % |
|-----|------:|--:|
| `unknown` | 489 | 47.6% |
| `internal_aux` | 195 | 19.0% |
| `motion_control` | 105 | 10.2% |
| `hmi_input` | 59 | 5.7% |
| `counter_timer` | 56 | 5.5% |
| `splice` | 54 | 5.3% |
| `radius` | 16 | 1.6% |
| `command` | 11 | 1.1% |
| `enable` | 9 | 0.9% |
| `fault` | 7 | 0.7% |
| `axis_object` | 7 | 0.7% |
| `dancer` | 7 | 0.7% |
| `axis_data` | 5 | 0.5% |
| `status` | 4 | 0.4% |
| `io_input` | 2 | 0.2% |
| `motion_group` | 1 | 0.1% |

## Glosario de roles

- **`axis_data`** — Estructura de datos de eje (UDT M*Data o similar) — agrupa setpoints/feedback de un eje
- **`axis_object`** — Tag de eje (AXIS_*) — referencia a un servo configurado en el motion group
- **`command`** — Comando (start/stop/exec) — pulso de inicio o detención de acción
- **`counter_timer`** — Estructura TIMER/COUNTER — .EN/.TT/.DN/.PRE/.ACC para temporización o conteo
- **`dancer`** — Dancer (rodillo bailarín) — tag relacionado con control de tensión por danzarín
- **`enable`** — Enable / habilitación — bit que arma una función o módulo
- **`fault`** — Fault / alarma / error — bit de detección de condición anómala
- **`hmi_input`** — Input desde HMI — valor escrito por el operador en pantalla
- **`internal_aux`** — Auxiliar interno — variable temporal/scratch, no productiva semánticamente
- **`io_input`** — Entrada física I/O — bit de un módulo de input digital
- **`motion_control`** — Estructura motion control (MOTION_INSTRUCTION) — bits .EN/.DN/.ER de un comando motion
- **`motion_group`** — Motion group (MOTION_GROUP) — agrupador del scheduling motion
- **`radius`** — Radio del rollo — tag de cálculo de diámetro/radio actual
- **`splice`** — Splice / empalme — tag relacionado con la lógica de empalme
- **`status`** — Status / feedback / estado — lectura de condición actual del sistema
- **`unknown`** — Sin rol inferible por heurística — requiere inspección manual

## Tags por rol (sample top 20 por rol)

### `axis_data` (5)

- `M1Data` — Data (scope=controller) · conf=0.90
- `M2Data` — Data (scope=controller) · conf=0.90
- `M3Data` — Data (scope=controller) · conf=0.90
- `M4Data` — Data (scope=controller) · conf=0.90
- `M71Data` — Data (scope=Axis) · conf=0.90

### `axis_object` (7)

- `Ax_Spare` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `M1` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `M2` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `M3` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `M4` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `Master` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `Vmaster1` — AXIS_VIRTUAL (scope=controller) · conf=1.00

### `command` (11)

- `CPU_Run` — BOOL (scope=controller) · conf=0.85
- `start_M3` — BOOL (scope=controller) · conf=0.85
- `M6_Position_FTC_Start` — REAL (scope=Axis) · conf=0.85
- `M6_Position_FTC_Stop` — REAL (scope=Axis) · conf=0.85
- `start_Ejector_1` — BOOL (scope=MainProgram) · conf=0.85
- `start_Ejector_2` — BOOL (scope=MainProgram) · conf=0.85
- `RT_Start` — BOOL (scope=AHT_DriveRoll_withDancer) · conf=0.85
- `RT_Start` — BOOL (scope=AHT_DriveRoll_withoutDancer) · conf=0.85
- `RT_Start` — BOOL (scope=AHT_SyncroAxis) · conf=0.85
- `RT_Start` — BOOL (scope=AxisBlock) · conf=0.85
- `RT_Start` — BOOL (scope=VirtualAxisBlock) · conf=0.85

### `counter_timer` (56)

- `DelayGrupSynced` — TIMER (scope=controller) · conf=1.00
- `DelayGrupSynced2` — TIMER (scope=controller) · conf=1.00
- `DelayMachineStill` — TIMER (scope=controller) · conf=1.00
- `RTO_1` — TIMER (scope=controller) · conf=1.00
- `TIMER_ACQL` — TIMER (scope=controller) · conf=1.00
- `Timer_step1` — TIMER (scope=controller) · conf=1.00
- `Timer_step2` — TIMER (scope=controller) · conf=1.00
- `TON1` — TIMER (scope=controller) · conf=1.00
- `TON2` — TIMER (scope=controller) · conf=1.00
- `TONA` — TIMER (scope=controller) · conf=1.00
- `BSL_Array_control` — CONTROL (scope=Axis) · conf=1.00
- `clock_phase` — TIMER (scope=Axis) · conf=1.00
- `count1_Exit2` — COUNTER (scope=Axis) · conf=1.00
- `TimeExit1_Home_Delay` — TIMER (scope=Axis) · conf=1.00
- `TimeExit1_PowerOn` — TIMER (scope=Axis) · conf=1.00
- `TimeExit2_Home_Delay` — TIMER (scope=Axis) · conf=1.00
- `TimeExit2_Homing` — TIMER (scope=Axis) · conf=1.00
- `TimeExit2_PowerOn` — TIMER (scope=Axis) · conf=1.00
- `Timer_Ejector2_Cycle` — TIMER (scope=Axis) · conf=1.00
- `TOF_Start_Stacker` — TIMER (scope=Axis) · conf=1.00
- ... +36 más

### `dancer` (7)

- `Unw_Dancer_Pos` — REAL (scope=controller) · conf=0.75
- `LocMemDancerPos1` — REAL (scope=DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerSetpoint` — REAL (scope=DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerPositionB` — DINT (scope=AHT_Unwinder) · conf=0.75
- `LocMemDancerPos1` — REAL (scope=AHT_DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerSetpoint` — REAL (scope=AHT_DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerPositionB` — DINT (scope=Unwinder) · conf=0.75

### `enable` (9)

- `Enable_Ax_M2` — BOOL (scope=Axis) · conf=0.80
- `Enable_Ax_M3` — BOOL (scope=Axis) · conf=0.80
- `Enable_Ax_M4` — BOOL (scope=Axis) · conf=0.80
- `Enable_Ax_M5` — BOOL (scope=Axis) · conf=0.80
- `Enable_M2` — BOOL (scope=Axis) · conf=0.80
- `Enable_M3` — BOOL (scope=Axis) · conf=0.80
- `Enable_M4` — BOOL (scope=Axis) · conf=0.80
- `Enable_M5` — BOOL (scope=Axis) · conf=0.80
- `Enable_ServoOnM6` — BOOL (scope=Axis) · conf=0.80

### `fault` (7)

- `AXIS_Fault` — BOOL (scope=controller) · conf=0.85
- `By_Pass_Alarm` — BOOL (scope=controller) · conf=0.85
- `M1_FaultCode` — BOOL (scope=controller) · conf=0.85
- `M2_FaultCode` — BOOL (scope=controller) · conf=0.85
- `M3_FaultCode` — BOOL (scope=controller) · conf=0.85
- `M4_FaultCode` — BOOL (scope=controller) · conf=0.85
- `M7_Fault` — BOOL (scope=Axis) · conf=0.85

### `hmi_input` (59)

- `HmiActualSize` — DINT (scope=controller) · conf=0.95
- `HmiDryRun` — BOOL (scope=controller) · conf=0.95
- `HmiEnableSimulation` — BOOL (scope=controller) · conf=0.95
- `HmiManualEnabled` — BOOL (scope=controller) · conf=0.95
- `HmiOldSize` — DINT (scope=controller) · conf=0.95
- `HmiProductLength` — REAL (scope=controller) · conf=0.95
- `HmiProductLengthJunior` — REAL (scope=controller) · conf=0.95
- `HmiProductLengthMaxi` — REAL (scope=controller) · conf=0.95
- `HmiProductLengthMidi` — REAL (scope=controller) · conf=0.95
- `HmiProductLengthMini` — REAL (scope=controller) · conf=0.95
- `HMIProductLength_Modif` — REAL (scope=controller) · conf=0.95
- `HmiResetAlarm` — BOOL (scope=controller) · conf=0.95
- `HmiSimulatedSpeed` — DINT (scope=controller) · conf=0.95
- `HmiSizeConfirm` — BOOL (scope=controller) · conf=0.95
- `HmiSizeSelector` — DINT (scope=controller) · conf=0.95
- `HmiStartMotor` — BOOL (scope=controller) · conf=0.95
- `HmiStartSimulation` — BOOL (scope=controller) · conf=0.95
- `HMI_ChangeDirection_M1` — BOOL (scope=controller) · conf=0.95
- `HMI_ChangeDirection_M2` — BOOL (scope=controller) · conf=0.95
- `HMI_ChangeDirection_M4` — BOOL (scope=controller) · conf=0.95
- ... +39 más

### `internal_aux` (195)

- `Aux2` — BOOL (scope=controller) · conf=0.75
- `aux35` — BOOL (scope=controller) · conf=0.75
- `aux36` — BOOL (scope=controller) · conf=0.75
- `aux37` — BOOL (scope=controller) · conf=0.75
- `aux38` — BOOL (scope=controller) · conf=0.75
- `aux39` — BOOL (scope=controller) · conf=0.75
- `aux52` — BOOL (scope=controller) · conf=0.75
- `aux53` — BOOL (scope=controller) · conf=0.75
- `AUX10` — BOOL (scope=Axis) · conf=0.75
- `aux103` — BOOL (scope=Axis) · conf=0.75
- `aux104` — BOOL (scope=Axis) · conf=0.75
- `aux105` — BOOL (scope=Axis) · conf=0.75
- `aux113` — BOOL (scope=Axis) · conf=0.75
- `aux114` — BOOL (scope=Axis) · conf=0.75
- `aux115` — BOOL (scope=Axis) · conf=0.75
- `aux123` — BOOL (scope=Axis) · conf=0.75
- `aux124` — BOOL (scope=Axis) · conf=0.75
- `aux125` — BOOL (scope=Axis) · conf=0.75
- `aux13` — BOOL (scope=Axis) · conf=0.75
- `aux14` — BOOL (scope=Axis) · conf=0.75
- ... +175 más

### `io_input` (2)

- `A5_mm_di_Accopiamento_Circ_Coltello` — REAL (scope=AOI_CCCT) · conf=0.85
- `A6_Accopiamento_di_Taglio_Controcoltello` — REAL (scope=AOI_CCCT) · conf=0.85

### `motion_control` (105)

- `MAOC1` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MDOC1` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `VirtualMRP` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAHM7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAJ2M7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAJ2M71` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAJM6` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAM1M7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAM1M71` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAM2M7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MamBkForM1` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MamM7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MamM71` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAMPhaseBkM7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MAMPhaseFrM7` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `MamPhForM1` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `Servo_Off` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `Servo_On` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `LocMAH` — MOTION_INSTRUCTION (scope=DancerCorAndNewRadiusComputation) · conf=1.00
- `LocMAM` — MOTION_INSTRUCTION (scope=DancerCorAndNewRadiusComputation) · conf=1.00
- ... +85 más

### `motion_group` (1)

- `Axis` — MOTION_GROUP (scope=controller) · conf=1.00

### `radius` (16)

- `Belt_Diameter` — REAL (scope=controller) · conf=0.70
- `LocInitRadius` — DINT (scope=DancerCorAndNewRadiusComputation) · conf=0.70
- `RadiusComputation_actual` — REAL (scope=RadiusComputation) · conf=0.70
- `RadiusComputation_Avg` — REAL (scope=RadiusComputation) · conf=0.70
- `Not_FreqUpdateRadius` — BOOL (scope=RadiusComputation) · conf=0.70
- `LocNewRadius` — REAL (scope=AHT_Unwinder) · conf=0.70
- `LocHmiNewRadius` — REAL (scope=AHT_Unwinder) · conf=0.70
- `LocHmiMinRadius` — REAL (scope=AHT_Unwinder) · conf=0.70
- `LocHmiManualRadius` — REAL (scope=AHT_Unwinder) · conf=0.70
- `LocHmiActualRadius` — REAL (scope=AHT_Unwinder) · conf=0.70
- `LocInitRadius` — DINT (scope=AHT_DancerCorAndNewRadiusComputation) · conf=0.70
- `LocNewRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiNewRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiMinRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiManualRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiActualRadius` — REAL (scope=Unwinder) · conf=0.70

### `splice` (54)

- `LocMustBeSpliceA` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `LocMustBeSpliceB` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `Loc_SplicePreparedA` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `Loc_SplicePreparedB` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `LocEnableAxManSplice` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `LocMemManSplice` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `LocDancPosStartEVSplice` — REAL (scope=AHT_CtcSplicer) · conf=0.75
- `LocStartEVSpliceA` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `LocStartEVSpliceB` — BOOL (scope=AHT_CtcSplicer) · conf=0.75
- `Counter_for_SpliceA` — DINT (scope=AHT_CtcSplicer) · conf=0.75
- `Counter_for_SpliceB` — DINT (scope=AHT_CtcSplicer) · conf=0.75
- `LocMustBeSpliceA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocMustBeSpliceB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `Loc_SplicePreparedA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `Loc_SplicePreparedB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocEnableAxManSplice` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocMemManSplice` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocDancPosStartEVSplice` — REAL (scope=CtcDiatecSplicer) · conf=0.75
- `LocStartEVSpliceA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocStartEVSpliceB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- ... +34 más

### `status` (4)

- `IO_Ready` — BOOL (scope=controller) · conf=0.80
- `SercosNet_Ready` — BOOL (scope=controller) · conf=0.80
- `SERCOS_Ready` — BOOL (scope=controller) · conf=0.80
- `Asse_Ready` — BOOL (scope=Servo_Manager) · conf=0.80

### `unknown` (489)

- `ABS_Master_Velocity` — REAL (scope=controller) · conf=0.00
- `AB_Virtual1` — VirtualAxisBlock (scope=controller) · conf=0.00
- `AI_01040` —  (scope=controller) · conf=0.00
- `AI_01041` —  (scope=controller) · conf=0.00
- `Alarm0` — DINT (scope=controller) · conf=0.00
- `Alarm1` — DINT (scope=controller) · conf=0.00
- `Alarm2` — DINT (scope=controller) · conf=0.00
- `Alarm3` — DINT (scope=controller) · conf=0.00
- `AlarmPresence` — BOOL (scope=controller) · conf=0.00
- `AuxCam` — DINT (scope=controller) · conf=0.00
- `AuxCamData` — OUTPUT_CAM (scope=controller) · conf=0.00
- `AXIS_MotionFault` — BOOL (scope=controller) · conf=0.00
- `BIT` — DINT (scope=controller) · conf=0.00
- `BIT1` — BOOL (scope=controller) · conf=0.00
- `Clock0_5Hz` — BOOL (scope=controller) · conf=0.00
- `Clock1Hz` — BOOL (scope=controller) · conf=0.00
- `Clock_Hz` — BOOL (scope=controller) · conf=0.00
- `CompAuxCam` — OUTPUT_COMPENSATION (scope=controller) · conf=0.00
- `ConversionConstant1_Master` — REAL (scope=controller) · conf=0.00
- `DB_M3` — AHT_DriveRoll_withDancer (scope=controller) · conf=0.00
- ... +469 más

