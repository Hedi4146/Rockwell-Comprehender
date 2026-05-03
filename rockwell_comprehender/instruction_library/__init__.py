"""Instruction Library — datos curados de instrucciones Rockwell.

**Capa D de v0.3** (DT-009). Esta capa NO extrae datos del L5X; almacena
**conocimiento de dominio curado** sobre instrucciones de Studio 5000:
pines (input/output/inout) con descripción semántica, atributos de
configuración, modos de fallo, referencias a documentación oficial.

El catálogo es **mínimo viable** — crece incrementalmente cuando aparece
caso real (DT-010, validación empírica antes de comprometer).

Uso:
    from rockwell_comprehender.instruction_library import (
        get_instruction_metadata, list_instructions
    )
    meta = get_instruction_metadata("CROUT")
    print(meta.summary)
    for pin in meta.pins:
        print(f"  {pin.name} [{pin.direction}]: {pin.description}")

    # O vía Project:
    project.get_instruction_metadata("CROUT")

Catálogo v0.3.x (14 instrucciones):
- Safety: CROUT, DCI_STOP, DCI_STOP_TEST_LOCK
- Motion: MAJ, MAG, MAS, MAH, MAOC, MAM, MSO, MSF, MAFR, MASR, MAPC

Fuentes:
- Rockwell pub 1756-RM095 (GuardLogix Safety Instructions)
- Rockwell pub MOTION-RM002 (Logix 5000 Motion Instructions)
- Rockwell pub 1756-RM003 (General Instructions)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class InstructionPin:
    """Un pin (input/output/inout) o atributo de configuración de una instrucción."""

    name: str
    direction: str           # "input" | "output" | "both" | "config"
    datatype: str            # "BOOL" | "REAL" | "DINT" | "AXIS_*" | "MOTION_INSTRUCTION" | "ENUM"
    description: str = ""
    required: bool = True


@dataclass
class InstructionFault:
    """Modo de fallo conocido de una instrucción."""

    name: str                # "Timeout" | "Discrepancy" | etc.
    description: str
    fault_code: Optional[int] = None


@dataclass
class InstructionMetadata:
    """Metadata curada de una instrucción Rockwell."""

    name: str                                          # "CROUT", "MAJ"
    full_name: str                                     # "Configurable Redundant Output"
    category: str                                      # "safety" | "motion" | "logic"
    vendor: str = "Rockwell Automation"
    summary: str = ""
    pins: list[InstructionPin] = field(default_factory=list)
    config_attributes: list[InstructionPin] = field(default_factory=list)
    fault_modes: list[InstructionFault] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    notes: str = ""


# ──────────────────────────────────────────────────────────────────────
# Catálogo curado
# ──────────────────────────────────────────────────────────────────────


_CROUT = InstructionMetadata(
    name="CROUT",
    full_name="Configurable Redundant Output",
    category="safety",
    summary=(
        "Salida configurable redundante con verificación de feedback. "
        "Acepta condición de habilitación + feedback de retorno; energiza "
        "salidas redundantes O1/O2 cuando feedback coincide. Uso típico: "
        "control STO de servo drives Kinetix 5700 vía CIP Safety."
    ),
    pins=[
        InstructionPin("EnableIn", "input", "BOOL", "Condición de habilitación del rung"),
        InstructionPin("Actuate", "input", "BOOL", "Comando para habilitar las salidas"),
        InstructionPin("Feedback1", "input", "BOOL", "Feedback canal A desde dispositivo controlado"),
        InstructionPin("Feedback2", "input", "BOOL", "Feedback canal B desde dispositivo controlado"),
        InstructionPin("Reset", "input", "BOOL", "Reset manual tras fault (típicamente pulso)"),
        InstructionPin("EnableOut", "output", "BOOL", "Condición OK para próxima cascada"),
        InstructionPin("O1", "output", "BOOL", "Salida canal 1 (típicamente STO ch1 a drive)"),
        InstructionPin("O2", "output", "BOOL", "Salida canal 2 (típicamente STO ch2 a drive)"),
        InstructionPin("FP", "output", "BOOL", "Fault Present — 1 si hay fallo activo"),
    ],
    config_attributes=[
        InstructionPin("FeedbackType", "config", "ENUM",
                       "'Positive' (feedback HIGH = drive habilitado) o 'Negative' (invertido)"),
        InstructionPin("FeedbackReactionTime", "config", "DINT",
                       "Tiempo máximo (ms) para recibir feedback consistente. "
                       "Típico: 1000ms para drives Kinetix 5700"),
    ],
    fault_modes=[
        InstructionFault("Timeout",
                         "Feedback no llegó dentro de FeedbackReactionTime"),
        InstructionFault("Discrepancy",
                         "Feedback1 y Feedback2 difieren más allá del tiempo configurado"),
    ],
    references=[
        "Rockwell pub 1756-RM095 (GuardLogix Safety Instructions)",
    ],
    notes=(
        "Se usa típicamente dentro del SafetyProgram (que en GuardLogix queda "
        "encriptado por requerimiento SIL/PLe). En proyectos del parque Softys "
        "aparece como tag CROUT_*_STO controlando grupos de drives Kinetix 5700 "
        "por zona (MDP*, UWM*). El nombre CROUT también aparece como abreviación "
        "de 'Configurable Output' en algunas docs antiguas."
    ),
)


_DCI_STOP = InstructionMetadata(
    name="DCI_STOP",
    full_name="Dual Channel Input Stop",
    category="safety",
    summary=(
        "Procesa una entrada dual-channel (E-stop, safety switch, lifeline). "
        "Verifica equivalencia entre los dos canales y produce InputStatus "
        "consolidado. Si los canales discrepan más de FeedbackReactionTime "
        "→ FaultCode."
    ),
    pins=[
        InstructionPin("EnableIn", "input", "BOOL", "Habilitación"),
        InstructionPin("InputCH1", "input", "BOOL", "Canal 1 desde dispositivo físico"),
        InstructionPin("InputCH2", "input", "BOOL", "Canal 2 desde dispositivo físico"),
        InstructionPin("EnableOut", "output", "BOOL", "Pasante a próxima cascada"),
        InstructionPin("InputStatus", "output", "BOOL",
                       "Estado consolidado: 1 = ambos canales OK"),
        InstructionPin("FaultCode", "output", "DINT", "Código de fallo"),
        InstructionPin("DiagnosticCode", "output", "DINT", "Código diagnóstico adicional"),
    ],
    config_attributes=[
        InstructionPin("FeedbackReactionTime", "config", "DINT",
                       "Tiempo máximo (ms) de discrepancia tolerada"),
    ],
    fault_modes=[
        InstructionFault("ChannelDiscrepancy",
                         "CH1 y CH2 difieren más allá del tiempo configurado"),
    ],
    references=["Rockwell pub 1756-RM095"],
    notes=(
        "En proyectos del parque aparece como tag DCS_*_EStop. Se cascadea "
        "via AND lógico para producir señales tipo All_Estop_Ready."
    ),
)


_DCI_STOP_TEST_LOCK = InstructionMetadata(
    name="DCI_STOP_TEST_LOCK",
    full_name="Dual Channel Input Stop with Test and Lock",
    category="safety",
    summary=(
        "Versión extendida de DCI_STOP para puertas de seguridad con "
        "solenoide de bloqueo y entrada de test periódico. Permite "
        "verificación funcional de los canales sin abrir físicamente "
        "la guarda. Uso típico: SafetyGate con interlock electromagnético."
    ),
    pins=[
        InstructionPin("InputCH1", "input", "BOOL", "Canal 1 del switch"),
        InstructionPin("InputCH2", "input", "BOOL", "Canal 2 del switch"),
        InstructionPin("TestInput", "input", "BOOL", "Entrada de testing periódico"),
        InstructionPin("LockOutput", "output", "BOOL", "Comando del solenoide de lock"),
        InstructionPin("InputStatus", "output", "BOOL", "Estado consolidado"),
        InstructionPin("LockStatus", "output", "BOOL", "Estado del lock"),
        InstructionPin("FaultCode", "output", "DINT", "Código de fallo"),
    ],
    config_attributes=[
        InstructionPin("FeedbackReactionTime", "config", "DINT", "ms"),
    ],
    fault_modes=[
        InstructionFault("ChannelDiscrepancy", "CH1/CH2 difieren"),
        InstructionFault("TestFailure", "Test periódico falló"),
    ],
    references=["Rockwell pub 1756-RM095"],
    notes="En el parque aparece como tag DCSTL_SafetyGate_*.",
)


_MAJ = InstructionMetadata(
    name="MAJ",
    full_name="Motion Axis Jog",
    category="motion",
    summary=(
        "Inicia movimiento de jog (continuo) sobre un eje. El movimiento "
        "continúa hasta que se ejecuta MAS (stop), MAH (home) u otra "
        "instrucción que cancele el comando."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*", "Eje a mover"),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura interna de control (.EN, .DN, .ER, .IP, .ACC...)"),
        InstructionPin("Direction", "input", "BOOL", "0=reverse, 1=forward"),
        InstructionPin("Speed", "input", "REAL", "Velocidad de jog"),
        InstructionPin("Accel", "input", "REAL", "Aceleración"),
        InstructionPin("Decel", "input", "REAL", "Deceleración"),
        InstructionPin("LockPosition", "input", "REAL", "Posición de lock (típicamente 0)"),
    ],
    config_attributes=[
        InstructionPin("SpeedUnits", "config", "ENUM",
                       "'Units per sec' | '% of Maximum'"),
        InstructionPin("AccelUnits", "config", "ENUM",
                       "'Units per sec2' | '% of Maximum'"),
        InstructionPin("DecelUnits", "config", "ENUM", "ídem"),
        InstructionPin("Profile", "config", "ENUM", "'Trapezoidal' | 'S-Curve'"),
        InstructionPin("Merge", "config", "ENUM",
                       "'Disabled' | 'Coordinated Motion' | 'All Motion'"),
        InstructionPin("MergeSpeed", "config", "ENUM", "'Programmed' | 'Current'"),
        InstructionPin("LockDirection", "config", "ENUM",
                       "'None' | direcciones específicas"),
    ],
    references=["Rockwell pub MOTION-RM002"],
)


_MAG = InstructionMetadata(
    name="MAG",
    full_name="Motion Axis Gear",
    category="motion",
    summary=(
        "Engrana un eje slave a un master con razón de transmisión. El "
        "slave sigue la velocidad del master proporcionalmente. Uso típico "
        "en líneas continuas: ejes de máquina sincronizados al VirtualMaster."
    ),
    pins=[
        InstructionPin("SlaveAxis", "both", "AXIS_*", "Eje slave (sincronizado)"),
        InstructionPin("MasterAxis", "input", "AXIS_*", "Eje master de referencia"),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION", "Estructura de control"),
        InstructionPin("Direction", "input", "DINT", "Dirección relativa al master"),
        InstructionPin("Ratio", "input", "REAL", "Relación slave/master (gear ratio)"),
        InstructionPin("AccelRate", "input", "REAL", "Aceleración para clutch (si Enabled)"),
    ],
    config_attributes=[
        InstructionPin("RatioSlaveCounts", "config", "DINT", "Numerador del ratio"),
        InstructionPin("RatioMasterCounts", "config", "DINT", "Denominador del ratio"),
        InstructionPin("MasterReference", "config", "ENUM", "'Command' | 'Actual'"),
        InstructionPin("RatioFormat", "config", "ENUM", "'Real' | 'Counts'"),
        InstructionPin("ClutchEnable", "config", "ENUM", "'Disabled' | 'Enabled'"),
        InstructionPin("AccelUnits", "config", "ENUM", "'Units per sec2' | '% of Maximum'"),
    ],
    notes=(
        "Aparece intensivamente en el parque (CINTA: 48 invocaciones; AQL: "
        "más; CPPIM: protegidas en SafetyProgram). Patrón típico: "
        "MAG(AxA, VMaster, LocMagA, Direction, Ratio, ..., Command, Real, "
        "Disabled, AccelRate, 'Units per sec2')."
    ),
    references=["Rockwell pub MOTION-RM002"],
)


_MAS = InstructionMetadata(
    name="MAS",
    full_name="Motion Axis Stop",
    category="motion",
    summary=(
        "Detiene movimiento del eje. Permite especificar tipo de stop "
        "(All / Specific motion type) y rampa de deceleración."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*", "Eje a detener"),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION", ""),
        InstructionPin("Decel", "input", "REAL", "Deceleración (si ChangeDecel=Yes)"),
    ],
    config_attributes=[
        InstructionPin("StopType", "config", "ENUM",
                       "'All' | 'Jog' | 'Move' | 'Gear' | 'CamProfile' | etc."),
        InstructionPin("ChangeDecel", "config", "ENUM", "'Yes' | 'No'"),
        InstructionPin("DecelUnits", "config", "ENUM", ""),
    ],
    references=["Rockwell pub MOTION-RM002"],
)


_MAH = InstructionMetadata(
    name="MAH",
    full_name="Motion Axis Home",
    category="motion",
    summary=(
        "Ejecuta secuencia de homing del eje según configuración del axis "
        "tag (active/passive, sensor, marker, switch, etc.)."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*", "Eje a homear"),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION", ""),
    ],
    notes=(
        "El comportamiento concreto del homing está en la configuración del "
        "axis tag (HomeMode, HomeDirection, HomeSpeed, etc.), NO en los "
        "operandos de MAH. Para inspección detallada hay que mirar el "
        "AxisParameters en Studio 5000."
    ),
    references=["Rockwell pub MOTION-RM002"],
)


_MAOC = InstructionMetadata(
    name="MAOC",
    full_name="Motion Arm Output Cam",
    category="motion",
    summary=(
        "Conecta levas de salida (output cams) a un eje de movimiento. "
        "Activa/desactiva bloques de salida (32 bits) según posiciones del "
        "eje y condiciones de entrada. Modos Once/Continuous/Persistent + "
        "Schedule Immediate/Pending/Forward/Reverse/Bi-directional. Uso "
        "típico: máquinas rotativas continuas (web handling, splicers, "
        "packaging) para latch/unlatch de outputs por posición de eje."
    ),
    pins=[
        InstructionPin("Axis", "input", "AXIS_*", "Eje asociado a la leva de salida"),
        InstructionPin("ExecutionTarget", "input", "INT", "Output Cam específica (0-7)"),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura .EN/.DN/.ER/.IP/.PC"),
        InstructionPin("Output", "input", "DINT",
                       "32 bits memoria/output activados según leva"),
        InstructionPin("Input", "input", "DINT",
                       "32 bits para condicionar/habilitar leva"),
        InstructionPin("OutputCam", "input", "OUTPUT_CAM[]",
                       "Arreglo que define eventos Latch/Unlatch por bit"),
        InstructionPin("CamStartPosition", "input", "REAL",
                       "Límite izquierdo del rango de leva"),
        InstructionPin("CamEndPosition", "input", "REAL",
                       "Límite derecho del rango de leva"),
        InstructionPin("OutputCompensation", "input", "OUTPUT_COMPENSATION[]",
                       "Arreglo (1-32 elementos) para compensaciones de bits"),
        InstructionPin("AxisArmPosition", "input", "REAL",
                       "Posición del eje en la que se arma la leva"),
        InstructionPin("CamArmPosition", "input", "REAL",
                       "Posición del perfil leva al armar"),
    ],
    config_attributes=[
        InstructionPin("ExecutionMode", "config", "ENUM",
                       "Once | Continuous | Persistent"),
        InstructionPin("ExecutionSchedule", "config", "ENUM",
                       "Immediate | Pending | Forward | Reverse | Bi-directional"),
        InstructionPin("Reference", "config", "ENUM",
                       "Actual | Command (qué posición usa para evaluación)"),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix 5000 Motion Instructions)",
    ],
    notes=(
        "Cam profiles disponibles en cada elemento OUTPUT_CAM: Inactive | "
        "Position | Enable | Position and Enable | Duration and Enable. Modo "
        "Persistent rearma automáticamente al regresar al rango. Curado vía "
        "NotebookLM (workflow Ruflo+NotebookLM 2026-05-03)."
    ),
)


_MAM = InstructionMetadata(
    name="MAM",
    full_name="Motion Axis Move",
    category="motion",
    summary=(
        "Comanda al eje a moverse a una posición absoluta especificada o por "
        "una distancia incremental. Calcula automáticamente el perfil "
        "(trapezoidal o S-Curve) según las dinámicas dadas. Soporta modos "
        "Absolute / Incremental / Rotary (shortest path / positive / negative) "
        "y variantes Master Offset para Master Driven Speed Control (MDSC). "
        "Uso típico: posicionamiento, packaging, web handling, indexado."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*",
                       "Eje a mover. En modo Master Offset, este es el eje slave."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER/.IP/.PC/.AC/.ACCEL/.DECEL)"),
        InstructionPin("Position", "input", "REAL",
                       "Coordenada absoluta destino o distancia incremental, según MoveType."),
        InstructionPin("Speed", "input", "REAL",
                       "Velocidad vector máxima programada del move."),
        InstructionPin("AccelRate", "input", "REAL",
                       "Tasa de aceleración programada."),
        InstructionPin("DecelRate", "input", "REAL",
                       "Tasa de desaceleración programada."),
        InstructionPin("AccelJerk", "input", "REAL",
                       "Tasa de cambio de aceleración (solo aplica si Profile=S-Curve, "
                       "pero debe estar poblado)."),
        InstructionPin("DecelJerk", "input", "REAL",
                       "Tasa de cambio de desaceleración (idem AccelJerk)."),
        InstructionPin("LockPosition", "input", "REAL",
                       "Master Driven Speed Control (MDSC): posición del Master donde el "
                       "Slave empieza a seguir."),
        InstructionPin("EventDistance", "input", "REAL[] or 0",
                       "Posición(es) medidas hacia atrás desde el final del move que "
                       "disparan el cálculo de CalculatedData."),
        InstructionPin("CalculatedData", "output", "REAL[] or 0",
                       "Almacena la distancia master o el tiempo computado para alcanzar "
                       "el EventDistance."),
    ],
    config_attributes=[
        InstructionPin("MoveType", "config", "ENUM",
                       "0=Absolute | 1=Incremental | 2=Rotary Shortest Path | "
                       "3=Rotary Positive | 4=Rotary Negative | "
                       "5=Absolute Master Offset | 6=Incremental Master Offset"),
        InstructionPin("SpeedUnits", "config", "ENUM",
                       "0='Units per sec' | 1='% of Maximum' | 3='Time' | "
                       "4='Units per MasterUnit' | 7='Master Units'"),
        InstructionPin("AccelUnits", "config", "ENUM",
                       "0='Units per sec²' | 1='% of Maximum' | 3='Time' | "
                       "4='Units per MasterUnit²' | 7='Master Units'"),
        InstructionPin("DecelUnits", "config", "ENUM",
                       "Mismo enum que AccelUnits."),
        InstructionPin("Profile", "config", "ENUM",
                       "0='Trapezoidal' | 1='S-Curve'"),
        InstructionPin("JerkUnits", "config", "ENUM",
                       "0='Units per sec³' | 1='% of Maximum' | 2='% of Time' | "
                       "3='Time' | 4='Units per MasterUnit³' | "
                       "6='% of Time-Master Driven' | 7='Master Units'"),
        InstructionPin("Merge", "config", "ENUM",
                       "0='Disabled' | 1='Enabled' (define qué pasa si hay motion previo activo)"),
        InstructionPin("MergeSpeed", "config", "ENUM",
                       "0='Programmed' | 1='Current' (qué speed evaluar al hacer merge)"),
        InstructionPin("LockDirection", "config", "ENUM",
                       "0='None' | 1='Immediate Forward Only' | 2='Immediate Reverse Only' | "
                       "3='Position Forward Only' | 4='Position Reverse Only'"),
    ],
    fault_modes=[
        InstructionFault(
            "NonRestStartError",
            "Cuando SpeedUnits='Time' o 'Master Units', el move debe arrancar desde "
            "estado de reposo (velocidad y aceleración = 0). Si no, runtime error."
        ),
        InstructionFault(
            "OvershootRisk",
            "Riesgo de overshoot de velocidad o posición si las dinámicas cambian "
            "durante deceleración con DecelRate menor, o si Profile=S-Curve y los "
            "límites de jerk no pueden prevenir overshoot en la distancia restante."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "Instrucción process-type transitional. Status bits clave: .DN va TRUE "
        "inmediatamente cuando el motion planner ACEPTA el move (no cuando "
        "completa); .PC va TRUE solo cuando el eje arriva al endpoint Position; "
        ".IP es TRUE durante el movimiento. .ACCEL/.DECEL reflejan la fase actual "
        "de velocidad. "
        "\n\n"
        "Re-issue (Absolute): un MAM nuevo SUPERSEDE al anterior — el eje abandona "
        "el target previo y va directo al nuevo target con las nuevas dinámicas, "
        "incluso si requiere cambiar dirección. NO para en el target original. "
        "\n\n"
        "Re-issue (Incremental + Merge=Enabled): el remanente del move anterior se "
        "conserva y se SUMA al nuevo move. Ej: move incremental de 4 unidades "
        "interrumpido en posición 1 con un nuevo move incremental de 4 → eje "
        "termina en posición 8 (no 5). "
        "\n\n"
        "Aparece intensivamente en el parque (AQL: 24 invocaciones; CPPIM: 12; "
        "CINTA: 11). Curado vía NotebookLM (workflow Ruflo+NotebookLM 2026-05-03)."
    ),
)


_MSO = InstructionMetadata(
    name="MSO",
    full_name="Motion Servo On",
    category="motion",
    summary=(
        "Activa el amplificador del drive y habilita el lazo cerrado de servo "
        "control para un eje físico. Engancha el lazo en la posición actual del "
        "eje en preparación para comandos de movimiento subsiguientes."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*",
                       "Eje sobre el que se activa el servo."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER)"),
    ],
    config_attributes=[],
    fault_modes=[
        InstructionFault(
            "AxisInMotion (22)",
            "Error si MSO se intenta mientras el eje está en movimiento."
        ),
        InstructionFault(
            "ServoMessageFailure (12)",
            "Falló el messaging al módulo de servo (Object Mode conflict, "
            "dispositivo en estado incorrecto)."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "Ejecución asíncrona: puede tomar múltiples scans en completar. La lógica "
        "de secuencia debe esperar al .DN antes de comandar motion subsiguiente. Al "
        "éxito, fuerza ServoActionStatus y DriveEnableStatus a TRUE. Aparece en "
        "CINTA (1). Curado vía NotebookLM batch (2026-05-03)."
    ),
)


_MSF = InstructionMetadata(
    name="MSF",
    full_name="Motion Servo Off",
    category="motion",
    summary=(
        "Desactiva inmediatamente la salida del drive y deshabilita el lazo de "
        "servo del eje. Deshabilita planners de motion activos. Para non-CIP "
        "transiciona a Axis Ready; para CIP a Stopped."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*",
                       "Eje sobre el que se desactiva el servo."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER)"),
    ],
    config_attributes=[],
    fault_modes=[
        InstructionFault(
            "OperandTypeFault",
            "Major fault si se pasa referencia no inicializada o tipo "
            "incorrecto al operando Axis."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "PELIGRO operacional: si se ejecuta MSF mientras el eje está en movimiento, "
        "el eje COASTS to uncontrolled stop (no hay deceleración controlada — usar MAS "
        "primero para parada controlada). El .DN solo se setea tras completar el "
        "messaging asíncrono. Limpia todos los status bits de motion tracking. "
        "Aparece en CINTA (1). Curado vía NotebookLM batch (2026-05-03)."
    ),
)


_MAFR = InstructionMetadata(
    name="MAFR",
    full_name="Motion Axis Fault Reset",
    category="motion",
    summary=(
        "Limpia el status de fault del eje especificado. Es el único método "
        "programático para limpiar motion faults del eje. Solo limpia el status — "
        "NO realiza recovery (no re-habilita el servo, hay que invocar MSO después)."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*",
                       "Eje sobre el que se resetea el fault."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER)"),
    ],
    config_attributes=[],
    fault_modes=[
        InstructionFault(
            "OperandTypeFault",
            "Major fault si se pasa referencia no inicializada o tipo "
            "incorrecto al operando Axis."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "Si la condición física que causó el fault no se corrigió previamente, el eje "
        "vuelve a faultar inmediatamente — da apariencia de 'reset no funcionó'. La "
        "ejecución requiere multiple coarse updates al hardware del drive, así que el "
        ".DN puede tardar varios segundos en setearse. Aparece en CINTA (3) + "
        "AQL (3) + CPPIM (4) = 10 invocaciones acumuladas. Curado vía NotebookLM "
        "batch (2026-05-03)."
    ),
)


_MASR = InstructionMetadata(
    name="MASR",
    full_name="Motion Axis Shutdown Reset",
    category="motion",
    summary=(
        "Transiciona un eje específico de Shutdown a Axis Ready, limpiando "
        "automáticamente los faults asociados. Si todos los ejes del módulo se "
        "sacan de Shutdown, el contacto OK del módulo se cierra."
    ),
    pins=[
        InstructionPin("Axis", "both", "AXIS_*",
                       "Eje a sacar del estado Shutdown."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER)"),
    ],
    config_attributes=[],
    fault_modes=[
        InstructionFault(
            "OperandTypeFault",
            "Major fault si se pasa referencia no inicializada o tipo "
            "incorrecto al operando Axis."
        ),
        InstructionFault(
            "ShutdownStatusTimeout",
            "Sequencing issue: reset iniciado antes de que el shutdown previo "
            "finalice del lado del hardware."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "El .DN solo se setea tras múltiples coarse updates de hardware. Si la causa "
        "física del shutdown persiste, el reset 'falla' (eje refalla inmediatamente). "
        "Para que cierre el contacto OK del módulo, hay que ejecutar MASR sobre TODOS "
        "los ejes en shutdown asociados al módulo. Aparece en CINTA (1) + AQL (3) + "
        "CPPIM (5) = 9 invocaciones. Curado vía NotebookLM batch (2026-05-03)."
    ),
)


_MAPC = InstructionMetadata(
    name="MAPC",
    full_name="Motion Axis Position Cam",
    category="motion",
    summary=(
        "Camming electrónico entre dos ejes — sincroniza un Slave a un Master "
        "usando un Position Cam Profile pre-calculado (vía MCCP). Permite "
        "cancelar/reemplazar/agendar el cam profile en posiciones específicas "
        "del Master. Complementa MAOC (output cams) para máquinas rotativas."
    ),
    pins=[
        InstructionPin("SlaveAxis", "both", "AXIS_*",
                       "Eje slave controlado por el Master."),
        InstructionPin("MasterAxis", "both", "AXIS_*",
                       "Eje master que provee la posición de referencia."),
        InstructionPin("MotionControl", "both", "MOTION_INSTRUCTION",
                       "Estructura de control (.EN/.DN/.ER/.IP/.AC/.PC)"),
        InstructionPin("CamProfile", "input", "CAM_PROFILE",
                       "Array con datos del cam profile ya calculados (vía MCCP)."),
        InstructionPin("SlaveScaling", "input", "REAL",
                       "Multiplicador unitless que escala la distancia del Slave."),
        InstructionPin("MasterScaling", "input", "REAL",
                       "Multiplicador unitless que escala la distancia del Master."),
        InstructionPin("MasterLockPosition", "input", "REAL",
                       "Posición absoluta del Master donde inicia ejecución del cam."),
        InstructionPin("CamLockPosition", "input", "REAL",
                       "Punto de inicio dentro del cam profile cuando el Slave engancha."),
    ],
    config_attributes=[
        InstructionPin("Direction", "config", "ENUM",
                       "0='Same' | 1='Opposite' | 2='Reverse' | 3='Unchanged'"),
        InstructionPin("ExecutionMode", "config", "ENUM",
                       "0='Once' | 1='Continuous' | 2='Persistent'"),
        InstructionPin("ExecutionSchedule", "config", "ENUM",
                       "0='Immediate' | 1='Pending' | 2='ForwardOnly' | "
                       "3='ReverseOnly' | 4='Bidirectional'"),
        InstructionPin("CamType", "config", "ENUM",
                       "0='New Cam' | 1='Replace and Restart' | 2='Replace and Continue'"),
        InstructionPin("MasterReference", "config", "ENUM",
                       "0='Actual' | 1='Command'"),
        InstructionPin("MasterDirection", "config", "ENUM",
                       "0='Bidirectional' | 1='ForwardOnly' | 2='ReverseOnly'"),
    ],
    fault_modes=[
        InstructionFault(
            "AxisNotConfigured",
            "EXERR=1 si Slave no configurado, EXERR=2 si Master no configurado."
        ),
        InstructionFault(
            "UncalculatedCamProfile",
            "El array CamProfile no tiene status que indique que ya se calculó "
            "(ejecutar MCCP antes que MAPC)."
        ),
    ],
    references=[
        "Rockwell pub MOTION-RM002 (Logix5000 Controllers Motion Instructions Reference Manual)",
    ],
    notes=(
        "Completa en 1 scan: .DN y .IP se setean inmediatamente al iniciar (no "
        "esperan al fin físico del cam). Con Schedule='Pending' espera a que el cam "
        "actual termine antes de tomar control — IGNORA MasterAxis y "
        "MasterLockPosition. Decrementar MasterScaling o incrementar SlaveScaling "
        "sube velocidades y aceleraciones requeridas drásticamente — causa común de "
        "motion faults inesperados. Aparece en CINTA (1) + AQL (1) + CPPIM (7) = 9 "
        "invocaciones. Curado vía NotebookLM batch (2026-05-03)."
    ),
)


# Catálogo público (orden curado: safety primero, después motion)
ALL_INSTRUCTIONS: list[InstructionMetadata] = [
    _CROUT,
    _DCI_STOP,
    _DCI_STOP_TEST_LOCK,
    _MAJ,
    _MAG,
    _MAS,
    _MAH,
    _MAOC,
    _MAM,
    _MSO,
    _MSF,
    _MAFR,
    _MASR,
    _MAPC,
]


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


_REGISTRY: Optional[dict[str, InstructionMetadata]] = None


def _ensure_registry() -> dict[str, InstructionMetadata]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = {i.name: i for i in ALL_INSTRUCTIONS}
    return _REGISTRY


def get_instruction_metadata(name: str) -> Optional[InstructionMetadata]:
    """Devuelve la metadata curada de la instrucción `name`, o None."""
    return _ensure_registry().get(name)


def list_instructions(
    category: Optional[str] = None,
) -> list[InstructionMetadata]:
    """Lista todas las instrucciones curadas, opcionalmente filtradas por categoría.

    Categorías actuales: 'safety' | 'motion'.
    """
    items = list(_ensure_registry().values())
    if category:
        items = [i for i in items if i.category == category]
    return items


def known_instruction_names() -> set[str]:
    """Set de nombres de instrucciones curadas. Útil para detectar invocaciones."""
    return set(_ensure_registry().keys())


__all__ = [
    "InstructionPin",
    "InstructionFault",
    "InstructionMetadata",
    "ALL_INSTRUCTIONS",
    "get_instruction_metadata",
    "list_instructions",
    "known_instruction_names",
]
