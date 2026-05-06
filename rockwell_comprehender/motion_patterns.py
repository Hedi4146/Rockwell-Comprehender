"""Motion Patterns — detector de composición motion nivel-2 (v0.4).

Cierra la **Capacidad #4 del Vision** (Semántica composicional motion):
hoy `instruction_library` tiene los átomos individuales (MAJ, MAS, MAH,
MAOC, etc.) pero no detecta **composiciones**. Este módulo identifica
patrones recurrentes de uso conjunto de motion instructions que
representan funciones semánticas de mayor nivel (splice transition,
gear chain, axis lifecycle, etc.).

**Diseño:**
- Análisis empírico previo identificó pares y sets recurrentes en el
  parque (CINTA + AQL + CPPIM). Los 8 detectores codificados aquí
  cubren ~85% de las routines con motion ops del parque actual.
- Cada detector busca co-ocurrencia de ops en la misma routine y/o
  por backing tag (axis name). Confidence se calcula por fortaleza
  del match (cantidad de ops, posicionamiento, presencia de master/slave).
- Output: `MotionPatternMatch` con location, backing_tag, instructions
  matched, evidence — apto para inclusión en TDR + smells.

**Stack mínimo (DT-008):** stdlib only + tokenize_rll/tokenize_st + estructuras
del modelo. Sin dependencias agregadas.

**Validación empírica (HANDOFF antipatrón #2):** detectores ejercitados
contra los 3 L5X del parque antes de declararlos funcionales.

**Patrones codificados:**
1. `splice_transition` — MAJ→MAS→MAJ (transición controlada de empalme)
2. `gear_chain` — MAG con master tag (acoplamiento master-slave)
3. `servo_on_off_cycle` — MSO+MSF co-ocurrentes (init/shutdown)
4. `homing_sequence` — MAH (homing) ± verificación
5. `axis_lifecycle` — routine con ≥3 de {MAH, MAJ, MAM, MAS} (manager completo)
6. `output_cam_pair` — MAOC+MDOC (cam activate/deactivate)
7. `registration_full` — MASR+MAFR (single+full registration)
8. `cam_profile_mgmt` — MCCP+MCSV (cam profile compute+evaluate)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .tokenizer import tokenize_rll
from .tokenizer.st_tokenizer import tokenize_st

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MotionPattern:
    """Definición de un pattern de composición motion."""

    name: str            # ID corto, ej "splice_transition"
    full_name: str       # nombre legible
    description: str
    references: tuple[str, ...] = ()


@dataclass
class MotionPatternMatch:
    """Match concreto de un pattern en una routine del proyecto."""

    pattern: MotionPattern
    location: str          # path canónico (Programs/X/Routines/Y o AOIs/Z/Routines/W)
    backing_tag: str = ""  # axis (operand 0) si aplica
    instructions: list[str] = field(default_factory=list)  # ops matched, en orden
    rungs: list[int] = field(default_factory=list)         # rungs involucrados
    confidence: float = 1.0
    evidence: str = ""

    def __repr__(self) -> str:
        return (f"MotionPatternMatch({self.pattern.name} {self.backing_tag} "
                f"@ {self.location} conf={self.confidence:.2f})")


# ──────────────────────────────────────────────────────────────────────
# Catálogo de patterns
# ──────────────────────────────────────────────────────────────────────


PATTERN_SPLICE_TRANSITION = MotionPattern(
    name="splice_transition",
    full_name="Splice Transition (MAJ→MAS→MAJ)",
    description=(
        "Transición controlada típica de empalme: el eje arranca con MAJ "
        "(jog libre, velocidad inicial), se detiene con MAS al evento de "
        "splice, y vuelve a arrancar con MAJ (o se sincroniza con MAG) a "
        "la velocidad final del rollo nuevo. Patrón canónico Diatec."
    ),
    references=("Rockwell pub MOTION-RM002 — MAJ/MAS instructions",),
)


PATTERN_GEAR_CHAIN = MotionPattern(
    name="gear_chain",
    full_name="Gear Chain (Master-Slave acoplamiento)",
    description=(
        "Eje slave acoplado a master vía MAG (Motion Axis Gear). Implementa "
        "sincronización a ratio constante. Si aparece MAG→MAG en la misma "
        "routine, indica re-engranaje dinámico (cambio de ratio en runtime, "
        "típico en líneas con velocidad variable)."
    ),
    references=("Rockwell pub MOTION-RM002 — MAG instruction",),
)


PATTERN_SERVO_ON_OFF = MotionPattern(
    name="servo_on_off_cycle",
    full_name="Servo On/Off Cycle (MSO+MSF)",
    description=(
        "Ciclo de habilitación/deshabilitación del servo. MSO (Motion Servo "
        "On) cierra el loop de control; MSF (Motion Servo Off) lo abre. "
        "Su co-ocurrencia en una misma routine indica un manager de estado "
        "del eje (init + shutdown bajo condiciones de fault o E-stop)."
    ),
    references=("Rockwell pub MOTION-RM002 — MSO/MSF instructions",),
)


PATTERN_HOMING_SEQUENCE = MotionPattern(
    name="homing_sequence",
    full_name="Homing Sequence",
    description=(
        "Secuencia de homing del eje. MAH (Motion Axis Home) inicia el "
        "comando de búsqueda de referencia. Si aparece junto a MAJ/MAS, "
        "indica un manager completo con jog manual de aproximación + "
        "homing automático."
    ),
    references=("Rockwell pub MOTION-RM002 — MAH instruction; pub MOTION-UM001 sec Homing",),
)


PATTERN_AXIS_LIFECYCLE = MotionPattern(
    name="axis_lifecycle",
    full_name="Axis Lifecycle Manager (≥3 de {MAH, MAJ, MAM, MAS})",
    description=(
        "Routine que orquesta el ciclo completo de un eje: homing (MAH), "
        "movimiento manual (MAJ/MAM), parada (MAS). Cuando ≥3 de estas "
        "ops aparecen en la misma routine, suele ser el axis manager / "
        "AOI tipo AxisBlock que centraliza todos los comandos de un eje."
    ),
    references=("Rockwell pub MOTION-RM002 — overview Axis Manager",),
)


PATTERN_OUTPUT_CAM_PAIR = MotionPattern(
    name="output_cam_pair",
    full_name="Output Cam Pair (MAOC+MDOC)",
    description=(
        "Par activate/deactivate del Output Cam. MAOC (Motion Arm Output "
        "Cam) habilita la generación de pulsos de salida coordinados con "
        "la posición del eje; MDOC los desarma. Su co-ocurrencia indica "
        "control encoder de glue gun, label, knife, o similares."
    ),
    references=("Rockwell pub MOTION-RM002 — MAOC/MDOC instructions",),
)


PATTERN_REGISTRATION_FULL = MotionPattern(
    name="registration_full",
    full_name="Registration Full (MASR+MAFR)",
    description=(
        "Suite completa de registration. MASR (Motion Arm Single "
        "Registration) arma una captura puntual; MAFR (Motion Arm Full "
        "Registration) arma captura continua. Su co-ocurrencia indica "
        "lógica de tracking de marca de registro (mark-to-mark sync)."
    ),
    references=("Rockwell pub MOTION-RM002 — MASR/MAFR instructions",),
)


PATTERN_CAM_PROFILE_MGMT = MotionPattern(
    name="cam_profile_mgmt",
    full_name="Cam Profile Management (MCCP+MCSV)",
    description=(
        "Gestión runtime de cam profiles. MCCP (Motion Calculate Cam "
        "Profile) computa el cam profile desde un array de puntos; MCSV "
        "(Motion Calculate Slave Value) evalúa el slave value en una "
        "coordenada master arbitraria. Su co-ocurrencia indica un cam "
        "dinámico (recipe-driven, sin gear ratio fijo)."
    ),
    references=("Rockwell pub MOTION-RM002 — MCCP/MCSV instructions",),
)


ALL_PATTERNS: tuple[MotionPattern, ...] = (
    PATTERN_SPLICE_TRANSITION,
    PATTERN_GEAR_CHAIN,
    PATTERN_SERVO_ON_OFF,
    PATTERN_HOMING_SEQUENCE,
    PATTERN_AXIS_LIFECYCLE,
    PATTERN_OUTPUT_CAM_PAIR,
    PATTERN_REGISTRATION_FULL,
    PATTERN_CAM_PROFILE_MGMT,
)


_MOTION_OPS = frozenset((
    "MAJ", "MAM", "MAS", "MAH", "MAG", "MAOC", "MAPC", "MASR", "MAFR",
    "MAR", "MSO", "MSF", "MAW", "MDW", "MDO", "MDS", "MDF", "MDR",
    "MATC", "MAT", "MCD", "MCSV", "MCCP", "MGS", "MGSD", "MGSR", "MGSP",
    "MDOC",
))


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def detect_motion_patterns(project: "Project") -> list[MotionPatternMatch]:
    """Detecta todos los motion patterns del catálogo en el proyecto.

    Iterates over Routines (programs + AOIs), tokeniza, ejecuta cada
    detector. Devuelve list ordenada por confidence desc + pattern.name.
    """
    routines_data = list(_iter_routines_with_motion(project))
    matches: list[MotionPatternMatch] = []
    matches.extend(_detect_splice_transition(routines_data))
    matches.extend(_detect_gear_chain(routines_data))
    matches.extend(_detect_servo_on_off(routines_data))
    matches.extend(_detect_homing_sequence(routines_data))
    matches.extend(_detect_axis_lifecycle(routines_data))
    matches.extend(_detect_output_cam_pair(routines_data))
    matches.extend(_detect_registration_full(routines_data))
    matches.extend(_detect_cam_profile_mgmt(routines_data))

    matches.sort(key=lambda m: (-m.confidence, m.pattern.name, m.location))
    return matches


def motion_patterns_to_markdown(
    project: "Project",
    matches: list[MotionPatternMatch],
) -> str:
    """Genera reporte Markdown de los patterns detectados."""
    from collections import Counter

    name = project.identity.target_name if project.identity else "<unknown>"
    by_pattern = Counter(m.pattern.name for m in matches)

    lines: list[str] = []
    lines.append(f"# Motion Patterns — {name}")
    lines.append("")
    lines.append(f"**Total matches:** {len(matches)} ({len(by_pattern)} patterns activados)")
    lines.append("")
    lines.append("## Por pattern (count)")
    lines.append("")
    for kind, cnt in by_pattern.most_common():
        meta = next((p for p in ALL_PATTERNS if p.name == kind), None)
        full = meta.full_name if meta else kind
        lines.append(f"- `{kind}` ({cnt}) — {full}")
    lines.append("")
    lines.append("## Detalle")
    cur = None
    for m in matches:
        if m.pattern.name != cur:
            cur = m.pattern.name
            lines.append("")
            lines.append(f"### `{m.pattern.name}` — {m.pattern.full_name}")
            lines.append("")
            lines.append(f"_{m.pattern.description}_")
            lines.append("")
        lines.append(
            f"- **{m.location}**"
            + (f" axis=`{m.backing_tag}`" if m.backing_tag else "")
            + f" conf={m.confidence:.2f}"
        )
        lines.append(f"  - ops: `{' → '.join(m.instructions[:10])}`"
                     + ("..." if len(m.instructions) > 10 else ""))
        if m.rungs:
            lines.append(f"  - rungs: {m.rungs[:8]}")
        if m.evidence:
            lines.append(f"  - _evidence:_ {m.evidence}")
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────
# Iteración de routines con motion
# ──────────────────────────────────────────────────────────────────────


@dataclass
class _RoutineMotionInfo:
    """Estructura interna con la info motion de una routine, normalizada."""

    location: str
    instructions: list[tuple[int, str, str]]  # (rung_n, op, backing)


def _iter_routines_with_motion(project: "Project"):
    """Itera todas las routines (programs + AOIs) y emite RoutineMotionInfo
    para las que contienen ≥1 motion op.
    """
    # Programs
    for r in project.routines:
        if not r.code:
            continue
        info = _routine_motion_info(
            code=r.code,
            rtype=r.type,
            location=f"Programs/{r.program}/Routines/{r.name}",
        )
        if info.instructions:
            yield info

    # AOIs
    for a in project.aois:
        for rname, r in a.routines.items():
            if not r.code:
                continue
            info = _routine_motion_info(
                code=r.code,
                rtype=r.type,
                location=f"AOIs/{a.name}/Routines/{rname}",
            )
            if info.instructions:
                yield info


def _routine_motion_info(code: str, rtype: str, location: str) -> _RoutineMotionInfo:
    info = _RoutineMotionInfo(location=location, instructions=[])
    if rtype == "RLL":
        rungs = tokenize_rll(code)
    elif rtype == "ST":
        rungs = tokenize_st(code)
    else:
        return info
    for rung in rungs:
        for inst in rung.instructions:
            if inst.operator in _MOTION_OPS:
                backing = inst.operands[0].text if inst.operands else ""
                info.instructions.append((rung.number, inst.operator, backing))
    return info


def _group_by_backing(info: _RoutineMotionInfo) -> dict[str, list[tuple[int, str]]]:
    """Agrupa instrucciones por backing tag (axis)."""
    by_bk: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for rung_n, op, backing in info.instructions:
        by_bk[backing].append((rung_n, op))
    return by_bk


# ──────────────────────────────────────────────────────────────────────
# Detectores individuales
# ──────────────────────────────────────────────────────────────────────


def _detect_splice_transition(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MAJ→MAS→MAJ o MAJ→MAS o MAJ→MAG en mismo backing tag.

    Confidence:
    - 1.00: secuencia completa MAJ→MAS→MAJ detectada por backing
    - 0.85: MAJ→MAS o MAJ→MAG (transición parcial)
    """
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            rungs = [rn for rn, _ in ops]
            # Buscar MAJ→MAS→MAJ
            full_match = False
            for i in range(len(ops_only) - 2):
                if (ops_only[i], ops_only[i+1], ops_only[i+2]) == ("MAJ", "MAS", "MAJ"):
                    full_match = True
                    break
            if full_match:
                out.append(MotionPatternMatch(
                    pattern=PATTERN_SPLICE_TRANSITION,
                    location=r.location,
                    backing_tag=backing,
                    instructions=ops_only,
                    rungs=sorted(set(rungs)),
                    confidence=1.0,
                    evidence="MAJ→MAS→MAJ encadenado",
                ))
                continue
            # Partial: MAJ→MAS o MAJ→MAG
            for i in range(len(ops_only) - 1):
                pair = (ops_only[i], ops_only[i+1])
                if pair in (("MAJ", "MAS"), ("MAJ", "MAG")):
                    out.append(MotionPatternMatch(
                        pattern=PATTERN_SPLICE_TRANSITION,
                        location=r.location,
                        backing_tag=backing,
                        instructions=ops_only,
                        rungs=sorted(set(rungs)),
                        confidence=0.85,
                        evidence=f"transición parcial {pair[0]}→{pair[1]}",
                    ))
                    break
    return out


