"""
model.py — Modelo canónico de un proyecto Rockwell parseado.

Provee:
- Dataclasses para todos los shapes documentados en el SKILL.md
- Schema SQLite para persistencia (tabla `xref` se crea VACÍA en v0.1, será
  poblada por tracer.py en v0.2 — DT-009)
- Clase Project con queries básicas (get_routine, get_aoi, get_udt, search)
- Errores tipados (FileNotFoundError reutilizado de stdlib, L5XParseError,
  UnsupportedFormatError)

Las queries de Project en v0.1 son implementaciones simples que recorren las
listas en memoria. Optimizaciones (índices, FTS) se diferieren a navigator.py.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────
# Errores tipados (contrato documentado en el SKILL.md)
# ─────────────────────────────────────────────────────────────────────────

class L5XParseError(Exception):
    """Error durante el parseo del L5X.

    Atributos:
        schema_version: SchemaRevision del archivo (ej. '1.0'), o None si no se pudo leer
        controller_type: ProcessorType del controller (ej. '1768-L43'), o None
        reason: descripción técnica del fallo
    """

    def __init__(
        self,
        reason: str,
        schema_version: Optional[str] = None,
        controller_type: Optional[str] = None,
    ):
        super().__init__(reason)
        self.schema_version = schema_version
        self.controller_type = controller_type
        self.reason = reason


class UnsupportedFormatError(Exception):
    """El archivo no es un L5X válido (ej. ACD binario, otro formato XML, etc.)."""

    pass


# ─────────────────────────────────────────────────────────────────────────
# Shapes de datos (definidos en el SKILL.md sección "Shapes")
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Parameter:
    """Parámetro de AOI (Input/Output/InOut)."""

    name: str
    usage: str  # "Input" | "Output" | "InOut"
    datatype: str
    dimension: str = ""  # "" para escalar, "10" para array, etc.
    required: bool = False
    visible: bool = True
    default: str = ""
    description: str = ""


@dataclass
class Member:
    """Member de un UDT."""

    name: str
    datatype: str
    dimension: str = ""
    hidden: bool = False
    description: str = ""


@dataclass
class Tag:
    """Tag declarado (controller-scoped, program-scoped, o local de AOI)."""

    name: str
    scope: str  # "controller" | "<nombre-programa>" | "<nombre-aoi>"
    datatype: str
    dimension: str = ""
    description: str = ""
    constant: bool = False
    external_access: str = ""  # "Read/Write" | "Read Only" | "None"
    # Para tags con datatype AXIS_*: módulo drive asociado, formato
    # "{ModuleName}:{Channel}" (ej. "M9_507U1:Ch20"). Valor "<NA>" si está
    # explícitamente marcado como no asociado. Vacío si no aplica.
    # Fuente: <Data Format="Axis"><AxisParameters MotionModule="..."/>
    motion_module: str = ""


@dataclass
class Routine:
    """Rutina (puede pertenecer a un programa o a un AOI).

    Si pertenece a un AOI, .program será None.
    """

    name: str
    program: Optional[str]
    type: str  # "RLL" | "ST" | "FBD" | "SFC"
    code: str
    description: str = ""


@dataclass
class AOIDetail:
    """AOI con su definición completa."""

    name: str
    revision: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)
    local_tags: list[Tag] = field(default_factory=list)
    routines: dict[str, Routine] = field(default_factory=dict)


@dataclass
class UDTDetail:
    """UDT con todos sus members."""

    name: str
    family: str
    description: str
    members: list[Member] = field(default_factory=list)


@dataclass
class SearchHit:
    """Resultado de búsqueda full-text en código."""

    location: str  # ej: "Programs/MainProgram/Routines/Drive_Rolls/Rung_5"
    snippet: str
    context: str   # "rung" | "st_line" | "tag_description" | etc.


@dataclass
class Observation:
    """Inconsistencia o nota detectada durante el parseo."""

    severity: str  # "info" | "warning"
    category: str  # "duplicated_aoi" | "orphan_tag" | "empty_routine" | etc.
    message: str
    references: list[str] = field(default_factory=list)


@dataclass
class Module:
    """Módulo físico del rack o de la red."""

    name: str  # puede ser sintético si el L5X no provee Name (caso POINT I/O)
    catalog_number: str
    vendor: str = ""
    parent_module: str = ""
    parent_port_id: str = ""
    inhibited: bool = False
    major_fault: bool = False
    has_explicit_name: bool = True  # False si es sintético


@dataclass
class Task:
    """Task del controller."""

    name: str
    type: str  # "CONTINUOUS" | "PERIODIC" | "EVENT"
    priority: int = 10
    rate: float = 0.0  # ms (solo para PERIODIC)
    watchdog: float = 0.0
    scheduled_programs: list[str] = field(default_factory=list)


@dataclass
class Program:
    """Programa del controller."""

    name: str
    main_routine: str = ""
    fault_routine: str = ""
    test_edits: bool = False
    disabled: bool = False


@dataclass
class Identity:
    """Identidad del proyecto (header del L5X)."""

    target_name: str           # ej. "CPU1"
    processor_type: str        # ej. "1768-L43"
    software_revision: str     # ej. "20.01"
    schema_revision: str       # ej. "1.0"
    major_rev: str = ""
    minor_rev: str = ""
    project_creation_date: str = ""
    last_modified_date: str = ""
    owner: str = ""
    export_date: str = ""


# ─────────────────────────────────────────────────────────────────────────
# Project — agrupa todo el modelo y expone API básica
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Project:
    """Modelo canónico de un proyecto Rockwell.

    Se construye via load_project() desde loader.py. Esta clase contiene la
    información ya extraída + una conexión SQLite opcional para queries
    futuras.

    En v0.1 los métodos de query (get_routine, get_aoi, get_udt, search) son
    implementaciones simples que recorren las listas. Optimizaciones avanzadas
    (full-text search nativo, índices) se diferieren a navigator.py.
    """

    identity: Identity
    modules: list[Module] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    programs: list[Program] = field(default_factory=list)
    routines: list[Routine] = field(default_factory=list)
    aois: list[AOIDetail] = field(default_factory=list)
    udts: list[UDTDetail] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    source_path: str = ""
    db_path: str = ""  # path al SQLite persistido

    # mapa_mental delega al módulo mapamental.py (import diferido para evitar
    # ciclo de importación model ↔ mapamental).
    @property
    def mapa_mental(self) -> str:
        """Mapa Mental del proyecto.

        Documento Markdown autocontenido (~800–1500 tokens) con seis secciones:
        identidad, arquitectura física, arquitectura lógica, mapa funcional
        de ejes, patrones de código, e issues/observaciones.

        La generación delega a mapamental.generate(self).
        """
        from .mapamental import generate
        return generate(self)
        return (
            f"# Mapa Mental — {self.identity.target_name}\n\n"
            f"_(Generador del Mapa Mental aún no implementado en este build "
            f"del paquete. Está planeado como el siguiente módulo a construir "
            f"después de loader.py + model.py. Mientras tanto, los datos están "
            f"todos cargados en `project` y disponibles vía atributos: "
            f"`project.identity`, `project.modules`, `project.programs`, "
            f"`project.aois`, `project.udts`, `project.tags`, `project.tasks`, "
            f"`project.observations`.)_\n\n"
            f"## Resumen rápido\n\n"
            f"- Controlador: {self.identity.processor_type}\n"
            f"- Studio 5000: v{self.identity.software_revision}\n"
            f"- Programas: {len(self.programs)}\n"
            f"- Tasks: {len(self.tasks)}\n"
            f"- Rutinas: {len(self.routines)}\n"
            f"- AOIs: {len(self.aois)}\n"
            f"- UDTs: {len(self.udts)}\n"
            f"- Módulos: {len(self.modules)}\n"
            f"- Tags (todos los scopes): {len(self.tags)}\n"
            f"- Observaciones detectadas: {len(self.observations)}\n"
        )

    # ─── Lupa puntual ──────────────────────────────────────────────────

    def get_routine(self, program: str, routine: str) -> Optional[Routine]:
        """Retorna una rutina específica de un programa, o None si no existe."""
        for r in self.routines:
            if r.program == program and r.name == routine:
                return r
        return None

    def get_aoi(self, aoi_name: str) -> Optional[AOIDetail]:
        """Retorna un AOI por nombre, o None si no existe."""
        for a in self.aois:
            if a.name == aoi_name:
                return a
        return None

    def get_udt(self, udt_name: str) -> Optional[UDTDetail]:
        """Retorna un UDT por nombre, o None si no existe."""
        for u in self.udts:
            if u.name == udt_name:
                return u
        return None

    # ─── Búsqueda full-text simple ────────────────────────────────────

    def search(self, query: str) -> list[SearchHit]:
        """Búsqueda case-insensitive en código de rutinas y descripciones de tags.

        Implementación v0.1: scan lineal sobre las listas en memoria. Para
        proyectos grandes y queries frecuentes, navigator.py implementará una
        capa con SQLite FTS5 o similar.
        """
        q = query.lower()
        hits: list[SearchHit] = []

        # Buscar en código de rutinas de programas
        for r in self.routines:
            if r.code and q in r.code.lower():
                where = (
                    f"Programs/{r.program}/Routines/{r.name}"
                    if r.program
                    else f"AOIs/?/Routines/{r.name}"  # AOI source debe venir desde aois
                )
                hits.append(
                    SearchHit(
                        location=where,
                        snippet=_first_match_snippet(r.code, q),
                        context="routine_code",
                    )
                )

        # Buscar en código de rutinas dentro de AOIs
        for aoi in self.aois:
            for rname, r in aoi.routines.items():
                if r.code and q in r.code.lower():
                    hits.append(
                        SearchHit(
                            location=f"AOIs/{aoi.name}/Routines/{rname}",
                            snippet=_first_match_snippet(r.code, q),
                            context="routine_code",
                        )
                    )

        # Buscar en descripciones de tags
        for t in self.tags:
            if t.description and q in t.description.lower():
                hits.append(
                    SearchHit(
                        location=f"Tags[{t.scope}]/{t.name}",
                        snippet=t.description[:200],
                        context="tag_description",
                    )
                )

        return hits


def _first_match_snippet(text: str, query: str, window: int = 80) -> str:
    """Devuelve un snippet centrado en la primera ocurrencia de `query`.

    TODO (v0.2): para rutinas RLL incluir el rung completo + el comentario
    del rung en el snippet cuando esté disponible. Esto requiere que loader
    indexe el código por rung al cargar (parsing adicional) o que SearchHit
    porte una referencia al rung_number para que un consumidor pueda
    re-leerlo del modelo. Actualmente el snippet es una ventana de
    caracteres alrededor del match — funcional para v0.1 pero pierde la
    estructura semántica del ladder.
    """
    idx = text.lower().find(query.lower())
    if idx < 0:
        return text[:window]
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(query) + window // 2)
    snippet = text[start:end].replace("\n", " ")
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


# ─────────────────────────────────────────────────────────────────────────
# Schema SQLite
# ─────────────────────────────────────────────────────────────────────────

SCHEMA_VERSION = "v0.1.0"

# El schema cubre TODO el modelo, incluyendo `xref` que se crea VACÍA en v0.1
# (DT-009 — los schemas se establecen temprano y crecen aditivamente).
SCHEMA_SQL = """
-- Metadatos de la base
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- Identidad del proyecto
CREATE TABLE IF NOT EXISTS identity (
    target_name           TEXT,
    processor_type        TEXT,
    software_revision     TEXT,
    schema_revision       TEXT,
    major_rev             TEXT,
    minor_rev             TEXT,
    project_creation_date TEXT,
    last_modified_date    TEXT,
    owner                 TEXT,
    export_date           TEXT
);

