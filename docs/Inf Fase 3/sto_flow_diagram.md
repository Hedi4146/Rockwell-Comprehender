# Flujo de Control STO - Kinetix 5700
## SafetyProgram - CPPIM_BD800_1

---

## Diagrama de Flujo del Circuito STO (Ejemplo: UWM01)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NIVEL 1: ENTRADAS DE CAMPO                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐         │
│   │   E-STOP PB's    │    │  SAFETY GATES    │    │    LIFELINES     │         │
│   │  (Dual Channel)  │    │  (Dual Channel)  │    │  (Dual Channel)  │         │
│   │                  │    │                  │    │                  │         │
│   │  PB1...PB9       │    │  UWM01 Gate      │    │  Drive Side      │         │
│   │  MCU, MOP, etc.  │    │  CH1 + CH2       │    │  Operator Side   │         │
│   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘         │
│            │                       │                       │                   │
│            ▼                       ▼                       ▼                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 2: PROCESAMIENTO DE ENTRADAS                           │
│                         (Rutina: S01_E_Stop)                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Cada entrada usa instrucción DCI_STOP (Dual Channel Input Stop):             │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │  DCS_PB1_EStop (tipo DCI_STOP)                                      │       │
│   │  ├── Input CH1 ──────┐                                              │       │
│   │  ├── Input CH2 ──────┼──► Discrepancy Check ──► InputStatus         │       │
│   │  ├── FeedbackReactionTime: 1000ms                                   │       │
│   │  └── FaultCode / DiagnosticCode                                     │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                     │                                           │
│                                     ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │              CONSOLIDACIÓN DE E-STOPS                               │       │
│   │                                                                     │       │
│   │    DCS_PB1_EStop.InputStatus ─────┐                                 │       │
│   │    DCS_PB2_EStop.InputStatus ─────┤                                 │       │
│   │    DCS_MCU_EStop.InputStatus ─────┼──► AND ──► All_Estop_Ready     │       │
│   │    DCS_MOP_EStop.InputStatus ─────┤           (BOOL)                │       │
│   │    ... (25 circuitos)        ─────┘                                 │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 3: PROCESAMIENTO DE GUARDAS                            │
│                         (Rutina: S02_SafetyDoor)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Cada guarda usa instrucción DCI_STOP_TEST_LOCK:                               │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │  DCSTL_SafetyGate_DR_UWM01 (tipo DCI_STOP_TEST_LOCK)                │       │
│   │  ├── Input CH1: UWM01_SafetySwitch_CH1                              │       │
│   │  ├── Input CH2: UWM01_SafetySwitch_CH2                              │       │
│   │  ├── Lock Output: Solenoid control                                  │       │
│   │  ├── Test Input: Periodic testing                                   │       │
│   │  └── Output: DCSTL_InputStatus_SafetyGate_DR_UWM01                  │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                     │                                           │
│                                     ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │              CONSOLIDACIÓN DE GUARDAS POR ZONA                      │       │
│   │                                                                     │       │
│   │    DCSTL_SafetyGate_DR_UWM01 ──┐                                    │       │
│   │    DCSTL_SafetyGate_OP_UWM01 ──┼──► SafetyGate_RDY_UWM01           │       │
│   │    Frame conditions        ────┘                                    │       │
│   │                                                                     │       │
│   │    + AllSafetyGuard_RDY_DRSide (global drive side)                 │       │
│   │    + AllSafetyGuard_RDY_OPSide (global operator side)              │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 4: CONTROL STO DE SERVO DRIVES                         │
│                         (Rutina: S03_DriveSTOControl)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Instrucción CONFIGURABLE_ROUT (CROUT) para cada grupo de servos:              │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │  CROUT_UWM01_ServoGroup_STO                                         │       │
│   │  ═══════════════════════════                                        │       │
│   │                                                                     │       │
│   │  ENTRADAS:                                                          │       │
│   │  ├── EnableIn ◄────── (All_Estop_Ready AND SafetyGate_RDY_UWM01)   │       │
│   │  ├── Actuate ◄─────── Comando desde programa estándar               │       │
│   │  ├── FeedbackType ─── 1 = Dual Channel feedback                     │       │
│   │  ├── Feedback1 ◄───── UWM01_ServoGroup_STO_Feedback_ChA             │       │
│   │  ├── Feedback2 ◄───── UWM01_ServoGroup_STO_Feedback_ChB             │       │
│   │  └── Reset ◄───────── UWM01_Reset (manual reset required)           │       │
│   │                                                                     │       │
│   │  PARÁMETROS:                                                        │       │
│   │  └── FeedbackReactionTime: 1000ms (tiempo para verificar feedback)  │       │
│   │                                                                     │       │
│   │  SALIDAS:                                                           │       │
│   │  ├── EnableOut ──────► Condición para siguiente bloque              │       │
│   │  ├── O1 ─────────────► UWM01_ServoGroup_STO_Enable                  │       │
│   │  ├── O2 ─────────────► (Redundante, mismo destino)                  │       │
│   │  ├── InputStatus ────► UWM01_ServoGroup_InputStatus_OK              │       │
│   │  ├── OutputStatus ───► UWM01_ServoGroup_OutputStatus_OK             │       │
│   │  ├── FP (Fault Present)                                             │       │
│   │  ├── FaultCode                                                      │       │
│   │  └── DiagnosticCode                                                 │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 5: COMUNICACIÓN CIP SAFETY AL DRIVE                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   La señal STO_Enable viaja por CIP Safety a cada Kinetix 5700:                 │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │                                                                     │       │
│   │   Safety Controller ──── EtherNet/IP (CIP Safety) ──── Kinetix 5700 │       │
│   │   (GuardLogix/                                         (Drive)      │       │
│   │    Compact GuardLogix)                                              │       │
│   │                                                                     │       │
│   │   Módulos de Safety en este proyecto:                               │       │
│   │   • SAS_UWM01, SAS_UWM01_1, SAS_UWM01_2, SAS_UWM01_3                │       │
│   │   • SAS_UWM02, SAS_UWM02_1, SAS_UWM02_2, SAS_UWM02_3                │       │
│   │   • ... (y demás zonas)                                             │       │
│   │                                                                     │       │
│   │   Servo Drives en UWM01:                                            │       │
│   │   • UWM01_SD47, UWM01_SD48, UWM01_SD49                              │       │
│   │                                                                     │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 6: RESPUESTA DEL DRIVE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐       │
│   │                      KINETIX 5700 DRIVE                             │       │
│   │                                                                     │       │
│   │   Recibe: STO_Enable = 0 (Safe Torque Off solicitado)               │       │
│   │                                                                     │       │
│   │   Acción interna del drive:                                         │       │
│   │   ┌───────────────────────────────────────────────────────────┐     │       │
│   │   │  1. Desactiva pulsos PWM a los IGBTs                      │     │       │
│   │   │  2. Motor pierde torque (coast to stop)                   │     │       │
│   │   │  3. Activa feedback STO confirmando estado seguro         │     │       │
│   │   └───────────────────────────────────────────────────────────┘     │       │
│   │                                                                     │       │
│   │   Envía feedback dual:                                              │       │
│   │   ├── STO_Feedback_ChA ──► Safety Controller                        │       │
│   │   └── STO_Feedback_ChB ──► Safety Controller                        │       │
│   │                                                                     │       │
│   └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

