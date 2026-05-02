# Mapa Mental — CPU1

## Identidad

- **Controlador:** `1768-L43` (firmware 20.13)
- **Studio 5000:** v20.01
- **Schema L5X:** 1.0
- **Creado:** Sun Jul 06 14:02:47 2014
- **Última modificación:** Tue Dec 24 13:11:06 2024
- **Owner del export:** Windows 用户, hch
- **Fecha de export:** Sun Dec 21 10:40:53 2025

## Arquitectura física

Topología: **12 módulos** organizados en árbol bajo el chassis local.

### Topología (árbol parent → child)

```
Local  [1768-L43]
  └─ ETHERNET  [1768-ENBT/A]
    └─ NODE_Z1  [1734-AENT/B]
      └─ (1734-OB8/C)  [1734-OB8/C]
      └─ (1734-OE2V/C)  [1734-OE2V/C]
      └─ (1734-IB8/C)  [1734-IB8/C]
      └─ (1734-IE2V/C)  [1734-IE2V/C]
  └─ SERCOS  [1768-M04SE]
    └─ M1  [2094-BC02-M02]
    └─ M2  [2094-BM01]
    └─ M3  [2094-BM01]
    └─ M4  [2094-BM01]
```

### Resumen por categoría

- **Bridges/scanners:** 3 (1× `1768-L43`, 1× `1768-ENBT/A`, 1× `1768-M04SE`)
- **Adapters de I/O:** 1 (1× `1734-AENT/B`)
- **Módulos I/O:** 4 (POINT I/O u otros)
- **Drives/servos:** 4 (3× `2094-BM01`, 1× `2094-BC02-M02`)

## Arquitectura lógica

### Tasks

- **FastTask** [PERIODIC] (rate=8.0ms, priority=10) → Reject
- **MainTask** [CONTINUOUS] (priority=10) → MainProgram
- **Motion** [EVENT] (priority=10) → Axis
- **Task1000ms** [PERIODIC] (rate=1000.0ms, priority=15) → ReadPar

### Programs y rutinas

- **Axis**: 4 rutinas — 4 RLL (main: `Main`)
  - `Drive_Rolls`, `Main`, `Master`, `Unwinders`
- **MainProgram**: 9 rutinas — 8 RLL, 1 ST (main: `MainRoutine`)
  - `Alarm`, `ChangeSize_Data_MASTER`, `ChangeSize_LenProduct`, `General`, `Glue`, `InitAxis`, `I_O_Interface`, `MainRoutine`, `Motors`
- **ReadPar**: 3 rutinas — 2 RLL, 1 ST (main: `Main1000ms`)
  - `I_O_Status`, `Main1000ms`, `ReadPara`
- **Reject**: 1 rutinas — 1 RLL (main: `RawMat_reject`)
  - `RawMat_reject`

### Tags por alcance

- **Controller-scope:** 209
- **Program-scope:** 240 (distribuidos en 4 programas)
- **AOI-local:** 578 (distribuidos en 26 AOIs)

### AOIs (26 totales)

Distribución por prefijo: 15 con prefijo `AHT`, 1 con prefijo `Servo`; 9 sin prefijo identificable.

Nombres: `AHT_CtcSplicer`, `AHT_DancerCorAndNewRadiusComputation`, `AHT_DriveFaultBit_Decoding`, `AHT_DriveFault_Decoding`, `AHT_DriveRoll_withDancer`, `AHT_DriveRoll_withoutDancer`, `AHT_Enable_DriveAxis`, `AHT_Enable_Reject`, `AHT_MotionAxisError`, `AHT_ON_OFF_CounterValve`, `AHT_RackAxisFault`, `AHT_RackSercosFault`, `AHT_Reject_Block`, `AHT_SyncroAxis`, `AHT_Unwinder`, `AOI_CCCT`, `AxisBlock`, `CtcDiatecSplicer`, `CtcDiatecSplicerBuffer`, `DancerCorAndNewRadiusComputation`, `FullSpeedSplicer`, `FullSpeedSplicer2`, `RadiusComputation`, `Servo_Manager`, `Unwinder`, `VirtualAxisBlock`

