"""
reporters/mermaid.py — Generación de diagramas Mermaid.

API pública:
    to_mermaid(project, kind) -> str

Donde kind ∈ {"topology", "iotree", "tasks"}.

Cada función produce un bloque Mermaid renderizable (sin las cercas ```mermaid).
El consumidor lo envuelve si necesita.

Decisiones de diseño v0.1:
- IDs sintéticos `n0`, `n1`, ... evitan problemas con caracteres especiales en
  nombres reales (espacios, paréntesis, slashes en catalog numbers).
- Etiquetas se usan para el texto visible, IDs para las flechas.
- Para topology e iotree: graph TD (top-down, refleja el árbol natural).
- Para tasks: graph LR (left-right, mejor para mostrar flujo task → program).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from ..model import Module, Project


# ─────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────

_VALID_KINDS = {"topology", "iotree", "tasks"}


def to_mermaid(project: Project, kind: str) -> str:
    """Genera un diagrama Mermaid del proyecto.

    Args:
        project: Project ya cargado
        kind: tipo de diagrama. Uno de:
            - "topology": árbol completo de módulos (parent → child)
            - "iotree":   subset filtrado a I/O y adapters
            - "tasks":    Tasks → Programs → Routines

    Returns:
        String con bloque Mermaid (sin las cercas ```mermaid).

    Raises:
        ValueError: si kind no es uno de los soportados.
    """
    if kind not in _VALID_KINDS:
        raise ValueError(
            f"kind={kind!r} no soportado. Usar uno de: {sorted(_VALID_KINDS)}"
        )

    if kind == "topology":
        return _topology(project)
    if kind == "iotree":
        return _iotree(project)
    if kind == "tasks":
        return _tasks(project)
    # Unreachable
    return ""


# ─────────────────────────────────────────────────────────────────────────
# topology — árbol completo de módulos
# ─────────────────────────────────────────────────────────────────────────


def _topology(p: Project) -> str:
    """Diagrama del árbol de módulos físicos."""
    if not p.modules:
        return "graph TD\n    empty[Sin módulos]"

    # Asignar IDs sintéticos estables
    id_by_name: dict[str, str] = {}
    for i, m in enumerate(p.modules):
        id_by_name[m.name] = f"n{i}"

    # Índice parent → [hijos]
    children: dict[str, list[Module]] = defaultdict(list)
    roots: list[Module] = []
    for m in p.modules:
        if not m.parent_module or m.parent_module == m.name:
            roots.append(m)
        elif m.parent_module in id_by_name:
            children[m.parent_module].append(m)
        else:
            # parent referenciado pero no presente como módulo: tratar como raíz
            roots.append(m)

    lines: list[str] = ["graph TD"]
    # Definir nodos con etiqueta
    for m in p.modules:
        nid = id_by_name[m.name]
        label = _node_label(m)
        cls = _node_class(m)
        lines.append(f'    {nid}["{label}"]:::{cls}')
    # Aristas
    for m in p.modules:
        for child in children.get(m.name, []):
            lines.append(f"    {id_by_name[m.name]} --> {id_by_name[child.name]}")

    # Estilos por clase
    lines.extend(_class_definitions())
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# iotree — subset I/O del árbol
# ─────────────────────────────────────────────────────────────────────────


def _iotree(p: Project) -> str:
    """Subset del árbol filtrado a I/O adapters + módulos I/O.

    Incluye también el camino desde el chassis local hasta los adapters,
    para que los nodos no queden colgando.
    """
    if not p.modules:
        return "graph TD\n    empty[Sin módulos]"

    # Marcamos qué módulos son I/O o están en el camino a un I/O
    relevant: set[str] = set()
    for m in p.modules:
        if _is_io_or_adapter(m):
            relevant.add(m.name)
            # Subir por la cadena de parents para incluir el camino
            current_parent = m.parent_module
            while current_parent:
                relevant.add(current_parent)
                # Encontrar el padre del padre
                next_parent = None
                for mm in p.modules:
                    if mm.name == current_parent:
                        next_parent = mm.parent_module
                        if next_parent == mm.name:
                            next_parent = None
                        break
                current_parent = next_parent

    if not relevant:
        return "graph TD\n    empty[Sin módulos I/O detectados]"

    # Construir el grafo solo con los relevantes
    id_by_name: dict[str, str] = {}
    for i, m in enumerate(p.modules):
        if m.name in relevant:
            id_by_name[m.name] = f"n{i}"

    lines: list[str] = ["graph TD"]
    for m in p.modules:
        if m.name not in relevant:
            continue
        nid = id_by_name[m.name]
        label = _node_label(m)
        cls = _node_class(m)
        lines.append(f'    {nid}["{label}"]:::{cls}')

    for m in p.modules:
        if m.name not in relevant:
            continue
        # Saltar self-loops: el chassis raíz (Local) tiene ParentModule="Local"
        if m.parent_module == m.name:
            continue
        if m.parent_module and m.parent_module in id_by_name:
            lines.append(
                f"    {id_by_name[m.parent_module]} --> {id_by_name[m.name]}"
            )

    lines.extend(_class_definitions())
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# tasks — Tasks → Programs → Routines
# ─────────────────────────────────────────────────────────────────────────


def _tasks(p: Project) -> str:
    """Diagrama de Tasks scheduling: Task → Program → Routines."""
    if not p.tasks:
        return "graph LR\n    empty[Sin tasks]"

    lines: list[str] = ["graph LR"]
    counter = 0
    task_ids: dict[str, str] = {}
    program_ids: dict[str, str] = {}

    # Definir nodos task
    for t in p.tasks:
        task_id = f"t{counter}"
        counter += 1
        task_ids[t.name] = task_id
        rate_str = ""
        if t.type == "PERIODIC" and t.rate:
            rate_str = f"<br/>{t.rate:g}ms"
        label = f"{t.name}<br/>[{t.type}]{rate_str}"
        lines.append(f'    {task_id}(("{label}")):::task')

    # Definir nodos program (asociados a tasks)
    program_routines: dict[str, list[str]] = defaultdict(list)
    for r in p.routines:
        if r.program:
            program_routines[r.program].append(r.name)

    for t in p.tasks:
        for prog_name in t.scheduled_programs:
            if prog_name not in program_ids:
                pid = f"p{counter}"
                counter += 1
                program_ids[prog_name] = pid
                n_rt = len(program_routines.get(prog_name, []))
                rt_str = f"<br/>{n_rt} rutina(s)" if n_rt else ""
                lines.append(f'    {pid}["{prog_name}{rt_str}"]:::program')
            # Arista task → program
            lines.append(f"    {task_ids[t.name]} --> {program_ids[prog_name]}")

    # Programs sin task asociada: nodos sueltos para no perderlos
    all_program_names = {pr.name for pr in p.programs}
    orphan = all_program_names - set(program_ids.keys())
    for prog_name in sorted(orphan):
        pid = f"p{counter}"
        counter += 1
        program_ids[prog_name] = pid
        lines.append(f'    {pid}["{prog_name}<br/>(sin task)"]:::orphan')

    # Estilos
    lines.append("    classDef task fill:#305496,stroke:#1a3a6f,color:#fff")
    lines.append("    classDef program fill:#d9e1f2,stroke:#305496,color:#000")
    lines.append("    classDef orphan fill:#f4cccc,stroke:#cc0000,color:#000")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────


# Mismas listas que mapamental.py (clasificación de módulos por catálogo)
_DRIVE_PREFIXES = ("2094-", "2198-", "2097-", "2090-")
_BRIDGE_PREFIXES = (
    "1768-ENBT", "1768-EWEB", "1768-M04SE", "1768-M16SE", "1768-CNB",
    "1756-ENBT", "1756-EN2T", "1756-EN3T", "1756-EN2TR", "1756-CNB",
    "1756-M16SE", "1756-M08SE", "1756-CN2", "1756-CN2R",
    "1769-L", "1768-L", "1756-L",
)
_ADAPTER_PREFIXES = ("1734-AENT", "1734-ACNR", "1738-AENT", "1794-AENT", "1769-AENTR")
_IO_MODULE_PREFIXES = ("1734-", "1738-", "1794-", "1756-I", "1756-O", "1769-I", "1769-O")


def _is_drive(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _DRIVE_PREFIXES)


def _is_bridge(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _BRIDGE_PREFIXES)


def _is_io_adapter(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _ADAPTER_PREFIXES)


def _is_io_module(catalog: str) -> bool:
    if _is_io_adapter(catalog):
        return False
    return any(catalog.startswith(p) for p in _IO_MODULE_PREFIXES)


def _is_io_or_adapter(m: Module) -> bool:
    return _is_io_adapter(m.catalog_number) or _is_io_module(m.catalog_number)


def _node_label(m: Module) -> str:
    """Texto visible en el nodo Mermaid. Escapa caracteres problemáticos."""
    name = m.name if m.has_explicit_name else f"({m.catalog_number})"
    label = f"{name}<br/>{m.catalog_number}"
    # Escapar comillas dobles y caracteres que rompen Mermaid
    return label.replace('"', "'")


def _node_class(m: Module) -> str:
    """Clase CSS para el nodo según tipo de módulo."""
    cn = m.catalog_number
    if _is_drive(cn):
        return "drive"
    if _is_bridge(cn):
        return "bridge"
    if _is_io_adapter(cn):
        return "adapter"
    if _is_io_module(cn):
        return "io"
    return "other"


def _class_definitions() -> Iterable[str]:
    """Definiciones de clase CSS para colorear nodos por categoría."""
    return [
        "    classDef drive fill:#fce4d6,stroke:#c65911,color:#000",
        "    classDef bridge fill:#deebf7,stroke:#2e75b6,color:#000",
        "    classDef adapter fill:#e2efda,stroke:#548235,color:#000",
        "    classDef io fill:#fff2cc,stroke:#bf8f00,color:#000",
        "    classDef other fill:#f2f2f2,stroke:#7f7f7f,color:#000",
    ]
