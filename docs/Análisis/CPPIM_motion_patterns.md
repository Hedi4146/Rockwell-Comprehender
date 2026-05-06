# Motion Patterns — CPPIM_BD800_1

**Total matches:** 45 (7 patterns activados)

## Por pattern (count)

- `registration_full` (17) — Registration Full (MASR+MAFR)
- `homing_sequence` (8) — Homing Sequence
- `gear_chain` (7) — Gear Chain (Master-Slave acoplamiento)
- `splice_transition` (5) — Splice Transition (MAJ→MAS→MAJ)
- `servo_on_off_cycle` (4) — Servo On/Off Cycle (MSO+MSF)
- `axis_lifecycle` (3) — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})
- `output_cam_pair` (1) — Output Cam Pair (MAOC+MDOC)

## Detalle

### `homing_sequence` — Homing Sequence

_Secuencia de homing del eje. MAH (Motion Axis Home) inicia el comando de búsqueda de referencia. Si aparece junto a MAJ/MAS, indica un manager completo con jog manual de aproximación + homing automático._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ MAH presente, +2 co-ops manager
- **AOIs/Servo_Homming/Routines/Logic** axis=`Axis` conf=1.00
  - ops: `MAJ → MAM → MAS → MAS → MAS → MAS → MAM → MAH`
  - rungs: [2, 3, 6, 7, 8, 10]
  - _evidence:_ MAH presente, +2 co-ops manager

### `output_cam_pair` — Output Cam Pair (MAOC+MDOC)

_Par activate/deactivate del Output Cam. MAOC (Motion Arm Output Cam) habilita la generación de pulsos de salida coordinados con la posición del eje; MDOC los desarma. Su co-ocurrencia indica control encoder de glue gun, label, knife, o similares._

- **Programs/Reject/Routines/CamSwitch** axis=`SD45A_Encoder_motor` conf=1.00
  - ops: `MAOC → MAOC → MDOC → MDOC`
  - rungs: [0, 1, 2]
  - _evidence:_ MAOC+MDOC presentes — output cam pair

### `registration_full` — Registration Full (MASR+MAFR)

_Suite completa de registration. MASR (Motion Arm Single Registration) arma una captura puntual; MAFR (Motion Arm Full Registration) arma captura continua. Su co-ocurrencia indica lógica de tracking de marca de registro (mark-to-mark sync)._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ MASR+MAFR presentes — registration full
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderA` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [92, 93, 95, 97, 98, 101, 102]
  - _evidence:_ MASR+MAFR presentes — registration full
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderB` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [108, 109, 111, 113, 114, 117, 118]
  - _evidence:_ MASR+MAFR presentes — registration full
- **AOIs/DancerControl/Routines/Logic** axis=`Axis` conf=1.00
  - ops: `MSO → MSF → MAJ → MAS → MAFR → MASR`
  - rungs: [3, 4, 11, 12, 15]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP001` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP002` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP003` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP004` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP005` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP006` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_MDP007` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM01` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM02` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM031` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM032` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM04` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full
- **Programs/MainProgram/Routines/ServoControl_ST** axis=`Converter1_UWM05` conf=1.00
  - ops: `MAFR → MASR`
  - rungs: [0]
  - _evidence:_ MASR+MAFR presentes — registration full

### `servo_on_off_cycle` — Servo On/Off Cycle (MSO+MSF)

_Ciclo de habilitación/deshabilitación del servo. MSO (Motion Servo On) cierra el loop de control; MSF (Motion Servo Off) lo abre. Su co-ocurrencia en una misma routine indica un manager de estado del eje (init + shutdown bajo condiciones de fault o E-stop)._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ MSO+MSF presentes — manager de estado
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderA` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [92, 93, 95, 97, 98, 101, 102]
  - _evidence:_ MSO+MSF presentes — manager de estado
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderB` conf=1.00
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [108, 109, 111, 113, 114, 117, 118]
  - _evidence:_ MSO+MSF presentes — manager de estado
- **AOIs/DancerControl/Routines/Logic** axis=`Axis` conf=1.00
  - ops: `MSO → MSF → MAJ → MAS → MAFR → MASR`
  - rungs: [3, 4, 11, 12, 15]
  - _evidence:_ MSO+MSF presentes — manager de estado

### `axis_lifecycle` — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})

_Routine que orquesta el ciclo completo de un eje: homing (MAH), movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas ops aparecen en la misma routine, suele ser el axis manager / AOI tipo AxisBlock que centraliza todos los comandos de un eje._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=0.85
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']
- **AOIs/Servo_Homming/Routines/Logic** axis=`Axis` conf=0.85
  - ops: `MAJ → MAM → MAS → MAS → MAS → MAS → MAM → MAH`
  - rungs: [2, 3, 6, 7, 8, 10]
  - _evidence:_ 4/4 lifecycle ops: ['MAH', 'MAJ', 'MAM', 'MAS']

