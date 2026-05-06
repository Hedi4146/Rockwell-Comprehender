# Tag Dictionary — CPU_AQL_M2

**Total tags:** 1401
**Roles distintos detectados:** 18

## Distribución por rol

| Rol | Count | % |
|-----|------:|--:|
| `unknown` | 767 | 54.7% |
| `counter_timer` | 197 | 14.1% |
| `motion_control` | 96 | 6.9% |
| `internal_aux` | 88 | 6.3% |
| `hmi_input` | 79 | 5.6% |
| `splice` | 52 | 3.7% |
| `command` | 32 | 2.3% |
| `axis_object` | 23 | 1.6% |
| `radius` | 20 | 1.4% |
| `dancer` | 13 | 0.9% |
| `axis_data` | 10 | 0.7% |
| `reset` | 6 | 0.4% |
| `enable` | 6 | 0.4% |
| `status` | 5 | 0.4% |
| `setpoint` | 3 | 0.2% |
| `io_input` | 2 | 0.1% |
| `motion_group` | 1 | 0.1% |
| `fault` | 1 | 0.1% |

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
- **`reset`** — Reset / clear — bit que resetea fault, alarma o estado
- **`setpoint`** — Setpoint / referencia objetivo — valor target hacia el que se controla
- **`splice`** — Splice / empalme — tag relacionado con la lógica de empalme
- **`status`** — Status / feedback / estado — lectura de condición actual del sistema
- **`unknown`** — Sin rol inferible por heurística — requiere inspección manual

## Tags por rol (sample top 20 por rol)

### `axis_data` (10)

- `M10Data` — Data (scope=controller) · conf=0.90
- `M13Data` — Data (scope=controller) · conf=0.90
- `M14Data` — Data (scope=controller) · conf=0.90
- `M15Data` — Data (scope=controller) · conf=0.90
- `M16_Data` — tension_date (scope=controller) · conf=0.90
- `M3Data` — Data (scope=controller) · conf=0.90
- `M4Data` — Data (scope=controller) · conf=0.90
- `M5Data` — Data (scope=controller) · conf=0.90
- `M6Data` — Data (scope=controller) · conf=0.90
- `M9Data` — Data (scope=controller) · conf=0.90

### `axis_object` (23)

