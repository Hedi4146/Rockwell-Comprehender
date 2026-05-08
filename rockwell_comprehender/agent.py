"""Agent — orquestador determinístico (v0.7).

Convierte el toolkit de "biblioteca de capacidades pasivas" a "agente
de comportamiento reproducible y auditable" SIN agregar LLM
(DT-008/DT-003). El cerebro sigue siendo Claude cuando se usa vía
Claude Code; este módulo entrega un comportamiento determinístico para
las preguntas más comunes que se pueden resolver mecánicamente.

**Filosofía:**
- Una pregunta en lenguaje natural → secuencia de llamadas al toolkit →
  respuesta consolidada.
- Determinístico: misma `(project, question)` ⇒ mismo `AgentResponse`.
- Auditable: cada call queda registrado en `tools_called` con args y
  output summary.
- Honestidad técnica: si la heurística no reconoce la pregunta,
  retorna `confidence=0` con sugerencia de delegar a Claude. NO inventa.

**Patrones de pregunta soportados:**
- `splice_diagnosis`: "problema en empalme", "splice issue"
- `unwinder_diagnosis`: "falla del debobinador", "unwinder problem"
- `dancer_diagnosis`: "problema con dancer", "tensión"
- `dead_code_audit`: "código muerto", "tags huérfanos"
- `motion_overview`: "qué hace el motion", "ejes del proyecto"
- `safety_overview`: "estado safety", "guardlogix"
- `smell_audit`: "smells", "best practices", "auditar"
- `tag_explain`: "qué es <tag>", "para qué sirve <tag>"
- `aoi_explain`: "qué hace <AOI>"
- `program_explain`: "qué hace el program <X>"
- `general_health`: "estado general", "audit completo"
- `compare_projects`: requiere 2 projects (no soportado en single-project agent)

**Lo que NO hace** (intencional, DT-008):
- No interpreta lenguaje natural complejo (eso requiere LLM)
- No mantiene memoria entre invocaciones (cada `ask` es stateless)
- No genera respuestas creativas — solo combina outputs estructurados
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .model import Project


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class ToolCall:
    """Registro de una llamada al toolkit dentro del agent."""

    api: str                   # "identify_domain", "detect_smells", ...
    args_summary: str          # representación corta de los args
    output_summary: str        # qué devolvió, en breve
    output_size: int = 0       # items count o chars

    def __repr__(self) -> str:
        return f"ToolCall({self.api}({self.args_summary}) -> {self.output_summary})"


@dataclass
class AgentResponse:
    """Respuesta determinística del agente a una pregunta."""

    question: str
    pattern: str                                # patrón reconocido (ej. "splice_diagnosis")
    answer: str                                 # respuesta consolidada (markdown)
    evidence: list[Any] = field(default_factory=list)   # objetos del toolkit que respaldan
    tools_called: list[ToolCall] = field(default_factory=list)
    confidence: float = 1.0                     # 0.0 si pattern no reconocido
    suggestion: str = ""                        # sugerencia adicional al usuario

    def __repr__(self) -> str:
        return (f"AgentResponse(pattern={self.pattern!r} "
                f"conf={self.confidence:.2f} tools={len(self.tools_called)})")


# ──────────────────────────────────────────────────────────────────────
# Reconocedor de patrones de pregunta (regex sobre la query)
# ──────────────────────────────────────────────────────────────────────


_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # Tag/AOI/Program explain — primero (más específico, captura el target)
    ("tag_explain",
     re.compile(r"\b(qu[eé] (es|hace|usa)|para qu[eé] sirve|explicar?|explain)\s+["
                r"`'\"]?(?P<target>[A-Za-z_][\w.\[\]:]*)[`'\"]?",
                re.IGNORECASE),
     "Explicación de un tag/AOI/program específico"),
    # General health primero también (más específico que motion/safety)
    ("general_health",
     re.compile(r"(salud|estado general|audit completo|resumen del proyecto|health)",
                re.IGNORECASE),
     "Salud general del proyecto"),
    ("splice_diagnosis",
     re.compile(r"(empalme|empalm[eo]s?|splice|splicer|\bctc\b)", re.IGNORECASE),
     "Diagnóstico de problema en empalme"),
    ("unwinder_diagnosis",
     re.compile(r"(unwind|unwinder|debobinad[ao]r|\buwm\b)", re.IGNORECASE),
     "Diagnóstico de problema en debobinador"),
    ("dancer_diagnosis",
     re.compile(r"(dancer|danzar[ií]n|tensi[oó]n|\bdnc\b)", re.IGNORECASE),
     "Diagnóstico relacionado con dancer/tensión"),
    ("safety_overview",
     re.compile(r"(safety|seguridad|guardlogix|estop|e-stop)", re.IGNORECASE),
     "Resumen de safety / GuardLogix del proyecto"),
    ("dead_code_audit",
     re.compile(r"(c[oó]digo muerto|hu[eé]rfano|orphan|dead code|no invocado|no usado)",
                re.IGNORECASE),
     "Auditoría de código muerto"),
    ("smell_audit",
     re.compile(r"(smell|best practice|mejor pr[aá]ctica|auditar|recomendaci[oó]n)",
                re.IGNORECASE),
     "Auditoría de smells y best practices"),
    ("motion_overview",
     re.compile(r"(\bmotion\b|\bejes?\b|\baxis\b|\baxes\b|\bservos?\b|\bmotores\b|resumen motion)",
                re.IGNORECASE),
     "Resumen de motion / ejes del proyecto"),
]


def _recognize_pattern(question: str) -> tuple[str, dict]:
    """Recognize the pattern of the question and extract groups."""
    for pattern_id, regex, _desc in _PATTERNS:
        m = regex.search(question)
        if m:
            return pattern_id, m.groupdict()
    return "unknown", {}


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def ask(project: "Project", question: str) -> AgentResponse:
    """Punto de entrada del agente determinístico.

    Args:
        project: Project ya cargado.
        question: pregunta en lenguaje natural (es/en).

    Returns:
        AgentResponse con answer + evidence + tools_called + confidence.
    """
    pattern, groups = _recognize_pattern(question)

    if pattern == "splice_diagnosis":
        return _handle_splice_diagnosis(project, question)
    if pattern == "unwinder_diagnosis":
        return _handle_unwinder_diagnosis(project, question)
    if pattern == "dancer_diagnosis":
        return _handle_dancer_diagnosis(project, question)
    if pattern == "safety_overview":
        return _handle_safety_overview(project, question)
    if pattern == "dead_code_audit":
        return _handle_dead_code_audit(project, question)
    if pattern == "smell_audit":
        return _handle_smell_audit(project, question)
    if pattern == "motion_overview":
        return _handle_motion_overview(project, question)
    if pattern == "general_health":
        return _handle_general_health(project, question)
    if pattern == "tag_explain":
        target = groups.get("target", "")
        return _handle_target_explain(project, question, target)

    # Pattern no reconocido — honestidad técnica
    return AgentResponse(
        question=question,
        pattern="unknown",
        answer=(
            f"No reconozco el patrón de la pregunta: \"{question}\".\n\n"
            "Patrones soportados:\n"
            "- Diagnóstico: empalme, unwinder/debobinador, dancer/tensión, safety\n"
            "- Auditoría: código muerto, smells, best practices, salud general\n"
            "- Resumen: motion/ejes, safety\n"
            "- Explicación: \"qué es X\" / \"qué hace X\" donde X es tag/AOI/program\n\n"
            "Para preguntas más complejas, consultar via Claude Code (que sí puede razonar)."
        ),
        confidence=0.0,
        suggestion="Reformular o consultar via Claude.",
    )


# ──────────────────────────────────────────────────────────────────────
# Handlers — uno por pattern (determinísticos)
# ──────────────────────────────────────────────────────────────────────


def _handle_splice_diagnosis(project: "Project", question: str) -> AgentResponse:
    tools: list[ToolCall] = []

    # 1. identify_domain
    hits = project.identify_domain("problema en empalme")
    tools.append(ToolCall(
        api="identify_domain",
        args_summary='"problema en empalme"',
        output_summary=f"{len(hits)} hits, top conf={hits[0].confidence if hits else 0:.2f}",
        output_size=len(hits),
    ))

    # 2. detect_motion_patterns con filtro splice_transition
    patterns = project.detect_motion_patterns()
    splice_patterns = [m for m in patterns if m.pattern.name == "splice_transition"]
    tools.append(ToolCall(
        api="detect_motion_patterns",
        args_summary="filter splice_transition",
        output_summary=f"{len(splice_patterns)} matches",
        output_size=len(splice_patterns),
    ))

    if not hits:
        return AgentResponse(
            question=question,
            pattern="splice_diagnosis",
            answer=(
                "No encuentro componentes de empalme en este proyecto. "
                "Posibles causas: (a) la arquitectura no usa empalme tipo Diatec "
                "(splicer/CTC); (b) los nombres de AOI/routine no contienen "
                "palabras-clave reconocidas (splice/splicer/ctc).\n\n"
                "Verificar con `project.search('Splic')` o consultar via Claude."
            ),
            evidence=[],
            tools_called=tools,
            confidence=0.4,
            suggestion="Si el proyecto sí tiene empalme con otro naming, especificar AOI por nombre.",
        )

    top = hits[:5]
    lines = [
        f"## Componentes de empalme detectados (top {len(top)} por confidence)",
        "",
    ]
    for h in top:
        lines.append(f"- **{h.target_kind}** `{h.target_name}` "
                     f"(conf {h.confidence:.2f}) "
                     f"— keywords: {', '.join(h.match_keywords[:5])}")

    if splice_patterns:
        lines.append("")
        lines.append(f"## Patterns motion `splice_transition` detectados ({len(splice_patterns)})")
        lines.append("")
        for m in splice_patterns[:5]:
            lines.append(f"- `{m.location}` axis=`{m.backing_tag}` conf={m.confidence:.2f}")
            lines.append(f"  - {m.evidence}")

    lines.append("")
    lines.append("## Próximo paso sugerido")
    lines.append("")
    lines.append("Para diagnosticar la causa raíz, trazar la cadena causal con:")
    lines.append("```python")
    lines.append('project.find_causal_path("Data.ReelRadiusA", "Data.HmiNewDiameter", '
                 'max_depth=8, direction="back")')
    lines.append("```")
    lines.append("o invocar `/diagnose empalme` desde Claude Code para flujo conversacional completo.")

    return AgentResponse(
        question=question,
        pattern="splice_diagnosis",
        answer="\n".join(lines),
        evidence=top + splice_patterns[:3],
        tools_called=tools,
        confidence=min(1.0, hits[0].confidence),
    )


def _handle_unwinder_diagnosis(project: "Project", question: str) -> AgentResponse:
    tools: list[ToolCall] = []
    hits = project.identify_domain("falla del unwinder")
    tools.append(ToolCall(
        api="identify_domain",
        args_summary='"falla del unwinder"',
        output_summary=f"{len(hits)} hits",
        output_size=len(hits),
    ))
    if not hits:
        return AgentResponse(
            question=question, pattern="unwinder_diagnosis",
            answer="No encuentro componentes de debobinador (unwinder) en este proyecto.",
            tools_called=tools, confidence=0.4,
        )
    top = hits[:5]
    lines = [
        f"## Componentes de debobinador detectados ({len(top)} top hits)",
        "",
    ]
    for h in top:
        lines.append(f"- **{h.target_kind}** `{h.target_name}` (conf {h.confidence:.2f})")
    lines.append("")
    lines.append("## Sugerencia de diagnóstico")
    lines.append("")
    lines.append("- Verificar `references_of` sobre el axis del unwinder")
    lines.append("- Revisar smells motion (motion_no_error_check) sobre el axis")
    return AgentResponse(
        question=question, pattern="unwinder_diagnosis",
        answer="\n".join(lines), evidence=top, tools_called=tools,
        confidence=hits[0].confidence,
    )


def _handle_dancer_diagnosis(project: "Project", question: str) -> AgentResponse:
    tools: list[ToolCall] = []
    hits = project.identify_domain("problema con dancer")
    tools.append(ToolCall(
        api="identify_domain", args_summary='"problema con dancer"',
        output_summary=f"{len(hits)} hits", output_size=len(hits),
    ))
    if not hits:
        return AgentResponse(
            question=question, pattern="dancer_diagnosis",
            answer="No encuentro componentes de dancer en este proyecto.",
            tools_called=tools, confidence=0.4,
        )
    top = hits[:5]
    lines = [f"## Componentes de dancer/tensión ({len(top)} hits)", ""]
    for h in top:
        lines.append(f"- **{h.target_kind}** `{h.target_name}` (conf {h.confidence:.2f})")
    return AgentResponse(
        question=question, pattern="dancer_diagnosis",
        answer="\n".join(lines), evidence=top, tools_called=tools,
        confidence=hits[0].confidence,
    )


def _handle_safety_overview(project: "Project", question: str) -> AgentResponse:
    tools: list[ToolCall] = []
    pi = project.program_inference()
    safety_progs = [(p, r) for p, r in pi if r.role == "safety_handler"]
    tools.append(ToolCall(
        api="program_inference",
        args_summary="(filter safety_handler)",
        output_summary=f"{len(safety_progs)} programs safety",
        output_size=len(safety_progs),
    ))
    smells = project.detect_smells()
    safety_smells = [s for s in smells if "safety" in s.kind.lower()]
    tools.append(ToolCall(
        api="detect_smells", args_summary="(filter safety)",
        output_summary=f"{len(safety_smells)} safety-related smells",
        output_size=len(safety_smells),
    ))
    lines = [f"## Resumen de safety", ""]
    if safety_progs:
        lines.append(f"### Programs safety detectados ({len(safety_progs)})")
        for p, r in safety_progs:
            lines.append(f"- `{p.name}` — conf={r.confidence:.2f} — evidencia: {'; '.join(r.evidence[:2])}")
    else:
        lines.append("Sin program safety detectado (puede ser proyecto sin GuardLogix).")
    if safety_smells:
        lines.append("")
        lines.append(f"### Safety smells detectados ({len(safety_smells)})")
        for s in safety_smells[:5]:
            lines.append(f"- `{s.kind}`: {s.target_name} ({s.severity})")
    return AgentResponse(
        question=question, pattern="safety_overview",
        answer="\n".join(lines),
        evidence=safety_progs + safety_smells[:5],
        tools_called=tools, confidence=1.0 if safety_progs else 0.7,
    )


def _handle_dead_code_audit(project: "Project", question: str) -> AgentResponse:
    tools: list[ToolCall] = []
    smells = project.detect_smells()
    aoi_dead = [s for s in smells if s.kind == "aoi_not_invoked"]
    tag_orphan_kinds = ("tag_scope_mismatch",)  # como proxy
    progr_unsched = [s for s in smells if s.kind == "program_unscheduled"]
    routines_empty = [s for s in smells if s.kind in ("routine_empty", "routine_trivial")]
    tools.append(ToolCall(
        api="detect_smells", args_summary="(filter dead-code)",
        output_summary=f"AOIs={len(aoi_dead)}, programs={len(progr_unsched)}, routines={len(routines_empty)}",
        output_size=len(aoi_dead) + len(progr_unsched) + len(routines_empty),
    ))
    lines = [f"## Auditoría de código muerto", ""]
    lines.append(f"- **AOIs no invocadas:** {len(aoi_dead)}")
    for s in aoi_dead[:10]:
        lines.append(f"  - `{s.target_name}`")
    lines.append(f"- **Programs sin task:** {len(progr_unsched)}")
    for s in progr_unsched:
        lines.append(f"  - `{s.target_name}`")
    lines.append(f"- **Routines vacías/triviales:** {len(routines_empty)}")
    for s in routines_empty[:10]:
        lines.append(f"  - `{s.target_name}` @ `{s.location}`")
    return AgentResponse(
        question=question, pattern="dead_code_audit",
        answer="\n".join(lines),
        evidence=aoi_dead + progr_unsched + routines_empty,
        tools_called=tools, confidence=1.0,
    )


def _handle_smell_audit(project: "Project", question: str) -> AgentResponse:
    from collections import Counter
    tools: list[ToolCall] = []
    smells = project.detect_smells()
    by_sev = Counter(s.severity for s in smells)
    by_kind = Counter(s.kind for s in smells)
    tools.append(ToolCall(
        api="detect_smells", args_summary="(all)",
        output_summary=f"{len(smells)} smells, {len(by_kind)} kinds",
        output_size=len(smells),
    ))
    lines = [f"## Auditoría de smells", ""]
    lines.append(f"**Total:** {len(smells)} smells "
                 f"({by_sev.get('high', 0)} high · {by_sev.get('medium', 0)} medium · "
                 f"{by_sev.get('low', 0)} low)")
    lines.append("")
    lines.append("### Top reglas activadas")
    for kind, cnt in by_kind.most_common(10):
        lines.append(f"- `{kind}`: {cnt}")
    return AgentResponse(
        question=question, pattern="smell_audit",
        answer="\n".join(lines),
        evidence=smells[:20],
        tools_called=tools, confidence=1.0,
    )


def _handle_motion_overview(project: "Project", question: str) -> AgentResponse:
    from collections import Counter
    tools: list[ToolCall] = []
    patterns = project.detect_motion_patterns()
    by_pat = Counter(m.pattern.name for m in patterns)
    tools.append(ToolCall(
        api="detect_motion_patterns", args_summary="(all)",
        output_summary=f"{len(patterns)} matches en {len(by_pat)} patterns",
        output_size=len(patterns),
    ))
    n_axis = sum(1 for t in project.tags if (t.datatype or "").startswith("AXIS_"))
    lines = [f"## Resumen motion", ""]
    lines.append(f"**Tags AXIS_*:** {n_axis}")
    lines.append(f"**Motion patterns detectados:** {len(patterns)}")
    lines.append("")
    for kind, cnt in by_pat.most_common():
        lines.append(f"- `{kind}`: {cnt}")
    return AgentResponse(
        question=question, pattern="motion_overview",
        answer="\n".join(lines),
        evidence=patterns[:10],
        tools_called=tools, confidence=1.0,
    )


def _handle_general_health(project: "Project", question: str) -> AgentResponse:
    from collections import Counter
    tools: list[ToolCall] = []
    smells = project.detect_smells()
    by_sev = Counter(s.severity for s in smells)
    tools.append(ToolCall(
        api="detect_smells", args_summary="(all)",
        output_summary=f"{len(smells)} smells",
        output_size=len(smells),
    ))
    pi = project.program_inference()
    tools.append(ToolCall(
        api="program_inference", args_summary="(all)",
        output_summary=f"{len(pi)} programs inferidos",
        output_size=len(pi),
    ))
    motion = project.detect_motion_patterns()
    tools.append(ToolCall(
        api="detect_motion_patterns", args_summary="(all)",
        output_summary=f"{len(motion)} matches",
        output_size=len(motion),
    ))
    lines = [f"## Salud general del proyecto"]
    lines.append("")
    if project.identity:
        lines.append(f"- **Target:** `{project.identity.target_name}` "
                     f"({project.identity.processor_type}, "
                     f"v{project.identity.software_revision})")
    lines.append(f"- **Modules:** {len(project.modules)} · "
                 f"AOIs: {len(project.aois)} · "
                 f"Programs: {len(project.programs)} · "
                 f"Routines: {len(project.routines)} · "
                 f"Tags: {len(project.tags)}")
    lines.append(f"- **Smells:** {len(smells)} ({by_sev.get('high',0)} H / "
                 f"{by_sev.get('medium',0)} M / {by_sev.get('low',0)} L)")
    lines.append(f"- **Motion patterns:** {len(motion)} matches")
    lines.append("")
    lines.append("### Programs por rol funcional")
    role_counter = Counter(r.role for _, r in pi)
    for role, cnt in role_counter.most_common():
        lines.append(f"- `{role}`: {cnt}")
    return AgentResponse(
        question=question, pattern="general_health",
        answer="\n".join(lines),
        evidence=[smells[:5], pi, motion[:5]],
        tools_called=tools, confidence=1.0,
    )


def _handle_target_explain(project: "Project", question: str, target: str) -> AgentResponse:
    """Explain a tag/AOI/program by name."""
    tools: list[ToolCall] = []
    if not target:
        return AgentResponse(
            question=question, pattern="tag_explain",
            answer="No pude extraer el target de la pregunta.",
            confidence=0.0, tools_called=tools,
        )

    # Try AOI
    aoi = project.get_aoi(target)
    if aoi:
        tools.append(ToolCall(api="get_aoi", args_summary=target,
                              output_summary=f"AOI con {len(aoi.parameters)} params",
                              output_size=len(aoi.parameters)))
        lines = [f"## AOI `{aoi.name}`", ""]
        lines.append(f"- **Parameters:** {len(aoi.parameters)}")
        lines.append(f"- **Routines:** {list(aoi.routines.keys())}")
        return AgentResponse(question=question, pattern="aoi_explain",
                             answer="\n".join(lines), evidence=[aoi],
                             tools_called=tools, confidence=1.0)

    # Try program
    prog = next((p for p in project.programs if p.name == target), None)
    if prog:
        role = project.classify_program(prog)
        tools.append(ToolCall(api="classify_program", args_summary=target,
                              output_summary=f"role={role.role} conf={role.confidence:.2f}",
                              output_size=1))
        lines = [f"## Program `{prog.name}`", "",
                 f"- **Role inferido:** `{role.role}` (conf {role.confidence:.2f})",
                 f"- **Descripción:** {role.description}",
                 f"- **Main routine:** `{prog.main_routine}`",
                 f"- **Evidence:**"]
        for e in role.evidence:
            lines.append(f"  - {e}")
        return AgentResponse(question=question, pattern="program_explain",
                             answer="\n".join(lines), evidence=[prog, role],
                             tools_called=tools, confidence=role.confidence)

    # Try tag
    tag = next((t for t in project.tags if t.name == target), None)
    if tag:
        tag_role = project.classify_tag(tag)
        tools.append(ToolCall(api="classify_tag", args_summary=target,
                              output_summary=f"role={tag_role.role}",
                              output_size=1))
        try:
            refs = project.references_of(target)
        except Exception:
            refs = []
        tools.append(ToolCall(api="references_of", args_summary=target,
                              output_summary=f"{len(refs)} refs",
                              output_size=len(refs)))
        lines = [f"## Tag `{tag.name}`", "",
                 f"- **Datatype:** `{tag.datatype}`",
                 f"- **Scope:** `{tag.scope}`",
                 f"- **Role inferido:** `{tag_role.role}` (conf {tag_role.confidence:.2f})",
                 f"- **Descripción:** {tag_role.description}",
                 f"- **References en código:** {len(refs)}"]
        if refs[:5]:
            lines.append("- **Top 5 references:**")
            for r in refs[:5]:
                lines.append(f"  - `{r.location}` op={r.operator} usage={r.usage}")
        return AgentResponse(question=question, pattern="tag_explain",
                             answer="\n".join(lines), evidence=[tag, tag_role],
                             tools_called=tools, confidence=tag_role.confidence)

    return AgentResponse(
        question=question, pattern="tag_explain",
        answer=f"No encuentro `{target}` como tag, AOI ni program en el proyecto.",
        confidence=0.0, tools_called=tools,
    )
