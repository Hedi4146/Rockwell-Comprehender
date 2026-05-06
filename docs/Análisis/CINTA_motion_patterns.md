# Motion Patterns — CPU1

**Total matches:** 21 (7 patterns activados)

## Por pattern (count)

- `gear_chain` (7) — Gear Chain (Master-Slave acoplamiento)
- `splice_transition` (7) — Splice Transition (MAJ→MAS→MAJ)
- `homing_sequence` (2) — Homing Sequence
- `axis_lifecycle` (2) — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})
- `output_cam_pair` (1) — Output Cam Pair (MAOC+MDOC)
- `registration_full` (1) — Registration Full (MASR+MAFR)
- `servo_on_off_cycle` (1) — Servo On/Off Cycle (MSO+MSF)

## Detalle

### `gear_chain` — Gear Chain (Master-Slave acoplamiento)

_Eje slave acoplado a master vía MAG (Motion Axis Gear). Implementa sincronización a ratio constante. Si aparece MAG→MAG en la misma routine, indica re-engranaje dinámico (cambio de ratio en runtime, típico en líneas con velocidad variable)._

- **AOIs/AHT_DriveRoll_withDancer/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAG → MAG → MAG → MAJ → MAS → MAS`
  - rungs: [1, 2, 3, 5, 6, 7]
  - _evidence:_ 3 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AHT_DriveRoll_withoutDancer/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAG → MAG → MAG → MAS → MAS`
  - rungs: [1, 2, 3, 4, 5]
  - _evidence:_ 3 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AHT_SyncroAxis/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAG → MAG → MAG → MAM → MAM → MAS → MAS`
  - rungs: [1, 2, 3, 5, 6, 7, 8]
  - _evidence:_ 3 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AHT_Unwinder/Routines/Logic** axis=`AxA` conf=1.00
  - ops: `MAG → MAG → MAJ → MAS → MAS → MAFR`
  - rungs: [25, 28, 32, 33, 39]
  - _evidence:_ 2 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AHT_Unwinder/Routines/Logic** axis=`AxB` conf=1.00
  - ops: `MAG → MAG → MAJ → MAS → MAS → MAFR`
  - rungs: [26, 30, 34, 35, 40]
  - _evidence:_ 2 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [2, 4, 6, 7, 8, 10, 12, 13]
  - _evidence:_ 6 MAGs en misma routine — re-engranaje dinámico
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=1.00
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ 5 MAGs en misma routine — re-engranaje dinámico

### `homing_sequence` — Homing Sequence

_Secuencia de homing del eje. MAH (Motion Axis Home) inicia el comando de búsqueda de referencia. Si aparece junto a MAJ/MAS, indica un manager completo con jog manual de aproximación + homing automático._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [2, 4, 6, 7, 8, 10, 12, 13]
  - _evidence:_ MAH presente, +2 co-ops manager
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=1.00
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ MAH presente, +2 co-ops manager

### `output_cam_pair` — Output Cam Pair (MAOC+MDOC)

_Par activate/deactivate del Output Cam. MAOC (Motion Arm Output Cam) habilita la generación de pulsos de salida coordinados con la posición del eje; MDOC los desarma. Su co-ocurrencia indica control encoder de glue gun, label, knife, o similares._

- **Programs/MainProgram/Routines/MainRoutine** axis=`Vmaster1` conf=1.00
  - ops: `MDOC → MAOC`
  - rungs: [6, 7]
  - _evidence:_ MAOC+MDOC presentes — output cam pair

### `registration_full` — Registration Full (MASR+MAFR)

_Suite completa de registration. MASR (Motion Arm Single Registration) arma una captura puntual; MAFR (Motion Arm Full Registration) arma captura continua. Su co-ocurrencia indica lógica de tracking de marca de registro (mark-to-mark sync)._

- **AOIs/Servo_Manager/Routines/Logic** axis=`Asse` conf=1.00
  - ops: `MASR → MAFR → MSO → MSF`
  - rungs: [0, 2, 3]
  - _evidence:_ MASR+MAFR presentes — registration full

### `servo_on_off_cycle` — Servo On/Off Cycle (MSO+MSF)

_Ciclo de habilitación/deshabilitación del servo. MSO (Motion Servo On) cierra el loop de control; MSF (Motion Servo Off) lo abre. Su co-ocurrencia en una misma routine indica un manager de estado del eje (init + shutdown bajo condiciones de fault o E-stop)._

- **AOIs/Servo_Manager/Routines/Logic** axis=`Asse` conf=1.00
  - ops: `MASR → MAFR → MSO → MSF`
  - rungs: [0, 2, 3]
  - _evidence:_ MSO+MSF presentes — manager de estado

### `axis_lifecycle` — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})

_Routine que orquesta el ciclo completo de un eje: homing (MAH), movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas ops aparecen en la misma routine, suele ser el axis manager / AOI tipo AxisBlock que centraliza todos los comandos de un eje._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [2, 4, 6, 7, 8, 10, 12, 13]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=0.85
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']

### `splice_transition` — Splice Transition (MAJ→MAS→MAJ)

_Transición controlada típica de empalme: el eje arranca con MAJ (jog libre, velocidad inicial), se detiene con MAS al evento de splice, y vuelve a arrancar con MAJ (o se sincroniza con MAG) a la velocidad final del rollo nuevo. Patrón canónico Diatec._

- **AOIs/AHT_DancerCorAndNewRadiusComputation/Routines/Logic** axis=`Ax` conf=0.85
  - ops: `MAJ → MAS`
  - rungs: [7, 8]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AHT_DriveRoll_withDancer/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAG → MAG → MAG → MAJ → MAS → MAS`
  - rungs: [1, 2, 3, 5, 6, 7]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AHT_Unwinder/Routines/Logic** axis=`AxA` conf=0.85
  - ops: `MAG → MAG → MAJ → MAS → MAS → MAFR`
  - rungs: [25, 28, 32, 33, 39]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AHT_Unwinder/Routines/Logic** axis=`AxB` conf=0.85
  - ops: `MAG → MAG → MAJ → MAS → MAS → MAFR`
  - rungs: [26, 30, 34, 35, 40]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [2, 4, 6, 7, 8, 10, 12, 13]
  - _evidence:_ transición parcial MAJ→MAG
- **AOIs/DancerCorAndNewRadiusComputation/Routines/Logic** axis=`Ax` conf=0.85
  - ops: `MAJ → MAS`
  - rungs: [9, 10]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=0.85
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ transición parcial MAJ→MAG
