# HANDOFF · v0.1 (Claude.ai web) → Nivel 2 (Claude Code)

**Documento de transición del proyecto Rockwell-Comprehender**

Para: Claude Code (la siguiente instancia que va a trabajar en este proyecto)
De: Claude.ai web (instancia que cerró v0.1)
Owner: Hedi Vásquez Mayor — Softys Colombia
Fecha de transición: 2026-05-02

---

## 0 · Lee esto primero — qué eres y qué no eres en este proyecto

Eres **Claude Code trabajando en un repo Git con un usuario senior técnico** (Hedi). El paquete `rockwell_comprehender` v0.1.0 ya está construido, validado y funcionando. Tu rol **no es construirlo desde cero** — es operarlo, refinarlo cuando aparezcan necesidades reales, y eventualmente extenderlo a v0.2.

**Estilo de trabajo que Hedi ya estableció con Claude.ai web** (replícalo):

1. **Honestidad técnica sobre todo.** Si algo no está claro, dilo. Si una idea suya tiene un problema, dilo. Si vas a hacer algo y no estás seguro, pregúntalo antes de ejecutar.

2. **Validación empírica antes de comprometer.** Esto es lex non scripta del proyecto — está formalizada en DT-010. No agregues dependencias al `pyproject.toml` sin haberlas ejercitado contra un archivo real primero. No declares algo "funcional" si solo lo probaste sintéticamente.

3. **Bitácora viva.** Cada decisión técnica relevante se documenta inmediatamente en `docs/01_Decisiones_Tecnicas.md` con justificación. Una decisión sin razón documentada es una decisión que se va a cuestionar después sin contexto.

4. **No expandas alcance unilateralmente.** Si Hedi te pide X, no entregues "X + Y + Z porque pensé que sería útil". Entrega X y, si crees que Y es valioso, lo propones explícitamente.

5. **Push back cuando aplica.** Si Hedi sugiere algo que técnicamente tiene un problema, dilo. La dinámica que funcionó hasta ahora es pares colaborando, no asistente complaciente.

---

## 1 · Estado al cierre de v0.1

### El paquete

`rockwell_comprehender` v0.1.0 — paquete Python instalable que comprende proyectos Rockwell Studio 5000 / RSLogix 5000 a partir de archivos `.L5X`.

**Capacidades:**
- Carga L5X arbitrario y construye modelo canónico en SQLite
- Genera Mapa Mental general (~800–1500 tokens) con identidad, arquitectura física/lógica, mapa funcional de ejes, patrones de código, observaciones automáticas
- Búsqueda full-text en código de rutinas
- Lupa puntual sobre rutinas, AOIs, UDTs específicos
- 3 reporters: Markdown completo, Excel multi-sheet, diagramas Mermaid (topology / iotree / tasks)
- Detección automática de inconsistencias estructurales (AOIs duplicadas, módulos sin nombre)

**Stack:** Python 3.10+, stdlib (sqlite3, xml.etree, dataclasses) + openpyxl. Sin más dependencias.

**Validado contra:**
- `CINTA_LAMINADA_M2_2024.L5X` (1.2 MB, RSLogix 5000 v20.01, CompactLogix 1768-L43, 4 ejes K6000 SERCOS)
- `AQL_M2.L5X` (2.9 MB, Studio 5000 v20.12, ControlLogix 1756-L61, 17 ejes productivos, 3 redes)

### Lo que está logrado de los criterios de éxito v0.1

Del documento `docs/00_Vision_y_Roadmap.md`:

| Criterio | Estado |
|----------|:------:|
| Cargo L5X arbitrario y produzco Mapa Mental coherente sin intervención | ✅ Validado en 2 arquitecturas distintas |
| Respondo preguntas estructurales sin fallar | ✅ search/get_routine/get_aoi funcionales |
| Genero reportes Markdown / Excel / diagramas Mermaid | ✅ Validado |
| **Caso de empalme se resuelve en ≤6 turnos de conversación** | 🟡 **PENDIENTE — test funcional definitivo** |

El test funcional del caso paradigma es **el primer trabajo prioritario en N2**.

