"""Audit Log — trazabilidad estructurada de invocaciones del toolkit (v0.7).

Cada call a una API pública del paquete puede dejar un registro JSONL
con `{timestamp, project, api, args_summary, output_summary, duration_ms}`.
Permite reproducir cualquier sesión paso a paso desde el log.

**Activación:**
- Variable de entorno: `ROCKWELL_AUDIT=1` activa logging global por default.
- Programática: `load_project(path, audit=True)` o `enable_audit(session_id)`.
- Archivo destino: `docs/Audit_trail/<session_id>.jsonl` (override con
  env var `ROCKWELL_AUDIT_PATH`).

**Decoradores:**
- `@audit_log("api_name")` — decora funciones del toolkit. Cuando audit
  está activo, registra cada call automáticamente. Cuando NO está activo,
  no impacta perf (early return).

**Stack mínimo (DT-008):** solo stdlib (`json`, `time`, `os`, `pathlib`,
`functools`, `uuid`).

**Uso típico (tras Sprint 10):**
    import os
    os.environ["ROCKWELL_AUDIT"] = "1"
    from rockwell_comprehender import load_project
    p = load_project("X.L5X")
    p.detect_smells()  # automáticamente loggeado
    # → docs/Audit_trail/<session_id>.jsonl
"""

from __future__ import annotations

import functools
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# ──────────────────────────────────────────────────────────────────────
# Estado del logger (singleton lazy)
# ──────────────────────────────────────────────────────────────────────


@dataclass
class _AuditState:
    enabled: bool = False
    session_id: str = ""
    log_path: Path | None = None
    project_name: str = ""
    call_count: int = 0


_state = _AuditState()


# ──────────────────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────────────────


def is_enabled() -> bool:
    """Returns True si audit logging está activo."""
    return _state.enabled


def enable_audit(session_id: str | None = None,
                 log_path: str | Path | None = None,
                 project_name: str = "") -> Path:
    """Activa audit logging para la sesión actual.

    Args:
        session_id: identificador. Si None, se genera uno via uuid4()[:8].
        log_path: path destino. Si None, usa env `ROCKWELL_AUDIT_PATH` o
            `docs/Audit_trail/<session_id>.jsonl`.
        project_name: nombre del proyecto activo (se incluye en cada record).

    Returns:
        Path absoluto del archivo de log.
    """
    if session_id is None:
        session_id = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    if log_path is None:
        env_path = os.environ.get("ROCKWELL_AUDIT_PATH")
        if env_path:
            log_path = Path(env_path)
        else:
            log_path = Path("docs/Audit_trail") / f"{session_id}.jsonl"
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _state.enabled = True
    _state.session_id = session_id
    _state.log_path = log_path
    _state.project_name = project_name
    _state.call_count = 0

    # Inicializar archivo con record meta
    _write_record({
        "type": "session_start",
        "session_id": session_id,
        "timestamp": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "project": project_name,
    })

    return log_path.absolute()


def disable_audit() -> None:
    """Cierra audit logging. Escribe record final."""
    if not _state.enabled:
        return
    _write_record({
        "type": "session_end",
        "session_id": _state.session_id,
        "timestamp": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_calls": _state.call_count,
    })
    _state.enabled = False
    _state.session_id = ""
    _state.log_path = None
    _state.project_name = ""


def set_project_name(name: str) -> None:
    """Setter para identificar el proyecto activo en los records."""
    _state.project_name = name


