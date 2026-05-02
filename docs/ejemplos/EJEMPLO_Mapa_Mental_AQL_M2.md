# Mapa Mental — CPU_AQL_M2

## Identidad

- **Controlador:** `1756-L61` (firmware 20.12)
- **Studio 5000:** v20.01
- **Schema L5X:** 1.0
- **Creado:** Fri Feb 15 12:45:57 2008
- **Última modificación:** Tue Jan 28 19:53:44 2025
- **Owner del export:** Windows 用户, hch
- **Fecha de export:** Sun Dec 21 10:19:38 2025

## Arquitectura física

Topología: **44 módulos** organizados en árbol bajo el chassis local.

### Topología (árbol parent → child)

```
Local  [1756-L61]
  └─ Ethernet  [1756-ENBT/A]
    └─ DEBO_TNT  [1794-AENT]
      └─ MODULO_0_DI_DEBO_TNT  [1794-IB16/A]
      └─ MODULO_1_DO_DEBO_TNT  [1794-OB16/A]
      └─ ANALOG_DEBO_TNT  [1794-IE4XOE2/B]
  └─ Sercos  [1756-M16SE]
    └─ M9_507U1  [2094-BC02-M02]
    └─ M10_508U1  [2094-BM01]
    └─ M11_510U1  [2094-BM01]
    └─ M12_509U1  [2094-BM01]
    └─ M13_511U1  [2094-BMP5]
    └─ M14_512U1  [2094-BM01]
    └─ M15_513U1  [2094-BM01]
    └─ M16_514U1  [2094-BM02]
    └─ M1_501U1  [2094-BC02-M02]
    └─ M2_502U1  [2094-BM02]
    └─ M4_503U1  [2094-BM02]
    └─ M3_504U1  [2094-BM01]
    └─ M5_505U1  [2094-BMP5]
    └─ M6_506U1  [2094-BMP5]
    └─ M7_507U1  [2094-BM02]
    └─ M8_508U1  [2094-BM02]
  └─ Cnet  [1756-CNB/E]
    └─ NODE_Z1  [1734-ACNR/A]
      └─ (1734-OB8/C)  [1734-OB8/C]
      └─ (1734-OB8/C)  [1734-OB8/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IE2V/C)  [1734-IE2V/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
    └─ NODE_Z3  [1734-ACNR/A]
      └─ (1734-OB8/C)  [1734-OB8/C]
      └─ (1734-OB8/C)  [1734-OB8/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IE2V/C)  [1734-IE2V/C]
  └─ Dinput  [1756-IB32/B]
  └─ (1756-OB16E)  [1756-OB16E]
  └─ Anillo_SynchLink_Consumido  [1756-EN2TR]
    └─ Anillo_SynchLink_Producido  [1756-EN2TR]
      └─ Side_Panel_M2  [1756-L61]
  └─ DInPut_7  [1756-IB32/B]
```

### Resumen por categoría

- **Bridges/scanners:** 6 (2× `1756-L61`, 2× `1756-EN2TR`, 1× `1756-ENBT/A`, 1× `1756-CNB/E`)
- **Adapters de I/O:** 1 (1× `1794-AENT`)
- **Módulos I/O:** 20 (POINT I/O u otros)
- **Drives/servos:** 16 (6× `2094-BM01`, 5× `2094-BM02`, 3× `2094-BMP5`, 2× `2094-BC02-M02`)

## Arquitectura lógica

### Tasks

- **FastTask** [PERIODIC] (rate=20.0ms, priority=10) → Reject
- **MainTask** [CONTINUOUS] (priority=10) → MainProgram
- **Motion** [EVENT] (priority=1) → Axis, ConsumeAxisAOI, Debo_Tela
- **Task500ms** [PERIODIC] (rate=555.0ms, priority=15) → ReadPar

### Programs y rutinas

- **Axis**: 4 rutinas — 4 RLL (main: `Ax`)
  - `Ax`, `R001_A_Corte_AQL`, `R001_B_Estampador_AQL`, `R002_Corte_WB`
- **ConsumeAxisAOI**: 1 rutinas — 1 RLL (main: `Main`)
  - `Main`
