"""patterns.py — Reconocimiento de patrones de naming y roles funcionales.

**Capa C de v0.3** (DT-009): tras la capa estructural (v0.1) y la capa de
trace causal (v0.2), esta capa enriquece el modelo del proyecto con
metadata semántica derivada de **convenciones de naming**:

- **Zonas físicas:** clusters detectados por prefijo común (MDP01, UWM01,
  STS_UWM01, etc.). Cada zona agrupa los modules / drives / tags que
  comparten ese prefijo.
- **Categorías de drives:** servo drives (SD\\d+), drives simples (M\\d+),
  drives complejos (M\\d+_\\d+U\\d+).
- **Patrones safety dual-channel:** DCS_*_EStop, DCSTL_SafetyGate_*,
  CROUT_*_STO, *_ChA / *_ChB / *_CH1 / *_CH2, *_Feedback_*.
- **Roles HMI:** HMI_*, *_Setpoint, *_Limit, *_Enable*, *_Reset, *_Cmd.

La detección es **conservadora** (solo reporta lo que matchea regex con
alta confianza). Los proyectos del parque Softys mezclan integradores
(HCH-chino con vendors Xu/Jin, Amantrini-brasileño, Rockwell estándar);
el catálogo crece incrementalmente cuando aparecen patrones nuevos en uso
real (DT-010 — validación empírica antes de comprometer).

API pública:
    from rockwell_comprehender.patterns import detect_patterns
    result = detect_patterns(project)
    # o vía property cached:
    result = project.detected_patterns

Estructuras devueltas: ver `DetectedPatterns` abajo.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras de salida
# ──────────────────────────────────────────────────────────────────────


@dataclass
class Zone:
    """Cluster de entidades (modules, drives, tags) que comparten un prefijo
    de zona física (`MDP01`, `UWM01`, etc.)."""

    name: str                                    # "UWM01"
    kind: str                                    # "unwinder" | "panel_drives" | "safety_status" | etc.
    member_modules: list[str] = field(default_factory=list)
    member_tags: list[str] = field(default_factory=list)


@dataclass
class NamingMatch:
    """Conjunto de entidades que matchearon un patrón de naming específico."""

    pattern_name: str         # "drive_servo_SD" | "safety_estop_dual" | etc.
    regex: str                # regex human-readable
    category: str             # "drive" | "safety" | "hmi_role" | "zone" | etc.
    matches: list[str]        # nombres de entidades que matchearon


@dataclass
class TagRole:
    """Rol inferido de un tag a partir de su nombre/sufijo/prefijo."""

    tag_name: str
    role: str                 # "hmi_command" | "feedback_signal" | "setpoint" | etc.


@dataclass
class DetectedPatterns:
    """Resultado completo del análisis de patterns sobre un proyecto."""

    zones: list[Zone] = field(default_factory=list)
    naming_matches: list[NamingMatch] = field(default_factory=list)
    tag_roles: dict[str, TagRole] = field(default_factory=dict)
    # Nuevos en v0.3.x (Diatec extension): tags agrupados por dominio
    # funcional (splice, unwinder, dancer, gearing, radius_compute) y por
    # rol de control de eje (start, enable, fault_code, physical_ref).
    # Orthogonales a tag_roles (que es per-tag, principalmente HMI).
    function_domain_tags: dict[str, list[str]] = field(default_factory=dict)
    axis_control_tags: dict[str, list[str]] = field(default_factory=dict)
    summary: dict[str, int] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────
# Catálogo de patrones (curado, crece con casos reales — DT-010)
# ──────────────────────────────────────────────────────────────────────


# Patrones de zonas físicas. Cada tupla: (kind, regex, group_index_para_extraer_id_zona)
# El regex matchea contra el nombre del module o del tag controller-scoped.
# Extraemos el grupo `id` para agrupar (ej. `MDP01_SD05` → zona `MDP01`).
_ZONE_PATTERNS: list[tuple[str, re.Pattern, int]] = [
    # MDP = Main Drives Panel (CPPIM/Amantrini)
    ("panel_drives", re.compile(r"^(MDP\d+)"), 1),
    # UWM = Unwinder Module (CPPIM/Amantrini)
    ("unwinder", re.compile(r"^(UWM\d+)"), 1),
    # STS = Safety Status zone (CPPIM)
    ("safety_status", re.compile(r"^STS_(UWM\d+|[A-Z]+\d+)"), 1),
    # SAS = Safety Adapter / Switch (CPPIM/Amantrini patrón observado)
    ("safety_adapter", re.compile(r"^SAS_(UWM\d+|[A-Z]+\d+)"), 1),
    # NODE_Z = nodos de I/O por zona (CINTA, AQL)
    ("io_node", re.compile(r"^NODE_(Z\d+)"), 1),
    # Diatec moderno (AQL): axis tags S04N71_DEBOB_AQL_DERECHO,
    # S04N72_DEBO_AQL_IZQUIERDO, ... — zona = sección S04 (16 axis en AQL)
    ("diatec_axis_section", re.compile(r"^(S\d+)N\d+_"), 1),
]

# Patrones de drives físicos (modules / axis tags). (kind, regex)
_DRIVE_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Servo drive con sufijo opcional A/B/C (CPPIM: SD01, SD02A, SD13B)
    ("drive_servo_SD", re.compile(r"^SD\d+[A-Z]?(?:_|$)")),
    # Drive complejo con tipo (AQL: M16_514U1, M3_504U1)
    ("drive_complex_module", re.compile(r"^M\d+_\d+U\d+")),
    # Drive simple (CINTA: M1, M2, M3, M4)
    ("drive_simple", re.compile(r"^M\d+$")),
    # Diatec moderno: AXIS_SERVO_DRIVE tags S\d+N\d+_<NAME>
    # (AQL: S04N71_DEBOB_AQL_DERECHO, S04N72_DEBO_AQL_IZQUIERDO, ...)
    ("drive_diatec_axis", re.compile(r"^S\d+N\d+_[A-Z]")),
]


# Patrones de dominio funcional (web-handling / Diatec / convergencia).
# Aplican sobre tags y agrupan por DOMINIO funcional, no por zona física.
# Útil para clasificar la lógica del proyecto: "qué tags tocan splice",
# "cuáles tocan tensión", etc. (kind, regex).
_FUNCTION_DOMAIN_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Splice control (CINTA + AQL — máquinas de empalme A↔B continuo).
    # Tags top en CINTA: Loc_SplicePreparedA/B (84 refs c/u), EVSpliceA,
    # StartForSplice, LocMemManSplice.
    ("splice", re.compile(r"^(Loc_)?Splice|^EV[A-Z]*Splice|^StartForSplice|SplicePrepared|SpliceMan", re.I)),
    # Unwinder (CINTA + AQL + CPPIM — bobinas de papel/film).
    ("unwinder", re.compile(r"^Unwind(er|ing)?|^Unwound|^UWM", re.I)),
    # Dancer / control de tensión (CINTA + AQL).
    ("dancer", re.compile(r"^Dancer|^DancerCor", re.I)),
    # Gearing electrónico (CINTA: 24× MAG, AQL: 24× MAG, sincronía eje-master).
    ("gearing", re.compile(r"^Loc_?Mag|^EV[A-Z]*Mag|GearRatio|GearEnable|^CS\[\d+\]\.Master", re.I)),
    # Radius / dancer-driven radius computation (Diatec legacy).
    ("radius_compute", re.compile(r"Radius.*Comput|RadiusCalc|^NewRadius|HmiActualRad", re.I)),
]


# Patrones de control de eje (axis control bits comunes en proyectos Diatec).
# Diferentes de tag_roles (que es HMI-focused) — estos son del nivel de
# control directo del axis (start, enable, fault code, physical reference).
_AXIS_CONTROL_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Comando de arranque del eje (CINTA: AxStart 73 refs, StartA, StartB).
    ("axis_start_command", re.compile(r"^(Loc_)?AxStart$|^StartA$|^StartB$|^StartMachine$|^StartMotor$")),
    # Status habilitado del eje (CINTA: AxEnabled 74 refs).
    ("axis_enable_status", re.compile(r"^(Loc_)?AxEnabled$|^EnableStatus$|^Enabled$|^AxisEnabled$")),
    # Código de fault del drive (CINTA: IstFaultCode 56 refs, DriveFaultBits_Code 33).
    ("axis_fault_code", re.compile(r"^IstFaultCode|^DriveFaultBits_Code|FaultCode$|^DriveFault")),
    # Referencia al physical axis (CINTA: PhysicalAx 41 refs).
    ("axis_physical_ref", re.compile(r"^PhysicalAx$|^Ax(_)?Spare$")),
]

# Patrones de safety. (kind, regex, category)
_SAFETY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("safety_estop_dual", re.compile(r"^DCS_.*_EStop")),
    ("safety_gate_lock", re.compile(r"^DCSTL_SafetyGate")),
    ("safety_crout_sto", re.compile(r"^CROUT_.*_STO")),
    ("safety_ChA", re.compile(r"_ChA$|_CH1$")),
    ("safety_ChB", re.compile(r"_ChB$|_CH2$")),
    ("safety_feedback", re.compile(r"_Feedback(_|$)")),
    ("safety_torque_disabled", re.compile(r"\.TorqueDisabled\d?$")),
    ("safety_torque_off", re.compile(r"\.SafeTorqueOff\d?$")),
]

# Patrones de roles HMI / control. (role, regex)
# Aplicar en orden de especificidad (más específicos primero).
_HMI_ROLE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("hmi_setpoint", re.compile(r"(?:Setpoint|SetPoint|SetValue)$", re.I)),
    ("hmi_limit", re.compile(r"Limit$", re.I)),
    ("hmi_enable_command", re.compile(r"(?:EnableCommand|EnableCmd)$|^HMI_.*Enable")),
    ("hmi_reset_command", re.compile(r"^HMI_.*Reset|_Reset$|^Cmd_.*Reset")),
    ("hmi_command", re.compile(r"^HMI_|^HMICommand|^Cmd_|^Hmi[A-Z]|\.Hmi|^HMI_.*Command")),
    ("hmi_diameter", re.compile(r"Hmi.*Diameter|.*Hmi.*Radius", re.I)),
    ("hmi_actual_value", re.compile(r"Hmi.*Actual", re.I)),
    ("hmi_status", re.compile(r"HmiStatus|StatusHMI", re.I)),
]


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def detect_patterns(project: "Project") -> DetectedPatterns:
    """Recorre el modelo del proyecto y detecta patterns de naming + roles.

    Es idempotente y puro — no modifica el proyecto. Pensado para usar vía
    `project.detected_patterns` (lazy property con cache).
    """
    result = DetectedPatterns()

    # 1. Zonas: agrupar modules y tags controller-scoped por prefijo de zona
    zone_modules: dict[tuple[str, str], list[str]] = defaultdict(list)
    zone_tags: dict[tuple[str, str], list[str]] = defaultdict(list)

    for m in project.modules:
        for kind, regex, group_idx in _ZONE_PATTERNS:
            mm = regex.match(m.name)
            if mm:
                zone_id = mm.group(group_idx)
                zone_modules[(kind, zone_id)].append(m.name)
                break

    for t in project.tags:
        if t.scope != "controller":
            continue
        for kind, regex, group_idx in _ZONE_PATTERNS:
            mm = regex.match(t.name)
            if mm:
                zone_id = mm.group(group_idx)
                zone_tags[(kind, zone_id)].append(t.name)
                break

    all_zone_keys = set(zone_modules.keys()) | set(zone_tags.keys())
    result.zones = [
        Zone(
            name=zone_id,
            kind=kind,
            member_modules=sorted(zone_modules.get((kind, zone_id), [])),
            member_tags=sorted(zone_tags.get((kind, zone_id), [])),
        )
        for kind, zone_id in sorted(all_zone_keys, key=lambda k: (k[0], k[1]))
    ]

    # 2. Naming matches por categoría (drives + safety)
    for kind, regex in _DRIVE_PATTERNS:
        matches = []
        for m in project.modules:
            if regex.search(m.name):
                matches.append(m.name)
        for t in project.tags:
            if t.scope == "controller" and regex.search(t.name):
                matches.append(t.name)
        if matches:
            result.naming_matches.append(
                NamingMatch(
                    pattern_name=kind,
                    regex=regex.pattern,
                    category="drive",
                    matches=sorted(set(matches)),
                )
            )

    for kind, regex in _SAFETY_PATTERNS:
        matches = []
        for t in project.tags:
            if regex.search(t.name):
                matches.append(t.name)
        for m in project.modules:
            if regex.search(m.name):
                matches.append(m.name)
        if matches:
            result.naming_matches.append(
                NamingMatch(
                    pattern_name=kind,
                    regex=regex.pattern,
                    category="safety",
                    matches=sorted(set(matches)),
                )
            )

    # 3. Tag roles por nombre/sufijo HMI
    seen_roles: set[str] = set()
    for t in project.tags:
        if t.name in seen_roles:
            continue
        for role, regex in _HMI_ROLE_PATTERNS:
            if regex.search(t.name):
                result.tag_roles[t.name] = TagRole(tag_name=t.name, role=role)
                seen_roles.add(t.name)
                break

    # 3b. Function domain tags (Diatec / web-handling — splice, unwinder,
    # dancer, gearing, radius_compute). Un tag puede pertenecer a múltiples
    # dominios (NO se usa break tras primer match).
    function_groups: dict[str, list[str]] = defaultdict(list)
    for t in project.tags:
        for kind, regex in _FUNCTION_DOMAIN_PATTERNS:
            if regex.search(t.name):
                function_groups[kind].append(t.name)
    result.function_domain_tags = {k: sorted(set(v)) for k, v in function_groups.items()}

    # 3c. Axis control tags (start, enable, fault_code, physical_ref).
    # Comunes en proyectos Diatec; un tag matchea SOLO uno (mutually exclusive).
    axis_groups: dict[str, list[str]] = defaultdict(list)
    seen_axis: set[str] = set()
    for t in project.tags:
        if t.name in seen_axis:
            continue
        for kind, regex in _AXIS_CONTROL_PATTERNS:
            if regex.search(t.name):
                axis_groups[kind].append(t.name)
                seen_axis.add(t.name)
                break
    result.axis_control_tags = {k: sorted(set(v)) for k, v in axis_groups.items()}

    # 4. Summary agregado
    role_counts: Counter[str] = Counter(tr.role for tr in result.tag_roles.values())
    naming_counts_by_cat: Counter[str] = Counter()
    naming_match_total = 0
    for nm in result.naming_matches:
        naming_counts_by_cat[nm.category] += len(nm.matches)
        naming_match_total += len(nm.matches)

    result.summary = {
        "zones_total": len(result.zones),
        "zones_by_kind": dict(Counter(z.kind for z in result.zones)),
        "naming_matches_total": naming_match_total,
        "naming_matches_by_category": dict(naming_counts_by_cat),
        "tag_roles_total": len(result.tag_roles),
        "tag_roles_by_role": dict(role_counts),
        # Nuevos v0.3.x — Diatec extension
        "function_domains_total": sum(len(v) for v in result.function_domain_tags.values()),
        "function_domains_by_kind": {k: len(v) for k, v in result.function_domain_tags.items()},
        "axis_control_total": sum(len(v) for v in result.axis_control_tags.values()),
        "axis_control_by_kind": {k: len(v) for k, v in result.axis_control_tags.items()},
    }

    return result