---

## 2 · Cómo está organizado el repositorio

```
Rockwell-Comprehender/                    ← raíz del repo Git
│
├── README.md                             ← guía rápida del repo
├── pyproject.toml                        ← metadata, dependencies = [openpyxl]
├── .gitignore                            ← ignora reportes_generados, __pycache__, etc.
│
├── rockwell_comprehender/                ← el paquete (esto va al PYTHONPATH)
│   ├── __init__.py
│   ├── loader.py                         ← carga L5X → modelo SQLite
│   ├── model.py                          ← dataclasses + schema SQLite
│   ├── mapamental.py                     ← genera Mapa Mental general
│   └── reporters/
│       ├── __init__.py
│       ├── markdown.py                   ← reporte Markdown completo
│       ├── excel.py                      ← Excel multi-sheet (BoM)
│       └── mermaid.py                    ← diagramas (topology/iotree/tasks)
│
├── docs/                                 ← documentación del proyecto
│   ├── 00_Vision_y_Roadmap.md            ← visión, niveles, criterios éxito
│   ├── 01_Decisiones_Tecnicas.md         ← bitácora DT-001 a DT-010
│   ├── 02_Arquitectura_Skill.md          ← diseño técnico del paquete
│   ├── 03_Casos_de_Uso_Reales.md         ← casos catalogados
│   ├── 04_Investigacion_Previa.md        ← investigación + hallazgos
│   ├── HANDOFF_v01_to_N2.md              ← este archivo
│   ├── SKILL.md                          ← contrato del paquete
│   └── ejemplos/
│       ├── EJEMPLO_Mapa_Mental_CINTA_M2.md
│       └── EJEMPLO_Mapa_Mental_AQL_M2.md
│
├── parque_l5x/                           ← archivos L5X reales del parque Softys
│   ├── CINTA_LAMINADA_M2_2024.L5X        ← caso base de validación
│   ├── AQL_M2.L5X                        ← caso de generalización
│   └── ...                               ← (Hedi agrega más a medida que aparecen)
│
└── reportes_generados/                   ← outputs de los reporters (en .gitignore)
```

---

## 3 · Cómo arrancar la primera vez

### Paso 1 — Verificar que el repo está bien

```bash
cd Rockwell-Comprehender
ls
# Debes ver: README.md, pyproject.toml, rockwell_comprehender/, docs/, parque_l5x/

cat docs/01_Decisiones_Tecnicas.md | head -50
# Confirma que tienes la bitácora completa
```

### Paso 2 — Instalar el paquete en modo desarrollo

```bash
pip install -e . --break-system-packages
```

(O sin `--break-system-packages` si trabajas en virtualenv — recomendado pero no obligatorio en v0.1.)

Esto deja `rockwell_comprehender` importable desde cualquier lugar y los cambios se reflejan inmediatamente sin reinstalar.

### Paso 3 — Smoke test

```python
from rockwell_comprehender import load_project

project = load_project("parque_l5x/CINTA_LAMINADA_M2_2024.L5X")
print(project.mapa_mental)
```

**Esperado:**
- Carga en <1 segundo
- Mapa Mental ~870 tokens con secciones: Identidad, Arquitectura física (12 modules), Arquitectura lógica (4 tasks, 4 programs, 17 routines), Mapa funcional (7 ejes), Patrones, Issues (6 observations)

Si no coincide, **algo está mal** — no continúes hasta diagnosticar. Posibles causas: openpyxl no instalado, archivo L5X corrupto, paquete no instalado correctamente.

### Paso 4 — Smoke test del segundo caso

```python
project2 = load_project("parque_l5x/AQL_M2.L5X")
assert len(project2.modules) == 44
assert len(project2.tags) == 1401
print("✓ Segundo caso valida")
```

Si los dos smoke tests pasan, el paquete está operativo y puedes empezar a trabajar.

---

## 4 · Próximo trabajo prioritario — Test funcional del caso paradigma

### Por qué importa

Es el único criterio de éxito v0.1 que quedó pendiente. **Hasta no hacer este test, no sabemos si el paquete funciona como herramienta de diagnóstico real, solo sabemos que funciona como código.**

