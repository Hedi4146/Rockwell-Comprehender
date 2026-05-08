"""CLI ergonómico — `python -m rockwell_comprehender ...` (v0.7.4).

Permite usar el toolkit desde shell sin Claude Code de por medio.
Versatilidad de canal: Python script, notebook, Claude Code, CLI.

**Subcomandos:**
- `ask` — pregunta determinística vía agent.ask
- `audit` — auditoría completa de un L5X
- `compare` — diff entre 2 L5X
- `bench` — ejecuta el banco de pruebas
- `version` — info del paquete

**Stack mínimo (DT-008):** solo `argparse` (stdlib).

Uso:
    python -m rockwell_comprehender ask "problema en empalme" --project=parque_l5x/CINTA_LAMINADA_M2_2024.L5X
    python -m rockwell_comprehender audit parque_l5x/CINTA_LAMINADA_M2_2024.L5X
    python -m rockwell_comprehender compare A.L5X B.L5X
    python -m rockwell_comprehender bench
    python -m rockwell_comprehender version
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _cmd_ask(args) -> int:
    from . import load_project
    if not Path(args.project).exists():
        print(f"ERROR: L5X no encontrado: {args.project}", file=sys.stderr)
        return 2
    p = load_project(args.project)
    if args.audit:
        from .audit_log import enable_audit, instrument_project
        log_path = enable_audit(project_name=p.identity.target_name if p.identity else "")
        instrument_project(p)
        print(f"# Audit log: {log_path}")
    response = p.ask(args.question)
    print(f"# Pattern: {response.pattern}")
    print(f"# Confidence: {response.confidence:.2f}")
    print(f"# Tools called: {len(response.tools_called)}")
    for t in response.tools_called:
        print(f"#   - {t.api}({t.args_summary[:50]}) -> {t.output_summary}")
    print()
    print(response.answer)
    if response.suggestion:
        print()
        print(f"[suggestion] {response.suggestion}")
    return 0 if response.confidence > 0 else 1


def _cmd_audit(args) -> int:
    from . import load_project
    from collections import Counter
    if not Path(args.project).exists():
        print(f"ERROR: L5X no encontrado: {args.project}", file=sys.stderr)
        return 2
    p = load_project(args.project)
    print("=" * 70)
    print(f"AUDIT - {p.identity.target_name if p.identity else args.project}")
    print("=" * 70)
    print()
    if p.identity:
        print(f"Procesador:    {p.identity.processor_type}")
        print(f"Software:      v{p.identity.software_revision}")
    print(f"Modules:       {len(p.modules)}")
    print(f"AOIs:          {len(p.aois)}")
    print(f"Programs:      {len(p.programs)}")
    print(f"Routines:      {len(p.routines)}")
    print(f"Tags:          {len(p.tags)}")
    print(f"UDTs:          {len(p.udts)}")
    print(f"Tasks:         {len(p.tasks)}")

    # Smells
    smells = p.detect_smells()
    by_sev = Counter(s.severity for s in smells)
    by_kind = Counter(s.kind for s in smells)
    print()
    print(f"Smells:        {len(smells)} total ({by_sev.get('high',0)} H / "
          f"{by_sev.get('medium',0)} M / {by_sev.get('low',0)} L)")
    print("Top reglas:")
    for k, c in by_kind.most_common(8):
        print(f"  {k:30s}: {c}")

    # Programs inferidos
    print()
    print("Programs inferidos:")
    for prog, role in p.program_inference():
        print(f"  {prog.name:30s}: {role.role:25s} conf={role.confidence:.2f}")

    # Motion patterns
    patterns = p.detect_motion_patterns()
    print()
    print(f"Motion patterns: {len(patterns)} matches")
    by_pat = Counter(m.pattern.name for m in patterns)
    for k, c in by_pat.most_common():
        print(f"  {k:25s}: {c}")

    return 0


def _cmd_compare(args) -> int:
    from . import load_project
    from .project_diff import diff_projects
    for path in (args.old, args.new):
        if not Path(path).exists():
            print(f"ERROR: L5X no encontrado: {path}", file=sys.stderr)
            return 2
    p_old = load_project(args.old)
    p_new = load_project(args.new)
    d = diff_projects(p_old, p_new)
    print(d.summary())
    if args.output:
        Path(args.output).write_text(d.to_markdown(), encoding="utf-8")
        print(f"# Reporte completo: {args.output}")
    else:
        print()
        # Mostrar primeros entries de cada categoría
        for label, items in [("Modules", d.modules), ("AOIs", d.aois),
                             ("Programs", d.programs), ("Tasks", d.tasks)]:
            if not items:
                continue
            print(f"\n{label} ({len(items)}):")
            for e in items[:8]:
                detail = f" — {e.detail}" if e.detail else ""
                print(f"  [{e.kind}] {e.name}{detail}")
            if len(items) > 8:
                print(f"  ... +{len(items) - 8} más (usar --output para reporte completo)")
    return 0


def _cmd_bench(args) -> int:
    """Re-ejecuta el bench."""
    bench_path = Path(__file__).resolve().parents[1] / "docs" / "Test" / "_bench.py"
    if not bench_path.exists():
        print(f"ERROR: bench script no encontrado en {bench_path}", file=sys.stderr)
        return 2
    # Ejecutar el bench como script
    import subprocess
    cmd = [sys.executable, str(bench_path)]
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.call(cmd, env=env, cwd=str(bench_path.parents[2]))


def _cmd_version(args) -> int:
    try:
        from . import __version__ as v
    except ImportError:
        v = "0.7-dev"
    print(f"rockwell_comprehender {v}")
    print()
    print("Capabilities:")
    caps = [
        ("v0.1", "Lectura estructural L5X + Mapa Mental + reporters MD/Excel/Mermaid"),
        ("v0.2", "Tracer xref RLL+ST + writers/readers/find_causal_path/trace_back"),
        ("v0.3", "instruction_library 38 entries + identify_domain (lexicón síntoma→código)"),
        ("v0.4", "motion_patterns nivel-2 (8 detectores)"),
        ("v0.5", "tag_dictionary + program_inference + project_diff"),
        ("v0.6", "test bench (40/40 PASS, 14 APIs × 3 L5X)"),
        ("v0.7", "agent.ask determinístico + slash commands + audit log + CLI"),
    ]
    for ver, desc in caps:
        print(f"  {ver}  {desc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rockwell_comprehender",
        description="Toolkit de comprensión profunda de proyectos Rockwell Studio 5000 (L5X).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ask
    p_ask = sub.add_parser("ask", help="Pregunta determinística vía agent.ask")
    p_ask.add_argument("question", help="Pregunta en lenguaje natural")
    p_ask.add_argument("--project", "-p", required=True, help="Path al .L5X")
    p_ask.add_argument("--audit", action="store_true",
                       help="Activa audit log JSONL para esta invocación")
    p_ask.set_defaults(fn=_cmd_ask)

    # audit
    p_audit = sub.add_parser("audit", help="Auditoría completa de un L5X")
    p_audit.add_argument("project", help="Path al .L5X")
    p_audit.set_defaults(fn=_cmd_audit)

    # compare
    p_cmp = sub.add_parser("compare", help="Diff entre 2 L5X")
    p_cmp.add_argument("old", help="L5X viejo")
    p_cmp.add_argument("new", help="L5X nuevo")
    p_cmp.add_argument("--output", "-o", help="Guardar reporte completo a Markdown path")
    p_cmp.set_defaults(fn=_cmd_compare)

    # bench
    p_bench = sub.add_parser("bench", help="Ejecuta el banco de pruebas")
    p_bench.set_defaults(fn=_cmd_bench)

    # version
    p_ver = sub.add_parser("version", help="Info del paquete + capabilities")
    p_ver.set_defaults(fn=_cmd_version)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
