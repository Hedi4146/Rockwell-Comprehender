# AGENT_CONTRACT.md — Contrato del Agente Rockwell Comprehender

**Versión:** v0.7 (Sprint 10 — Formalización del agente)
**Fecha:** 2026-05-07
**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Complementa:** [`SKILL.md`](SKILL.md) (contrato del skill nivel-Claude)

---

## 0. Quién soy

`rockwell_comprehender` es un **toolkit Python** para comprensión profunda de proyectos Rockwell Studio 5000 (archivos `.L5X`). Combinado con un LLM cliente (Claude Code, Claude API, etc.) opera como un **agente tool-using**: el LLM razona, el toolkit ejecuta lectura, análisis y reportes deterministas.

Este documento es el **contrato formal del agente** (complementa `SKILL.md` que es el contrato del skill): qué pregunta acepta, qué retorna, qué garantiza, qué NO hace, latencia esperada, casos no cubiertos, política de confidence.

---

## 1. Arquitectura operativa

```
┌──────────────────────────────────────────────────────┐
│   LLM cliente (Claude Code / Claude API / otro)      │
│   - Razonamiento, planificación, lenguaje natural    │
│   - Decide qué tool invocar                          │
└──────────────────────┬───────────────────────────────┘
                       │ invoca
                       ▼
┌──────────────────────────────────────────────────────┐
│   rockwell_comprehender (toolkit determinístico)     │
│   - 14+ APIs analíticas                              │
│   - Agent.ask determinístico (8 patterns)            │
│   - Stack mínimo Python 3.10+ stdlib + openpyxl      │
└──────────────────────┬───────────────────────────────┘
                       │ lee
                       ▼
┌──────────────────────────────────────────────────────┐
│   .L5X file (XML exportado de Studio 5000)           │
└──────────────────────────────────────────────────────┘
```

**Canales de invocación soportados** (versatilidad v0.7.4):
1. **Claude Code** — slash commands `/diagnose`, `/audit`, `/compare`, `/explain`, `/health`
2. **Python script / notebook** — `from rockwell_comprehender import load_project`
3. **CLI shell** — `python -m rockwell_comprehender ask|audit|compare|bench|version`
4. **Importable** desde otros toolkits Python

---

## 2. APIs públicas — el contrato

### 2.1 Carga

```python
load_project(path: str) -> Project
```

Carga un L5X y construye el modelo canónico en SQLite. Latencia esperada: 200 ms (CINTA), 400 ms (AQL), 6.5 s (CPPIM 410 modules).

### 2.2 Mapa Mental (capa 1)

```python
project.mapa_mental  # str (markdown), property
```

Síntesis estructurada del proyecto en ~800–6000 caracteres. Determinístico.

### 2.3 Búsqueda + lupa puntual

```python
project.search(query: str) -> list[SearchHit]
project.get_aoi(name: str) -> AOIDetail | None
project.get_routine(program: str, name: str) -> Routine | None
project.get_udt(name: str) -> UDTDetail | None
```

### 2.4 Tracer (trace causal)

```python
project.references_of(tag: str, scope=None) -> list[XrefEntry]
project.writers_of(tag: str, scope=None) -> list[XrefEntry]
project.readers_of(tag: str, scope=None) -> list[XrefEntry]
project.find_causal_path(from_tag, to_tag, max_depth=8, direction="back") -> list[Step]
project.trace_back(tag, depth=3, max_branches=20, scope=None) -> TraceNode
project.trace_forward(tag, depth=3, max_branches=20, scope=None) -> TraceNode
```

Cubre código RLL **y** ST (desde C.3 Sprint 1).

### 2.5 Análisis semántico

```python
project.identify_domain(query: str) -> list[DomainHit]
project.classify_tag(tag: Tag) -> TagRole
project.tag_dictionary(scope=None) -> list[(Tag, TagRole)]
project.classify_program(program: Program) -> ProgramRole
project.program_inference() -> list[(Program, ProgramRole)]
```

### 2.6 Asesor proactivo

```python
project.detect_smells() -> list[Smell]                  # 15 reglas
project.detect_motion_patterns() -> list[MotionPatternMatch]   # 8 patterns
```

### 2.7 Comparación entre proyectos

```python
from rockwell_comprehender.project_diff import diff_projects
diff_projects(p_old, p_new) -> ProjectDiff
```

### 2.8 Reporters

```python
to_markdown(project, output_path) -> str
to_excel(project, output_path) -> str
to_mermaid(project, kind: str) -> str
to_html_explorer(project, output_path) -> str
to_tdr_html(project, output_path) -> str
```

### 2.9 Agente determinístico (v0.7)

