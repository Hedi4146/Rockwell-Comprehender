"""Tracer — análisis de dependencias de tags entre rutinas (v0.2 del paquete).

Construido en v0.2 (DT-009). Esta primera capa expone `classify_operands`,
la función que toma una `Instruction` (del tokenizer) y devuelve cada
operando con su uso semántico (`read` | `write` | `both` | `ignore`)
según:

1. Tabla curada de operadores RLL stdlib (top ~50 cubren ~99% del corpus
   real medido en CINTA + AQL).
2. Lookup dinámico contra `project.aois` para invocaciones de AOI: el
   primer argumento es backing tag (`write`, instance data) y los demás
   se mapean posicionalmente contra los `visible` parameters del AOI
   (cada `Parameter.usage` Input/Output/InOut → read/write/both).
3. Sub-parser de expresiones para `CPT(dest, expr)` y `CMP(expr)` —
   extrae las referencias a tags dentro de la expresión aritmética.
4. Lista negra de **enums** (`ON, OFF, Yes, No, Command, Real, Disabled,
   Trapezoidal, ...`) que el tokenizer clasifica como `tag` por su forma
   pero que semánticamente son literales.

Lo que NO hace este módulo (todavía):
- Construcción de `xref` en SQLite (Paso 3).
- API pública `writers_of/readers_of/trace_back` (Pasos 4-5).

Cobertura conocida (definida por DT-010 — validar empíricamente):
- Operadores raros (BSL/BSR/FFL/MSG/GSV/SSV/MAOC/MCCP/MCSV/MRP/XPY/AVE/LOG)
  reciben perfil mínimo (típicamente solo arg 0 como write). Las posiciones
  no listadas se ignoran. Si aparece un caso real que pida más detalle,
  se refina el perfil específico.
- Algunas instrucciones de motion (MAJ/MAM/MAH) tienen muchos args mixtos
  (struct + enums + numbers); cubrimos los args con tags productivos
  (axis, master, motion_control) y dejamos enums/units/numbers como ignore.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .model import AOIDetail, Project
from .tokenizer import Instruction, Operand


# ──────────────────────────────────────────────────────────────────────
# Estructuras de salida
# ──────────────────────────────────────────────────────────────────────


@dataclass
class ClassifiedOperand:
    """Un operando con su clasificación semántica."""

    operand: Operand
    usage: str  # "read" | "write" | "both" | "ignore"


@dataclass
class ClassificationResult:
    """Resultado de clasificar todos los operandos de una instrucción."""

    operator: str
    classified: list[ClassifiedOperand]
    # Tags adicionales extraídos de sub-expresiones de CPT/CMP (siempre `read`).
    expr_reads: list[Operand] = field(default_factory=list)
    # True si el operador no se reconoció ni como stdlib ni como AOI.
    unknown_operator: bool = False


# ──────────────────────────────────────────────────────────────────────
# Tabla de semántica de operadores RLL stdlib
# ──────────────────────────────────────────────────────────────────────


@dataclass
class OperatorProfile:
    """Perfil de semántica de un operador RLL.

    Las posiciones (0-indexed) listadas en `reads`/`writes`/`both` se
    clasifican con esa semántica si el operando en esa posición es de
    `kind="tag"`. Posiciones no listadas se ignoran (típicamente literals,
    enums o constantes).

    `cpt_expr_pos`: si está definido, el operando en esa posición es una
    expresión aritmética que se sub-parsea para extraer reads adicionales
    (caso CPT y CMP).
    """

    name: str
    reads: tuple[int, ...] = ()
    writes: tuple[int, ...] = ()
    both: tuple[int, ...] = ()
    cpt_expr_pos: Optional[int] = None


OPERATOR_TABLE: dict[str, OperatorProfile] = {
    # ── Bit logic ─────────────────────────────────────────────────
    "XIC":  OperatorProfile("XIC",  reads=(0,)),
    "XIO":  OperatorProfile("XIO",  reads=(0,)),
    "OTE":  OperatorProfile("OTE",  writes=(0,)),
    "OTL":  OperatorProfile("OTL",  writes=(0,)),
    "OTU":  OperatorProfile("OTU",  writes=(0,)),
    "ONS":  OperatorProfile("ONS",  both=(0,)),
    "OSR":  OperatorProfile("OSR",  reads=(0,), writes=(1,)),
    "OSF":  OperatorProfile("OSF",  reads=(0,), writes=(1,)),

    # ── Timer / Counter (struct = write; preset/accum no productivos) ──
    "TON":  OperatorProfile("TON",  writes=(0,)),
    "TOF":  OperatorProfile("TOF",  writes=(0,)),
    "RTO":  OperatorProfile("RTO",  writes=(0,)),
    "CTU":  OperatorProfile("CTU",  writes=(0,)),
    "CTD":  OperatorProfile("CTD",  writes=(0,)),
    "RES":  OperatorProfile("RES",  writes=(0,)),

    # ── Compare ───────────────────────────────────────────────────
    "EQU":  OperatorProfile("EQU",  reads=(0, 1)),
    "NEQ":  OperatorProfile("NEQ",  reads=(0, 1)),
    "LES":  OperatorProfile("LES",  reads=(0, 1)),
    "GRT":  OperatorProfile("GRT",  reads=(0, 1)),
    "LEQ":  OperatorProfile("LEQ",  reads=(0, 1)),
    "GEQ":  OperatorProfile("GEQ",  reads=(0, 1)),
    "LIM":  OperatorProfile("LIM",  reads=(0, 1, 2)),
    "MEQ":  OperatorProfile("MEQ",  reads=(0, 1, 2)),
    "CMP":  OperatorProfile("CMP",  cpt_expr_pos=0),

    # ── Math ──────────────────────────────────────────────────────
    "ADD":  OperatorProfile("ADD",  reads=(0, 1), writes=(2,)),
    "SUB":  OperatorProfile("SUB",  reads=(0, 1), writes=(2,)),
    "MUL":  OperatorProfile("MUL",  reads=(0, 1), writes=(2,)),
    "DIV":  OperatorProfile("DIV",  reads=(0, 1), writes=(2,)),
    "MOD":  OperatorProfile("MOD",  reads=(0, 1), writes=(2,)),
    "SQR":  OperatorProfile("SQR",  reads=(0,), writes=(1,)),
    "NEG":  OperatorProfile("NEG",  reads=(0,), writes=(1,)),
    "ABS":  OperatorProfile("ABS",  reads=(0,), writes=(1,)),
    "XPY":  OperatorProfile("XPY",  reads=(0, 1), writes=(2,)),
    "AVE":  OperatorProfile("AVE",  reads=(0,), writes=(1,)),
    "LOG":  OperatorProfile("LOG",  reads=(0,), writes=(1,)),

    # ── CPT (caso especial: arg 1 es expresión, sub-parsea) ───────
    "CPT":  OperatorProfile("CPT",  writes=(0,), cpt_expr_pos=1),

    # ── Move / Logic on data ──────────────────────────────────────
    "MOV":  OperatorProfile("MOV",  reads=(0,), writes=(1,)),
    "MVM":  OperatorProfile("MVM",  reads=(0, 1), writes=(2,)),
    "COP":  OperatorProfile("COP",  reads=(0, 2), writes=(1,)),
    "CPS":  OperatorProfile("CPS",  reads=(0, 2), writes=(1,)),
    "FLL":  OperatorProfile("FLL",  reads=(0, 2), writes=(1,)),
    "CLR":  OperatorProfile("CLR",  writes=(0,)),
    "BTD":  OperatorProfile("BTD",  reads=(0,), writes=(1,)),
    "AND":  OperatorProfile("AND",  reads=(0, 1), writes=(2,)),
    "OR":   OperatorProfile("OR",   reads=(0, 1), writes=(2,)),
    "XOR":  OperatorProfile("XOR",  reads=(0, 1), writes=(2,)),
    "NOT":  OperatorProfile("NOT",  reads=(0,), writes=(1,)),

    # ── Program flow (sin operandos productivos) ──────────────────
    "JSR":  OperatorProfile("JSR"),  # arg 0 = nombre de routine, no es tag
    "JMP":  OperatorProfile("JMP"),
    "LBL":  OperatorProfile("LBL"),
    "MCR":  OperatorProfile("MCR"),
    "NOP":  OperatorProfile("NOP"),
    "AFI":  OperatorProfile("AFI"),
    "TND":  OperatorProfile("TND"),
    "RET":  OperatorProfile("RET"),
    "SBR":  OperatorProfile("SBR"),
    "UID":  OperatorProfile("UID"),
    "UIE":  OperatorProfile("UIE"),

    # ── Motion (axis = arg 0; master/motion_control donde aplique) ──
    # Cubrimos los args con tags productivos. Args con enums/units/
    # numbers se ignoran — refinable si emerge necesidad.
    "MAJ":  OperatorProfile("MAJ",  writes=(0, 1), reads=(2, 3)),
    "MAS":  OperatorProfile("MAS",  writes=(0, 1)),
    "MAG":  OperatorProfile("MAG",  writes=(0, 2), reads=(1, 3, 4)),
    "MAH":  OperatorProfile("MAH",  writes=(0, 1)),
    "MAM":  OperatorProfile("MAM",  writes=(0, 1), reads=(2, 3)),
    "MAW":  OperatorProfile("MAW",  writes=(0, 1)),
    "MDW":  OperatorProfile("MDW",  writes=(0, 1)),
    "MAOC": OperatorProfile("MAOC", writes=(0, 1)),
    "MAPC": OperatorProfile("MAPC", writes=(0, 1)),
    "MATC": OperatorProfile("MATC", writes=(0, 1)),
    "MAT":  OperatorProfile("MAT",  writes=(0, 1)),
    "MASR": OperatorProfile("MASR", writes=(0, 1)),
    "MCD":  OperatorProfile("MCD",  writes=(0, 1)),
    "MAFR": OperatorProfile("MAFR", writes=(0, 1)),
    "MGS":  OperatorProfile("MGS"),
    "MGSD": OperatorProfile("MGSD"),
    "MGSR": OperatorProfile("MGSR"),
    "MGSP": OperatorProfile("MGSP"),
    "MSF":  OperatorProfile("MSF",  writes=(0, 1)),
    "MSO":  OperatorProfile("MSO",  writes=(0, 1)),
    "MDF":  OperatorProfile("MDF",  writes=(0, 1)),
    "MDO":  OperatorProfile("MDO",  writes=(0, 1)),
    "MDR":  OperatorProfile("MDR",  writes=(0, 1)),
    "MDS":  OperatorProfile("MDS",  writes=(0, 1)),
    "MDOC": OperatorProfile("MDOC", writes=(0, 1)),
    "MCCP": OperatorProfile("MCCP", writes=(0, 1)),
    "MCSV": OperatorProfile("MCSV", writes=(0, 1)),

    # ── File / Array ──────────────────────────────────────────────
    "BSL":  OperatorProfile("BSL",  writes=(0,)),
    "BSR":  OperatorProfile("BSR",  writes=(0,)),
    "FFL":  OperatorProfile("FFL",  writes=(0,)),
    "FFU":  OperatorProfile("FFU",  writes=(0,)),
    "LFL":  OperatorProfile("LFL",  writes=(0,)),
    "LFU":  OperatorProfile("LFU",  writes=(0,)),

    # ── System / Mensajería ────────────────────────────────────────
    # GSV(class, instance, attr, dest) — class/attr son strings, instance
    # puede ser tag o constante; dest = write
    "GSV":  OperatorProfile("GSV",  writes=(3,)),
    # SSV(class, instance, attr, src) — src = read
    "SSV":  OperatorProfile("SSV",  reads=(3,)),
    "MSG":  OperatorProfile("MSG",  writes=(0,)),
    "CIP":  OperatorProfile("CIP"),
    "MRP":  OperatorProfile("MRP"),
}


# ──────────────────────────────────────────────────────────────────────
# Listas negras: enums y funciones que el tokenizer clasificó como tag
# pero semánticamente son literales.
# ──────────────────────────────────────────────────────────────────────


_RLL_ENUMS: set[str] = {
    # Booleanos / on-off
    "ON", "OFF", "Yes", "No", "OK",
    # Modos de motion
    "Command", "Real", "Disabled", "Enabled",
    "Position", "Velocity", "Gear", "All",
    "Forward", "Reverse",
    "Programmed", "Continuous", "Single", "Pulse",
    "Trapezoidal", "S-Curve",
    "Immediate", "Conditional",
    # Otros
    "None", "Decimal", "Hex", "Binary", "Octal", "ASCII",
}


_CPT_FUNCTIONS: set[str] = {
    "SIN", "COS", "TAN", "ASN", "ACS", "ATN",
    "SQRT", "LN", "LOG", "EXP",
    "ABS", "NEG", "NOT", "TRN", "FRD", "TOD",
    "MIN", "MAX", "AVE",
    "AND", "OR", "XOR",
    "IF",
}


# Regex para extraer identificadores tipo tag dentro de expresiones CPT/CMP.
# Mismo patrón que el tokenizer: nombre + opcional .field, [idx], :port.
_TAG_IN_EXPR_RE = re.compile(r"[A-Za-z_]\w*(?:\.\w+|\[\d+\]|:\w+)*")


# ──────────────────────────────────────────────────────────────────────
# API pública del Paso 2
# ──────────────────────────────────────────────────────────────────────


def classify_operands(
    inst: Instruction,
    project: Optional[Project] = None,
    aoi_index: Optional[dict[str, AOIDetail]] = None,
) -> ClassificationResult:
    """Clasifica los operandos de una instrucción según semántica del operador.

    Tres caminos:
      1. Operador en `OPERATOR_TABLE` → aplicar perfil posicional.
      2. Operador no en tabla pero sí en `project.aois` → tratarlo como
         AOI invocation (mapeo args ↔ visible parameters).
      3. Ninguno de los anteriores → todos los operandos `ignore` y flag
         `unknown_operator=True`.

    `aoi_index` (opcional) es un dict {aoi_name: AOIDetail} pre-computado
    para evitar recorrer `project.aois` en bulk.
    """
    op = inst.operator

    if op in OPERATOR_TABLE:
        return _classify_with_profile(inst, OPERATOR_TABLE[op])

    if project is not None or aoi_index is not None:
        idx = aoi_index if aoi_index is not None else {a.name: a for a in project.aois}
        aoi = idx.get(op)
        if aoi is not None:
            return _classify_aoi_invocation(inst, aoi)

    return ClassificationResult(
        operator=op,
        classified=[ClassifiedOperand(operand=o, usage="ignore") for o in inst.operands],
        unknown_operator=True,
    )


# ──────────────────────────────────────────────────────────────────────
# Implementación
# ──────────────────────────────────────────────────────────────────────


def _classify_with_profile(inst: Instruction, prof: OperatorProfile) -> ClassificationResult:
    usage_by_pos: dict[int, str] = {}
    for pos in prof.reads:
        usage_by_pos[pos] = "read"
    for pos in prof.writes:
        usage_by_pos[pos] = "write"
    for pos in prof.both:
        usage_by_pos[pos] = "both"

    classified: list[ClassifiedOperand] = []
    for i, opd in enumerate(inst.operands):
        usage = usage_by_pos.get(i, "ignore")
        # Recategorizar enums/no-tags a ignore (eran tag por forma, no por semántica)
        if usage != "ignore":
            if opd.kind != "tag" or opd.text in _RLL_ENUMS:
                usage = "ignore"
        classified.append(ClassifiedOperand(operand=opd, usage=usage))

    expr_reads: list[Operand] = []
    if prof.cpt_expr_pos is not None and len(inst.operands) > prof.cpt_expr_pos:
        expr_text = inst.operands[prof.cpt_expr_pos].text
        for tag_text in _extract_tags_from_expression(expr_text):
            expr_reads.append(Operand(text=tag_text, kind="tag"))

    return ClassificationResult(
        operator=inst.operator,
        classified=classified,
        expr_reads=expr_reads,
    )


def _classify_aoi_invocation(inst: Instruction, aoi: AOIDetail) -> ClassificationResult:
    """Clasifica los args de una invocación AOI usando aoi.parameters.

    Convención de Studio 5000:
      - arg[0] del invoke = backing tag (instance data del AOI). El AOI
        actualiza esa estructura cada scan → `write`.
      - arg[1..] mapean posicionalmente a los parameters `visible=True`
        del AOI (los invisible — EnableIn/EnableOut, counters auto, etc. —
        no aparecen en el invoke).
      - `Parameter.usage` Input → read, Output → write, InOut → both.
    """
    classified: list[ClassifiedOperand] = []
    visible_params = [p for p in aoi.parameters if p.visible]

    if inst.operands:
        backing = inst.operands[0]
        usage = "write" if backing.kind == "tag" else "ignore"
        classified.append(ClassifiedOperand(operand=backing, usage=usage))

    for i, opd in enumerate(inst.operands[1:]):
        if i >= len(visible_params):
            classified.append(ClassifiedOperand(operand=opd, usage="ignore"))
            continue
        usage = _param_usage_to_kind(visible_params[i].usage)
        if opd.kind != "tag" or opd.text in _RLL_ENUMS:
            usage = "ignore"
        classified.append(ClassifiedOperand(operand=opd, usage=usage))

    return ClassificationResult(operator=inst.operator, classified=classified)


def _param_usage_to_kind(param_usage: str) -> str:
    u = (param_usage or "").lower()
    if u == "input":
        return "read"
    if u == "output":
        return "write"
    if u == "inout":
        return "both"
    return "ignore"


def _extract_tags_from_expression(expr: str) -> list[str]:
    """Extrae identificadores tipo tag de una expresión CPT/CMP, en orden de
    aparición y deduplicados.

    Filtra funciones conocidas (SIN, SQRT, IF, etc.) y enums.
    """
    found: list[str] = []
    seen: set[str] = set()
    for m in _TAG_IN_EXPR_RE.finditer(expr):
        text = m.group(0)
        if text in _CPT_FUNCTIONS or text in _RLL_ENUMS:
            continue
        if text in seen:
            continue
        seen.add(text)
        found.append(text)
    return found


# ──────────────────────────────────────────────────────────────────────
# Paso 3 — build_xref: poblar la tabla SQLite con todas las referencias
# ──────────────────────────────────────────────────────────────────────


import sqlite3 as _sqlite3  # noqa: E402  (import al final por organización)
from .model import init_db as _init_db  # noqa: E402
from .tokenizer import tokenize_rll as _tokenize_rll  # noqa: E402


def build_xref(project: Project, conn: Optional[_sqlite3.Connection] = None) -> int:
    """Recorre todo el código RLL del proyecto, clasifica los operandos de cada
    instrucción y persiste las referencias en la tabla `xref` de SQLite.

    Idempotente: trunca `xref` antes de poblarla. La construcción es batch
    (una sola transacción), así que se puede llamar múltiples veces sin
    acumular duplicados.

    Para tags estructurados (`M3Data.Input.X`, `BIT2.31`, `AxA[3].DN`,
    `DEBO_TNT:0:I.1`) se generan DOS rows: una con el path completo
    (operand_kind=`tag`) y otra sintética con el root (operand_kind=`tag_root`).
    Eso permite que `writers_of("M3Data")` encuentre tanto writes directos a
    `M3Data` como a cualquier subfield.

    Args:
        project: Project ya cargado con load_project().
        conn: conexión SQLite opcional. Si no se pasa, se abre/crea contra
            project.db_path.

    Returns:
        Número de rows insertadas en xref.
    """
    own_conn = conn is None
    if own_conn:
        if not project.db_path:
            raise ValueError(
                "Project no tiene db_path; build_xref necesita una base SQLite. "
                "Pasa una conexión explícita vía el argumento conn."
            )
        conn = _init_db(project.db_path)

    cur = conn.cursor()
    # Defensive: drop+recreate xref para garantizar que la tabla tiene el schema
    # actual aunque el SQLite preexista con un schema más viejo (CREATE TABLE
    # IF NOT EXISTS no altera tablas existentes).
    cur.execute("DROP TABLE IF EXISTS xref")
    cur.executescript(_XREF_TABLE_SQL)

    aoi_idx = {a.name: a for a in project.aois}
    rows: list[tuple] = []

    # Routines de programas
    for r in project.routines:
        if not r.code or r.type != "RLL":
            continue
        for rung in _tokenize_rll(r.code):
            loc = f"Programs/{r.program}/Routines/{r.name}/Rung_{rung.number}"
            for inst_idx, inst in enumerate(rung.instructions):
                rows.extend(_xref_rows_from_instruction(inst, loc, inst_idx, project, aoi_idx))

    # Routines de AOIs
    for a in project.aois:
        for rname, r in a.routines.items():
            if not r.code or r.type != "RLL":
                continue
            for rung in _tokenize_rll(r.code):
                loc = f"AOIs/{a.name}/Routines/{rname}/Rung_{rung.number}"
                for inst_idx, inst in enumerate(rung.instructions):
                    rows.extend(_xref_rows_from_instruction(inst, loc, inst_idx, project, aoi_idx))

    cur.executemany(
        "INSERT INTO xref(source_kind, source_location, operand, operand_kind, "
        "usage, operator, instruction_index) VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    if own_conn:
        # No cerramos la conexión: el caller (típicamente el método de Project)
        # puede querer hacer queries inmediatamente. SQLite cierra cuando GC.
        pass
    return len(rows)


def _xref_rows_from_instruction(
    inst: Instruction,
    location: str,
    instruction_index: int,
    project: Project,
    aoi_idx: dict[str, AOIDetail],
) -> list[tuple]:
    """Genera las xref rows para una instrucción.

    `instruction_index` es la posición 0-based de la instrucción dentro del
    rung; permite distinguir reads/writes de instrucciones distintas en el
    mismo rung (granularidad por-instrucción del Paso 5b.1).

    Para cada operando con `usage != "ignore"` y `kind == "tag"`:
      - 1 row con el operando completo (operand_kind="tag")
      - 1 row adicional con el root del tag (operand_kind="tag_root") si el
        operando es estructurado.

    Para tags extraídos de expresiones CPT/CMP: rows con usage="read",
    operator=el de la instrucción (CPT/CMP).
    """
    res = classify_operands(inst, project=project, aoi_index=aoi_idx)
    rows: list[tuple] = []

    for co in res.classified:
        if co.usage == "ignore":
            continue
        if co.operand.kind != "tag":
            continue
        rows.append(("rung", location, co.operand.text, "tag", co.usage, inst.operator, instruction_index))
        root = _tag_root(co.operand.text)
        if root and root != co.operand.text:
            rows.append(("rung", location, root, "tag_root", co.usage, inst.operator, instruction_index))

    for opd in res.expr_reads:
        rows.append(("rung", location, opd.text, "tag", "read", inst.operator, instruction_index))
        root = _tag_root(opd.text)
        if root and root != opd.text:
            rows.append(("rung", location, root, "tag_root", "read", inst.operator, instruction_index))

    return rows


# DDL canónico de la tabla xref. Usado tanto por init_db (vía SCHEMA_SQL en
# model.py) como por build_xref para drop+recreate defensivo.
_XREF_TABLE_SQL = """
CREATE TABLE xref (
    source_kind        TEXT,
    source_location    TEXT,
    operand            TEXT,
    operand_kind       TEXT,
    usage              TEXT,
    operator           TEXT,
    instruction_index  INTEGER
);
CREATE INDEX idx_xref_operand     ON xref(operand);
CREATE INDEX idx_xref_source      ON xref(source_location);
CREATE INDEX idx_xref_operator    ON xref(operator);
CREATE INDEX idx_xref_instruction ON xref(source_location, instruction_index);
"""


def _tag_root(tag_text: str) -> str:
    """Devuelve el root de un tag estructurado.

    Ejemplos:
        'M3Data.Input.Dancer.Position' → 'M3Data'
        'BIT2.31'                      → 'BIT2'
        'AxA[3].DN'                    → 'AxA'
        'DEBO_TNT:0:I.1'               → 'DEBO_TNT'
        'simple_tag'                   → 'simple_tag'
    """
    out = tag_text
    for sep in (".", "[", ":"):
        idx = out.find(sep)
        if idx >= 0:
            out = out[:idx]
    return out