### UDTs (10 totales)

`DataUnw` (98 members), `Motion` (73 members), `CamSegment` (46 members), `OutputSplice` (26 members), `InputSplice` (16 members), `AxPar` (7 members), `DancerInput` (7 members), `Reject` (4 members), `Data` (2 members), `Input` (2 members)

## Mapa funcional de ejes

**7 ejes primitivos** (tags `AXIS_*` controller-scoped):

| Eje | Tipo | Hardware | AOI principal | Función inferida |
|---|---|---|---|---|
| `Ax_Spare` | SERVO_DRIVE | — | — | _Spare / no productivo_ |
| `M1` | SERVO_DRIVE | `2094-BC02-M02` (Ch1) | `AHT_Unwinder` | Debobinador |
| `M2` | SERVO_DRIVE | `2094-BM01` (Ch2) | `AHT_Unwinder` | Debobinador |
| `M3` | SERVO_DRIVE | `2094-BM01` (Ch3) | `AHT_DriveRoll_withDancer` | Drive roll con dancer (control de tensión) |
| `M4` | SERVO_DRIVE | `2094-BM01` (Ch4) | `AHT_DriveRoll_withoutDancer` | Drive roll sin dancer |
| `Master` | SERVO_DRIVE | `2094-BM01` (Ch130) | `VirtualAxisBlock` | Eje virtual / master |
| `Vmaster1` | VIRTUAL | — | — | _Eje virtual / referencia maestra_ |

_Nota: AOIs como `AHT_RackSercosFault` aparecen asociadas a múltiples ejes — son AOIs de servicio (manejo de fallas, decoding) y no caracterizan función específica._

**1 bloque de control de eje** (tags con UDT/AOI tipo `AxisBlock` o `VirtualAxisBlock` — envuelven un eje primitivo con su lógica):

- `AB_Virtual1` (tipo `VirtualAxisBlock`)

_Adicionalmente, 4 bloques manager en program-scope:_ `AB_M2`@Axis, `AB_M3`@Axis, `AB_M71`@Axis, `AB_Virtual2`@Axis

## Patrones de código

- **Lenguajes de rutinas:** 48 RLL, 2 ST
- **Encapsulación por entidad detectada:** 6 tags controller-scope con sufijo `Data` — 4 corresponden a ejes (`M1Data`, `M2Data`, `M3Data`, `M4Data`); 2 a estructuras auxiliares (`AuxCamData`, `Virtual1Data`). Sugiere convención de UDT estructurado por entidad.
- **Convención de AOIs:** `AHT`=15, `(sin prefijo)`=9, `Servo`=1
- **AOIs con nombres potencialmente duplicados:** 2 pares — ver sección Issues.

## Issues / observaciones

6 observaciones detectadas durante el parseo, agrupadas:

- **[WARNING] `aoi_naming_collision`:** 2 ocurrencia(s).
  - _Ejemplo:_ AOIs con nombres potencialmente duplicados (base 'Unwinder'): ['AHT_Unwinder', 'Unwinder']. Conviene revisar si son versiones distintas de l…
  - Referencias: `AHT_Unwinder`, `Unwinder`, `AHT_DancerCorAndNewRadiusComputation`, `DancerCorAndNewRadiusComputation`
- **[INFO] `module_without_name`:** 4 ocurrencia(s).
  - _Ejemplo:_ Módulo 1734-OB8/C bajo NODE_Z1 no tiene atributo Name. Se le asigna identificador sintético 'NODE_Z1:port1(1734-OB8/C)'. Esto es normal para…
  - Referencias: `NODE_Z1:port1(1734-OB8/C)`, `NODE_Z1:port1(1734-OE2V/C)`, `NODE_Z1:port1(1734-IB8/C)`, `NODE_Z1:port1(1734-IE2V/C)`