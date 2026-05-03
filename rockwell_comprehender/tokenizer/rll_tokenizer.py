"""Tokenizer de RLL (Relay Ladder Logic) para Rockwell Studio 5000 / RSLogix 5000.

Convierte el `code` de una rutina RLL (string monolítico tal como viene del L5X)
en una estructura jerárquica `Rung → Instruction → Operand`.

Diseño:
- **Robusto a garbage:** chars desconocidos, decoración (`─`, comentarios
  multi-línea sin `//`, texto suelto) se saltan sin abortar el parseo del
  resto del rung.
- **No-opinionated sobre semántica:** este módulo NO clasifica operandos como
  read/write. Eso es trabajo del Paso 2 (tabla de semántica de operadores en
  tracer.py), que tiene contexto del operador y de las firmas de AOI.
- **Aplana branches:** los brackets `[...]` y comas dentro de un rung son
  delimitadores estructurales (branches paralelos / serie). Para el tracer,
  todas las instrucciones del rung tienen la misma semántica de operandos
  independientemente del bracket — así que se aplanan.
- **Tags estructurados** como `M3Data.Input.Dancer.Position` o `BIT2.31` o
  `DEBO_TNT:0:I.1` se preservan como UN operando con kind="tag". El indexer
  del Paso 3 decide si también indexa el root (`M3Data`) por separado.
- **Clasificación superficial de operandos:**
    - `constant` → numérico (`-?d+(.d+)?(e±d+)?`)
    - `tag`      → identificador con opcional `.field`, `[idx]`, `:port`
    - `literal`  → todo lo demás (multi-word, enums, símbolos)
  El Paso 2 puede recategorizar en función de la posición (ej. arg 8 de MAG
  es un enum aunque parezca tag).

Uso:
    from rockwell_comprehender.tokenizer import tokenize_rll
    rungs = tokenize_rll(routine.code)
    for r in rungs:
        print(f"Rung {r.number}: {len(r.instructions)} instrucciones")
        for inst in r.instructions:
            print(f"  {inst.operator}({', '.join(o.text for o in inst.operands)})")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────
# Estructuras de salida
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Operand:
    """Operando individual dentro de una instrucción."""

    text: str            # texto crudo tal como aparece (ej. "M3Data.Input.X")
    kind: str            # "tag" | "constant" | "literal"


@dataclass
class Instruction:
    """Una instrucción RLL (operador + sus operandos)."""

    operator: str        # ej. "XIC", "MOV", "AHT_CtcSplicer"
    operands: list[Operand] = field(default_factory=list)
    raw_text: str = ""   # ej. "OTE(StartMachine)" — útil para debug/snippets


@dataclass
class Rung:
    """Un rung del routine."""

    number: int                                      # del marcador // Rung N
    comment: str = ""                                # texto después de "// Rung N" en la misma línea
    instructions: list[Instruction] = field(default_factory=list)
    raw_text: str = ""                               # texto completo del rung (para snippets)


# ─────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────


def tokenize_rll(code: str) -> list[Rung]:
    """Tokeniza un bloque de código RLL en una lista de Rungs.

    Si `code` no tiene marcadores `// Rung N`, todo el contenido se trata
    como un único Rung 0.
    """
    if not code or not code.strip():
        return []
    rung_specs = _split_rungs(code)
    return [_tokenize_rung(num, comment, body) for num, comment, body in rung_specs]


# ─────────────────────────────────────────────────────────────────────────
# Implementación
# ─────────────────────────────────────────────────────────────────────────


# Header de un rung. Captura el número y deja el resto de la línea como
# comentario opcional. Soporta variantes como "// Rung 3:" o "// Rung 3: notas".
_RUNG_HEADER_RE = re.compile(r"^//\s*Rung\s+(\d+)([^\n]*)\n", re.MULTILINE)

# Identificador estilo Python: letras/underscore + alfanumérico/underscore.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Numérico: entero o flotante (con notación científica opcional).
_NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")

# Tag estructurado: <name>(\.<field> | \[<idx>\] | :<port>)*
# - Cubre M3Data.Input.Dancer.Position, BIT2.31, AxA[3].DN,
#   DEBO_TNT:0:I.1, Local:1:I.Data.0
_TAG_RE = re.compile(r"^[A-Za-z_]\w*(?:\.\w+|\[\d+\]|:\w+)*$")


def _split_rungs(code: str) -> list[tuple[int, str, str]]:
    """Divide `code` en rungs según marcadores `// Rung N`.

    Devuelve lista de (rung_number, header_comment, body_text). Si no hay
    marcadores, devuelve [(0, "", code)].
    """
    headers = list(_RUNG_HEADER_RE.finditer(code))
    if not headers:
        body = code.strip().rstrip(";").strip()
        return [(0, "", body)] if body else []
    rungs: list[tuple[int, str, str]] = []
    for i, m in enumerate(headers):
        num = int(m.group(1))
        comment_tail = m.group(2).strip().lstrip(":").strip()
        body_start = m.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(code)
        body = code[body_start:body_end].strip().rstrip(";").strip()
        rungs.append((num, comment_tail, body))
    return rungs


def _tokenize_rung(num: int, comment: str, body: str) -> Rung:
    instructions = _parse_instructions(body)
    return Rung(number=num, comment=comment, instructions=instructions, raw_text=body)


def _parse_instructions(text: str) -> list[Instruction]:
    """Recorre `text` extrayendo todas las llamadas `IDENT(args)` que
    aparezcan en cualquier nivel de bracket. Aplana branches; ignora chars
    de adorno y texto suelto.
    """
    instructions: list[Instruction] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\n\r,;[]":
            i += 1
            continue
        # Comentario de línea embebido (raro fuera del header del rung)
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            nl = text.find("\n", i + 2)
            i = (nl + 1) if nl >= 0 else n
            continue
        m = _IDENT_RE.match(text, i)
        if not m:
            i += 1
            continue
        ident = m.group(0)
        end_ident = m.end()
        # Tolerar whitespace entre identificador y '('
        j = end_ident
        while j < n and text[j] in " \t":
            j += 1
        if j < n and text[j] == "(":
            close_idx = _find_matching_paren(text, j)
            if close_idx < 0:
                # Paren sin cerrar — paramos este rung; los próximos rungs
                # del routine se procesan independientemente
                break
            args_text = text[j + 1:close_idx]
            operands = _parse_operands(args_text)
            instructions.append(
                Instruction(
                    operator=ident,
                    operands=operands,
                    raw_text=text[i:close_idx + 1],
                )
            )
            i = close_idx + 1
        else:
            # Identificador suelto (label, fragmento de comentario, enum, etc.)
            i = end_ident
    return instructions


def _find_matching_paren(text: str, open_idx: int) -> int:
    """Encuentra el índice del ')' que cierra al '(' en `open_idx`. -1 si no hay."""
    if open_idx >= len(text) or text[open_idx] != "(":
        return -1
    depth = 1
    i = open_idx + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _parse_operands(args_text: str) -> list[Operand]:
    """Divide `args_text` por comas top-level y clasifica cada operando."""
    if not args_text.strip():
        return []
    operands: list[Operand] = []
    for raw in _split_top_level(args_text):
        text = raw.strip()
        if not text:
            continue
        operands.append(Operand(text=text, kind=_classify_operand(text)))
    return operands


def _split_top_level(s: str) -> list[str]:
    """Divide `s` por comas a depth 0 (no dentro de parens o brackets)."""
    parts: list[str] = []
    start = 0
    depth = 0
    for i, c in enumerate(s):
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
            if depth < 0:
                depth = 0  # tolerar desbalances
        elif c == "," and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _classify_operand(text: str) -> str:
    """Clasificación superficial. El Paso 2 (tracer) puede recategorizar
    según contexto del operador.
    """
    if not text:
        return "literal"
    # String entre comillas
    if (text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'"):
        return "literal"
    if _NUMERIC_RE.match(text):
        return "constant"
    if _TAG_RE.match(text):
        return "tag"
    return "literal"