- **Debo_Tela**: 7 rutinas — 6 RLL, 1 FBD (main: `R00_Main`)
  - `R00_Main`, `R01_Local`, `R02_Alarm`, `R03_Mapeo`, `R05_TNT_Dancer`, `R08_TNT_Unwinder`, `SLC`
- **MainProgram**: 13 rutinas — 12 RLL, 1 ST (main: `MainRoutine`)
- **ReadPar**: 1 rutinas — 1 ST (main: `ReadPara`)
  - `ReadPara`
- **Reject**: 2 rutinas — 1 ST, 1 RLL (main: `Reject_Control1`)
  - `Cull_Msg`, `Reject_Control1`
- **Reject1**: 1 rutinas — 1 RLL (main: `Reject`)
  - `Reject`

### Tags por alcance

- **Controller-scope:** 775
- **Program-scope:** 57 (distribuidos en 7 programas)
- **AOI-local:** 569 (distribuidos en 24 AOIs)

### AOIs (24 totales)

Distribución por prefijo: 4 con prefijo `Axis`, 1 con prefijo `AOI`; 13 sin prefijo identificable.

Nombres: `AOI_CCCT`, `AxisBlock`, `AxisBlockVM`, `AxisConsumeCIPSync_AOI`, `Axis_Faults_CIP`, `Axis_Faults_Sercos`, `Axis_ObjectCIP`, `Axis_Object_Sercos`, `Blink`, `C_U_Reg`, `CtcDiatecSplicer`, `CtcDiatecSplicerBuffer`, `DancerCorAndNewRadiusComputation`, `Dancer_Tension_Servo`, `FullSpeedSplicer`, `FullSpeedSplicer2`, `Full_Speed_Splicer`, `RadiusComputation`, `Radius_Computation`, `RejectFun`, `RejectFunctionLonger`, `Servo_Manager`, `Unwinder`, `VirtualAxisBlock`

### UDTs (29 totales)

`DataUnw` (110 members), `Motion` (74 members), `Cull_Register` (50 members), `CamSegment` (46 members), `UDT_ConsumeHistory` (42 members), `UDT_Unwinder` (33 members), `OutputSplice` (26 members), `UDT_CIPSyncProduceConsumeAxis` (26 members), `InputSplice` (19 members), `tension_date` (18 members), `Reject` (12 members), `OffsetSize` (10 members), `AxPar` (7 members), `DancerInput` (7 members), `DateTime_Get_Data` (7 members), `DateTime_Type` (7 members), `udt_MAJ` (7 members), `End_Turn` (6 members), `udt_MAG` (6 members), `Size` (5 members), `Arreglo_Master` (4 members), `LengthSize` (3 members), `Position_Size` (3 members), `RejectSize` (3 members), `udt_MAS` (3 members), `AxOutput` (2 members), `Data` (2 members), `Input` (2 members), `CamSize` (1 members)

## Mapa funcional de ejes

**20 ejes primitivos** (tags `AXIS_*` controller-scoped):

