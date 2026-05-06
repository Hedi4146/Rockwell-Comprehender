# Motion Patterns — CPU_AQL_M2

**Total matches:** 43 (7 patterns activados)

## Por pattern (count)

- `splice_transition` (12) — Splice Transition (MAJ→MAS→MAJ)
- `axis_lifecycle` (9) — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})
- `gear_chain` (8) — Gear Chain (Master-Slave acoplamiento)
- `homing_sequence` (7) — Homing Sequence
- `registration_full` (3) — Registration Full (MASR+MAFR)
- `servo_on_off_cycle` (3) — Servo On/Off Cycle (MSO+MSF)
- `output_cam_pair` (1) — Output Cam Pair (MAOC+MDOC)

## Detalle

### `gear_chain` — Gear Chain (Master-Slave acoplamiento)

_Eje slave acoplado a master vía MAG (Motion Axis Gear). Implementa sincronización a ratio constante. Si aparece MAG→MAG en la misma routine, indica re-engranaje dinámico (cambio de ratio en runtime, típico en líneas con velocidad variable)._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAM → MAM`...
  - rungs: [2, 3, 4, 5, 6, 7, 8, 9]
  - _evidence:_ 5 MAGs en misma routine — re-engranaje dinámico
- **AOIs/AxisBlockVM/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [3, 5, 7, 8, 9, 11, 13, 14]
  - _evidence:_ 6 MAGs en misma routine — re-engranaje dinámico
- **AOIs/Unwinder/Routines/Logic** axis=`AxA` conf=1.00
  - ops: `MAG → MAG → MAJ → MAS → MAS`
  - rungs: [36, 41, 44, 45]
  - _evidence:_ 2 MAGs en misma routine — re-engranaje dinámico
- **AOIs/Unwinder/Routines/Logic** axis=`AxB` conf=1.00
  - ops: `MAG → MAG → MAJ → MAS → MAS`
  - rungs: [38, 42, 46, 47]
  - _evidence:_ 2 MAGs en misma routine — re-engranaje dinámico
- **AOIs/Unwinder/Routines/Logic** axis=`AxC` conf=1.00
  - ops: `MAG → MAG → MAS → MAS → MAS → MAM → MAM`
  - rungs: [39, 40, 48, 49, 50, 51, 52]
  - _evidence:_ 2 MAGs en misma routine — re-engranaje dinámico
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=1.00
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ 5 MAGs en misma routine — re-engranaje dinámico

### `homing_sequence` — Homing Sequence

_Secuencia de homing del eje. MAH (Motion Axis Home) inicia el comando de búsqueda de referencia. Si aparece junto a MAJ/MAS, indica un manager completo con jog manual de aproximación + homing automático._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAM → MAM`...
  - rungs: [2, 3, 4, 5, 6, 7, 8, 9]
  - _evidence:_ MAH presente, +2 co-ops manager
- **AOIs/AxisBlockVM/Routines/Logic** axis=`PhysicalAx` conf=1.00
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [3, 5, 7, 8, 9, 11, 13, 14]
  - _evidence:_ MAH presente, +2 co-ops manager
- **AOIs/Dancer_Tension_Servo/Routines/Logic** axis=`Ref_ServoAxis` conf=1.00
  - ops: `MAJ → MAS → MAH`
  - rungs: [1, 2]
  - _evidence:_ MAH presente, +2 co-ops manager
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=1.00
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ MAH presente, +2 co-ops manager
- **Programs/Axis/Routines/R001_A_Corte_AQL** axis=`S04N74_CORTE_APLIC_AQL` conf=1.00
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ MAH presente, +2 co-ops manager
- **Programs/Axis/Routines/R001_B_Estampador_AQL** axis=`S04N75_RODILLO_ESTAMPADOR` conf=1.00
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ MAH presente, +2 co-ops manager
- **Programs/Axis/Routines/R002_Corte_WB** axis=`S04N79_UNIDAD_CORTE_WB` conf=1.00
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ MAH presente, +2 co-ops manager

### `output_cam_pair` — Output Cam Pair (MAOC+MDOC)

_Par activate/deactivate del Output Cam. MAOC (Motion Arm Output Cam) habilita la generación de pulsos de salida coordinados con la posición del eje; MDOC los desarma. Su co-ocurrencia indica control encoder de glue gun, label, knife, o similares._

