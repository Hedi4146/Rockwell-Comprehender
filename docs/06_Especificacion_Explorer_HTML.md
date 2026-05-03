# 06 · Especificación — Explorer HTML v0.1

**Para:** Claude Code
**De:** Claude.ai web (sesión de razonamiento estratégico con Hedi)
**Fecha:** 2026-05-02
**Estado:** Especificación lista para implementación

---

## 0 · Lectura previa obligatoria

Antes de empezar a codificar, lee:
- `docs/HANDOFF_v01_to_N2.md` (si no lo has leído ya)
- `docs/01_Decisiones_Tecnicas.md` (DT-001 a DT-010)
- `docs/SKILL.md`

Y revisa el estado del paquete:
```bash
python -c "from rockwell_comprehender import load_project; \
  p = load_project('parque_l5x/CINTA_LAMINADA_M2_2024.L5X'); \
  print(p.mapa_mental)"
```

Si esto no funciona, **detente y diagnostica** antes de continuar.

---

## 1 · Por qué este reporter es el corazón del proyecto

El paquete `rockwell_comprehender` v0.1 ya extrae toda la información estructural de un proyecto Rockwell. Pero esa información hoy solo es accesible:

- A Claude (vía conversación con el paquete)
- A Hedi (vía Python interactivo o reportes Markdown/Excel)

**No es accesible al usuario primario en producción**: el técnico de mantenimiento de planta que enfrenta una falla a las 3 AM y necesita comprensión rápida sin esperar a que llegue el experto.

El Explorer HTML resuelve esto. Es **un solo archivo HTML estático** que:
- Se abre en cualquier navegador sin instalación
- Replica visualmente el Controller Organizer de Studio 5000 (familiar a todos los técnicos)
- **Pero con vista de experto integrada**: cada elemento muestra información que un ingeniero senior tendría en la cabeza

---

## 2 · El insight clave — qué diferencia "Explorer útil" de "Explorer replica"

El Controller Organizer en Studio 5000 ya existe. Si construyes una réplica visual exacta, no agregas valor — el técnico ya lo tiene.

**El Explorer v0.1 agrega valor cuando expone integración cognitiva que un experto hace mentalmente y un técnico inexperto no puede.**

### Ejemplo paradigma — relación servomotor ↔ servodrive

Pregunta común de técnico: *"¿Qué drive físico controla este eje S04N86_DANCER_DEBO_TNT?"*

**Cómo lo resuelve un experto:** sabe que en Studio 5000 la asociación está en AxisParameters → MotionModule. Click derecho → Properties → Motion → MotionModule. Ve "M16_514U1:Ch27" y reconoce el drive 2094-BM02.

**Cómo lo resuelve un técnico inexperto:** no sabe dónde está la información. Pregunta a Hedi (3 AM, no contesta). Abre cada drive del SERCOS uno por uno. Adivina. Riesgo de error alto.

**Cómo lo resuelve el Explorer v0.1:** click en el eje → panel lateral muestra:
```
S04N86_DANCER_DEBO_TNT
  Función inferida: Dancer / control de tensión
  Drive físico:     M16_514U1 (2094-BM02)
  Canal:            Ch27
  Programa:         Debo_Tela
  AOIs principales: Axis_Object_Sercos
```

**Eso es vista de experto.** El paquete v0.1 ya tiene toda esa información — falta exponerla visualmente.

---

## 3 · Especificación visual — referencia

Hedi compartió capturas de Studio 5000 que muestran el Controller Organizer real. Las describo textualmente para que la implementación se inspire en ellas:

### Captura 1 — Tasks + Motion Groups
```
Controller [CPU2_FORMACION_M2]
├── Controller Tags
├── Controller Fault Handler
├── Power-Up Handler
├── Tasks
│   ├── MainTask
│   │   └── MainProgram
│   │       ├── Program Tags
│   │       ├── MainRoutine
│   │       ├── Cambio_de_Talla
│   │       ├── InitAxis
│   │       ├── MachineStatus
│   │       ├── Phase_Control
│   │       └── ServoControl
│   ├── TimeScan
│   │   └── Reject
│   └── Unscheduled Programs / Phases
├── Motion Groups
│   ├── Axis (12 ejes con nombres semánticos S02N31_*, S02N32_*, ...)
│   └── Ungrouped Axes (S02N43_*, S02N44_*)
```

### Captura 2 — AOIs + I/O Configuration
```
├── Add-On Instructions (27 AOIs)
│   ├── AHT_Delta_PhaseMotors
│   ├── AHT_Homing
│   ├── AOI_CCCT
│   ├── AxisBlockVM_Emp_Indiv
│   └── ... (24 más)
├── Data Types
├── Trends
└── I/O Configuration
    └── 1756 Backplane, 1756-A17
        ├── [0] 1756-L61 CPC_400_PLC1
        ├── [3] 1756-L61 CPU2_FORMACION_M2
        ├── [4] 1756-M16SE SERCOS3
        ├── [5] 1756-ENBT/A Ether
        ├── [9] 1756-IB32/A Input4
        └── [13] 1756-IF6I Analog_Input2
```