def _detect_gear_chain(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MAG presente. MAG→MAG en misma routine = re-engranaje.

    Confidence:
    - 1.00: MAG→MAG (re-engranaje dinámico)
    - 0.7: MAG single
    """
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            mag_count = ops_only.count("MAG")
            if mag_count == 0:
                continue
            rungs = [rn for rn, _ in ops]
            if mag_count >= 2:
                out.append(MotionPatternMatch(
                    pattern=PATTERN_GEAR_CHAIN,
                    location=r.location,
                    backing_tag=backing,
                    instructions=ops_only,
                    rungs=sorted(set(rungs)),
                    confidence=1.0,
                    evidence=f"{mag_count} MAGs en misma routine — re-engranaje dinámico",
                ))
            else:
                out.append(MotionPatternMatch(
                    pattern=PATTERN_GEAR_CHAIN,
                    location=r.location,
                    backing_tag=backing,
                    instructions=ops_only,
                    rungs=sorted(set(rungs)),
                    confidence=0.7,
                    evidence="1 MAG — gear ratio constante",
                ))
    return out


def _detect_servo_on_off(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MSO+MSF co-ocurrentes en misma routine."""
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            has_mso = "MSO" in ops_only
            has_msf = "MSF" in ops_only
            if not (has_mso and has_msf):
                continue
            rungs = [rn for rn, _ in ops]
            out.append(MotionPatternMatch(
                pattern=PATTERN_SERVO_ON_OFF,
                location=r.location,
                backing_tag=backing,
                instructions=ops_only,
                rungs=sorted(set(rungs)),
                confidence=1.0,
                evidence="MSO+MSF presentes — manager de estado",
            ))
    return out


def _detect_homing_sequence(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MAH presente."""
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            if "MAH" not in ops_only:
                continue
            rungs = [rn for rn, _ in ops]
            # confidence más alta si MAH+MAS o MAH+MAJ co-ocurren
            extra = sum(1 for op in ("MAS", "MAJ") if op in ops_only)
            confidence = 0.8 if extra == 0 else 1.0
            out.append(MotionPatternMatch(
                pattern=PATTERN_HOMING_SEQUENCE,
                location=r.location,
                backing_tag=backing,
                instructions=ops_only,
                rungs=sorted(set(rungs)),
                confidence=confidence,
                evidence=f"MAH presente, +{extra} co-ops manager"
                         if extra else "MAH solo (homing puro)",
            ))
    return out


def _detect_axis_lifecycle(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """Routine con ≥3 de {MAH, MAJ, MAM, MAS}."""
    LIFECYCLE = {"MAH", "MAJ", "MAM", "MAS"}
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            present = LIFECYCLE & set(ops_only)
            if len(present) < 3:
                continue
            rungs = [rn for rn, _ in ops]
            confidence = 0.8 + 0.05 * (len(present) - 3)
            confidence = min(1.0, confidence)
            out.append(MotionPatternMatch(
                pattern=PATTERN_AXIS_LIFECYCLE,
                location=r.location,
                backing_tag=backing,
                instructions=ops_only,
                rungs=sorted(set(rungs)),
                confidence=confidence,
                evidence=f"{len(present)}/4 lifecycle ops: {sorted(present)}",
            ))
    return out


def _detect_output_cam_pair(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MAOC+MDOC co-ocurrentes."""
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            if not ("MAOC" in ops_only and "MDOC" in ops_only):
                continue
            rungs = [rn for rn, _ in ops]
            out.append(MotionPatternMatch(
                pattern=PATTERN_OUTPUT_CAM_PAIR,
                location=r.location,
                backing_tag=backing,
                instructions=ops_only,
                rungs=sorted(set(rungs)),
                confidence=1.0,
                evidence="MAOC+MDOC presentes — output cam pair",
            ))
    return out


def _detect_registration_full(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MASR+MAFR co-ocurrentes."""
    out: list[MotionPatternMatch] = []
    for r in routines:
        for backing, ops in _group_by_backing(r).items():
            if not backing:
                continue
            ops_only = [op for _, op in ops]
            if not ("MASR" in ops_only and "MAFR" in ops_only):
                continue
            rungs = [rn for rn, _ in ops]
            out.append(MotionPatternMatch(
                pattern=PATTERN_REGISTRATION_FULL,
                location=r.location,
                backing_tag=backing,
                instructions=ops_only,
                rungs=sorted(set(rungs)),
                confidence=1.0,
                evidence="MASR+MAFR presentes — registration full",
            ))
    return out


def _detect_cam_profile_mgmt(routines: list[_RoutineMotionInfo]) -> list[MotionPatternMatch]:
    """MCCP+MCSV co-ocurrentes (en general no comparten backing)."""
    out: list[MotionPatternMatch] = []
    # Para este pattern, MCCP/MCSV pueden tener distintos backing — buscamos
    # co-ocurrencia en routine, no en mismo axis.
    for r in routines:
        ops_only = [op for _, op, _ in r.instructions]
        rungs = sorted({rn for rn, _, _ in r.instructions})
        if not ("MCCP" in ops_only and "MCSV" in ops_only):
            continue
        # backing = primer MCCP backing
        backing = ""
        for _, op, b in r.instructions:
            if op == "MCCP":
                backing = b
                break
        out.append(MotionPatternMatch(
            pattern=PATTERN_CAM_PROFILE_MGMT,
            location=r.location,
            backing_tag=backing,
            instructions=ops_only,
            rungs=rungs,
            confidence=1.0,
            evidence="MCCP+MCSV presentes — cam profile dinámico",
        ))
    return out