```

---

## Secuencia de Activación STO (Escenario: E-Stop presionado)

```
TIEMPO ──────────────────────────────────────────────────────────────────────►

t=0ms     Operador presiona E-Stop PB1
          │
          ▼
t=1ms     DCS_PB1_EStop detecta apertura de CH1 y CH2
          │
          ▼
t=2ms     DCS_PB1_EStop.InputStatus = 0 (NO OK)
          │
          ▼
t=3ms     All_Estop_Ready = 0 (cascada AND falla)
          │
          ▼
t=4ms     CROUT_UWM01_ServoGroup_STO.EnableIn = 0
          │
          ▼
t=5ms     CROUT_UWM01_ServoGroup_STO procesa:
          ├── O1 = 0 (desactiva STO enable)
          └── O2 = 0 (redundante)
          │
          ▼
t=6ms     UWM01_ServoGroup_STO_Enable = 0
          │
          ▼
t=7ms     Señal viaja por CIP Safety a drives UWM01_SD47/48/49
          │
          ▼
t=10-15ms Kinetix 5700 ejecuta STO interno:
          ├── Corta pulsos PWM
          ├── Motor pierde torque
          └── Feedback_ChA/ChB = 1 (confirmando STO activo)
          │
          ▼
t=20ms    Safety Controller recibe feedback
          │
          ▼
t=1000ms  FeedbackReactionTime expira
          └── Si feedback no llegó ─► FaultCode activado

```

---

## Secuencia de Rearme (Reset)

```
TIEMPO ──────────────────────────────────────────────────────────────────────►

t=0       Operador libera E-Stop (gira botón)
          │
          ▼
