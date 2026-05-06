# Tag Dictionary — CPPIM_BD800_1

**Total tags:** 2460
**Roles distintos detectados:** 16

## Distribución por rol

| Rol | Count | % |
|-----|------:|--:|
| `unknown` | 1665 | 67.7% |
| `safety` | 203 | 8.3% |
| `counter_timer` | 158 | 6.4% |
| `axis_object` | 143 | 5.8% |
| `motion_control` | 115 | 4.7% |
| `hmi_input` | 34 | 1.4% |
| `dancer` | 28 | 1.1% |
| `command` | 26 | 1.1% |
| `enable` | 21 | 0.9% |
| `splice` | 20 | 0.8% |
| `radius` | 19 | 0.8% |
| `reset` | 18 | 0.7% |
| `status` | 5 | 0.2% |
| `fault` | 3 | 0.1% |
| `motion_group` | 1 | 0.0% |
| `limit` | 1 | 0.0% |

## Glosario de roles

- **`axis_object`** — Tag de eje (AXIS_*) — referencia a un servo configurado en el motion group
- **`command`** — Comando (start/stop/exec) — pulso de inicio o detención de acción
- **`counter_timer`** — Estructura TIMER/COUNTER — .EN/.TT/.DN/.PRE/.ACC para temporización o conteo
- **`dancer`** — Dancer (rodillo bailarín) — tag relacionado con control de tensión por danzarín
- **`enable`** — Enable / habilitación — bit que arma una función o módulo
- **`fault`** — Fault / alarma / error — bit de detección de condición anómala
- **`hmi_input`** — Input desde HMI (sufijo _Hmi)
- **`limit`** — Límite / umbral — valor de comparación para alarma o clamp
- **`motion_control`** — Estructura motion control (MOTION_INSTRUCTION) — bits .EN/.DN/.ER de un comando motion
- **`motion_group`** — Motion group (MOTION_GROUP) — agrupador del scheduling motion
- **`radius`** — Radio del rollo — tag de cálculo de diámetro/radio actual
- **`reset`** — Reset / clear — bit que resetea fault, alarma o estado
- **`safety`** — Safety / E-stop — tag con datatype safety o naming safety
- **`splice`** — Splice / empalme — tag relacionado con la lógica de empalme
- **`status`** — Status / feedback / estado — lectura de condición actual del sistema
- **`unknown`** — Sin rol inferible por heurística — requiere inspección manual

## Tags por rol (sample top 20 por rol)

### `axis_object` (143)