### Aspecto visual a replicar
- **Iconos** distintos por tipo de elemento (carpeta, controlador, eje, AOI, módulo)
- **Indentación** clara que muestra jerarquía
- **Expansión/colapso** de nodos
- **Selección de un nodo** → resalta + muestra panel lateral con detalles

---

## 4 · API técnica

### Función pública
```python
from rockwell_comprehender.reporters import to_html_explorer

to_html_explorer(project: Project, output_path: str) -> str
# Retorna: path absoluto del archivo .html generado.
# Genera UN SOLO archivo .html autocontenido (sin dependencias externas).
# CSS y JS embebidos. Listo para abrirse offline.
```

### Restricciones técnicas
- **Una sola dependencia OK:** Si necesitas, puedes usar CDN para una librería de tree (jstree, treeview, similar). Pero el HTML debe seguir siendo abrible offline una vez cargado, o sin red para uso ocasional.
- **Sin backend, sin servidor.** Es HTML estático.
- **Sin localStorage / sessionStorage.** Toda la data va embebida en el HTML mismo (data attributes, JSON inline, etc).
- **Tamaño objetivo:** <2 MB para proyectos típicos (1-3 MB de L5X). Si necesitas más, advertir.
- **Compatible con navegadores modernos** (Chrome, Firefox, Edge — Hedi y su equipo usan estos).

---

## 5 · Estructura del HTML

### 5.1 Layout general (dos paneles)

```
┌─────────────────────────────────────────────────────────────┐
│  Header: <Nombre del Proyecto> | <Controlador> | <Versión>   │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                       │
│  Panel izquierdo:    │  Panel derecho:                       │
│  Árbol Controller    │  Detalles del nodo seleccionado       │
│  Organizer           │                                       │
│                      │  (Inicia mostrando "Vista general"     │
│  - Expandible        │   = el Mapa Mental del proyecto)      │
│  - Click selecciona  │                                       │
│  - Doble-click       │                                       │
│    expande/colapsa   │                                       │
│                      │                                       │
└──────────────────────┴──────────────────────────────────────┘
```

### 5.2 Estructura del árbol (panel izquierdo)

Replicar la jerarquía universal de Rockwell. Para cada proyecto:

```
[Controller: <nombre>] (icono carpeta)
├── 📋 Controller Tags (N tags)
├── ⚠️ Controller Fault Handler
├── ⚡ Power-Up Handler
├── 📂 Tasks (N tasks)
│   └── Por cada Task:
│       └── [Task name] [icono según tipo: continuous/periodic/event]
│           └── Por cada Program asociado:
│               └── [Program name] (icono carpeta)
│                   ├── 📋 Program Tags (N)
│                   └── Por cada Routine:
│                       └── [Routine name] (icono según tipo: RLL/ST/FBD)
├── 📂 Motion Groups
│   └── Por cada grupo:
│       └── [Group name]
│           └── Por cada eje (sorted alpha):
│               └── [Axis name] (icono según tipo: SERVO/VIRTUAL)
├── 📂 Add-On Instructions (N AOIs)
│   └── Por cada AOI (sorted alpha):
│       └── [AOI name]
├── 📂 Data Types (N UDTs)
│   └── Por cada UDT (sorted alpha):
│       └── [UDT name] (N members)
└── 📂 I/O Configuration
    └── Para cada chassis raíz:
        └── [Chassis] (ej: "1756 Backplane, 1756-A17")
            └── Por cada slot ordenado por número:
                └── [N] <Module name> [<Catalog>]
                    └── Si tiene hijos (adapters):
                        └── Recursión
```

### 5.3 Panel derecho — vista por tipo de nodo

El contenido cambia según qué se haya seleccionado en el árbol. Plantillas mínimas:

#### 5.3.1 Vista inicial (sin selección) — "Vista general del proyecto"
Renderizar el contenido de `project.mapa_mental` formateado como Markdown → HTML. Este es el resumen ejecutivo que ya genera v0.1.

#### 5.3.2 Click en eje (Axis)
```
[Nombre del eje]
─────────────────────────────────
Tipo:                  AXIS_SERVO_DRIVE / AXIS_VIRTUAL
Función inferida:      [from mapamental.py inference]
Drive físico:          [from motion_module → catalog del módulo]
Canal:                 [from motion_module]
Programa que lo usa:   [from search del nombre en código]
AOIs principales:      [from inference]
Descripción:           [tag.description]
```

