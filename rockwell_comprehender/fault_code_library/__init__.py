"""Fault Code Library — códigos de fallo curados de drives Rockwell.

**Capa D extendida** (paralela a `instruction_library/`). Esta capa NO extrae
datos del L5X; almacena **conocimiento de dominio curado** sobre fault codes
de drives (Kinetix 5700, Kinetix 6000, etc.):
código, severidad, descripción, causa raíz, recovery action, parámetros
relacionados, referencias a publicación oficial.

El catálogo es **mínimo viable** — crece incrementalmente cuando aparece
caso real (DT-010, validación empírica antes de comprometer). Cada fault
code se cura desde su manual oficial vía NotebookLM (publicación 2198-UM002
para Kinetix 5700; 2094-UM001/UM002 para Kinetix 6000; etc.).

Uso:
    from rockwell_comprehender.fault_code_library import (
        get_fault_code, list_fault_codes
    )
    fc = get_fault_code("FLT S07", family="Kinetix 5700")
    print(fc.description)
    print(f"Recovery: {fc.recovery}")

    # Listar todos los faults de una family:
    all_k5700 = list_fault_codes(family="Kinetix 5700")

    # Filtrar por severity:
    majors = list_fault_codes(severity="Major")

Pilot inicial v0.3.x (8 fault codes Kinetix 5700, representativos de
categorías: power, thermal, motor, feedback, communication, safety, config).

Fuentes:
- Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)
- Rockwell pub 2094-UM001 (Kinetix 6000 Multi-Axis Drives User Manual) — pendiente
- Rockwell pub 2094-UM002 (Kinetix 6200/6500 Modular User Manual) — pendiente
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# Estructura
# ──────────────────────────────────────────────────────────────────────


@dataclass
class FaultCode:
    """Metadata curada de un fault code de drive Rockwell."""

    code: str                                          # "FLT S07", "INIT FLT M02", "E15"
    name: str                                          # "Bus Overvoltage Fault"
    family: str                                        # "Kinetix 5700" | "Kinetix 6000" | ...
    severity: str                                      # "Major" | "Minor" | "Initialization" | "Configuration" | "Inhibit"
    description: str = ""                              # Qué significa
    cause: str = ""                                    # Causas típicas
    recovery: str = ""                                 # Acción para limpiar
    related_parameters: list[str] = field(default_factory=list)  # Axis params relevantes
    references: list[str] = field(default_factory=list)
    notes: str = ""


# ──────────────────────────────────────────────────────────────────────
# Catálogo curado
# ──────────────────────────────────────────────────────────────────────


_K5700_FLT_S03 = FaultCode(
    code="FLT S03",
    name="Motor Overspeed Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El drive detecta que la velocidad del motor excedió el límite máximo "
        "de velocidad configurado de fábrica (factory limit, no el user limit "
        "configurable)."
    ),
    cause=(
        "Dinámicas de motion mal tuneadas (velocity loop con overshoot), "
        "perfil de motion con velocidad excesiva, problema de cuenta del "
        "feedback, o resonancia mecánica."
    ),
    recovery=(
        "1. Verificar que el commanded motion no exceda el speed rating del motor. "
        "2. Re-tune del velocity loop (autotune o manual). "
        "3. Verificar feedback wiring / shielding. "
        "4. MAFR para clear el fault, después MSO para re-habilitar."
    ),
    related_parameters=["MotorRatedVelocity", "VelocityLimit", "MaxVelocity"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Acción del drive: disable o coast (depende de drive series y config). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S05 = FaultCode(
    code="FLT S05",
    name="Motor Overtemperature Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El thermistor o sensor de temperatura del motor indica que la "
        "temperatura excedió el factory limit. Protección térmica del motor."
    ),
    cause=(
        "Operación continua arriba del torque rating, ambiente con temperatura "
        "elevada, ventilación insuficiente del gabinete, ciclo de duty muy "
        "agresivo, o thermistor con falla."
    ),
    recovery=(
        "1. Esperar enfriamiento del motor (puede tardar varios minutos). "
        "2. Verificar que la operación esté dentro del continuous torque rating. "
        "3. Reducir ambient temperature o mejorar ventilación. "
        "4. Verificar conexión del thermistor. "
        "5. MAFR + MSO."
    ),
    related_parameters=["MotorThermalCurrentLimit", "MotorOverloadFactor"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Acción del drive: current decel o disable coast (depende de load control config). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S13 = FaultCode(
    code="FLT S13",
    name="Inverter Thermal Overload Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El thermal model del inverter calculó una temperatura excediendo "
        "el 110% capacity rating. Protege componentes de potencia del drive."
    ),
    cause=(
        "Duty cycle alto del commanded motion, accel/decel muy agresivos "
        "(genera RMS current alto), drive subdimensionado para la carga, "
        "o ventilación inadecuada del drive."
    ),
    recovery=(
        "1. Reducir duty cycle del motion comandado. "
        "2. Bajar AccelRate / DecelRate para reducir RMS current. "
        "3. Verificar dimensionamiento del drive vs requerimiento real. "
        "4. Esperar enfriamiento del drive. "
        "5. MAFR + MSO."
    ),
    related_parameters=["InverterCapacity", "InverterOverloadFactor", "ContinuousCurrent"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Acción del drive: disable y coast (protege power components). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S44 = FaultCode(
    code="FLT S44",
    name="Feedback Signal Loss User Limit",
    family="Kinetix 5700",
    severity="Minor",
    description=(
        "Los electrical signals de los canales del feedback están comprometidos "
        "o perdidos. User Limit (UL): el límite es configurable, NO el factory limit."
    ),
    cause=(
        "Cable de encoder dañado / desconectado, shielding inadecuado, EMI desde "
        "drives vecinos, conector de feedback sucio o flojo, o problema con "
        "alimentación del encoder."
    ),
    recovery=(
        "1. Verificar integridad del cable de encoder. "
        "2. Revisar shielding y aterrizajes. "
        "3. Reseat conectores de feedback. "
        "4. Verificar tensión de alimentación del encoder. "
        "5. MAFR + MSO. Si persiste, escalar a S47 (device failure)."
    ),
    related_parameters=["FeedbackType", "FeedbackResolution"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Severity puede ser Minor o Major según drive series y configuración. Acción: ramped decel o hold. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S47 = FaultCode(
    code="FLT S47",
    name="Feedback Device Failure",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "Error interno o falla de hardware del feedback device conectado "
        "(encoder, resolver, sensor de posición). Más severo que S44 — "
        "el device tiene problema interno, no solo señal."
    ),
    cause=(
        "Encoder con falla interna, daño físico al sensor, falla del "
        "circuito electrónico del feedback device, o motor con encoder "
        "integrado dañado."
    ),
    recovery=(
        "1. Reemplazar feedback device. "
        "2. Si el encoder es integrado al motor (Hiperface, EnDat), "
        "puede requerir reemplazo del motor completo. "
        "3. Verificar que el reemplazo sea compatible con la config del axis. "
        "4. Re-comisionar (auto-tune, hookup test) tras reemplazo."
    ),
    related_parameters=["FeedbackType", "FeedbackResolution", "MotorCatalogNumber"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Acción del drive: disable o coast stop (previene motion uncontrolled). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S50 = FaultCode(
    code="FLT S50",
    name="Hardware Overtravel Positive",
    family="Kinetix 5700",
    severity="Minor",
    description=(
        "El eje viajó más allá del límite máximo de posición definido por un "
        "limit switch físico (hardware). Protección de fin de carrera positivo."
    ),
    cause=(
        "Motion comandado más allá del límite mecánico, falla del limit switch "
        "(falsa activación), homing incorrecto que dejó la referencia desplazada, "
        "o operador que comandó jog manual fuera de rango."
    ),
    recovery=(
        "1. Verificar seguridad mecánica antes de cualquier movimiento. "
        "2. Jog manual del eje en dirección REVERSA hasta salir del overtravel. "
        "3. Verificar/corregir el motion profile y la posición home. "
        "4. MAFR + MSO. "
        "5. Re-validar limit switch wiring si fue falsa activación."
    ),
    related_parameters=["PositiveSWOvertravel", "HomeMode", "HomePosition"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Severity puede ser Minor o Major según config. Acción: ramped decel o hold. NO confundir con SW Overtravel (límite por software). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_NODE_FLT_01 = FaultCode(
    code="NODE FLT 01",
    name="Late Control Update",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El drive perdió varios syncronous position updates consecutivos del "
        "controller via EtherNet/IP. La sincronización CIP Motion se "
        "comprometió."
    ),
    cause=(
        "Tráfico de red elevado, RPI muy agresivo, switch saturado, topología "
        "no optimizada (DLR vs star), latencia inducida por dispositivos "
        "no-CIP, o jitter del controller."
    ),
    recovery=(
        "1. Verificar utilización de la red (Stratix diagnostics, packets dropped). "
        "2. Aumentar RPI si aplica. "
        "3. Optimizar topología (separar tráfico safety/motion del tráfico HMI/IO). "
        "4. Verificar QoS de los switches. "
        "5. MAFR + MSO."
    ),
    related_parameters=["RPI", "ControllerOwnedTimeStamp"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Network-level fault (NODE FLT vs FLT S regular). Acción: decel y disable. Si frecuente, ver ENET-RM002 para tuning de network. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_NODE_FLT_06 = FaultCode(
    code="NODE FLT 06",
    name="Lost Controller Connection",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "Pérdida COMPLETA de la conexión EtherNet/IP entre el servo drive y "
        "el Logix controller. Más severo que NODE FLT 01 (que es solo updates "
        "tardíos)."
    ),
    cause=(
        "Cable Ethernet desconectado o dañado, switch caído, controller "
        "apagado/reset, falla del módulo de comunicación, o config IP "
        "incorrecta."
    ),
    recovery=(
        "1. Verificar conexión física del cable Ethernet al drive. "
        "2. Verificar que el switch esté operativo. "
        "3. Confirmar que el controller esté powered y en RUN. "
        "4. Verificar IP del drive y comunicación con ping. "
        "5. Una vez restaurada conexión: MAFR + MSO."
    ),
    related_parameters=["NodeAddress", "NetworkConnectionStatus"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Acción del drive: ramped decel o coast. Si la pérdida es prolongada, considerar Hold Last State del axis para safety. Curado vía NotebookLM batch (2026-05-03).",
)


ALL_FAULT_CODES: list[FaultCode] = [
    _K5700_FLT_S03,
    _K5700_FLT_S05,
    _K5700_FLT_S13,
    _K5700_FLT_S44,
    _K5700_FLT_S47,
    _K5700_FLT_S50,
    _K5700_NODE_FLT_01,
    _K5700_NODE_FLT_06,
]


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


_REGISTRY: Optional[dict[str, FaultCode]] = None


def _ensure_registry() -> dict[str, FaultCode]:
    """Construye/devuelve el registry indexado por (family, code)."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = {f"{fc.family}::{fc.code}": fc for fc in ALL_FAULT_CODES}
    return _REGISTRY