- **Programs/MainProgram/Routines/MainRoutine** axis=`Vmaster1` conf=1.00
  - ops: `MDOC → MAOC`
  - rungs: [3, 4]
  - _evidence:_ MAOC+MDOC presentes — output cam pair

### `registration_full` — Registration Full (MASR+MAFR)

_Suite completa de registration. MASR (Motion Arm Single Registration) arma una captura puntual; MAFR (Motion Arm Full Registration) arma captura continua. Su co-ocurrencia indica lógica de tracking de marca de registro (mark-to-mark sync)._

- **AOIs/Axis_ObjectCIP/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MAFR → MASR → MAS`
  - rungs: [0, 1, 2, 3]
  - _evidence:_ MASR+MAFR presentes — registration full
- **AOIs/Axis_Object_Sercos/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MAFR → MASR → MAS`
  - rungs: [0, 1, 2, 3]
  - _evidence:_ MASR+MAFR presentes — registration full
- **AOIs/Servo_Manager/Routines/Logic** axis=`Asse` conf=1.00
  - ops: `MASR → MAFR → MSO → MSF`
  - rungs: [0, 2, 3]
  - _evidence:_ MASR+MAFR presentes — registration full

### `servo_on_off_cycle` — Servo On/Off Cycle (MSO+MSF)

_Ciclo de habilitación/deshabilitación del servo. MSO (Motion Servo On) cierra el loop de control; MSF (Motion Servo Off) lo abre. Su co-ocurrencia en una misma routine indica un manager de estado del eje (init + shutdown bajo condiciones de fault o E-stop)._

- **AOIs/Axis_ObjectCIP/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MAFR → MASR → MAS`
  - rungs: [0, 1, 2, 3]
  - _evidence:_ MSO+MSF presentes — manager de estado
- **AOIs/Axis_Object_Sercos/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MAFR → MASR → MAS`
  - rungs: [0, 1, 2, 3]
  - _evidence:_ MSO+MSF presentes — manager de estado
- **AOIs/Servo_Manager/Routines/Logic** axis=`Asse` conf=1.00
  - ops: `MASR → MAFR → MSO → MSF`
  - rungs: [0, 2, 3]
  - _evidence:_ MSO+MSF presentes — manager de estado

### `axis_lifecycle` — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})

_Routine que orquesta el ciclo completo de un eje: homing (MAH), movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas ops aparecen en la misma routine, suele ser el axis manager / AOI tipo AxisBlock que centraliza todos los comandos de un eje._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAM → MAM`...
  - rungs: [2, 3, 4, 5, 6, 7, 8, 9]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **AOIs/AxisBlockVM/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [3, 5, 7, 8, 9, 11, 13, 14]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=0.85
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **Programs/Axis/Routines/R001_A_Corte_AQL** axis=`S04N74_CORTE_APLIC_AQL` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **Programs/Axis/Routines/R001_B_Estampador_AQL** axis=`S04N75_RODILLO_ESTAMPADOR` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **Programs/Axis/Routines/R002_Corte_WB** axis=`S04N79_UNIDAD_CORTE_WB` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']

### `splice_transition` — Splice Transition (MAJ→MAS→MAJ)

_Transición controlada típica de empalme: el eje arranca con MAJ (jog libre, velocidad inicial), se detiene con MAS al evento de splice, y vuelve a arrancar con MAJ (o se sincroniza con MAG) a la velocidad final del rollo nuevo. Patrón canónico Diatec._

- **AOIs/AxisBlock/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAM → MAM`...
  - rungs: [2, 3, 4, 5, 6, 7, 8, 9]
  - _evidence:_ transición parcial MAJ→MAG
- **AOIs/AxisBlockVM/Routines/Logic** axis=`PhysicalAx` conf=0.85
  - ops: `MAJ → MAM → MAG → MAG → MAG → MAJ → MAG → MAG → MAG → MAM`...
  - rungs: [3, 5, 7, 8, 9, 11, 13, 14]
  - _evidence:_ transición parcial MAJ→MAG
