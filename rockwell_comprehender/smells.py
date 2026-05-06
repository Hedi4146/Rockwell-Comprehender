"""Smells — detector de architecture smells y best-practice violations.

Sprint 4 (Asesor proactivo). Esta capa convierte al toolkit de "responde
lo que pregunto" a "sugiere lo que debo revisar". Identifica patrones
que típicamente indican problemas de mantenibilidad, errores latentes o
desviaciones de mejores prácticas Rockwell.

Reglas en C.1 (5 iniciales — detección estructural):
1. OTL/OTU sin pareja — latch sin unlatch o viceversa
2. AOIs con muchos parámetros (>30) — smell de god-object
3. Routines vacías — code vacío, solo NOP/AFI, o solo whitespace
4. Programs sin task asignado — código que nunca se scanea
5. Controller-scope mismatch — tag controller-scope que solo se usa
   en un único program (candidato a program-local)

Reglas extendidas en C.2 (best practices Rockwell, NotebookLM-curated):
ver `_BEST_PRACTICE_RULES`.

Stack mínimo (DT-008): solo stdlib + estructuras del modelo +
`project.references_of()` del tracer v0.2. Sin dependencias nuevas.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class Smell:
    """Un smell detectado en el proyecto."""

    kind: str          # ID de la regla, ej "otl_otu_unpaired"
    severity: str      # "high" | "medium" | "low"
    target_kind: str   # "tag" | "aoi" | "routine" | "program"
    target_name: str
    location: str      # path canónico (Programs/X/Routines/Y, AOIs/Z, ...)
    description: str   # explicación legible
    evidence: str = "" # detalle factual (counts, locations, etc.)
    rule_source: str = "C.1"  # "C.1" (estructural) | "C.2" (best practice)

    def __repr__(self) -> str:
        return f"Smell({self.kind} {self.severity} {self.target_name})"


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def detect_smells(project: "Project") -> list[Smell]:
    """Ejecuta todas las reglas de C.1 + C.2 contra el proyecto.

    Returns:
        Lista de Smells ordenada por severity desc + kind.
    """
    smells: list[Smell] = []

    # C.1 — reglas estructurales
    smells.extend(_detect_otl_otu_unpaired(project))
    smells.extend(_detect_aoi_too_many_params(project))
    smells.extend(_detect_empty_routines(project))
    smells.extend(_detect_programs_without_task(project))
    smells.extend(_detect_controller_scope_mismatch(project))

    # C.2 — best practices Rockwell (curado vía NotebookLM)
    smells.extend(_detect_motion_no_error_handling(project))
    smells.extend(_detect_naming_aoi_not_pascal(project))
    smells.extend(_detect_disabled_programs(project))
    smells.extend(_detect_aoi_not_invoked(project))
    smells.extend(_detect_routine_jsr_to_self(project))
    smells.extend(_detect_st_transitional_without_oneshot(project))
    smells.extend(_detect_tag_naming_legacy_lowercase(project))
    smells.extend(_detect_safety_program_naming(project))
    smells.extend(_detect_task_without_programs(project))
    smells.extend(_detect_routines_without_main(project))

    severity_order = {"high": 0, "medium": 1, "low": 2}
    smells.sort(key=lambda s: (severity_order.get(s.severity, 3), s.kind, s.target_name))
    return smells


def smells_to_markdown(project: "Project", smells: list[Smell]) -> str:
    """Genera un reporte Markdown legible de los smells encontrados."""
    from collections import Counter

    name = project.identity.target_name if project.identity else "<unknown>"
    lines: list[str] = []
    lines.append(f"# Smell report — {name}")
    lines.append("")
    lines.append(f"**Total smells:** {len(smells)}")
    by_severity = Counter(s.severity for s in smells)
    by_kind = Counter(s.kind for s in smells)
    lines.append("")
    lines.append("## Por severidad")
    for sev in ("high", "medium", "low"):
        if by_severity[sev]:
            lines.append(f"- **{sev}:** {by_severity[sev]}")
    lines.append("")
    lines.append("## Por regla (count)")
    for kind, cnt in by_kind.most_common():
        lines.append(f"- `{kind}`: {cnt}")
    lines.append("")
    lines.append("## Detalle")
    cur_kind = None
    for s in smells:
        if s.kind != cur_kind:
            cur_kind = s.kind
            lines.append("")
            lines.append(f"### `{s.kind}` ({s.severity}, {s.rule_source})")
            lines.append("")
        lines.append(f"- **{s.target_kind}** `{s.target_name}` @ `{s.location}`")
        lines.append(f"  - {s.description}")
        if s.evidence:
            lines.append(f"  - _evidence:_ {s.evidence}")
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────
# C.1 — Reglas estructurales (5 iniciales)
# ──────────────────────────────────────────────────────────────────────


def _detect_otl_otu_unpaired(project: "Project") -> list[Smell]:
    """Tags con OTL pero sin OTU (o viceversa) en cualquier parte del proyecto.

    Severidad: high — un OTL sin OTU genera un bit que se queda enclavado
    sin posibilidad de reset; un OTU sin OTU previo es código muerto.
    """
    if not project.db_path:
        return []
    project._ensure_xref_built()
    import sqlite3 as _sql
    conn = _sql.connect(project.db_path)
    try:
        cur = conn.cursor()
        otl_rows = cur.execute(
            "SELECT DISTINCT operand FROM xref WHERE operator='OTL' AND operand_kind='tag'"
        ).fetchall()
        otu_rows = cur.execute(
            "SELECT DISTINCT operand FROM xref WHERE operator='OTU' AND operand_kind='tag'"
        ).fetchall()
    finally:
        conn.close()

    otl_tags = {r[0] for r in otl_rows}
    otu_tags = {r[0] for r in otu_rows}

    smells: list[Smell] = []
    for t in sorted(otl_tags - otu_tags):
        smells.append(Smell(
            kind="otl_without_otu",
            severity="high",
            target_kind="tag",
            target_name=t,
            location="(global)",
            description="Tag tiene OTL (latch) pero no aparece OTU (unlatch) en ningún rung — bit puede quedar enclavado sin reset.",
            evidence=f"OTL detectado, OTU ausente para '{t}'",
        ))
    for t in sorted(otu_tags - otl_tags):
        smells.append(Smell(
            kind="otu_without_otl",
            severity="medium",
            target_kind="tag",
            target_name=t,
            location="(global)",
            description="Tag tiene OTU (unlatch) pero ningún OTL — el unlatch es no-op (bit ya estaría en 0 sin OTL previo).",
            evidence=f"OTU detectado, OTL ausente para '{t}'",
        ))
    return smells


def _detect_aoi_too_many_params(project: "Project", threshold: int = 30) -> list[Smell]:
    """AOIs con >threshold parameters — smell de god-object.

    Severidad: medium — AOIs con muchos parámetros tienden a violar SRP,
    son difíciles de invocar correctamente, y suelen mezclar responsabilidades.
    """
    smells = []
    for aoi in project.aois:
        n = len(aoi.parameters)
        if n > threshold:
            smells.append(Smell(
                kind="aoi_too_many_params",
                severity="medium",
                target_kind="aoi",
                target_name=aoi.name,
                location=f"AOIs/{aoi.name}",
                description=f"AOI con {n} parameters (>{threshold}) — smell de god-object. Considerar descomposición funcional.",
                evidence=f"{n} parameters total",
            ))
    return smells


def _detect_empty_routines(project: "Project") -> list[Smell]:
    """Routines con code vacío o trivial (solo NOP/AFI/whitespace).

    Severidad: low — puede ser intencional (placeholder) pero es ruido si
    se acumula. Excluye fault_routines (a menudo intencionalmente vacías).
    """
    fault_routines = {p.fault_routine for p in project.programs if p.fault_routine}

    smells: list[Smell] = []
    for r in project.routines:
        if r.name in fault_routines:
            continue
        code = (r.code or "").strip()
        if not code:
            smells.append(Smell(
                kind="routine_empty",
                severity="low",
                target_kind="routine",
                target_name=r.name,
                location=f"Programs/{r.program}/Routines/{r.name}",
                description="Routine sin código (vacía).",
                evidence="code is empty",
            ))
            continue
        # Code trivial: solo NOP/AFI/comentarios
        # Limpiar comentarios primero
        clean = re.sub(r"\(\*.*?\*\)", "", code, flags=re.DOTALL)
        clean = re.sub(r"//[^\n]*", "", clean)
        clean = re.sub(r"\s+", "", clean)
        # Considerar trivial si solo contiene NOP() y AFI()
        trivial_pattern = re.compile(r"^(NOP\(\)|AFI\(\)|;)*$", re.IGNORECASE)
        if trivial_pattern.match(clean):
            smells.append(Smell(
                kind="routine_trivial",
                severity="low",
                target_kind="routine",
                target_name=r.name,
                location=f"Programs/{r.program}/Routines/{r.name}",
                description="Routine con solo NOP/AFI — sin lógica productiva.",
                evidence=f"code reducido a: {clean[:60]!r}",
            ))
    return smells


def _detect_programs_without_task(project: "Project") -> list[Smell]:
    """Programs no asignados a ninguna task — nunca se scanean.

    Severidad: high — código que nunca se ejecuta es por definición código
    muerto (a menos que sea intencionalmente reservado para futuro).
    """
    scheduled = set()
    for t in project.tasks:
        scheduled.update(t.scheduled_programs)

    smells = []
    for p in project.programs:
        if p.name not in scheduled:
            smells.append(Smell(
                kind="program_unscheduled",
                severity="high",
                target_kind="program",
                target_name=p.name,
                location=f"Programs/{p.name}",
                description="Program no asignado a ninguna task — su código nunca se scanea.",
                evidence=f"Programs scheduled: {sorted(scheduled)[:5]}{'...' if len(scheduled) > 5 else ''}",
            ))
    return smells


def _detect_controller_scope_mismatch(project: "Project", sample: int = 50) -> list[Smell]:
    """Tags controller-scope cuyas references vienen de un solo program.

    Severidad: low — el tag funcionaría igual como program-local. Mantenerlo
    como controller-scope es desperdicio de namespace global y aumenta
    superficie de cambio entre programs.

    Limitado a `sample` tags para evitar costo computacional excesivo.
    """
    SKIP_DT = ("AXIS_", "MOTION_GROUP", "COORDINATE_SYSTEM", "TASK", "PROGRAM",
               "ROUTINE", "MODULE", "MESSAGE", "CONNECTION_STATUS", "ALARM")
    controller_tags = [t for t in project.tags if t.scope == "controller"]
    analyzable = [
        t for t in controller_tags
        if not any((t.datatype or "").startswith(s) for s in SKIP_DT)
        and not (getattr(t, 'motion_module', None))
    ][:sample]

    smells = []
    for t in analyzable:
        try:
            refs = project.references_of(t.name)
        except Exception:
            continue
        if not refs:
            continue  # Tag huérfano — otro tipo de smell, no scope mismatch
        # Extraer programs de cada ref
        programs_seen = set()
        for r in refs:
            loc = r.location
            if loc.startswith("Programs/"):
                parts = loc.split("/")
                if len(parts) >= 2:
                    programs_seen.add(parts[1])
        if len(programs_seen) == 1:
            prog = next(iter(programs_seen))
            smells.append(Smell(
                kind="tag_scope_mismatch",
                severity="low",
                target_kind="tag",
                target_name=t.name,
                location=f"controller-scope (only used in Programs/{prog})",
                description=f"Tag controller-scope solo usado en program '{prog}' — candidato a program-local para reducir namespace global.",
                evidence=f"references_of: {len(refs)} hits, all in Programs/{prog}",
            ))
    return smells


# ──────────────────────────────────────────────────────────────────────
# C.2 — Best practices Rockwell (curado vía NotebookLM 2026-05-06)
# Implementadas como reglas concretas. La curación NotebookLM proveyó
# justificación bibliográfica (pub 1756-RM003, MOTION-RM002).
# ──────────────────────────────────────────────────────────────────────


def _detect_motion_no_error_handling(project: "Project") -> list[Smell]:
    """Instrucciones motion (MAJ/MAM/MAS/MAH/...) cuyo motion_control bit .ER
    nunca se lee — falta error handling explícito.

    Severidad: medium — best practice Rockwell (MOTION-RM002): siempre
    inspeccionar .ER y .ERR del motion_control struct para detectar fallos
    del comando antes de re-disparar.
    """
    if not project.db_path:
        return []
    project._ensure_xref_built()
    import sqlite3 as _sql
    conn = _sql.connect(project.db_path)
    try:
        cur = conn.cursor()
        # Motion ops que escriben motion_control (el 2do operando típicamente)
        motion_ops = ("MAJ", "MAM", "MAS", "MAH", "MAG", "MAOC", "MAPC",
                      "MASR", "MAFR", "MAR", "MSO", "MSF", "MAW", "MDW")
        placeholders = ",".join("?" * len(motion_ops))
        # Tags que aparecen como motion_control (write con kind=tag, instr motion)
        rows = cur.execute(
            f"SELECT DISTINCT operand FROM xref "
            f"WHERE operator IN ({placeholders}) AND usage='write' AND operand_kind='tag'",
            motion_ops,
        ).fetchall()
    finally:
        conn.close()

    motion_control_tags = {r[0] for r in rows}

    # Para cada motion_control, verificar si .ER se lee en algún rung
    smells = []
    for tag in sorted(motion_control_tags):
        # ¿Existe lectura de tag.ER en xref?
        try:
            er_refs = project.references_of(f"{tag}.ER")
        except Exception:
            continue
        if not er_refs:
            smells.append(Smell(
                kind="motion_no_error_check",
                severity="medium",
                rule_source="C.2",
                target_kind="tag",
                target_name=tag,
                location="(global)",
                description=f"Motion control tag '{tag}' usado en motion instruction pero el bit .ER nunca se lee — falta error handling explícito.",
                evidence="Best practice Rockwell MOTION-RM002: inspeccionar .ER tras cada motion instruction.",
            ))
    return smells


def _detect_naming_aoi_not_pascal(project: "Project") -> list[Smell]:
    """AOIs cuyo nombre no sigue PascalCase (convención Rockwell para AOIs).

    Severidad: low — best practice de naming convention (1756-RM094 style guide).
    Ignora prefijos comunes de empresa (AHT_, raC_, AOI_).
    """
    smells = []
    for aoi in project.aois:
        name = aoi.name
        # Strip prefixes
        stripped = re.sub(r"^(AHT_|raC_|AOI_)", "", name)
        if not stripped:
            continue
        # Debe empezar con uppercase y no contener camelCase con guión bajo intercalado
        if not stripped[0].isupper():
            smells.append(Smell(
                kind="aoi_naming_lowercase_start",
                severity="low",
                rule_source="C.2",
                target_kind="aoi",
                target_name=name,
                location=f"AOIs/{name}",
                description="AOI no inicia con uppercase tras strip de prefijo — best practice Rockwell: PascalCase.",
                evidence=f"name stripped: '{stripped}'",
            ))
    return smells


def _detect_disabled_programs(project: "Project") -> list[Smell]:
    """Programs con flag disabled=True — código que está intencionalmente
    desactivado pero queda en el L5X.

    Severidad: medium — si está disabled debe documentarse en el código por
    qué; si no se documenta, es legacy candidato a remover.
    """
    smells = []
    for p in project.programs:
        if getattr(p, "disabled", False):
            smells.append(Smell(
                kind="program_disabled",
                severity="medium",
                rule_source="C.2",
                target_kind="program",
                target_name=p.name,
                location=f"Programs/{p.name}",
                description="Program marcado como Disabled — no se ejecuta. Documentar intención o remover.",
                evidence="disabled=True",
            ))
    return smells


def _detect_aoi_not_invoked(project: "Project") -> list[Smell]:
    """AOIs definidas que no se invocan en ningún rung del proyecto.

    Severidad: medium — código muerto. Best practice: eliminar AOIs no
    usadas para reducir superficie del proyecto y confusión.
    """
    if not project.db_path:
        return []
    project._ensure_xref_built()
    import sqlite3 as _sql
    conn = _sql.connect(project.db_path)
    try:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT DISTINCT operator FROM xref"
        ).fetchall()
    finally:
        conn.close()
    invoked_ops = {r[0] for r in rows}

    smells = []
    for aoi in project.aois:
        if aoi.name not in invoked_ops:
            smells.append(Smell(
                kind="aoi_not_invoked",
                severity="medium",
                rule_source="C.2",
                target_kind="aoi",
                target_name=aoi.name,
                location=f"AOIs/{aoi.name}",
                description="AOI definida pero nunca invocada — código muerto candidato.",
                evidence=f"No aparece como operator en xref",
            ))
    return smells


def _detect_routine_jsr_to_self(project: "Project") -> list[Smell]:
    """Routines que invocan JSR a sí mismas — recursión típicamente no
    intencionada en RLL.

    Severidad: high — JSR recursivo en RLL puede causar stack overflow o
    comportamiento errático según firmware.
    """
    smells = []
    JSR_RE = re.compile(r"\bJSR\(\s*([A-Za-z_]\w*)", re.IGNORECASE)
    for r in project.routines:
        if not r.code:
            continue
        for m in JSR_RE.finditer(r.code):
            target = m.group(1)
            if target == r.name:
                smells.append(Smell(
                    kind="routine_jsr_self",
                    severity="high",
                    rule_source="C.2",
                    target_kind="routine",
                    target_name=r.name,
                    location=f"Programs/{r.program}/Routines/{r.name}",
                    description="Routine invoca JSR a sí misma — recursión RLL, potencial stack overflow.",
                    evidence=f"JSR({target}) detectado en su propio code",
                ))
                break
    return smells


def _detect_st_transitional_without_oneshot(project: "Project") -> list[Smell]:
    """Instrucciones transicionales (MAM/MAS/MDO/...) en código ST sin
    estar dentro de un IF disparado por One-Shot.

    Severidad: high — gotcha crítico de pub 1756-RM003 cap 24: en ST toda
    instrucción se comporta como EnableIn=true cada scan, lo que re-dispara
    transicionales en cada barrido. Debe usarse OSR/OSRI + IF.
    """
    smells = []
    transitional = ("MAM", "MAS", "MDO", "MDS", "MDF", "MDR", "ABL", "ARL")
    pattern = re.compile(
        rf"\b({'|'.join(transitional)})\s*\(",
        re.IGNORECASE,
    )

    for r in project.routines:
        if not r.code or r.type != "ST":
            continue
        # Buscar transicionales no precedidos por IF dentro de N caracteres
        for m in pattern.finditer(r.code):
            start = m.start()
            # Heurística: ¿hay un IF en los 200 chars previos (mismo bloque)?
            window_start = max(0, start - 300)
            window = r.code[window_start:start]
            if "IF " not in window.upper():
                op = m.group(1).upper()
                smells.append(Smell(
                    kind="st_transitional_no_oneshot",
                    severity="high",
                    rule_source="C.2",
                    target_kind="routine",
                    target_name=r.name,
                    location=f"Programs/{r.program}/Routines/{r.name}",
                    description=f"Instrucción transicional {op} en ST sin IF previo — re-disparo cada scan probable.",
                    evidence=f"snippet: ...{r.code[max(0,start-30):start+50]!r}",
                ))
                break  # 1 smell por routine para no inundar
    return smells


def _detect_tag_naming_legacy_lowercase(project: "Project") -> list[Smell]:
    """Tags scope=controller con naming legacy (todo lowercase, sin
    prefijo identificador HMI_/Cmd_/Hmi_/etc.).

    Severidad: low — best practice: tags controller-scope con prefijo
    semántico (HMI_, M*_, IO_, Cmd_) facilita auditoría y cross-reference.
    """
    smells = []
    legacy_pattern = re.compile(r"^[a-z][a-z_0-9]*$")  # todo lowercase
    for t in project.tags:
        if t.scope != "controller":
            continue
        if (t.datatype or "").startswith(("AXIS_", "MOTION_GROUP")):
            continue
        if legacy_pattern.match(t.name):
            smells.append(Smell(
                kind="tag_naming_legacy_lowercase",
                severity="low",
                rule_source="C.2",
                target_kind="tag",
                target_name=t.name,
                location=f"Tags(controller)/{t.name}",
                description="Tag controller-scope con naming todo lowercase — sin prefijo semántico.",
                evidence=f"name='{t.name}', scope=controller",
            ))
    return smells


def _detect_safety_program_naming(project: "Project") -> list[Smell]:
    """Programs con AOIs CROUT/DCI_* o tags DCS_* pero nombre que no incluye
    'Safety' — best practice GuardLogix: programs de seguridad nombrados
    explícitamente.

    Severidad: medium — naming claro previene mezclar lógica safety con
    standard, lo cual es regulatoriamente requerido en SIL/PLe.
    """
    if not project.db_path:
        return []
    project._ensure_xref_built()
    import sqlite3 as _sql
    conn = _sql.connect(project.db_path)
    try:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT DISTINCT source_location FROM xref "
            "WHERE operator IN ('CROUT', 'DCI_STOP', 'DCI_STOP_TEST_LOCK')"
        ).fetchall()
    finally:
        conn.close()
    safety_locations = [r[0] for r in rows]

    program_with_safety_inst = set()
    for loc in safety_locations:
        if loc.startswith("Programs/"):
            parts = loc.split("/")
            if len(parts) >= 2:
                program_with_safety_inst.add(parts[1])

    smells = []
    for prog_name in program_with_safety_inst:
        if "safety" not in prog_name.lower():
            smells.append(Smell(
                kind="safety_program_naming",
                severity="medium",
                rule_source="C.2",
                target_kind="program",
                target_name=prog_name,
                location=f"Programs/{prog_name}",
                description=f"Program contiene safety instructions (CROUT/DCI_*) pero name no incluye 'Safety' — best practice GuardLogix nombrar explícitamente.",
                evidence=f"safety instr detectadas en Programs/{prog_name}",
            ))
    return smells


def _detect_task_without_programs(project: "Project") -> list[Smell]:
    """Tasks sin scheduled_programs — task definida pero no scanea nada.

    Severidad: low — task vacía es ruido en config, no causa daño pero
    confunde durante audit.
    """
    smells = []
    for t in project.tasks:
        if not t.scheduled_programs:
            smells.append(Smell(
                kind="task_without_programs",
                severity="low",
                rule_source="C.2",
                target_kind="task",
                target_name=t.name,
                location=f"Tasks/{t.name}",
                description="Task definida sin scheduled_programs — no scanea nada.",
                evidence=f"type={t.type}, scheduled_programs=[]",
            ))
    return smells


def _detect_routines_without_main(project: "Project") -> list[Smell]:
    """Programs cuyo main_routine no existe en sus routines.

    Severidad: high — el program no puede ejecutar nada (Studio 5000 normalmente
    no acepta esto, pero L5X exportados pueden contenerlo si hay edición manual).
    """
    routine_names_by_program = defaultdict(set)
    for r in project.routines:
        if r.program:
            routine_names_by_program[r.program].add(r.name)

    smells = []
    for p in project.programs:
        if not p.main_routine:
            continue
        if p.main_routine not in routine_names_by_program.get(p.name, set()):
            smells.append(Smell(
                kind="program_main_routine_missing",
                severity="high",
                rule_source="C.2",
                target_kind="program",
                target_name=p.name,
                location=f"Programs/{p.name}",
                description=f"main_routine='{p.main_routine}' no existe en routines del program.",
                evidence=f"routines disponibles: {sorted(routine_names_by_program.get(p.name, []))[:5]}",
            ))
    return smells