### `splice_transition` — Splice Transition (MAJ→MAS→MAJ)

_Transición controlada típica de empalme: el eje arranca con MAJ (jog libre, velocidad inicial), se detiene con MAS al evento de splice, y vuelve a arrancar con MAJ (o se sincroniza con MAG) a la velocidad final del rollo nuevo. Patrón canónico Diatec._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=0.85
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderA` conf=0.85
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [92, 93, 95, 97, 98, 101, 102]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderB` conf=0.85
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [108, 109, 111, 113, 114, 117, 118]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/DancerControl/Routines/Logic** axis=`Axis` conf=0.85
  - ops: `MSO → MSF → MAJ → MAS → MAFR → MASR`
  - rungs: [3, 4, 11, 12, 15]
  - _evidence:_ transición parcial MAJ→MAS
- **AOIs/PhaseAdjustment/Routines/Logic** axis=`Axis` conf=0.85
  - ops: `MAJ → MAS`
  - rungs: [0, 1]
  - _evidence:_ transición parcial MAJ→MAS

### `axis_lifecycle` — Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})

_Routine que orquesta el ciclo completo de un eje: homing (MAH), movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas ops aparecen en la misma routine, suele ser el axis manager / AOI tipo AxisBlock que centraliza todos los comandos de un eje._

- **AOIs/Axis_MasterAV/Routines/Logic** axis=`Ref_Axis_AV` conf=0.80
  - ops: `MASR → MAJ → MCD → MAM → MAS`
  - rungs: [2, 4, 6, 7]
  - _evidence:_ 3/4 lifecycle ops: ['MAJ', 'MAM', 'MAS']

### `homing_sequence` — Homing Sequence

_Secuencia de homing del eje. MAH (Motion Axis Home) inicia el comando de búsqueda de referencia. Si aparece junto a MAJ/MAS, indica un manager completo con jog manual de aproximación + homing automático._

- **Programs/MainProgram/Routines/PhaseControl** axis=`SD49A_Tissue_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)
- **Programs/MainProgram/Routines/PhaseControl** axis=`SD49B_Backsheet_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)
- **Programs/MainProgram/Routines/PhaseControl** axis=`SD53A_PE_film_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)
- **Programs/MainProgram/Routines/PhaseControl** axis=`SD70A_AQL_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)
- **Programs/MainProgram/Routines/PhaseControl** axis=`SD75A_Top_sheet_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)
- **Programs/MainProgram/Routines/PhaseControl** axis=`SD75B_Cuff_tension` conf=0.80
  - ops: `MAH`
  - rungs: [55]
  - _evidence:_ MAH solo (homing puro)

### `gear_chain` — Gear Chain (Master-Slave acoplamiento)

_Eje slave acoplado a master vía MAG (Motion Axis Gear). Implementa sincronización a ratio constante. Si aparece MAG→MAG en la misma routine, indica re-engranaje dinámico (cambio de ratio en runtime, típico en líneas con velocidad variable)._

- **AOIs/AOI_AxisControl_CIP/Routines/Logic** axis=`Ref_Axis_CD` conf=0.70
  - ops: `MSO → MSF → MASR → MAFR → MAH → MAS → MAS → MAS → MAJ → MAS`...
  - rungs: [1, 2, 4, 7, 15, 16, 19, 23]
  - _evidence:_ 1 MAG — gear ratio constante
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderA` conf=0.70
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [92, 93, 95, 97, 98, 101, 102]
  - _evidence:_ 1 MAG — gear ratio constante
- **AOIs/AOI_UnwinderControl/Routines/Logic** axis=`UnwinderB` conf=0.70
  - ops: `MSO → MSF → MASR → MAFR → MAG → MAS → MAJ → MAS`
  - rungs: [108, 109, 111, 113, 114, 117, 118]
  - _evidence:_ 1 MAG — gear ratio constante
- **Programs/MainProgram/Routines/VirtualAutoControl** axis=`Virtual_BackEar` conf=0.70
  - ops: `MAG → MAS`
  - rungs: [11, 12]
  - _evidence:_ 1 MAG — gear ratio constante
- **Programs/MainProgram/Routines/VirtualAutoControl** axis=`Virtual_Backear_cutunit` conf=0.70
  - ops: `MAPC → MAG → MAS`
  - rungs: [13, 14]
  - _evidence:_ 1 MAG — gear ratio constante
- **Programs/MainProgram/Routines/VirtualAutoControl** axis=`Virtual_FrontEar` conf=0.70
  - ops: `MAG → MAS`
  - rungs: [18, 19]
  - _evidence:_ 1 MAG — gear ratio constante
- **Programs/MainProgram/Routines/VirtualAutoControl** axis=`Virtual_Waistband` conf=0.70
  - ops: `MAG → MAS`
  - rungs: [21, 22]
  - _evidence:_ 1 MAG — gear ratio constante
