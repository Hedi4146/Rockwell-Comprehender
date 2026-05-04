"""st_tokenizer.py — Tokenizer de Structured Text (ST) para Studio 5000.

ST en Logix puede contener:
- Assignments: ``lhs := rhs ;``
- Function calls: ``MAJ(...)``, ``MAS(...)``, ``MOV(...)``, AOI invocations
- Control flow: IF/THEN/ELSE/END_IF, FOR/DO/END_FOR, WHILE/END_WHILE, CASE/OF/END_CASE
- Comments: ``(* block *)`` y ``// line``

Para el tracer (que necesita operandos read/write), lo importante es:

1. **Function calls** (motion, AOI invocations) → ``Instruction(operator=name, operands=args)``
2. **Assignments** → ``Instruction(operator=":=", operands=[lhs, rhs])``

Control flow keywords (IF/THEN/FOR/WHILE/...) se ignoran como tokens —
sus condiciones quedan como parte del RHS de assignments adyacentes o
no se extraen (el v0.3 valor está en function calls + asignaciones, no
en condicionales).

El loader v0.1+ inyecta line-number prefixes a la code de routines ST
(formato ``N: \\n<content>``); este tokenizer los elimina al preprocesar.

Reusa la API de tokenize_rll: devuelve ``list[Rung]`` con UNA Rung
(number=0) que contiene todas las instrucciones del routine.
"""

from __future__ import annotations

import re

from .rll_tokenizer import (
    Instruction,
    Operand,
    Rung,
    _find_matching_paren,
    _IDENT_RE,
    _parse_operands,
)


# ─────────────────────────────────────────────────────────────────────────
# Patrones de pre-procesamiento
# ─────────────────────────────────────────────────────────────────────────


# Line-number prefixes inyectados por el loader: "0:\n", "12: \n", etc.
# Los eliminamos para que el parser vea ST limpio.
_LINE_NUM_RE = re.compile(r"^\s*\d+:\s*$", re.MULTILINE)

# Block comment ST: (* ... *), puede ser multi-línea.
_BLOCK_COMMENT_RE = re.compile(r"\(\*.*?\*\)", re.DOTALL)

# Line comment ST: // hasta fin de línea.
_LINE_COMMENT_RE = re.compile(r"//[^\n]*")

# Assignment statement: lhs := rhs ;
# lhs puede tener .field, [idx], :port (estructurado)
# rhs puede contener cualquier expresión (incluyendo function calls — se
# extraen separado en el segundo pase).
_ASSIGN_RE = re.compile(
    r"([A-Za-z_][\w.\[\]:]*)\s*:=\s*([^;]+?);",
    re.DOTALL,
)


# Keywords ST que NO son function calls (defensive).
_ST_KEYWORDS = frozenset([
    "IF", "THEN", "ELSE", "ELSIF", "END_IF",
    "FOR", "TO", "BY", "DO", "END_FOR",
    "WHILE", "END_WHILE",
    "REPEAT", "UNTIL", "END_REPEAT",
    "CASE", "OF", "END_CASE",
    "RETURN", "EXIT",
    "AND", "OR", "NOT", "XOR", "MOD",
    "TRUE", "FALSE",
])


# ─────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────


def tokenize_st(code: str) -> list[Rung]:
    """Tokeniza ST en una lista con UNA Rung (number=0) conteniendo todas
    las instrucciones extraíbles.

    Devuelve lista vacía si ``code`` está vacío o no tiene contenido tras
    pre-procesamiento.

    Tipos de instrucciones extraídas:
    - ``operator=":="`` → assignment, operands=[lhs, rhs_text]
    - ``operator=<name>`` → function call (motion, AOI, MOV, MSG, etc.),
      operands = parsed args
    """
    if not code or not code.strip():
        return []

    cleaned = _preprocess(code)
    if not cleaned.strip():
        return []

    instructions: list[Instruction] = []

    # 1. Assignments: lhs := rhs ;
    # Capturamos primero las asignaciones; el rhs puede contener function
    # calls que también capturaremos en el siguiente pase (no es un problema
    # — el tracer ve ambas perspectivas).
    for m in _ASSIGN_RE.finditer(cleaned):
        lhs = m.group(1).strip()
        rhs = m.group(2).strip()
        instructions.append(
            Instruction(
                operator=":=",
                operands=[
                    Operand(text=lhs, kind="tag"),
                    Operand(text=rhs, kind="literal"),
                ],
                raw_text=m.group(0),
            )
        )

    # 2. Function calls (anywhere)
    instructions.extend(_extract_function_calls(cleaned))

    return [Rung(number=0, comment="", instructions=instructions, raw_text=cleaned)]


# ─────────────────────────────────────────────────────────────────────────
# Implementación
# ─────────────────────────────────────────────────────────────────────────


def _preprocess(code: str) -> str:
    """Pre-procesa ST: elimina line-num prefixes del loader, strip comments.

    Orden importante:
    1. Block comments primero (pueden contener //, no queremos confundir).
    2. Line comments después.
    3. Line-number prefixes al final (algunos están dentro de comments).
    """
    code = _BLOCK_COMMENT_RE.sub(" ", code)
    code = _LINE_COMMENT_RE.sub("", code)
    code = _LINE_NUM_RE.sub("", code)
    return code


def _extract_function_calls(text: str) -> list[Instruction]:
    """Extrae llamadas IDENT(args) que aparezcan en cualquier nivel del ST.

    Reusa la lógica de RLL para mantener consistencia. Filtra ST keywords
    (IF, FOR, AND, etc.) que técnicamente podrían matchear el patrón pero
    no son function calls reales.
    """
    instructions: list[Instruction] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\n\r,;[]:":
            i += 1
            continue
        m = _IDENT_RE.match(text, i)
        if not m:
            i += 1
            continue
        ident = m.group(0)
        end_ident = m.end()
        # Skip ST keywords sin importar lo que sigue
        if ident.upper() in _ST_KEYWORDS:
            i = end_ident
            continue
        # Tolerar whitespace entre identificador y '('
        j = end_ident
        while j < n and text[j] in " \t":
            j += 1
        if j < n and text[j] == "(":
            close_idx = _find_matching_paren(text, j)
            if close_idx < 0:
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
            i = end_ident
    return instructions
