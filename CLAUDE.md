# Claude Code — Rockwell Comprehender

Reglas y contexto operativo para cualquier chat de Claude Code trabajando en este proyecto.

## Contexto del proyecto

- **Proyecto:** `rockwell-comprehender` — toolkit Python para comprensión profunda de proyectos Studio 5000 (archivos `.L5X`) con la depth de un ingeniero senior. Visión completa: [docs/00_Vision_y_Roadmap.md](docs/00_Vision_y_Roadmap.md).
- **Stack:** Python 3.10+ con stdlib (`sqlite3`, `xml.etree`, `dataclasses`) + `openpyxl`. Stack mínimo per **DT-008**.
- **Estructura real:**
  - `rockwell_comprehender/` — paquete principal (`loader`, `model`, `mapamental`, `navigator`, `tracer`, `patterns`, `tokenizer`, `instruction_library`, `fault_code_library`, `reporters`)
  - `parque_l5x/` — fuente de verdad de archivos L5X (algunos grandes en `.gitignore` por IP de terceros)
  - `docs/` — bitácora viva: visión, decisiones técnicas (`01_Decisiones_Tecnicas.md`), arquitectura, casos, hallazgos, backlog
  - `reportes_generados/` — outputs de los reporters (gitignored)

## Lectura obligatoria al inicio de cada sesión

Antes de proponer o ejecutar cualquier trabajo:

1. [docs/00_Vision_y_Roadmap.md](docs/00_Vision_y_Roadmap.md) — visión, niveles N1/N2/N3, criterios de éxito
2. [docs/01_Decisiones_Tecnicas.md](docs/01_Decisiones_Tecnicas.md) — DT-001 a DT-010 (lectura completa, son ley del proyecto)
3. [docs/HANDOFF_v01_to_N2.md](docs/HANDOFF_v01_to_N2.md) — estado al cierre de v0.1 + antipatrones documentados
4. [docs/Backlog.md](docs/Backlog.md) — items técnicos abiertos
5. La auditoría más reciente en `docs/05_*.md` (si existe) — estado actual de capacidades

## Capacidades activas

Tres habilidades disponibles en sesiones de este directorio:

1. **Paquete `rockwell_comprehender` v0.1+** — el deliverable real del proyecto. Carga L5X, genera Mapa Mental, búsqueda en código, lupa puntual, reporters MD/Excel/Mermaid. Validado contra 2 L5X reales (CINTA, AQL).
2. **NotebookLM skill** — query a Google NotebookLM (cuenta Pro Softys) para Q&A autoritativo sobre 6 manuales Rockwell. Vive en `~/.claude/skills/notebooklm/`, fuera del paquete. Doc operativa: [docs/Inf Fase 3/NotebookLM_Skill_Instrucciones_Operativas.md](docs/Inf%20Fase%203/NotebookLM_Skill_Instrucciones_Operativas.md).
3. **Memoria persistente del proyecto** — `~/.claude/projects/c--Master-Project-rockwell-comprehender/memory/` se carga automáticamente. Contexto de continuidad entre sesiones.

## Reglas absolutas

- **Nunca commit sin confirmación explícita previa del usuario.** Regla absoluta del owner. Se aplica a cualquier `git commit/push/merge/rebase/reset`. No hay excepciones por "cambio trivial" ni por "task del plan". Read-only git (`status`, `log`, `diff`, `show`, `blame`) sí puede correr libre.
- **Nunca agregar dependencias al `pyproject.toml` sin validación empírica** contra al menos 2 L5X reales (HANDOFF antipatrón #1; razón: aprendizaje DT-010 con `l5x` library).
- **Nunca declarar algo "validado" en un solo caso.** Mínimo 2 L5X de arquitectura distinta (HANDOFF antipatrón #2).
- **Nunca crear stubs vacíos para funcionalidad futura** (DT-009). El código en disco refleja lo implementado en la versión actual; documentación arquitectónica describe la visión completa.
- **Nunca inventar tags / AOIs / rutinas.** Si no aparece en `project.search()`, responder "no encuentro X" sin variantes alucinatorias.
- **Nunca instalar infraestructura especulativa** que viole DT-003 / DT-008 (sin embeddings vectoriales, sin frameworks ML, sin servidores externos, sin MCP servers pesados, sin Studio5000-AI-Assistant style stack). Lección dura 2026-05-03 documentada.

## Lecciones operativas críticas

- **NotebookLM es estrictamente serial.** Su skill usa Patchright con un único perfil de browser → 2+ queries concurrentes corrompen el state y rompen auth. Para batch: 1 subagent que itera con `delay 2-3s` entre llamadas.
- **Reportes/tests intermedios → `docs/Test/`** (no en raíz).
- **Documentación como subproducto.** Cada decisión técnica se anota inmediatamente en `01_Decisiones_Tecnicas.md` con justificación. Una decisión sin razón documentada es una decisión que se va a cuestionar después sin contexto.
- **Validación contra archivos reales > diseño en abstracto.** Cada componente nuevo se ejercita contra CINTA + AQL antes de declararlo funcional.

## Filosofía del proyecto

(condensado de [docs/00_Vision_y_Roadmap.md](docs/00_Vision_y_Roadmap.md) sec 4)

1. **Construcción gradual.** No comprometer stack pesado antes de validar necesidad.
2. **Cada decisión documentada** en bitácora viva con justificación.
3. **Validación contra casos reales** del parque, no demos sintéticos.
4. **Reuso pragmático.** Aprovechar lo maduro (`l5x`-style libraries solo si demuestran valor empírico — DT-010 mostró que stdlib basta).
5. **Honestidad técnica.** Decir lo que no funciona, lo que falta, lo que tiene riesgo. Sin sobreventa.
6. **Arquitectura limpia desde día uno.** Paquete instalable con interfaces claras, no scripts sueltos.

## Casos de uso prioritarios

(de [docs/03_Casos_de_Uso_Reales.md](docs/03_Casos_de_Uso_Reales.md))

| # | Caso | Estado |
|---|------|--------|
| 1 | **Empalme con velocidad excesiva** (CASO PARADIGMA) | 🟡 Test funcional pendiente — ÚNICO criterio v0.1 abierto |
| 2 | Auditoría rápida de proyecto desconocido | ✅ v0.1 |
| 3 | Comparación entre proyectos | ⚠️ Manual en v0.1, automático en v0.2 |
| 4 | Plan migración K6000→K5700 | ✅ v0.1 (BoM en Excel) |
| 5 | Detección código muerto | ⚠️ Parcial v0.1, completo v0.2 |
| 6 | Documentación técnica TDR | ✅ v0.1 |

## Seguridad

- Nunca hardcodear credentials, API keys, secrets en código fuente.
- Nunca commitear `.env` o cualquier archivo con secrets.
- Nunca usar flags `--no-verify`, `--no-gpg-sign`, etc. salvo petición explícita del usuario.
- Validar entrada de usuario en boundaries del sistema; sanitizar paths para prevenir directory traversal.
