"""
reporters/markdown.py — Reporte Markdown completo del proyecto.

API pública:
    to_markdown(project, output_path) -> str

Genera un documento extendido que incluye:
1. El Mapa Mental compacto (mapamental.generate)
2. Inventario completo de tags por scope (tablas)
3. Detalle de cada AOI (parámetros, local tags, código de cada rutina interna)
4. Código completo de cada rutina de programa
5. Detalle completo de cada UDT con sus members

Decisiones de diseño v0.1:
- Documentación COMPLETA, no resumen. El Mapa Mental es para chat/contexto;
  este reporte es para entrega/archivo.
- El código de rutinas se incluye TAL CUAL fue extraído por el loader. Para
  RLL es texto reconstruido por rung; para FBD/SFC es XML serializado (limitación
  documentada — un renderer humano para FBD/SFC es trabajo de v0.2+).
- Todos los tags incluidos (ctrl + program + AOI-local) en tablas separadas
  por scope, no concatenadas, para que cada sección sea consultable.
- Outputs son archivos en disco, retorna el path final.
"""

from __future__ import annotations

import os
from typing import TextIO

from ..mapamental import generate as generate_mapa_mental
from ..model import Project


def to_markdown(project: Project, output_path: str) -> str:
    """Genera reporte Markdown completo y lo escribe a output_path.

    Args:
        project: Project ya cargado
        output_path: ruta destino del archivo .md

    Returns:
        Path absoluto del archivo escrito.
    """
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        _write_report(f, project)
    return abs_path


# ─────────────────────────────────────────────────────────────────────────
# Composición del reporte
# ─────────────────────────────────────────────────────────────────────────


def _write_report(f: TextIO, p: Project) -> None:
    """Escribe el reporte completo al stream f."""
    # 1. Mapa Mental al inicio (visión general autónoma)
    f.write(generate_mapa_mental(p))
    f.write("\n\n---\n\n")

    # 2-6. Secciones detalladas
    _write_tags_full(f, p)
    _write_aois_full(f, p)
    _write_routines_full(f, p)
    _write_udts_full(f, p)
    _write_modules_full(f, p)
    _write_observations_full(f, p)


# ─────────────────────────────────────────────────────────────────────────
# 2. Tags completos por scope
# ─────────────────────────────────────────────────────────────────────────


def _write_tags_full(f: TextIO, p: Project) -> None:
    f.write("# Inventario completo de tags\n\n")

    # Agrupar por scope
    scopes: dict[str, list] = {}
    for t in p.tags:
        scopes.setdefault(t.scope, []).append(t)

    f.write(f"Total: **{len(p.tags)} tags** distribuidos en "
            f"**{len(scopes)} scopes** (controller + cada programa + cada AOI).\n\n")

    # Controller-scope primero
    program_names = {pr.name for pr in p.programs}
    aoi_names = {a.name for a in p.aois}

    if "controller" in scopes:
        f.write("## Controller-scope\n\n")
        _write_tag_table(f, scopes["controller"])
        f.write("\n")

    # Program-scope
    program_scopes = sorted(s for s in scopes if s in program_names)
    if program_scopes:
        f.write("## Program-scope\n\n")
        for scope in program_scopes:
            f.write(f"### Programa `{scope}` ({len(scopes[scope])} tags)\n\n")
            _write_tag_table(f, scopes[scope])
            f.write("\n")

    # AOI-local
    aoi_scopes = sorted(s for s in scopes if s in aoi_names)
    if aoi_scopes:
        f.write("## AOI-local\n\n")
        f.write("> Tags locales declarados dentro de cada AOI. Solo accesibles "
                "desde el código del AOI propietario.\n\n")
        for scope in aoi_scopes:
            f.write(f"### AOI `{scope}` ({len(scopes[scope])} local tags)\n\n")
            _write_tag_table(f, scopes[scope])
            f.write("\n")

    f.write("---\n\n")


def _write_tag_table(f: TextIO, tags: list) -> None:
    """Tabla Markdown estándar de tags."""
    f.write("| Name | DataType | Dim | ExternalAccess | MotionModule | Description |\n")
    f.write("|---|---|---|---|---|---|\n")
    for t in sorted(tags, key=lambda x: x.name):
        desc = (t.description or "").replace("\n", " ").replace("|", "\\|")
        if len(desc) > 80:
            desc = desc[:80] + "…"
        dim = t.dimension or ""
        ea = t.external_access or "—"
        mm = t.motion_module or "—"
        f.write(f"| `{t.name}` | `{t.datatype}` | {dim} | {ea} | {mm} | {desc} |\n")


# ─────────────────────────────────────────────────────────────────────────
# 3. AOIs completos con código
# ─────────────────────────────────────────────────────────────────────────