- `Converter1_MDP001` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP002` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP003` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP004` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP005` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP006` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_MDP007` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM01` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM02` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM031` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM032` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM04` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `Converter1_UWM05` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD01A_Front_tape_cut_unit` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD01B_Compressing_unit` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD02A_Forming_Drum` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD02B_Core_transfer_drum` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD03A_Tissue_corner_traction` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD03B_Backsheet_corner_traction` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- `SD04A_PE_film_location_traction` — AXIS_CIP_DRIVE (scope=controller) · conf=1.00
- ... +123 más

### `command` (26)

- `AltaBlue_Plus_Command` — AltaBlue_Plus_Command (scope=controller) · conf=0.85
- `AltaBlue_Plus_SW_Command` — AltaBlue_Plus_Parameter (scope=controller) · conf=0.85
- `BuzzerSelect_cmd` — DINT (scope=controller) · conf=0.85
- `CallBuzzer_cmd` — BOOL (scope=controller) · conf=0.85
- `CMD_Index_0` — DINT (scope=controller) · conf=0.85
- `CMD_Index_1` — DINT (scope=controller) · conf=0.85
- `CMD_Index_2` — DINT (scope=controller) · conf=0.85
- `CMD_Index_3` — DINT (scope=controller) · conf=0.85
- `CMD_Index_4` — DINT (scope=controller) · conf=0.85
- `CMD_Index_5` — DINT (scope=controller) · conf=0.85
- `CMD_Index_6` — DINT (scope=controller) · conf=0.85
- `CMD_Index_7` — DINT (scope=controller) · conf=0.85
- `CMD_Index_8` — DINT (scope=controller) · conf=0.85
- `CMD_Index_9` — DINT (scope=controller) · conf=0.85
- `Dust_Remove_System_Start` — BOOL (scope=controller) · conf=0.85
- `FaultBuzzer_cmd` — BOOL (scope=controller) · conf=0.85
- `Machine_Actual_Stop` — DINT (scope=controller) · conf=0.85
- `OSRI_HMI_Command` — FBD_ONESHOT (scope=controller) · conf=0.85
- `ServoPositionRead_cmd` — BOOL (scope=controller) · conf=0.85
- `StartUpBuzzer_cmd` — BOOL (scope=controller) · conf=0.85
- ... +6 más

### `counter_timer` (158)

- `AuxiliaryMotorStartDelay` — TIMER (scope=controller) · conf=1.00
- `Axial_Flow_Fan_Delay_Timer` — TIMER (scope=controller) · conf=1.00
- `BigMotorStartTON` — TIMER (scope=controller) · conf=1.00
- `BreakDelay` — TIMER (scope=controller) · conf=1.00
- `BTSRComm` — TIMER (scope=controller) · conf=1.00
- `BTSR_InitTimer` — TIMER (scope=controller) · conf=1.00
- `BTSR_ModeSwitchTimer` — TIMER (scope=controller) · conf=1.00
- `BuzzerDelay` — TIMER (scope=controller) · conf=1.00
- `BuzzerStop` — TIMER (scope=controller) · conf=1.00
- `ChangeSizeDelay` — TIMER (scope=controller) · conf=1.00
- `ClearErrorDelay` — TIMER (scope=controller) · conf=1.00
- `ContactorDetectTimer` — TIMER (scope=controller) · conf=1.00
- `DelayDorReposition` — TIMER (scope=controller) · conf=1.00
- `EarTapeFinishDelay` — TIMER (scope=controller) · conf=1.00
- `ErrorDisplayShift` — CONTROL (scope=controller) · conf=1.00
- `EstopOffDelayTimer` — TIMER (scope=controller) · conf=1.00
- `FluffFinishDelay` — TIMER (scope=controller) · conf=1.00
- `FluffPulpFinishDelay` — COUNTER (scope=controller) · conf=1.00
- `FluffSpliceReadyposition` — COUNTER (scope=controller) · conf=1.00
- `FluffSplicerWorkposition` — COUNTER (scope=controller) · conf=1.00
- ... +138 más

### `dancer` (28)

- `DancerActualPosition` — DINT (scope=controller) · conf=0.75
- `DancerActualPositionUnused` — DINT (scope=controller) · conf=0.75
- `DancerControl` — DancerControl (scope=controller) · conf=0.75
- `DancerSettingPositionHMIUnused` — DINT (scope=controller) · conf=0.75
- `TractionDancerActualPosition` — DINT (scope=controller) · conf=0.75
- `TractionDancerSettingPosition` — DINT (scope=controller) · conf=0.75
- `UnwinderDancerTension` — DINT (scope=controller) · conf=0.75
- `GearRatio_NoDancer` — REAL (scope=AOI_AxisControl_CIP) · conf=0.75
- `DancerActualPositionRegister` — DINT (scope=AOI_AxisControl_CIP) · conf=0.75
- `DancerSettingPositionRegister` — DINT (scope=AOI_AxisControl_CIP) · conf=0.75
- `DancerRatioRegister` — REAL (scope=AOI_AxisControl_CIP) · conf=0.75
- `GearRatio_WithDancer` — REAL (scope=AOI_AxisControl_CIP) · conf=0.75
- `DancerErrorValue` — REAL (scope=AOI_UnwinderControl) · conf=0.75
- `DancerPositionRestore` — REAL (scope=AOI_UnwinderControl) · conf=0.75
- `DancerSettingPositionForAOI` — DINT (scope=AOI_UnwinderControl) · conf=0.75
- `DancerSpeedValue` — REAL (scope=AOI_UnwinderControl) · conf=0.75
- `DancerOpenFlag` — BOOL (scope=AOI_UnwinderControl) · conf=0.75
- `DancerSettingLimit` — DINT (scope=AOI_UnwinderControl) · conf=0.75
- `DancerInSplcerPosition` — BOOL (scope=AOI_UnwinderControl) · conf=0.75
- `DancerSettingPositionOpen` — DINT (scope=AOI_UnwinderControl) · conf=0.75
- ... +8 más

### `enable` (21)

- `CROUT_ServoPower_Contactor_Enable` — CONFIGURABLE_ROUT (scope=controller) · conf=0.80
- `Machine_E_Stop_Active` — BOOL (scope=controller) · conf=0.80
- `MDP001_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP002_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP003_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP004_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP005_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP006_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MDP007_ServoGroup1_Safeoff_Enable` — BOOL (scope=controller) · conf=0.80
- `MicroStop_Active` — BOOL (scope=controller) · conf=0.80
- `ServoPower_Contactor_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM01_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM02_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM031_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM032_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM04_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `UWM05_ServoGroup_STO_Enable` — BOOL (scope=controller) · conf=0.80
- `PositionRegistration_Enable` — BOOL (scope=MaterialCorrectionCAM_CD) · conf=0.80
- `PhaseCorrection_Enable` — BOOL (scope=MaterialCorrectionCAM_CD) · conf=0.80
- `PositionRegistration_Enable` — BOOL (scope=MaterialCorrection_CD) · conf=0.80
- ... +1 más

