# 02 · ARQUITECTURA DEL SKILL

Diseño técnico del paquete `rockwell_comprehender` y del skill que lo expone a Claude.

**Estado:** Borrador inicial — se refina durante construcción de v0.1.

---

## Visión arquitectónica

```
┌─────────────────────────────────────────────────────────────┐
│         CLAUDE (web, code, o web app futura)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │  invoca
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         SKILL: rockwell-project-comprehender                 │
│         ────────────────────────────────────                 │
│         SKILL.md instruye cómo usar el paquete               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │  importa
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         PAQUETE PYTHON: rockwell_comprehender                │
│                                                              │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐  ┌──────────┐    │
│  │ loader   │→ │  model  │→ │mapamental │→ │navigator │    │
│  └──────────┘  └─────────┘  └───────────┘  └──────────┘    │
│                                                 ↓           │
│                                          ┌────────────┐    │
│                                          │ tracer v0.2│    │
│                                          └- - - - - - ┘    │
│                                                              │
│  ┌──────────────┐                ┌──────────┐                │
│  │   reporters  │                │   api    │                │
│  └──────────────┘                └──────────┘                │
└─────────────────────────────────────────────────────────────┘
                       │
                       │  lee/escribe
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  ARCHIVOS:  L5X de entrada    SQLite de modelo               │
│             Mapa Mental .md   Reportes generados             │
└─────────────────────────────────────────────────────────────┘
```

---

## Estructura del paquete `rockwell_comprehender`

```
rockwell_comprehender/
├── __init__.py              ← v0.1 — Exports públicos
├── loader.py                ← v0.1 — Carga L5X y construye modelo
├── model.py                 ← v0.1 — Modelo canónico (dataclasses + SQLite)
├── mapamental.py            ← v0.1 — Genera Mapa Mental general (Capa 1)
├── navigator.py             ← v0.1 — Mapas funcionales y lupa (Capas 2-3)
├── reporters/               ← v0.1 — Generadores de salida
│   ├── __init__.py
│   ├── markdown.py          ← Salida MD legible
│   ├── excel.py             ← Salida XLSX para entregables
│   └── mermaid.py           ← Diagramas Mermaid
└── api.py                   ← v0.1 — API pública limpia

# Módulos planeados para v0.2+:
# ├── tracer.py               ← v0.2 — Trace de dependencias (Capa 4)
# └── tokenizer/
#     └── rll_tokenizer.py    ← v0.2 — Tokenizer de rungs ladder
```

---

## Módulos en detalle

### `loader.py` — Carga de proyectos

**Propósito:** Punto de entrada para cargar un L5X y dejarlo listo para análisis.

**Interfaz pública:**
```python
def load_l5x(filepath: str) -> Project:
    """Carga un L5X y retorna un Project listo para análisis."""
```

**Responsabilidades:**
- Validar que el archivo es L5X válido
- Detectar versión, schema, controlador
- Delegar parsing detallado a la librería `l5x` de jvalenzuela
- Construir el modelo canónico en `model.py`
- Persistir en SQLite intermedia para consultas eficientes
- Disparar la generación del Mapa Mental

**Dependencias:** `l5x` (PyPI), `sqlite3` (stdlib)

---

### `model.py` — Modelo canónico

**Propósito:** Representación interna del proyecto, accesible vía dataclasses y queryable vía SQLite.

**Esquema SQLite:**

