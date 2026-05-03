"""Explorer HTML reporter — Paso 1: árbol Controller Organizer.

Genera un único archivo HTML autocontenido (CSS y JS embebidos) que muestra
la estructura jerárquica de un proyecto Rockwell, replicando el Controller
Organizer de Studio 5000. Esta primera iteración entrega solo el árbol
expandible/colapsable. Los paneles de detalle llegan en pasos posteriores.
"""
from __future__ import annotations

import html
import json
import os
import re

from ..model import Module, Project
# Helpers de inferencia funcional ya implementados en mapamental.py.
# La spec del Explorer (sección 6.3) instruye explícitamente "Importar y
# usar esos helpers, no reimplementar". Son nombres con underscore por
# convención interna del módulo, pero su uso aquí es intencional.
from ..mapamental import (
    _build_axis_to_module,
    _classify_aoi_prefixes,
    _format_hardware_cell,
    _infer_axis_function,
    _infer_from_tag_name,
    _is_bridge,
    _is_drive,
    _is_generic_aoi,
    _is_io_adapter,
    _is_io_module,
    _looks_like_spare,
    _map_axes_to_aois,
)


_ICONS = {
    "controller": "⚙️",
    "controller-tags": "📋",
    "fault-handler": "⚠️",
    "powerup-handler": "⚡",
    "tasks-folder": "📂",
    "task-continuous": "🔁",
    "task-periodic": "🔁",
    "task-event": "🔁",
    "program": "📂",
    "program-tags": "📋",
    "routine": "📜",
    "motion-groups-folder": "📂",
    "motion-group": "📂",
    "axis": "🎯",
    "aois-folder": "📂",
    "aoi": "🧩",
    "udts-folder": "📂",
    "udt": "📐",
    "io-folder": "📂",
    "module": "📦",
}


