# Program Inference — CPU_AQL_M2

**Programs analizados:** 7

| Program | Role | Conf | Evidence |
|---------|------|-----:|----------|
| `Axis` | `motion_control` | 0.80 | name 'Axis' relacionado con motion; 12 motion ops; 24 refs a tags Hmi* |
| `ConsumeAxisAOI` | `motion_control` | 0.30 | name 'ConsumeAxisAOI' relacionado con motion |
| `Debo_Tela` | `motion_control` | 0.50 | 8 motion ops; 12 refs a tags Hmi* |
| `MainProgram` | `main_dispatcher` | 0.30 | name 'MainProgram' es Main / dispatcher; 1 motion ops (pocos); 281 refs a tags Hmi* |
| `ReadPar` | `data_init` | 0.30 | name 'ReadPar' inicia con read/init/setup |
| `Reject` | `sequence_logic` | 0.50 | name 'Reject' inicia con reject/cull; 210 bit logic ops, sin motion/safety |
| `Reject1` | `reject_control` | 0.40 | name 'Reject1' inicia con reject/cull |

## Detalle por program

### `Axis` — motion_control (conf 0.80)

**Descripción del rol:** Program de motion — comanda ejes (MAJ/MAS/MAH/MAM/MAG)

**Evidencia:**
- name 'Axis' relacionado con motion
- 12 motion ops
- 24 refs a tags Hmi*

### `ConsumeAxisAOI` — motion_control (conf 0.30)

**Descripción del rol:** Program de motion — comanda ejes (MAJ/MAS/MAH/MAM/MAG)

**Evidencia:**
- name 'ConsumeAxisAOI' relacionado con motion

### `Debo_Tela` — motion_control (conf 0.50)

**Descripción del rol:** Program de motion — comanda ejes (MAJ/MAS/MAH/MAM/MAG)

**Evidencia:**
- 8 motion ops
- 12 refs a tags Hmi*

### `MainProgram` — main_dispatcher (conf 0.30)

**Descripción del rol:** Program principal — JSR a múltiples routines, orquesta ciclo de scan

**Evidencia:**
- name 'MainProgram' es Main / dispatcher
- 1 motion ops (pocos)
- 281 refs a tags Hmi*

### `ReadPar` — data_init (conf 0.30)

**Descripción del rol:** Program de inicialización — carga setpoints, config inicial al arranque

**Evidencia:**
- name 'ReadPar' inicia con read/init/setup

### `Reject` — sequence_logic (conf 0.50)

**Descripción del rol:** Program de secuencia — lógica de estados, alarmas, condicionales (XIC/XIO/OTE/JSR)

**Evidencia:**
- name 'Reject' inicia con reject/cull
- 210 bit logic ops, sin motion/safety

### `Reject1` — reject_control (conf 0.40)

**Descripción del rol:** Program de rechazo — reject motors, cull functions

**Evidencia:**
- name 'Reject1' inicia con reject/cull