```sql
-- Proyectos cargados (puede haber múltiples en la misma sesión)
CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    name TEXT,
    filepath TEXT,
    software_version TEXT,
    schema_revision TEXT,
    target_name TEXT,
    target_type TEXT,
    loaded_at TIMESTAMP
);

-- Controlador del proyecto
CREATE TABLE controller (
    project_id INTEGER REFERENCES project(id),
    name TEXT,
    processor_type TEXT,
    major_rev INTEGER,
    minor_rev INTEGER,
    project_creation_date TEXT,
    last_modified_date TEXT,
    comm_path TEXT,
    project_sn TEXT
);

-- Modules I/O (jerárquico)
CREATE TABLE module (
    project_id INTEGER,
    name TEXT,
    catalog_number TEXT,
    parent_module TEXT,
    parent_slot INTEGER,
    major INTEGER,
    minor INTEGER,
    -- ports como JSON
    ports_json TEXT
);

-- DataTypes (UDTs custom)
CREATE TABLE datatype (
    project_id INTEGER,
    name TEXT,
    family TEXT,
    description TEXT
);

CREATE TABLE datatype_member (
    project_id INTEGER,
    datatype_name TEXT,
    member_name TEXT,
    member_datatype TEXT,
    dimension TEXT,
    hidden BOOLEAN,
    description TEXT
);

-- AOIs (Add-On Instructions)
CREATE TABLE aoi (
    project_id INTEGER,
    name TEXT,
    revision TEXT,
    description TEXT
);

CREATE TABLE aoi_parameter (
    project_id INTEGER,
    aoi_name TEXT,
    param_name TEXT,
    param_datatype TEXT,
    usage TEXT,  -- Input/Output/InOut
    description TEXT
);

-- Tags
CREATE TABLE tag (
    project_id INTEGER,
    scope TEXT,  -- 'controller' o nombre del programa
    name TEXT,
    datatype TEXT,
    dimensions TEXT,
    description TEXT,
    alias_for TEXT,
    external_access TEXT
);

-- Programs
CREATE TABLE program (
    project_id INTEGER,
    name TEXT,
    main_routine TEXT,
    fault_routine TEXT,
    description TEXT
);

-- Routines (con código completo embebido)
CREATE TABLE routine (
    project_id INTEGER,
    program_name TEXT,
    name TEXT,
    type TEXT,  -- RLL, ST, SFC, FBD
    description TEXT,
    code TEXT  -- texto completo del código
);

-- Tasks
CREATE TABLE task (
    project_id INTEGER,
    name TEXT,
    type TEXT,  -- CONTINUOUS, PERIODIC, EVENT
    rate INTEGER,
    priority INTEGER,
    watchdog INTEGER
);

CREATE TABLE task_program (
    project_id INTEGER,
    task_name TEXT,
    program_name TEXT
);

-- Cross-references derivadas (poblada por tracer.py en v0.2)
CREATE TABLE xref (
    project_id INTEGER,
    tag_name TEXT,
    used_in_program TEXT,
    used_in_routine TEXT,
    rung_number INTEGER,
    usage_type TEXT  -- read, write, both
);

-- Índice full-text para búsqueda en código
CREATE VIRTUAL TABLE code_fts USING fts5(
    project_id, program_name, routine_name, code,
    tokenize='porter unicode61'
);
```

**Interfaz pública:**
```python
@dataclass
class Project:
    id: int
    name: str
    controller: Controller
    modules: list[Module]
    datatypes: list[DataType]
    aois: list[AOI]
    tags: list[Tag]
    programs: list[Program]
    tasks: list[Task]
    
    def query(self, sql: str) -> list[dict]:
        """Query directo a la SQLite del modelo."""
    
    def find_tag(self, name: str) -> Tag | None: ...
    def find_routine(self, program: str, name: str) -> Routine | None: ...
    def find_aoi(self, name: str) -> AOI | None: ...
```

---

### `mapamental.py` — Generador del Mapa Mental (Capa 1)

**Propósito:** Producir el documento Markdown compacto (~800–1500 tokens) que Claude carga al inicio para tener visión estructural del proyecto.

**Interfaz pública:**
```python
def generate(project: Project) -> str:
    """Genera el Mapa Mental del proyecto en Markdown."""
```

**Estructura del Mapa Mental generado:**

```markdown
# {NombreProyecto} — Ficha del proyecto

## Identidad
- Controlador: {processor_type} {major}.{minor}
- Software: {software_version}
- Última modificación: {last_modified}
- Función: {inferida del nombre y módulos}

## Arquitectura física
{tabla de módulos con jerarquía + IPs}

## Arquitectura lógica
- {N} Tasks: {breakdown}
- {N} Programs, {N} Routines, {N} AOIs
- Framework detectado: {AHT_, Lp_, etc.}

## Mapa funcional de ejes (si tiene motion)
{tabla por eje con función inferida}

## Patrones de código
{patrones de naming detectados}
{AOIs principales y su rol}

## Issues / observaciones
{detecciones automáticas: AOIs duplicadas, código muerto sospechoso, etc.}
```

**Heurísticas de generación:**
- Detección de framework por prefijos consistentes
- Inferencia de función de eje por nombre de tag y AOI invocada
- Detección de duplicados de AOI por similitud de nombre
- Detección de programas/rutinas vacíos o stubs

---

### `navigator.py` — Mapas funcionales y lupa (Capas 2-3)

**Propósito:** Permitir profundización dirigida cuando una pregunta lo requiere.

**Interfaz pública:**
```python
def search_code(project: Project, query: str) -> list[CodeMatch]:
    """Búsqueda full-text en código de rutinas."""

def get_routine_code(project: Project, program: str, routine: str) -> str:
    """Lupa puntual: código completo de una rutina."""

def get_aoi_full(project: Project, aoi_name: str) -> AOIDetail:
    """Lupa puntual: AOI con params, locals, código de rutinas internas."""

def get_udt_full(project: Project, udt_name: str) -> UDTDetail:
    """Lupa puntual: UDT con todos sus members."""

def functional_map(project: Project, domain: str) -> FunctionalMap:
    """Mapa funcional para un dominio (v0.3)."""
```

---

### `reporters/` — Generadores de salida