### `fault` (3)

- `Air_Pressure_Alarm` — DINT (scope=controller) · conf=0.85
- `BTSR_Comm_Fault` — DINT (scope=controller) · conf=0.85
- `MPAUX5_Standard_IO_Module_Comm_Fault` —  (scope=controller) · conf=0.85

### `hmi_input` (34)

- `CoolingSystemSwitch_HMI` — BOOL (scope=controller) · conf=0.85
- `HMICommand` — DINT (scope=controller) · conf=0.95
- `HMICommand1` — DINT (scope=controller) · conf=0.95
- `HMIPhaseForwardCommand` — DINT (scope=controller) · conf=0.95
- `HMIPhaseReverseCommand` — DINT (scope=controller) · conf=0.95
- `HMI_CommandIndex` — DINT (scope=controller) · conf=0.95
- `HMI_HomeReset` — BOOL (scope=controller) · conf=0.95
- `HotMeltSwitch_HMI` — DINT (scope=controller) · conf=0.85
- `ServoClutch_HMI` — BOOL (scope=controller) · conf=0.85
- `UnwinderParameter_HMI` — UDT_HMI_UnwinderParameter (scope=controller) · conf=0.85
- `VBP_ParameterSwitch_HMI` — DINT (scope=controller) · conf=0.85
- `VBP_PumpName_HMI` — DINT (scope=controller) · conf=0.85
- `VibrationDisplay_HMI` — REAL (scope=controller) · conf=0.85
- `HMI_CurrentData_Old` — Udt_CurrentData (scope=MainProgram) · conf=0.95
- `HMI_CurrentDateTime` — Udt_DataTime (scope=MainProgram) · conf=0.95
- `HMI_CurrentDateTime_old` — Udt_DataTime (scope=MainProgram) · conf=0.95
- `HMI_Efficency` — REAL (scope=MainProgram) · conf=0.95
- `HMI_GenericData` — Udt_GenericData (scope=MainProgram) · conf=0.95
- `HMI_PlcClock_AcceptEdits` — BOOL (scope=MainProgram) · conf=0.95
- `HMI_PlcClock_DiscardEdits` — BOOL (scope=MainProgram) · conf=0.95
- ... +14 más

### `limit` (1)

- `NetOperatingTime_Min` — REAL (scope=MainProgram) · conf=0.90

### `motion_control` (115)