#### 5.3.3 Click en módulo (I/O)
```
[Module name]
─────────────────────────────────
Catalog:           [m.catalog_number]
Vendor:            [m.vendor]
Slot/Port:         [m.parent_port_id]
Inhibido:          Sí/No
Major Fault:       Sí/No
Hijos:             [si tiene módulos hijos, listar]
Categoría:         Drive/Bridge/Adapter/IO Module
```

#### 5.3.4 Click en AOI
```
[AOI name] (rev N)
─────────────────────────────────
Parámetros:        N (input/output/inout)
Local tags:        N
Routines:          N (lista nombres)
Descripción:       [aoi.description]

⚠️ Si tiene par duplicado: avisar
   "Esta AOI tiene un par potencialmente duplicado: [nombre del par]"
```

#### 5.3.5 Click en routine
```
[Routine name] (RLL / ST / FBD)
─────────────────────────────────
Programa:          [r.program]
Descripción:       [r.description]
Lenguaje:          RLL / ST / FBD

[Botón: Ver código completo]
   Al hacer click, expandir un área con el código en <pre><code>
```

#### 5.3.6 Click en UDT
```
[UDT name]
─────────────────────────────────
Members:           N
Descripción:       [u.description]

Tabla de members (Name | DataType | Dim | Description)
```

#### 5.3.7 Click en Tag (controller-scope, program-scope, AOI-local)
```
[Tag name]
─────────────────────────────────
Scope:             controller / [program] / [AOI]
DataType:          [t.datatype]
Dimensión:         [t.dimension or "scalar"]
External Access:   [t.external_access]
Descripción:       [t.description]
Motion Module:     [t.motion_module if axis]

⚠️ Trace de uso: "Disponible en v0.2"
```

#### 5.3.8 Vistas de cabeceras (Tasks, AOIs, etc.)
Click en un encabezado de carpeta (ej: "Add-On Instructions") muestra **contadores y resumen**. Ejemplo:
```
Add-On Instructions
─────────────────────────────────
Total: 27 AOIs
Distribución por prefijo:
  AHT_*: 11
  AOI_*: 1
  Sin prefijo: 15

⚠️ AOIs duplicadas detectadas: [si project.observations tiene aoi_naming_collision]
```

### 5.4 Top-bar y barra de búsqueda

En el header, además del nombre/controlador, incluir:
- **Caja de búsqueda** que filtra el árbol por nombre (tipo "incremental search")
- **Filtros de visibilidad** opcionales (ej: ocultar program tags para reducir ruido)
- Si Hedi pide más filtros después de probarlo, se agregan; no anticipar.

### 5.5 Observaciones automáticas (importante)

`project.observations` contiene detecciones automáticas (AOIs duplicadas, módulos sin nombre, etc). Estas deben aparecer:
- **En el panel derecho cuando el nodo afectado se selecciona** (ej: AOI duplicada)
- **En una sección expandible "Observaciones del proyecto"** accesible desde el header (botón con badge tipo "⚠️ 6 observaciones")

---

## 6 · Reglas de implementación (importantes)

### 6.1 NO usar localStorage/sessionStorage
El entorno donde se va a abrir el HTML puede ser cualquiera (el navegador del técnico, una carpeta compartida, etc.). No depender de almacenamiento del navegador.

### 6.2 NO inventar datos
Si el paquete v0.1 no tiene un dato (ej: el catalog number del motor), **no inventar uno aproximado**. Mostrar `—` o "(información no disponible)". Es la regla del HANDOFF: no alucinar.

### 6.3 Función inferida — usar lo que ya hay
La inferencia funcional ("Dancer", "Debobinador", etc.) **ya está implementada** en `mapamental.py` con el diccionario `_TAG_NAME_HINTS` y la función `_infer_from_tag_name`. **Importar y usar esos helpers**, no reimplementar.

Igual con la asociación eje↔drive vía `motion_module` — ya está en el modelo.

### 6.4 Cualquier capacidad nueva merece DT
Si durante la construcción decides algo arquitectónico (ej: "los iconos los voy a hacer con emojis", "uso jstree", etc), si tiene impacto técnico relevante, propón una entrada DT-011 / DT-012 en `01_Decisiones_Tecnicas.md`. No silentemente.

### 6.5 Iterar sobre lo simple primero
NO construir todo de una vez. Sigue este orden:

1. **HTML estático con árbol del Controller Organizer** funcionando (sin paneles aún, solo el árbol expandible)
2. **Panel derecho con vista por defecto** (Mapa Mental al cargar)
3. **Vistas individuales por tipo de nodo** — empezar por **Eje** (es el caso paradigma)
4. **Búsqueda y filtros** — solo si los pasos 1-3 funcionan bien
5. **Observaciones automáticas** integradas
6. **Validación contra ambos L5X** — generar el HTML para CINTA_TWIN y AQL_M2