| Eje | Tipo | Hardware | AOI principal | Función inferida |
|---|---|---|---|---|
| `Axis_CSTAid` | VIRTUAL | — | — | _Eje virtual / referencia maestra_ |
| `Ax_Spare` | SERVO_DRIVE | — | — | _Spare / no productivo_ |
| `S04N71_DEBOB_AQL_DERECHO` | SERVO_DRIVE | `2094-BC02-M02` (Ch90) | `Unwinder` | Debobinador |
| `S04N72_DEBO_AQL_IZQUIERDO` | SERVO_DRIVE | `2094-BM02` (Ch91) | `Unwinder` | Debobinador |
| `S04N73_ROD_ARRASTRE_TNT` | SERVO_DRIVE | `2094-BM01` (Ch93) | `AxisBlockVM` | Rodillo de arrastre |
| `S04N74_CORTE_APLIC_AQL` | SERVO_DRIVE | `2094-BM02` (Ch92) | `AxisBlockVM` | Corte |
| `S04N75_RODILLO_ESTAMPADOR` | SERVO_DRIVE | `2094-BMP5` (Ch94) | `AxisBlockVM` | Estampador |
| `S04N76_ROD_BAND_ALIM_AQL` | SERVO_DRIVE | `2094-BMP5` (Ch95) | `AxisBlockVM` | Rodillo de banda alimentadora |
| `S04N77_DEBO_TNT_IZQUIERDO` | SERVO_DRIVE | `2094-BM02` (Ch96) | `Axis_Object_Sercos` | Debobinador |
| `S04N78_DEBO_TNT_DERECHO` | SERVO_DRIVE | `2094-BM02` (Ch97) | `Axis_Object_Sercos` | Debobinador |
| `S04N79_UNIDAD_CORTE_WB` | SERVO_DRIVE | `2094-BC02-M02` (Ch20) | `AxisBlockVM` | Corte |
| `S04N80_WB_TAMBOR_TRANSF` | SERVO_DRIVE | `2094-BM01` (Ch21) | `AxisBlockVM` | Tambor / transferencia |
| `S04N81_DEBOB_WB_DERECHO` | SERVO_DRIVE | `2094-BM01` (Ch23) | `Unwinder` | Debobinador |
| `S04N82_DEB_WB_IZQUIERDO` | SERVO_DRIVE | `2094-BM01` (Ch22) | `Unwinder` | Debobinador |
| `S04N83_ROD_BAND_ALIM_WB` | SERVO_DRIVE | `2094-BMP5` (Ch24) | `AxisBlockVM` | Rodillo de banda alimentadora |
| `S04N84_RODILLO_BARRERAS` | SERVO_DRIVE | `2094-BM01` (Ch25) | `AxisBlockVM` | Barreras |
| `S04N85_RODILLO_TRACC_TNT` | SERVO_DRIVE | `2094-BM01` (Ch26) | `AxisBlockVM` | Rodillo de arrastre |
| `S04N86_DANCER_DEBO_TNT` | SERVO_DRIVE | `2094-BM02` (Ch27) | `Axis_Object_Sercos` | Dancer / control de tensión |
| `Vmaster1` | VIRTUAL | — | — | _Eje virtual / referencia maestra_ |
| `VM_Consumer_GrandMaster` | VIRTUAL | — | — | _Eje virtual / referencia maestra_ |

**10 bloques de control de eje** (tags con UDT/AOI tipo `AxisBlock` o `VirtualAxisBlock` — envuelven un eje primitivo con su lógica):

- `AB_M10` (tipo `AxisBlockVM`)
- `AB_M13` (tipo `AxisBlockVM`)
- `AB_M14` (tipo `AxisBlockVM`)
- `AB_M15` (tipo `AxisBlockVM`)
- `AB_M3` (tipo `AxisBlockVM`)
- `AB_M4` (tipo `AxisBlockVM`)
- `AB_M5` (tipo `AxisBlockVM`)
- `AB_M6` (tipo `AxisBlockVM`)
- `AB_M9` (tipo `AxisBlockVM`)
- `AB_Virtual1` (tipo `VirtualAxisBlock`)

## Patrones de código

- **Lenguajes de rutinas:** 56 RLL, 3 ST, 1 FBD
- **Encapsulación por entidad detectada:** 17 tags controller-scope con sufijo `Data` — 10 corresponden a ejes (`M10Data`, `M13Data`, `M14Data`, `M15Data`, `M16_Data`, `M3Data`, `M4Data`, `M5Data`, `M6Data`, `M9Data`); 7 a estructuras auxiliares (`ACQL_Unw_Data`, `AcqlSpliceRejData`, `AuxCamData`, `Virtual1Data`, `WaistBandSpliceRejData`, `WaistBand_Unw_Data`, `WaistbandMissingRejectData`). Sugiere convención de UDT estructurado por entidad.
- **Convención de AOIs:** `(sin prefijo)`=13, `Axis`=4, `AOI`=1

## Issues / observaciones

13 observaciones detectadas durante el parseo, agrupadas:

- **[INFO] `module_without_name`:** 13 ocurrencia(s).
  - _Ejemplo:_ Módulo 1734-OB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-OB8/C)'. Esto es normal para…