- `BackcutunitAxisMRP` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `BackEarVirtualAxisMRP` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `Converter_Reset` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `Converter_ShutdownReset` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `GlueCamSwitchControl` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `GlueCamSwitchControl2` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `GlueCamSwitchControlOff` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `GlueCamSwitchControlOff2` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineChangeJog` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineEStop` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineJogModeRun` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineJOGStop` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineRunJog` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MachineStop` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAG_BackEarVirtual` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAG_BackEarVirtual_cutunit` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAG_FrontEarVirtual` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAG_WaistbandVirtual` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MAPC_BackEarVirtual_cutunit` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- `MasterAxisMRP` — MOTION_INSTRUCTION (scope=controller) · conf=1.00
- ... +95 más

### `motion_group` (1)

- `Axis` — MOTION_GROUP (scope=controller) · conf=1.00

### `radius` (19)

- `AQL_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Backear_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `BackSheet_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Cuff_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `DiameterDisplayHMI_Unused` — REAL (scope=controller) · conf=0.70
- `Frontear_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `FrontTape_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Hook_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `MaterialActualDiameter` — DINT (scope=controller) · conf=0.70
- `PEfilm_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Tissue_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Topsheet_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `Waistband_MaterialActualDiameterDisplay` — DINT (scope=controller) · conf=0.70
- `MaterialActualDiameter_Real` — REAL (scope=MainProgram) · conf=0.70
- `DriveAxisDiameterRegister` — REAL (scope=AOI_AxisControl_CIP) · conf=0.70
- `DiameterSpeed` — REAL (scope=AOI_UnwinderControl) · conf=0.70
- `MaxDiameter` — REAL (scope=AOI_UnwinderControl) · conf=0.70
- `MinDiameter` — REAL (scope=AOI_UnwinderControl) · conf=0.70
- `MaterialFinishDiameterWarming` — DINT (scope=AOI_UnwinderControl) · conf=0.70

### `reset` (18)

- `OSF_Reset` — BOOL (scope=controller) · conf=0.90
- `OSF_UWM02_Reset` — BOOL (scope=controller) · conf=0.90
- `OSF_UWM031_Reset` — BOOL (scope=controller) · conf=0.90
- `OSF_UWM032_Reset` — BOOL (scope=controller) · conf=0.90
- `OSF_UWM04_Reset` — BOOL (scope=controller) · conf=0.90
- `OSF_UWM05_Reset` — BOOL (scope=controller) · conf=0.90
- `OSRI_Reset` — FBD_ONESHOT (scope=controller) · conf=0.90
- `Position_Reset` — BOOL (scope=controller) · conf=0.90
- `Reset_Program` — BOOL (scope=controller) · conf=0.90
- `RO_CPT_TIME_Reset` — BOOL (scope=controller) · conf=0.90
- `UWM031_32_Reset` — BOOL (scope=controller) · conf=0.90
- `UWM04_Reset` — BOOL (scope=controller) · conf=0.90
- `UWM05_Reset` — BOOL (scope=controller) · conf=0.90
- `Vision_Reset` — BOOL (scope=MainProgram) · conf=0.90
- `UWM01_Reset` — BOOL (scope=SafetyProgram) · conf=0.90
- `UWM02_Reset` — BOOL (scope=SafetyProgram) · conf=0.90
- `UWM031_Reset` — BOOL (scope=SafetyProgram) · conf=0.90
- `UWM03_Reset` — BOOL (scope=SafetyProgram) · conf=0.90

### `safety` (203)