### El caso

Está descrito completo en `docs/03_Casos_de_Uso_Reales.md` (Caso #1). Resumen:

> "Tenemos problema en empalme: el debobinador arranca con mucha velocidad y se enreda al cargar el rollo nuevo."

El flujo esperado: localizar lógica de empalme → identificar cálculo de velocidad inicial → trazar inputs (diámetro inicial, posición danzarín, referencia máquina) → identificar que el diámetro es input HMI → concluir: probable error humano de carga.

**Criterio de éxito:** se resuelve en ≤6 turnos de conversación.

### Cómo hacerlo

**Opción A (más limpia):** abrir un chat NUEVO en Claude.ai web dentro del Project original, subir el L5X, y conversar simulando ser Hedi reportando el síntoma. Observar si Claude usa el skill correctamente.

**Opción B (en Code):** simular la conversación contra el paquete directamente:

```python
# Carga
project = load_project("parque_l5x/CINTA_LAMINADA_M2_2024.L5X")

# Turno 1: ver Mapa Mental
print(project.mapa_mental)

# Turno 3: leer el AOI relevante
aoi = project.get_aoi("AHT_CtcSplicer")
print(aoi.routines["Logic"].code)

# Turno 4: trazar origen del input HMI
hits = project.search("HmiRollDiameter")  # o el nombre real que aparezca
for h in hits: print(h.location, h.snippet)
```

**Reporte del test al final:**
- ¿Cuántos turnos? (objetivo: ≤6)
- ¿El paquete proporcionó la información necesaria sin friction?
- ¿Algún punto donde te ves forzado a hacer trabajo manual extra?
- ¿Hallazgos sobre el código del proyecto que valgan documentación?

Si revela limitaciones → input para v0.2.
Si funciona limpio → criterio de éxito v0.1 logrado, declaramos v0.1 oficialmente cerrado.

---

## 5 · Roadmap de Nivel 2

Después del test funcional, hay tres caminos posibles:

### Camino A — Refinamiento de v0.1.x

Si el test funcional reveló limitaciones específicas, las atacas como mejoras incrementales sin saltar a v0.2 todavía. Ejemplos plausibles:

- Mejorar inferencia funcional con más sustrings semánticos
- Detección de colisiones AOI por underscore/numeración (Hallazgo 3 diferido)
- Snippets de búsqueda más ricos (TODO ya anotado en `_first_match_snippet`)

### Camino B — Arrancar v0.2 (tracer.py)

Trace automático de dependencias. La capacidad central:

```python
project.writers_of("HmiRollDiameter")    # ¿quién escribe este tag?
project.readers_of("M3Data.Setpoint")    # ¿quién lo lee?
project.trace_back("V_new", depth=5)     # cadena causal hacia atrás
project.trace_forward("HmiRollDiameter") # qué se ve afectado
```

**Importante para v0.2:**
- La tabla `xref` ya existe vacía en SQLite desde v0.1 (DT-009)
- El módulo `tokenizer/rll_tokenizer.py` se crea cuando empiezas v0.2 (DT-009)
- Estrategia: tokenización de RLL + análisis de operandos. Inspirado en l5x2c pero más simple.
- Validar contra ambos L5X antes de cerrar v0.2

### Camino C — Análisis batch del parque

Usar el paquete v0.1 tal cual sobre múltiples L5X del parque para generar reportes ejecutivos masivos. Ejemplo:

```python
# Procesar todos los L5X de la carpeta
for l5x_path in Path("parque_l5x").glob("*.L5X"):
    project = load_project(str(l5x_path))
    out_dir = f"reportes_generados/{project.identity.target_name}"
    to_excel(project, f"{out_dir}/inventario.xlsx")
    to_markdown(project, f"{out_dir}/reporte.md")
```

Útil si Hedi tiene urgencia de documentar el parque entero antes de avanzar funcionalidad.

**Cómo decidir entre A, B y C:** Hedi te lo dirá explícitamente. Si no lo dice, **pregúntale antes de elegir uno**. No asumas.

---

## 6 · Anti-patrones (qué NO hacer)

Aprendizajes meta del sprint v0.1, formalizados en DT-010 y consecuencias:

### NO agregar dependencias al `pyproject.toml` sin validación empírica

**Lección concreta:** la librería `l5x` de jvalenzuela se agregó con razonamiento aparentemente sólido en DT-002. Durante implementación se descubrió que xml.etree directo cubría todas las necesidades. La librería estuvo en el código como dead weight hasta que se eliminó en DT-010.

**Regla:** si crees que necesitas una librería nueva, primero la importas en una rama de exploración, ejercitas las APIs concretas que pensabas usar contra el caso real más complejo (los L5X en `parque_l5x/`), y solo si aporta valor concreto la agregas. La pregunta correcta no es "¿esta librería funciona?" sino "¿qué hace por mí que yo no haría con stdlib?".

### NO declarar algo "validado" probándolo solo en un caso

**Lección concreta:** el matching eje↔módulo por nombre funcionaba perfecto en CINTA_TWIN (donde nombres de eje y drive coinciden literalmente: M1, M2, etc.). Falló completamente en AQL_M2 (nombres semánticos `S04N71_*` vs nombres de catálogo `M1_501U1`). Sin el segundo caso de validación, hubiéramos creído que estaba bien.

**Regla:** ningún componente nuevo se considera validado hasta que se ejercita contra al menos dos L5X de arquitectura distinta. Para v0.2, esto significa: tracer probado contra CINTA_TWIN Y AQL_M2 antes de declararlo funcional.

### NO crear stubs vacíos para funcionalidad futura

**Regla (DT-009):** el código en disco refleja lo implementado en la versión actual. Si v0.2 va a tener `tokenizer/rll_tokenizer.py`, ese archivo NO existe en v0.1. Crear stubs vacíos genera ruido en imports, IDE auto-complete, y falsa expectativa de funcionalidad.

**Excepción:** schemas de datos (SQLite) sí pueden tener tablas vacías para v0.2 (caso `xref`), porque su costo de pre-creación es nulo y evitan migración de schema entre versiones.

### NO mezclar documentación arquitectónica con código stub

**Regla (DT-009 + aclaración):** la documentación arquitectónica describe la visión integrada del paquete a través de versiones. Es OK que `02_Arquitectura_Skill.md` mencione `tracer.py` como módulo planeado v0.2 — eso es documentación. Lo que NO es OK es crear el archivo `tracer.py` vacío.

### NO inventar tags, AOIs, ni rutinas

Si Hedi pregunta "¿hay un tag llamado X?" y no aparece en `project.search("X")`, responde "no encuentro X en este proyecto". No respondas "X probablemente está en algún sitio del proyecto" o cualquier variante alucinatoria. El paquete tiene la fuente de verdad — úsala.

### NO ocultar limitaciones

Si una pregunta requiere capacidad v0.2 (trace causal automático), dilo explícitamente: "v0.1 no tiene trace automático. Voy a navegar manualmente, te muestro cada paso." No intentes simular la capacidad.

---

## 7 · Bitácora de decisiones — los 10 puntos canónicos

Lectura obligatoria: `docs/01_Decisiones_Tecnicas.md` completo.

Resumen de las decisiones cerradas:

| ID | Decisión |
|----|----------|
| DT-001 | Fuente principal: L5X (no ACD directo) |
| DT-002 | Reuso de librería `l5x` (jvalenzuela) — **revertida en DT-010** |
| DT-003 | NO reuso del proyecto `studio5000-AI-Assistant` |
| DT-004 | Arquitectura "Mapa Mental + Lupa" |
| DT-005 | Construcción gradual N1 → N2 → N3 |
| DT-006 | Versión v0.1 primero, no construcción completa |
| DT-007 | Empaquetado como paquete Python instalable |
| DT-008 | Stack tecnológico mínimo |
| DT-009 | Política de evolución entre versiones (schemas vs código) |
| DT-010 | Refinamiento de DT-002 — eliminación de `l5x` con aprendizaje meta |

**Si te encuentras razonando "deberíamos hacer X"**, antes de proponerlo a Hedi verifica que no contradiga ninguna DT existente. Si la contradice, el camino correcto es proponer una DT nueva que actualice o supersede a la anterior, no ignorar la bitácora.

---

## 8 · Workflow recomendado con Hedi

Esta es la dinámica que funcionó durante v0.1 y vale la pena replicar:

### Para tareas técnicas

1. Hedi describe el problema o necesidad
2. Tú haces preguntas si hay ambigüedad — **antes de codificar**
3. Cuando la dirección está clara, ejecutas
4. Reportas con honestidad: qué hiciste, qué funcionó, qué no, qué hallazgos surgieron
5. Si revelaste algo que merece DT nueva, la propones

### Para validaciones

Después de cualquier cambio en el código:
- Re-correr smoke test contra ambos L5X
- Verificar conteos esperados
- Confirmar sin regresión en observaciones automáticas

### Para decisiones técnicas

Si vas a tomar una decisión que afecta la arquitectura:
- **Pregunta a Hedi antes** si tiene escala estructural
- Documenta en bitácora con justificación
- Refiere a DTs existentes cuando sea relevante

### Para documentación

Cualquier hallazgo importante durante el trabajo se documenta inmediatamente en el archivo correspondiente:
- Decisión técnica → `01_Decisiones_Tecnicas.md`
- Hallazgo sobre proyecto real → `04_Investigacion_Previa.md`
- Caso de uso nuevo → `03_Casos_de_Uso_Reales.md`

**No esperes al final del sprint.** La documentación como subproducto pesa poco. La documentación retroactiva pesa mucho.

---

## 9 · Comandos útiles del repo

### Ver el estado del paquete
```bash
python -c "import rockwell_comprehender as rc; print(rc.__version__)"
# Esperado: 0.1.0
```

### Generar todos los reportes de un L5X
```bash
python -m rockwell_comprehender.run_all parque_l5x/CINTA_LAMINADA_M2_2024.L5X reportes_generados/
# (Si este script no existe todavía, crearlo es buena idea)
```

### Tests
```bash
# v0.1 no tiene test suite formal — Hedi y la otra instancia validaron contra
# los L5X reales como única forma de testing. Si quieres agregar pytest, OK,
# pero no por completitud — solo si previene regresiones específicas.
```

### Git workflow
```bash
git status
git diff
git add -A
git commit -m "descripción concreta del cambio"
git log --oneline -10
```

Hedi tiene GitHub privado. Sincronización con remoto cuando él lo decida.

---

## 10 · Archivos de la documentación que debes leer

Por orden de prioridad:

1. **Este archivo** (HANDOFF) — ya lo estás leyendo
2. `docs/SKILL.md` — el contrato del paquete, qué hace y cuándo se usa
3. `docs/00_Vision_y_Roadmap.md` — para entender hacia dónde va el proyecto a largo plazo
4. `docs/01_Decisiones_Tecnicas.md` — DT-001 a DT-010, lectura obligatoria completa
5. `docs/03_Casos_de_Uso_Reales.md` — los casos que el paquete debe resolver, especialmente Caso #1 (empalme)
6. `docs/02_Arquitectura_Skill.md` — diseño técnico, útil cuando vayas a tocar código
7. `docs/04_Investigacion_Previa.md` — historia del proyecto, hallazgos, aprendizajes meta
8. `docs/ejemplos/*.md` — outputs reales para tener referencia visual del Mapa Mental

Después de leer 1-5, ya tienes contexto suficiente para arrancar. 6-8 los consultas según se necesiten.

---

## 11 · Cierre

El paquete v0.1 representa varios días de trabajo iterativo entre Hedi y dos instancias previas de Claude (web). Salió bien porque hubo disciplina técnica, documentación viva, y pares colaborando con honestidad.

Tu rol como Claude Code es **continuar esa tradición en otro entorno** — uno donde tienes acceso real al filesystem, ejecución persistente, y todos los L5X del parque al alcance. Eso es valor enorme. Aprovéchalo.

**Bienvenido al proyecto.**

---

*Última actualización: 2026-05-02*