- **AOIs/DancerCorAndNewRadiusComputation/Routines/Logic** axis=`Ax` conf=0.85
  - ops: `MAS → MAM → MAJ → MAS`
  - rungs: [14, 15, 20, 21]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/Dancer_Tension_Servo/Routines/Logic** axis=`Ref_ServoAxis` conf=0.85
  - ops: `MAJ → MAS → MAH`
  - rungs: [1, 2]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/Unwinder/Routines/Logic** axis=`AxA` conf=0.85
  - ops: `MAG → MAG → MAJ → MAS → MAS`
  - rungs: [36, 41, 44, 45]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/Unwinder/Routines/Logic** axis=`AxB` conf=0.85
  - ops: `MAG → MAG → MAJ → MAS → MAS`
  - rungs: [38, 42, 46, 47]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/VirtualAxisBlock/Routines/Logic** axis=`VirtualAx` conf=0.85
  - ops: `MAJ → MAG → MAG → MAG → MAG → MAG → MAM → MAH → MAM → MAS`
  - rungs: [2, 3, 4, 5, 6, 7, 11, 12]
  - _evidence:_ transición parcial MAJ→MAG
- **Programs/Axis/Routines/R001_A_Corte_AQL** axis=`S04N74_CORTE_APLIC_AQL` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ transición parcial MAJ→MAS
- **Programs/Axis/Routines/R001_B_Estampador_AQL** axis=`S04N75_RODILLO_ESTAMPADOR` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ transición parcial MAJ→MAS
- **Programs/Axis/Routines/R002_Corte_WB** axis=`S04N79_UNIDAD_CORTE_WB` conf=0.85
  - ops: `MAJ → MAS → MAH → MAM`
  - rungs: [3, 6]
  - _evidence:_ transición parcial MAJ→MAS
- **Programs/Debo_Tela/Routines/R08_TNT_Unwinder** axis=`S04N77_DEBO_TNT_IZQUIERDO` conf=0.85
  - ops: `MAJ → MAG → MAJ → MAS`
  - rungs: [4]
  - _evidence:_ transición parcial MAJ→MAG
- **Programs/Debo_Tela/Routines/R08_TNT_Unwinder** axis=`S04N78_DEBO_TNT_DERECHO` conf=0.85
  - ops: `MAJ → MAG → MAJ → MAS`
  - rungs: [6]
  - _evidence:_ transición parcial MAJ→MAG

### `axis_lifecycle` — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})

_Routine que orquesta el ciclo completo de un eje: homing (MAH), movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas ops aparecen en la misma routine, suele ser el axis manager / AOI tipo AxisBlock que centraliza todos los comandos de un eje._

- **AOIs/AxisConsumeCIPSync_AOI/Routines/Logic** axis=`Out_Axis_Consumed` conf=0.80
  - ops: `MAS → MAJ → MAJ → MAM → MAJ`
  - rungs: [15, 84, 85, 113, 172]
  - _evidence:_ 3/4 lifecycle ops: ['MAJ', 'MAM', 'MAS']
- **AOIs/DancerCorAndNewRadiusComputation/Routines/Logic** axis=`Ax` conf=0.80
  - ops: `MAS → MAM → MAJ → MAS`
  - rungs: [14, 15, 20, 21]
  - _evidence:_ 3/4 lifecycle ops: ['MAJ', 'MAM', 'MAS']
- **AOIs/Dancer_Tension_Servo/Routines/Logic** axis=`Ref_ServoAxis` conf=0.80
  - ops: `MAJ → MAS → MAH`
  - rungs: [1, 2]
  - _evidence:_ 3/4 lifecycle ops: ['MAH', 'MAJ', 'MAS']

### `gear_chain` — Gear Chain (Master-Slave acoplamiento)

_Eje slave acoplado a master vía MAG (Motion Axis Gear). Implementa sincronización a ratio constante. Si aparece MAG→MAG en la misma routine, indica re-engranaje dinámico (cambio de ratio en runtime, típico en líneas con velocidad variable)._

- **Programs/Debo_Tela/Routines/R08_TNT_Unwinder** axis=`S04N77_DEBO_TNT_IZQUIERDO` conf=0.70
  - ops: `MAJ → MAG → MAJ → MAS`
  - rungs: [4]
  - _evidence:_ 1 MAG — gear ratio constante
- **Programs/Debo_Tela/Routines/R08_TNT_Unwinder** axis=`S04N78_DEBO_TNT_DERECHO` conf=0.70
  - ops: `MAJ → MAG → MAJ → MAS`
  - rungs: [6]
  - _evidence:_ 1 MAG — gear ratio constante
