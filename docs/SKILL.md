---
name: rockwell-project-comprehender
description: "Usa este skill cuando el usuario suba un archivo .L5X (export XML de proyectos Rockwell Studio 5000 / RSLogix 5000) o haga preguntas sobre la arquitectura, lógica, tags, rutinas, AOIs, UDTs, programas, controladores, ejes de motion, o estructura de un proyecto PLC Allen-Bradley ControlLogix / CompactLogix. Triggers incluyen: mención de 'L5X', 'Studio 5000', 'RSLogix', 'Logix', 'ladder', 'rung', 'AOI', 'UDT', 'rutina', 'tag controller-scoped', 'program-scoped', 'GuardLogix', 'Kinetix', así como peticiones para auditar un proyecto desconocido, diagnosticar comportamiento anómalo de máquina, comparar dos proyectos, detectar código muerto, o documentar técnicamente un proyecto. NO usar para: archivos .ACD binarios (Studio 5000 nativo, no exportado a XML); proyectos de FactoryTalk View / HMI; otros PLCs como Siemens TIA Portal, Beckhoff TwinCAT, Omron Sysmac, Schneider Unity; lógica de drives standalone sin contexto de proyecto Logix."
---

# Rockwell Project Comprehender

## Visión general

Este skill implementa un sistema de comprensión profunda de proyectos Rockwell Studio 5000 / RSLogix 5000 a partir de archivos `.L5X` (exportes XML). Convierte un proyecto PLC en algo navegable conversacionalmente: arquitectura, lógica, dependencias y configuración quedan accesibles para diagnóstico, auditoría y documentación.

**Versión actual: v0.1** — lector inteligente con cuatro capacidades: parser completo de L5X, generación de Mapa Mental general, búsqueda full-text en código, y lupa puntual sobre rutinas/AOIs/UDTs específicos. El trace automático de dependencias y la detección de dominios funcionales son v0.2 y v0.3 respectivamente.

**Metáfora operativa:** *Mapa Mental + Lupa*. El mapa mental cabe en contexto y se carga al inicio (~800–1500 tokens — denso en datos estructurales, sin relleno). La lupa se aplica bajo demanda sobre piezas específicas. No se carga el proyecto completo en contexto — se navega como navegaría un ingeniero senior: visión global primero, profundidad localizada después.

## Cuándo usar este skill

Activar cuando el usuario:
- Suba un archivo `.L5X` o lo mencione por nombre/ruta
- Pregunte sobre arquitectura, configuración, ejes, módulos, tags, rutinas o lógica de un proyecto Rockwell
- Reporte un comportamiento anómalo de máquina y pida ayuda para diagnosticar la causa en código
- Pida una auditoría rápida de un proyecto desconocido
- Quiera comparar dos proyectos similares
- Necesite documentación técnica generada del proyecto
- Quiera detectar código muerto, AOIs duplicadas, tags no usados

## Cuándo NO usar

- Archivos `.ACD` binarios → pedir al usuario que exporte a `.L5X` desde Studio 5000 primero
- Proyectos de FactoryTalk View, RSView, PanelView → fuera de alcance
- Otros fabricantes de PLC (Siemens, Beckhoff, Omron, Schneider) → fuera de alcance
- Preguntas conceptuales generales sobre PLC/ladder que no requieren un proyecto cargado → responder directamente sin invocar el skill

## Workflow paso a paso

### 1. Verificar disponibilidad del L5X

El archivo debe estar accesible en el filesystem del sandbox (típicamente `/mnt/user-data/uploads/` o `/mnt/project/`). Si el usuario menciona un L5X que no está disponible, pedir que lo suba antes de continuar.

### 2. Cargar el proyecto

```python
from rockwell_comprehender import load_project

project = load_project("/mnt/user-data/uploads/PROYECTO.L5X")
```

Esta llamada parsea el L5X completo, construye el modelo canónico en SQLite y deja el `Project` listo para consulta. Tarda <5 segundos para proyectos de 1-2 MB.

### 3. Mostrar el Mapa Mental al usuario

```python
print(project.mapa_mental)
```

El Mapa Mental es un documento Markdown autocontenido que cubre: identidad del proyecto (controlador, schema, versión Studio 5000), arquitectura física (módulos I/O, drives, redes), arquitectura lógica (programas, tasks, rutinas principales), mapa funcional de ejes si tiene motion, patrones de código identificados, e issues/observaciones detectadas durante el parseo. Compacto: ~800–1500 tokens, denso en datos estructurales sin relleno.

**Mostrar siempre el Mapa Mental al inicio.** Es el contexto de partida para cualquier conversación posterior.

### 4. Enrutar las preguntas a la capa correcta

