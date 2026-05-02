"""
mapamental.py — Generador del Mapa Mental general (Capa 1 de la arquitectura).

Función principal:
    generate(project: Project) -> str

Produce un documento Markdown autocontenido (~800–1500 tokens) con seis
secciones:
    1. Identidad
    2. Arquitectura física
    3. Arquitectura lógica
    4. Mapa funcional de ejes (si tiene motion)
    5. Patrones de código
    6. Issues / observaciones

Si el documento generado excede el target en proyectos grandes, las secciones
posteriores (patrones, issues) son las primeras candidatas a recortar — la
prioridad es la pirámide identidad > física > lógica > ejes > patrones > issues.

Heurísticas implementadas:
- Detección de ejes: tags controller-scoped con datatype AXIS_*
- Mapeo eje → función: regex sobre invocaciones de AOIs en código de programas,
  detectando qué tag de eje se pasa como argumento
- Topología de red: análisis de relaciones parent-child entre Modules
- Patrones: conteo de tipos de rutinas (RLL/ST/FBD), prefijos de AOIs,
  estructura de datos por eje (M*Data style)
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Iterable

from .model import (
    AOIDetail,
    Module,
    Observation,
    Project,
    Tag,
)


# ─────────────────────────────────────────────────────────────────────────
# Función pública
# ─────────────────────────────────────────────────────────────────────────


def generate(project: Project) -> str:
    """Genera el documento Markdown del Mapa Mental."""
    sections = [
        _section_identidad(project),
        _section_arquitectura_fisica(project),
        _section_arquitectura_logica(project),
        _section_mapa_funcional_ejes(project),
        _section_patrones_codigo(project),
        _section_issues(project),
    ]
    return "\n\n".join(s for s in sections if s)


# ─────────────────────────────────────────────────────────────────────────
# Sección 1 — Identidad
# ─────────────────────────────────────────────────────────────────────────


def _section_identidad(p: Project) -> str:
    i = p.identity
    parts = [
        f"# Mapa Mental — {i.target_name or '(sin-nombre)'}",
        "",
        "## Identidad",
        "",
        f"- **Controlador:** `{i.processor_type}` (firmware {i.major_rev}.{i.minor_rev})",
        f"- **Studio 5000:** v{i.software_revision}",
        f"- **Schema L5X:** {i.schema_revision}",
    ]
    if i.project_creation_date:
        parts.append(f"- **Creado:** {i.project_creation_date}")
    if i.last_modified_date:
        parts.append(f"- **Última modificación:** {i.last_modified_date}")
    if i.owner:
        parts.append(f"- **Owner del export:** {i.owner}")
    if i.export_date:
        parts.append(f"- **Fecha de export:** {i.export_date}")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────
# Sección 2 — Arquitectura física
# ─────────────────────────────────────────────────────────────────────────


def _section_arquitectura_fisica(p: Project) -> str:
    if not p.modules:
        return ""

    # Construir índice parent → [hijos]
    children: dict[str, list[Module]] = defaultdict(list)
    roots: list[Module] = []
    for m in p.modules:
        if not m.parent_module or m.parent_module == m.name:
            roots.append(m)
        else:
            children[m.parent_module].append(m)

    # Clasificar tipos por catalog number
    drives = [m for m in p.modules if _is_drive(m.catalog_number)]
    bridges = [m for m in p.modules if _is_bridge(m.catalog_number)]
    io_adapters = [m for m in p.modules if _is_io_adapter(m.catalog_number)]
    io_modules = [m for m in p.modules if _is_io_module(m.catalog_number)]

    parts = [
        "## Arquitectura física",
        "",
        f"Topología: **{len(p.modules)} módulos** organizados en árbol bajo el chassis local.",
        "",
        "### Topología (árbol parent → child)",
        "",
        "```",
    ]

    # Árbol indentado
    def render_tree(node: Module, depth: int = 0) -> Iterable[str]:
        prefix = "  " * depth
        connector = "└─ " if depth > 0 else ""
        label = node.name if node.has_explicit_name else f"({node.catalog_number})"
        line = f"{prefix}{connector}{label}  [{node.catalog_number}]"
        # NOTA: MajorFault del L5X es atributo de CONFIGURACIÓN (escalar
        # fallas al controller), no de ESTADO actual del módulo. Por eso
        # NO se muestra como warning aquí — sería engañoso.
        if node.inhibited:
            line += "  ⚠ INHIBITED"
        yield line
        for child in children.get(node.name, []):
            yield from render_tree(child, depth + 1)

    for root in roots:
        parts.extend(render_tree(root))
    parts.append("```")
    parts.append("")

    # Resumen por categoría
    cat_lines = []
    if bridges:
        cat_lines.append(
            f"- **Bridges/scanners:** {len(bridges)} ({_short_catalog_list(bridges)})"
        )
    if io_adapters:
        cat_lines.append(
            f"- **Adapters de I/O:** {len(io_adapters)} ({_short_catalog_list(io_adapters)})"
        )
    if io_modules:
        cat_lines.append(
            f"- **Módulos I/O:** {len(io_modules)} (POINT I/O u otros)"
        )
    if drives:
        cat_lines.append(
            f"- **Drives/servos:** {len(drives)} ({_short_catalog_list(drives)})"
        )
    if cat_lines:
        parts.append("### Resumen por categoría")
        parts.append("")
        parts.extend(cat_lines)

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────
# Sección 3 — Arquitectura lógica
# ─────────────────────────────────────────────────────────────────────────


def _section_arquitectura_logica(p: Project) -> str:
    parts = [
        "## Arquitectura lógica",
        "",
    ]

    # Tasks
    if p.tasks:
        parts.append("### Tasks")
        parts.append("")
        for t in p.tasks:
            extra = []
            if t.type == "PERIODIC" and t.rate:
                extra.append(f"rate={t.rate}ms")
            if t.priority:
                extra.append(f"priority={t.priority}")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            scheduled = ", ".join(t.scheduled_programs) if t.scheduled_programs else "-"
            parts.append(f"- **{t.name}** [{t.type}]{extra_str} → {scheduled}")
        parts.append("")

    # Programs y rutinas
    if p.programs:
        parts.append("### Programs y rutinas")
        parts.append("")
        for prog in p.programs:
            prog_routines = [r for r in p.routines if r.program == prog.name]
            type_counts = Counter(r.type for r in prog_routines)
            tipo_str = ", ".join(f"{n} {t}" for t, n in type_counts.items()) or "sin rutinas"
            main_marker = f" (main: `{prog.main_routine}`)" if prog.main_routine else ""
            parts.append(
                f"- **{prog.name}**: {len(prog_routines)} rutinas — {tipo_str}{main_marker}"
            )
            # Listar nombres de rutinas si son pocos
            if len(prog_routines) <= 10:
                names = [r.name for r in prog_routines]
                parts.append(f"  - {', '.join(f'`{n}`' for n in names)}")
        parts.append("")

    # Tags desagregados por scope (TODO punto 1 — sin cifra bruta engañosa)
    parts.extend(_render_tags_breakdown(p))
    parts.append("")

    # AOIs y UDTs (resumen)
    if p.aois:
        prefixes = _classify_aoi_prefixes(p.aois)
        prefix_str = ", ".join(f"{n} con prefijo `{px}`" for px, n in prefixes.most_common(3) if px)
        sin_prefix = prefixes.get("", 0)
        parts.append(
            f"### AOIs ({len(p.aois)} totales)"
        )
        parts.append("")
        if prefix_str:
            parts.append(f"Distribución por prefijo: {prefix_str}; {sin_prefix} sin prefijo identificable.")
            parts.append("")
        # Listar nombres en líneas (compact)
        aoi_names = sorted(a.name for a in p.aois)
        parts.append("Nombres: " + ", ".join(f"`{n}`" for n in aoi_names))
        parts.append("")

    if p.udts:
        parts.append(f"### UDTs ({len(p.udts)} totales)")
        parts.append("")
        # Mostrar nombre + cantidad de members
        udt_lines = []
        for u in sorted(p.udts, key=lambda x: -len(x.members)):
            udt_lines.append(f"`{u.name}` ({len(u.members)} members)")
        parts.append(", ".join(udt_lines))

    return "\n".join(parts)


def _render_tags_breakdown(p: Project) -> list[str]:
    """Tags desagregados por scope — TODO punto 1 cumplido.

    NO mostrar la cifra bruta total. Mostrar los tres scopes por separado.
    """
    aoi_names = {a.name for a in p.aois}
    program_names = {pr.name for pr in p.programs}

    n_ctrl = sum(1 for t in p.tags if t.scope == "controller")
    n_prog = sum(1 for t in p.tags if t.scope in program_names)
    n_aoi = sum(1 for t in p.tags if t.scope in aoi_names)
    n_otro = len(p.tags) - n_ctrl - n_prog - n_aoi  # debería ser 0; defensa

    lines = [
        "### Tags por alcance",
        "",
        f"- **Controller-scope:** {n_ctrl}",
        f"- **Program-scope:** {n_prog} (distribuidos en {len(program_names)} programas)",
        f"- **AOI-local:** {n_aoi} (distribuidos en {len(aoi_names)} AOIs)",
    ]
    if n_otro > 0:
        lines.append(f"- _Otros (no clasificados):_ {n_otro}")
    return lines


# ─────────────────────────────────────────────────────────────────────────
# Sección 4 — Mapa funcional de ejes
# ─────────────────────────────────────────────────────────────────────────


# Heurísticas de mapeo AOI → descripción funcional.
# Patrones por palabras clave en el nombre del AOI.
_AOI_FUNCTION_HINTS = [
    (re.compile(r"DriveRoll.*withDancer", re.I), "Drive roll con dancer (control de tensión)"),
    (re.compile(r"DriveRoll.*withoutDancer", re.I), "Drive roll sin dancer"),
    (re.compile(r"DriveRoll", re.I), "Drive roll (genérico)"),
    (re.compile(r"Unwinder", re.I), "Debobinador"),
    (re.compile(r"Rewind", re.I), "Bobinador"),
    (re.compile(r"Splic", re.I), "Empalme (splice)"),
    (re.compile(r"Syncro|Synchro", re.I), "Eje sincronizado"),
    (re.compile(r"VirtualAxis", re.I), "Eje virtual / master"),
    (re.compile(r"AxisBlock", re.I), "Eje genérico"),
    (re.compile(r"Cam", re.I), "Cam (perfil de leva)"),
    (re.compile(r"Servo|Drive", re.I), "Servo/drive (manejo o falla)"),
]


def _section_mapa_funcional_ejes(p: Project) -> str:
    # Detectar ejes primitivos (datatype AXIS_*)
    primitive_axes = [
        t for t in p.tags
        if t.scope == "controller" and t.datatype.startswith("AXIS_")
    ]

    # Detectar bloques manager de eje: tags cuyo datatype es un AOI cuyo nombre
    # sugiere control de eje (AxisBlock, VirtualAxisBlock, etc). Son wrappers
    # que envuelven un AXIS_* primitivo + datos + lógica.
    aoi_names_by_axis = {
        a.name for a in p.aois
        if re.search(r"AxisBlock$|^AxisBlock|VirtualAxis", a.name, re.I)
    }
    manager_blocks = [
        t for t in p.tags
        if t.scope == "controller" and t.datatype in aoi_names_by_axis
    ]

    if not primitive_axes and not manager_blocks:
        return ""  # Proyecto sin motion → omitir sección

    # Mapear cada eje primitivo a los AOIs que lo procesan
    axis_to_aois = _map_axes_to_aois(p, [a.name for a in primitive_axes])

    # Cruzar eje↔módulo usando motion_module del L5X (autoritativo) con
    # fallback a matching por nombre exacto para casos legacy
    axis_to_module = _build_axis_to_module(p, primitive_axes)

    parts = [
        "## Mapa funcional de ejes",
        "",
    ]

    if primitive_axes:
        parts.append(
            f"**{len(primitive_axes)} ejes primitivos** (tags `AXIS_*` controller-scoped):"
        )
        parts.append("")
        parts.append("| Eje | Tipo | Hardware | AOI principal | Función inferida |")
        parts.append("|---|---|---|---|---|")

        for ax in primitive_axes:
            ax_type = ax.datatype.replace("AXIS_", "")
            mod = axis_to_module.get(ax.name)
            hw = _format_hardware_cell(mod, ax)

            # Spare: marcar honestamente sin inferir función productiva
            if _looks_like_spare(ax.name):
                parts.append(
                    f"| `{ax.name}` | {ax_type} | {hw} | — | _Spare / no productivo_ |"
                )
                continue

            # AXIS_VIRTUAL: función fija. Aparecen en código como argumento de
            # referencia (master de velocidad), NO como objeto controlado, así
            # que la heurística de invocaciones genera falsos positivos.
            if ax.datatype == "AXIS_VIRTUAL":
                parts.append(
                    f"| `{ax.name}` | {ax_type} | {hw} | — | _Eje virtual / referencia maestra_ |"
                )
                continue

            # AXIS_SERVO_DRIVE / otros físicos: inferir función con orden de
            # prioridad (de más explícito a más inferido):
            #   1. Substring del nombre del eje (info explícita del proyecto)
            #   2. AOIs invocadoras filtradas (no genéricas)
            #   3. AOIs invocadoras (incluyendo genéricas)
            aois = sorted(axis_to_aois.get(ax.name, []))
            filtered_aois = [a for a in aois if not _is_generic_aoi(a)]
            primary_aoi = filtered_aois[0] if filtered_aois else (aois[0] if aois else "—")
            function = (
                _infer_from_tag_name(ax.name)
                or _infer_axis_function(filtered_aois)
                or _infer_axis_function(aois)
                or "—"
            )
            aoi_display = f"`{primary_aoi}`" if primary_aoi != "—" else "—"
            parts.append(
                f"| `{ax.name}` | {ax_type} | {hw} | {aoi_display} | {function} |"
            )

        # Notas explicativas si hay AOIs comunes
        common_aois = _detect_common_aois(axis_to_aois)
        if common_aois:
            parts.append("")
            parts.append(
                f"_Nota: AOIs como {', '.join(f'`{a}`' for a in common_aois)} "
                f"aparecen asociadas a múltiples ejes — son AOIs de servicio "
                f"(manejo de fallas, decoding) y no caracterizan función específica._"
            )

    # Bloques manager: tags que envuelven ejes (AxisBlock, VirtualAxisBlock)
    if manager_blocks:
        n = len(manager_blocks)
        bloques_word = "bloque" if n == 1 else "bloques"
        parts.append("")
        parts.append(
            f"**{n} {bloques_word} de control de eje** (tags con UDT/AOI tipo "
            f"`AxisBlock` o `VirtualAxisBlock` — envuelven un eje primitivo con su lógica):"
        )
        parts.append("")
        for mb in manager_blocks:
            parts.append(f"- `{mb.name}` (tipo `{mb.datatype}`)")
        # Buscar también bloques manager en program-scope (informativo)
        program_blocks = [
            t for t in p.tags
            if t.scope not in ("controller",)
            and t.datatype in aoi_names_by_axis
            and t.scope in {pr.name for pr in p.programs}
        ]
        if program_blocks:
            parts.append("")
            np_ = len(program_blocks)
            bp_word = "bloque manager" if np_ == 1 else "bloques manager"
            parts.append(
                f"_Adicionalmente, {np_} {bp_word} en program-scope:_ "
                + ", ".join(f"`{t.name}`@{t.scope}" for t in program_blocks)
            )

    return "\n".join(parts)


def _map_axes_to_aois(p: Project, axis_names: list[str]) -> dict[str, set[str]]:
    """Para cada eje, qué AOIs son invocados con ese eje (o su tag Data) en argumentos."""
    if not axis_names:
        return {}
    aoi_names = {a.name for a in p.aois}

    call_pattern = re.compile(r"(\w+)\(([^)]*)\)")
    axis_tokens = "|".join(re.escape(a) for a in axis_names)
    axis_in_args = re.compile(rf"\b({axis_tokens})(?:Data)?\b")

    out: dict[str, set[str]] = defaultdict(set)
    for routine in p.routines:
        if routine.program is None or not routine.code:
            continue
        for m in call_pattern.finditer(routine.code):
            called = m.group(1)
            if called not in aoi_names:
                continue
            args = m.group(2)
            for am in axis_in_args.finditer(args):
                out[am.group(1)].add(called)
    return out


def _infer_axis_function(aoi_list: list[str]) -> str:
    """Mapea AOIs a una descripción funcional usando heurísticas de nombre."""
    for aoi in aoi_list:
        for pattern, description in _AOI_FUNCTION_HINTS:
            if pattern.search(aoi):
                return description
    return ""


def _build_axis_to_module(p: Project, axes: list[Tag]) -> dict[str, Module]:
    """Mapea axis tag → Module asociado.

    Estrategia (orden de prioridad):
    1. Usar el campo motion_module del axis tag (autoritativo desde el L5X).
       Formato: "{ModuleName}:{Channel}". Vacío o "<NA>" → no asociado.
    2. Fallback: matching por nombre exacto (proyectos legacy donde axis name
       coincide con module name, ej. CINTA_M2: M1↔M1).
    """
    modules_by_name = {m.name: m for m in p.modules}
    out: dict[str, Module] = {}

    for ax in axes:
        # 1. Vía motion_module del L5X
        mm = (ax.motion_module or "").strip()
        if mm and mm not in ("<NA>",):
            module_name = mm.split(":", 1)[0]
            if module_name in modules_by_name:
                out[ax.name] = modules_by_name[module_name]
                continue
        # 2. Fallback: matching por nombre exacto
        if ax.name in modules_by_name:
            mod = modules_by_name[ax.name]
            if _is_drive(mod.catalog_number):
                out[ax.name] = mod

    return out


def _format_hardware_cell(mod: Module | None, ax: Tag) -> str:
    """Formatea la celda 'Hardware' del Mapa Mental.

    Si hay módulo asociado: muestra catálogo + (canal del motion_module si
    está disponible).
    Si motion_module es '<NA>': "—" (eje no asociado).
    Si no hay módulo: "—".
    """
    if mod is None:
        return "—"
    catalog = f"`{mod.catalog_number}`"
    # Si tenemos canal en motion_module, lo agregamos en compacto
    mm = (ax.motion_module or "").strip()
    if mm and ":" in mm and mm not in ("<NA>",):
        channel = mm.split(":", 1)[1]
        return f"{catalog} ({channel})"
    return catalog


# Diccionario de inferencia funcional desde el NOMBRE del axis tag.
# Información explícita del proyecto (no semántica), aplicada PRIMERO porque
# es más confiable que inferir desde AOIs invocadores.
# Patrones cubren convenciones comunes en español + inglés en proyectos
# Rockwell de manufactura industrial.
#
# IMPORTANTE: usamos (?<![A-Za-z]) y (?![A-Za-z]) en vez de \b porque en
# Python regex \b considera el guión bajo `_` como word-char, lo que rompe
# el matching cuando los nombres usan underscore como separador (caso muy
# común en proyectos reales: S04N77_DEBO_TNT_IZQUIERDO). Con lookahead/
# lookbehind sobre [A-Za-z] consideramos underscores y dígitos como
# separadores válidos.
#
# Orden importa: patrones más específicos antes que genéricos.
_TAG_NAME_HINTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"DANCER", re.I),                                          "Dancer / control de tensión"),
    (re.compile(r"ESTAMP", re.I),                                          "Estampador"),
    (re.compile(r"DEBOB|UNWIND|(?<![A-Za-z])DEBO(?![A-Za-z])|(?<![A-Za-z])DEB(?![A-Za-z])", re.I),
                                                                            "Debobinador"),
    (re.compile(r"REWIND|BOBIN", re.I),                                    "Bobinador"),
    (re.compile(r"(?<![A-Za-z])CORTE(?![A-Za-z])|(?<![A-Za-z])CUT(?![A-Za-z])", re.I),
                                                                            "Corte"),
    (re.compile(r"SPLIC|EMPALME", re.I),                                   "Splice / empalme"),
    (re.compile(r"(?<![A-Za-z])TAMBOR|(?<![A-Za-z])DRUM(?![A-Za-z])|TRANSF", re.I),
                                                                            "Tambor / transferencia"),
    (re.compile(r"BARRER", re.I),                                          "Barreras"),
    # Rodillos: diferenciar por subtipo (los específicos ANTES del genérico)
    (re.compile(r"ROD\w*ARRASTRE|ARRASTRE|TRACC|TIRO", re.I),              "Rodillo de arrastre"),
    (re.compile(r"ROD\w*BAND|BAND_ALIM|ALIMENT", re.I),                    "Rodillo de banda alimentadora"),
    (re.compile(r"(?<![A-Za-z])RODILLO(?![A-Za-z])|(?<![A-Za-z])ROLL(?![A-Za-z])|(?<![A-Za-z])ROD(?![A-Za-z])", re.I),
                                                                            "Rodillo (genérico)"),
]


def _infer_from_tag_name(tag_name: str) -> str:
    """Infiere función del eje a partir de su nombre.

    Aprovecha la convención de naming descriptivo común en proyectos reales
    (ej. 'S04N86_DANCER_DEBO_TNT' → 'Dancer / control de tensión').
    Retorna "" si ningún patrón matchea.
    """
    for pattern, description in _TAG_NAME_HINTS:
        if pattern.search(tag_name):
            return description
    return ""


def _is_generic_aoi(aoi_name: str) -> bool:
    """AOIs que aparecen para todos los ejes (servicios comunes)."""
    nl = aoi_name.lower()
    return (
        "fault" in nl
        or "decoding" in nl
        or "rackaxis" in nl
        or "racksercos" in nl
        or "sercosfault" in nl
        or "enable_drive" in nl
        or "motionaxiserror" in nl
    )


def _looks_like_spare(axis_name: str) -> bool:
    """Detecta convenciones de naming para ejes de respaldo / sin uso productivo."""
    nl = axis_name.lower()
    return (
        "spare" in nl
        or "_unused" in nl
        or "_reserved" in nl
        or nl.startswith("ax_spare")
    )


def _detect_common_aois(axis_to_aois: dict[str, set[str]]) -> list[str]:
    """AOIs que aparecen en al menos la mitad de los ejes (servicios)."""
    counts: Counter[str] = Counter()
    for aois in axis_to_aois.values():
        counts.update(aois)
    threshold = max(2, len(axis_to_aois) // 2)
    return sorted(a for a, c in counts.items() if c >= threshold and _is_generic_aoi(a))


# ─────────────────────────────────────────────────────────────────────────
# Sección 5 — Patrones de código
# ─────────────────────────────────────────────────────────────────────────


def _section_patrones_codigo(p: Project) -> str:
    parts = [
        "## Patrones de código",
        "",
    ]

    # Distribución de tipos de rutinas
    type_counts: Counter[str] = Counter()
    for r in p.routines:
        type_counts[r.type] += 1
    for a in p.aois:
        for r in a.routines.values():
            type_counts[r.type] += 1
    if type_counts:
        rows = [f"{n} {t}" for t, n in type_counts.most_common()]
        parts.append(f"- **Lenguajes de rutinas:** {', '.join(rows)}")

    # Convención de nombres de tags estructurados por entidad (M1Data, M2Data, ...)
    data_tags = [
        t.name
        for t in p.tags
        if t.scope == "controller" and re.match(r"^[A-Z][\w]*Data$", t.name)
    ]
    if data_tags:
        # Distinguir cuáles corresponden a ejes. Dos vías:
        # 1. Cruce directo con axis_names (caso CINTA_M2: M1Data ↔ M1)
        # 2. Cruce con prefijos de motion_module (caso AQL_M2: M3Data ↔ M3_504U1
        #    donde el eje real se llama S04N73_ROD_ARRASTRE_TNT pero su drive
        #    tiene prefijo M3 — es la convención de aliasing del proyecto)
        axis_names = {
            t.name for t in p.tags
            if t.scope == "controller" and t.datatype.startswith("AXIS_")
        }
        # Prefijos de módulo extraídos de motion_module (ej. "M3" de "M3_504U1:Ch93")
        module_prefixes = set()
        for t in p.tags:
            if t.scope == "controller" and t.datatype.startswith("AXIS_"):
                mm = (t.motion_module or "").strip()
                if mm and mm not in ("<NA>",):
                    module_name = mm.split(":", 1)[0]
                    # Si el módulo es "M3_504U1", extraer prefijo "M3"; si es
                    # "M3" ya completo, también queda "M3"
                    pmatch = re.match(r"^([A-Za-z]+\d+)(_|$)", module_name)
                    if pmatch:
                        module_prefixes.add(pmatch.group(1))

        def _matches_axis(name: str) -> bool:
            stem = name.removesuffix("Data").rstrip("_")  # M16_Data → M16
            if stem in axis_names or stem + "1" in axis_names:
                return True
            if stem in module_prefixes:
                return True
            return False

        per_axis = sorted(n for n in data_tags if _matches_axis(n))
        otros = sorted(set(data_tags) - set(per_axis))

        if per_axis:
            ejemplo_ejes = ", ".join(f"`{n}`" for n in per_axis)
            ejes_str = f"{len(per_axis)} corresponden a ejes ({ejemplo_ejes})"
        else:
            ejes_str = ""
        if otros:
            ejemplo_otros = ", ".join(f"`{n}`" for n in otros)
            otros_str = f"{len(otros)} a estructuras auxiliares ({ejemplo_otros})"
        else:
            otros_str = ""
        partes_desc = [s for s in [ejes_str, otros_str] if s]
        desc = "; ".join(partes_desc) if partes_desc else "varias entidades"
        parts.append(
            f"- **Encapsulación por entidad detectada:** {len(data_tags)} tags "
            f"controller-scope con sufijo `Data` — {desc}. Sugiere convención "
            f"de UDT estructurado por entidad."
        )

    # Prefijos de AOIs
    prefixes = _classify_aoi_prefixes(p.aois)
    if prefixes:
        most = prefixes.most_common(3)
        rows = [f"`{px or '(sin prefijo)'}`={n}" for px, n in most]
        parts.append(f"- **Convención de AOIs:** {', '.join(rows)}")

    # AOI duplicate detection (resumen del que ya hizo loader)
    dup_obs = [
        o for o in p.observations if o.category == "aoi_naming_collision"
    ]
    if dup_obs:
        parts.append(
            f"- **AOIs con nombres potencialmente duplicados:** "
            f"{len(dup_obs)} pares — ver sección Issues."
        )

    if len(parts) == 2:
        # Solo el header
        return ""
    return "\n".join(parts)


def _classify_aoi_prefixes(aois: list[AOIDetail]) -> Counter:
    """Cuenta AOIs por prefijo (token antes del primer '_')."""
    c: Counter[str] = Counter()
    for a in aois:
        if "_" in a.name:
            prefix = a.name.split("_", 1)[0]
            c[prefix] += 1
        else:
            c[""] += 1
    return c


# ─────────────────────────────────────────────────────────────────────────
# Sección 6 — Issues / observaciones (agrupadas, no raw — TODO punto 2)
# ─────────────────────────────────────────────────────────────────────────


def _section_issues(p: Project) -> str:
    if not p.observations:
        return "## Issues / observaciones\n\n_Ninguna inconsistencia detectada durante el parseo._"

    # Agrupar por (severity, category)
    grouped: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for o in p.observations:
        grouped[(o.severity, o.category)].append(o)

    parts = ["## Issues / observaciones", ""]
    parts.append(f"{len(p.observations)} observaciones detectadas durante el parseo, agrupadas:")
    parts.append("")

    # Ordenar: warnings primero
    severity_order = {"warning": 0, "info": 1}
    keys = sorted(
        grouped.keys(),
        key=lambda k: (severity_order.get(k[0], 99), k[1]),
    )

    for severity, category in keys:
        obs_list = grouped[(severity, category)]
        n = len(obs_list)
        # Tomar 1 ejemplo representativo
        sample = obs_list[0]
        parts.append(
            f"- **[{severity.upper()}] `{category}`:** {n} ocurrencia(s)."
        )
        # Ejemplo (acortado)
        msg = sample.message
        if len(msg) > 140:
            msg = msg[:140] + "…"
        parts.append(f"  - _Ejemplo:_ {msg}")
        # Si hay múltiples y todas las refs son distintas, listar las refs
        if n > 1 and n <= 4:
            all_refs = [r for o in obs_list for r in o.references]
            if all_refs:
                parts.append(f"  - Referencias: {', '.join(f'`{r}`' for r in all_refs)}")

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────
# Helpers de clasificación de módulos
# ─────────────────────────────────────────────────────────────────────────

# Catálogos drives (Kinetix series)
_DRIVE_PREFIXES = ("2094-", "2198-", "2097-", "2090-")
# Bridges/scanners de bus
_BRIDGE_PREFIXES = (
    "1768-ENBT", "1768-EWEB", "1768-M04SE", "1768-CNB",
    "1756-ENBT", "1756-EN2T", "1756-EN3T", "1756-EN2TR", "1756-CNB",
    "1769-L", "1768-L", "1756-L",
)
# I/O adapters
_ADAPTER_PREFIXES = ("1734-AENT", "1738-AENT", "1794-AENT", "1769-AENTR")
# I/O modules (POINT I/O y similares)
_IO_MODULE_PREFIXES = ("1734-", "1738-", "1794-", "1756-I", "1756-O", "1769-I", "1769-O")


def _is_drive(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _DRIVE_PREFIXES)


def _is_bridge(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _BRIDGE_PREFIXES)


def _is_io_adapter(catalog: str) -> bool:
    return any(catalog.startswith(p) for p in _ADAPTER_PREFIXES)


def _is_io_module(catalog: str) -> bool:
    # Es módulo I/O si el prefijo coincide y NO es adapter
    if _is_io_adapter(catalog):
        return False
    return any(catalog.startswith(p) for p in _IO_MODULE_PREFIXES)


def _short_catalog_list(modules: list[Module]) -> str:
    """Resumen compacto de catálogos ('2× 2094-BM01, 1× 2094-BC02-M02')."""
    c: Counter[str] = Counter(m.catalog_number for m in modules)
    return ", ".join(f"{n}× `{cat}`" for cat, n in c.most_common())