-- Módulos físicos
CREATE TABLE IF NOT EXISTS modules (
    name                TEXT,
    catalog_number      TEXT,
    vendor              TEXT,
    parent_module       TEXT,
    parent_port_id      TEXT,
    inhibited           INTEGER,
    major_fault         INTEGER,
    has_explicit_name   INTEGER
);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    name        TEXT PRIMARY KEY,
    type        TEXT,
    priority    INTEGER,
    rate        REAL,
    watchdog    REAL
);

CREATE TABLE IF NOT EXISTS task_programs (
    task_name      TEXT,
    program_name   TEXT,
    PRIMARY KEY (task_name, program_name)
);

-- Programs
CREATE TABLE IF NOT EXISTS programs (
    name           TEXT PRIMARY KEY,
    main_routine   TEXT,
    fault_routine  TEXT,
    test_edits     INTEGER,
    disabled       INTEGER
);

-- Routines (de programas; las de AOIs se asocian via aoi_name en la tabla aoi_routines)
CREATE TABLE IF NOT EXISTS routines (
    program     TEXT,
    name        TEXT,
    type        TEXT,
    code        TEXT,
    description TEXT,
    PRIMARY KEY (program, name)
);

-- AOIs
CREATE TABLE IF NOT EXISTS aois (
    name        TEXT PRIMARY KEY,
    revision    TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS aoi_parameters (
    aoi_name    TEXT,
    name        TEXT,
    usage       TEXT,
    datatype    TEXT,
    dimension   TEXT,
    required    INTEGER,
    visible     INTEGER,
    "default"   TEXT,
    description TEXT,
    PRIMARY KEY (aoi_name, name)
);

CREATE TABLE IF NOT EXISTS aoi_routines (
    aoi_name    TEXT,
    name        TEXT,
    type        TEXT,
    code        TEXT,
    description TEXT,
    PRIMARY KEY (aoi_name, name)
);

-- UDTs
CREATE TABLE IF NOT EXISTS udts (
    name        TEXT PRIMARY KEY,
    family      TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS udt_members (
    udt_name    TEXT,
    name        TEXT,
    datatype    TEXT,
    dimension   TEXT,
    hidden      INTEGER,
    description TEXT,
    PRIMARY KEY (udt_name, name)
);

-- Tags (controller-scoped, program-scoped, AOI-local — discriminados por scope)
CREATE TABLE IF NOT EXISTS tags (
    name             TEXT,
    scope            TEXT,
    datatype         TEXT,
    dimension        TEXT,
    description      TEXT,
    constant         INTEGER,
    external_access  TEXT,
    motion_module    TEXT,           -- solo para AXIS_*: "{ModuleName}:{Channel}" o "<NA>" o ""
    PRIMARY KEY (scope, name)
);

-- Observaciones detectadas durante el parseo
CREATE TABLE IF NOT EXISTS observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    severity    TEXT,
    category    TEXT,
    message     TEXT,
    references_ TEXT  -- JSON array; "references" es palabra reservada en algunos contextos
);

-- Cross-references derivadas (tabla VACÍA en v0.1, poblada por tracer.py en v0.2 — DT-009)
CREATE TABLE IF NOT EXISTS xref (
    source_kind     TEXT,    -- "rung" | "st_line" | "fbd_block"
    source_location TEXT,    -- ej: "Programs/MainProgram/Routines/X/Rung_5"
    operand         TEXT,    -- nombre del tag/operando referenciado
    operand_kind    TEXT,    -- "tag" | "constant" | "literal"
    usage           TEXT     -- "read" | "write" | "both"
);
CREATE INDEX IF NOT EXISTS idx_xref_operand ON xref(operand);
CREATE INDEX IF NOT EXISTS idx_xref_source  ON xref(source_location);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Crea/abre la base SQLite y aplica el schema completo (incluye xref vacía).

    El schema es idempotente (CREATE TABLE IF NOT EXISTS).
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("schema_version", SCHEMA_VERSION),
    )
    conn.commit()
    return conn