```python
project.ask(question: str) -> AgentResponse
```

Reconoce 8+ patrones de pregunta y mapea a secuencia de calls. **Sin LLM** — heurística regex + lexicón (DT-008). Si el patrón no se reconoce, retorna `confidence=0` con sugerencia de delegar al LLM cliente.

---

## 3. Garantías

### 3.1 Determinismo

**Misma input → misma output.** Verificable empíricamente:

```python
p = load_project("X.L5X")
r1 = p.ask("problema en empalme")
r2 = p.ask("problema en empalme")
assert r1.answer == r2.answer  # PASS — verificado v0.7.1
```

Aplica a TODAS las APIs del toolkit. NO aplica al LLM cliente que lo invoca.

### 3.2 Auditabilidad

```python
import os; os.environ["ROCKWELL_AUDIT"] = "1"
# o programáticamente:
from rockwell_comprehender.audit_log import enable_audit, instrument_project
enable_audit(session_id="my_session")
project = load_project("X.L5X")
instrument_project(project)
```

Cada call queda en `docs/Audit_trail/<session_id>.jsonl` con `{timestamp, project, api, args_summary, output_summary, duration_ms}`. Permite reproducir cualquier sesión paso a paso desde el log.

### 3.3 Honestidad técnica

Cuando el toolkit no puede responder:
- `identify_domain` retorna lista vacía si no hay match en lexicón.
- `agent.ask` retorna `confidence=0` con `pattern="unknown"` y sugerencia de delegar al LLM.
- `references_of` retorna lista vacía para tags huérfanos (no inventa).
- Excepciones se propagan visiblemente — no se ocultan.

### 3.4 Reproducibilidad cross-canal

Mismo `Project` desde Claude Code, script Python, o CLI produce mismos outputs. La presentación cambia (markdown/JSON/HTML), no la lógica.

---

## 4. Latencia esperada (baseline bench v0.6)

Medida sobre 3 L5X (CINTA 1.2MB, AQL 2.9MB, CPPIM 15MB):

| API | CINTA | AQL | CPPIM (peor) |
|-----|------:|----:|-------------:|
| `search` | 0.5 ms | 0.9 ms | 35 ms |
| `identify_domain` | 5 ms | 3 ms | 3 ms |
| `mapa_mental` | 8 ms | 18 ms | 485 ms |
| `tag_dictionary` | 25 ms | 103 ms | 232 ms |
| `to_markdown` | 26 ms | 164 ms | 516 ms |
| `detect_smells` | 55 ms | 400 ms | 1,113 ms |
| `program_inference` | 18 ms | 553 ms | 2,574 ms |
| `detect_motion_patterns` | 102 ms | 906 ms | 2,780 ms |
| `references_of` | 242 ms | 1,763 ms | 3,902 ms |
| `to_tdr_html` | 116 ms | 1,014 ms | 2,549 ms |
| `load_project` | 218 ms | 372 ms | 6,559 ms |
| `to_excel` | 679 ms | 3,248 ms | 7,385 ms |
| `to_html_explorer` | 536 ms | 6,487 ms | 20,241 ms |

**APIs interactivas** (chat — < 1 s incluso CPPIM): `identify_domain`, `mapa_mental`, `tag_dictionary`, `to_markdown`.

**APIs de batch** (1-20 s): `detect_smells`, `program_inference`, `detect_motion_patterns`, `references_of`, `to_tdr_html`, `to_excel`, `to_html_explorer`.

---

## 5. Patrones de `agent.ask`

| Pattern ID | Trigger keywords | Confidence típica |
|------------|------------------|------------------:|
| `splice_diagnosis` | empalme, splice, splicer, ctc | hasta 1.00 |
| `unwinder_diagnosis` | unwind, debobinador, uwm | hasta 0.90 |
| `dancer_diagnosis` | dancer, danzarín, tensión, dnc | hasta 0.80 |
| `safety_overview` | safety, seguridad, guardlogix, estop | 0.70-1.00 |
| `dead_code_audit` | código muerto, huérfano, orphan | 1.00 |
| `smell_audit` | smell, best practice, auditar, recomendación | 1.00 |
| `motion_overview` | motion, ejes, axis, servos, motores | 1.00 |
| `general_health` | salud, estado general, audit completo | 1.00 |
| `tag_explain` / `aoi_explain` / `program_explain` | "qué es/hace X" | depende del target |
| `unknown` | cualquier otra cosa | 0.00 |

Confidence < 0.5 → el agente sugiere delegar al LLM cliente.

---

## 6. Lo que el agente NO hace (intencional)