- `AxisFault1` — Axis_Faults_Sercos (scope=controller) · conf=1.00
- `Axis_CSTAid` — AXIS_VIRTUAL (scope=controller) · conf=1.00
- `Ax_Spare` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `Objecto` — Axis_Object_Sercos (scope=controller) · conf=1.00
- `S04N71_DEBOB_AQL_DERECHO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N72_DEBO_AQL_IZQUIERDO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N73_ROD_ARRASTRE_TNT` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N74_CORTE_APLIC_AQL` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N75_RODILLO_ESTAMPADOR` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N76_ROD_BAND_ALIM_AQL` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N77_DEBO_TNT_IZQUIERDO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N78_DEBO_TNT_DERECHO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N79_UNIDAD_CORTE_WB` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N80_WB_TAMBOR_TRANSF` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N81_DEBOB_WB_DERECHO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N82_DEB_WB_IZQUIERDO` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N83_ROD_BAND_ALIM_WB` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N84_RODILLO_BARRERAS` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N85_RODILLO_TRACC_TNT` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- `S04N86_DANCER_DEBO_TNT` — AXIS_SERVO_DRIVE (scope=controller) · conf=1.00
- ... +3 más

### `command` (32)

- `Cmd_Disable` — BOOL (scope=controller) · conf=0.85
- `Cmd_Enable` — BOOL (scope=controller) · conf=0.85
- `CMD_Home_M4` — BOOL (scope=controller) · conf=0.85
- `CMD_Home_M5` — BOOL (scope=controller) · conf=0.85
- `CMD_Home_M9` — BOOL (scope=controller) · conf=0.85
- `Cmd_Reset` — BOOL (scope=controller) · conf=0.85
- `Cmd_ServoSelect` — BOOL (scope=controller) · conf=0.85
- `Cmd_Stop` — BOOL (scope=controller) · conf=0.85
- `Cmd_Unwind` — BOOL (scope=controller) · conf=0.85
- `M4_Pos_Phase_Command` — REAL (scope=controller) · conf=0.85
- `M5_Pos_Phase_Command` — REAL (scope=controller) · conf=0.85
- `M9_Pos_Phase_Command` — REAL (scope=controller) · conf=0.85
- `single_packing_no_jam_start` — DINT (scope=controller) · conf=0.85
- `Start_Blower_AQL` — BOOL (scope=controller) · conf=0.85
- `Start_Blower_Waits_Band` — BOOL (scope=controller) · conf=0.85
- `Start_Homing_M4` — BOOL (scope=controller) · conf=0.85
- `Start_Homing_M5` — BOOL (scope=controller) · conf=0.85
- `Start_Machine` — BOOL (scope=controller) · conf=0.85
- `Start_Reposition_M4` — BOOL (scope=controller) · conf=0.85
- `Start_Reposition_M5` — BOOL (scope=controller) · conf=0.85
- ... +12 más

### `counter_timer` (197)

- `Air_Blast_Timer` — TIMER (scope=controller) · conf=1.00
- `apertura_guardas` — COUNTER (scope=controller) · conf=1.00
- `apertura_guardas_wb` — COUNTER (scope=controller) · conf=1.00
- `Bit_Retention_C_AQL` — TIMER (scope=controller) · conf=1.00
- `Bit_Retention_C_WB` — TIMER (scope=controller) · conf=1.00
- `Bit_Retention_E_AQL` — TIMER (scope=controller) · conf=1.00
- `Confir_Running` — TIMER (scope=controller) · conf=1.00
- `CONTADOR_CINTA` — COUNTER (scope=controller) · conf=1.00
- `COUNTER_1` — COUNTER (scope=controller) · conf=1.00
- `CR30_AQL_FLT_TMR` — TIMER (scope=controller) · conf=1.00
- `CTU1` — COUNTER (scope=controller) · conf=1.00
- `CTU10` — COUNTER (scope=controller) · conf=1.00
- `CTU11` — COUNTER (scope=controller) · conf=1.00
- `CTU13` — COUNTER (scope=controller) · conf=1.00
- `CTU14` — COUNTER (scope=controller) · conf=1.00
- `CTU15` — COUNTER (scope=controller) · conf=1.00
- `CTU16` — COUNTER (scope=controller) · conf=1.00
- `CTU17` — COUNTER (scope=controller) · conf=1.00
- `CTU18` — COUNTER (scope=controller) · conf=1.00
- `CTU19` — COUNTER (scope=controller) · conf=1.00
- ... +177 más

### `dancer` (13)

- `Dancer_Actual_Position` — REAL (scope=controller) · conf=0.75
- `K_Gain_Dancer_Left` — REAL (scope=controller) · conf=0.75
- `K_Gain_Dancer_Right` — REAL (scope=controller) · conf=0.75
- `M785_Dancer_TNT_Homed` — BOOL (scope=controller) · conf=0.75
- `SP_Dancer_TNT_Normal` — INT (scope=controller) · conf=0.75
- `SP_Dancer_TNT_Splice` — INT (scope=controller) · conf=0.75
- `TNT_Dancer_spd` — INT (scope=controller) · conf=0.75
- `TNT_Error_Dancer` — REAL (scope=controller) · conf=0.75
- `TNT_Sensor_Home_Dancer` — BOOL (scope=controller) · conf=0.75
- `LocMemDancerPos1` — REAL (scope=DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerSetpoint` — REAL (scope=DancerCorAndNewRadiusComputation) · conf=0.75
- `StopPositionDancer` — DINT (scope=DancerCorAndNewRadiusComputation) · conf=0.75
- `LocDancerPositionB` — DINT (scope=Unwinder) · conf=0.75

### `enable` (6)

- `Enable_Start_Stop_Folding_Cam` — BOOL (scope=controller) · conf=0.80
- `Reject_Enable` — DINT (scope=controller) · conf=0.80
- `SISTEMAS_VISION_ENABLE` — BOOL (scope=controller) · conf=0.80
- `Splice_TNT_active` — BOOL (scope=controller) · conf=0.80
- `Enable_Save_Pos_phase_M7` — BOOL (scope=Axis) · conf=0.80
- `Enable_Calc_Diameter` — BOOL (scope=Radius_Computation) · conf=0.80

### `fault` (1)

- `TNT_Alarm_Present` — BOOL (scope=controller) · conf=0.85

### `hmi_input` (79)

