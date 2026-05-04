# Claude Code — Rockwell Comprehender (Python + RuFlo V3)

Reglas y contexto operativo para cualquier chat de Claude Code trabajando en este proyecto.

## ⚠️ LECTURA OBLIGATORIA AL INICIO DE CADA SESIÓN

Antes de proponer o ejecutar cualquier trabajo en este repo, **leer**:

1. **[`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md)** — fuente de verdad operativa con phases/milestones/tasks ejecutables, scoreboard, política de commit baked-in, anti-deviation rules. **Si dudás de qué hacer, está acá.**
2. Sección 0 del plan (Scoreboard) → ver % de cada phase, identificar próxima task NO marcada `[x]`.
3. Sección 2 del plan (Reglas anti-deviation) → 5 preguntas obligatorias antes de empezar.

**Si una tarea propuesta NO está en el plan (alguna phase) y NO es trivial → PARAR, preguntar al owner.** No agregar al plan unilateralmente.

## Política de commits (override del global para este proyecto)

El owner autorizó commits automáticos cuando una task del plan cumple sus acceptance criteria. **NO preguntar al owner por cada commit que sigue el plan.** El mensaje del commit está definido EN la task.

**SÍ requiere confirmación explícita (sin excepción):**
- Push a remote (`git push`)
- Cambios fuera del scope de la task actual (deviation)
- Reverts, rebases, force-push, branch deletes
- Modificación de archivos sensibles (`settings.json`, `.gitignore`, `pyproject.toml` deps)
- Operaciones destructivas de filesystem

**Lección dura 2026-05-03:** una sesión completa se desvió ~3 hrs hacia trabajo tangencial (curación de fault codes K5700) que no movía la aguja del objetivo. El plan existe para prevenir esto. Y el patrón "preguntar por cada commit" creaba interrupciones innecesarias — ahora la política está en el plan.

## Contexto del proyecto

- **Proyecto:** `rockwell-comprehender` — toolkit Python para análisis estático de proyectos Studio 5000 (archivos `.L5X`).
- **Stack:** Python 3.x, paquete `rockwell_comprehender/` (no JS/Node — ignora cualquier referencia a npm/test/build de origen genérico).
- **Estructura real:**
  - `rockwell_comprehender/` — código fuente del paquete
  - `parque_l5x/` — fuente de verdad de archivos L5X (algunos grandes están en `.gitignore` por IP de terceros)
  - `docs/` — documentación e investigación (`docs/Inf Fase 3/`, `docs/Test/` para reportes intermedios)
  - `reportes_generados/` — outputs (gitignored)
  - `.claude/`, `.claude-flow/`, `.swarm/`, `ruvector.db`, `.mcp.json`, `daemon.pid` — runtime de Claude Code + RuFlo (gitignored)

## Capacidades activas en este proyecto

Cuatro habilidades desbloqueadas para sesiones en este directorio:

1. **NotebookLM skill** — query a Google NotebookLM (cuenta Pro Softys) para Q&A sobre 6 manuales Rockwell (Logix 5000, Kinetix 5700, motion EtherNet/IP / SERCOS / Analog). Doc: [docs/Inf Fase 3/NotebookLM_Skill_Instrucciones_Operativas.md](docs/Inf%20Fase%203/NotebookLM_Skill_Instrucciones_Operativas.md).
2. **RuFlo MCP** (Fase 2 / full init) — ~241 herramientas `mcp__ruflo__*` deferred, 98 agent definitions en `.claude/agents/`, 33 skills, 10 commands, hooks activos, AgentDB vectorial. Doc: [docs/Inf Fase 3/Ruflo_MCP_Instrucciones_Operativas.md](docs/Inf%20Fase%203/Ruflo_MCP_Instrucciones_Operativas.md).
3. **Agent Teams** (nativo experimental Claude Code) — `TeamCreate`/`SendMessage`/`TeamDelete` para teammates persistentes con comunicación bidireccional + plan approval + worktrees aislados. Habilitado via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` en settings.json. Doc: [docs/Inf Fase 3/Agent_Teams_Instrucciones_Operativas.md](docs/Inf%20Fase%203/Agent_Teams_Instrucciones_Operativas.md).
4. **Memoria persistente** — `C:\Users\LENOVO\.claude\projects\c--Master-Project-rockwell-comprehender\memory\` se carga automáticamente y se importa a AgentDB vía hook `auto-memory-hook.mjs import` en SessionStart.

## Lecciones operativas críticas (no reaprender por las malas)

- **NotebookLM es estrictamente serial.** Su skill usa Patchright con un único perfil de browser → 2+ queries concurrentes corrompen el state y rompen auth. Para batch: 1 subagent que itera con `delay 2-3s` entre llamadas. **NUNCA** spawnees N subagents concurrentes contra NotebookLM.
- **Ruflo no ejecuta — coordina.** `agent_spawn` registra metadata en AgentDB pero no corre código. El ejecutor real es el **Task tool nativo de Claude Code** (o `claude -p` externo). Ruflo aporta tracking + persistencia + memoria semántica encima.
- **Patrón ortogonal correcto:** para paralelización real, Task tool sobre tareas que **no comparten recurso** (ej. analizar 4 L5X distintos). Encima, registrar en Ruflo (`task_create` × N) solo para tracking.
- **Reportes/tests intermedios** → `docs/Test/` (no en raíz).
- **Nunca commitear sin confirmación explícita previa del usuario.** Regla absoluta — incluso si el cambio parece trivial.

## Discovery de tools (deferred)

Las 241 tools de ruflo aparecen en system-reminders por nombre pero su schema NO está cargado. Antes de invocar, cargar:

```
ToolSearch("+ruflo")                                           → primeras N tools
ToolSearch("swarm")                                            → swarm_init/status/health/shutdown
ToolSearch("memory_search")                                    → memory_search, memory_search_unified, memory_retrieve
ToolSearch("hive-mind")                                        → consensus + worker spawn
ToolSearch("select:mcp__ruflo__<name1>,mcp__ruflo__<name2>")   → carga directa por nombre
```

## Concurrencia y batching

- **1 mensaje = todas las operaciones relacionadas.** Si lanzas N tool calls independientes, mételos en un solo mensaje con N `<function_calls>` en paralelo.
- Batchea Bash, Read, Edit, Write cuando sean independientes — no las hagas secuenciales sin necesidad.
- **Excepción NotebookLM:** las queries van serializadas estrictas (ver lección crítica arriba).

## Swarm orchestration (cuando aplica)

- Topology default recomendada: `hierarchical` o `hierarchical-mesh` para 5-15 agentes; `mesh` para 3-5 con paridad.
- Strategy `specialized` para roles bien diferenciados (anti-drift).
- **Después de spawn de agentes vía Task tool, NO hagas polling.** Trust the agents to return — revisa todos los results juntos al final.
- Ruflo registra el swarm en `.claude-flow/` para persistencia y retomabilidad — útil si el chat crashea a mitad.

## Agentes disponibles vía Task tool

Tras el init full hay **98 agent definitions en 23 categorías** dentro de `.claude/agents/`. Algunos types útiles:
- **Core:** `coder`, `reviewer`, `tester`, `planner`, `researcher`
- **Specialized:** `code-analyzer`, `system-architect`, `performance-engineer`, `memory-specialist`, `security-architect`, `security-auditor`
- **Coordination:** `hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`
- **GitHub:** `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`
- **SPARC:** `sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`
- **Test:** `tdd-london-swarm`, `production-validator`

Para listado completo: `Glob ".claude/agents/**/*.md"`. Cualquier string sirve como `subagent_type` custom; los listados arriba traen prompts especializados.

## Memory bridge (Claude ↔ AgentDB)

- Tras SessionStart, el hook `auto-memory-hook.mjs import` debería sincronizar `~/.claude/projects/.../memory/*.md` con AgentDB.
- Si `memory_bridge_status` reporta `not-synced`, ejecutar manualmente: `mcp__ruflo__memory_import_claude({allProjects: true})`.
- Búsqueda semántica cross-project: `mcp__ruflo__memory_search_unified`.

## Seguridad

- **Nunca** hardcodear credentials, API keys, secrets en código fuente.
- **Nunca** commitear `.env` o cualquier archivo con secrets.
- **Nunca** usar flags `--no-verify`, `--no-gpg-sign`, etc. salvo petición explícita del usuario.
- Validar entrada de usuario en boundaries del sistema; sanitizar paths para prevenir directory traversal.

## Operaciones git

- **Confirmación explícita SIEMPRE antes de commit/push/merge/rebase/reset.** El usuario ha establecido esta regla como absoluta. No hay excepciones por "cambio trivial".
- Read-only git (status, log, diff, show, blame) puede correr sin pedir permiso.
- Backups generados por agentes (`*.bak.*`) están gitignorados — no se versionan.

## Referencias rápidas

- **Doc operativa NotebookLM:** [docs/Inf Fase 3/NotebookLM_Skill_Instrucciones_Operativas.md](docs/Inf%20Fase%203/NotebookLM_Skill_Instrucciones_Operativas.md)
- **Doc operativa Ruflo MCP:** [docs/Inf Fase 3/Ruflo_MCP_Instrucciones_Operativas.md](docs/Inf%20Fase%203/Ruflo_MCP_Instrucciones_Operativas.md)
- **Investigación skills Studio 5000:** [docs/Inf Fase 3/Skills_Claude_Studio5000_Investigacion.md](docs/Inf%20Fase%203/Skills_Claude_Studio5000_Investigacion.md)
- **CAPABILITIES de RuFlo:** [.claude-flow/CAPABILITIES.md](.claude-flow/CAPABILITIES.md)
- **Memoria persistente del proyecto:** `C:\Users\LENOVO\.claude\projects\c--Master-Project-rockwell-comprehender\memory\`
