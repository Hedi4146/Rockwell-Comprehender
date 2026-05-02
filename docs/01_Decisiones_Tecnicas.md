# 01 · BITÁCORA DE DECISIONES TÉCNICAS

Documento vivo donde se registra cada decisión arquitectónica relevante con su justificación. Una decisión sin razón documentada es una decisión que se va a cuestionar después sin contexto.

**Formato:** cada entrada incluye fecha, decisión, contexto, alternativas consideradas, razón de la elección, y consecuencias.

---

## DT-001 · Fuente principal: L5X (no ACD directo)

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida y validada con piloto

**Decisión:** Usar archivos L5X exportados desde Studio 5000 como fuente primaria de información del proyecto. El parsing directo de archivos ACD se difiere indefinidamente.

**Contexto:** Necesitamos cargar proyectos PLC y construir un modelo canónico. Hay dos formatos posibles: ACD (binario propietario) y L5X (XML).

**Alternativas consideradas:**

| Alternativa | Pros | Contras |
|-------------|------|---------|
| ACD vía `acd-tools` (hutcheb) | Sin paso manual del usuario | Bugs reproducibles en v20 (Comments parsing, ControllerBuilder); módulos I/O no extraíbles; AOIs ausentes; código con hashes sin resolver |
| L5X vía librería `l5x` | Cobertura 100%, código limpio, schema estable | Requiere export manual desde Studio 5000 |
| SDK oficial Rockwell | Funcionalidad completa | Requiere Windows + Studio 5000 v36+ + licencia Professional |

**Razón de la elección:** El piloto comparativo con `CINTA_LAMINADA_M2_2024` mostró que el L5X gana 21-0 en categorías diferenciadoras (modules, AOIs, tasks, código limpio, comentarios). Hedi confirmó que puede exportar L5X de cualquier archivo de su parque sin afectar producción. El paso manual de export (~30 segundos por archivo) es aceptable como gobernanza.

**Consecuencias:**
- Workflow estándar: usuario abre proyecto en Studio 5000 → exporta L5X → sube al sistema
- Cobertura uniforme G1 (v10-v19) / G2 (v20-v27) / G3 (v28+) con un solo parser
- Sin dependencia de bugs de librerías beta
- Sin dependencia de SDK oficial Rockwell
- Permitida sub-modalidad "ACD metadata-only" para casos donde no haya L5X disponible (usando lo que `acd-tools` SÍ logra extraer sin bugs: QuickInfo.XML, TagInfo.XML básico)

**Validación:** Piloto del 2026-05-01 con archivo CINTA_LAMINADA_M2_2024 (v20.01) confirmó que el L5X es completo y limpio mientras el ACD vía librería es parcial y con bugs.

---

## DT-002 · Reuso de librería `l5x` (jvalenzuela)

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Usar la librería `l5x` v1.7 de jvalenzuela (PyPI) como capa base de parsing en nuestro loader. No reimplementar parsing de XML L5X desde cero.

**Contexto:** Necesitamos parsear L5X y exponer un modelo de objetos pythónico. Hay varias opciones.

**Alternativas consideradas:**

| Alternativa | Veredicto |
|-------------|-----------|
| `l5x` (jvalenzuela) | Maduro, API limpia, en PyPI |
| `Allen-Bradley-Toolkit` (cmseaton42) | Redundante con `l5x` |
| Parsing XML directo con `xml.etree` | Reinvento la rueda |
| Parsing XML con `lxml` | Más rápido pero también requiere reinventar el modelo |

**Razón:** `l5x` ofrece ya un modelo `Project → Controller → {Tags, Programs, Modules}` con manejo de scopes, alias, consumed tags, structures. Soporta lectura y escritura. Madurez probada. Ahorra ~2-3 días de trabajo de parsing básico que no aporta valor diferencial.

**Consecuencias:**
- Dependencia técnica: `pip install l5x`
- Nuestro código se concentra en lo que ningún proyecto open-source ofrece: comprensión, mapa mental, navegación, trace
- Si jvalenzuela deprecara la librería, el riesgo es bajo: el parsing L5X es estable y podríamos forkearla o sustituirla con esfuerzo acotado

---

## DT-003 · NO reuso del proyecto `studio5000-AI-Assistant` (rivie13)

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** No integrar código del proyecto `rivie13/studio5000-AI-Assistant`. Sí estudiar su `PERFORMANCE_OPTIMIZATIONS.md` para ideas.

