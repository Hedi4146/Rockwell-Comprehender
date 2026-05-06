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

    `protected=True` indica que la rutina está protegida con Source Protection
    en Studio 5000 (`<EncodedData EncryptionConfig="9">` en el L5X).
    Cuando es protected, `code=""` porque el cuerpo está encriptado en blob
    base64 que no podemos parsear. Es común en GuardLogix Safety routines y
    en proyectos integrados por terceros (Amantrini, HCH, etc.).
    """

    name: str
    program: Optional[str]
    type: str  # "RLL" | "ST" | "FBD" | "SFC"
    code: str
    description: str = ""
    protected: bool = False


@dataclass
class AOIDetail:
    """AOI con su definición completa.

    `protected=True` indica que el AOI completo está encriptado (vendor
    como Xu/Jin/Rockwell/etc. lo distribuyó con Source Protection).
    Cuando es protected, `parameters` y `routines` quedan vacíos porque
    no podemos parsear el blob; solo conocemos el nombre y metadata del
    header (revision, vendor, etc.).
    """

    name: str
    revision: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)
    local_tags: list[Tag] = field(default_factory=list)
    routines: dict[str, Routine] = field(default_factory=dict)
    protected: bool = False


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
class PathStep:
    """Un paso de un path causal devuelto por `find_causal_path`.

    `target` es el tag alcanzado en este step (NO el operand de la xref entry,
    que apunta al predecesor). `via` es la entry que conectó el paso anterior
    con este target.
    """

    target: str
    via: "XrefEntry"


@dataclass
class XrefEntry:
    """Una entrada del cross-reference (resultado de writers_of/readers_of/etc).

    Cada entry corresponde a una referencia individual a un operando dentro
    de un rung. Si el operando original era estructurado (`M3Data.Input.X`),
    `operand_kind="tag_root"` indica que la entry fue matched vía el root
    indexing (la query fue por `M3Data` pero el código tenía `M3Data.Input.X`).
    """

    operand: str              # nombre tal como aparece en xref (puede ser root o full path)
    operand_kind: str         # "tag" | "tag_root"
    usage: str                # "read" | "write" | "both"
    location: str             # ej: "AOIs/AHT_Unwinder/Routines/Logic/Rung_13"
    operator: str             # instrucción que produjo la referencia
    instruction_index: int = 0  # posición 0-based dentro del rung (Paso 5b.1)
    source_kind: str = "rung"


@dataclass
class TraceNode:
    """Nodo del árbol de trace (causal hacia atrás o hacia adelante).

    Cada nodo representa un operando alcanzado durante el trace. `via`
    indica el XrefEntry (writer/reader) que conectó al nodo padre con
    este nodo. `children` son los siguientes niveles del trace.
    `truncated` se setea cuando se cortó la expansión:
        - "depth"    → alcanzamos depth limit
        - "cycle"    → el operando ya estaba en el camino (evitar loop)
        - "branches" → más de max_branches writers/readers; se truncó la lista
    """

    operand: str
    depth: int = 0
    via: Optional["XrefEntry"] = None   # None para el root del trace
    children: list["TraceNode"] = field(default_factory=list)
    truncated: Optional[str] = None

    def render(self, indent: int = 0, max_label: int = 0) -> str:
        """Devuelve el árbol como string ASCII para impresión."""
        lines: list[str] = []
        self._render_into(lines, prefix="", is_last=True, is_root=True)
        return "\n".join(lines)

    def _render_into(self, lines: list[str], prefix: str, is_last: bool, is_root: bool) -> None:
        if is_root:
            label = self.operand
            if self.truncated:
                label += f"  [TRUNCATED: {self.truncated}]"
            lines.append(label)
            child_prefix = ""
        else:
            connector = "└─ " if is_last else "├─ "
            via_str = ""
            if self.via is not None:
                via_str = f"  ← via {self.via.operator} @ {self.via.location}  [{self.via.usage}]"
            label = f"{prefix}{connector}{self.operand}{via_str}"
            if self.truncated:
                label += f"  [TRUNCATED: {self.truncated}]"
            lines.append(label)
            child_prefix = prefix + ("   " if is_last else "│  ")

        for i, child in enumerate(self.children):
            child._render_into(
                lines, prefix=child_prefix,
                is_last=(i == len(self.children) - 1),
                is_root=False,
            )

    def count_nodes(self) -> int:
        """Cuenta total de nodos en el árbol (incluye este)."""
        return 1 + sum(c.count_nodes() for c in self.children)


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

    # ─── Trace de dependencias (v0.2) ─────────────────────────────────

    # Flag interno: True después del primer build_xref. Se evalúa lazy en
    # cada llamada a writers_of/readers_of/references_of. NO es persistente
    # (si se vuelve a cargar el proyecto, el SQLite es nuevo y el flag se
    # resetea automáticamente al construirse el dataclass).
    _xref_built: bool = field(default=False, repr=False, compare=False)
    # Cache de invocaciones de AOIs para cross-AOI traversal (Paso 5b.2).
    # Key: aoi_name → list[(location, instruction_index, args_in_order)].
    _invocation_cache: dict = field(default_factory=dict, repr=False, compare=False)
    # Cache lazy de pattern recognition (v0.3 Capa C). None hasta primer acceso.
    _detected_patterns_cache: object = field(default=None, repr=False, compare=False)

    @property
    def detected_patterns(self):
        """Devuelve los patterns detectados (zonas, naming matches, roles).

        Lazy: la primera llamada ejecuta `detect_patterns(self)`; las
        siguientes retornan el cache. Ver `rockwell_comprehender.patterns`.
        """
        if self._detected_patterns_cache is None:
            from .patterns import detect_patterns
            self._detected_patterns_cache = detect_patterns(self)
        return self._detected_patterns_cache

    def get_instruction_metadata(self, name: str):
        """Devuelve metadata curada de una instrucción Rockwell, o None.

        Wrapper de conveniencia para `instruction_library.get_instruction_metadata`.
        Útil en flujos donde se tiene el Project en mano y se quiere consultar
        metadata sin importar el módulo aparte.
        """
        from .instruction_library import get_instruction_metadata as _get
        return _get(name)

    def identify_domain(self, query: str) -> list:
        """Identifica AOIs/routines/programs relacionados con un síntoma.

        Wrapper de conveniencia para `domain_lexicon.identify_domain`.
        Implementa el criterio v0.3 del Vision: dado un síntoma en lenguaje
        natural ("problema en empalme", "falla del unwinder"), retorna
        list[DomainHit] ordenada por confidence desc.

        Stack mínimo (DT-008): heurística regex + lexicón curado, sin
        embeddings ni LLM externo.
        """
        from .domain_lexicon import identify_domain as _identify
        return _identify(self, query)

    def detect_smells(self) -> list:
        """Detecta architecture smells y best-practice violations.

        Wrapper de conveniencia para `smells.detect_smells`. Ejecuta C.1
        (5 reglas estructurales) + C.2 (10+ best practices Rockwell
        curadas vía NotebookLM) contra el proyecto.

        Returns:
            list[Smell] ordenada por severidad desc + kind.
        """
        from .smells import detect_smells as _detect
        return _detect(self)

    def _ensure_xref_built(self) -> None:
        """Construye el xref la primera vez que se necesita."""
        if self._xref_built:
            return
        from .tracer import build_xref  # import diferido para evitar ciclo
        build_xref(self)
        self._xref_built = True

    def writers_of(self, tag: str, scope: Optional[str] = None) -> list[XrefEntry]:
        """Devuelve todas las referencias donde `tag` es escrito.

        Incluye writes directos (`OTE`, `MOV`, `CPT(dest, ...)`) y writes vía
        AOI invocations (parámetros Output) o InOut (que cuentan como write).

        Args:
            tag: nombre del operando. Puede ser path completo
                (`M3Data.Input.Dancer.Position`) o root (`M3Data`). En el
                segundo caso, encuentra TODAS las referencias a sub-fields
                gracias al root indexing del Paso 3.
            scope: opcional. Filtra por prefijo de location. Útil cuando el
                mismo nombre de tag local existe en múltiples AOIs. Ejemplos:
                - `"Programs"` → solo writes en código de programas
                - `"AOIs/AHT_Unwinder"` → solo writes dentro de AHT_Unwinder
                - `"AOIs/AHT_Unwinder/Routines/Logic"` → solo en esa rutina
        """
        return self._xref_query(tag, scope, usage_in=("write", "both"))

    def readers_of(self, tag: str, scope: Optional[str] = None) -> list[XrefEntry]:
        """Devuelve todas las referencias donde `tag` es leído.

        Incluye lecturas directas (`XIC`, `XIO`, args de comparadores y math)
        y lecturas vía AOI invocations (parámetros Input) o InOut. Para
        operadores tipo CPT/CMP, incluye también tags extraídos del
        sub-parser de la expresión aritmética.

        Args/scope: ver `writers_of`.
        """
        return self._xref_query(tag, scope, usage_in=("read", "both"))

    def references_of(self, tag: str, scope: Optional[str] = None) -> list[XrefEntry]:
        """Devuelve TODAS las referencias a `tag` (reads + writes + both).

        Útil cuando se quiere ver el universo completo de menciones del tag
        en código sin filtrar por dirección.
        """
        return self._xref_query(tag, scope, usage_in=("read", "write", "both"))

    def trace_back(
        self,
        tag: str,
        depth: int = 3,
        max_branches: int = 20,
        scope: Optional[str] = None,
    ) -> "TraceNode":
        """Trace causal hacia atrás (antecedentes). Soporta cross-AOI (Paso 5b.2).

        Para cada writer del tag (granularidad por-instrucción del Paso 5b.1),
        encuentra los tags leídos por la MISMA instrucción y los considera
        antecedentes. Si un antecedente es un parameter del AOI actual, rastrea
        las invocaciones del AOI hacia afuera y resuelve qué tag se pasa como
        ese parameter en cada invocación (cross-AOI traversal del Paso 5b.2).

        Recursivo con limitación por depth, ciclo (visited set por camino),
        y max_branches.

        Args:
            tag: operando del que rastrear hacia atrás.
            depth: profundidad máxima del árbol.
            max_branches: si un nivel tiene más de N writers (intra + cross),
                se truncan y se marca `truncated="branches"`.
            scope: opcional. Filtro inicial de writers (intra-scope). El
                cross-AOI sale del scope al cruzar (busca invocadores del
                AOI en cualquier parte del corpus).
        """
        self._ensure_xref_built()
        aoi_context = self._infer_aoi_context_from_scope(scope)
        return self._trace_back_node(
            tag=tag,
            depth_limit=depth,
            max_branches=max_branches,
            scope=scope,
            visited=frozenset(),
            current_depth=0,
            via=None,
            aoi_context=aoi_context,
        )

    def trace_forward(
        self,
        tag: str,
        depth: int = 3,
        max_branches: int = 20,
        scope: Optional[str] = None,
    ) -> "TraceNode":
        """Trace causal hacia adelante (consecuentes) — versión intra-scope.

        Para cada reader del tag, encuentra los tags escritos en el MISMO
        rung y los considera consecuentes potenciales. Mismas limitaciones
        que `trace_back` respecto a cross-AOI.
        """
        self._ensure_xref_built()
        aoi_context = self._infer_aoi_context_from_scope(scope)
        return self._trace_forward_node(
            tag=tag,
            depth_limit=depth,
            max_branches=max_branches,
            scope=scope,
            visited=frozenset(),
            current_depth=0,
            via=None,
            aoi_context=aoi_context,
        )

    def _trace_back_node(
        self,
        tag: str,
        depth_limit: int,
        max_branches: int,
        scope: Optional[str],
        visited: frozenset,
        current_depth: int,
        via: Optional[XrefEntry],
        aoi_context: Optional[AOIDetail] = None,
    ) -> "TraceNode":
        node = TraceNode(operand=tag, depth=current_depth, via=via)
        if tag in visited:
            node.truncated = "cycle"
            return node
        if current_depth >= depth_limit:
            node.truncated = "depth"
            return node

        # Path 1: writers intra-scope (granularidad por-instrucción del Paso 5b.1)
        intra_writers = self.writers_of(tag, scope=scope)

        # Path 2: cross-AOI (Paso 5b.2). Si tag es un parameter visible del AOI
        # actual y no fue escrito intra-scope, rastrear hacia afuera siguiendo
        # las invocaciones del AOI.
        cross_writers: list[tuple[XrefEntry, Optional[AOIDetail]]] = []
        if aoi_context is not None:
            visible_param_names = {p.name for p in aoi_context.parameters if p.visible}
            if tag in visible_param_names:
                cross_writers = self._cross_aoi_back(aoi_context, tag)

        total = len(intra_writers) + len(cross_writers)
        if total == 0:
            return node

        new_visited = visited | {tag}
        if total > max_branches:
            node.truncated = "branches"
            # Mantener proporcionalmente
            keep_intra = min(len(intra_writers), max_branches // 2 + 1)
            intra_writers = intra_writers[:keep_intra]
            cross_writers = cross_writers[: max_branches - keep_intra]

        for w in intra_writers:
            upstream_tags = self._reads_at_instruction(w.location, w.instruction_index)
            child_aoi_context = self._infer_aoi_context_from_location(w.location)
            for ut in upstream_tags:
                if ut == tag:
                    continue
                child = self._trace_back_node(
                    tag=ut,
                    depth_limit=depth_limit,
                    max_branches=max_branches,
                    scope=scope,
                    visited=new_visited,
                    current_depth=current_depth + 1,
                    via=w,
                    aoi_context=child_aoi_context,
                )
                node.children.append(child)

        for entry, child_aoi_context in cross_writers:
            # `entry.operand` es el arg pasado en la invocación = nuevo tag a rastrear
            child = self._trace_back_node(
                tag=entry.operand,
                depth_limit=depth_limit,
                max_branches=max_branches,
                scope=None,  # cross-AOI sale del scope inicial
                visited=new_visited,
                current_depth=current_depth + 1,
                via=entry,
                aoi_context=child_aoi_context,
            )
            node.children.append(child)
        return node

    def _trace_forward_node(
        self,
        tag: str,
        depth_limit: int,
        max_branches: int,
        scope: Optional[str],
        visited: frozenset,
        current_depth: int,
        via: Optional[XrefEntry],
        aoi_context: Optional[AOIDetail] = None,
    ) -> "TraceNode":
        node = TraceNode(operand=tag, depth=current_depth, via=via)
        if tag in visited:
            node.truncated = "cycle"
            return node
        if current_depth >= depth_limit:
            node.truncated = "depth"
            return node

        readers = self.readers_of(tag, scope=scope)
        if not readers:
            return node

        new_visited = visited | {tag}
        if len(readers) > max_branches:
            node.truncated = "branches"
            readers = readers[:max_branches]

        for r in readers:
            downstream_tags = self._writes_at_instruction(r.location, r.instruction_index)
            child_aoi_context = self._infer_aoi_context_from_location(r.location)
            for dt in downstream_tags:
                if dt == tag:
                    continue
                child = self._trace_forward_node(
                    tag=dt,
                    depth_limit=depth_limit,
                    max_branches=max_branches,
                    scope=scope,
                    visited=new_visited,
                    current_depth=current_depth + 1,
                    via=r,
                    aoi_context=child_aoi_context,
                )
                node.children.append(child)
        return node

    # ─── BFS find_causal_path (Paso 3 v0.2.x) ─────────────────────────

    def find_causal_path(
        self,
        from_tag: str,
        to_tag: str,
        max_depth: int = 10,
        direction: str = "back",
        scope: Optional[str] = None,
    ) -> Optional[list["PathStep"]]:
        """Encuentra el camino causal más corto entre dos tags usando BFS.

        Resuelve el problema de explosión de árbol que aparece con `trace_back`
        a depth alto: en lugar de generar todo el grafo y filtrar, BFS encuentra
        el path más corto en O(nodos+aristas) sin construir el árbol completo.

        Args:
            from_tag: tag origen (donde inicia la búsqueda).
            to_tag: tag destino que queremos alcanzar.
            max_depth: profundidad máxima de exploración. 10 es razonable para
                proyectos industriales típicos.
            direction:
                - `"back"`: rastrea hacia atrás (`from_tag` depende causalmente
                   de `to_tag` — antecedentes / writers chain). Soporta cross-AOI.
                - `"forward"`: rastrea hacia adelante (`to_tag` depende de
                   `from_tag` — consecuentes / readers chain). Cross-AOI no
                   implementado todavía.
            scope: opcional. Filtro inicial de búsqueda. Cuando el BFS cruza
                una invocación AOI, el `scope` se resetea a None desde ese
                hop en adelante (cross-AOI sale del scope intencionalmente).

        Returns:
            Lista de `PathStep`: cada step expone `target` (tag alcanzado) y
            `via` (XrefEntry que conectó). Lista vacía si `from_tag == to_tag`.
            `None` si no existe path en `max_depth`.
        """
        self._ensure_xref_built()

        if from_tag == to_tag:
            return []

        initial_aoi_ctx = self._infer_aoi_context_from_scope(scope)

        from collections import deque
        # frontier: deque de (tag, aoi_context, depth, current_scope)
        # current_scope se resetea a None después de un cross-AOI hop.
        # visited: dict tag -> (predecessor_tag, via_entry) — None para from_tag
        frontier: deque = deque([(from_tag, initial_aoi_ctx, 0, scope)])
        visited: dict[str, Optional[tuple[str, XrefEntry]]] = {from_tag: None}

        while frontier:
            current, aoi_ctx, depth, current_scope = frontier.popleft()

            if depth >= max_depth:
                continue

            # Generar candidatos del próximo hop según dirección.
            # Cada candidato es (next_tag, via_entry, next_aoi_ctx, next_scope).
            candidates: list[tuple[str, XrefEntry, Optional[AOIDetail], Optional[str]]] = []

            if direction == "back":
                # Intra-scope: writers + sus reads (granularidad por-instrucción).
                # next_scope = current_scope (sigue intra)
                for w in self.writers_of(current, scope=current_scope):
                    new_ctx = self._infer_aoi_context_from_location(w.location)
                    for ut in self._reads_at_instruction(w.location, w.instruction_index):
                        if ut == current:
                            continue
                        candidates.append((ut, w, new_ctx, current_scope))
                # Cross-AOI: si current es parameter del aoi_context actual.
                # next_scope = None (salimos del scope al cruzar la frontera).
                if aoi_ctx is not None:
                    visible_param_names = {p.name for p in aoi_ctx.parameters if p.visible}
                    if current in visible_param_names:
                        for entry, child_ctx in self._cross_aoi_back(aoi_ctx, current):
                            candidates.append((entry.operand, entry, child_ctx, None))
            elif direction == "forward":
                for r in self.readers_of(current, scope=current_scope):
                    new_ctx = self._infer_aoi_context_from_location(r.location)
                    for dt in self._writes_at_instruction(r.location, r.instruction_index):
                        if dt == current:
                            continue
                        candidates.append((dt, r, new_ctx, current_scope))
                # Cross-AOI forward: no implementado en esta iteración
            else:
                raise ValueError(f"direction debe ser 'back' o 'forward', no '{direction}'")

            for next_tag, via, next_ctx, next_scope in candidates:
                if next_tag in visited:
                    continue
                visited[next_tag] = (current, via)

                if next_tag == to_tag:
                    return self._reconstruct_path(visited, to_tag)

                frontier.append((next_tag, next_ctx, depth + 1, next_scope))

        return None  # no path found within max_depth

    @staticmethod
    def _reconstruct_path(
        visited: dict, end: str
    ) -> list["PathStep"]:
        """Reconstruye el path BFS desde `end` hacia atrás siguiendo predecessors.

        Cada PathStep tiene `target` = el tag alcanzado en ese step (NO el operand
        de la xref entry, que apunta al predecesor del step).
        """
        steps: list[PathStep] = []
        current = end
        while visited.get(current) is not None:
            pred, via = visited[current]
            steps.append(PathStep(target=current, via=via))
            current = pred
        return list(reversed(steps))

    # ─── Cross-AOI helpers (Paso 5b.2) ────────────────────────────────

    def _infer_aoi_context_from_scope(self, scope: Optional[str]) -> Optional[AOIDetail]:
        """Si `scope` es 'AOIs/X' o 'AOIs/X/...' devuelve self.get_aoi('X')."""
        if not scope or not scope.startswith("AOIs/"):
            return None
        parts = scope.split("/", 2)
        if len(parts) >= 2:
            return self.get_aoi(parts[1])
        return None

    def _infer_aoi_context_from_location(self, location: str) -> Optional[AOIDetail]:
        """Si `location` es 'AOIs/X/Routines/...' devuelve self.get_aoi('X')."""
        if not location.startswith("AOIs/"):
            return None
        parts = location.split("/", 3)
        if len(parts) >= 2:
            return self.get_aoi(parts[1])
        return None

    def _get_aoi_invocations(self, aoi_name: str) -> list[tuple[str, int, list[str]]]:
        """Re-tokeniza el corpus para encontrar todas las invocaciones del AOI.

        Retorna list de (location, instruction_index, args_in_order). Cached
        per-call para evitar re-tokenizar repetidamente.
        """
        if aoi_name in self._invocation_cache:
            return self._invocation_cache[aoi_name]

        from .tokenizer import tokenize_rll
        results: list[tuple[str, int, list[str]]] = []

        for r in self.routines:
            if not r.code or r.type != "RLL":
                continue
            for rung in tokenize_rll(r.code):
                for i, inst in enumerate(rung.instructions):
                    if inst.operator == aoi_name:
                        args = [o.text for o in inst.operands]
                        loc = f"Programs/{r.program}/Routines/{r.name}/Rung_{rung.number}"
                        results.append((loc, i, args))

        for a in self.aois:
            for rname, r in a.routines.items():
                if not r.code or r.type != "RLL":
                    continue
                for rung in tokenize_rll(r.code):
                    for i, inst in enumerate(rung.instructions):
                        if inst.operator == aoi_name:
                            args = [o.text for o in inst.operands]
                            loc = f"AOIs/{a.name}/Routines/{rname}/Rung_{rung.number}"
                            results.append((loc, i, args))

        self._invocation_cache[aoi_name] = results
        return results

    def _cross_aoi_back(
        self, aoi: AOIDetail, param_name: str
    ) -> list[tuple[XrefEntry, Optional["AOIDetail"]]]:
        """Para `param_name` (un visible parameter del AOI), encuentra los args
        correspondientes en cada invocación. Devuelve list de
        (XrefEntry representando el arg, contexto AOI del invoker).

        Convención de mapeo:
            arg[0] de la invocación = backing tag (instance data)
            arg[i] (i>=1) → visible_params[i-1]
        """
        visible_params = [p for p in aoi.parameters if p.visible]
        param_idx = next(
            (i for i, p in enumerate(visible_params) if p.name == param_name),
            None,
        )
        if param_idx is None:
            return []
        arg_idx = param_idx + 1  # +1 porque arg[0] = backing

        results: list[tuple[XrefEntry, Optional[AOIDetail]]] = []
        for loc, inst_idx, args in self._get_aoi_invocations(aoi.name):
            if arg_idx >= len(args):
                continue
            arg_text = args[arg_idx]
            if not arg_text:
                continue
            # Filtrar constantes/literales/enums obvios; solo seguimos tags
            first = arg_text[0]
            if first.isdigit() or first in ("-", "?", '"', "'"):
                continue
            # Construir XrefEntry sintética representando el arg
            entry = XrefEntry(
                operand=arg_text,
                operand_kind="tag",
                usage="write",  # la invocación AOI "escribe" en el param desde fuera
                location=loc,
                operator=aoi.name,
                instruction_index=inst_idx,
                source_kind="rung",
            )
            child_context = self._infer_aoi_context_from_location(loc)
            results.append((entry, child_context))
        return results

    def _reads_at_location(self, location: str) -> list[str]:
        """Tags leídos en el rung especificado (todas las instrucciones)."""
        return self._tags_at_location(location, None, usage_in=("read", "both"))

    def _writes_at_location(self, location: str) -> list[str]:
        """Tags escritos en el rung especificado (todas las instrucciones)."""
        return self._tags_at_location(location, None, usage_in=("write", "both"))

    def _reads_at_instruction(self, location: str, instruction_index: int) -> list[str]:
        """Tags leídos por la instrucción específica dentro del rung (Paso 5b.1).

        Esta es la granularidad fina que necesita trace_back para no producir
        ruido lateral cuando el rung tiene múltiples instrucciones distintas.
        """
        return self._tags_at_location(location, instruction_index, usage_in=("read", "both"))

    def _writes_at_instruction(self, location: str, instruction_index: int) -> list[str]:
        """Tags escritos por la instrucción específica dentro del rung."""
        return self._tags_at_location(location, instruction_index, usage_in=("write", "both"))

    def _tags_at_location(
        self,
        location: str,
        instruction_index: Optional[int],
        usage_in: tuple[str, ...],
    ) -> list[str]:
        if not self.db_path:
            return []
        import sqlite3 as _sql
        conn = _sql.connect(self.db_path)
        try:
            cur = conn.cursor()
            placeholders = ",".join("?" * len(usage_in))
            sql = (
                f"SELECT DISTINCT operand FROM xref "
                f"WHERE source_location = ? AND usage IN ({placeholders}) "
                f"AND operand_kind = 'tag'"
            )
            params: list = [location, *usage_in]
            if instruction_index is not None:
                sql += " AND instruction_index = ?"
                params.append(instruction_index)
            sql += " ORDER BY operand"
            return [row[0] for row in cur.execute(sql, params)]
        finally:
            conn.close()

    def _xref_query(
        self,
        tag: str,
        scope: Optional[str],
        usage_in: tuple[str, ...],
    ) -> list[XrefEntry]:
        self._ensure_xref_built()
        if not self.db_path:
            return []
        import sqlite3 as _sql  # diferido
        conn = _sql.connect(self.db_path)
        try:
            cur = conn.cursor()
            placeholders = ",".join("?" * len(usage_in))
            sql = (
                f"SELECT operand, operand_kind, usage, source_location, operator, "
                f"instruction_index, source_kind "
                f"FROM xref "
                f"WHERE operand = ? AND usage IN ({placeholders})"
            )
            params: list = [tag, *usage_in]
            if scope:
                sql += " AND source_location LIKE ?"
                params.append(scope.rstrip("/") + "%")
            sql += " ORDER BY source_location, instruction_index, operator"
            return [
                XrefEntry(
                    operand=row[0],
                    operand_kind=row[1],
                    usage=row[2],
                    location=row[3],
                    operator=row[4],
                    instruction_index=row[5],
                    source_kind=row[6],
                )
                for row in cur.execute(sql, params)
            ]
        finally:
            conn.close()

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

SCHEMA_VERSION = "v0.2.2"  # bump: + columnas protected en routines / aoi_routines / aois

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
-- v0.2.2: + protected (Source Protection / EncodedData EncryptionConfig=9)
CREATE TABLE IF NOT EXISTS routines (
    program     TEXT,
    name        TEXT,
    type        TEXT,
    code        TEXT,
    description TEXT,
    protected   INTEGER DEFAULT 0,
    PRIMARY KEY (program, name)
);

-- AOIs (v0.2.2: + protected)
CREATE TABLE IF NOT EXISTS aois (
    name        TEXT PRIMARY KEY,
    revision    TEXT,
    description TEXT,
    protected   INTEGER DEFAULT 0
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

-- v0.2.2: + protected
CREATE TABLE IF NOT EXISTS aoi_routines (
    aoi_name    TEXT,
    name        TEXT,
    type        TEXT,
    code        TEXT,
    description TEXT,
    protected   INTEGER DEFAULT 0,
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

-- Cross-references derivadas (tabla creada vacía en v0.1, poblada por
-- tracer.build_xref() en v0.2 — DT-009).
--
-- Evolución:
-- v0.2.0: + columna `operator` (instrucción que produjo la referencia,
--         ej. "OTE", "MOV", "AHT_CtcSplicer"). Cambio aditivo (DT-009).
-- v0.2.1: + columna `instruction_index` (posición 0-based de la instrucción
--         dentro del rung). Habilita granularidad por-instrucción para trace_back
--         (resuelve el ruido lateral cuando un rung tiene múltiples writes).
--
-- `operand_kind` puede ser "tag" (referencia directa al operando) o "tag_root"
-- (entrada sintética del root de un tag estructurado — p.ej. una referencia a
-- "M3Data.Input.X" produce dos rows: una con operand="M3Data.Input.X" kind="tag",
-- otra con operand="M3Data" kind="tag_root").
CREATE TABLE IF NOT EXISTS xref (
    source_kind        TEXT,     -- "rung" | "st_line" | "fbd_block"
    source_location    TEXT,     -- ej: "Programs/MainProgram/Routines/X/Rung_5"
    operand            TEXT,     -- nombre del tag/operando referenciado
    operand_kind       TEXT,     -- "tag" | "tag_root"
    usage              TEXT,     -- "read" | "write" | "both"
    operator           TEXT,     -- instrucción que produjo el ref
    instruction_index  INTEGER   -- posición de la instrucción dentro del rung (0-based)
);
CREATE INDEX IF NOT EXISTS idx_xref_operand     ON xref(operand);
CREATE INDEX IF NOT EXISTS idx_xref_source      ON xref(source_location);
CREATE INDEX IF NOT EXISTS idx_xref_operator    ON xref(operator);
CREATE INDEX IF NOT EXISTS idx_xref_instruction ON xref(source_location, instruction_index);
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
