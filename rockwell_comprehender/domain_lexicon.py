"""Domain Lexicon — síntoma → código (criterio v0.3).

Capa de v0.3 (DT-009). Esta capa NO extrae datos del L5X; mapea
**síntomas en lenguaje natural** (queries del operador/ingeniero) a
**identifiers concretos** del proyecto (AOIs, routines, programs)
mediante un lexicón curado de keywords técnicos + heurística de
confidence scoring.

Cierra el criterio v0.3 documentado en `docs/00_Vision_y_Roadmap.md`
sec 8: "Sin guía manual, identifico que el caso de empalme involucra
dominio splice + unwinder. Genero la cadena causal en 1-2 turnos con
confianza alta."

Uso:
    from rockwell_comprehender import load_project
    project = load_project("parque_l5x/CINTA_LAMINADA_M2_2024.L5X")
    hits = project.identify_domain("problema en empalme")
    for h in hits[:5]:
        print(f"{h.confidence:.2f}  {h.target_kind:8s}  {h.target_name}")
        print(f"        keywords: {h.match_keywords}")

Diseño:
- `SYMPTOM_LEXICON`: mapeo síntoma → keywords primarios (matches directos
  de alta señal). Ej: "empalme" → ["splice", "splicer", "ctc"].
- `RELATED_KEYWORDS`: mapeo síntoma → keywords secundarios (asociaciones
  contextuales del dominio). Ej: "empalme" → ["unwind", "dancer", "radius"]
  porque el empalme involucra el debobinador y el cálculo de radio del
  rollo aunque sintácticamente NO contenga "splice".
- Scoring: confidence = base (0.5 primary / 0.4 only-related) + bonus por
  cantidad de matches + bonus si target es AOI + bonus si keyword
  aparece al inicio del name (post strip de prefijos AHT_/CTC_).

Stack mínimo (DT-008): solo `re` + estructuras del modelo. Sin embeddings,
sin LLM externo, sin frameworks ML. La heurística es honesta y debuggable
— cuando aparezca un caso real que la rompa, se refina la tabla.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Lexicón síntoma → keywords técnicos
# ──────────────────────────────────────────────────────────────────────


# Mapeo síntoma (en español o inglés, lowercase) → lista de keywords
# técnicos a buscar (lowercase, substring match en identifier names).
SYMPTOM_LEXICON: dict[str, list[str]] = {
    # Empalme / continuous splice
    "empalme":      ["splice", "splicer", "ctc"],
    "splice":       ["splice", "splicer", "ctc"],
    "splicer":      ["splice", "splicer", "ctc"],
    # Debobinador
    "debobinador":  ["unwind", "unwinder", "uwm"],
    "unwinder":     ["unwind", "unwinder", "uwm"],
    "unwind":       ["unwind", "unwinder", "uwm"],
    # Rebobinador
    "rebobinador":  ["rewind", "rewinder", "rwm"],
    "rewinder":     ["rewind", "rewinder", "rwm"],
    # Tensión / dancer
    "tension":      ["tension", "tnt", "dancer"],
    "tensión":      ["tension", "tnt", "dancer"],
    "danzarin":     ["dancer", "dnc"],
    "danzarín":     ["dancer", "dnc"],
    "dancer":       ["dancer", "dnc"],
    # Rollo / radio / diámetro
    "rollo":        ["roll", "radius", "diameter"],
    "diametro":     ["radius", "diameter"],
    "diámetro":     ["radius", "diameter"],
    "radius":       ["radius", "diameter"],
    # Velocidad
    "velocidad":    ["speed", "velocity", "vel"],
    "speed":        ["speed", "velocity", "vel"],
    # Fallos / alarmas
    "fault":        ["fault", "alarm", "error", "decoding"],
    "falla":        ["fault", "alarm", "error", "decoding"],
    "alarma":       ["alarm", "fault"],
    # Drive / motor
    "drive":        ["drive", "motor", "kinetix"],
    "motor":        ["drive", "motor", "kinetix"],
    "servo":        ["servo", "drive", "kinetix"],
    # Safety / E-stop
    "safety":       ["safety", "estop", "guard", "dcs"],
    "seguridad":    ["safety", "estop", "guard", "dcs"],
    "estop":        ["estop", "safety"],
    "e-stop":       ["estop", "safety"],
    "guarda":       ["guard", "safety"],
    "lock":         ["lock", "safety"],
    # Homing / jog / motion
    "homing":       ["home", "homing", "mah"],
    "home":         ["home", "homing", "mah"],
    "jog":          ["jog", "maj"],
    # Sincronización
    "sincro":       ["sync", "syncro", "gear", "mag"],
    "sincronización": ["sync", "syncro", "gear", "mag"],
    # Tasks / programs
    "scheduling":   ["task", "scheduling"],
    "tarea":        ["task", "scheduling"],
    # HMI
    "hmi":          ["hmi", "operator"],
    "pantalla":     ["hmi", "operator"],
    # Reject / rechazo
    "reject":       ["reject", "rej", "cull"],
    "rechazo":      ["reject", "rej", "cull"],
}


# Para síntomas con asociaciones contextuales: keywords adicionales que
# NO son sintácticamente parte del síntoma pero pertenecen al mismo
# dominio funcional. Ej: empalme técnicamente es splice, pero involucra
# el unwinder y el dancer (calculan velocidad inicial del nuevo rollo).
RELATED_KEYWORDS: dict[str, list[str]] = {
    "empalme":      ["unwind", "unwinder", "dancer", "radius", "computation", "newradius"],
    "splice":       ["unwind", "unwinder", "dancer", "radius", "computation", "newradius"],
    "splicer":      ["unwind", "unwinder", "dancer", "radius", "computation", "newradius"],
    "debobinador":  ["splice", "splicer", "dancer", "radius"],
    "unwinder":     ["splice", "splicer", "dancer", "radius"],
    "tension":      ["dancer", "drive", "speed"],
    "tensión":      ["dancer", "drive", "speed"],
    "rollo":        ["unwind", "rewind", "splice"],
    "fault":        ["drive", "motor", "axis"],
    "falla":        ["drive", "motor", "axis"],
    "drive":        ["fault", "motor", "axis"],
    "motor":        ["fault", "drive", "axis"],
    "safety":       ["fault", "alarm", "estop"],
    "seguridad":    ["fault", "alarm", "estop"],
    "homing":       ["axis", "motion"],
    "home":         ["axis", "motion"],
    "sincro":       ["axis", "motion", "master", "slave"],
    "sincronización": ["axis", "motion", "master", "slave"],
}


# Prefijos comunes en identifiers Rockwell que se strippean para detectar
# si una palabra clave aparece al "inicio efectivo" del name. AHT_ es
# convención de algunos integradores; CTC_ es continuous-tape-control;
# DCI_ y DCS_ son safety dual-channel.
_NAME_PREFIX_RE = re.compile(r"^(aht_|ctc_|dci_|dcs_|udt_|tag_|aoi_)+", re.IGNORECASE)


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class DomainHit:
    """Match de un identifier del proyecto contra una query de dominio."""

    target_kind: str          # "aoi" | "routine" | "tag" | "program"
    target_name: str
    confidence: float         # 0.0–1.0
    match_keywords: list[str] # keywords (primary + related) que matchearon
    location: str             # path canónico (Programs/X/Routines/Y, AOIs/Z)
    primary_count: int = 0    # count de keywords primarios matched
    related_count: int = 0    # count de keywords related matched

    def __repr__(self) -> str:
        return (
            f"DomainHit({self.target_kind} {self.target_name!r} "
            f"conf={self.confidence:.2f} kw={self.match_keywords})"
        )


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def identify_domain(project: "Project", query: str) -> list[DomainHit]:
    """Identifica AOIs/routines/programs/tags relacionados con un síntoma.

    Algoritmo:
      1. Normaliza query a lowercase y extrae keywords primarios + related
         del lexicón.
      2. Para cada AOI / routine / program del proyecto: cuenta matches de
         keywords primarios y related en el name (lowercase, substring).
      3. Computa confidence via `_score()` con bonus por kind, cantidad de
         matches, y posición inicial del keyword.
      4. Devuelve hits con confidence > 0, ordenados desc por confidence.

    Args:
        project: Project ya cargado.
        query: Síntoma en lenguaje natural ("problema en empalme",
            "falla del unwinder", "no responde el dancer").

    Returns:
        Lista de `DomainHit` ordenada por confidence desc. Vacía si la
        query no tiene matches en el lexicón.
    """
    query_lower = query.lower()
    primary_keywords: set[str] = set()
    related_keywords: set[str] = set()

    for symptom, techs in SYMPTOM_LEXICON.items():
        if symptom in query_lower:
            primary_keywords.update(techs)
            related_keywords.update(RELATED_KEYWORDS.get(symptom, []))

    if not primary_keywords:
        return []

    # Quitar overlap: si un keyword está en primary, no cuenta como related.
    related_keywords -= primary_keywords

    hits: list[DomainHit] = []

    # AOIs (peso máximo — son las unidades funcionales encapsuladas)
    for aoi in project.aois:
        hit = _score_target(
            name=aoi.name,
            target_kind="aoi",
            location=f"AOIs/{aoi.name}",
            primary_keywords=primary_keywords,
            related_keywords=related_keywords,
            kind_bonus=0.2,
        )
        if hit:
            hits.append(hit)

    # Routines
    for r in project.routines:
        loc = f"Programs/{r.program}/Routines/{r.name}" if r.program else f"Routines/{r.name}"
        hit = _score_target(
            name=r.name,
            target_kind="routine",
            location=loc,
            primary_keywords=primary_keywords,
            related_keywords=related_keywords,
            kind_bonus=0.0,
        )
        if hit:
            hits.append(hit)

    # Programs
    for p in project.programs:
        hit = _score_target(
            name=p.name,
            target_kind="program",
            location=f"Programs/{p.name}",
            primary_keywords=primary_keywords,
            related_keywords=related_keywords,
            kind_bonus=0.1,
        )
        if hit:
            hits.append(hit)

    hits.sort(key=lambda h: (-h.confidence, h.target_name))
    return hits


# ──────────────────────────────────────────────────────────────────────
# Implementación
# ──────────────────────────────────────────────────────────────────────


def _score_target(
    name: str,
    target_kind: str,
    location: str,
    primary_keywords: set[str],
    related_keywords: set[str],
    kind_bonus: float,
) -> DomainHit | None:
    """Calcula confidence para un target dado y emite DomainHit si match.

    Confidence model (heurística honesta, ajustable):
      - base = 0.5 si hay matches primarios; 0.4 si solo related.
      - bonus_count = min(0.3, 0.1*(n_primary-1) + 0.05*n_related)
        — recompensa densidad de matches sin saturarse.
      - kind_bonus = 0.2 (AOI), 0.1 (program), 0.0 (routine).
      - bonus_pos = 0.1 si algún keyword primary aparece al inicio del
        name (post strip de prefijos AHT_/CTC_/etc.).
      - cap a 1.0.
    """
    name_lower = name.lower()

    primary_matches = [k for k in primary_keywords if k in name_lower]
    related_matches = [k for k in related_keywords if k in name_lower]

    if not primary_matches and not related_matches:
        return None

    # Base
    if primary_matches:
        base = 0.5
    else:
        base = 0.4

    # Bonus by count
    n_primary = len(primary_matches)
    n_related = len(related_matches)
    bonus_count = min(0.3, 0.1 * max(0, n_primary - 1) + 0.05 * n_related)

    # Bonus position (primary keyword at start of stripped name)
    stripped = _NAME_PREFIX_RE.sub("", name_lower)
    bonus_pos = 0.0
    for k in primary_matches:
        if stripped.startswith(k):
            bonus_pos = 0.1
            break

    confidence = min(1.0, base + bonus_count + kind_bonus + bonus_pos)

    return DomainHit(
        target_kind=target_kind,
        target_name=name,
        confidence=round(confidence, 3),
        match_keywords=sorted(set(primary_matches + related_matches)),
        location=location,
        primary_count=n_primary,
        related_count=n_related,
    )
