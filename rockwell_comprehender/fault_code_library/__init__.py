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


_K5700_FLT_S07 = FaultCode(
    code="FLT S07",
    name="Motor Thermal Overload Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El cálculo interno del thermal model del motor indica que la "
        "temperatura excedió el factory limit. Diferente de FLT S05 "
        "(que es del thermistor físico): este es el modelo I²T calculado "
        "por el drive."
    ),
    cause=(
        "El commanded motion profile requiere RMS current continuo que "
        "genera más calor que la capacidad física del motor. Típicamente "
        "duty cycles muy agresivos, dimensionamiento insuficiente del motor, "
        "o moves repetitivos sin tiempo de cooling."
    ),
    recovery=(
        "1. Cambiar el commanded motion profile para reducir velocidad o "
        "aumentar tiempo del move (baja el RMS current). "
        "2. Verificar que el motor esté correctamente dimensionado para la carga. "
        "3. Esperar que el motor se enfríe (timer del thermal model). "
        "4. MAFR + MSO."
    ),
    related_parameters=["MotorCapacity", "MotorThermalOverloadFactoryLimit"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="I²T model — diferente del thermistor S05. Si ambos disparan, el problema es físico (el motor SÍ está caliente). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S11 = FaultCode(
    code="FLT S11",
    name="Inverter Overtemperature Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "Temperatura física medida DENTRO del inverter excede el factory "
        "limit. Diferente de FLT S13 (que es el thermal MODEL del inverter): "
        "este es el sensor físico real del drive."
    ),
    cause=(
        "Commanded motion demanding, ambient temperature alta del gabinete, "
        "filtros de aire obstruidos, ventilación inadecuada, o falla del "
        "fan interno del drive."
    ),
    recovery=(
        "1. Cambiar el command profile (reducir speed o aumentar tiempo del move). "
        "2. Reducir ambient temperature del gabinete (verificar AC, abrir si es seguro). "
        "3. Verificar que el airflow al inverter NO esté obstruido. "
        "4. Verificar limpieza de filtros / ventilas. "
        "5. Esperar enfriamiento + MAFR + MSO."
    ),
    related_parameters=["InverterCapacity", "DriveOvertempFault"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Sensor físico — diferente del thermal model S13. Si ambos disparan, el inverter SÍ está físicamente caliente. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S33 = FaultCode(
    code="FLT S33",
    name="Bus Undervoltage Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El nivel de DC bus voltage medido es menor que el límite mínimo "
        "configurado de fábrica. Indica problema de alimentación AC o pérdida "
        "de potencia del bus."
    ),
    cause=(
        "AC input voltage bajo en alguna fase, line drops o sags en la "
        "facility power, falla externa de potencia, o problema en el módulo "
        "de power supply (DC bus power supply)."
    ),
    recovery=(
        "1. Verificar AC input voltage en TODAS las fases con multímetro. "
        "2. Monitorear la facility power por faults o line drops "
        "(¿hay otros equipos disparando breakers?). "
        "3. Si el input es inestable, instalar UPS en la AC input. "
        "4. Verificar continuidad y dimensionamiento del cableado AC. "
        "5. MAFR + MSO una vez restaurada la alimentación."
    ),
    related_parameters=["DCBusVoltage", "BusUnderVoltageLimit"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Diagnostic crítico: si dispara repetidamente, hay problema de power quality del facility (no del drive). Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S35 = FaultCode(
    code="FLT S35",
    name="Bus Overvoltage Factory Limit",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El nivel de DC bus voltage medido es MAYOR que el factory limit "
        "máximo. Típicamente indica energía regenerativa que el bus no puede "
        "disipar."
    ),
    cause=(
        "Energía regenerativa excesiva del motor (decel agresiva, cargas "
        "overhauling como ejes verticales bajando), shunt resistance "
        "abierta o desconectada, falta de capacidad de disipación en el bus."
    ),
    recovery=(
        "1. Cambiar el motion profile para reducir energía regenerativa "
        "(decel rates más bajos, S-Curve en vez de Trapezoidal). "
        "2. Desconectar el shunt connector y MEDIR la shunt resistance "
        "(debe estar continua, no abierta). "
        "3. Si shunt está abierta: reemplazar power supply o agregar shunt "
        "module externo. "
        "4. Considerar Active Shunt Module para más capacidad de disipación. "
        "5. MAFR + MSO."
    ),
    related_parameters=["DCBusVoltage", "BusOverVoltageLimit"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Frecuente en máquinas con cargas overhauling (vertical axes, web rewinders frenando). Si hay multi-axis con shared bus, una decel agresiva de UN eje puede disparar el fault de OTROS. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_SAFE_FLT_09 = FaultCode(
    code="SAFE FLT 09",
    name="GuardStop Input Fault",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "Los hardwired safety inputs (S1 y S2 del STO) presentan estados "
        "diferentes por más de 1.0 segundo, o hay issues con el wiring "
        "safety y la alimentación +24V. Los diagnostics internos detectaron "
        "STO function mismatch."
    ),
    cause=(
        "Discrepancy entre canales A y B del STO (un canal ON, otro OFF), "
        "wiring del safety con falla intermitente, +24V no presente o "
        "inestable, conector STO suelto, o falla interna del drive en los "
        "circuitos safety."
    ),
    recovery=(
        "1. Verificar safety wiring en ambos canales (continuidad, conexiones firmes). "
        "2. Confirmar que el STO connector esté correctamente seated. "
        "3. Verificar que +24V esté presente en ambos canales con multímetro. "
        "4. Verificar el estado sincronizado de ambos safety inputs. "
        "5. Clear el error y EJECUTAR un proof test de safety. "
        "6. Si el error persiste tras todo lo anterior: drive con falla "
        "interna safety — RETORNAR a Rockwell (no se puede reparar en campo)."
    ),
    related_parameters=["GuardStopInputFault", "GuardStopInputStatus"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Categoría SAFE FLT (no FLT S regular) — falls del subsistema safety. El proof test (paso 5) es REQUERIDO certificación SIL/PLe — documentar la ejecución. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_INHIBIT_S02 = FaultCode(
    code="INHIBIT S02",
    name="Motor Not Configured",
    family="Kinetix 5700",
    severity="Inhibit",
    description=(
        "Start inhibit que previene que el drive se habilite porque el "
        "motor asociado no fue configurado correctamente. NO es un fault "
        "(el drive nunca llegó a operar) — es un inhibit en init."
    ),
    cause=(
        "Los motor configuration parameters no se establecieron o "
        "downloaded al controller. Típicamente: nuevo axis sin config, "
        "MotorCatalogNumber vacío o incorrecto, o cambio de motor sin "
        "actualizar la config en Logix Designer."
    ),
    recovery=(
        "1. Abrir Logix Designer y verificar Axis Properties → Motor tab. "
        "2. Verificar que MotorCatalogNumber esté correcto y aplicado al axis. "
        "3. Si se cambió el motor físico: actualizar el catalog number, "
        "re-comisionar (autotune + hookup test). "
        "4. Download al controller. "
        "5. INHIBIT desaparece automáticamente al detectar config válida."
    ),
    related_parameters=["MotorCatalogNumber", "AxisConfigState"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Categoría INHIBIT (no FLT) — no requiere MAFR, se limpia solo al corregir config. Common en commissioning de nuevos axes. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S54 = FaultCode(
    code="FLT S54",
    name="Position Error Fault",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El position error del position control loop excedió el valor "
        "establecido en el parámetro Position Error Tolerance por más tiempo "
        "que el Position Error Tolerance Time. El axis position real está "
        "lagging demasiado del commanded — el drive ejecuta protective stop."
    ),
    cause=(
        "Position loop mal tuneado, motor/drive subdimensionado para la "
        "aplicación, sistema mecánico fuera de spec o atascado, o problemas "
        "con motor power wiring."
    ),
    recovery=(
        "1. Verificar position loop tuning (autotune o manual). "
        "2. Aumentar feedforward gain (compensa fricción/inercia). "
        "3. Verificar dimensionamiento drive+motor vs requerimiento real. "
        "4. Inspeccionar mecánica (atascos, alineamiento, lubricación). "
        "5. Verificar motor power wiring (continuidad, sin cortos). "
        "6. Si el sistema funciona pero margen es justo: aumentar "
        "PositionErrorTolerance y/o PositionErrorToleranceTime."
    ),
    related_parameters=["PositionErrorTolerance", "PositionErrorToleranceTime"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="El más común diagnostico de motion 'algo está mal mecánicamente' o 'tuning mal'. Si dispara durante decel: feedforward bajo. Durante steady-state: fricción alta o load excesivo. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_INHIBIT_S01 = FaultCode(
    code="INHIBIT S01",
    name="Enable Input Inhibit",
    family="Kinetix 5700",
    severity="Inhibit",
    description=(
        "Cuando Drive Enable Input Checking está habilitado, el drive "
        "triggers este start inhibit cuando detecta que el hardware enable "
        "input físico está inactivo. Previene que el drive transicione a "
        "torque-producing state si falta el permissive."
    ),
    cause=(
        "Permissive físico (hardware enable) perdido o desconectado al "
        "intentar habilitar el axis. Wiring del input con falla, terminales "
        "flojos, o lógica de control que no está aplicando el enable."
    ),
    recovery=(
        "1. Confirmar que el digital input asignado al enable function esté ACTIVE. "
        "2. Verificar wiring y terminales del hardware enable input en el drive. "
        "3. Verificar digital input assignments en la software config (¿está apuntando al input correcto?). "
        "4. Verificar la lógica que aplica el enable (HMI, permissives, etc.)."
    ),
    related_parameters=["DriveEnableInputChecking", "EnableInput"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="INHIBIT (no fault) — el drive nunca llegó a operar. Common al startup tras paro de planta. Si dispara repetidamente: lógica del enable mal escrita o input físico con problema intermitente. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_FLT_S49 = FaultCode(
    code="FLT S49",
    name="Brake Slip Fault",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El displacement del motor excedió la brake slip tolerance permitida "
        "mientras el mechanical holding brake estaba engaged. El drive "
        "detectó que el brake falló en mantener el eje estacionario."
    ),
    cause=(
        "Fuerzas mecánicas externas excediendo el rated holding torque del "
        "brake del motor (cargas verticales, overhauling, vibración). "
        "Wear mecánico de las pastillas del brake con el tiempo. "
        "Comando de engage del brake antes de que motor esté en 0 rpm "
        "(brake slip durante deceleración residual)."
    ),
    recovery=(
        "1. Verificar integridad mecánica del sistema y que la load aplicada "
        "no exceda el rated brake-holding torque del motor. "
        "2. Verificar que BrakeSlipTolerance esté correctamente configurado "
        "para la aplicación. "
        "3. Modificar el control logic para asegurar deceleración a 0 rpm "
        "ANTES de engage del brake. "
        "4. Inspección física del brake (wear pads, fricción, alineamiento)."
    ),
    related_parameters=["BrakeSlipTolerance", "MechanicalBrakeEngageDelay"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="⚠️ Datos parcialmente EXTRAPOLADOS — NotebookLM marcó causes y recovery como 'inferred from general motion control principles, please verify'. Description y nombre sí son del manual 2198-UM002. Re-validar contra fuente oficial antes de usar para decisiones críticas. Curado vía NotebookLM batch (2026-05-03).",
)


_K5700_NODE_FLT_05 = FaultCode(
    code="NODE FLT 05",
    name="Clock Skew Fault",
    family="Kinetix 5700",
    severity="Major",
    description=(
        "El internal time del Logix controller y el time del drive system "
        "no matchean. La time coordination precisa es requerida para "
        "Integrated Motion — el drive genera major network fault para "
        "proteger el sistema de movement uncoordinated."
    ),
    cause=(
        "Ethernet network congestion severa, poor network topology, "
        "Ethernet switches dropping PTP (Precision Time Protocol) packets, "
        "o cables disconnected/degraded. También: switch no-CIP en el path "
        "que rompe PTP transparency."
    ),
    recovery=(
        "1. Disconnect y re-connect control power al drive (re-sync PTP). "
        "2. Verificar operación del Logix controller y del Ethernet switch. "
        "3. Asegurar que la network topology esté optimizada para CIP Sync "
        "y PTP traffic (switches Stratix con PTP transparent clock support). "
        "4. Revisar utilización de la red (Stratix diagnostics, packet loss). "
        "5. Verificar cables Ethernet (cat 5e mínimo, sin damage)."
    ),
    related_parameters=["TimeSynchronization", "PTPPortState"],
    references=["Rockwell pub 2198-UM002 (Kinetix 5700 Servo Drive User Manual)"],
    notes="Crítico para CIP Motion. Si dispara frecuentemente, escalar a network engineer — puede haber switches no-PTP-compliant o congestión real. Diferente de NODE FLT 01 (late update) y NODE FLT 06 (lost connection): este es desync de tiempo, no pérdida de paquetes. Curado vía NotebookLM batch (2026-05-03).",
)


# NOTAS sobre faltantes en este batch (NOT FOUND en 2198-UM002):
# - SW Overtravel (Software Overtravel POSITIVE/NEGATIVE): probablemente
#   documentado en config attributes del axis (PositiveSWOvertravel /
#   NegativeSWOvertravel) en lugar de fault code propio. Investigar
#   manual MOTION-RM003 o axis config docs.
# - Auxiliary Position Feedback fault: 2198-UM002 cubre solo motor
#   feedback principal. Aux feedback puede estar en Kinetix 5700 SI
#   manual variant o configurable en CIP Motion. Investigar separado.


ALL_FAULT_CODES: list[FaultCode] = [
    _K5700_FLT_S03,
    _K5700_FLT_S05,
    _K5700_FLT_S07,
    _K5700_FLT_S11,
    _K5700_FLT_S13,
    _K5700_FLT_S33,
    _K5700_FLT_S35,
    _K5700_FLT_S44,
    _K5700_FLT_S47,
    _K5700_FLT_S49,
    _K5700_FLT_S50,
    _K5700_FLT_S54,
    _K5700_INHIBIT_S01,
    _K5700_INHIBIT_S02,
    _K5700_SAFE_FLT_09,
    _K5700_NODE_FLT_01,
    _K5700_NODE_FLT_05,
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