def get_fault_code(
    code: str,
    family: Optional[str] = None,
) -> Optional[FaultCode]:
    """Devuelve el FaultCode `code` para la `family` dada, o None.

    Si `family` es None, retorna el primer match en cualquier family.
    Para casos donde el mismo código existe en families distintas con
    semántica diferente, especificar siempre `family`.
    """
    reg = _ensure_registry()
    if family:
        return reg.get(f"{family}::{code}")
    for fc in reg.values():
        if fc.code == code:
            return fc
    return None


def list_fault_codes(
    family: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[FaultCode]:
    """Lista fault codes, opcionalmente filtrados por family y/o severity.

    Families actuales: 'Kinetix 5700' (otros pendientes).
    Severities: 'Major' | 'Minor' | 'Initialization' | 'Configuration' | 'Inhibit'.
    """
    items = list(_ensure_registry().values())
    if family:
        items = [f for f in items if f.family == family]
    if severity:
        items = [f for f in items if f.severity == severity]
    return items


def known_fault_codes(family: Optional[str] = None) -> set[str]:
    """Set de códigos curados, opcionalmente filtrados por family.

    Útil para detectar si un fault code reportado en logs/HMI ya está
    en el library o necesita ser curado.
    """
    items = list_fault_codes(family=family)
    return set(f.code for f in items)


__all__ = [
    "FaultCode",
    "ALL_FAULT_CODES",
    "get_fault_code",
    "list_fault_codes",
    "known_fault_codes",
]
