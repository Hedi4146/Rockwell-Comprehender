"""Tag Dictionary — diccionario semántico de tags (v0.5).

Cierra:
- **Capacidad #6 del Vision** (Roles de tags): de 80% → 95%+
- **Criterio v0.3 ítem 2** (diccionario semántico navegable):
  HmiRollDiameter → "diámetro de rollo, input operador"

Heurística honesta (DT-008 stack mínimo): regex sobre prefijos/sufijos
del name del tag + datatype + scope. Sin embeddings ni LLM externo.

**Roles inferidos:**
- `hmi_input` — input desde HMI (Hmi*, Hmi_*, etc.)
- `setpoint` — referencia/objetivo (*_Setpoint, *_SP, *_Ref)
- `limit` — umbral (*_Limit, *_Min, *_Max, *_Threshold)
- `command` — comando (*_Cmd, *_Command, Start_*, Stop_*)
- `status` — estado/feedback (*_Status, *_State, *_FB, *_Done)
- `enable` — habilitación (*_Enable, *_En, *_Active)
- `reset` — reset (*_Reset, *_Rst, Reset_*)
- `fault` — fault/alarma (*_Fault, *_Alarm, *_Error, _FaultCode)
- `axis_data` — UDT de eje (M*Data, Axis_Data*)
- `motion_control` — motion instruction tag (datatype MOTION_INSTRUCTION)
- `axis_object` — axis tag (datatype AXIS_*)
- `io_input` — entrada I/O (I_*, *_IN, scope con prefijo de slot)
- `io_output` — salida I/O (O_*, *_OUT)
- `internal_aux` — auxiliar interno (aux*, tmp*, scratch*)
- `constant` — constante (constant=True)
- `counter_timer` — TIMER/COUNTER datatype
- `unknown` — no clasificable

API:
    project.classify_tag(tag) -> TagRole
    project.tag_dictionary() -> list[(Tag, TagRole)]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Project, Tag


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class TagRole:
    """Rol semántico inferido de un tag."""

    role: str                      # ID del rol (hmi_input, setpoint, etc.)
    description: str               # traducción humana legible
    confidence: float = 1.0        # 0-1, basado en match heurístico
    matched_pattern: str = ""      # regex/heurística que matcheó

    def __repr__(self) -> str:
        return f"TagRole({self.role} {self.confidence:.2f})"


# ──────────────────────────────────────────────────────────────────────
# Reglas de clasificación (orden = prioridad — primera que matchea gana)
# ──────────────────────────────────────────────────────────────────────


# Cada regla = (role_id, description, name_pattern, datatype_pattern, confidence)
# El primer pattern truthy se aplica; ambos son opcionales.

_RULES: list[tuple[str, str, re.Pattern | None, re.Pattern | None, float]] = [
    # Datatype-driven (alta certeza)
    ("axis_object",
     "Tag de eje (AXIS_*) — referencia a un servo configurado en el motion group",
     None, re.compile(r"^AXIS_", re.IGNORECASE), 1.0),

    ("motion_control",
     "Estructura motion control (MOTION_INSTRUCTION) — bits .EN/.DN/.ER de un comando motion",
     None, re.compile(r"^MOTION_INSTRUCTION$", re.IGNORECASE), 1.0),

    ("counter_timer",
     "Estructura TIMER/COUNTER — .EN/.TT/.DN/.PRE/.ACC para temporización o conteo",
     None, re.compile(r"^(TIMER|COUNTER|CONTROL)$", re.IGNORECASE), 1.0),

    ("motion_group",
     "Motion group (MOTION_GROUP) — agrupador del scheduling motion",
     None, re.compile(r"^MOTION_GROUP$", re.IGNORECASE), 1.0),

    # Name-driven (semántica explícita en nombre)
    ("hmi_input",
     "Input desde HMI — valor escrito por el operador en pantalla",
     re.compile(r"^Hmi[A-Z_]", re.IGNORECASE), None, 0.95),

    ("hmi_input",
     "Input desde HMI (sufijo _Hmi)",
     re.compile(r"_Hmi[A-Za-z]*$", re.IGNORECASE), None, 0.85),

    ("setpoint",
     "Setpoint / referencia objetivo — valor target hacia el que se controla",
     re.compile(r"(_Setpoint|_SP|_Ref|_Target)$", re.IGNORECASE), None, 0.90),

    ("limit",
     "Límite / umbral — valor de comparación para alarma o clamp",
     re.compile(r"(_Limit|_Min|_Max|_Threshold|_LowLim|_HiLim)$", re.IGNORECASE), None, 0.90),

    ("command",
     "Comando (start/stop/exec) — pulso de inicio o detención de acción",
     re.compile(r"(_Cmd|_Command|_Start|_Stop|_Exec|_Run)$|^(Start_|Stop_|Cmd_|Run_)", re.IGNORECASE), None, 0.85),

    ("reset",
     "Reset / clear — bit que resetea fault, alarma o estado",
     re.compile(r"(_Reset|_Rst|_Clear|_Clr)$|^(Reset_|Clr_|Clear_)", re.IGNORECASE), None, 0.90),

    ("fault",
     "Fault / alarma / error — bit de detección de condición anómala",
     re.compile(r"(_Fault|_Alarm|_Error|_FaultCode|_Err)$|Fault_|Alarm_|^Alm[A-Z_]", re.IGNORECASE), None, 0.85),

    ("enable",
     "Enable / habilitación — bit que arma una función o módulo",
     re.compile(r"(_Enable|_En|_Active|_Armed)$|^Enable_", re.IGNORECASE), None, 0.80),

    ("status",
     "Status / feedback / estado — lectura de condición actual del sistema",
     re.compile(r"(_Status|_State|_FB|_Feedback|_Done|_Ready|_Busy|_Active)$", re.IGNORECASE), None, 0.80),

    ("axis_data",
     "Estructura de datos de eje (UDT M*Data o similar) — agrupa setpoints/feedback de un eje",
     re.compile(r"^M\d+Data$|^(M\d+|Ax[A-Z]|Axis_).*Data$", re.IGNORECASE), None, 0.90),

    ("io_input",
     "Entrada física I/O — bit de un módulo de input digital",
     re.compile(r"^I_|_DI_|^DI_", re.IGNORECASE), None, 0.85),

    ("io_output",
     "Salida física I/O — bit de un módulo de output digital",
     re.compile(r"^O_|_DO_|^DO_", re.IGNORECASE), None, 0.85),

    ("internal_aux",
     "Auxiliar interno — variable temporal/scratch, no productiva semánticamente",
     re.compile(r"^(aux|tmp|temp|scratch|buf|temporary)\d*$", re.IGNORECASE), None, 0.75),

    # Heurísticas sobre constructos comunes Diatec/Amantrini
    ("dancer",
     "Dancer (rodillo bailarín) — tag relacionado con control de tensión por danzarín",
     re.compile(r"[Dd]ancer|[Dd]nc(?![A-Za-z])", re.IGNORECASE), None, 0.75),

    ("radius",
     "Radio del rollo — tag de cálculo de diámetro/radio actual",
     re.compile(r"[Rr]adius|[Dd]iameter", re.IGNORECASE), None, 0.70),

    ("splice",
     "Splice / empalme — tag relacionado con la lógica de empalme",
     re.compile(r"[Ss]plic|[Cc]tc(?![A-Za-z])", re.IGNORECASE), None, 0.75),

    ("safety",
     "Safety / E-stop — tag con datatype safety o naming safety",
     re.compile(r"^(DCS|DCI|CROUT|EStop|E_Stop|Safety_|SafeOK)", re.IGNORECASE), None, 0.85),
]


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def classify_tag(tag: "Tag") -> TagRole:
    """Clasifica un tag en su rol semántico inferido.

    Aplica reglas en orden — la primera que matchea gana. Si ninguna
    regla matchea, devuelve role='unknown' con confidence=0.0.

    Args:
        tag: Tag del modelo (con name, datatype, scope, constant, ...)

    Returns:
        TagRole con role + description + confidence + matched_pattern.
    """
    if getattr(tag, "constant", False):
        return TagRole(
            role="constant",
            description="Constante — valor inmutable definido por el ingeniero (no escribible)",
            confidence=1.0,
            matched_pattern="constant=True",
        )

    name = tag.name or ""
    datatype = tag.datatype or ""

    for role_id, desc, name_re, dt_re, conf in _RULES:
        if dt_re is not None and dt_re.match(datatype):
            return TagRole(role=role_id, description=desc, confidence=conf,
                           matched_pattern=f"datatype~/{dt_re.pattern}/")
        if name_re is not None and name_re.search(name):
            return TagRole(role=role_id, description=desc, confidence=conf,
                           matched_pattern=f"name~/{name_re.pattern}/")

    return TagRole(role="unknown",
                   description="Sin rol inferible por heurística — requiere inspección manual",
                   confidence=0.0,
                   matched_pattern="(no rule matched)")


def tag_dictionary(project: "Project", scope: str | None = None) -> list[tuple]:
    """Genera el diccionario completo de tags del proyecto con rol inferido.

    Args:
        project: Project ya cargado.
        scope: opcional, "controller" | "program" | None (todos).

    Returns:
        list[(Tag, TagRole)] — tags con su rol inferido.
    """
    out: list[tuple] = []
    for t in project.tags:
        if scope is not None and t.scope != scope:
            continue
        out.append((t, classify_tag(t)))
    return out


def tag_dictionary_to_markdown(
    project: "Project",
    entries: list[tuple] | None = None,
) -> str:
    """Genera reporte Markdown del diccionario de tags."""
    from collections import Counter

    if entries is None:
        entries = tag_dictionary(project)

    by_role = Counter(role.role for _, role in entries)
    name = project.identity.target_name if project.identity else "<unknown>"

    lines: list[str] = []
    lines.append(f"# Tag Dictionary — {name}")
    lines.append("")
    lines.append(f"**Total tags:** {len(entries)}")
    lines.append(f"**Roles distintos detectados:** {len(by_role)}")
    lines.append("")
    lines.append("## Distribución por rol")
    lines.append("")
    lines.append("| Rol | Count | % |")
    lines.append("|-----|------:|--:|")
    total = len(entries) or 1
    for role_id, cnt in by_role.most_common():
        pct = 100 * cnt / total
        lines.append(f"| `{role_id}` | {cnt} | {pct:.1f}% |")
    lines.append("")
    lines.append("## Glosario de roles")
    lines.append("")
    seen_roles: dict[str, str] = {}
    for _, role in entries:
        if role.role not in seen_roles:
            seen_roles[role.role] = role.description
    for role_id, desc in sorted(seen_roles.items()):
        lines.append(f"- **`{role_id}`** — {desc}")
    lines.append("")
    lines.append("## Tags por rol (sample top 20 por rol)")
    lines.append("")
    by_role_tags: dict[str, list[tuple]] = {}
    for t, r in entries:
        by_role_tags.setdefault(r.role, []).append((t, r))
    for role_id in sorted(by_role_tags):
        items = by_role_tags[role_id]
        lines.append(f"### `{role_id}` ({len(items)})")
        lines.append("")
        for t, r in items[:20]:
            lines.append(f"- `{t.name}` — {t.datatype} (scope={t.scope}) · conf={r.confidence:.2f}")
        if len(items) > 20:
            lines.append(f"- ... +{len(items) - 20} más")
        lines.append("")

    return "\n".join(lines) + "\n"