| Tipo de pregunta | Acción |
|---|---|
| Estructural ("¿cuántos ejes tiene?", "¿qué controlador usa?", "¿qué patrón de organización siguen los programas?") | Responder desde el Mapa Mental ya cargado |
| Sobre código específico ("muéstrame la rutina X", "¿cómo está implementado el AOI Y?") | `project.get_routine(programa, rutina)` / `project.get_aoi(nombre)` / `project.get_udt(nombre)` |
| Búsqueda ("¿dónde se usa el tag DancerPosition?", "¿hay menciones a Splice?") | `project.search(termino)` — retorna lista de hits con location y snippet |
| Causal ("¿de dónde viene este valor?", "¿qué calcula este setpoint?") | **Manual en v0.1**: combinar `search` + `get_routine` iterativamente, leer el código, inferir cadena causal con razonamiento. NO existe trace automático aún. |
| Comparación entre proyectos | Cargar dos `Project` en paralelo y comparar sus modelos manualmente |
| Generación de documentación | Usar `project.mapa_mental` como base + reporters (`markdown`, `excel`, `mermaid`) para entregables formales |

### 5. Generar entregables si se piden

El paquete incluye módulos `reporters/` para producir entregables formales: documentos Markdown extendidos, hojas Excel multi-tab (BoMs, listados de tags, configuración de ejes), diagramas Mermaid de arquitectura. Las interfaces exactas se afinan durante la construcción de v0.1; consultar el código del paquete instalado para los nombres exactos. Patrón general:

```python
from rockwell_comprehender.reporters import markdown, excel, mermaid

# Los reporters reciben un Project ya cargado y producen archivos en disco
# o strings con el contenido formateado. Salidas típicas en /mnt/user-data/outputs/
```

## API pública v0.1

```python
from rockwell_comprehender import load_project

# Carga
project = load_project(filepath: str) -> Project

# Mapa Mental (Capa 1 — siempre disponible)
project.mapa_mental                                    # str (markdown, ~800–1500 tokens)

# Lupa puntual (Capa 3)
project.get_routine(program: str, routine: str)       # → Routine con .code, .type, .scope
project.get_aoi(aoi_name: str)                        # → AOIDetail con definición completa
project.get_udt(udt_name: str)                        # → UDTDetail con todos los members

# Búsqueda full-text en código
project.search(query: str)                            # → list[SearchHit] con location y snippet
```

> Nota: la información de tags individuales está disponible dentro del Mapa Mental (lista resumida) y vía `search()` (referencias en código). No hay método `get_tag()` dedicado en v0.1 — si hace falta más adelante, se evalúa para v0.2.
>
> Mapas funcionales por dominio (`functional_map`) y trace causal (`trace_back`, `writers_of`, `readers_of`) son v0.2-v0.3. En v0.1 no están disponibles.

## Capacidades v0.1

✅ Parsear L5X de proyectos Studio 5000 (verificado contra v20.01 con ControlLogix 1768-L43; soporte amplio esperado vía librería `l5x` de jvalenzuela, pero no todas las versiones testeadas)
✅ Generar Mapa Mental general legible en <5 segundos
✅ Identificar arquitectura: controlador, módulos I/O, drives, redes, ejes de motion
✅ Listar programas, rutinas, AOIs, UDTs, tags con sus alcances
✅ Buscar texto en código de rutinas (RLL, ST, FBD)
✅ Mostrar código completo de una rutina o AOI específica
✅ Generar reportes Markdown / Excel / diagramas Mermaid básicos
✅ Detectar inconsistencias estructurales obvias durante el parseo (duplicados de AOIs, tags huérfanos)

## Limitaciones honestas

❌ **No hace trace automático de dependencias.** Preguntas como "¿de dónde viene el valor de tal tag?" requieren guía manual: el modelo combina `search` + lectura de código + razonamiento. El trace automático (`writers_of`, `readers_of`, `trace_back`) llega en v0.2.

❌ **No detecta dominios funcionales automáticamente.** El skill no "sabe" qué partes del código son del subsistema de empalme, del control de tensión, del HMI, etc. El usuario tiene que indicar el dominio o el modelo lo infiere conversacionalmente. La detección automática llega en v0.3.

❌ **No procesa archivos `.ACD`.** Solo acepta `.L5X` exportados. Si el usuario tiene un ACD, debe abrir el proyecto en Studio 5000 y exportar a L5X.

❌ **No incluye lógica de HMI** (FactoryTalk View, PanelView). Esos son archivos separados con otro formato.

❌ **No verificado contra proyectos muy grandes** (>10 MB). El caso de prueba base es `CINTA_LAMINADA_M2_2024.L5X` (1.2 MB). Proyectos de 10-50 MB pueden requerir estrategias adicionales aún no implementadas.

❌ **No genera código L5X nuevo.** El skill es de lectura/comprensión, no de generación. La generación informada es una capacidad considerada para futuro pero con riesgos serios (ver decisión técnica DT-003 del proyecto).

❌ **El parser depende de la librería `l5x` de jvalenzuela.** Schemas de L5X anteriores a v17 o muy posteriores a v34 pueden no estar bien soportados — verificar caso por caso.

## Ejemplos de uso

### Ejemplo 1 — Auditoría rápida de proyecto desconocido

> **Usuario:** Acabo de recibir este L5X de una máquina que no conozco. Necesito en 5 minutos saber qué tipo de máquina es, cuántos ejes maneja, qué arquitectura usa.

```python
project = load_project("/mnt/user-data/uploads/MAQUINA_DESCONOCIDA.L5X")
print(project.mapa_mental)
```