def record(api: str, args_summary: str, output_summary: str,
           duration_ms: float, output_size: int = 0,
           extra: dict | None = None) -> None:
    """Registra una entrada de audit log manualmente."""
    if not _state.enabled:
        return
    rec = {
        "type": "call",
        "session_id": _state.session_id,
        "timestamp": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "project": _state.project_name,
        "api": api,
        "args_summary": args_summary,
        "output_summary": output_summary,
        "output_size": output_size,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        rec["extra"] = extra
    _write_record(rec)
    _state.call_count += 1


def audit_log(api_name: str,
              args_extractor: Callable[..., str] | None = None,
              output_extractor: Callable[..., str] | None = None) -> Callable:
    """Decorador que envuelve una función del toolkit con audit logging.

    Args:
        api_name: nombre de la API (string, ej "detect_smells").
        args_extractor: función opcional que toma `(*args, **kwargs)` y
            retorna string corto representativo. Si None, usa repr básico.
        output_extractor: función opcional que toma el `output` y retorna
            string corto + size. Si None, usa heurística (len, type).

    El wrapper:
    1. Si audit no está activo: invoca normalmente (sin overhead).
    2. Si activo: mide duration, extrae summaries, escribe record.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _state.enabled:
                return fn(*args, **kwargs)
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                duration_ms = (time.perf_counter() - t0) * 1000.0
                record(
                    api=api_name,
                    args_summary=_default_args_summary(args, kwargs, args_extractor),
                    output_summary=f"EXCEPTION: {type(exc).__name__}: {exc}",
                    duration_ms=duration_ms,
                    output_size=0,
                )
                raise
            duration_ms = (time.perf_counter() - t0) * 1000.0
            args_summary = _default_args_summary(args, kwargs, args_extractor)
            output_summary, output_size = _default_output_summary(result, output_extractor)
            record(
                api=api_name,
                args_summary=args_summary,
                output_summary=output_summary,
                duration_ms=duration_ms,
                output_size=output_size,
            )
            return result
        return wrapper
    return decorator


# ──────────────────────────────────────────────────────────────────────
# Implementación interna
# ──────────────────────────────────────────────────────────────────────


def _write_record(rec: dict) -> None:
    """Append JSONL a log_path. Defensivo — no falla si IO falla."""
    if _state.log_path is None:
        return
    try:
        with open(_state.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        # Fallar silencioso — el audit log no debe interrumpir la app.
        pass


def _default_args_summary(args: tuple, kwargs: dict,
                          extractor: Callable | None) -> str:
    """Genera summary de args. Si hay extractor, lo usa; si no, heurística."""
    if extractor is not None:
        try:
            return extractor(*args, **kwargs)[:200]
        except Exception:
            pass
    parts = []
    # Note: cuando se decora vía instrument_project (object.__setattr__),
    # los args ya no incluyen self. Cuando se decora a nivel de clase,
    # args[0] sería self. Heurística: si args[0] es un objeto del paquete
    # (tiene atributo 'identity' o 'name'), skipear.
    skip_first = bool(args and (hasattr(args[0], "identity") or
                                hasattr(args[0], "_xref_built")))
    for a in (args[1:] if skip_first else args):
        s = repr(a)
        if len(s) > 60:
            s = s[:57] + "..."
        parts.append(s)
    for k, v in kwargs.items():
        s = f"{k}={v!r}"
        if len(s) > 60:
            s = s[:57] + "..."
        parts.append(s)
    return ", ".join(parts)[:200]


def _default_output_summary(output: Any, extractor: Callable | None) -> tuple[str, int]:
    if extractor is not None:
        try:
            res = extractor(output)
            if isinstance(res, tuple):
                return str(res[0])[:200], int(res[1])
            return str(res)[:200], 0
        except Exception:
            pass
    if output is None:
        return "None", 0
    if isinstance(output, str):
        size = len(output)
        return f"<str len={size}>", size
    if isinstance(output, (list, tuple)):
        size = len(output)
        return f"<{type(output).__name__} len={size}>", size
    if isinstance(output, dict):
        size = len(output)
        return f"<dict keys={size}>", size
    # Fallback
    s = repr(output)
    if len(s) > 100:
        s = s[:97] + "..."
    return s, 0


# ──────────────────────────────────────────────────────────────────────
# Auto-init desde env var (opt-in al import)
# ──────────────────────────────────────────────────────────────────────


def instrument_project(project: Any) -> None:
    """Decora en runtime las APIs públicas de un Project para audit logging.

    Aplica `audit_log` decorator sobre los métodos analíticos del objeto
    project (instance-level, no clase). Es opt-in y reversible — solo
    afecta al objeto pasado.

    APIs instrumentadas:
        mapa_mental (property — se dejará pasar)
        search, references_of, writers_of, readers_of,
        find_causal_path, trace_back, trace_forward,
        get_aoi, get_routine, get_udt,
        identify_domain, classify_tag, tag_dictionary,
        classify_program, program_inference,
        detect_smells, detect_motion_patterns,
        get_instruction_metadata, ask
    """
    apis_to_instrument = [
        "search", "references_of", "writers_of", "readers_of",
        "find_causal_path", "trace_back", "trace_forward",
        "get_aoi", "get_routine", "get_udt",
        "identify_domain", "classify_tag", "tag_dictionary",
        "classify_program", "program_inference",
        "detect_smells", "detect_motion_patterns",
        "get_instruction_metadata", "ask",
    ]
    for api in apis_to_instrument:
        if not hasattr(project, api):
            continue
        original = getattr(project, api)
        if not callable(original):
            continue
        # Marca para evitar doble decoración
        if getattr(original, "_audit_wrapped", False):
            continue
        wrapped = audit_log(api)(original)
        wrapped._audit_wrapped = True  # type: ignore[attr-defined]
        try:
            object.__setattr__(project, api, wrapped)
        except (AttributeError, TypeError):
            # Si el dataclass es frozen u otra restricción, ignorar.
            pass


def _maybe_auto_enable() -> None:
    """Si ROCKWELL_AUDIT=1 está seteado, activar audit por default."""
    if os.environ.get("ROCKWELL_AUDIT", "").strip() in ("1", "true", "TRUE", "yes"):
        try:
            enable_audit()
        except Exception:
            pass


_maybe_auto_enable()