t=1ms     DCS_PB1_EStop detecta cierre de CH1 y CH2
          │
          ▼
t=2ms     DCS_PB1_EStop.InputStatus = 1 (OK)
          │
          ▼
t=3ms     All_Estop_Ready = 1 (si todos los E-Stops OK)
          │
          ▼
          *** SISTEMA EN ESPERA DE RESET MANUAL ***
          │
          ▼
t=X       Operador presiona botón RESET (UWM01_Reset = 1)
          │
          ▼
t=X+1ms   CROUT_UWM01_ServoGroup_STO.Reset = 1
          │
          ▼
t=X+2ms   CROUT procesa reset:
          ├── Verifica EnableIn = 1 (condiciones OK)
          ├── Verifica Feedback1 y Feedback2 consistentes
          └── Si todo OK ─► O1 = 1, O2 = 1
          │
          ▼
t=X+3ms   UWM01_ServoGroup_STO_Enable = 1
          │
          ▼
t=X+4ms   Señal viaja a drives por CIP Safety
          │
          ▼
t=X+10ms  Kinetix 5700 libera STO:
          ├── Permite PWM (cuando programa estándar lo solicite)
          └── Feedback_ChA/ChB reflejan nuevo estado

```

---

## Resumen de Tags del Circuito UWM01

| Tag | Tipo | Función |
|-----|------|---------|
| `UWM01_SafetySwitch_CH1` | BOOL | Entrada física canal A de guarda |
| `UWM01_SafetySwitch_CH2` | BOOL | Entrada física canal B de guarda |
| `DCSTL_SafetyGate_DR_UWM01` | DCI_STOP_TEST_LOCK | Procesamiento de guarda con bloqueo |
| `SafetyGate_RDY_UWM01` | BOOL | Estado consolidado de guardas zona UWM01 |
| `All_Estop_Ready` | BOOL | Estado consolidado de todos los E-Stops |
| `CROUT_UWM01_ServoGroup_STO` | CONFIGURABLE_ROUT | Instrucción de salida configurable |
| `UWM01_ServoGroup_STO_Enable` | BOOL | **Comando STO al drive** |
| `UWM01_ServoGroup_STO_Feedback_ChA` | BOOL | Retroalimentación canal A desde drive |
| `UWM01_ServoGroup_STO_Feedback_ChB` | BOOL | Retroalimentación canal B desde drive |
| `UWM01_ServoGroup_InputStatus_OK` | BOOL | Estado de entradas OK |
| `UWM01_ServoGroup_OutputStatus_OK` | BOOL | Estado de salidas OK |
| `UWM01_Reset` | BOOL | Comando de reset manual |

---

## Arquitectura de Safety por Zonas

```
                    ┌───────────────────────────────────────┐
                    │         SAFETY CONTROLLER             │
                    │      (GuardLogix/Compact GL)          │
                    └───────────────────┬───────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           ▼                            ▼                            ▼
    ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
    │   ZONA MDP   │            │  ZONA UWM    │            │  ZONA AUX    │
    │  (Paneles)   │            │ (Unwinders)  │            │ (Auxiliar)   │
    └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
           │                           │                           │
    ┌──────┴──────┐             ┌──────┴──────┐                    │
    │             │             │             │                    │
    ▼             ▼             ▼             ▼                    ▼
┌───────┐   ┌───────┐     ┌───────┐    ┌───────┐           ┌───────────┐
│MDP001 │   │MDP007 │     │ UWM01 │    │ UWM05 │           │  STS_MCU  │
│SD01-06│   │SD41-45│     │SD47-49│    │SD73-75│           │  STS_MOP  │
└───────┘   └───────┘     └───────┘    └───────┘           └───────────┘
  6 ejes      5 ejes       3 ejes       3 ejes

Total: 63 ejes servo con STO integrado
```

---

## Notas Importantes

1. **Redundancia Dual Canal**: Todas las entradas y salidas de seguridad usan verificación de canal dual (CH1/CH2 o ChA/ChB)

2. **FeedbackReactionTime = 1000ms**: El sistema espera hasta 1 segundo para recibir confirmación de los drives

3. **Reset Manual Obligatorio**: Después de cualquier evento de seguridad, se requiere intervención humana para rearmar

4. **CIP Safety sobre EtherNet/IP**: Comunicación de seguridad certificada entre el controlador y los Kinetix 5700

5. **Las rutinas están encriptadas** por Amantrini Automação (EncryptionConfig="9"), pero la estructura de tags permite inferir el flujo lógico