**Propósito:** Producir entregables visibles para Hedi como subproducto del análisis.

- `markdown.py`: Mapa Mental, reportes ejecutivos, documentación
- `excel.py`: BoMs, listados de tags, configuraciones de eje (multi-hoja)
- `mermaid.py`: Diagramas de arquitectura, flowcharts de lógica

---

### `api.py` — API pública limpia

**Propósito:** Punto de entrada principal del paquete. Lo que importará una futura web app o CLI.

```python
from rockwell_comprehender import load_project

# Caso de uso típico
project = load_project("CINTA_LAMINADA_M2_2024.L5X")

print(project.mapa_mental)  # texto markdown ~800–1500 tokens

routine = project.get_routine("Axis", "Drive_Rolls")
print(routine.code)

results = project.search("Dancer")
for r in results:
    print(f"{r.location}: {r.snippet}")

# v0.2+
trace = project.trace_back("M3Data.Setpoint", depth=5)
trace.render_mermaid()
```

---

## Módulos planeados (v0.2+)

> Esta sección documenta módulos NO implementados en v0.1. Se construyen al iniciar v0.2, según DT-009 (no se crean stubs vacíos para versiones futuras).

### `tracer.py` — Trace de dependencias (Capa 4) — v0.2

**Propósito:** Responder preguntas causales tipo "¿de dónde viene este valor?".

**Interfaz pública prevista:**
```python
def writers_of(project: Project, tag_name: str) -> list[CodeLocation]:
    """Dónde se escribe este tag."""

def readers_of(project: Project, tag_name: str) -> list[CodeLocation]:
    """Dónde se lee este tag."""

def trace_back(project: Project, tag_name: str, depth: int = 3) -> TraceTree:
    """Cadena causal hacia atrás: ¿qué influye en este tag?"""

def trace_forward(project: Project, tag_name: str, depth: int = 3) -> TraceTree:
    """Cadena causal hacia adelante: ¿qué afecta este tag?"""
```

**Estrategia prevista:** Tokenización de código RLL/ST + análisis de uso de operandos. Inspirado en `l5x2c` pero más simple. Requiere el módulo `tokenizer/rll_tokenizer.py` (también v0.2).

**Soporte de schema en v0.1:** La tabla `xref` se crea vacía en el schema SQLite desde v0.1 (DT-009), de modo que `tracer.py` solo agrega datos sin requerir migración.

---

## Estructura del SKILL.md

El archivo `SKILL.md` que registra el skill ante Claude tendrá estructura:

```yaml
---
name: rockwell-project-comprehender
description: |
  Comprende profundamente proyectos Rockwell Studio 5000 / RSLogix 5000
  cargando archivos L5X. Genera Mapa Mental general, permite navegación
  capa por capa, búsqueda en código, trace de dependencias. Úsalo cuando
  el usuario suba un L5X o pregunte sobre la arquitectura/lógica de un
  proyecto PLC Allen-Bradley.
---

# Rockwell Project Comprehender

## Cuándo usar este skill
[Trigger conditions]

## Cómo usarlo
[Workflow paso a paso]

## Capacidades
[Lista de queries y operaciones soportadas]

## Limitaciones honestas
[Lo que no puede hacer]

## Ejemplos
[Casos de uso reales]
```

El SKILL.md formal se redacta en la primera sesión del nuevo Project.

---

## Flujo de trabajo típico (v0.1)

```
1. Usuario sube L5X
   ↓
2. Claude llama load_project("archivo.L5X")
   ↓
3. Loader parsea con `l5x` → modelo canónico → SQLite
   ↓
4. Generador construye Mapa Mental
   ↓
5. Claude carga Mapa Mental a contexto y lo muestra al usuario
   ↓
6. Usuario hace preguntas
   ↓
7. Claude decide qué capa consultar:
   ├─ Pregunta estructural → responde desde Mapa Mental
   ├─ Pregunta sobre código específico → llama navigator.get_routine_code()
   ├─ Pregunta de búsqueda → llama navigator.search_code()
   └─ Pregunta causal (v0.2+) → llama tracer.trace_back()
```

---

## Consideraciones de testing

**Casos de prueba:**
1. CINTA_LAMINADA_M2_2024 (v20.01, 1768-L43, ~1.2 MB) — caso base
2. Algún proyecto G2 v24-v28 — validación cobertura
3. Algún proyecto G3 v32+ — validación cobertura
4. Caso de empalme — validación de comprensión causal

**Métricas de éxito:**
- Tiempo de carga de un L5X de 1-2 MB: < 5 segundos
- Mapa Mental generado coherente sin intervención manual
- Búsqueda full-text en código: < 100ms
- Caso de empalme se resuelve en ≤6 turnos (v0.1) / ≤2 turnos (v0.3)

---

*Borrador inicial. Se refina durante construcción.*

*Última actualización: 2026-05-01*
