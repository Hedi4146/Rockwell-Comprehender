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

Catálogo inicial v0.3 (7 instrucciones):
- Safety: CROUT, DCI_STOP, DCI_STOP_TEST_LOCK
- Motion: MAJ, MAG, MAS, MAH

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


# Catálogo público (orden curado: safety primero, después motion)
ALL_INSTRUCTIONS: list[InstructionMetadata] = [
    _CROUT,
    _DCI_STOP,
    _DCI_STOP_TEST_LOCK,
    _MAJ,
    _MAG,
    _MAS,
    _MAH,
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