- `CROUT_MDP001_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP002_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP003_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP004_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP005_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP006_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_MDP007_ServoGroup1_Safeoff` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM01_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM02_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM031_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM032_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM04_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `CROUT_UWM05_ServoGroup_STO` — CONFIGURABLE_ROUT (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate1_1` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate1_2` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate1_3` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate2_1` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate2_2` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate2_3` — BOOL (scope=controller) · conf=0.85
- `DCSTL_InputStatus_Main_SafetyGate3_1` — BOOL (scope=controller) · conf=0.85
- ... +183 más

### `splice` (20)

- `fluffsplicepulse` — BOOL (scope=controller) · conf=0.75
- `FluffSplicerCOUNT` — DINT (scope=controller) · conf=0.75
- `FluffSplicerFlag` — BOOL (scope=controller) · conf=0.75
- `FluffSplicerPumpWork` — BOOL (scope=controller) · conf=0.75
- `FluffSplicerSetting` — REAL (scope=controller) · conf=0.75
- `FluffSpliceSpeedDownNumberSetting` — DINT (scope=controller) · conf=0.75
- `FluffSpliceSpeedDownSetting` — DINT (scope=controller) · conf=0.75
- `FluffSpliceSpeedDownSetting1` — DINT (scope=controller) · conf=0.75
- `FluffSpliceSplicerSetting` — DINT (scope=controller) · conf=0.75
- `FluffSpliceSplicerSettingRegister` — DINT (scope=controller) · conf=0.75
- `FluffSpliceWaitSetting` — DINT (scope=controller) · conf=0.75
- `FluffSpliceWaitSettingRegister` — DINT (scope=controller) · conf=0.75
- `ManualSpliceButton` — BOOL (scope=controller) · conf=0.75
- `SplicerTorqueSettingHMI` — DINT (scope=controller) · conf=0.75
- `SpliceActionTime` — DINT (scope=AOI_UnwinderControl) · conf=0.75
- `LeftSideSpliceFlag` — BOOL (scope=AOI_UnwinderControl) · conf=0.75
- `MaterialSpliceFlag` — BOOL (scope=AOI_UnwinderControl) · conf=0.75
- `RightSideSpliceFlag` — BOOL (scope=AOI_UnwinderControl) · conf=0.75
- `UnwindDecelerateForPositionSplice` — REAL (scope=AOI_UnwinderControl) · conf=0.75
- `SpliceActionStartTime` — DINT (scope=AOI_UnwinderControl) · conf=0.75

### `status` (5)

- `All_Estop_Ready` — BOOL (scope=controller) · conf=0.80
- `AltaBlue_Plus_State` — AltaBlue_Plus_State (scope=controller) · conf=0.80
- `BTSR_Ready` — DINT (scope=controller) · conf=0.80
- `SafeI_Status` — DINT (scope=controller) · conf=0.80
- `ServoPower_Contactor_Feedback` — BOOL (scope=controller) · conf=0.80

### `unknown` (1665)

- `ABP_ParameterSelect` — DINT (scope=controller) · conf=0.00
- `ActualFlowValue` — REAL (scope=controller) · conf=0.00
- `ActualPressureValue` — REAL (scope=controller) · conf=0.00
- `AddressIndex` — DINT (scope=controller) · conf=0.00
- `AlarmRedLamp` —  (scope=controller) · conf=0.00
- `AlarmSwitch` — DINT (scope=controller) · conf=0.00
- `AllSafetyGuard_RDY_DRSide` — BOOL (scope=controller) · conf=0.00
- `AllSafetyGuard_RDY_OPSide` — BOOL (scope=controller) · conf=0.00
- `AllWaysOff` — BOOL (scope=controller) · conf=0.00
- `AllWaysOn` — BOOL (scope=controller) · conf=0.00
- `AltaBluePlusPump` — UDT_GlueMotorEnable (scope=controller) · conf=0.00
- `AltaBluePlus_Index` — DINT (scope=controller) · conf=0.00
- `AltaBlue_Plus` — raC_Opr_NetModbusTCPClient (scope=controller) · conf=0.00
- `AltaBlue_Plus_CommandCompare` — INT (scope=controller) · conf=0.00
- `AltaBlue_Plus_CommandHMI` — AltaBlue_Plus_Command (scope=controller) · conf=0.00
- `AltaBlue_Plus_Data` — raC_UDT_ModbusClientData (scope=controller) · conf=0.00
- `AltaBlue_Plus_Display` — AltaBlue_Plus_Display (scope=controller) · conf=0.00
- `AltaBlue_Plus_DisplayHMI` — AltaBlue_Plus_Display (scope=controller) · conf=0.00
- `AltaBlue_Plus_EN_0` — BOOL (scope=controller) · conf=0.00
- `AltaBlue_Plus_EN_1` — BOOL (scope=controller) · conf=0.00
- ... +1645 más