- `HmiAcqlAlarmDiameter` — REAL (scope=controller) · conf=0.95
- `HmiAcqlLength` — REAL (scope=controller) · conf=0.95
- `HmiCountLubrication` — DINT (scope=controller) · conf=0.95
- `HmiDelayBlowClean` — DINT (scope=controller) · conf=0.95
- `HmiDelayLubrication` — DINT (scope=controller) · conf=0.95
- `HmiDisableTimeRampM3` — BOOL (scope=controller) · conf=0.95
- `HmiDryRun` — BOOL (scope=controller) · conf=0.95
- `HmiEnableACQL` — BOOL (scope=controller) · conf=0.95
- `HmiEnableBlowClean` — BOOL (scope=controller) · conf=0.95
- `HmiEnableLubrication` — BOOL (scope=controller) · conf=0.95
- `HmiEnableM3` — BOOL (scope=controller) · conf=0.95
- `HmiEnableSimulation` — BOOL (scope=controller) · conf=0.95
- `HmiEnableWaistBand` — BOOL (scope=controller) · conf=0.95
- `HmiInsertWaistbandUnwinder` — BOOL (scope=controller) · conf=0.95
- `HmiM10DriveFault` — DINT (scope=controller) · conf=0.95
- `HmiM11DriveFault` — DINT (scope=controller) · conf=0.95
- `HmiM12DriveFault` — DINT (scope=controller) · conf=0.95
- `HmiM13DriveFault` — DINT (scope=controller) · conf=0.95
- `HmiM14DriveFault` — DINT (scope=controller) · conf=0.95
- `HmiM15DriveFault` — DINT (scope=controller) · conf=0.95
- ... +59 más

### `internal_aux` (88)

