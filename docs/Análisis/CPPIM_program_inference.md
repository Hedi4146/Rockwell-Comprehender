# Program Inference — CPPIM_BD800_1

**Programs analizados:** 7

| Program | Role | Conf | Evidence |
|---------|------|-----:|----------|
| `AltaBluePlusControl` | `sequence_logic` | 0.50 | 486 bit logic ops, sin motion/safety; 11 JSR — alto dispatch |
| `Fault` | `fault_management` | 0.40 | name 'Fault' relacionado con faults/alarmas; 1 motion ops (pocos) |
| `MainProgram` | `motion_control` | 0.50 | name 'MainProgram' es Main / dispatcher; 41 motion ops |
| `Reject` | `reject_control` | 0.40 | name 'Reject' inicia con reject/cull; 2 motion ops (pocos) |
| `SafetyProgram` | `safety_handler` | 0.90 | name 'SafetyProgram' contiene 'safety'; scheduled by SafetyTask SafetyTask |
| `TemperatureControl` | `diagnostic` | 0.60 | name 'TemperatureControl' relacionado con diagnóstico; scheduled by Temperature task |
| `Unwinder` | `sequence_logic` | 0.50 | name 'Unwinder' relacionado con motion; 111 bit logic ops, sin motion/safety |

## Detalle por program

### `AltaBluePlusControl` — sequence_logic (conf 0.50)

**Descripción del rol:** Program de secuencia — lógica de estados, alarmas, condicionales (XIC/XIO/OTE/JSR)

**Evidencia:**
- 486 bit logic ops, sin motion/safety
- 11 JSR — alto dispatch

### `Fault` — fault_management (conf 0.40)

**Descripción del rol:** Program de gestión de faults — concentra alarmas, decoding y latching

**Evidencia:**
- name 'Fault' relacionado con faults/alarmas
- 1 motion ops (pocos)

### `MainProgram` — motion_control (conf 0.50)

**Descripción del rol:** Program de motion — comanda ejes (MAJ/MAS/MAH/MAM/MAG)

**Evidencia:**
- name 'MainProgram' es Main / dispatcher
- 41 motion ops

### `Reject` — reject_control (conf 0.40)

**Descripción del rol:** Program de rechazo — reject motors, cull functions

**Evidencia:**
- name 'Reject' inicia con reject/cull
- 2 motion ops (pocos)

### `SafetyProgram` — safety_handler (conf 0.90)

**Descripción del rol:** Program de safety — implementa GuardLogix dual-channel, E-stop, CROUT/DCI_*

**Evidencia:**
- name 'SafetyProgram' contiene 'safety'
- scheduled by SafetyTask SafetyTask

### `TemperatureControl` — diagnostic (conf 0.60)

**Descripción del rol:** Program diagnóstico — temperature, status, monitor

**Evidencia:**
- name 'TemperatureControl' relacionado con diagnóstico
- scheduled by Temperature task

### `Unwinder` — sequence_logic (conf 0.50)

**Descripción del rol:** Program de secuencia — lógica de estados, alarmas, condicionales (XIC/XIO/OTE/JSR)

**Evidencia:**
- name 'Unwinder' relacionado con motion
- 111 bit logic ops, sin motion/safety
