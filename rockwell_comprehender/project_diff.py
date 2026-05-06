"""Project Diff — comparación automática entre proyectos (v0.5).

Automatiza el **Caso 3** del catálogo (Comparación entre proyectos),
que en v0.1+ era manual. Dado dos `Project` cargados, computa diff
estructurado:

- Modules: added / removed / changed (catalog_number diff)
- AOIs: added / removed / changed (parameter count diff)
- UDTs: added / removed
- Programs: added / removed
- Routines: added / removed
- Tags controller-scope: added / removed (sample, no full diff por tamaño)
- Tasks: added / removed

Output: `ProjectDiff` con todas las listas, y `to_markdown()` para
reporte navegable.

**Stack mínimo (DT-008):** stdlib only + estructuras del modelo.

API:
    from rockwell_comprehender.project_diff import diff_projects
    d = diff_projects(p_old, p_new)
    print(d.summary())
    md = d.to_markdown()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class DiffEntry:
    """Una entrada del diff: agregado, eliminado, o cambiado."""

    name: str
    kind: str           # "added" | "removed" | "changed"
    detail: str = ""    # info adicional (ej: "params: 30 → 35", "catalog: 2094-X → 2198-Y")


@dataclass
class ProjectDiff:
    """Diff completo entre dos projects (old → new)."""

    old_name: str
    new_name: str
    modules: list[DiffEntry] = field(default_factory=list)
    aois: list[DiffEntry] = field(default_factory=list)
    udts: list[DiffEntry] = field(default_factory=list)
    programs: list[DiffEntry] = field(default_factory=list)
    routines: list[DiffEntry] = field(default_factory=list)
    tags: list[DiffEntry] = field(default_factory=list)
    tasks: list[DiffEntry] = field(default_factory=list)

    def summary(self) -> str:
        parts = []
        for label, items in [
            ("modules", self.modules), ("aois", self.aois), ("udts", self.udts),
            ("programs", self.programs), ("routines", self.routines),
            ("tags", self.tags), ("tasks", self.tasks),
        ]:
            n_add = sum(1 for e in items if e.kind == "added")
            n_rem = sum(1 for e in items if e.kind == "removed")
            n_chg = sum(1 for e in items if e.kind == "changed")
            if n_add + n_rem + n_chg == 0:
                parts.append(f"{label}: =")
            else:
                parts.append(f"{label}: +{n_add}/-{n_rem}/~{n_chg}")
        return f"Diff {self.old_name} → {self.new_name}: " + " | ".join(parts)

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append(f"# Project Diff — {self.old_name} → {self.new_name}")
        lines.append("")
        lines.append(self.summary())
        lines.append("")

        sections = [
            ("Modules", self.modules),
            ("AOIs", self.aois),
            ("UDTs", self.udts),
            ("Programs", self.programs),
            ("Routines", self.routines),
            ("Tags (controller scope)", self.tags),
            ("Tasks", self.tasks),
        ]

        for label, items in sections:
            if not items:
                continue
            n_add = sum(1 for e in items if e.kind == "added")
            n_rem = sum(1 for e in items if e.kind == "removed")
            n_chg = sum(1 for e in items if e.kind == "changed")
            lines.append(f"## {label} (+{n_add} / -{n_rem} / ~{n_chg})")
            lines.append("")
            if n_add:
                lines.append(f"### Added ({n_add})")
                for e in items:
                    if e.kind == "added":
                        suffix = f" — {e.detail}" if e.detail else ""
                        lines.append(f"- `{e.name}`{suffix}")
                lines.append("")
            if n_rem:
                lines.append(f"### Removed ({n_rem})")
                for e in items:
                    if e.kind == "removed":
                        suffix = f" — {e.detail}" if e.detail else ""
                        lines.append(f"- `{e.name}`{suffix}")
                lines.append("")
            if n_chg:
                lines.append(f"### Changed ({n_chg})")
                for e in items:
                    if e.kind == "changed":
                        lines.append(f"- `{e.name}` — {e.detail}")
                lines.append("")
        return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def diff_projects(p_old: "Project", p_new: "Project") -> ProjectDiff:
    """Computa el diff estructural entre dos projects."""
    old_name = p_old.identity.target_name if p_old.identity else "old"
    new_name = p_new.identity.target_name if p_new.identity else "new"
    diff = ProjectDiff(old_name=old_name, new_name=new_name)

    # Modules: comparar por name; detectar catalog change
    old_mods = {m.name: m for m in p_old.modules}
    new_mods = {m.name: m for m in p_new.modules}
    for name in sorted(set(old_mods) | set(new_mods)):
        if name not in old_mods:
            cn = new_mods[name].catalog_number or "?"
            diff.modules.append(DiffEntry(name, "added", f"catalog={cn}"))
        elif name not in new_mods:
            cn = old_mods[name].catalog_number or "?"
            diff.modules.append(DiffEntry(name, "removed", f"catalog={cn}"))
        else:
            o = old_mods[name].catalog_number
            n = new_mods[name].catalog_number
            if o != n:
                diff.modules.append(DiffEntry(name, "changed", f"catalog: {o} → {n}"))

    # AOIs: comparar por name; detectar param count diff
    old_aois = {a.name: a for a in p_old.aois}
    new_aois = {a.name: a for a in p_new.aois}
    for name in sorted(set(old_aois) | set(new_aois)):
        if name not in old_aois:
            params = len(new_aois[name].parameters)
            diff.aois.append(DiffEntry(name, "added", f"{params} params"))
        elif name not in new_aois:
            params = len(old_aois[name].parameters)
            diff.aois.append(DiffEntry(name, "removed", f"{params} params"))
        else:
            o_p = len(old_aois[name].parameters)
            n_p = len(new_aois[name].parameters)
            if o_p != n_p:
                diff.aois.append(DiffEntry(name, "changed", f"params: {o_p} → {n_p}"))

    # UDTs
    old_udts = {u.name for u in p_old.udts}
    new_udts = {u.name for u in p_new.udts}
    for name in sorted(new_udts - old_udts):
        diff.udts.append(DiffEntry(name, "added"))
    for name in sorted(old_udts - new_udts):
        diff.udts.append(DiffEntry(name, "removed"))

    # Programs
    old_progs = {p.name for p in p_old.programs}
    new_progs = {p.name for p in p_new.programs}
    for name in sorted(new_progs - old_progs):
        diff.programs.append(DiffEntry(name, "added"))
    for name in sorted(old_progs - new_progs):
        diff.programs.append(DiffEntry(name, "removed"))

    # Routines (key: program/name)
    old_rts = {f"{r.program}/{r.name}" for r in p_old.routines}
    new_rts = {f"{r.program}/{r.name}" for r in p_new.routines}
    for key in sorted(new_rts - old_rts):
        diff.routines.append(DiffEntry(key, "added"))
    for key in sorted(old_rts - new_rts):
        diff.routines.append(DiffEntry(key, "removed"))

    # Tags controller-scope (sample diff: solo names, no datatype-level)
    old_tags = {t.name for t in p_old.tags if t.scope == "controller"}
    new_tags = {t.name for t in p_new.tags if t.scope == "controller"}
    only_new = sorted(new_tags - old_tags)
    only_old = sorted(old_tags - new_tags)
    # Limit per side to 200 to keep reports manageable
    for name in only_new[:200]:
        diff.tags.append(DiffEntry(name, "added"))
    if len(only_new) > 200:
        diff.tags.append(DiffEntry(f"(+{len(only_new) - 200} more added not listed)", "added"))
    for name in only_old[:200]:
        diff.tags.append(DiffEntry(name, "removed"))
    if len(only_old) > 200:
        diff.tags.append(DiffEntry(f"(+{len(only_old) - 200} more removed not listed)", "removed"))

    # Tasks
    old_tk = {t.name for t in p_old.tasks}
    new_tk = {t.name for t in p_new.tasks}
    for name in sorted(new_tk - old_tk):
        diff.tasks.append(DiffEntry(name, "added"))
    for name in sorted(old_tk - new_tk):
        diff.tasks.append(DiffEntry(name, "removed"))

    return diff
