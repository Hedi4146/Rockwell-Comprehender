"""Program Inference — inferencia funcional de programs (v0.5).

Cierra **Capacidad #7 del Vision** (Estructura programa - semántica
funcional): de 85% → 95%+. Hoy el Mapa Mental describe programs
estructuralmente; este módulo agrega inferencia automática de **rol
funcional** del program (motion_control, safety_handler, sequence_logic,
hmi_interface, fault_management, etc.) basado en evidencia múltiple.

**Heurística honesta (DT-008):** combina señales de:
1. Nombre del program (Safety*, Reject, Unwinder, Axis, Main, ...)
2. Tipo de la task que lo schedulea (SafetyTask → safety_handler)
3. AOIs invocadas en sus routines (CROUT/DCI_* → safety; MAJ/MAS → motion)
4. Conteo de motion ops vs bit logic vs comparators
5. Naming routines del program

Devuelve `ProgramRole` con role_id + confidence + evidence.

API:
    project.classify_program(program) -> ProgramRole
    project.program_inference() -> list[(Program, ProgramRole)]
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .tokenizer import tokenize_rll
from .tokenizer.st_tokenizer import tokenize_st

if TYPE_CHECKING:
    from .model import Program, Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class ProgramRole:
    """Rol funcional inferido de un program."""

    role: str           # "motion_control" | "safety_handler" | ...
    confidence: float   # 0-1
    description: str
    evidence: list[str]  # listado de señales que aportaron al match

    def __repr__(self) -> str:
        return f"ProgramRole({self.role} {self.confidence:.2f})"


_ROLE_DESCRIPTIONS: dict[str, str] = {
    "safety_handler": "Program de safety — implementa GuardLogix dual-channel, E-stop, CROUT/DCI_*",
    "motion_control": "Program de motion — comanda ejes (MAJ/MAS/MAH/MAM/MAG)",
    "sequence_logic": "Program de secuencia — lógica de estados, alarmas, condicionales (XIC/XIO/OTE/JSR)",
    "hmi_interface": "Program de interfaz HMI — sincronización de tags HmiNew*, lectura de pantalla",
    "fault_management": "Program de gestión de faults — concentra alarmas, decoding y latching",
    "io_mapping": "Program de mapeo I/O — copia entre tags físicos y lógicos",
    "reject_control": "Program de rechazo — reject motors, cull functions",
    "data_init": "Program de inicialización — carga setpoints, config inicial al arranque",
    "main_dispatcher": "Program principal — JSR a múltiples routines, orquesta ciclo de scan",
    "diagnostic": "Program diagnóstico — temperature, status, monitor",
    "unknown": "Sin rol inferible con confianza — requiere inspección manual",
}


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def classify_program(project: "Project", program: "Program") -> ProgramRole:
    """Infiere el rol funcional de un program."""
    name = program.name or ""
    name_lower = name.lower()
    evidence: list[str] = []
    candidates: dict[str, float] = {}  # role_id → score

    # ── Señal 1: nombre del program ───────────────────────────────────
    if re.search(r"safety", name_lower):
        candidates["safety_handler"] = candidates.get("safety_handler", 0) + 0.5
        evidence.append(f"name '{name}' contiene 'safety'")
    if re.search(r"^(reject|cull)", name_lower):
        candidates["reject_control"] = candidates.get("reject_control", 0) + 0.4
        evidence.append(f"name '{name}' inicia con reject/cull")
    if re.search(r"^(fault|alarm)", name_lower) or re.search(r"alarm", name_lower):
        candidates["fault_management"] = candidates.get("fault_management", 0) + 0.4
        evidence.append(f"name '{name}' relacionado con faults/alarmas")
    if re.search(r"^(read|init|setup|param)", name_lower):
        candidates["data_init"] = candidates.get("data_init", 0) + 0.3
        evidence.append(f"name '{name}' inicia con read/init/setup")
    if re.search(r"^(temperature|temp_|monitor|diagnostic)", name_lower):
        candidates["diagnostic"] = candidates.get("diagnostic", 0) + 0.4
        evidence.append(f"name '{name}' relacionado con diagnóstico")
    if re.search(r"(axis|unwinder|rewinder|drive|motion)", name_lower):
        candidates["motion_control"] = candidates.get("motion_control", 0) + 0.3
        evidence.append(f"name '{name}' relacionado con motion")
    if name_lower in ("mainprogram", "main"):
        candidates["main_dispatcher"] = candidates.get("main_dispatcher", 0) + 0.3
        evidence.append(f"name '{name}' es Main / dispatcher")
    if re.search(r"hmi", name_lower):
        candidates["hmi_interface"] = candidates.get("hmi_interface", 0) + 0.4
        evidence.append(f"name '{name}' contiene 'hmi'")
    if re.search(r"^(io|i_o)", name_lower):
        candidates["io_mapping"] = candidates.get("io_mapping", 0) + 0.4
        evidence.append(f"name '{name}' relacionado con I/O")

    # ── Señal 2: task type que lo schedulea ───────────────────────────
    for t in project.tasks:
        if program.name in t.scheduled_programs:
            if t.type == "PERIODIC" and "safety" in t.name.lower():
                candidates["safety_handler"] = candidates.get("safety_handler", 0) + 0.4
                evidence.append(f"scheduled by SafetyTask {t.name}")
            elif "temperature" in t.name.lower():
                candidates["diagnostic"] = candidates.get("diagnostic", 0) + 0.2
                evidence.append(f"scheduled by Temperature task")
            break

    # ── Señal 3: análisis de routines del program ─────────────────────
    op_count: Counter = Counter()
    safety_ops_seen = 0
    motion_ops_seen = 0
    bit_logic_ops_seen = 0
    jsr_count = 0
    hmi_tag_refs = 0

    for r in project.routines:
        if r.program != program.name or not r.code:
            continue
        try:
            if r.type == "RLL":
                rungs = tokenize_rll(r.code)
            elif r.type == "ST":
                rungs = tokenize_st(r.code)
            else:
                continue
        except Exception:
            continue
        for rung in rungs:
            for inst in rung.instructions:
                op = inst.operator
                op_count[op] += 1
                if op in ("CROUT", "DCI_STOP", "DCI_STOP_TEST_LOCK"):
                    safety_ops_seen += 1
                elif op in ("MAJ", "MAM", "MAS", "MAH", "MAG", "MSO", "MSF",
                            "MAOC", "MAPC", "MASR", "MAFR"):
                    motion_ops_seen += 1
                elif op in ("XIC", "XIO", "OTE", "OTL", "OTU"):
                    bit_logic_ops_seen += 1
                elif op == "JSR":
                    jsr_count += 1
                # HMI tag refs: cualquier operando con 'Hmi' en name
                for opd in inst.operands:
                    if "Hmi" in (opd.text or ""):
                        hmi_tag_refs += 1
                        break

    if safety_ops_seen >= 1:
        candidates["safety_handler"] = candidates.get("safety_handler", 0) + 0.5
        evidence.append(f"{safety_ops_seen} safety ops (CROUT/DCI_*)")
    if motion_ops_seen >= 5:
        candidates["motion_control"] = candidates.get("motion_control", 0) + 0.5
        evidence.append(f"{motion_ops_seen} motion ops")
    elif motion_ops_seen >= 1:
        candidates["motion_control"] = candidates.get("motion_control", 0) + 0.2
        evidence.append(f"{motion_ops_seen} motion ops (pocos)")
    if bit_logic_ops_seen >= 30 and motion_ops_seen == 0 and safety_ops_seen == 0:
        candidates["sequence_logic"] = candidates.get("sequence_logic", 0) + 0.5
        evidence.append(f"{bit_logic_ops_seen} bit logic ops, sin motion/safety")
    if jsr_count >= 5 and motion_ops_seen == 0:
        candidates["main_dispatcher"] = candidates.get("main_dispatcher", 0) + 0.4
        evidence.append(f"{jsr_count} JSR — alto dispatch")
    if hmi_tag_refs >= 10:
        candidates["hmi_interface"] = candidates.get("hmi_interface", 0) + 0.3
        evidence.append(f"{hmi_tag_refs} refs a tags Hmi*")

    # ── Decisión final ────────────────────────────────────────────────
    if not candidates:
        return ProgramRole(
            role="unknown",
            confidence=0.0,
            description=_ROLE_DESCRIPTIONS["unknown"],
            evidence=evidence,
        )
    role, raw_score = max(candidates.items(), key=lambda x: x[1])
    confidence = min(1.0, raw_score)
    return ProgramRole(
        role=role,
        confidence=round(confidence, 2),
        description=_ROLE_DESCRIPTIONS.get(role, "—"),
        evidence=evidence,
    )


def program_inference(project: "Project") -> list[tuple]:
    """Aplica classify_program a todos los programs del proyecto."""
    return [(p, classify_program(project, p)) for p in project.programs]


def program_inference_to_markdown(project: "Project", entries: list[tuple] | None = None) -> str:
    """Reporte Markdown de inferencia funcional de programs."""
    if entries is None:
        entries = program_inference(project)
    name = project.identity.target_name if project.identity else "<unknown>"
    lines: list[str] = []
    lines.append(f"# Program Inference — {name}")
    lines.append("")
    lines.append(f"**Programs analizados:** {len(entries)}")
    lines.append("")
    lines.append("| Program | Role | Conf | Evidence |")
    lines.append("|---------|------|-----:|----------|")
    for p, role in entries:
        ev = "; ".join(role.evidence[:3]) if role.evidence else "—"
        lines.append(f"| `{p.name}` | `{role.role}` | {role.confidence:.2f} | {ev} |")
    lines.append("")
    lines.append("## Detalle por program")
    for p, role in entries:
        lines.append("")
        lines.append(f"### `{p.name}` — {role.role} (conf {role.confidence:.2f})")
        lines.append("")
        lines.append(f"**Descripción del rol:** {role.description}")
        lines.append("")
        if role.evidence:
            lines.append("**Evidencia:**")
            for e in role.evidence:
                lines.append(f"- {e}")
        else:
            lines.append("_(sin evidencia)_")
    return "\n".join(lines) + "\n"
