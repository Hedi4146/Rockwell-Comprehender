# Backlog técnico — Rockwell Comprehender

Issues identificados durante validación + áreas de mejora detectadas, priorizadas por impacto. Vivos hasta que se cierren con commit/PR/decisión documentada.

---

## 1. Patterns Capa C: cobertura sesgada hacia Amantrini moderno

**Detectado:** Test L5X paralelo, 2026-05-03 (3 corridas, los 3 reports concuerdan).

**Síntoma:** Patterns Capa C de `rockwell_comprehender/patterns.py` detecta **43 zonas** en CPPIM (Amantrini Studio v33), **1-2 zonas** en CINTA y AQL (Diatec legacy + Diatec moderno).

**Implicación:** Si el toolkit se aplica a PLCs Diatec legacy de la migración K6000→K5700 (la mayoría de los casos reales del proyecto), las heurísticas no detectan la estructura. Output útil queda atrofiado para el caso de uso principal.

**Material para investigar:**
- `docs/Análisis/L5X_baseline/report_cinta.md` (Diatec legacy, 12 AOIs zombie)
- `docs/Análisis/L5X_baseline/report_aql.md` (Diatec moderno)
- `docs/Análisis/L5X_baseline/report_cppim.md` (Amantrini, ProtectedRoutine + raC_*)

**Acción sugerida:** Ampliar heurísticas de `patterns.py` con signatures Diatec legacy. Investigar qué tokens/estructuras distinguen Diatec legacy vs Diatec moderno vs Amantrini. Posiblemente refactor de Capa C a sistema de heurísticas pluggable por OEM.

**Priority:** **medium** — afecta calidad del análisis para el caso de uso principal del proyecto, pero no bloquea uso.

**Owner:** TBD

---

## 2. PDF Extractor pipeline para curación de instrucciones (deferred)

**Detectado:** Sesión 2026-05-03, tras validar workflow NotebookLM batch query.

**Síntoma:** El workflow de curación actual depende 100% de NotebookLM (cuenta Pro Softys + browser Patchright + Google Cloud). Funciona bien (~1 min/instr en batch validado), pero tiene dependencias externas no controladas:
- Cuenta Google + términos de uso pueden cambiar
- Browser Patchright es flakey (atascado ocasional)
- 1er intento de batch tuvo sustitución silenciosa (NotebookLM devolvió 5 instr distintas a las pedidas)
- Cap de output token de Gemini desconocido — limita tamaño de batch
- Solo accesible desde la máquina con cuenta autenticada

**Implicación:** No bloqueante hoy (workflow funciona), pero crea single-point-of-failure operativo + impide que otros usuarios del toolkit curen sus propias instrucciones sin acceso a la cuenta NotebookLM Pro.

**Acción sugerida (pipeline alternativo):**
1. Descargar localmente todos los PDFs del corpus actual (20 manuales) a `docs/manuals/` (gitignored — son IP de Rockwell, no se versionan).
2. Build de un módulo `tools/instruction_curator/` con:
   - `pdf_extractor.py` (`pymupdf` o `pdfplumber`): extrae secciones por nombre de instrucción usando TOC del PDF
   - `llm_structurer.py`: llamada batch a Sonnet/Haiku via `anthropic` SDK con texto extraído → JSON estructurado
   - `code_generator.py`: JSON → entries `InstructionMetadata` Python
   - `cli.py`: `python -m tools.instruction_curator.curate <pub> <instr_name>...`
3. Validar contra entry MAM (ground truth NotebookLM-curated) que el output auto-generado matche al menos 90% del schema.
4. Una vez validado: paralelizable, offline, reproducible, sin dependencia NotebookLM.

**Triggers para retomar (cualquiera de estos justifica la inversión ~2-4 hrs):**
- Library escala a 25+ entries totales (compounding empieza a importar)
- Library scope se expande de "parque actual" a "todo Rockwell motion+safety+general"
- Sustitución silenciosa NotebookLM se vuelve crónica (>10% de queries)
- Browser Patchright se cae 2+ veces consecutivas en una sesión
- Necesidad de integrar curación en CI/CD del repo (auto-actualización cuando aparezca nueva pub Rockwell)
- Distribución del toolkit a otros usuarios sin acceso a la cuenta NotebookLM Pro Softys
- Necesidad de procesar PDFs propios que NO podemos subir a NotebookLM (NDAs / IP cliente)

**Análisis costo/beneficio actual (2026-05-03):**
- Para scope ~30 instr (parque actual): NotebookLM gana (~30 min vs 2.5+ hrs build C).
- Para scope ~100+ instr (todo Rockwell): C gana (~3-5 hrs vs 5+ hrs B).
- C tiene además value estratégico (independencia, reproducibilidad, distribución).

**Priority:** **low** (no bloqueante). Bajar a **medium** cuando se cumpla algún trigger.

**Owner:** TBD (pendiente decisión Hedi cuando aplique algún trigger)

---

## Convenciones de este backlog

- Cada entry tiene **Detectado** (cuándo/cómo se descubrió), **Síntoma** (observable), **Implicación** (por qué importa), **Acción sugerida** (próximo paso concreto), **Priority** (high/medium/low/very low), **Owner** (TBD si no hay dueño asignado).
- Cuando un issue se cierra: mover a sección "Cerrados" con fecha de cierre + commit/PR/decisión.
- Issues que requieren múltiples sub-tareas se rompen en un sub-backlog dentro de la misma entry.
- No es sustituto de un tracker formal (Linear, GitHub Issues). Es captura ligera para que los hallazgos no se enterren en chat history.

---

## Cerrados

_(vacío hasta que se cierre el primero)_
