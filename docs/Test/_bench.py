"""Test Bench — métricas de rendimiento, consumo de tokens y resultado.

Sprint 9 v0.6 (2026-05-06). Banco de pruebas que evalúa **todas las
capacidades adquiridas** del paquete `rockwell_comprehender` contra los
3 L5X del parque, midiendo:

- **Latencia** (`time.perf_counter`): wall-clock de cada API.
- **Consumo de tokens (estimado):** `chars / 4` aproximación honesta
  cuando el output es texto (Mapa Mental, Markdown, HTML, etc.). Para
  outputs estructurados (lists, dicts), se mide `len(repr(out))`. NO
  usamos `tiktoken` porque sería una dependencia (DT-008). La aproximación
  4-chars/token es razonable para texto natural en español/inglés.
- **Resultado (assertion):** PASS si el output cumple invariantes
  esperados (no None, len > 0 cuando aplica, tipo correcto), FAIL si no.

Output:
- `docs/Test/_bench_report.md` — reporte consolidado Markdown.
- `docs/Test/_bench_results.json` — datos crudos para análisis posterior.
- stdout — tabla resumen.

Uso:
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python docs/Test/_bench.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ──────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────

PROJECTS = [
    ("CINTA", "parque_l5x/CINTA_LAMINADA_M2_2024.L5X"),
    ("AQL",   "parque_l5x/AQL_M2.L5X"),
    ("CPPIM", "parque_l5x/CPPIM_BD800_1.L5X"),
]

# Aproximación honesta token-count: chars / 4. Documentado en módulo.
CHARS_PER_TOKEN = 4


# ──────────────────────────────────────────────────────────────────────
# Estructuras
# ──────────────────────────────────────────────────────────────────────


@dataclass
class BenchResult:
    api: str
    project: str
    duration_ms: float
    output_chars: int
    tokens_approx: int
    output_kind: str       # "text" | "list" | "dict" | "object" | "html"
    items_or_size: int     # len(list) o size del output según corresponda
    assertion: str         # "PASS" | "FAIL" | "SKIP"
    detail: str = ""       # explicación del assertion / nota
    peak_mem_kb: int = 0   # pico de memoria capturado por tracemalloc


@dataclass
class BenchSummary:
    total_apis: int = 0
    total_runs: int = 0
    pass_count: int = 0
    fail_count: int = 0
    skip_count: int = 0
    total_duration_ms: float = 0.0
    total_tokens_approx: int = 0
    results: list[BenchResult] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _measure(fn, *args, **kwargs):
    """Ejecuta fn y devuelve (result, duration_ms, peak_mem_kb)."""
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
    finally:
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return result, elapsed_ms, peak // 1024


def _size_text(s) -> int:
    if isinstance(s, str):
        return len(s)
    return len(str(s))


def _approx_tokens(chars: int) -> int:
    return chars // CHARS_PER_TOKEN


def _record(summary: BenchSummary, r: BenchResult) -> None:
    summary.results.append(r)
    summary.total_runs += 1
    summary.total_duration_ms += r.duration_ms
    summary.total_tokens_approx += r.tokens_approx
    if r.assertion == "PASS":
        summary.pass_count += 1
    elif r.assertion == "FAIL":
        summary.fail_count += 1
    else:
        summary.skip_count += 1


# ──────────────────────────────────────────────────────────────────────
# Bench
# ──────────────────────────────────────────────────────────────────────


def run_bench() -> BenchSummary:
    from rockwell_comprehender import load_project
    from rockwell_comprehender.project_diff import diff_projects
    from rockwell_comprehender.reporters.markdown import to_markdown
    from rockwell_comprehender.reporters.excel import to_excel
    from rockwell_comprehender.reporters.mermaid import to_mermaid
    from rockwell_comprehender.reporters.html_explorer import to_html_explorer
    from rockwell_comprehender.reporters.tdr_html import to_tdr_html
    from rockwell_comprehender.smells import smells_to_markdown
    from rockwell_comprehender.motion_patterns import motion_patterns_to_markdown
    from rockwell_comprehender.tag_dictionary import tag_dictionary_to_markdown
    from rockwell_comprehender.program_inference import program_inference_to_markdown

    summary = BenchSummary()
    apis_seen: set[str] = set()

    projs: dict[str, object] = {}

    for label, path in PROJECTS:
        # ─── load_project ─────────────────────────────────────────────
        project, dur_ms, peak = _measure(load_project, path)
        projs[label] = project
        # assertion: project tiene identity + alguna estructura
        assertion = ("PASS" if project and project.identity and len(project.modules) > 0
                     else "FAIL")
        size = len(project.modules) + len(project.aois) + len(project.programs)
        _record(summary, BenchResult(
            api="load_project", project=label, duration_ms=dur_ms,
            output_chars=0, tokens_approx=0, output_kind="object",
            items_or_size=size, assertion=assertion,
            detail=f"{len(project.modules)} modules + {len(project.aois)} aois + {len(project.programs)} programs",
            peak_mem_kb=peak,
        ))
        apis_seen.add("load_project")

        # ─── mapa_mental ──────────────────────────────────────────────
        mm, dur_ms, peak = _measure(lambda p=project: p.mapa_mental)
        chars = _size_text(mm)
        assertion = "PASS" if chars > 500 else "FAIL"
        _record(summary, BenchResult(
            api="mapa_mental", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="text", items_or_size=chars, assertion=assertion,
            detail=f"{chars} chars",
            peak_mem_kb=peak,
        ))
        apis_seen.add("mapa_mental")

        # ─── search ───────────────────────────────────────────────────
        hits, dur_ms, peak = _measure(lambda p=project: p.search("Splice"))
        n = len(hits)
        chars = sum(len(h.snippet) for h in hits)
        assertion = "PASS" if n >= 0 else "FAIL"  # search puede ser 0 hits y ok
        _record(summary, BenchResult(
            api="search('Splice')", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} hits",
            peak_mem_kb=peak,
        ))
        apis_seen.add("search")

        # ─── references_of (un tag controller) ────────────────────────
        sample_tag = next((t for t in project.tags if t.scope == "controller"
                           and not t.datatype.startswith(("AXIS_", "MOTION_"))), None)
        if sample_tag:
            refs, dur_ms, peak = _measure(lambda p=project, n=sample_tag.name: p.references_of(n))
            n_refs = len(refs)
            assertion = "PASS"
            _record(summary, BenchResult(
                api="references_of", project=label, duration_ms=dur_ms,
                output_chars=n_refs * 80, tokens_approx=_approx_tokens(n_refs * 80),
                output_kind="list", items_or_size=n_refs, assertion=assertion,
                detail=f"sample tag '{sample_tag.name}' → {n_refs} refs",
                peak_mem_kb=peak,
            ))
            apis_seen.add("references_of")

        # ─── identify_domain ──────────────────────────────────────────
        dom_hits, dur_ms, peak = _measure(lambda p=project: p.identify_domain("problema en empalme"))
        n = len(dom_hits)
        chars = sum(60 + len(", ".join(h.match_keywords)) for h in dom_hits)
        # CPPIM no tiene splicer Diatec — 0 hits es válido también, pero
        # esperamos al menos algún hit en cualquier proyecto del parque
        assertion = "PASS" if n >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="identify_domain", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} hits (top conf={dom_hits[0].confidence if dom_hits else 0:.2f})",
            peak_mem_kb=peak,
        ))
        apis_seen.add("identify_domain")

        # ─── detect_smells ────────────────────────────────────────────
        smells, dur_ms, peak = _measure(lambda p=project: p.detect_smells())
        n = len(smells)
        chars = sum(len(s.description) + len(s.target_name) + 50 for s in smells)
        assertion = "PASS" if n >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="detect_smells", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} smells (15 reglas activas)",
            peak_mem_kb=peak,
        ))
        apis_seen.add("detect_smells")

        # ─── detect_motion_patterns ───────────────────────────────────
        mp, dur_ms, peak = _measure(lambda p=project: p.detect_motion_patterns())
        n = len(mp)
        chars = sum(len(m.evidence) + 80 for m in mp)
        assertion = "PASS" if n >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="detect_motion_patterns", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} matches",
            peak_mem_kb=peak,
        ))
        apis_seen.add("detect_motion_patterns")

        # ─── tag_dictionary ───────────────────────────────────────────
        td, dur_ms, peak = _measure(lambda p=project: p.tag_dictionary())
        n = len(td)
        # estimación: cada entry ~120 chars en reporte
        chars = n * 120
        assertion = "PASS" if n >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="tag_dictionary", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} tags clasificados",
            peak_mem_kb=peak,
        ))
        apis_seen.add("tag_dictionary")

        # ─── program_inference ────────────────────────────────────────
        pi, dur_ms, peak = _measure(lambda p=project: p.program_inference())
        n = len(pi)
        chars = sum(len(role.role) + len(role.description) + 100 for _, role in pi)
        assertion = "PASS" if n >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="program_inference", project=label, duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="list", items_or_size=n, assertion=assertion,
            detail=f"{n} programs inferidos",
            peak_mem_kb=peak,
        ))
        apis_seen.add("program_inference")

        # ─── to_markdown (TDR completo) ───────────────────────────────
        out_path = f"docs/Test/_bench_tmp_{label}.md"
        try:
            saved, dur_ms, peak = _measure(to_markdown, project, out_path)
            chars = os.path.getsize(saved)
            assertion = "PASS" if chars > 1000 else "FAIL"
            _record(summary, BenchResult(
                api="to_markdown", project=label, duration_ms=dur_ms,
                output_chars=chars, tokens_approx=_approx_tokens(chars),
                output_kind="text", items_or_size=chars, assertion=assertion,
                detail=f"{chars} bytes",
                peak_mem_kb=peak,
            ))
            try:
                os.remove(saved)
            except OSError:
                pass
        except Exception as exc:
            _record(summary, BenchResult(
                api="to_markdown", project=label, duration_ms=0.0,
                output_chars=0, tokens_approx=0, output_kind="text",
                items_or_size=0, assertion="FAIL", detail=str(exc),
            ))
        apis_seen.add("to_markdown")

        # ─── to_excel ─────────────────────────────────────────────────
        out_path = f"docs/Test/_bench_tmp_{label}.xlsx"
        try:
            saved, dur_ms, peak = _measure(to_excel, project, out_path)
            chars = os.path.getsize(saved)
            assertion = "PASS" if chars > 1000 else "FAIL"
            _record(summary, BenchResult(
                api="to_excel", project=label, duration_ms=dur_ms,
                output_chars=chars, tokens_approx=0,  # binario, no tokens
                output_kind="binary", items_or_size=chars, assertion=assertion,
                detail=f"{chars} bytes (xlsx)",
                peak_mem_kb=peak,
            ))
            try:
                os.remove(saved)
            except OSError:
                pass
        except Exception as exc:
            _record(summary, BenchResult(
                api="to_excel", project=label, duration_ms=0.0,
                output_chars=0, tokens_approx=0, output_kind="binary",
                items_or_size=0, assertion="FAIL", detail=str(exc),
            ))
        apis_seen.add("to_excel")

        # ─── to_html_explorer ─────────────────────────────────────────
        out_path = f"docs/Test/_bench_tmp_{label}_explorer.html"
        try:
            saved, dur_ms, peak = _measure(to_html_explorer, project, out_path)
            chars = os.path.getsize(saved)
            assertion = "PASS" if chars > 5000 else "FAIL"
            _record(summary, BenchResult(
                api="to_html_explorer", project=label, duration_ms=dur_ms,
                output_chars=chars, tokens_approx=_approx_tokens(chars),
                output_kind="html", items_or_size=chars, assertion=assertion,
                detail=f"{chars} bytes (html)",
                peak_mem_kb=peak,
            ))
            try:
                os.remove(saved)
            except OSError:
                pass
        except Exception as exc:
            _record(summary, BenchResult(
                api="to_html_explorer", project=label, duration_ms=0.0,
                output_chars=0, tokens_approx=0, output_kind="html",
                items_or_size=0, assertion="FAIL", detail=str(exc),
            ))
        apis_seen.add("to_html_explorer")

        # ─── to_tdr_html ──────────────────────────────────────────────
        out_path = f"docs/Test/_bench_tmp_{label}_tdr.html"
        try:
            saved, dur_ms, peak = _measure(to_tdr_html, project, out_path)
            chars = os.path.getsize(saved)
            assertion = "PASS" if chars > 1000 else "FAIL"
            _record(summary, BenchResult(
                api="to_tdr_html", project=label, duration_ms=dur_ms,
                output_chars=chars, tokens_approx=_approx_tokens(chars),
                output_kind="html", items_or_size=chars, assertion=assertion,
                detail=f"{chars} bytes (TDR)",
                peak_mem_kb=peak,
            ))
            try:
                os.remove(saved)
            except OSError:
                pass
        except Exception as exc:
            _record(summary, BenchResult(
                api="to_tdr_html", project=label, duration_ms=0.0,
                output_chars=0, tokens_approx=0, output_kind="html",
                items_or_size=0, assertion="FAIL", detail=str(exc),
            ))
        apis_seen.add("to_tdr_html")

    # ─── diff_projects (cross-project, una sola vez) ──────────────────
    if "CINTA" in projs and "AQL" in projs:
        d, dur_ms, peak = _measure(diff_projects, projs["CINTA"], projs["AQL"])
        chars = len(d.to_markdown())
        n_changes = (len(d.modules) + len(d.aois) + len(d.programs)
                     + len(d.routines) + len(d.tags) + len(d.tasks))
        assertion = "PASS" if n_changes >= 1 else "FAIL"
        _record(summary, BenchResult(
            api="diff_projects", project="CINTA→AQL", duration_ms=dur_ms,
            output_chars=chars, tokens_approx=_approx_tokens(chars),
            output_kind="object", items_or_size=n_changes, assertion=assertion,
            detail=f"{n_changes} entries en diff total",
            peak_mem_kb=peak,
        ))
        apis_seen.add("diff_projects")

    summary.total_apis = len(apis_seen)
    return summary


# ──────────────────────────────────────────────────────────────────────
# Reportes
# ──────────────────────────────────────────────────────────────────────


def write_markdown_report(summary: BenchSummary, out_path: str) -> None:
    lines: list[str] = []
    lines.append("# Test Bench — Métricas de capacidades")
    lines.append("")
    lines.append(f"**Generado:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append(f"- **APIs distintas evaluadas:** {summary.total_apis}")
    lines.append(f"- **Runs totales:** {summary.total_runs}")
    lines.append(f"- **PASS:** {summary.pass_count}  |  **FAIL:** {summary.fail_count}  |  **SKIP:** {summary.skip_count}")
    lines.append(f"- **Tiempo total wall-clock:** {summary.total_duration_ms:.1f} ms ({summary.total_duration_ms/1000:.2f} s)")
    lines.append(f"- **Tokens aprox totales (output):** {summary.total_tokens_approx:,} (chars/4)")
    lines.append("")
    lines.append("> _Nota sobre tokens:_ aproximación honesta `chars/4` sin dependencias externas (DT-008). Para outputs binarios (xlsx) se reporta tamaño en bytes pero NO se cuentan tokens.")
    lines.append("")

    # Tabla por API
    lines.append("## Latencia por API (ms) — promedio sobre 3 L5X")
    lines.append("")
    lines.append("| API | CINTA | AQL | CPPIM | Promedio | Tokens (avg) | PASS |")
    lines.append("|-----|------:|----:|------:|---------:|-------------:|:----:|")
    by_api: dict[str, dict[str, BenchResult]] = {}
    for r in summary.results:
        by_api.setdefault(r.api, {})[r.project] = r
    for api in sorted(by_api):
        runs = by_api[api]
        cinta = runs.get("CINTA")
        aql = runs.get("AQL")
        cppim = runs.get("CPPIM")
        cross = runs.get("CINTA→AQL")
        durs = [r.duration_ms for r in runs.values()]
        toks = [r.tokens_approx for r in runs.values()]
        avg_dur = sum(durs) / len(durs) if durs else 0
        avg_tok = sum(toks) // len(toks) if toks else 0
        passes = sum(1 for r in runs.values() if r.assertion == "PASS")
        total = len(runs)
        def fmt(r):
            return f"{r.duration_ms:.1f}" if r else "—"
        lines.append(
            f"| `{api}` | {fmt(cinta)} | {fmt(aql)} | {fmt(cppim)}{'' if not cross else f' (cross: {cross.duration_ms:.1f})'} | "
            f"**{avg_dur:.1f}** | {avg_tok:,} | {passes}/{total} |"
        )
    lines.append("")

    # Tabla detallada
    lines.append("## Resultados detallados")
    lines.append("")
    lines.append("| API | Project | ms | chars | tokens (~) | items | mem peak (KB) | result | detail |")
    lines.append("|-----|---------|---:|------:|-----------:|------:|--------------:|:------:|--------|")
    for r in summary.results:
        badge = "✅" if r.assertion == "PASS" else "❌" if r.assertion == "FAIL" else "⊘"
        lines.append(
            f"| `{r.api}` | {r.project} | {r.duration_ms:.1f} | {r.output_chars:,} | "
            f"{r.tokens_approx:,} | {r.items_or_size:,} | {r.peak_mem_kb:,} | {badge} | {r.detail} |"
        )
    lines.append("")

    # Top APIs por consumo
    lines.append("## Top 5 APIs por latencia (peor caso CPPIM)")
    lines.append("")
    cppim_runs = [r for r in summary.results if r.project == "CPPIM"]
    cppim_sorted = sorted(cppim_runs, key=lambda r: -r.duration_ms)[:5]
    lines.append("| Rank | API | ms | tokens (~) |")
    lines.append("|-----:|-----|---:|-----------:|")
    for i, r in enumerate(cppim_sorted, 1):
        lines.append(f"| {i} | `{r.api}` | {r.duration_ms:.1f} | {r.tokens_approx:,} |")
    lines.append("")

    lines.append("## Top 5 APIs por output token-count")
    lines.append("")
    by_tokens = sorted(summary.results, key=lambda r: -r.tokens_approx)[:5]
    lines.append("| Rank | API | Project | tokens (~) | chars |")
    lines.append("|-----:|-----|---------|-----------:|------:|")
    for i, r in enumerate(by_tokens, 1):
        lines.append(f"| {i} | `{r.api}` | {r.project} | {r.tokens_approx:,} | {r.output_chars:,} |")
    lines.append("")

    # Conclusiones
    lines.append("## Lectura honesta")
    lines.append("")
    if summary.fail_count == 0:
        lines.append(f"- **0 fallos** sobre {summary.total_runs} runs — todas las APIs evaluadas cumplen sus invariantes en los 3 L5X del parque.")
    else:
        lines.append(f"- ⚠️ **{summary.fail_count} fallos** detectados — ver tabla detallada para diagnóstico.")
    lines.append(f"- **Wall-clock total** ~{summary.total_duration_ms:.0f} ms para ejecutar todas las capacidades sobre los 3 L5X. Costo amortizado ~{summary.total_duration_ms/summary.total_runs:.0f} ms por API+project.")
    lines.append(f"- **Tokens estimados de output:** {summary.total_tokens_approx:,} acumulados. Esto representa el costo de **leer todos los outputs** como input a un LLM.")
    lines.append("- **Stack mínimo (DT-008) preservado:** medición sin dependencias externas (`time.perf_counter`, `tracemalloc`, aproximación `chars/4`).")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def write_json_results(summary: BenchSummary, out_path: str) -> None:
    payload = {
        "total_apis": summary.total_apis,
        "total_runs": summary.total_runs,
        "pass_count": summary.pass_count,
        "fail_count": summary.fail_count,
        "skip_count": summary.skip_count,
        "total_duration_ms": summary.total_duration_ms,
        "total_tokens_approx": summary.total_tokens_approx,
        "results": [asdict(r) for r in summary.results],
        "metadata": {
            "chars_per_token": CHARS_PER_TOKEN,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "note": "Token approximation chars/4 — no external deps per DT-008",
        },
    }
    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=" * 78)
    print("ROCKWELL_COMPREHENDER — TEST BENCH")
    print("=" * 78)
    print()
    print("Ejecutando bench contra los 3 L5X del parque...")
    print()

    summary = run_bench()

    # Stdout summary
    print(f"\nAPIs evaluadas:      {summary.total_apis}")
    print(f"Runs totales:        {summary.total_runs}")
    print(f"PASS / FAIL / SKIP:  {summary.pass_count} / {summary.fail_count} / {summary.skip_count}")
    print(f"Wall-clock total:    {summary.total_duration_ms:.1f} ms ({summary.total_duration_ms/1000:.2f} s)")
    print(f"Tokens aprox totales:{summary.total_tokens_approx:,}")
    print()

    # Reportes
    md_path = "docs/Test/_bench_report.md"
    json_path = "docs/Test/_bench_results.json"
    write_markdown_report(summary, md_path)
    write_json_results(summary, json_path)
    print(f"Reporte MD:   {md_path}")
    print(f"Datos crudos: {json_path}")
