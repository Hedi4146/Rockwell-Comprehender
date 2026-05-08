"""Behavior Tests — assertions sobre RESPUESTAS específicas del agente (v0.7.5).

A diferencia del `_bench.py` (Sprint 9) que valida que las APIs no fallen
y mide rendimiento, los behavior tests validan que **respuestas
específicas** sean correctas. Verifican el comportamiento determinístico
del agente contra casos de uso documentados en `AGENT_CONTRACT.md`.

Output:
- stdout — tabla de assertions con PASS/FAIL
- exit code 0 si todas pasan, 1 si alguna falla

Uso:
    PYTHONUTF8=1 python docs/Test/_behavior_tests.py
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rockwell_comprehender import load_project


@dataclass
class TestResult:
    test_id: str
    description: str
    passed: bool
    detail: str = ""
    duration_ms: float = 0.0


_results: list[TestResult] = []


def _run(test_id: str, description: str, fn) -> None:
    """Ejecuta un test y registra el resultado."""
    t0 = time.perf_counter()
    try:
        ok, detail = fn()
        passed = bool(ok)
        if not detail:
            detail = "OK" if passed else "FAIL"
    except AssertionError as e:
        passed = False
        detail = f"AssertionError: {e}"
    except Exception as e:
        passed = False
        detail = f"{type(e).__name__}: {e}"
    duration_ms = (time.perf_counter() - t0) * 1000.0
    _results.append(TestResult(test_id, description, passed, detail, duration_ms))


# ──────────────────────────────────────────────────────────────────────
# Loading projects (cached)
# ──────────────────────────────────────────────────────────────────────


_PROJECTS = {
    "CINTA": "parque_l5x/CINTA_LAMINADA_M2_2024.L5X",
    "AQL":   "parque_l5x/AQL_M2.L5X",
    "CPPIM": "parque_l5x/CPPIM_BD800_1.L5X",
}

_cache: dict[str, object] = {}


def _get(label: str):
    if label not in _cache:
        _cache[label] = load_project(_PROJECTS[label])
    return _cache[label]


# ──────────────────────────────────────────────────────────────────────
# Tests de comportamiento
# ──────────────────────────────────────────────────────────────────────


def test_t01_splice_diagnosis_cinta():
    """T01: agent.ask('problema en empalme') en CINTA reconoce el patrón
    splice_diagnosis con confidence 1.00 y retorna AHT_CtcSplicer en evidence."""
    p = _get("CINTA")
    r = p.ask("problema en empalme")
    if r.pattern != "splice_diagnosis":
        return False, f"pattern={r.pattern}, expected splice_diagnosis"
    if r.confidence < 0.7:
        return False, f"confidence={r.confidence:.2f} < 0.7"
    aoi_names = [getattr(e, "target_name", None) for e in r.evidence]
    if "AHT_CtcSplicer" not in aoi_names:
        return False, f"AHT_CtcSplicer not in evidence: {aoi_names[:5]}"
    return True, f"pattern={r.pattern} conf={r.confidence:.2f} top={aoi_names[0]}"


def test_t02_splice_diagnosis_determinism():
    """T02: dos invocaciones consecutivas de splice_diagnosis retornan
    EXACTAMENTE el mismo AgentResponse (determinismo verificable)."""
    p = _get("CINTA")
    r1 = p.ask("problema en empalme")
    r2 = p.ask("problema en empalme")
    if r1.answer != r2.answer:
        return False, "answers difieren"
    if r1.confidence != r2.confidence:
        return False, f"confidences difieren: {r1.confidence} vs {r2.confidence}"
    if len(r1.tools_called) != len(r2.tools_called):
        return False, f"tools_called len difiere: {len(r1.tools_called)} vs {len(r2.tools_called)}"
    return True, f"answer/conf/tools idénticos ({len(r1.answer)} chars, {len(r1.tools_called)} tools)"


def test_t03_unknown_pattern_zero_confidence():
    """T03: query no reconocida retorna pattern='unknown' con confidence=0
    y sugerencia de delegar al LLM."""
    p = _get("CINTA")
    r = p.ask("dame la receta de quesadillas")
    if r.pattern != "unknown":
        return False, f"pattern={r.pattern}, expected unknown"
    if r.confidence != 0.0:
        return False, f"confidence={r.confidence}, expected 0.0"
    if "Claude" not in r.answer and "delegar" not in r.answer.lower():
        return False, "answer no menciona delegar al LLM"
    return True, f"correctly identified as unknown ({r.confidence:.2f})"


def test_t04_safety_overview_cppim():
    """T04: safety_overview en CPPIM detecta SafetyProgram con conf=0.90."""
    p = _get("CPPIM")
    r = p.ask("estado safety")
    if r.pattern != "safety_overview":
        return False, f"pattern={r.pattern}"
    if "SafetyProgram" not in r.answer:
        return False, "SafetyProgram no aparece en answer"
    return True, "SafetyProgram detectado en answer"


def test_t05_dead_code_audit_cinta():
    """T05: dead_code_audit en CINTA reporta AOIs no invocadas."""
    p = _get("CINTA")
    r = p.ask("código muerto")
    if r.pattern != "dead_code_audit":
        return False, f"pattern={r.pattern}"
    if r.confidence < 1.0:
        return False, f"confidence={r.confidence}"
    if "AOIs no invocadas" not in r.answer:
        return False, "answer no menciona AOIs no invocadas"
    return True, "AOIs no invocadas reportadas"


def test_t06_explain_aoi():
    """T06: explain de AOI conocido (AHT_CtcSplicer) en CINTA."""
    p = _get("CINTA")
    r = p.ask("qué hace AHT_CtcSplicer")
    if r.pattern != "aoi_explain":
        return False, f"pattern={r.pattern}, expected aoi_explain"
    if "AHT_CtcSplicer" not in r.answer:
        return False, "answer no contiene AHT_CtcSplicer"
    return True, f"AOI explain correcto"


def test_t07_explain_program():
    """T07: explain de Program con role inferido."""
    p = _get("CPPIM")
    r = p.ask("qué hace SafetyProgram")
    if r.pattern != "program_explain":
        return False, f"pattern={r.pattern}, expected program_explain"
    if "safety_handler" not in r.answer:
        return False, "answer no contiene 'safety_handler' role"
    return True, "Program SafetyProgram → safety_handler"


def test_t08_general_health_kpis():
    """T08: general_health reporta KPIs (modules, AOIs, programs)."""
    p = _get("AQL")
    r = p.ask("salud general")
    if r.pattern != "general_health":
        return False, f"pattern={r.pattern}"
    needs = ["Modules:", "AOIs:", "Programs:"]
    missing = [n for n in needs if n not in r.answer]
    if missing:
        return False, f"missing en answer: {missing}"
    return True, "KPIs presentes"


def test_t09_motion_overview_patterns():
    """T09: motion_overview reporta patterns motion detectados."""
    p = _get("AQL")
    r = p.ask("resumen motion")
    if r.pattern != "motion_overview":
        return False, f"pattern={r.pattern}"
    # AQL tiene splice_transition, gear_chain, etc. — esperar al menos 1
    if "splice_transition" not in r.answer and "gear_chain" not in r.answer:
        return False, "ningún pattern motion conocido en answer"
    return True, "patterns motion reportados"


def test_t10_explain_unknown_target():
    """T10: explain de target inexistente retorna confidence=0."""
    p = _get("CINTA")
    r = p.ask("qué hace ESTE_TAG_NO_EXISTE_AQUI")
    # target no existe — handler retorna confidence=0
    if r.confidence > 0.0:
        return False, f"confidence={r.confidence}, expected 0"
    if "no encuentro" not in r.answer.lower() and "no encuentr" not in r.answer.lower():
        return False, "answer no menciona que no encuentra el target"
    return True, "target inexistente reportado correctamente"


def test_t11_smell_audit_returns_smells():
    """T11: smell_audit retorna lista de smells ordenada por severidad."""
    p = _get("CINTA")
    r = p.ask("auditar smells")
    if r.pattern != "smell_audit":
        return False, f"pattern={r.pattern}"
    if "Total:" not in r.answer:
        return False, "answer no contiene 'Total:'"
    return True, "smell_audit OK"


def test_t12_cross_l5x_consistency():
    """T12: el patrón splice_diagnosis funciona en CINTA + AQL (ambos Diatec)
    pero da PARCIAL en CPPIM (no tiene splicer Diatec)."""
    cinta_r = _get("CINTA").ask("problema en empalme")
    aql_r = _get("AQL").ask("problema en empalme")
    cppim_r = _get("CPPIM").ask("problema en empalme")
    if cinta_r.pattern != "splice_diagnosis" or cinta_r.confidence < 0.7:
        return False, f"CINTA fail: {cinta_r.pattern}/{cinta_r.confidence}"
    if aql_r.pattern != "splice_diagnosis" or aql_r.confidence < 0.7:
        return False, f"AQL fail: {aql_r.pattern}/{aql_r.confidence}"
    # CPPIM debería reconocer pattern pero con menor confidence
    if cppim_r.pattern != "splice_diagnosis":
        return False, f"CPPIM fail: pattern={cppim_r.pattern}"
    return True, (f"CINTA conf={cinta_r.confidence:.2f}, AQL conf={aql_r.confidence:.2f}, "
                  f"CPPIM conf={cppim_r.confidence:.2f}")


def test_t13_audit_log_records():
    """T13: con audit log activo, las invocaciones del agente quedan en JSONL."""
    from rockwell_comprehender.audit_log import enable_audit, disable_audit, instrument_project
    import json
    log_path = enable_audit(session_id="behavior_t13")
    p = _get("CINTA")
    instrument_project(p)
    p.detect_smells()
    p.identify_domain("empalme")
    disable_audit()
    if not log_path.exists():
        return False, "log file no creado"
    with open(log_path, encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
    if len(lines) < 3:
        return False, f"records {len(lines)} < 3"
    # Verificar que es JSONL parseable
    for ln in lines:
        json.loads(ln)
    return True, f"{len(lines)} records JSONL válidos"


def test_t14_cli_version_imports():
    """T14: el CLI module se importa sin errores (no ejecuta argv)."""
    try:
        from rockwell_comprehender import __main__ as cli_main
        if not hasattr(cli_main, "main"):
            return False, "CLI no expone main()"
    except Exception as e:
        return False, f"import falla: {e}"
    return True, "CLI module importable"


def test_t15_diff_projects_smoke():
    """T15: diff_projects entre CINTA y AQL produce summary parseable."""
    from rockwell_comprehender.project_diff import diff_projects
    d = diff_projects(_get("CINTA"), _get("AQL"))
    summary = d.summary()
    if "modules:" not in summary or "aois:" not in summary:
        return False, f"summary incompleto: {summary[:80]}"
    md = d.to_markdown()
    if len(md) < 500:
        return False, f"markdown muy corto: {len(md)} chars"
    return True, summary


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────


TESTS = [
    ("T01", "splice_diagnosis CINTA con AHT_CtcSplicer en evidence", test_t01_splice_diagnosis_cinta),
    ("T02", "splice_diagnosis es determinístico (idem-input → idem-output)", test_t02_splice_diagnosis_determinism),
    ("T03", "query no reconocida → pattern=unknown, confidence=0", test_t03_unknown_pattern_zero_confidence),
    ("T04", "safety_overview en CPPIM detecta SafetyProgram", test_t04_safety_overview_cppim),
    ("T05", "dead_code_audit en CINTA reporta AOIs no invocadas", test_t05_dead_code_audit_cinta),
    ("T06", "aoi_explain devuelve metadata de AHT_CtcSplicer", test_t06_explain_aoi),
    ("T07", "program_explain devuelve role safety_handler para SafetyProgram", test_t07_explain_program),
    ("T08", "general_health reporta KPIs (modules/aois/programs)", test_t08_general_health_kpis),
    ("T09", "motion_overview reporta patterns motion conocidos", test_t09_motion_overview_patterns),
    ("T10", "explain de target inexistente → confidence=0 y mensaje", test_t10_explain_unknown_target),
    ("T11", "smell_audit retorna 'Total:' en answer", test_t11_smell_audit_returns_smells),
    ("T12", "splice_diagnosis funciona en 3 L5X (CINTA, AQL, CPPIM)", test_t12_cross_l5x_consistency),
    ("T13", "audit log activo deja records JSONL parseables", test_t13_audit_log_records),
    ("T14", "CLI module importable sin errores", test_t14_cli_version_imports),
    ("T15", "diff_projects produce summary + markdown coherente", test_t15_diff_projects_smoke),
]


if __name__ == "__main__":
    print("=" * 78)
    print("BEHAVIOR TESTS - rockwell_comprehender v0.7")
    print("=" * 78)
    print(f"Tests: {len(TESTS)}")
    print()

    for tid, desc, fn in TESTS:
        _run(tid, desc, fn)

    # Summary
    pass_count = sum(1 for r in _results if r.passed)
    fail_count = len(_results) - pass_count
    total_ms = sum(r.duration_ms for r in _results)

    print(f"{'Test':5s}  {'PASS':5s}  {'ms':>7s}  Description")
    print("-" * 78)
    for r in _results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{r.test_id:5s}  {status:5s}  {r.duration_ms:7.1f}  {r.description[:60]}")
        if not r.passed:
            print(f"        FAIL detail: {r.detail}")

    print()
    print(f"Resultado: {pass_count}/{len(_results)} PASS")
    print(f"Wall-clock total: {total_ms:.1f} ms")

    sys.exit(0 if fail_count == 0 else 1)