- `Aux2` — BOOL (scope=controller) · conf=0.75
- `aux28` — BOOL (scope=controller) · conf=0.75
- `aux29` — BOOL (scope=controller) · conf=0.75
- `Aux1` — BOOL (scope=Servo_Manager) · conf=0.75
- `Aux2` — BOOL (scope=Servo_Manager) · conf=0.75
- `Aux3` — BOOL (scope=Servo_Manager) · conf=0.75
- `Aux1` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux2` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux3` — BOOL (scope=AxisBlock) · conf=0.75
- `aux4` — BOOL (scope=AxisBlock) · conf=0.75
- `aux5` — BOOL (scope=AxisBlock) · conf=0.75
- `aux6` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux7` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux8` — BOOL (scope=AxisBlock) · conf=0.75
- `aux9` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux15` — BOOL (scope=AxisBlock) · conf=0.75
- `Aux1` — BOOL (scope=AxisBlockVM) · conf=0.75
- `Aux2` — BOOL (scope=AxisBlockVM) · conf=0.75
- `Aux3` — BOOL (scope=AxisBlockVM) · conf=0.75
- `aux4` — BOOL (scope=AxisBlockVM) · conf=0.75
- ... +68 más

### `io_input` (2)

- `A5_mm_di_Accopiamento_Circ_Coltello` — REAL (scope=AOI_CCCT) · conf=0.85
- `A6_Accopiamento_di_Taglio_Controcoltello` — REAL (scope=AOI_CCCT) · conf=0.85

### `motion_control` (96)

- `M4_MAH` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M4_MAJ` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M4_MAS` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M5_MAH` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M5_MAJ` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M5_MAS` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M9_MAH` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M9_MAJ` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M9_MAS` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_HOME_M4` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_HOME_M5` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_HOME_M9` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_Reposition_M4` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_Reposition_M5` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAM_Reposition_M9` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAOC1` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MDOC1` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `VirtualMRP` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `M7_JOG_POS_2` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- `M7_Move_In_Jog` — MOTION_INSTRUCTION (scope=Axis) · conf=1.00
- ... +76 más

### `motion_group` (1)

- `Axis` — MOTION_GROUP (scope=controller) · conf=1.00

### `radius` (20)

- `H_Lim_Diameter_Avg` — DINT (scope=controller) · conf=0.70
- `Kp_Diameter_Left` — REAL (scope=controller) · conf=0.70
- `Kp_Diameter_Right` — REAL (scope=controller) · conf=0.70
- `Left_Enable_Calc_Diameter` — BOOL (scope=controller) · conf=0.70
- `L_Lim_Diameter_Avg` — DINT (scope=controller) · conf=0.70
- `Right_Enable_Calc_Diameter` — BOOL (scope=controller) · conf=0.70
- `SCL_TNT_Left_Diameter_Avg` — REAL (scope=controller) · conf=0.70
- `SCL_TNT_Right_Diameter_Avg` — REAL (scope=controller) · conf=0.70
- `LocInitRadius` — DINT (scope=DancerCorAndNewRadiusComputation) · conf=0.70
- `RadiusAvg` — REAL (scope=RadiusComputation) · conf=0.70
- `LocSensorDiameter` — REAL (scope=RadiusComputation) · conf=0.70
- `LocNewRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiNewRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiMinRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiManualRadius` — REAL (scope=Unwinder) · conf=0.70
- `LocHmiActualRadius` — REAL (scope=Unwinder) · conf=0.70
- `Diameter_Avg` — REAL (scope=Radius_Computation) · conf=0.70
- `Kp_Diameter` — REAL (scope=Radius_Computation) · conf=0.70
- `H_Lim_Diameter_Avg` — REAL (scope=Radius_Computation) · conf=0.70
- `L_Lim_Diameter_Avg` — REAL (scope=Radius_Computation) · conf=0.70

### `reset` (6)

- `CLR_Cull_Reg` — BOOL (scope=controller) · conf=0.90
- `Counter_Reset` — DINT (scope=controller) · conf=0.90
- `Reset_Acum_Flag` — BOOL (scope=controller) · conf=0.90
- `ONS_JOG_Start_Clear` — BOOL (scope=Axis) · conf=0.90
- `ONS_Reset` — BOOL (scope=AxisConsumeCIPSync_AOI) · conf=0.90
- `Reset_Add_ONS` — BOOL (scope=RejectFunctionLonger) · conf=0.90

### `setpoint` (3)

- `GUARDAS_FROM_SP` — BOOL (scope=controller) · conf=0.90
- `MSG_From_Sp` — MESSAGE (scope=controller) · conf=0.90
- `Run_Ok_SP` —  (scope=controller) · conf=0.90

### `splice` (52)

- `AcqlSpliceRejData` — Reject (scope=controller) · conf=0.75
- `PB_Prepare_Splice_TNT` — BOOL (scope=controller) · conf=0.75
- `SW_Left_Guard_Splicer_TNT` — BOOL (scope=controller) · conf=0.75
- `SW_Right_Guard_Splicer_TNT` — BOOL (scope=controller) · conf=0.75
- `TNT_Left_SpliceON` — BOOL (scope=controller) · conf=0.75
- `TNT_Left_Splice_Prepared` — BOOL (scope=controller) · conf=0.75
- `TNT_Right_SpliceON` — BOOL (scope=controller) · conf=0.75
- `TNT_Right_Splice_Prepared` — BOOL (scope=controller) · conf=0.75
- `torque_Splice_TNT` — DINT (scope=controller) · conf=0.75
- `Torque_Splice_TNT_TLN` — DINT (scope=controller) · conf=0.75
- `WaistBandSpliceRejData` — Reject (scope=controller) · conf=0.75
- `LocMustBeSpliceA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocMustBeSpliceB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `Loc_SplicePreparedA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `Loc_SplicePreparedB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocEnableAxManSplice` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocMemManSplice` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocDancPosStartEVSplice` — REAL (scope=CtcDiatecSplicer) · conf=0.75
- `LocStartEVSpliceA` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- `LocStartEVSpliceB` — BOOL (scope=CtcDiatecSplicer) · conf=0.75
- ... +32 más

### `status` (5)

- `ControlNet_Node_Z1_Status` — DINT (scope=controller) · conf=0.80
- `ControlNet_Node_Z3_Status` — DINT (scope=controller) · conf=0.80
- `ControlNet_Status` — DINT (scope=controller) · conf=0.80
- `Sercos_Ready` — BOOL (scope=controller) · conf=0.80
- `Asse_Ready` — BOOL (scope=Servo_Manager) · conf=0.80

### `unknown` (767)

- `AB_M10` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M13` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M14` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M15` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M3` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M4` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M5` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M6` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_M9` — AxisBlockVM (scope=controller) · conf=0.00
- `AB_Virtual1` — VirtualAxisBlock (scope=controller) · conf=0.00
- `Accum_Reject_Counter` — Cull_Register (scope=controller) · conf=0.00
- `ACQL_Unw_Data` — DataUnw (scope=controller) · conf=0.00
- `ADD_ON_SAP` — BOOL (scope=controller) · conf=0.00
- `Air_Blast` —  (scope=controller) · conf=0.00
- `AJUSTAR_CAMARA` — BOOL (scope=controller) · conf=0.00
- `Alarm0` — DINT (scope=controller) · conf=0.00
- `Alarm1` — DINT (scope=controller) · conf=0.00
- `AlarmPresence` — BOOL (scope=controller) · conf=0.00
- `ANVIL_AQL` — BOOL (scope=controller) · conf=0.00
- `ANVIL_CINTA_FRONTAL` — BOOL (scope=controller) · conf=0.00
- ... +747 más