def _write_aois_full(f: TextIO, p: Project) -> None:
    if not p.aois:
        return
    f.write("# AOIs — definiciones completas\n\n")
    f.write(f"{len(p.aois)} AOIs definidos en el controller.\n\n")

    for aoi in sorted(p.aois, key=lambda a: a.name):
        f.write(f"## `{aoi.name}` (rev {aoi.revision or '—'})\n\n")
        if aoi.description:
            f.write(f"_{aoi.description}_\n\n")

        # Parámetros
        if aoi.parameters:
            f.write("### Parámetros\n\n")
            f.write("| Name | Usage | DataType | Dim | Required | Default | Description |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for pp in aoi.parameters:
                desc = (pp.description or "").replace("\n", " ").replace("|", "\\|")
                if len(desc) > 60:
                    desc = desc[:60] + "…"
                req = "✓" if pp.required else ""
                default = pp.default or ""
                dim = pp.dimension or ""
                f.write(
                    f"| `{pp.name}` | {pp.usage} | `{pp.datatype}` | {dim} | "
                    f"{req} | {default} | {desc} |\n"
                )
            f.write("\n")

        # Local tags
        if aoi.local_tags:
            f.write(f"### Local tags ({len(aoi.local_tags)})\n\n")
            _write_tag_table(f, aoi.local_tags)
            f.write("\n")

        # Routines internas con código
        if aoi.routines:
            f.write(f"### Routines internas ({len(aoi.routines)})\n\n")
            for rname, r in aoi.routines.items():
                f.write(f"#### `{rname}` ({r.type})\n\n")
                if r.description:
                    f.write(f"_{r.description}_\n\n")
                _write_code_block(f, r.code, r.type)
                f.write("\n")

        f.write("---\n\n")


# ─────────────────────────────────────────────────────────────────────────
# 4. Routines de programa con código
# ─────────────────────────────────────────────────────────────────────────


def _write_routines_full(f: TextIO, p: Project) -> None:
    if not p.routines:
        return
    f.write("# Rutinas de programas — código completo\n\n")

    # Agrupar por programa
    by_program: dict[str, list] = {}
    for r in p.routines:
        if r.program:
            by_program.setdefault(r.program, []).append(r)

    for prog_name in sorted(by_program.keys()):
        f.write(f"## Programa `{prog_name}`\n\n")
        for r in sorted(by_program[prog_name], key=lambda x: x.name):
            f.write(f"### `{r.name}` ({r.type})\n\n")
            if r.description:
                f.write(f"_{r.description}_\n\n")
            _write_code_block(f, r.code, r.type)
            f.write("\n")
        f.write("---\n\n")


def _write_code_block(f: TextIO, code: str, rtype: str) -> None:
    """Escribe un bloque de código fenced apropiado al tipo de rutina."""
    if not code.strip():
        f.write("_(rutina vacía o sin código extraíble)_\n")
        return
    # Para RLL/ST usamos lenguaje vacío (el código no es código real ejecutable
    # en ningún lenguaje conocido por highlighters). Para FBD/SFC dejamos xml.
    fence_lang = "xml" if rtype in ("FBD", "SFC") else ""
    if rtype in ("FBD", "SFC"):
        f.write(f"> ⚠️ Rutina {rtype} — representación XML serializada. "
                f"Un renderer visual humano es trabajo de v0.2+.\n\n")
    f.write(f"```{fence_lang}\n")
    f.write(code.rstrip())
    f.write("\n```\n")


# ─────────────────────────────────────────────────────────────────────────
# 5. UDTs completos
# ─────────────────────────────────────────────────────────────────────────


def _write_udts_full(f: TextIO, p: Project) -> None:
    if not p.udts:
        return
    f.write("# UDTs — definiciones completas\n\n")
    f.write(f"{len(p.udts)} UDTs definidos.\n\n")
    for u in sorted(p.udts, key=lambda x: x.name):
        f.write(f"## `{u.name}`")
        if u.family and u.family != "NoFamily":
            f.write(f" — family `{u.family}`")
        f.write("\n\n")
        if u.description:
            f.write(f"_{u.description}_\n\n")
        if u.members:
            f.write(f"### Members ({len(u.members)})\n\n")
            f.write("| Name | DataType | Dim | Hidden | Description |\n")
            f.write("|---|---|---|---|---|\n")
            for m in u.members:
                desc = (m.description or "").replace("\n", " ").replace("|", "\\|")
                if len(desc) > 60:
                    desc = desc[:60] + "…"
                dim = m.dimension or ""
                hidden = "✓" if m.hidden else ""
                f.write(f"| `{m.name}` | `{m.datatype}` | {dim} | {hidden} | {desc} |\n")
            f.write("\n")
        f.write("---\n\n")


# ─────────────────────────────────────────────────────────────────────────
# 6. Modules completos
# ─────────────────────────────────────────────────────────────────────────


def _write_modules_full(f: TextIO, p: Project) -> None:
    if not p.modules:
        return
    f.write("# Modules — inventario completo\n\n")
    f.write(f"{len(p.modules)} módulos físicos en el proyecto.\n\n")
    f.write("| Name | Catalog | Vendor | Parent | PortId | Inhibited | "
            "ExplicitName |\n")
    f.write("|---|---|---|---|---|---|---|\n")
    for m in p.modules:
        inh = "✓" if m.inhibited else ""
        en = "" if m.has_explicit_name else "(sintético)"
        f.write(
            f"| `{m.name}` | `{m.catalog_number}` | {m.vendor or '—'} | "
            f"{m.parent_module or '—'} | {m.parent_port_id or '—'} | "
            f"{inh} | {en} |\n"
        )
    f.write("\n---\n\n")


# ─────────────────────────────────────────────────────────────────────────
# 7. Observations
# ─────────────────────────────────────────────────────────────────────────


def _write_observations_full(f: TextIO, p: Project) -> None:
    f.write("# Observaciones detectadas (completo)\n\n")
    if not p.observations:
        f.write("_Ninguna observación detectada durante el parseo._\n\n")
        return
    f.write(f"{len(p.observations)} observaciones registradas durante el parseo.\n\n")
    f.write("| # | Severity | Category | Message | References |\n")
    f.write("|---|---|---|---|---|\n")
    for i, o in enumerate(p.observations, 1):
        msg = o.message.replace("\n", " ").replace("|", "\\|")
        if len(msg) > 100:
            msg = msg[:100] + "…"
        refs = ", ".join(f"`{r}`" for r in o.references) if o.references else "—"
        f.write(f"| {i} | {o.severity} | `{o.category}` | {msg} | {refs} |\n")
    f.write("\n")