Después de cada paso, valida que funciona antes de avanzar.

### 6.6 Tests sugeridos durante la construcción

Cuando termines, ejecutar estos casos:

```python
# Test 1 — generar para CINTA_TWIN
project = load_project("parque_l5x/CINTA_LAMINADA_M2_2024.L5X")
html_path = to_html_explorer(project, "reportes_generados/explorer_cinta.html")

# Test 2 — generar para AQL_M2 (más complejo)
project = load_project("parque_l5x/AQL_M2.L5X")
html_path = to_html_explorer(project, "reportes_generados/explorer_aql.html")

# Test 3 — abrir ambos en navegador y verificar:
# - El árbol carga correctamente con todos los nodos
# - Click en un eje (ej: M3 en CINTA, S04N86_DANCER en AQL) muestra panel correcto
# - Click en un módulo drive (1768-M04SE en CINTA, 1756-M16SE en AQL) muestra info
# - Click en un AOI (AHT_CtcSplicer) muestra parámetros y rutinas
# - Búsqueda incremental funciona
# - Observaciones aparecen donde corresponde
```

Reportar tamaños de archivo generados — si exceden 5 MB, hay que optimizar.

---

## 7 · Lo que NO está en alcance v0.1 del Explorer

Diferir explícitamente para versiones posteriores:

❌ **Trace de variables** (`writers_of`, `readers_of`) — eso es v0.2 del paquete (tracer.py). Mostrar placeholder en el panel.

❌ **Diagramas Mermaid integrados** — los reporters Mermaid ya existen y se generan aparte. El Explorer no los embebe.

❌ **Edición o anotación** — solo lectura. El Explorer es comprensión, no modificación.

❌ **Multi-proyecto** — un Explorer = un proyecto. Si Hedi necesita varios, genera varios HTMLs.

❌ **Persistencia de selecciones / favoritos** — no hay localStorage (regla 6.1).

❌ **Tema oscuro / personalizaciones visuales** — no es prioridad. Default limpio y legible es suficiente.

❌ **Análisis con AI integrado** — el Explorer expone los datos del paquete, no llama a Claude ni LLMs.

---

## 8 · Validación final con Hedi

Cuando termines, confirma:

1. ✅ Generaste HTMLs para CINTA_TWIN y AQL_M2
2. ✅ Abren correctamente en navegador
3. ✅ El árbol replica la estructura del Controller Organizer
4. ✅ Click en un eje muestra correctamente función inferida + drive asociado + canal
5. ✅ Click en otros tipos de nodos muestra paneles informativos
6. ✅ La búsqueda incremental funciona

Después, **dile a Hedi** que pruebe los HTMLs y te diga:
- Si el caso paradigma (servomotor↔servodrive) se resuelve con un click
- Qué información falta en los paneles
- Si hay nodos que se ven raros o con errores

Su feedback define las iteraciones siguientes.

---

## 9 · Por qué construir esto antes de v0.2 (tracer)

Decisión tomada con Hedi en sesión 2026-05-02:

El paquete v0.1 ya tiene **60-70% de las respuestas que un técnico necesita en producción**. Lo único que falta es **exponerlas visualmente**. El Explorer hace esto.

Construir v0.2 (tracer.py) primero significa agregar capacidad técnica que **solo Claude usa**, sin que nada llegue a manos del equipo de mantenimiento. Eso viola el principio operativo establecido: *"cada nueva capacidad debe producir algo visible para humanos"*.

Construir Explorer primero:
- Entrega valor inmediato al usuario primario (técnicos de planta)
- Permite **descubrir empíricamente** qué capacidades adicionales (v0.2/v0.3) son las más necesarias
- Mantiene la disciplina DT-010 (validación empírica antes de comprometer trabajo grande)

Cuando el Explorer esté en uso real, las decisiones de v0.2/v0.3 se toman con datos, no con especulación.

---

## 10 · Cierre

Esto es la prioridad operativa actual del proyecto. Hedi está listo para validar tan pronto entregues una versión funcional, aunque sea mínima. **Velocidad de iteración > completitud inicial**.

Si tienes dudas sobre cualquier parte de esta especificación, **pregunta antes de codificar**. Es preferible perder 5 min en clarificar que 2 horas en re-construir algo malentendido.

Vamos.

---

*Especificación generada: 2026-05-02*
*Origen: sesión de razonamiento estratégico Claude.ai web ↔ Hedi*
*Validación visual: capturas de Studio 5000 Controller Organizer (CPU2_FORMACION_M2)*
*Caso paradigma motivador: relación servomotor S04N86_DANCER_DEBO_TNT ↔ servodrive M16_514U1:Ch27*