def to_html_explorer(project: Project, output_path: str) -> str:
    """Genera el Explorer HTML y lo escribe en `output_path`.

    Devuelve la ruta absoluta del archivo generado. Crea el directorio
    padre si no existe.
    """
    head = _render_head(project)
    topbar = _render_topbar(project)
    tree = _render_tree(project)
    panels = _build_panels(project)
    # Vista al cargar = mapa mental (también es el panel del nodo controller raíz)
    detail_default = panels.get(
        f"controller::{project.identity.target_name}",
        _md_to_html(project.mapa_mental),
    )
    # Serializar paneles. Reemplazo `</` por `<\/` para que un eventual
    # `</script>` dentro del HTML embebido no rompa el bloque <script>.
    panels_json = json.dumps(panels, ensure_ascii=False).replace("</", "<\\/")

    full = (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        f"<head>\n{head}\n</head>\n"
        "<body>\n"
        f"{topbar}\n"
        '<main class="layout">\n'
        '  <aside class="tree-pane">\n'
        f"{tree}\n"
        "  </aside>\n"
        '  <section class="detail-pane" id="detail">\n'
        '    <div class="detail-content">\n'
        f"{detail_default}\n"
        "    </div>\n"
        "  </section>\n"
        "</main>\n"
        f'<script type="application/json" id="panels-data">{panels_json}</script>\n'
        f"<script>{_JS}</script>\n"
        "</body>\n"
        "</html>\n"
    )

    abs_path = os.path.abspath(output_path)
    parent = os.path.dirname(abs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(full)
    return abs_path


def _e(s) -> str:
    return html.escape(str(s) if s is not None else "")


def _render_head(project: Project) -> str:
    title = f"Explorer — {project.identity.target_name}"
    return (
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{_e(title)}</title>\n"
        f"  <style>{_CSS}</style>"
    )


def _render_topbar(project: Project) -> str:
    ident = project.identity
    n_obs = len(project.observations)
    n_warn = sum(1 for o in project.observations if o.severity == "warning")
    if n_obs == 0:
        obs_btn = ""
    elif n_warn > 0:
        obs_btn = (
            f'<button class="obs-badge warn" id="obs-badge" type="button" '
            f'title="{n_warn} warning(s) + {n_obs - n_warn} info">'
            f'⚠ {n_obs} observaciones</button>'
        )
    else:
        obs_btn = (
            f'<button class="obs-badge info" id="obs-badge" type="button">'
            f'ⓘ {n_obs} observaciones</button>'
        )
    return (
        '<header class="topbar">\n'
        '  <div class="title">\n'
        f'    <span class="proj-name">{_e(ident.target_name)}</span>\n'
        '    <span class="sep">|</span>\n'
        f'    <span class="proc">{_e(ident.processor_type)}</span>\n'
        '    <span class="sep">|</span>\n'
        f'    <span class="ver">Studio 5000 v{_e(ident.software_revision)}</span>\n'
        "  </div>\n"
        '  <div class="controls">\n'
        '    <input type="search" id="search-input" placeholder="Buscar en árbol…" '
        'spellcheck="false" autocomplete="off" />\n'
        '    <label class="filter-toggle">'
        '<input type="checkbox" id="filter-hide-tags"> Ocultar Tags</label>\n'
        f'    {obs_btn}\n'
        "  </div>\n"
        "</header>"
    )


def _node(
    *,
    type_: str,
    id_: str,
    label: str,
    leaf: bool = False,
    open_: bool = False,
    children_html: str = "",
    icon: str | None = None,
) -> str:
    classes = ["node"]
    if leaf:
        classes.append("leaf")
    if open_:
        classes.append("open")
    icon_html = icon if icon is not None else _ICONS.get(type_, "")
    parts = [
        f'<li class="{" ".join(classes)}" data-type="{_e(type_)}" data-id="{_e(id_)}">',
        '<span class="caret"></span>',
        f'<span class="icon">{icon_html}</span>',
        f'<span class="label">{label}</span>',
    ]
    if children_html:
        parts.append(f"<ul>{children_html}</ul>")
    parts.append("</li>")
    return "".join(parts)


def _render_tree(project: Project) -> str:
    ident = project.identity
    sections: list[str] = []

    ctrl_tags = [t for t in project.tags if t.scope == "controller"]
    sections.append(_node(
        type_="controller-tags", id_="__controller_tags__", leaf=True,
        label=f"Controller Tags <span class=\"meta\">({len(ctrl_tags)})</span>",
    ))
    sections.append(_node(
        type_="fault-handler", id_="__fault_handler__", leaf=True,
        label="Controller Fault Handler",
    ))
    sections.append(_node(
        type_="powerup-handler", id_="__powerup_handler__", leaf=True,
        label="Power-Up Handler",
    ))

    tasks_children = "".join(_render_task(t, project) for t in project.tasks)
    sections.append(_node(
        type_="tasks-folder", id_="__tasks__",
        label=f"Tasks <span class=\"meta\">({len(project.tasks)})</span>",
        children_html=tasks_children,
    ))

    sections.append(_render_motion_groups(project))

    aoi_items = "".join(
        _node(type_="aoi", id_=a.name, leaf=True, label=_e(a.name))
        for a in sorted(project.aois, key=lambda a: a.name)
    )
    sections.append(_node(
        type_="aois-folder", id_="__aois__",
        label=f"Add-On Instructions <span class=\"meta\">({len(project.aois)})</span>",
        children_html=aoi_items,
    ))

    udt_items = "".join(
        _node(
            type_="udt", id_=u.name, leaf=True,
            label=f"{_e(u.name)} <span class=\"meta\">({len(u.members)} members)</span>",
        )
        for u in sorted(project.udts, key=lambda u: u.name)
    )
    sections.append(_node(
        type_="udts-folder", id_="__udts__",
        label=f"Data Types <span class=\"meta\">({len(project.udts)})</span>",
        children_html=udt_items,
    ))

    sections.append(_node(
        type_="io-folder", id_="__io__",
        label="I/O Configuration",
        children_html=_render_io(project),
    ))

    return (
        '<ul class="tree" id="root">'
        + _node(
            type_="controller", id_=ident.target_name, open_=True,
            label=f"Controller [{_e(ident.target_name)}]",
            children_html="".join(sections),
        )
        + "</ul>"
    )


def _render_task(task, project: Project) -> str:
    icon = _ICONS.get(f"task-{task.type.lower()}", _ICONS["task-continuous"])
    rate_str = ""
    if task.type in ("PERIODIC", "EVENT") and task.rate:
        rate_str = f" · {task.rate:g} ms"
    label = (
        f"{_e(task.name)} "
        f'<span class="meta">[{_e(task.type)}{rate_str}]</span>'
    )
    children = []
    for prog_name in task.scheduled_programs:
        prog = next((p for p in project.programs if p.name == prog_name), None)
        if prog is None:
            children.append(_node(
                type_="program", id_=prog_name, leaf=True,
                label=f'{_e(prog_name)} <span class="meta">(no encontrado)</span>',
            ))
        else:
            children.append(_render_program(prog, project))
    return _node(
        type_="task", id_=task.name, label=label, icon=icon,
        children_html="".join(children),
    )


def _render_program(prog, project: Project) -> str:
    prog_tags = [t for t in project.tags if t.scope == prog.name]
    routines = [r for r in project.routines if r.program == prog.name]
    routines_sorted = sorted(
        routines, key=lambda r: (r.name != prog.main_routine, r.name)
    )
    children = [_node(
        type_="program-tags", id_=f"__pgm_tags::{prog.name}", leaf=True,
        label=f"Program Tags <span class=\"meta\">({len(prog_tags)})</span>",
    )]
    for r in routines_sorted:
        main_tag = ' <span class="meta">(main)</span>' if r.name == prog.main_routine else ""
        children.append(_node(
            type_="routine", id_=f"{prog.name}::{r.name}", leaf=True,
            label=f'{_e(r.name)} <span class="meta">[{_e(r.type)}]</span>{main_tag}',
        ))
    return _node(
        type_="program", id_=prog.name,
        label=_e(prog.name),
        children_html="".join(children),
    )


def _render_motion_groups(project: Project) -> str:
    # Ejes primitivos = tags controller-scoped con datatype AXIS_*. Mismo
    # criterio que mapamental._section_mapa_funcional_ejes (consistencia).
    axis_tags = sorted(
        (t for t in project.tags
         if t.scope == "controller" and t.datatype.startswith("AXIS_")),
        key=lambda t: t.name,
    )
    axes_children = "".join(
        _node(type_="axis", id_=t.name, leaf=True, label=_e(t.name))
        for t in axis_tags
    )
    axes_node = _node(
        type_="motion-group", id_="__axes__",
        label=(
            f'Axes <span class="meta">({len(axis_tags)}) · '
            f'agrupación no extraída en v0.1 del paquete</span>'
        ),
        children_html=axes_children,
    )
    return _node(
        type_="motion-groups-folder", id_="__motion_groups__",
        label="Motion Groups",
        children_html=axes_node,
    )


def _render_io(project: Project) -> str:
    children_map: dict[str, list[Module]] = {}
    roots: list[Module] = []
    for m in project.modules:
        if not m.parent_module or m.parent_module == m.name:
            roots.append(m)
        else:
            children_map.setdefault(m.parent_module, []).append(m)

    def sort_key(m: Module):
        try:
            port_int = int(m.parent_port_id) if m.parent_port_id else 0
        except ValueError:
            port_int = 0
        return (port_int, m.name)

    roots.sort(key=sort_key)
    for k in children_map:
        children_map[k].sort(key=sort_key)

    def render(m: Module) -> str:
        kids = children_map.get(m.name, [])
        cat = f" [{_e(m.catalog_number)}]" if m.catalog_number else ""
        port = (
            f' <span class="meta">slot/port {_e(m.parent_port_id)}</span>'
            if m.parent_port_id and m.parent_module != m.name else ""
        )
        warn = ""
        if m.inhibited:
            warn += ' <span class="warn">⊘ inhibido</span>'
        if not m.has_explicit_name:
            warn += ' <span class="warn">⚠ sin nombre explícito</span>'
        label = f"{_e(m.name)}{cat}{port}{warn}"
        if kids:
            inner = "".join(render(k) for k in kids)
            return _node(type_="module", id_=m.name, label=label, children_html=inner)
        return _node(type_="module", id_=m.name, label=label, leaf=True)

    return "".join(render(r) for r in roots)


# ─────────────────────────────────────────────────────────────────────────
# Paneles del detalle (panel derecho) — uno por tipo de nodo del árbol
# ─────────────────────────────────────────────────────────────────────────


def _build_panels(p: Project) -> dict[str, str]:
    """Pre-renderiza todos los paneles del detalle. Retorna dict
    keyed por '<type>::<id>' (mismo formato que data-type/data-id en el árbol).
    """
    primitive_axes = [
        t for t in p.tags
        if t.scope == "controller" and t.datatype.startswith("AXIS_")
    ]
    axis_to_module = _build_axis_to_module(p, primitive_axes)
    axis_to_aois = _map_axes_to_aois(p, [a.name for a in primitive_axes])
    aoi_partners = _aoi_duplicate_partners(p)

    panels: dict[str, str] = {}

    # Controller root → vista general (Mapa Mental)
    panels[f"controller::{p.identity.target_name}"] = _md_to_html(p.mapa_mental)

    # Cabeceras
    panels["controller-tags::__controller_tags__"] = _panel_controller_tags(p)
    panels["fault-handler::__fault_handler__"] = _panel_placeholder(
        "Controller Fault Handler",
        "Esta entrada existe en el modelo de Studio 5000 pero no está expuesta en v0.1 del paquete.",
    )
    panels["powerup-handler::__powerup_handler__"] = _panel_placeholder(
        "Power-Up Handler",
        "Esta entrada existe en el modelo de Studio 5000 pero no está expuesta en v0.1 del paquete.",
    )
    panels["tasks-folder::__tasks__"] = _panel_tasks_folder(p)
    panels["motion-groups-folder::__motion_groups__"] = _panel_motion_folder(p, primitive_axes)
    panels["motion-group::__axes__"] = _panel_motion_folder(p, primitive_axes)
    panels["aois-folder::__aois__"] = _panel_aois_folder(p)
    panels["udts-folder::__udts__"] = _panel_udts_folder(p)
    panels["io-folder::__io__"] = _panel_io_folder(p)

    for t in p.tasks:
        panels[f"task::{t.name}"] = _panel_task(t, p)

    for prog in p.programs:
        panels[f"program::{prog.name}"] = _panel_program(prog, p)
        panels[f"program-tags::__pgm_tags::{prog.name}"] = _panel_program_tags(prog, p)

    for r in p.routines:
        panels[f"routine::{r.program}::{r.name}"] = _panel_routine(r)

    for ax in primitive_axes:
        panels[f"axis::{ax.name}"] = _panel_axis(
            ax,
            axis_to_module.get(ax.name),
            axis_to_aois.get(ax.name, set()),
            p,
        )

    for a in p.aois:
        panels[f"aoi::{a.name}"] = _panel_aoi(a, aoi_partners.get(a.name, set()))

    for u in p.udts:
        panels[f"udt::{u.name}"] = _panel_udt(u)

    for m in p.modules:
        panels[f"module::{m.name}"] = _panel_module(m, p)

    # Panel de observaciones (accesible vía badge en header)
    if p.observations:
        panels["__observations__::__all__"] = _panel_observations(p)

    return panels


def _panel_observations(p: Project) -> str:
    """Panel listando todas las observations agrupadas por (severity, category)."""
    from collections import defaultdict
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for o in p.observations:
        grouped[(o.severity, o.category)].append(o)

    n_warn = sum(1 for o in p.observations if o.severity == "warning")
    n_info = sum(1 for o in p.observations if o.severity == "info")

    parts = [
        f'<div class="panel"><h1>Observaciones automáticas</h1>',
        f'<p class="subtitle">{len(p.observations)} detectadas durante el parseo '
        f'(⚠ {n_warn} warning · ⓘ {n_info} info)</p>',
    ]

    severity_order = {"warning": 0, "info": 1}
    keys = sorted(grouped.keys(), key=lambda k: (severity_order.get(k[0], 9), k[1]))

    cur_sev = None
    for severity, category in keys:
        if severity != cur_sev:
            heading = "⚠ Warnings" if severity == "warning" else "ⓘ Info"
            parts.append(f'<h3>{heading}</h3>')
            cur_sev = severity

        obs_list = grouped[(severity, category)]
        n = len(obs_list)
        sample = obs_list[0]
        sample_msg = sample.message
        if len(sample_msg) > 280:
            sample_msg = sample_msg[:280] + "…"

        all_refs = []
        for o in obs_list:
            all_refs.extend(o.references)
        refs_html = ", ".join(f"<code>{_e(r)}</code>" for r in all_refs) if all_refs else "—"

        parts.append('<div class="obs-group">')
        parts.append(
            f'<div class="obs-head">'
            f'<span class="obs-cat">{_e(category)}</span>'
            f'<span class="obs-count">{n} ocurrencia(s)</span>'
            f'</div>'
        )
        parts.append(f'<p class="obs-msg">{_e(sample_msg)}</p>')
        parts.append(f'<p class="obs-refs"><strong>Referencias:</strong> {refs_html}</p>')
        parts.append('</div>')

    parts.append(
        '<p class="meta">Para `aoi_naming_collision`: navegar al AOI específico '
        'desde el árbol — el panel del AOI muestra el par duplicado y permite revisar '
        'si una versión es legacy o código activo.</p>'
    )
    parts.append('</div>')
    return "".join(parts)


def _aoi_duplicate_partners(p: Project) -> dict[str, set[str]]:
    """Para cada AOI con colisión de naming, set de los nombres pareja."""
    out: dict[str, set[str]] = {}
    for o in p.observations:
        if o.category != "aoi_naming_collision":
            continue
        for ref in o.references:
            partners = set(o.references) - {ref}
            out.setdefault(ref, set()).update(partners)
    return out


def _kv(rows: list[tuple[str, str]]) -> str:
    """Renderiza una tabla key/value usada en los paneles."""
    body = "".join(
        f'<tr><th>{label}</th><td>{value}</td></tr>'
        for label, value in rows
    )
    return f'<table class="kv">{body}</table>'


def _or_dash(s: str | None) -> str:
    return _e(s) if s else "—"


def _trace_note() -> str:
    return ('<p class="meta">Trace de uso completo (writers/readers): '
            'disponible en v0.2 del paquete (<code>tracer.py</code>).</p>')


def _panel_placeholder(title: str, note: str) -> str:
    return (
        f'<div class="panel"><h1>{_e(title)}</h1>'
        f'<p class="meta">{_e(note)}</p></div>'
    )


def _panel_controller_tags(p: Project) -> str:
    n = sum(1 for t in p.tags if t.scope == "controller")
    by_dt = {}
    for t in p.tags:
        if t.scope == "controller":
            by_dt[t.datatype] = by_dt.get(t.datatype, 0) + 1
    top = sorted(by_dt.items(), key=lambda x: -x[1])[:10]
    rows_html = "".join(
        f'<tr><td><code>{_e(dt)}</code></td><td style="text-align:right">{n_}</td></tr>'
        for dt, n_ in top
    )
    return (
        f'<div class="panel"><h1>Controller Tags</h1>'
        f'<p class="subtitle">{n} tags controller-scoped</p>'
        f'<h3>Top datatypes</h3>'
        f'<table class="kv"><thead><tr><th>DataType</th>'
        f'<th style="text-align:right">Count</th></tr></thead><tbody>{rows_html}</tbody></table>'
        f'<p class="meta">Listado individual de tags no expuesto en árbol v0.1 (reduciría la legibilidad). '
        f'Tags individuales accesibles vía el paquete con <code>project.tags</code>.</p></div>'
    )


def _panel_tasks_folder(p: Project) -> str:
    rows = []
    for t in p.tasks:
        scheduled = ", ".join(f"<code>{_e(x)}</code>" for x in t.scheduled_programs) or "—"
        extra = []
        if t.type in ("PERIODIC", "EVENT") and t.rate:
            extra.append(f"rate={t.rate:g}ms")
        if t.priority:
            extra.append(f"priority={t.priority}")
        extra_str = " · ".join(extra)
        rows.append(
            f'<tr><td><code>{_e(t.name)}</code></td>'
            f'<td>{_e(t.type)}</td>'
            f'<td><span class="meta">{_e(extra_str)}</span></td>'
            f'<td>{scheduled}</td></tr>'
        )
    return (
        f'<div class="panel"><h1>Tasks</h1>'
        f'<p class="subtitle">{len(p.tasks)} tasks definidas</p>'
        f'<table class="kv"><thead><tr><th>Nombre</th><th>Tipo</th>'
        f'<th>Parámetros</th><th>Programs</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def _panel_motion_folder(p: Project, primitive_axes) -> str:
    physical = [t for t in primitive_axes if t.datatype != "AXIS_VIRTUAL" and not _looks_like_spare(t.name)]
    virtual = [t for t in primitive_axes if t.datatype == "AXIS_VIRTUAL"]
    spare = [t for t in primitive_axes if _looks_like_spare(t.name)]
    return (
        f'<div class="panel"><h1>Motion Groups</h1>'
        f'<p class="subtitle">{len(primitive_axes)} ejes primitivos detectados</p>'
        + _kv([
            ("Físicos productivos", str(len(physical))),
            ("Virtuales / referencia", str(len(virtual))),
            ("Spare / no productivos", str(len(spare))),
        ])
        + '<p class="meta">El nombre del Motion Group propiamente dicho '
          '(p.ej. <code>"Axis"</code> en Studio 5000) <strong>no está extraído en v0.1</strong> '
          'del paquete — se muestra como agrupación única "Axes". Si la replica fiel '
          'es importante, abrir DT-011 para extender el loader.</p>'
        + '</div>'
    )


def _panel_aois_folder(p: Project) -> str:
    prefixes = _classify_aoi_prefixes(p.aois)
    rows = "".join(
        f'<tr><td><code>{_e(px) if px else "(sin prefijo)"}</code></td>'
        f'<td style="text-align:right">{n}</td></tr>'
        for px, n in prefixes.most_common()
    )
    dups = sum(1 for o in p.observations if o.category == "aoi_naming_collision")
    warn = (f'<div class="badge-warn">⚠ {dups} pares de AOIs con nombres potencialmente '
            f'duplicados detectados — verificar en cada AOI individualmente.</div>') if dups else ""
    return (
        f'<div class="panel"><h1>Add-On Instructions</h1>'
        f'<p class="subtitle">{len(p.aois)} AOIs definidos</p>'
        f'{warn}'
        f'<h3>Distribución por prefijo</h3>'
        f'<table class="kv"><thead><tr><th>Prefijo</th>'
        f'<th style="text-align:right">Count</th></tr></thead><tbody>{rows}</tbody></table>'
        f'</div>'
    )


def _panel_udts_folder(p: Project) -> str:
    sample = sorted(p.udts, key=lambda u: -len(u.members))[:10]
    rows = "".join(
        f'<tr><td><code>{_e(u.name)}</code></td>'
        f'<td style="text-align:right">{len(u.members)}</td></tr>'
        for u in sample
    )
    return (
        f'<div class="panel"><h1>Data Types (UDTs)</h1>'
        f'<p class="subtitle">{len(p.udts)} UDTs definidos</p>'
        f'<h3>Top por número de members</h3>'
        f'<table class="kv"><thead><tr><th>UDT</th>'
        f'<th style="text-align:right">Members</th></tr></thead><tbody>{rows}</tbody></table>'
        f'</div>'
    )


def _panel_io_folder(p: Project) -> str:
    drives = [m for m in p.modules if _is_drive(m.catalog_number)]
    bridges = [m for m in p.modules if _is_bridge(m.catalog_number)]
    adapters = [m for m in p.modules if _is_io_adapter(m.catalog_number)]
    io_mods = [m for m in p.modules if _is_io_module(m.catalog_number)]
    return (
        f'<div class="panel"><h1>I/O Configuration</h1>'
        f'<p class="subtitle">{len(p.modules)} módulos en topología</p>'
        + _kv([
            ("Drives / servos", str(len(drives))),
            ("Bridges / scanners", str(len(bridges))),
            ("I/O adapters", str(len(adapters))),
            ("I/O modules", str(len(io_mods))),
            ("Otros / no clasificados",
             str(len(p.modules) - len(drives) - len(bridges) - len(adapters) - len(io_mods))),
        ])
        + '</div>'
    )


def _panel_task(t, p: Project) -> str:
    progs = ", ".join(f"<code>{_e(x)}</code>" for x in t.scheduled_programs) or "—"
    return (
        f'<div class="panel"><h1>{_e(t.name)}</h1>'
        f'<p class="subtitle">Task · {_e(t.type)}</p>'
        + _kv([
            ("Tipo", _e(t.type)),
            ("Rate", f"{t.rate:g} ms" if t.type in ("PERIODIC", "EVENT") and t.rate else "—"),
            ("Prioridad", str(t.priority) if t.priority else "—"),
            ("Watchdog", f"{t.watchdog:g} ms" if t.watchdog else "—"),
            ("Programs scheduled", progs),
        ])
        + '</div>'
    )


def _panel_program(prog, p: Project) -> str:
    routines = [r for r in p.routines if r.program == prog.name]
    rt_str = ", ".join(f"<code>{_e(r.name)}</code>" for r in sorted(routines, key=lambda x: x.name))
    n_tags = sum(1 for t in p.tags if t.scope == prog.name)
    return (
        f'<div class="panel"><h1>{_e(prog.name)}</h1>'
        f'<p class="subtitle">Program</p>'
        + _kv([
            ("Main routine", f"<code>{_e(prog.main_routine)}</code>" if prog.main_routine else "—"),
            ("Fault routine", f"<code>{_e(prog.fault_routine)}</code>" if prog.fault_routine else "—"),
            ("Disabled", "Sí" if prog.disabled else "No"),
            ("Test edits", "Sí" if prog.test_edits else "No"),
            ("Routines", f"{len(routines)} — {rt_str}" if routines else "0"),
            ("Program tags", str(n_tags)),
        ])
        + '</div>'
    )


def _panel_program_tags(prog, p: Project) -> str:
    tags = [t for t in p.tags if t.scope == prog.name]
    by_dt = {}
    for t in tags:
        by_dt[t.datatype] = by_dt.get(t.datatype, 0) + 1
    top = sorted(by_dt.items(), key=lambda x: -x[1])[:10]
    rows_html = "".join(
        f'<tr><td><code>{_e(dt)}</code></td><td style="text-align:right">{n_}</td></tr>'
        for dt, n_ in top
    )
    return (
        f'<div class="panel"><h1>Program Tags — {_e(prog.name)}</h1>'
        f'<p class="subtitle">{len(tags)} tags program-scoped</p>'
        f'<h3>Top datatypes</h3>'
        f'<table class="kv"><thead><tr><th>DataType</th>'
        f'<th style="text-align:right">Count</th></tr></thead><tbody>{rows_html}</tbody></table>'
        f'</div>'
    )


def _panel_routine(r) -> str:
    code_block = ""
    if r.code:
        code_html = html.escape(r.code)
        code_block = (
            f'<details><summary>Ver código completo ({len(r.code):,} caracteres)</summary>'
            f'<pre><code>{code_html}</code></pre></details>'
        )
    return (
        f'<div class="panel"><h1>{_e(r.name)}</h1>'
        f'<p class="subtitle">Routine · programa <code>{_e(r.program or "")}</code></p>'
        + _kv([
            ("Lenguaje", _e(r.type)),
            ("Programa", f"<code>{_e(r.program or '—')}</code>"),
            ("Descripción", _or_dash(r.description)),
            ("Tamaño del código", f"{len(r.code or ''):,} caracteres"),
        ])
        + code_block
        + '</div>'
    )


def _panel_axis(ax, module, aois_set, p: Project) -> str:
    # Función inferida: prioridad nombre > AOIs filtrados > AOIs todos
    sorted_aois = sorted(aois_set)
    filtered = [a for a in sorted_aois if not _is_generic_aoi(a)]
    if _looks_like_spare(ax.name):
        inferred = "Spare / no productivo"
    elif ax.datatype == "AXIS_VIRTUAL":
        inferred = "Eje virtual / referencia maestra"
    else:
        inferred = (
            _infer_from_tag_name(ax.name)
            or _infer_axis_function(filtered)
            or _infer_axis_function(sorted_aois)
            or "—"
        )

    drive_str = "—"
    channel_str = "—"
    if module:
        # Formato: <code>NombreMódulo</code> (catalog) — coincide con el ejemplo
        # de la spec ("M16_514U1 (2094-BM02)") y le da al técnico el handle
        # exacto del módulo tal como aparece en Studio 5000.
        drive_str = f"<code>{_e(module.name)}</code>"
        if module.catalog_number:
            drive_str += f' <span class="meta">({_e(module.catalog_number)})</span>'
    mm = (ax.motion_module or "").strip()
    if mm and mm != "<NA>" and ":" in mm:
        channel_str = f"<code>{_e(mm.split(':', 1)[1])}</code>"
    elif mm == "<NA>":
        channel_str = '<span class="meta">no asociado en motion_module</span>'

    prog_uses = set()
    for hit in p.search(ax.name):
        parts = hit.location.split("/")
        if len(parts) >= 2 and parts[0] == "Programs":
            prog_uses.add(parts[1])
    progs_str = ", ".join(f"<code>{_e(x)}</code>" for x in sorted(prog_uses)) or "—"

    main_aois_str = (
        ", ".join(f"<code>{_e(a)}</code>" for a in filtered)
        if filtered else "—"
    )
    other_aois = [a for a in sorted_aois if a not in filtered]
    other_aois_str = (
        ", ".join(f"<code>{_e(a)}</code>" for a in other_aois)
        if other_aois else "—"
    )

    return (
        f'<div class="panel"><h1>{_e(ax.name)}</h1>'
        f'<p class="subtitle">Eje · <code>{_e(ax.datatype)}</code></p>'
        + _kv([
            ("Función inferida", _e(inferred) if inferred != "—" else "—"),
            ("Drive físico", drive_str),
            ("Canal", channel_str),
            ("Programa(s) que lo usan", progs_str),
            ("AOIs principales", main_aois_str),
            ("AOIs de servicio (genéricos)", other_aois_str),
            ("Motion module (raw)",
             f"<code>{_e(mm)}</code>" if mm else '<span class="meta">vacío</span>'),
            ("Descripción", _or_dash(ax.description)),
            ("External access", _or_dash(ax.external_access)),
        ])
        + _trace_note()
        + '</div>'
    )


def _panel_module(m: Module, p: Project) -> str:
    cat = m.catalog_number or ""
    if _is_drive(cat):
        category = "Drive / Servo"
    elif _is_bridge(cat):
        category = "Bridge / Scanner"
    elif _is_io_adapter(cat):
        category = "I/O Adapter"
    elif _is_io_module(cat):
        category = "I/O Module"
    else:
        category = '<span class="meta">no clasificado por catálogo</span>'

    if not m.parent_module or m.parent_module == m.name:
        parent_str = '<span class="meta">root del chassis</span>'
    else:
        port_part = (f', port <code>{_e(m.parent_port_id)}</code>'
                     if m.parent_port_id else "")
        parent_str = f"bajo <code>{_e(m.parent_module)}</code>{port_part}"

    children = [c for c in p.modules if c.parent_module == m.name and c.name != m.name]
    children_str = (", ".join(f"<code>{_e(c.name)}</code>" for c in children)
                    if children else "—")

    return (
        f'<div class="panel"><h1>{_e(m.name)}</h1>'
        f'<p class="subtitle">Módulo · {category}</p>'
        + _kv([
            ("Catalog", f"<code>{_e(cat)}</code>"),
            ("Vendor", _or_dash(m.vendor)),
            ("Ubicación física", parent_str),
            ("Inhibido", "Sí ⊘" if m.inhibited else "No"),
            ("MajorFault (config)",
             ('Sí <span class="meta">— atributo de configuración del L5X '
              '(escala fallas al controller), no estado actual del módulo</span>')
             if m.major_fault else "No"),
            ("Nombre explícito", "Sí" if m.has_explicit_name else
             'No <span class="meta">(inferido del catálogo)</span>'),
            ("Hijos", children_str),
        ])
        + '</div>'
    )


def _panel_aoi(a, partners: set[str]) -> str:
    usage_counts: dict[str, int] = {}
    for prm in a.parameters:
        usage_counts[prm.usage or "Other"] = usage_counts.get(prm.usage or "Other", 0) + 1
    usage_str = ", ".join(f"{n} {u}" for u, n in sorted(usage_counts.items())) or "—"

    routines_rows = "".join(
        f'<tr><td><code>{_e(rname)}</code></td><td>{_e(r.type)}</td>'
        f'<td style="text-align:right">{len(r.code or ""):,} chars</td></tr>'
        for rname, r in a.routines.items()
    )
    routines_block = (
        f'<h3>Routines</h3>'
        f'<table class="kv"><thead><tr><th>Nombre</th><th>Tipo</th>'
        f'<th style="text-align:right">Tamaño</th></tr></thead>'
        f'<tbody>{routines_rows}</tbody></table>'
    ) if a.routines else ""

    dup_block = ""
    if partners:
        partners_str = ", ".join(f"<code>{_e(p)}</code>" for p in sorted(partners))
        dup_block = (
            f'<div class="badge-warn">⚠ Esta AOI tiene par(es) potencialmente '
            f'duplicado(s): {partners_str}. Verificar si una versión es legacy '
            f'/ código muerto.</div>'
        )

    return (
        f'<div class="panel"><h1>{_e(a.name)}</h1>'
        f'<p class="subtitle">Add-On Instruction · revisión {_e(a.revision) or "—"}</p>'
        f'{dup_block}'
        + _kv([
            ("Parámetros", f"{len(a.parameters)} ({usage_str})"),
            ("Local tags", str(len(a.local_tags))),
            ("Descripción", _or_dash(a.description)),
        ])
        + routines_block
        + '</div>'
    )


def _panel_udt(u) -> str:
    rows = "".join(
        f'<tr><td><code>{_e(m.name)}</code></td>'
        f'<td><code>{_e(m.datatype)}</code></td>'
        f'<td>{_e(m.dimension) if m.dimension and m.dimension != "0" else "scalar"}</td>'
        f'<td>{"hidden" if m.hidden else ""}</td>'
        f'<td>{_or_dash(m.description)}</td></tr>'
        for m in u.members
    )
    return (
        f'<div class="panel"><h1>{_e(u.name)}</h1>'
        f'<p class="subtitle">User-Defined Type</p>'
        + _kv([
            ("Family", _or_dash(u.family)),
            ("Members", str(len(u.members))),
            ("Descripción", _or_dash(u.description)),
        ])
        + '<h3>Members</h3>'
        + (f'<table class="kv"><thead><tr><th>Name</th><th>DataType</th>'
           f'<th>Dim</th><th>Flags</th><th>Descripción</th></tr></thead>'
           f'<tbody>{rows}</tbody></table>' if u.members else "—")
        + '</div>'
    )


def _md_to_html(text: str) -> str:
    """Parser Markdown→HTML minimal embebido. Cubre lo que produce
    `mapamental.py`: headers (#..######), fenced code (```), tablas (|..|),
    listas '-' con anidación por indent (2 espacios = 1 nivel), bold (**),
    inline code (`).

    Sin dependencias externas (DT-010). HTML-escapa todo el texto fuera de
    marcas markdown. Para Markdown más rico (italic/links/blockquotes) se
    extiende cuando aparezca caso de uso real.
    """
    lines = text.split("\n")
    out: list[str] = []
    para_buf: list[str] = []
    i = 0
    n = len(lines)

    def flush_para() -> None:
        if para_buf:
            joined = " ".join(para_buf).strip()
            if joined:
                out.append(f"<p>{_md_inline(joined)}</p>")
            para_buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            lang = stripped[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # closing fence
            code_html = html.escape("\n".join(code_lines))
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{code_html}</code></pre>")
            continue

        m = re.match(r"^(#{1,6}) +(.*)$", stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_md_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < n:
            sep = lines[i + 1].strip()
            if re.match(r"^\|[\s\-:|]+\|$", sep):
                flush_para()
                consumed = _md_table(lines, i, out)
                i += consumed
                continue

        if re.match(r"^\s*[-*+] +", line):
            flush_para()
            list_lines: list[str] = []
            while i < n:
                cur = lines[i]
                if re.match(r"^\s*[-*+] +", cur):
                    list_lines.append(cur)
                    i += 1
                elif cur.strip() and (cur.startswith(" ") or cur.startswith("\t")):
                    list_lines.append(cur)
                    i += 1
                else:
                    break
            out.append(_md_list(list_lines))
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        para_buf.append(stripped)
        i += 1

    flush_para()
    return "\n".join(out)


def _md_table(lines: list[str], start: int, out: list[str]) -> int:
    """Render una tabla a partir de `lines[start]`. Devuelve nº de líneas consumidas."""
    header = [c.strip() for c in lines[start].strip().strip("|").split("|")]
    aligns: list[str] = []
    for cell in lines[start + 1].strip().strip("|").split("|"):
        c = cell.strip()
        if c.startswith(":") and c.endswith(":"):
            aligns.append("center")
        elif c.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    j = start + 2
    rows: list[list[str]] = []
    while j < len(lines) and lines[j].strip().startswith("|"):
        rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
        j += 1
    parts = ['<table>', '<thead><tr>']
    for k, h in enumerate(header):
        a = aligns[k] if k < len(aligns) else "left"
        parts.append(f'<th style="text-align:{a}">{_md_inline(h)}</th>')
    parts.append('</tr></thead><tbody>')
    for row in rows:
        parts.append('<tr>')
        for k, c in enumerate(row):
            a = aligns[k] if k < len(aligns) else "left"
            parts.append(f'<td style="text-align:{a}">{_md_inline(c)}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')
    out.append("".join(parts))
    return j - start


def _md_list(list_lines: list[str]) -> str:
    """Render lista UL con anidación por indent (2 espacios = 1 nivel)."""
    items: list[tuple[int, str]] = []
    cur_depth = 0
    cur_text: list[str] = []
    for ln in list_lines:
        m = re.match(r"^(\s*)([-*+]) +(.*)$", ln)
        if m:
            if cur_text:
                items.append((cur_depth, " ".join(cur_text)))
                cur_text = []
            cur_depth = len(m.group(1)) // 2
            cur_text.append(m.group(3))
        else:
            if cur_text:
                cur_text.append(ln.strip())
    if cur_text:
        items.append((cur_depth, " ".join(cur_text)))

    rendered, _ = _md_list_render(items, 0, 0)
    return rendered


def _md_list_render(items: list[tuple[int, str]], idx: int, depth: int) -> tuple[str, int]:
    parts = ["<ul>"]
    while idx < len(items):
        d, text = items[idx]
        if d < depth:
            break
        if d > depth:
            idx += 1
            continue
        nxt = idx + 1
        if nxt < len(items) and items[nxt][0] > d:
            inner, nxt = _md_list_render(items, nxt, d + 1)
            parts.append(f"<li>{_md_inline(text)}{inner}</li>")
        else:
            parts.append(f"<li>{_md_inline(text)}</li>")
        idx = nxt
    parts.append("</ul>")
    return "".join(parts), idx


def _md_inline(text: str) -> str:
    """Inline transforms: `code` y **bold**. HTML-escapa el resto."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "`":
            end = text.find("`", i + 1)
            if end == -1:
                out.append(html.escape(text[i:]))
                break
            out.append(f"<code>{html.escape(text[i + 1:end])}</code>")
            i = end + 1
        else:
            nxt = text.find("`", i)
            chunk = text[i:] if nxt == -1 else text[i:nxt]
            escaped = html.escape(chunk)
            escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
            out.append(escaped)
            i = n if nxt == -1 else nxt
    return "".join(out)


_CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 13px; color: #1f2328; background: #fff;
}
.topbar {
  background: #1f6feb; color: #fff; padding: 8px 14px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
.topbar .title { display: flex; gap: 8px; align-items: center; font-weight: 600; }
.topbar .proj-name { font-size: 14px; }
.topbar .sep { opacity: 0.5; font-weight: normal; }
.topbar .proc, .topbar .ver { opacity: 0.92; font-weight: normal; }
.topbar .controls { display: flex; align-items: center; gap: 12px; }
.topbar .controls input[type="search"] {
  background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.4);
  color: #fff; padding: 4px 8px; border-radius: 3px; font-size: 12px;
  min-width: 220px; outline: none;
}
.topbar .controls input[type="search"]::placeholder { color: rgba(255,255,255,0.7); }
.topbar .controls input[type="search"]:focus {
  background: rgba(255,255,255,0.28); border-color: rgba(255,255,255,0.7);
}
.topbar .filter-toggle {
  font-size: 12px; cursor: pointer; user-select: none;
  display: inline-flex; align-items: center; gap: 4px; opacity: 0.95;
}
.topbar .filter-toggle input { margin: 0; cursor: pointer; }
.topbar .obs-badge {
  border: 0; padding: 4px 10px; border-radius: 3px; cursor: pointer;
  font-size: 12px; font-weight: 600; white-space: nowrap;
}
.topbar .obs-badge.warn { background: #fef0d6; color: #6b4500; }
.topbar .obs-badge.info { background: #dbeafe; color: #1e40af; }
.topbar .obs-badge:hover { filter: brightness(0.95); }
.layout { display: flex; height: calc(100vh - 36px); }
.tree-pane {
  flex: 0 0 380px; min-width: 240px; max-width: 50%;
  overflow: auto; padding: 8px 0;
  background: #f6f8fa; border-right: 1px solid #d0d7de; resize: horizontal;
}
.detail-pane {
  flex: 1 1 auto; overflow: auto; background: #fff;
}
.detail-content {
  max-width: 980px; padding: 18px 28px 40px 28px; line-height: 1.55;
}
.detail-content h1, .detail-content h2, .detail-content h3,
.detail-content h4, .detail-content h5, .detail-content h6 {
  font-weight: 600; margin: 1.2em 0 0.4em 0; line-height: 1.25;
}
.detail-content h1 { font-size: 22px; border-bottom: 1px solid #d0d7de; padding-bottom: 6px; }
.detail-content h2 { font-size: 18px; border-bottom: 1px solid #eaeef2; padding-bottom: 4px; margin-top: 1.6em; }
.detail-content h3 { font-size: 15px; }
.detail-content h4 { font-size: 13.5px; color: #57606a; }
.detail-content p { margin: 0.4em 0; }
.detail-content ul { margin: 0.3em 0 0.6em 0; padding-left: 22px; }
.detail-content li { margin: 0.15em 0; }
.detail-content code {
  background: #eef1f4; padding: 1px 4px; border-radius: 3px;
  font-family: 'Cascadia Code', Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
}
.detail-content pre {
  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px;
  padding: 10px 12px; overflow: auto; line-height: 1.4;
}
.detail-content pre code {
  background: transparent; padding: 0; font-size: 12px;
}
.detail-content table {
  border-collapse: collapse; margin: 0.6em 0; font-size: 12.5px;
}
.detail-content th, .detail-content td {
  border: 1px solid #d0d7de; padding: 4px 8px;
}
.detail-content thead th { background: #f6f8fa; font-weight: 600; }
.detail-content strong { font-weight: 600; }
.tree, .tree ul { list-style: none; margin: 0; padding-left: 18px; }
.tree { padding-left: 6px; }
.node { padding: 1px 0; line-height: 1.6; user-select: none; }
.node > .caret {
  display: inline-block; width: 12px; height: 12px; text-align: center;
  cursor: pointer; color: #57606a; vertical-align: middle;
}
.node > .caret::before {
  content: "▶"; font-size: 9px; display: inline-block;
  transition: transform 0.1s;
}
.node.open > .caret::before { transform: rotate(90deg); }
.node.leaf > .caret { visibility: hidden; }
.node > .icon { margin: 0 4px 0 2px; }
.node > .label { padding: 1px 4px; border-radius: 3px; cursor: pointer; }
.node > .label:hover { background: #e6edf3; }
.node.selected > .label { background: #cfe1fd; outline: 1px solid #1f6feb; }
.node > ul { display: none; }
.node.open > ul { display: block; }
.node.hidden { display: none; }
.node.match > .label { background: #fff3a4; }
.node.match > .label:hover { background: #fbe372; }
.meta { color: #6e7781; font-weight: normal; font-size: 11px; }
.warn { color: #b35900; font-size: 11px; margin-left: 4px; }
.panel .obs-group {
  border: 1px solid #d0d7de; border-radius: 4px;
  padding: 10px 14px; margin: 10px 0; background: #fafbfc;
}
.panel .obs-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 6px;
}
.panel .obs-cat {
  font-family: 'Cascadia Code', Consolas, monospace;
  font-size: 12px; font-weight: 600; color: #1f2328;
}
.panel .obs-count {
  font-size: 11px; color: #57606a; font-weight: 500;
}
.panel .obs-msg { margin: 4px 0; font-size: 12.5px; color: #1f2328; }
.panel .obs-refs { margin: 4px 0; font-size: 12px; color: #57606a; }
.panel h1 { font-size: 22px; margin: 0 0 4px 0; padding: 0; border: 0; }
.panel .subtitle {
  color: #57606a; font-size: 13px; margin: 0 0 14px 0;
}
.panel h3 {
  font-size: 14px; font-weight: 600; margin: 18px 0 6px 0;
  color: #1f2328;
}
.panel table.kv {
  border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 13px;
}
.panel table.kv th {
  text-align: left; padding: 5px 14px 5px 0; vertical-align: top;
  color: #57606a; font-weight: 500; width: 200px; white-space: nowrap;
  border: 0;
}
.panel table.kv td {
  padding: 5px 0; vertical-align: top; border: 0;
}
.panel table.kv thead th {
  border-bottom: 1px solid #d0d7de; padding: 4px 8px; background: transparent;
  font-weight: 600; color: #1f2328; width: auto; white-space: normal;
}
.panel table.kv tbody td { padding: 4px 8px; border-bottom: 1px solid #eaeef2; }
.panel .badge-warn {
  background: #fef0d6; border: 1px solid #f1c47a; color: #6b4500;
  padding: 8px 12px; border-radius: 4px; margin: 12px 0; font-size: 12.5px;
}
.panel details { margin: 14px 0; }
.panel details summary {
  cursor: pointer; font-weight: 500; padding: 6px 8px;
  color: #1f6feb; background: #f6f8fa; border: 1px solid #d0d7de;
  border-radius: 4px; user-select: none;
}
.panel details[open] summary { margin-bottom: 8px; }
.panel details pre {
  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px;
  padding: 10px 12px; overflow: auto; line-height: 1.4;
  font-size: 12px; max-height: 500px;
}
.panel details pre code { background: transparent; padding: 0; font-size: 12px; }
"""


_JS = """
(function() {
  const root = document.getElementById('root');
  const detail = document.querySelector('#detail .detail-content');
  const search = document.getElementById('search-input');
  const hideTagsCb = document.getElementById('filter-hide-tags');
  const obsBadge = document.getElementById('obs-badge');
  if (!root) return;

  let panels = {};
  try {
    const dataNode = document.getElementById('panels-data');
    if (dataNode) panels = JSON.parse(dataNode.textContent);
  } catch (err) {
    console.error('Explorer: no se pudo parsear panels-data', err);
  }

  function toggle(li) {
    if (li && !li.classList.contains('leaf')) li.classList.toggle('open');
  }

  function showPanel(li) {
    if (!li || !detail) return;
    const type = li.dataset.type;
    const id = li.dataset.id;
    const key = type + '::' + id;
    const html = panels[key];
    if (typeof html === 'string') {
      detail.innerHTML = html;
    } else {
      const lbl = li.querySelector(':scope > .label');
      const name = lbl ? lbl.textContent.trim() : '?';
      detail.innerHTML = '<div class="panel"><h1>' + name +
        '</h1><p class="meta">No hay panel definido para este nodo en v0.1 ' +
        '(type=' + type + ', id=' + id + ').</p></div>';
    }
    detail.parentElement.scrollTop = 0;
  }

  function applyFilters() {
    const q = (search && search.value || '').trim().toLowerCase();
    const hideTags = hideTagsCb && hideTagsCb.checked;
    const all = root.querySelectorAll('.node');
    all.forEach(li => li.classList.remove('hidden', 'match'));

    if (hideTags) {
      root.querySelectorAll(
        '.node[data-type="controller-tags"], .node[data-type="program-tags"]'
      ).forEach(li => li.classList.add('hidden'));
    }

    if (!q) return;

    // Find matches (skipping already-hidden by filter)
    all.forEach(li => {
      if (li.classList.contains('hidden')) return;
      const lbl = li.querySelector(':scope > .label');
      if (!lbl) return;
      if (lbl.textContent.toLowerCase().includes(q)) {
        li.classList.add('match');
      }
    });

    // Compute keepVisible: matches + their descendants + their ancestors (auto-expanded)
    const keep = new Set();
    root.querySelectorAll('.node.match').forEach(m => {
      keep.add(m);
      m.querySelectorAll('.node').forEach(d => keep.add(d));
      let n = m.parentElement && m.parentElement.closest('.node');
      while (n) {
        keep.add(n);
        if (!n.classList.contains('leaf')) n.classList.add('open');
        n = n.parentElement && n.parentElement.closest('.node');
      }
    });

    all.forEach(li => {
      if (!keep.has(li)) li.classList.add('hidden');
    });
  }

  if (search) search.addEventListener('input', applyFilters);
  if (hideTagsCb) hideTagsCb.addEventListener('change', applyFilters);

  if (obsBadge) {
    obsBadge.addEventListener('click', function() {
      const html = panels['__observations__::__all__'];
      if (typeof html === 'string') {
        detail.innerHTML = html;
        detail.parentElement.scrollTop = 0;
        document.querySelectorAll('.node.selected').forEach(n => n.classList.remove('selected'));
      }
    });
  }

  root.addEventListener('click', function(e) {
    const t = e.target;
    if (t.classList.contains('caret')) {
      toggle(t.closest('.node'));
      e.stopPropagation();
      return;
    }
    const labelEl = t.classList.contains('label') ? t : (t.closest && t.closest('.label'));
    if (labelEl) {
      document.querySelectorAll('.node.selected').forEach(n => n.classList.remove('selected'));
      const li = labelEl.closest('.node');
      if (li) {
        li.classList.add('selected');
        showPanel(li);
      }
    }
  });

  root.addEventListener('dblclick', function(e) {
    const t = e.target;
    const labelEl = t.classList.contains('label') ? t : (t.closest && t.closest('.label'));
    if (labelEl) toggle(labelEl.closest('.node'));
  });
})();
"""
