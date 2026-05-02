"""
loader.py — Carga un archivo .L5X y construye el modelo canónico.

Punto de entrada único: load_project(filepath) → Project

Estrategia:
- Validación rápida (file exists, raíz XML correcta)
- Parser basado en `xml.etree.ElementTree` (stdlib) — la validación práctica
  durante la construcción de v0.1 mostró que cubre el 100% de las necesidades
  (ver DT-010 en la bitácora de decisiones técnicas)
- Persistencia a SQLite (schema completo desde v0.1, incluye `xref` vacía)
- Captura de inconsistencias durante el parseo en project.observations

Decisiones técnicas relevantes:
- DT-002 + DT-010: parsing con `xml.etree` puro; la librería `l5x` se evaluó
  pero no aporta valor en v0.1 y se removió como dependencia
- DT-008: stack mínimo, solo stdlib (sqlite3, xml.etree, dataclasses)
- DT-009: NO hay tracer.py ni tokenizer/ — la tabla `xref` se crea vacía
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from typing import Optional

from .model import (
    AOIDetail,
    Identity,
    L5XParseError,
    Member,
    Module,
    Observation,
    Parameter,
    Program,
    Project,
    Routine,
    Tag,
    Task,
    UDTDetail,
    UnsupportedFormatError,
    init_db,
)


# ─────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────


def load_project(filepath: str, db_path: Optional[str] = None) -> Project:
    """Carga un archivo .L5X y construye el modelo canónico del proyecto.

    Args:
        filepath: ruta al archivo .L5X
        db_path: ruta donde persistir la base SQLite. Si es None, se crea en
                 un archivo temporal.

    Returns:
        Project con todo el modelo cargado (identity, modules, programs,
        routines, aois, udts, tags, tasks, observations).

    Raises:
        FileNotFoundError: si filepath no existe
        UnsupportedFormatError: si no es un L5X válido (ACD binario, XML
                                con raíz distinta, etc.)
        L5XParseError: si el L5X parece válido pero el parseo falla por
                       alguna razón estructural; lleva .schema_version,
                       .controller_type y .reason
    """
    # 1. Validación temprana
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"L5X file not found: {filepath}")

    _validate_is_l5x(filepath)

    # 2. Parse XML directo (necesitamos acceso completo al árbol)
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        raise UnsupportedFormatError(
            f"File is not valid XML: {e}. If this is a Studio 5000 .ACD file, "
            f"please export it to .L5X first."
        )

    # 3. Validar raíz RSLogix5000Content
    if root.tag != "RSLogix5000Content":
        raise UnsupportedFormatError(
            f"XML root is <{root.tag}>, expected <RSLogix5000Content>. "
            f"This does not appear to be a Studio 5000 / RSLogix 5000 export."
        )

    # 4. Localizar Controller
    controller = root.find("Controller")
    if controller is None:
        raise L5XParseError(
            reason="No <Controller> element found under <RSLogix5000Content>",
            schema_version=root.attrib.get("SchemaRevision"),
            controller_type=None,
        )

    # 5. Construir Identity (lo primero — útil para errores con contexto)
    identity = _parse_identity(root, controller)

    # 6. Inicializar SQLite
    if db_path is None:
        fd, db_path = tempfile.mkstemp(suffix=".sqlite", prefix="rwc_")
        os.close(fd)
    conn = init_db(db_path)

    # 7. Construir el Project iterativamente, capturando observaciones
    observations: list[Observation] = []

    modules = _parse_modules(controller, observations)
    udts = _parse_udts(controller, observations)
    aois = _parse_aois(controller, observations)
    tags = _parse_tags(controller, observations)
    tasks = _parse_tasks(controller, observations)
    programs, program_routines, program_tags = _parse_programs(
        controller, observations
    )

    # Tags de programas se agregan al pool global de tags
    tags.extend(program_tags)
    # Tags locales de AOIs también
    for a in aois:
        tags.extend(a.local_tags)

    # 8. Detección de inconsistencias estructurales adicionales
    _detect_structural_issues(
        modules=modules,
        aois=aois,
        udts=udts,
        tags=tags,
        program_routines=program_routines,
        observations=observations,
    )

    # 9. Persistir en SQLite
    project = Project(
        identity=identity,
        modules=modules,
        tasks=tasks,
        programs=programs,
        routines=program_routines,
        aois=aois,
        udts=udts,
        tags=tags,
        observations=observations,
        source_path=os.path.abspath(filepath),
        db_path=db_path,
    )
    _persist(conn, project)
    conn.close()

    return project


# ─────────────────────────────────────────────────────────────────────────
# Validación de formato
# ─────────────────────────────────────────────────────────────────────────


def _validate_is_l5x(filepath: str) -> None:
    """Verifica magic bytes / inicio de archivo. ACD empieza distinto."""
    with open(filepath, "rb") as f:
        head = f.read(64)

    # ACD files binarios típicamente empiezan con secuencias no-XML.
    # L5X siempre empieza con declaración XML (con o sin BOM)
    head_stripped = head.lstrip(b"\xef\xbb\xbf").lstrip()
    if not head_stripped.startswith(b"<?xml"):
        raise UnsupportedFormatError(
            f"File does not start with XML declaration. "
            f"If this is a Studio 5000 .ACD (binary) file, please export it "
            f"to .L5X format first using: File → Save As → L5X."
        )


# ─────────────────────────────────────────────────────────────────────────
# Parseo de cada sección
# ─────────────────────────────────────────────────────────────────────────


def _parse_identity(root: ET.Element, controller: ET.Element) -> Identity:
    """Extrae los headers de identidad del proyecto."""
    return Identity(
        target_name=controller.attrib.get("Name", ""),
        processor_type=controller.attrib.get("ProcessorType", ""),
        software_revision=root.attrib.get("SoftwareRevision", ""),
        schema_revision=root.attrib.get("SchemaRevision", ""),
        major_rev=controller.attrib.get("MajorRev", ""),
        minor_rev=controller.attrib.get("MinorRev", ""),
        project_creation_date=controller.attrib.get("ProjectCreationDate", ""),
        last_modified_date=controller.attrib.get("LastModifiedDate", ""),
        owner=root.attrib.get("Owner", ""),
        export_date=root.attrib.get("ExportDate", ""),
    )


def _parse_modules(
    controller: ET.Element, observations: list[Observation]
) -> list[Module]:
    """Parsea Modules — incluye lógica para módulos sin Name (POINT I/O).

    Para módulos sin atributo Name se sintetiza un identificador estable.
    Cuando hay múltiples módulos del mismo catálogo bajo el mismo parent y
    puerto (caso típico: varios 1734-IB8/C en un mismo NODE), se desambigua
    con sufijo `#N` basado en el orden de aparición en el L5X.
    """
    out: list[Module] = []
    mods_elem = controller.find("Modules")
    if mods_elem is None:
        return out

    # Pass 1: recolectar candidatos y bases sintéticas para detectar colisiones
    candidates: list[tuple[ET.Element, str, bool]] = []  # (elem, base_name, has_explicit)
    synth_base_counts: dict[str, int] = {}
    for m in mods_elem:
        explicit = m.attrib.get("Name", "")
        if explicit:
            candidates.append((m, explicit, True))
        else:
            parent = m.attrib.get("ParentModule", "?")
            port = m.attrib.get("ParentModPortId", "?")
            catalog = m.attrib.get("CatalogNumber", "?")
            base = f"{parent}:port{port}({catalog})"
            candidates.append((m, base, False))
            synth_base_counts[base] = synth_base_counts.get(base, 0) + 1

    # Pass 2: asignar nombres finales (con sufijo #N solo donde hay colisión)
    synth_idx_seen: dict[str, int] = {}
    for m, base, has_explicit in candidates:
        if has_explicit:
            final_name = base
        else:
            if synth_base_counts[base] > 1:
                idx = synth_idx_seen.get(base, 0) + 1
                synth_idx_seen[base] = idx
                final_name = f"{base}#{idx}"
            else:
                final_name = base
            catalog = m.attrib.get("CatalogNumber", "?")
            parent = m.attrib.get("ParentModule", "?")
            observations.append(
                Observation(
                    severity="info",
                    category="module_without_name",
                    message=(
                        f"Módulo {catalog} bajo {parent} no tiene atributo "
                        f"Name. Se le asigna identificador sintético "
                        f"'{final_name}'. Esto es normal para POINT I/O y similares."
                    ),
                    references=[final_name],
                )
            )

        out.append(
            Module(
                name=final_name,
                catalog_number=m.attrib.get("CatalogNumber", ""),
                vendor=m.attrib.get("Vendor", ""),
                parent_module=m.attrib.get("ParentModule", ""),
                parent_port_id=m.attrib.get("ParentModPortId", ""),
                inhibited=m.attrib.get("Inhibited", "false").lower() == "true",
                major_fault=m.attrib.get("MajorFault", "false").lower() == "true",
                has_explicit_name=has_explicit,
            )
        )
    return out


def _parse_udts(
    controller: ET.Element, observations: list[Observation]
) -> list[UDTDetail]:
    """Parsea DataTypes — solo los UDTs definidos por el usuario."""
    out: list[UDTDetail] = []
    dts = controller.find("DataTypes")
    if dts is None:
        return out

    for dt in dts:
        if dt.tag != "DataType":
            continue

        members: list[Member] = []
        members_elem = dt.find("Members")
        if members_elem is not None:
            for m in members_elem:
                if m.tag != "Member":
                    continue
                desc = _get_description(m)
                members.append(
                    Member(
                        name=m.attrib.get("Name", ""),
                        datatype=m.attrib.get("DataType", ""),
                        dimension=m.attrib.get("Dimension", "0"),
                        hidden=m.attrib.get("Hidden", "false").lower() == "true",
                        description=desc,
                    )
                )

        out.append(
            UDTDetail(
                name=dt.attrib.get("Name", ""),
                family=dt.attrib.get("Family", ""),
                description=_get_description(dt),
                members=members,
            )
        )
    return out


def _parse_aois(
    controller: ET.Element, observations: list[Observation]
) -> list[AOIDetail]:
    """Parsea AddOnInstructionDefinitions — params, local tags, routines."""
    out: list[AOIDetail] = []
    seen_names: set[str] = set()

    aois_elem = controller.find("AddOnInstructionDefinitions")
    if aois_elem is None:
        return out

    for a in aois_elem:
        if a.tag != "AddOnInstructionDefinition":
            continue

        name = a.attrib.get("Name", "")
        if name in seen_names:
            observations.append(
                Observation(
                    severity="warning",
                    category="duplicated_aoi",
                    message=f"AOI '{name}' aparece más de una vez en el L5X.",
                    references=[name],
                )
            )
        seen_names.add(name)

        # Parámetros
        params: list[Parameter] = []
        params_elem = a.find("Parameters")
        if params_elem is not None:
            for p in params_elem:
                if p.tag != "Parameter":
                    continue
                params.append(
                    Parameter(
                        name=p.attrib.get("Name", ""),
                        usage=p.attrib.get("Usage", ""),
                        datatype=p.attrib.get("DataType", ""),
                        dimension=p.attrib.get("Dimension", "0"),
                        required=p.attrib.get("Required", "false").lower() == "true",
                        visible=p.attrib.get("Visible", "true").lower() == "true",
                        default=p.attrib.get("Default", ""),
                        description=_get_description(p),
                    )
                )

        # Local tags
        local_tags: list[Tag] = []
        ltags_elem = a.find("LocalTags")
        if ltags_elem is not None:
            for t in ltags_elem:
                if t.tag != "LocalTag":
                    continue
                local_tags.append(
                    Tag(
                        name=t.attrib.get("Name", ""),
                        scope=name,  # scope = nombre del AOI
                        datatype=t.attrib.get("DataType", ""),
                        dimension=t.attrib.get("Dimensions", ""),
                        description=_get_description(t),
                        constant=False,
                        external_access="",
                    )
                )

        # Routines internas del AOI
        routines: dict[str, Routine] = {}
        routines_elem = a.find("Routines")
        if routines_elem is not None:
            for r in routines_elem:
                if r.tag != "Routine":
                    continue
                rname = r.attrib.get("Name", "")
                routines[rname] = Routine(
                    name=rname,
                    program=None,  # AOI, no programa
                    type=r.attrib.get("Type", ""),
                    code=_extract_routine_code(r),
                    description=_get_description(r),
                )

        out.append(
            AOIDetail(
                name=name,
                revision=a.attrib.get("Revision", ""),
                description=_get_description(a),
                parameters=params,
                local_tags=local_tags,
                routines=routines,
            )
        )
    return out


def _parse_tags(
    controller: ET.Element, observations: list[Observation]
) -> list[Tag]:
    """Parsea controller-scoped Tags."""
    out: list[Tag] = []
    tags_elem = controller.find("Tags")
    if tags_elem is None:
        return out

    for t in tags_elem:
        if t.tag != "Tag":
            continue
        out.append(
            Tag(
                name=t.attrib.get("Name", ""),
                scope="controller",
                datatype=t.attrib.get("DataType", ""),
                dimension=t.attrib.get("Dimensions", ""),
                description=_get_description(t),
                constant=t.attrib.get("Constant", "false").lower() == "true",
                external_access=t.attrib.get("ExternalAccess", ""),
                motion_module=_extract_motion_module(t),
            )
        )
    return out


def _extract_motion_module(tag_elem: ET.Element) -> str:
    """Extrae el atributo MotionModule de un axis tag.

    Formato: <Data Format="Axis"><AxisParameters MotionModule="M9_507U1:Ch20"/>

    Retorna:
        - "" si no es un axis tag o no tiene la metadata
        - "<NA>" si el L5X marca el eje explícitamente como no asociado
        - "{ModuleName}:{Channel}" si está asociado a hardware
    """
    if not tag_elem.attrib.get("DataType", "").startswith("AXIS_"):
        return ""
    data = tag_elem.find("Data")
    if data is None or data.attrib.get("Format") != "Axis":
        return ""
    ap = data.find("AxisParameters")
    if ap is None:
        return ""
    return ap.attrib.get("MotionModule", "")


def _parse_tasks(
    controller: ET.Element, observations: list[Observation]
) -> list[Task]:
    """Parsea Tasks y los programas asociados a cada uno."""
    out: list[Task] = []
    tasks_elem = controller.find("Tasks")
    if tasks_elem is None:
        return out

    for t in tasks_elem:
        if t.tag != "Task":
            continue
        scheduled = []
        sp = t.find("ScheduledPrograms")
        if sp is not None:
            for prog in sp:
                if prog.tag == "ScheduledProgram":
                    scheduled.append(prog.attrib.get("Name", ""))

        try:
            priority = int(t.attrib.get("Priority", "10"))
        except ValueError:
            priority = 10
        try:
            rate = float(t.attrib.get("Rate", "0"))
        except ValueError:
            rate = 0.0
        try:
            watchdog = float(t.attrib.get("Watchdog", "0"))
        except ValueError:
            watchdog = 0.0

        out.append(
            Task(
                name=t.attrib.get("Name", ""),
                type=t.attrib.get("Type", ""),
                priority=priority,
                rate=rate,
                watchdog=watchdog,
                scheduled_programs=scheduled,
            )
        )
    return out


def _parse_programs(
    controller: ET.Element, observations: list[Observation]
) -> tuple[list[Program], list[Routine], list[Tag]]:
    """Parsea Programs, sus Routines, y los program-scoped Tags.

    Retorna (programs, all_routines, all_program_tags).
    """
    progs: list[Program] = []
    all_routines: list[Routine] = []
    all_program_tags: list[Tag] = []

    progs_elem = controller.find("Programs")
    if progs_elem is None:
        return progs, all_routines, all_program_tags

    for p in progs_elem:
        if p.tag != "Program":
            continue

        pname = p.attrib.get("Name", "")
        progs.append(
            Program(
                name=pname,
                main_routine=p.attrib.get("MainRoutineName", ""),
                fault_routine=p.attrib.get("FaultRoutineName", ""),
                test_edits=p.attrib.get("TestEdits", "false").lower() == "true",
                disabled=p.attrib.get("Disabled", "false").lower() == "true",
            )
        )

        # Routines del programa
        routines_elem = p.find("Routines")
        if routines_elem is not None:
            for r in routines_elem:
                if r.tag != "Routine":
                    continue
                code = _extract_routine_code(r)
                if not code.strip():
                    observations.append(
                        Observation(
                            severity="info",
                            category="empty_routine",
                            message=(
                                f"Rutina '{r.attrib.get('Name', '?')}' del "
                                f"programa '{pname}' está vacía o no tiene "
                                f"código extraíble."
                            ),
                            references=[
                                f"{pname}/{r.attrib.get('Name', '?')}"
                            ],
                        )
                    )
                all_routines.append(
                    Routine(
                        name=r.attrib.get("Name", ""),
                        program=pname,
                        type=r.attrib.get("Type", ""),
                        code=code,
                        description=_get_description(r),
                    )
                )

        # Program-scoped tags
        tags_elem = p.find("Tags")
        if tags_elem is not None:
            for t in tags_elem:
                if t.tag != "Tag":
                    continue
                all_program_tags.append(
                    Tag(
                        name=t.attrib.get("Name", ""),
                        scope=pname,
                        datatype=t.attrib.get("DataType", ""),
                        dimension=t.attrib.get("Dimensions", ""),
                        description=_get_description(t),
                        constant=t.attrib.get("Constant", "false").lower() == "true",
                        external_access=t.attrib.get("ExternalAccess", ""),
                    )
                )

    return progs, all_routines, all_program_tags


# ─────────────────────────────────────────────────────────────────────────
# Helpers de extracción
# ─────────────────────────────────────────────────────────────────────────


def _get_description(elem: ET.Element) -> str:
    """Extrae el texto del sub-elemento <Description> si existe."""
    desc = elem.find("Description")
    if desc is None:
        return ""
    # Description puede contener CDATA con texto, o sub-elementos tipo
    # <localizable>, etc. Tomamos el texto plano agregado.
    return "".join(desc.itertext()).strip()


def _extract_routine_code(routine: ET.Element) -> str:
    """Extrae el código de una rutina como string legible.

    Soporta:
    - RLL: lista de <Rung Number="N"><Text>...</Text></Rung>
    - ST:  <STContent><Line Number="N"><![CDATA[...]]></Line>...</STContent>
    - FBD: <FBDContent>... — para v0.1, retornamos el XML serializado
    - SFC: <SFCContent>... — idem

    Para RLL y ST devolvemos el código en forma reconstruida y legible. Para
    FBD/SFC dejamos un placeholder con el XML porque su representación legible
    requiere un renderer dedicado (futuro).
    """
    rtype = routine.attrib.get("Type", "")

    if rtype == "RLL":
        rll = routine.find("RLLContent")
        if rll is None:
            return ""
        rungs = []
        for rung in rll.findall("Rung"):
            num = rung.attrib.get("Number", "?")
            text_elem = rung.find("Text")
            text = "".join(text_elem.itertext()).strip() if text_elem is not None else ""
            comment_elem = rung.find("Comment")
            comment = "".join(comment_elem.itertext()).strip() if comment_elem is not None else ""
            if comment:
                rungs.append(f"// Rung {num}: {comment}\n{text}")
            else:
                rungs.append(f"// Rung {num}\n{text}")
        return "\n\n".join(rungs)

    if rtype == "ST":
        st = routine.find("STContent")
        if st is None:
            return ""
        lines = []
        for line in st.findall("Line"):
            num = line.attrib.get("Number", "?")
            text = "".join(line.itertext())
            lines.append(f"{num}: {text}")
        return "\n".join(lines)

    if rtype in ("FBD", "SFC"):
        # Devolvemos el XML como string para que search() funcione, aunque
        # no es una representación humana. Un renderer FBD/SFC es trabajo futuro.
        content = routine.find(f"{rtype}Content")
        if content is None:
            return ""
        return ET.tostring(content, encoding="unicode")

    # Tipo desconocido: devolver lo que se pueda
    return ET.tostring(routine, encoding="unicode")


# ─────────────────────────────────────────────────────────────────────────
# Detección de inconsistencias
# ─────────────────────────────────────────────────────────────────────────


def _detect_structural_issues(
    modules: list[Module],
    aois: list[AOIDetail],
    udts: list[UDTDetail],
    tags: list[Tag],
    program_routines: list[Routine],
    observations: list[Observation],
) -> None:
    """Detecciones livianas que no requieren trace causal (eso es v0.2).

    Categorías cubiertas en v0.1:
    - duplicated_aoi (ya cubierto en _parse_aois)
    - empty_routine (ya cubierto en _parse_programs)
    - module_without_name (ya cubierto en _parse_modules)
    - aoi_naming_collision: dos AOIs cuyos nombres difieren solo en prefijo
      (ej. 'Unwinder' vs 'AHT_Unwinder' — caso real reportado)
    """
    # Detectar AOIs cuyos nombres están "casi duplicados" por prefijo
    aoi_names = [a.name for a in aois]
    base_names = {}
    for n in aoi_names:
        # Quitar prefijos comunes tipo "AHT_", "Std_", etc.
        for prefix in ("AHT_", "Std_", "Custom_", "Lib_"):
            if n.startswith(prefix):
                base = n[len(prefix):]
                base_names.setdefault(base, []).append(n)
                break

    for base, variants in base_names.items():
        # Si la versión sin prefijo TAMBIÉN existe como AOI
        if base in aoi_names:
            all_variants = variants + [base]
            observations.append(
                Observation(
                    severity="warning",
                    category="aoi_naming_collision",
                    message=(
                        f"AOIs con nombres potencialmente duplicados (base "
                        f"'{base}'): {all_variants}. Conviene revisar si son "
                        f"versiones distintas de la misma instrucción y cuál "
                        f"está en uso."
                    ),
                    references=all_variants,
                )
            )


# ─────────────────────────────────────────────────────────────────────────
# Persistencia SQLite
# ─────────────────────────────────────────────────────────────────────────


def _persist(conn: sqlite3.Connection, p: Project) -> None:
    """Persiste el Project completo en la base SQLite ya inicializada."""
    cur = conn.cursor()

    # Identity
    cur.execute(
        """INSERT INTO identity VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            p.identity.target_name,
            p.identity.processor_type,
            p.identity.software_revision,
            p.identity.schema_revision,
            p.identity.major_rev,
            p.identity.minor_rev,
            p.identity.project_creation_date,
            p.identity.last_modified_date,
            p.identity.owner,
            p.identity.export_date,
        ),
    )

    # Modules
    cur.executemany(
        """INSERT INTO modules VALUES (?,?,?,?,?,?,?,?)""",
        [
            (
                m.name,
                m.catalog_number,
                m.vendor,
                m.parent_module,
                m.parent_port_id,
                int(m.inhibited),
                int(m.major_fault),
                int(m.has_explicit_name),
            )
            for m in p.modules
        ],
    )

    # Tasks + task_programs
    cur.executemany(
        """INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?)""",
        [(t.name, t.type, t.priority, t.rate, t.watchdog) for t in p.tasks],
    )
    for t in p.tasks:
        for pname in t.scheduled_programs:
            cur.execute(
                """INSERT OR IGNORE INTO task_programs VALUES (?,?)""",
                (t.name, pname),
            )

    # Programs
    cur.executemany(
        """INSERT OR REPLACE INTO programs VALUES (?,?,?,?,?)""",
        [
            (
                pr.name,
                pr.main_routine,
                pr.fault_routine,
                int(pr.test_edits),
                int(pr.disabled),
            )
            for pr in p.programs
        ],
    )

    # Routines (de programas)
    cur.executemany(
        """INSERT OR REPLACE INTO routines VALUES (?,?,?,?,?)""",
        [
            (r.program, r.name, r.type, r.code, r.description)
            for r in p.routines
            if r.program is not None
        ],
    )

    # AOIs
    cur.executemany(
        """INSERT OR REPLACE INTO aois VALUES (?,?,?)""",
        [(a.name, a.revision, a.description) for a in p.aois],
    )
    for a in p.aois:
        cur.executemany(
            """INSERT OR REPLACE INTO aoi_parameters VALUES (?,?,?,?,?,?,?,?,?)""",
            [
                (
                    a.name,
                    pp.name,
                    pp.usage,
                    pp.datatype,
                    pp.dimension,
                    int(pp.required),
                    int(pp.visible),
                    pp.default,
                    pp.description,
                )
                for pp in a.parameters
            ],
        )
        cur.executemany(
            """INSERT OR REPLACE INTO aoi_routines VALUES (?,?,?,?,?)""",
            [
                (a.name, rname, r.type, r.code, r.description)
                for rname, r in a.routines.items()
            ],
        )

    # UDTs
    cur.executemany(
        """INSERT OR REPLACE INTO udts VALUES (?,?,?)""",
        [(u.name, u.family, u.description) for u in p.udts],
    )
    for u in p.udts:
        cur.executemany(
            """INSERT OR REPLACE INTO udt_members VALUES (?,?,?,?,?,?)""",
            [
                (u.name, m.name, m.datatype, m.dimension, int(m.hidden), m.description)
                for m in u.members
            ],
        )

    # Tags (todos los scopes)
    cur.executemany(
        """INSERT OR REPLACE INTO tags VALUES (?,?,?,?,?,?,?,?)""",
        [
            (
                t.name,
                t.scope,
                t.datatype,
                t.dimension,
                t.description,
                int(t.constant),
                t.external_access,
                t.motion_module,
            )
            for t in p.tags
        ],
    )

    # Observations
    import json
    cur.executemany(
        """INSERT INTO observations(severity, category, message, references_) VALUES (?,?,?,?)""",
        [
            (o.severity, o.category, o.message, json.dumps(o.references))
            for o in p.observations
        ],
    )

    # NOTA: tabla `xref` queda VACÍA en v0.1 (DT-009).

    conn.commit()
