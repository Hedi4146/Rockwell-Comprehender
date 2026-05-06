# Program Inference — CPU1

**Programs analizados:** 4

| Program | Role | Conf | Evidence |
|---------|------|-----:|----------|
| `Axis` | `sequence_logic` | 0.50 | name 'Axis' relacionado con motion; 49 bit logic ops, sin motion/safety; 23 refs a tags Hmi* |
| `MainProgram` | `main_dispatcher` | 0.30 | name 'MainProgram' es Main / dispatcher; 1 motion ops (pocos); 41 refs a tags Hmi* |
| `ReadPar` | `data_init` | 0.30 | name 'ReadPar' inicia con read/init/setup |
| `Reject` | `reject_control` | 0.40 | name 'Reject' inicia con reject/cull |

## Detalle por program

### `Axis` — sequence_logic (conf 0.50)

**Descripción del rol:** Program de secuencia — lógica de estados, alarmas, condicionales (XIC/XIO/OTE/JSR)

**Evidencia:**
- name 'Axis' relacionado con motion
- 49 bit logic ops, sin motion/safety
- 23 refs a tags Hmi*

### `MainProgram` — main_dispatcher (conf 0.30)

**Descripción del rol:** Program principal — JSR a múltiples routines, orquesta ciclo de scan

**Evidencia:**
- name 'MainProgram' es Main / dispatcher
- 1 motion ops (pocos)
- 41 refs a tags Hmi*

### `ReadPar` — data_init (conf 0.30)

**Descripción del rol:** Program de inicialización — carga setpoints, config inicial al arranque

**Evidencia:**
- name 'ReadPar' inicia con read/init/setup

### `Reject` — reject_control (conf 0.40)

**Descripción del rol:** Program de rechazo — reject motors, cull functions

**Evidencia:**
- name 'Reject' inicia con reject/cull