**Contexto:** Existe un proyecto MCP con FAISS vector search, integración SDK Studio 5000, y generación de código L5X.

**Razón:**
1. **Filosofía opuesta:** ese proyecto está pensado para **generar** código (con limitaciones reales que su propio README admite — formato RLL con problemas). Nosotros estamos pensados para **comprender** código existente.
2. **Stack pesado:** requiere `torch + sentence-transformers + faiss-cpu` (~3 GB de dependencias) para búsqueda vectorial. En proyectos del tamaño de CINTA TWIN (1.2 MB), el razonamiento natural de Claude basta sin embeddings.
3. **Dependencia SDK Rockwell:** funcionalidades clave requieren Studio 5000 instalado en Windows.
4. **Acoplamiento MCP fuerte:** está diseñado como servidor MCP, no como librería reutilizable.

**Consecuencias:**
- Si en v0.3 o Nivel 3 enfrentamos proyectos masivos (Pañalera 2 completa, miles de rutinas) y la búsqueda semántica con razonamiento natural deja de escalar, evaluamos agregar FAISS como capa opcional. **No antes.**
- Mantenemos stack ligero: `python + l5x + sqlite3 + xml`. Sin GPU, sin embeddings, sin servidores.

---

## DT-004 · Arquitectura "Mapa Mental + Lupa"

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Diseñar el skill con cuatro capas de profundidad descendente: (1) Mapa Mental general siempre cargado, (2) Mapas funcionales bajo demanda, (3) Lupa puntual bajo demanda, (4) Trace de dependencias bajo demanda.

**Contexto:** Un proyecto Logix promedio no cabe en el contexto de Claude (CINTA TWIN sola = 350K tokens, ventana = 200K). Y los proyectos grandes son 10x más. No se puede cargar todo.

**Alternativa rechazada:** Cargar el proyecto entero y usar embeddings vectoriales para búsqueda. Demasiado pesado para nuestros tamaños actuales.

**Razón:** Imita cómo trabaja un ingeniero senior — mapa estructural mental siempre presente, profundización dirigida cuando se requiere. Permite trabajar con proyectos arbitrariamente grandes sin saturar el contexto.

**Consecuencias:**
- El loader debe pre-calcular el Mapa Mental como entregable de carga
- Necesitamos índices consultables (SQLite + búsqueda full-text) para las capas 2-4
- Cada conversación carga al inicio el Mapa Mental + datos de identificación del proyecto
- La navegación a capas más profundas es decisión del modelo durante la conversación, no del usuario

---

## DT-005 · Construcción gradual N1 → N2 → N3

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Construir secuencialmente los tres niveles de madurez. No saltar a Nivel 3 directamente.

**Contexto:** La visión de largo plazo es una aplicación web; existe la tentación de empezar por ahí.

**Razón:**
1. **Nivel 1 enseña qué se necesita.** Datos reales de uso > diseño especulativo.
2. **El trabajo no se pierde.** Código de N1 se reutiliza tal cual en N2 y N3.
3. **Decisiones arquitectónicas informadas** después de uso real.
4. **Costo de oportunidad:** Hedi tiene la migración K5700 y plataforma AI/Data activas; comprometer 3-6 meses a una web app retrasa esos proyectos.
5. **El caso paradigmático del empalme se resuelve completamente en N1.**

**Consecuencias:**
- Foco actual: solo v0.1 del Nivel 1
- Documentar workflows reales que emerjan durante uso de N1 y N2 — esa documentación se vuelve la spec de la futura UI de N3
- Decisión de pasar a N3 se toma con datos, no por fechas

---

## DT-006 · Versión v0.1 primero, no construcción completa

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Construir solo v0.1 (lector inteligente con Mapa Mental + búsqueda + lupa puntual) antes de validar. v0.2 (trace automático) y v0.3 (dominios funcionales) se difieren a decisión post-v0.1.

**Razón:**
1. v0.1 ya resuelve el caso del empalme, solo con más conversación
2. v0.1 enseña qué patrones realmente necesitan automatización en v0.2
3. 5 días vs 14-20 — si el enfoque es equivocado, perdimos una semana, no un mes
4. Riesgo de over-engineering antes de validar dominios funcionales reales

**Consecuencias:**
- Sprint actual acotado a v0.1
- Validación con caso de empalme antes de comprometer v0.2
- Hedi y Claude deciden juntos si v0.2 vale la pena con datos en mano

---