- **No genera código L5X** (DT-003).
- **No interpreta lenguaje natural complejo** — sin LLM embebido (DT-008). Para razonar sobre preguntas no triviales, delegar al LLM cliente.
- **No mantiene memoria entre invocaciones** — `agent.ask` es stateless.
- **No instala dependencias pesadas** (DT-008): sin embeddings, ML frameworks, servidores externos.
- **No accede a internet** — toda info viene del L5X y conocimiento curado offline.

---

## 7. Casos NO cubiertos (limitaciones honestas)

- **Caso paradigma Amantrini**: caso #1 (empalme) validado en Diatec (CINTA, AQL); para Amantrini (CPPIM) requiere caso paradigma propio (input v0.8).
- **Routines protegidas**: si el L5X tiene Source Protection, las routines tienen `code=""` — toolkit no puede analizarlas.
- **FBD (Function Block Diagram)**: no hay tokenizer. Routines FBD se ignoran. RLL+ST cubren >95% del parque.
- **JSR cross-program**: el dead-code asume convención clásica. JSR cross-program podría producir falsos positivos.
- **ACD parsing directo**: descartado por DT-001. Solo L5X exportados.

---

## 8. Política de confidence

| Confidence | Significa |
|-----------:|-----------|
| 1.00 | Match perfecto: regla activada exactamente o múltiples evidencias coincidentes |
| 0.85–0.99 | Match fuerte: heurística primaria activada, evidencia auxiliar consistente |
| 0.70–0.84 | Match moderado: keyword primario o evidencia secundaria suficiente |
| 0.50–0.69 | Match débil: heurística parcial; revisar evidence antes de actuar |
| 0.00–0.49 | Sin confianza: el toolkit sugiere delegar al LLM cliente |

---

## 9. Stack tecnológico (DT-008 vigente)

```python
dependencies = ["openpyxl"]  # única más allá de stdlib
```

**Stdlib usada:** `sqlite3`, `xml.etree`, `dataclasses`, `re`, `json`, `pathlib`, `argparse`, `time`, `tracemalloc`, `functools`, `uuid`, `os`, `sys`.

**Sin:** torch, faiss, sentence-transformers, langchain, llamaindex, MCP servers, agent frameworks, tiktoken.

---

## 10. Cómo verificar el contrato

### 10.1 Bench (Sprint 9)

```bash
PYTHONUTF8=1 python docs/Test/_bench.py
```

Esperado: **40/40 PASS** sobre 14 APIs × 3 L5X. Reporte: `docs/Test/_bench_report.md`.

### 10.2 Behavior tests (Sprint 10 v0.7.5)

```bash
PYTHONUTF8=1 python docs/Test/_behavior_tests.py
```

Esperado: ≥10 assertions específicos pasan deterministamente sobre los 3 L5X.

### 10.3 CLI

```bash
python -m rockwell_comprehender version
python -m rockwell_comprehender audit parque_l5x/CINTA_LAMINADA_M2_2024.L5X
python -m rockwell_comprehender ask "problema en empalme" --project parque_l5x/CINTA_LAMINADA_M2_2024.L5X
```

---

## 11. Histórico de versiones

- **v0.1** (2026-05-03 cerrada) — Lectura estructural + Mapa Mental + reporters MD/Excel/Mermaid.
- **v0.2** (2026-05-03 implementada) — Tracer xref + cross-AOI traversal.
- **v0.3** (2026-05-06 cerrada) — instruction_library 38 entries + identify_domain.
- **v0.4** (2026-05-06 cerrada) — motion_patterns nivel-2 (8 detectores).
- **v0.5** (2026-05-06 cerrada) — tag_dictionary + program_inference + project_diff.
- **v0.6** (2026-05-06 cerrada) — test bench 40/40 PASS.
- **v0.7** (2026-05-07 cerrada) — agent.ask determinístico + slash commands + audit log + CLI + AGENT_CONTRACT.

---

## 12. Cómo extender el contrato

Si emerge una capacidad nueva (ej. caso paradigma Amantrini):
1. Documentar DT nueva en `docs/01_Decisiones_Tecnicas.md` con justificación.
2. Implementar módulo en `rockwell_comprehender/`.
3. Agregar wrapper en `Project` (`model.py`).
4. Agregar test al bench (`docs/Test/_bench.py`).
5. Agregar behavior test (`docs/Test/_behavior_tests.py`).
6. Actualizar este contrato con API nueva + latencia.

DTs vigentes (DT-001 a DT-010) son ley. Extensiones que las contradigan deben proponerse como DT-N que las supersede explícitamente.

---

*Contrato vivo. Última actualización: 2026-05-07 al cierre del Sprint 10. Próxima revisión: cuando v0.8 abra (caso paradigma Amantrini, según decisión del owner).*
