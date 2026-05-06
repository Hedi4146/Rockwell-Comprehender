"""TDR HTML ejecutivo — Sprint 5 D.2.

Genera un Technical Design Review (TDR) auto-contenido en HTML que
combina:
  - Mapa Mental del proyecto (mapamental.py)
  - Smell summary y top smells (smells.py)
  - Casos de dominio comunes (domain_lexicon.py)
  - Recomendaciones del asesor (síntesis automática)

Auto-contenido: CSS+JS inline, sin dependencias externas. Apto para
imprimir a PDF desde browser ("Print to PDF") sin perder formato.

Stack mínimo (DT-008): solo stdlib + reusa módulos existentes del
paquete.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Project


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def to_tdr_html(project: "Project", output_path: str) -> str:
    """Genera TDR HTML ejecutivo y lo escribe a output_path.

    Args:
        project: Project ya cargado.
        output_path: ruta destino del .html

    Returns:
        Path absoluto del archivo escrito.
    """
    parts = [
        _tdr_head(project),
        _tdr_summary_card(project),
        _tdr_mapa_mental_section(project),
        _tdr_smells_section(project),
        _tdr_domain_examples_section(project),
        _tdr_recommendations_section(project),
        _tdr_foot(),
    ]
    html = "\n".join(parts)
    Path(output_path).write_text(html, encoding="utf-8")
    return os.path.abspath(output_path)


# ──────────────────────────────────────────────────────────────────────
# Helpers HTML
# ──────────────────────────────────────────────────────────────────────


def _e(s) -> str:
    """Escape HTML."""
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


_CSS = """
* { box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.5;
    color: #222;
    max-width: 980px;
    margin: 0 auto;
    padding: 2rem 1rem;
    background: #fafafa;
}
h1 { color: #1a3a5c; border-bottom: 3px solid #1a3a5c; padding-bottom: 0.5rem; }
h2 { color: #2a5a8a; margin-top: 2.5rem; border-bottom: 1px solid #ddd; padding-bottom: 0.25rem; }
h3 { color: #3a4a5a; margin-top: 1.5rem; }
.card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.card.warn { border-left: 4px solid #d97706; }
.card.danger { border-left: 4px solid #dc2626; }
.card.ok { border-left: 4px solid #16a34a; }
.card.info { border-left: 4px solid #1d4ed8; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #eee; }
th { background: #f3f4f6; font-weight: 600; }
code { font-family: 'Consolas', 'Monaco', monospace;
       background: #f0f0f0; padding: 0.1rem 0.3rem; border-radius: 3px;
       font-size: 0.9em; }
pre { background: #f5f5f5; padding: 1rem; border-radius: 4px;
      overflow-x: auto; font-size: 0.85em; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem; margin: 1.5rem 0; }
.kpi { background: white; padding: 1rem; border-radius: 6px; text-align: center;
       border: 1px solid #ddd; }
.kpi-value { font-size: 2rem; font-weight: bold; color: #1a3a5c; }
.kpi-label { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }
.severity-high { background: #fee2e2; color: #991b1b; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.85em; font-weight: bold; }
.severity-medium { background: #fef3c7; color: #92400e; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.85em; font-weight: bold; }
.severity-low { background: #dbeafe; color: #1e40af; padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.85em; }
.meta { color: #666; font-size: 0.9em; }
ul.compact { margin: 0.5rem 0; padding-left: 1.5rem; }
ul.compact li { margin: 0.2rem 0; }
.muted { color: #999; }
.toc { background: white; border: 1px solid #ddd; padding: 1rem 1.5rem;
       border-radius: 6px; margin: 1rem 0; }
.toc ul { margin: 0; padding-left: 1.5rem; }
.toc a { text-decoration: none; color: #1d4ed8; }
.toc a:hover { text-decoration: underline; }
@media print {
    body { max-width: none; background: white; padding: 0; }
    h1 { page-break-before: avoid; }
    h2 { page-break-after: avoid; }
    .card { box-shadow: none; }
}
"""


def _tdr_head(project: "Project") -> str:
    name = project.identity.target_name if project.identity else "<unknown>"
    sw = project.identity.software_revision if project.identity else "?"
    proc = project.identity.processor_type if project.identity else "?"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>TDR — {_e(name)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Technical Design Review — {_e(name)}</h1>
<p class="meta">Procesador <code>{_e(proc)}</code> · Studio 5000 v{_e(sw)} · Generado {now}</p>

<div class="toc">
<strong>Contenido</strong>
<ul>
  <li><a href="#summary">1. Resumen ejecutivo</a></li>
  <li><a href="#mapa">2. Mapa Mental</a></li>
  <li><a href="#smells">3. Smells & Best Practices</a></li>
  <li><a href="#domain">4. Casos de dominio comunes</a></li>
  <li><a href="#recs">5. Recomendaciones</a></li>
</ul>
</div>
"""


def _tdr_summary_card(project: "Project") -> str:
    n_modules = len(project.modules)
    n_aois = len(project.aois)
    n_routines = len(project.routines)
    n_tags = len(project.tags)
    n_programs = len(project.programs)
    n_tasks = len(project.tasks)

    return f"""
<h2 id="summary">1. Resumen ejecutivo</h2>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-value">{n_modules}</div><div class="kpi-label">Modules</div></div>
  <div class="kpi"><div class="kpi-value">{n_aois}</div><div class="kpi-label">AOIs</div></div>
  <div class="kpi"><div class="kpi-value">{n_programs}</div><div class="kpi-label">Programs</div></div>
  <div class="kpi"><div class="kpi-value">{n_routines}</div><div class="kpi-label">Routines</div></div>
  <div class="kpi"><div class="kpi-value">{n_tags}</div><div class="kpi-label">Tags</div></div>
  <div class="kpi"><div class="kpi-value">{n_tasks}</div><div class="kpi-label">Tasks</div></div>
</div>
"""


def _tdr_mapa_mental_section(project: "Project") -> str:
    mm = project.mapa_mental
    # Mapa Mental ya viene en Markdown — convertir a HTML simple.
    # Para simplicidad usamos un <pre> con whitespace preservado.
    mm_html = _md_to_html_simple(mm)
    return f"""
<h2 id="mapa">2. Mapa Mental</h2>
<div class="card info">
{mm_html}
</div>
"""


def _tdr_smells_section(project: "Project") -> str:
    try:
        smells = project.detect_smells()
    except Exception as e:
        return f"""
<h2 id="smells">3. Smells & Best Practices</h2>
<div class="card warn">
<p>Detección de smells no disponible: {_e(str(e))}</p>
</div>
"""

    by_sev = Counter(s.severity for s in smells)
    by_kind = Counter(s.kind for s in smells)

    sev_table = "<table><thead><tr><th>Severidad</th><th>Count</th></tr></thead><tbody>"
    for sev in ("high", "medium", "low"):
        if by_sev[sev]:
            sev_table += f'<tr><td><span class="severity-{sev}">{sev}</span></td><td>{by_sev[sev]}</td></tr>'
    sev_table += "</tbody></table>"

    kind_rows = "".join(
        f'<tr><td><code>{_e(k)}</code></td><td>{c}</td></tr>'
        for k, c in by_kind.most_common(15)
    )
    kind_table = f"""<table>
<thead><tr><th>Regla</th><th>Count</th></tr></thead>
<tbody>{kind_rows}</tbody></table>"""

    # Top 10 high severity con detalle
    high_smells = [s for s in smells if s.severity == "high"][:10]
    if high_smells:
        high_html = "<h3>Top 10 smells de alta severidad</h3><ul class='compact'>"
        for s in high_smells:
            high_html += (
                f'<li><span class="severity-high">{s.severity}</span> '
                f'<code>{_e(s.kind)}</code>: '
                f'<strong>{_e(s.target_kind)}</strong> '
                f'<code>{_e(s.target_name)}</code> — {_e(s.description)}</li>'
            )
        high_html += "</ul>"
    else:
        high_html = '<p class="meta">Sin smells de alta severidad detectados.</p>'

    total = len(smells)
    return f"""
<h2 id="smells">3. Smells & Best Practices</h2>
<div class="card {'danger' if by_sev['high'] > 5 else 'warn' if by_sev['medium'] > 0 else 'ok'}">
<p><strong>Total: {total} smells detectados</strong> contra 15 reglas
({by_sev['high']} high · {by_sev['medium']} medium · {by_sev['low']} low).</p>
<h3>Por severidad</h3>
{sev_table}
<h3>Por regla (top 15)</h3>
{kind_table}
{high_html}
<p class="meta">Reporte completo disponible vía <code>project.detect_smells()</code> + <code>smells_to_markdown()</code>.</p>
</div>
"""


def _tdr_domain_examples_section(project: "Project") -> str:
    """Muestra ejemplos de identify_domain() para síntomas típicos."""
    examples = [
        "problema en empalme",
        "falla del unwinder",
        "problema con el dancer",
        "falla del drive",
        "safety estop",
    ]
    blocks = []
    for query in examples:
        try:
            hits = project.identify_domain(query)
        except Exception:
            continue
        if not hits:
            blocks.append(
                f'<h3>"{_e(query)}"</h3>'
                f'<p class="meta">Sin hits detectados (síntoma no aplica a este proyecto).</p>'
            )
            continue
        rows = "".join(
            f'<tr><td>{h.confidence:.2f}</td>'
            f'<td><span class="meta">{_e(h.target_kind)}</span></td>'
            f'<td><code>{_e(h.target_name)}</code></td>'
            f'<td><span class="meta">kw: {", ".join(_e(k) for k in h.match_keywords[:5])}</span></td></tr>'
            for h in hits[:5]
        )
        blocks.append(f"""
<h3>"{_e(query)}"</h3>
<table>
<thead><tr><th>Conf</th><th>Kind</th><th>Target</th><th>Keywords</th></tr></thead>
<tbody>{rows}</tbody>
</table>""")
    body = "".join(blocks) if blocks else '<p class="meta">No se ejecutaron ejemplos.</p>'
    return f"""
<h2 id="domain">4. Casos de dominio comunes</h2>
<div class="card info">
<p>Demostración de <code>project.identify_domain(query)</code> contra síntomas típicos. Cada hit muestra confidence (0-1), tipo de target y keywords matched.</p>
{body}
</div>
"""


def _tdr_recommendations_section(project: "Project") -> str:
    """Genera recomendaciones automáticas del asesor basadas en smells + heurísticas."""
    try:
        smells = project.detect_smells()
    except Exception:
        smells = []

    by_kind = Counter(s.kind for s in smells)
    recs = []

    if by_kind.get("otl_without_otu", 0) > 5:
        recs.append((
            "high",
            f"Auditar OTL sin OTU ({by_kind['otl_without_otu']} casos)",
            "Revisar si los bits enclavados se resetean por HMI directo o si requieren OTU explícito. Tags Alarm.* típicamente se gestionan desde HMI; otros pueden ser bugs."
        ))
    if by_kind.get("aoi_too_many_params", 0) > 0:
        recs.append((
            "medium",
            f"Considerar descomposición de AOIs grandes ({by_kind['aoi_too_many_params']} con >30 params)",
            "AOIs con >30 parameters tienden a ser god-objects difíciles de invocar y mantener. Evaluar si pueden separarse en sub-AOIs por responsabilidad."
        ))
    if by_kind.get("aoi_not_invoked", 0) > 0:
        recs.append((
            "medium",
            f"Eliminar AOIs no invocadas ({by_kind['aoi_not_invoked']} casos)",
            "AOIs definidas pero nunca usadas son código muerto. Confirmar con el equipo si son legacy borrables o templates intencionales."
        ))
    if by_kind.get("motion_no_error_check", 0) > 5:
        recs.append((
            "medium",
            f"Agregar error handling a motion instructions ({by_kind['motion_no_error_check']} sin .ER check)",
            "Best practice MOTION-RM002: inspeccionar bit .ER del motion_control struct tras cada motion instruction. Sin esto, errores silenciosos del comando pueden encadenarse."
        ))
    if by_kind.get("st_transitional_no_oneshot", 0) > 0:
        recs.append((
            "high",
            f"Revisar instrucciones transicionales ST sin One-Shot ({by_kind['st_transitional_no_oneshot']} casos)",
            "Gotcha crítico pub 1756-RM003 cap 24: en ST instrucciones como MAM/MAS/MDO se re-disparan en cada scan si no se empaquetan en IF con OSR/OSRI. Comportamiento errático probable."
        ))
    if by_kind.get("program_unscheduled", 0) > 0:
        recs.append((
            "high",
            f"Programs no asignados a task ({by_kind['program_unscheduled']} casos)",
            "Código que nunca se ejecuta. Confirmar si son intencionalmente reservados o legacy borrable."
        ))
    if by_kind.get("safety_program_naming", 0) > 0:
        recs.append((
            "medium",
            f"Revisar naming de programs con safety logic ({by_kind['safety_program_naming']} casos)",
            "Best practice GuardLogix: programs con CROUT/DCI_* deben tener 'Safety' en su nombre para evitar mezclar con lógica standard. Requerimiento regulatorio SIL/PLe."
        ))
    if by_kind.get("tag_scope_mismatch", 0) > 10:
        recs.append((
            "low",
            f"Optimizar scope de tags ({by_kind['tag_scope_mismatch']} controller-scope solo usados en 1 program)",
            "Mover a program-local reduce namespace global y mejora encapsulación. Bajo impacto pero higiénico."
        ))

    if not recs:
        recs.append((
            "ok",
            "Sin recomendaciones críticas",
            "El proyecto no presenta smells masivos que ameriten recomendaciones automáticas en este TDR. Ver tabla completa en sección 3."
        ))

    rec_html = ""
    for sev, title, body in recs:
        cls = "danger" if sev == "high" else "warn" if sev == "medium" else "ok" if sev == "ok" else "info"
        sev_html = f'<span class="severity-{sev}">{sev}</span>' if sev in ("high", "medium", "low") else ""
        rec_html += f"""
<div class="card {cls}">
<strong>{sev_html} {_e(title)}</strong>
<p>{_e(body)}</p>
</div>
"""

    return f"""
<h2 id="recs">5. Recomendaciones del asesor</h2>
<p class="meta">Recomendaciones generadas automáticamente desde el análisis de smells y heurísticas del paquete <code>rockwell_comprehender</code>. Priorizadas por severidad.</p>
{rec_html}
"""


def _tdr_foot() -> str:
    return """
<hr style="margin-top: 3rem;">
<p class="meta">Generado por <code>rockwell_comprehender</code> · TDR v0.3.x · Sprint 5 D.2.</p>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────
# Conversor Markdown → HTML simple
# ──────────────────────────────────────────────────────────────────────


def _md_to_html_simple(text: str) -> str:
    """Conversor MD→HTML mínimo para el Mapa Mental.

    Soporta solo lo necesario: headers (#, ##, ###), listas (-), enlaces
    [txt](url), bold **, código inline `, párrafos. No es un parser
    completo — el Mapa Mental usa un subset acotado de Markdown.
    """
    import re as _re
    out = []
    in_list = False
    for line in text.splitlines():
        s = line.rstrip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("")
            continue
        # Headers
        h = _re.match(r"^(#{1,6})\s+(.*)$", s)
        if h:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(h.group(1))
            out.append(f"<h{level + 2}>{_inline(h.group(2))}</h{level + 2}>")
            continue
        # List items
        m = _re.match(r"^\s*[-*]\s+(.*)$", s)
        if m:
            if not in_list:
                out.append("<ul class='compact'>")
                in_list = True
            out.append(f"<li>{_inline(m.group(1))}</li>")
            continue
        # Paragraph
        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{_inline(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _inline(text: str) -> str:
    """Inline markdown → HTML (bold, code, escape)."""
    import re as _re
    # Escape primero
    t = _e(text)
    # Bold (** o __)
    t = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    # Inline code
    t = _re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t