## DT-007 · Empaquetado como paquete Python instalable

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** El código del skill se organiza como un paquete Python instalable con interfaces claras (módulos: `loader`, `model`, `mapamental`, `navigator`, `tracer`, `reporters`, `api`), no como scripts sueltos.

**Razón:**
- Mismo paquete corre en Claude web (sandbox), Claude Code (local), y futuro backend de web app
- Interfaces claras facilitan testing y mantenimiento
- Una API pública (`api.py`) define el contrato hacia consumidores externos (futura UI)

**Consecuencias:**
- Mayor disciplina inicial en la organización del código
- Setup ligeramente más complejo pero pagado a futuro
- Convención: `from rockwell_comprehender import load_project` debe ser el punto de entrada limpio

---

## DT-008 · Stack tecnológico mínimo

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Mantener stack ligero — Python 3.10+, librería `l5x`, `sqlite3` (stdlib), `xml.etree` (stdlib). Sin dependencias pesadas hasta que se justifiquen.

**Sin:** torch, faiss, embeddings vectoriales, frameworks ML, servidores externos, bases de datos no-SQLite.

**Razón:** Cualquier dependencia pesada se paga en cada deployment, en cada nuevo entorno, en cada conversación. Los stacks ligeros son fáciles de mantener y portar.

**Consecuencias:**
- Si en v0.3 o Nivel 3 emerge necesidad real de capacidad pesada, se agrega como capa opcional
- Compatibilidad con sandbox de Claude web garantizada
- Compatibilidad con Claude Code en cualquier máquina garantizada

---

## DT-009 · Política de evolución entre versiones

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida

**Decisión:** Distinción clara entre schemas y código respecto a su tratamiento en la evolución entre versiones del paquete.

- **Schemas de datos** (SQLite, formatos de archivo, contratos de API): se establecen temprano y crecen aditivamente. Tablas/campos planeados para versiones futuras se crean vacíos desde el inicio.
- **Código** (módulos, clases, funciones): se construye cuando se necesita. No se crean stubs vacíos para versiones futuras.

**Razón:** Los schemas tienen costo de migración pero costo nulo de pre-creación. El código tiene costo de mantenimiento real incluso vacío — ruido en imports, confusión sobre el alcance real, falsa expectativa de funcionalidad.

**Consecuencias:**
- En v0.1: tabla `xref` se crea vacía en el schema SQLite (será poblada por `tracer.py` en v0.2)
- En v0.1: NO se crea el módulo `tokenizer/rll_tokenizer.py` — se agrega al iniciar v0.2
- Aplica a futuras versiones: cualquier nuevo schema se diseña anticipando evolución; cualquier nuevo módulo se construye solo cuando hay funcionalidad concreta que implementar
- La estructura del paquete debe reflejar siempre lo realmente implementado en la versión actual

**Aclaración sobre alcance:**

DT-009 aplica a **artefactos físicos en el repositorio** (archivos `.py` vacíos, módulos sin contenido funcional, paquetes stub).

NO aplica a:
- **Documentación arquitectónica** que describe la visión integrada del paquete a través de versiones (ej: árboles de paquete en docs, diagramas de capas, secciones "Módulos planeados")
- **Schemas de datos** (ver consecuencias arriba — se pre-crean vacíos)
- **Comentarios y TODOs en código existente** que documentan trabajo futuro

La regla operativa es: **el código en disco refleja lo implementado en la versión actual. La documentación refleja la visión completa, distinguiendo claramente qué es presente vs futuro.**

---

## DT-010 · Refinamiento de DT-002 — eliminación de la dependencia `l5x`

**Fecha:** 2026-05-01
**Estado:** ✅ Decidida — `l5x` se elimina del paquete v0.1
**Estado de DT-002:** vigente en filosofía ("reutilizar lo bueno que existe"), aplicación específica revertida con base en evidencia empírica

**Contexto:** Durante la construcción y validación de `loader.py` v0.1 contra `CINTA_LAMINADA_M2_2024.L5X` (1.2 MB, Studio 5000 v20.01, ControlLogix 1768-L43), se ejercitó el uso real de la librería `l5x` v1.7 de jvalenzuela. La evaluación teórica de DT-002 había sido razonable pero la evidencia empírica mostró otra cosa.

**Evidencia — qué intenté usar de `l5x`:**

