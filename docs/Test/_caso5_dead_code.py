"""Caso #5 — detección de código muerto en proyectos Rockwell L5X.

Usa la API ya construida del paquete (project.references_of() del tracer
v0.2 + project.routines/aois/programs/tags) para detectar 3 categorías
clásicas de código muerto:

  1. **Tags controller-scoped huérfanos** — sin readers ni writers en
     código. Se filtran AXIS_*, MOTION_GROUP, TASK, MESSAGE, etc.
     que típicamente no aparecen como operandos en código RLL/ST.

  2. **AOIs definidas pero no invocadas** — para cada AOI, se busca su
     nombre como operador (instr) en el código tokenizado. El gap del
     `search()` (no indexa nombres de AOIs) se workarondea con un regex
     boundary `r"\\b{aoi}\\("` aplicado sobre el code string de cada
     routine — más preciso que substring (evita falsos positivos como
     "FullSpeedSplicer" matcheando "FullSpeedSplicer2").

  3. **Routines no llamadas** — routines de programa (no de AOI) que NO
     son main_routine ni fault_routine de su program y que no aparecen
     como target de un JSR(target,...) en ninguna otra routine del MISMO
     program (limitación de Studio 5000: JSR es intra-program).

Caveats honestos:
  - Una AOI puede estar referenciada solo desde tags estructurados (sin
    invocación directa) → falso positivo "no invocada" si el AOI define
    instance data y otro código manipula esos miembros sin invocarlo.
  - Routines pueden invocarse vía mecanismos no detectados (Add-On Profile,
    SBR sin JSR explícito en este program, etc.). Se documenta como límite.
  - Tags controller AXIS_*, MOTION_GROUP, etc. se EXCLUYEN del cálculo de
    huérfanos: son referenciados por configuración (motion module) no por
    código RLL/ST, y `references_of` solo ve referencias en código.

Uso:
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 \\
      python docs/Test/_caso5_dead_code.py parque_l5x/CINTA_LAMINADA_M2_2024.L5X

Salida: stdout legible. main() devuelve dict structured para reuso en tests.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Ejecutable desde la raíz del repo sin instalar
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rockwell_comprehender import load_project


# Tipos de datatype controller-scoped que NO se referencian en código RLL/ST
# y que por tanto saldrían como "huérfanos" sin serlo realmente. Son
# referenciados por configuración (motion module, task, message, etc.).
EXCLUDED_DATATYPE_PREFIXES = (
    "AXIS_",
    "MOTION_GROUP",
    "COORDINATE_SYSTEM",
    "TASK",
    "PROGRAM",
    "ROUTINE",
    "MODULE",
    "MESSAGE",
    "CONNECTION_STATUS",
    "ALARM",
)


def find_dead_aois(project) -> list[tuple[str, bool]]:
    """Detecta AOIs definidas pero no invocadas desde ningún código.

    Returns: list de (aoi_name, is_protected) ordenado por nombre.
    """
    aoi_names = {a.name for a in project.aois}
    invoked = set()

    # Patrón AOI invocation: NombreAOI seguido de paréntesis.
    # Estricto con \b para evitar match parcial (FullSpeedSplicer en FullSpeedSplicer2).
    # Una sola pasada por TODO el código.
    def scan_code(code: str, exclude_self: str | None) -> None:
        for aoi_name in aoi_names:
            if aoi_name == exclude_self:
                continue
            if aoi_name in invoked:
                continue
            if re.search(rf"\b{re.escape(aoi_name)}\(", code):
                invoked.add(aoi_name)

    for r in project.routines:
        if r.code:
            scan_code(r.code, exclude_self=None)

    for a in project.aois:
        for rname, r in a.routines.items():
            if r.code:
                scan_code(r.code, exclude_self=a.name)

    dead = []
    for a in project.aois:
        if a.name not in invoked:
            dead.append((a.name, a.protected))
    return sorted(dead, key=lambda x: x[0])


def find_unreachable_routines(project) -> list[tuple[str, str, str]]:
    """Detecta routines de programa no llamadas desde main_routine ni JSR.

    Returns: list de (program, routine_name, reason) ordenado.
    """
    # main_routine + fault_routine de cada program son entry points
    entry_points: set[tuple[str, str]] = set()
    for p in project.programs:
        if p.main_routine:
            entry_points.add((p.name, p.main_routine))
        if p.fault_routine:
            entry_points.add((p.name, p.fault_routine))

    # JSR(target, ...) intra-program. JSR en Studio 5000 solo llama
    # routines del MISMO program; cross-program no aplica.
    jsr_pattern = re.compile(r"\bJSR\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
    called: set[tuple[str, str]] = set()

    for r in project.routines:
        if not r.code or not r.program:
            continue
        for m in jsr_pattern.finditer(r.code):
            target = m.group(1)
            called.add((r.program, target))

    # JSR puede aparecer también en código de AOIs invocando routines del
    # program que las hostea — no se modela aquí (caso raro), se anota como
    # caveat en el reporte.

    unreachable = []
    for r in project.routines:
        if not r.program:
            continue  # routines de AOI: siempre alcanzables vía la invocación del AOI
        key = (r.program, r.name)
        if key in entry_points:
            continue
        if key in called:
            continue
        reason = "no main/fault routine + sin JSR target en ninguna routine del program"
        unreachable.append((r.program, r.name, reason))

    return sorted(unreachable, key=lambda x: (x[0], x[1]))


def find_orphan_controller_tags(project) -> list[tuple[str, str]]:
    """Detecta tags controller-scoped sin referencias en código.

    Returns: list de (tag_name, datatype) ordenado.
    """
    orphans = []
    for t in project.tags:
        if t.scope != "controller":
            continue
        # Excluir tipos referenciados por configuración, no por código
        if any(t.datatype.upper().startswith(p) for p in EXCLUDED_DATATYPE_PREFIXES):
            continue
        # Excluir tags con motion_module asignado (referenciados por config)
        if t.motion_module:
            continue
        # Excluir constants (definidos pero pueden no aparecer en código si son
        # documentación inline; aún los reportamos pero los marcamos)
        try:
            refs = project.references_of(t.name)
        except Exception as e:
            # Si references_of falla, no inventamos workaround — anotar
            print(f"  [WARN] references_of('{t.name}') falló: {e}", file=sys.stderr)
            continue
        if not refs:
            orphans.append((t.name, t.datatype))
    return sorted(orphans, key=lambda x: x[0])


def main(l5x_path: str) -> dict:
    """Ejecuta las 3 detecciones contra un L5X y devuelve dict structured."""
    project = load_project(l5x_path)
    iden = project.identity

    print("=" * 78)
    print(f"Caso #5 — Detección de código muerto")
    print(f"L5X: {l5x_path}")
    print(f"Target: {iden.target_name}  ·  Processor: {iden.processor_type}  "
          f"·  SW: v{iden.software_revision}")
    print(f"Inventario: programs={len(project.programs)}  routines={len(project.routines)}  "
          f"aois={len(project.aois)}  tags(controller)={sum(1 for t in project.tags if t.scope=='controller')}")
    print("=" * 78)

    # 1. AOIs no invocadas
    print("\n## 1. AOIs definidas pero NO invocadas\n")
    dead_aois = find_dead_aois(project)
    if not dead_aois:
        print("(ninguna)")
    else:
        for name, protected in dead_aois:
            tag = " [PROTECTED]" if protected else ""
            print(f"  - {name}{tag}")
        print(f"\n  TOTAL: {len(dead_aois)} AOIs no invocadas de {len(project.aois)} definidas")

    # 2. Routines no alcanzables
    print("\n## 2. Routines no llamadas (no main/fault, sin JSR target)\n")
    unreachable = find_unreachable_routines(project)
    if not unreachable:
        print("(ninguna)")
    else:
        for program, routine, reason in unreachable:
            print(f"  - {program}/{routine}")
        total_program_routines = sum(1 for r in project.routines if r.program)
        print(f"\n  TOTAL: {len(unreachable)} routines no alcanzables "
              f"de {total_program_routines} routines de program")

    # 3. Tags controller huérfanos
    print("\n## 3. Tags controller-scoped huérfanos (sin refs en código)\n")
    orphan_tags = find_orphan_controller_tags(project)
    if not orphan_tags:
        print("(ninguno tras filtros AXIS_*/MOTION_GROUP/TASK/MESSAGE/etc.)")
    else:
        # Limitar print a primeros 50 para legibilidad; total al final
        for name, datatype in orphan_tags[:50]:
            print(f"  - {name:50s} : {datatype}")
        if len(orphan_tags) > 50:
            print(f"  ... y {len(orphan_tags) - 50} más")
        controller_tags_total = sum(1 for t in project.tags if t.scope == "controller")
        excluded_count = sum(
            1 for t in project.tags
            if t.scope == "controller"
            and (any(t.datatype.upper().startswith(p) for p in EXCLUDED_DATATYPE_PREFIXES)
                 or t.motion_module)
        )
        analyzed = controller_tags_total - excluded_count
        print(f"\n  TOTAL: {len(orphan_tags)} huérfanos de {analyzed} tags analizados "
              f"(de {controller_tags_total} controller; {excluded_count} excluidos por filtros)")

    print("\n" + "=" * 78)
    print("FIN")
    print("=" * 78)

    return {
        "l5x_path": l5x_path,
        "identity": {
            "target_name": iden.target_name,
            "processor_type": iden.processor_type,
            "software_revision": iden.software_revision,
        },
        "dead_aois": dead_aois,
        "unreachable_routines": unreachable,
        "orphan_tags": orphan_tags,
        "totals": {
            "aois_total": len(project.aois),
            "program_routines_total": sum(1 for r in project.routines if r.program),
            "controller_tags_total": sum(1 for t in project.tags if t.scope == "controller"),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python {sys.argv[0]} <l5x_path>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