El Mapa Mental responde directamente las cuatro preguntas del usuario en su sección "Identidad" + "Arquitectura física" + "Mapa funcional de ejes". Si el usuario pide más detalle sobre un eje específico, se aplica lupa:

```python
project.get_routine("MotionControl", "Axis_Drive_Rolls")
```

### Ejemplo 2 — Diagnóstico causal de comportamiento anómalo (CASO PARADIGMA)

> **Usuario:** Tenemos problema en el empalme: el debobinador arranca muy rápido y se enreda al cargar el rollo nuevo.

Flujo esperado en v0.1 (5-7 turnos, guía manual):

**Turno 1 (Claude):** Carga el L5X y muestra el Mapa Mental. Identifica AOIs relacionadas con empalme (`AHT_CtcSplicer`, `CtcDiatecSplicer`, etc.) y los debobinadores presentes. Pregunta al usuario por contexto: ¿el síntoma ocurre solo en empalme con máquina andando o también en arranque desde cero?

```python
project.search("Splice")
project.search("Unwinder")
```

**Turno 2 (Usuario):** Solo en empalme con máquina andando.

**Turno 3 (Claude):** Eso apunta a la lógica de transición. Lee el AOI relevante:

```python
aoi = project.get_aoi("AHT_CtcSplicer")
print(aoi.routines["Logic"].code)
```

Identifica el cálculo del setpoint inicial (típicamente `V_new = V_master × (D_master / D_new)`). Identifica el input `HmiRollDiameter`.

**Turno 4 (Claude):** Traza manualmente el origen del input usando búsqueda:

```python
project.search("HmiRollDiameter")
```

Encuentra que es un tag controller-scoped escrito desde el HMI. Concluye: la causa más probable es que el operador cargó un D_new menor al real, lo que infla el ratio.

**Turno 5 (Claude):** Presenta hipótesis y recomendaciones (validación de procedimiento de carga, default desde corrida anterior, clamp de velocidad transitoria).

> En v0.2, los turnos 3-4 se colapsan en una sola operación con `project.trace_back("V_new")`. En v0.1 el razonamiento causal es manual pero ejecutable.

### Ejemplo 3 — Detección de código muerto

> **Usuario:** Antes de migrar este proyecto, quiero saber qué código no se usa y podría limpiarse.

En v0.1 esta capacidad es **manual y guiada** — el caso #5 del catálogo de casos lo confirma. El flujo es:

1. **Identificar candidatos desde el Mapa Mental.** El Mapa Mental ya lista los AOIs definidos, los programas, las rutinas y los tags principales. El modelo recorre esa lista para enumerar los AOIs y rutinas a verificar.

2. **Verificar uso con `search()`.** Para cada AOI candidato:

   ```python
   hits = project.search("MiAOI")
   # Si solo aparece en su propia definición y no en código que lo invoque,
   # es un AOI declarado pero no usado.
   ```

3. **Inspeccionar dudas con la lupa.** Si un hit es ambiguo, leer la rutina/AOI específica para confirmar:

   ```python
   project.get_routine(programa, rutina)
   ```

4. **Presentar al usuario una lista priorizada** de candidatos a limpieza, con el contexto de cómo se llegó a cada conclusión. El modelo es transparente sobre que esto NO es exhaustivo: una verificación automática y completa es capacidad v0.2.

> En v0.2, esto será un reporte automático: `project.dead_code_report()` con cobertura completa. En v0.1, la fortaleza del flujo manual es que el modelo explica su razonamiento y deja al usuario validar cada decisión antes de borrar nada.

## Notas de implementación para el modelo

- **Siempre cargar el proyecto antes de responder preguntas técnicas sobre él.** No inventar tags, AOIs, ni rutinas que no estén verificados en el modelo.
- **El Mapa Mental es la fuente de verdad estructural.** Para preguntas estructurales no llamar funciones adicionales — responder desde el Mapa Mental ya cargado.
- **La lupa se aplica solo cuando se necesita.** No cargar todas las rutinas en contexto. Cargar la específica que la pregunta requiere.
- **Honestidad sobre limitaciones.** Si una pregunta requiere trace causal automático, decir explícitamente "v0.1 hace esto manualmente, voy a guiarte paso a paso" en lugar de fingir capacidades que no existen.
- **Si el parser falla** sobre un L5X concreto, reportar el error con contexto (versión Studio 5000, controlador, schema) y proponer alternativas — no intentar recuperarse silenciosamente.

## Casos de prueba de referencia

- `CINTA_LAMINADA_M2_2024.L5X` (1.2 MB, Studio 5000 v20.01, ControlLogix 1768-L43) — caso base de validación v0.1
- Proyectos adicionales se agregan a medida que aparezcan en el trabajo real

---

*v0.1 · Skill perteneciente al proyecto Rockwell Project Comprehender. Para detalles arquitectónicos ver `02_Arquitectura_Skill.md`. Para roadmap ver `00_Vision_y_Roadmap.md`. Para decisiones técnicas ver `01_Decisiones_Tecnicas.md`.*