| Lo que `l5x` expone | ¿Útil en v0.1? | Por qué |
|---|---|---|
| `l5x.Project(filepath)` | Redundante | `_validate_is_l5x` ya hace lo mismo con magic bytes |
| `prj.controller.tags` | No | xml.etree directo da exactamente la misma información sin abstracción intermedia |
| `prj.programs[name]` | No | Solo expone `.element` y `.tags` — no rutinas, no nada útil de alto nivel |
| `prj.modules` | **Falla** | `prj.modules.names` lanza `KeyError('Name')` con módulos POINT I/O sin atributo Name |
| `prj.doc` | No | Es el mismo Element root al que se llega con `ET.parse()` directo |
| AOIs, UDTs, Tasks, código de rutinas | No expuestos | La librería simplemente no modela estos elementos |

Áreas donde `l5x` *podría* aportar pero **no en v0.1**:
- Lectura/escritura de valores estructurados de tags (relevante para v0.2/v0.3 si surge necesidad)
- Serialización L5X round-trip con CDATA (DT-003 explícitamente descarta generación de L5X)
- Manejo robusto de CDATA en lectura (en la práctica `xml.etree` con `itertext()` funcionó sin problemas, incluso con caracteres no-ASCII como el campo Owner del L5X de prueba)

**Razón de la decisión:**

1. **Honestidad técnica.** El código v0.1 no usa `l5x` para ninguna operación productiva. Mantenerla como dependencia es deuda escondida.
2. **Coherencia con DT-008** (stack mínimo): "sin dependencias hasta que se justifiquen". `l5x` no se justifica en v0.1.
3. **Robustez práctica.** `xml.etree` directo es más robusto que `l5x` contra L5X reales (la librería falla con POINT I/O; xml.etree no).
4. **Reversibilidad.** Si en v0.2/v0.3 emerge una necesidad concreta (ej. lectura de valores iniciales de tags estructurados anidados), reincorporar la librería es trivial. No hay costo de oportunidad.
5. **Coherencia con DT-009** (YAGNI para código): se construye/agrega cuando se necesita.

**Consecuencias:**

- `l5x` se elimina de `dependencies` en `pyproject.toml`. v0.1 corre solo con stdlib (`sqlite3`, `xml.etree`, `dataclasses`, `tempfile`, `os`, `json`).
- `loader.py` elimina `import l5x`, el bloque `try/except` con `l5x.Project()`, y la categoría de Observation `l5x_library_fallback` (nunca se disparaba productivamente).
- DT-002 queda en la bitácora con su razonamiento original intacto. DT-010 es el aprendizaje, no una corrección que reescriba el pasado.

**Aprendizaje meta para futuras decisiones tipo "¿reutilizo X librería?":**

> Las decisiones de reuso de librerías deben validarse contra archivos reales antes de comprometerse al `pyproject.toml`. La decisión teórica (DT-002) era razonable con la información disponible en el momento; la decisión empírica (DT-010) la corrige sin invalidarla. Cuando una librería externa parezca atractiva, la regla operativa es: importarla en una rama de exploración, ejercitar las APIs concretas que pensamos usar contra el caso real más complejo disponible, y solo entonces decidir si entra al `pyproject.toml`. Una dependencia es un compromiso de mantenimiento; una validación empírica de 30 minutos puede ahorrar meses de deuda.
>
> **Corolario práctico observado en este caso:** el bloque `try/except` que acomodaba un fallback para cuando `l5x` fallara JAMÁS se disparó en práctica — la librería sí cargaba el archivo, simplemente no aportaba nada útil después. Esto evidencia que "la dependencia funciona" no es suficiente justificación. El test correcto es: **"¿qué operación productiva hace esta librería que mi código no haría con stdlib?"** Si la respuesta es "ninguna o trivial", es deuda.

---

## Decisiones pendientes (en evaluación)

### DT-PEND-001 · Esquema exacto del Mapa Mental
**Status:** Borrador presentado en sesión 2026-05-01, formato exacto se afina con CINTA TWIN como caso real durante construcción de v0.1.

### DT-PEND-002 · Formato de persistencia del análisis
**Status:** SQLite por defecto (DT-008). Pendiente: ¿se guarda en sandbox temporal, o se exporta para reuso entre sesiones de Claude web? En Claude Code es trivial; en web requiere decisión.

### DT-PEND-003 · Manejo de proyectos grandes
**Status:** Diferido. CINTA TWIN (1.2 MB) sirve para v0.1. Cuando lleguemos a Pañalera 2 completa (potencialmente 10-50 MB) re-evaluamos: ¿segmentación por programa/AOI? ¿índices más sofisticados?

---

*Documento vivo. Cada decisión nueva se agrega abajo con su número correlativo.*

*Última actualización: 2026-05-01*
