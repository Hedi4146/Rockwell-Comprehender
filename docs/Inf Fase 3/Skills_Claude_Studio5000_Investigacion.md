# INVESTIGACIÓN: SKILLS DE CLAUDE PARA AUTOMATIZACIÓN BAJO STUDIO 5000

**Proyecto:** Migración K6000→K5700 + Plataforma AI/Data Analytics — Pañalera N2
**Autor:** Análisis técnico para Hedi Vásquez · Softys Colombia
**Fecha:** 2026-05-01
**Versión:** 1.0

---

## TL;DR — Resumen ejecutivo

Existe un ecosistema funcional —pero fragmentado— de herramientas para automatizar Studio 5000 con código y/o IA. Las más maduras son las de **lectura/análisis de archivos L5X**; las de **generación de código ladder importable** son aún experimentales y poco confiables. El **SDK oficial de Rockwell (Logix Designer SDK 2.01+)** es robusto pero tiene fricciones de instalación (Windows + Python 3.12 + licencia Studio 5000 Professional).

Para tu proyecto, recomiendo construir un conjunto inicial de **5 skills priorizados** —cuatro de análisis/transformación de L5X y uno de búsqueda en manuales Rockwell— que aportan valor inmediato sin depender del SDK ni de licencias adicionales. Skills de generación de código y de interacción en línea con PLC se posponen como Fase 2 una vez validada la metodología.

---

## 1. Marco conceptual: ¿qué es un *skill* en Claude?

Un **skill** en la plataforma Claude (Anthropic) es una carpeta empaquetada que contiene instrucciones específicas de dominio que Claude carga cuando detecta una tarea relevante. Estructura:

```
skill-name/
├── SKILL.md              ← Único requerido. YAML frontmatter + instrucciones
├── scripts/              ← Código ejecutable (Python, bash, etc.)
├── references/           ← Documentación técnica que Claude lee bajo demanda
└── assets/               ← Plantillas, archivos de salida, esquemas
```

El mecanismo es de **divulgación progresiva** en tres niveles:

| Nivel | Contenido | Tamaño típico | Cuándo se carga |
|-------|-----------|---------------|-----------------|
| 1. Metadata | name + description (frontmatter) | ~100 palabras | Siempre en contexto |
| 2. Cuerpo SKILL.md | Instrucciones detalladas | <500 líneas | Cuando el skill se activa |
| 3. Recursos | Scripts, plantillas, refs | Sin límite | Bajo demanda |

**Implicación clave para Studio 5000:** un skill puede empaquetar plantillas L5X, scripts de parsing, tablas de equivalencia K6000↔K5700, listas de instrucciones válidas, etc. Una vez instalado, no requiere repetir ese conocimiento en cada conversación.

---

## 2. Estado del arte — Ecosistema técnico Studio 5000 + IA/automatización

### 2.1 Herramientas oficiales de Rockwell

| Herramienta | Versión actual | Capacidad | Limitaciones | Aplicabilidad a tu proyecto |
|-------------|----------------|-----------|--------------|------------------------------|
| **Logix Designer SDK** | 2.01+ | Automatización de UI: descargar/cargar proyectos, scripting de cambios, modificar tags online/offline, gestión de SD cards | Solo Windows, Python 3.12 estricto, requiere Studio 5000 v31+ instalado, licencia **Professional Edition** | Útil para despliegue masivo en flota, no crítico para Fase 1 |
| **FactoryTalk Logix Echo V2** | Integrado en v35+ | PLC virtual, simulación con motion (Axis-Test Mode para Kinetix) | Requiere licencia | Muy útil para validar migración K5700 sin hardware |
| **L5X export/import** | Soportado v17+ | XML legible, importación selectiva (rutinas, programas, AOIs) | Schema cambia entre versiones (Schema 4.x en v30+) | **Pieza central** de cualquier estrategia de skills |
| **L5K** | Legacy | Texto ASCII previo a L5X | Menos flexible, no permite exportar partes | Evitar |
| **ACD format** | Binario propietario | Formato nativo de proyecto | No editable directamente sin SDK o librerías terceras | Requiere extracción intermedia |

### 2.2 Librerías de comunidad (Python / .NET)

| Proyecto | Lenguaje | Función | Madurez | Uso para skills |
|----------|----------|---------|---------|-----------------|
| **`l5x` (PyPI)** | Python | Lectura/escritura L5X con API pythónica (Project, Controller, Tags) | Estable, mantenida | ✅ Base sólida |
| **`pyldsdk`** | Python | Wrapper sobre Logix Designer SDK oficial (descargas a PLC, etc.) | Comunidad, requiere DLLs del SDK | ⚠️ Solo si se acepta dependencia del SDK |
| **`acd` (hutcheb)** | Python | Parsea ACD binario → SQLite → objetos Python; serializa a L5X | Beta, probado v20-v35 | ✅ Alternativa para entrar al ACD sin SDK |
| **`L5Sharp`** | .NET 8 | API tipada para L5X con LINQ | Estable | Alternativa si se prefiere .NET |
| **`l5x2c`** | Python | Transcompila ladder a C para verificación formal (CBMC) | Investigación | 🔬 Experimental, interesante para safety |
| **`pycomm3`** | Python | Comunicación CIP en línea con PLC (lectura/escritura tags) | Maduro, ampliamente usado | ✅ Ya seleccionado para tu plataforma de datos |
| **`pylogix`** | Python | Similar a pycomm3, comunicación en línea | Maduro | Alternativa a pycomm3 |
| **Simulink PLC Coder** | MATLAB | Genera ST/AOIs desde Simulink | Comercial (MathWorks) | No relevante salvo trabajo con modelos |

### 2.3 Proyectos AI + Studio 5000 ya existentes

**`rivie13/studio5000-AI-Assistant`** (GitHub, 14 estrellas) — Servidor MCP que conecta modelos IA con el SDK de Studio 5000 y la documentación interna. Ofrece 18 herramientas: generación de ladder desde lenguaje natural, creación de proyectos L5X/ACD, búsqueda semántica en proyectos L5X de hasta 49k líneas, indexado de PDFs técnicos con análisis vectorial.

**Auto-evaluación honesta del proyecto (de su propio README):**
- ✅ Funciona bien: parsing de docs Rockwell, búsqueda vectorial L5X, validación rápida de instrucciones, generación de ACDs vacíos
- ⚠️ Funciona parcialmente: generación de L5X con lógica (problemas de formato RLL, requiere correcciones manuales)
- 🔧 No funciona confiablemente: importación parcial vía SDK, automatización end-to-end

**Lectura para nosotros:** la generación automática de **ladder válido importable** sigue siendo un problema abierto. La automatización confiable hoy está en **lectura, análisis y transformación** de L5X, no en generación.

### 2.4 Lo que NO existe (gap del ecosistema)

| Capacidad ausente | Por qué importa para ti |
|-------------------|--------------------------|
| Generador automático de configuraciones de eje Kinetix con templates | Configurar 53 ejes K5700 a mano es repetitivo y propenso a error |
| Mapeador K6000 → K5700 con tabla de equivalencias de atributos | La conversión de configuración entre familias no está automatizada |
| Validador de coherencia eléctrica de rack K5700 (potencias, fuentes, derating) | Hoy se hace manualmente con hojas de cálculo |
| Generador de configuración Telegraf/OPC UA desde L5X | Las ~510 tags requerirían trabajo manual significativo |
| Auditor de safety logic L5X con reporte normativo (SIL/PLe) | La documentación de safety hoy es manual |

**Estos gaps son exactamente donde un skill propio tiene mayor ROI para tu proyecto.**

---

## 3. Mapeo a tu proyecto — ¿Dónde aporta cada cosa?

### 3.1 Fase 1 — Migración K6000→K5700

| Actividad del proyecto | Volumen | Skill ayuda | Tipo de ayuda |
|------------------------|---------|-------------|----------------|
| Configurar 53 ejes K5700 (Side Panel + Central + AQL) | 53 ejes × ~30 atributos | ✅ Alto | Generación + validación |
| Distribuir drives en 7 racks con balance de potencia | 7 racks | ✅ Medio | Validación |
| Mapear safety I/O distribuido (CR30 → L8SP) | 5 controllers consolidados | ✅ Medio | Análisis L5X + reporte |
| Generar BoM con códigos Rockwell + precio Sonepar | ~150 líneas | ✅ Alto | Generación |
| Producir TDR/diagramas/Gantt | Documental | ✅ Alto | Generación de documentos |
| Validar lógica de safety (`.sk` decryption) | 1 programa safety | ⚠️ Medio | Análisis estructural |
| Validar compatibilidad cables 2090-K6CK-D15M | Verificación | ❌ Bajo | Ya resuelto manualmente |

### 3.2 Fase 2 — Plataforma AI/Data Analytics

| Actividad del proyecto | Volumen | Skill ayuda | Tipo de ayuda |
|------------------------|---------|-------------|----------------|
| Configurar ~510 tags desde cero post-migración | 510 tags | ✅ Muy alto | Extracción + mapeo |
| Definir schema InfluxDB (buckets, measurements, tags) | Schema completo | ✅ Alto | Generación |
| Configurar Telegraf (OPC UA o pycomm3 wrapper) | Config completa | ✅ Alto | Generación |
| Crear dashboards Grafana iniciales | 5–10 dashboards | ✅ Medio | Generación de JSON |
| Cliente pycomm3 con tag mapping y reconexión | Código Python | ✅ Alto | Generación |
| Documentación de tags (descripción, unidad, criticidad) | 510 tags | ✅ Muy alto | Enriquecimiento |

---

## 4. Catálogo de skills propuestos

A continuación, 15 candidatos. Cada uno especifica: propósito, entrada, salida, esfuerzo de construcción, valor para tu proyecto.

### 4.1 Skills de análisis de L5X (Fase 1 + transversal)

#### S01 — `l5x-tag-extractor`
- **Propósito:** Extrae todas las tags (controlador, programa, AOI) de un L5X a CSV/JSON con jerarquía, tipo, descripción, alias.
- **Entrada:** Archivo `.L5X` exportado de Studio 5000.
- **Salida:** CSV con columnas: `Scope, Path, Name, DataType, Alias, Dimensions, Description, ExternalAccess`.
- **Tecnología:** Python + librería `l5x` o `xml.etree.ElementTree`.
- **Esfuerzo:** Bajo (1–2 días).
- **Valor proyecto:** Crítico para Fase 2 (tag list para OPC UA / pycomm3).

#### S02 — `l5x-motion-axis-extractor`
- **Propósito:** Extrae configuración de todos los ejes Motion (Cartesian, Coordinated, Kinetix) con sus parámetros: `MotorType, FeedbackType, ConversionConstant, MaxSpeed, MaxAccel, Gains`, etc.
- **Entrada:** L5X del proyecto migrado (o legacy).
- **Salida:** Excel con una hoja por módulo (Side Panel, Central, AQL) y una fila por eje con todos sus atributos críticos.
- **Tecnología:** Python + parsing XML.
- **Esfuerzo:** Medio (3–5 días).
- **Valor proyecto:** Alto para auditoría de la migración y como punto de comparación K6000 vs K5700.

#### S03 — `l5x-io-tree-builder`
- **Propósito:** Reconstruye el árbol I/O (jerarquía AENT/AENTR/Module → Slot → Channel) desde el L5X y genera diagrama Mermaid + tabla de IPs.
- **Entrada:** L5X.
- **Salida:** Markdown con diagrama Mermaid + tabla `Adapter / IP / Slot / Module / Tags`.
- **Esfuerzo:** Medio (3–5 días).
- **Valor proyecto:** Alto — automatiza un entregable que hoy haces manualmente para cada documento (ya tienes ejemplo en tu archivo `Diagramas_Red_K5700_Mermaid_v5.md`).

#### S04 — `l5x-diff-reporter`
- **Propósito:** Compara dos archivos L5X (versión antes/después) y genera reporte estructurado de cambios: rutinas añadidas/eliminadas/modificadas, tags nuevos, cambios en configuración de módulos, cambios en motion groups.
- **Entrada:** Dos archivos L5X.
- **Salida:** Reporte HTML/Markdown con secciones: `Added, Removed, Modified` por categoría.
- **Tecnología:** Python + diff XML estructural.
- **Esfuerzo:** Medio-alto (5–7 días).
- **Valor proyecto:** Alto durante migración para validar que cambios planeados están aplicados y nada más se modificó accidentalmente.

#### S05 — `l5x-safety-auditor`
- **Propósito:** Analiza programas Safety en un L5X y genera reporte de: cantidad de E-Stops, zonas de seguridad detectadas, instrucciones safety usadas (STO, SS1, SLS, SBC), routing entre Safety I/O y axes, posibles problemas de migración a L8SP.
- **Entrada:** L5X con safety. Si está cifrado, requiere `.sk` source key file (manejo lateral por usuario).
- **Salida:** Reporte estructurado + checklist de validación CIP Safety / EtherNet/IP.
- **Esfuerzo:** Alto (10+ días) — requiere comprensión profunda de modelos safety Rockwell.
- **Valor proyecto:** Alto pero diferible — útil para certificación final.

### 4.2 Skills de generación / transformación (Fase 1)

#### S06 — `k5700-axis-template-generator`
- **Propósito:** Dado un motor (catálogo MPL/MPM/MPF), un drive K5700 (D006/D012/D020/D032/D057), y opcionalmente parámetros mecánicos (relación, paso), genera un fragmento L5X importable con la configuración del eje conforme a las prácticas Rockwell (publicación 2198-UM002, Motion-RM003).
- **Entrada:** YAML/JSON con motor, drive, opciones de feedback (motor only / dual), seguridad (Motion+Safety).
- **Salida:** Fragmento L5X importable como AddOnInstruction o Tag/Module en un programa existente.
- **Esfuerzo:** Alto (10–15 días) — requiere validación cuidadosa de schema L5X y testing en Studio 5000.
- **Valor proyecto:** Muy alto si funciona — escalaría a 53 ejes; pero **riesgo:** los proyectos similares en GitHub reportan problemas de formato L5X.
- **Recomendación:** **No empezar por aquí.** Validar primero con generación a Excel + import manual (S01–S03).

#### S07 — `k5700-rack-validator`
- **Propósito:** Valida que una distribución de drives en racks K5700 sea eléctrica y térmicamente correcta:
  - Suma de corriente DC-bus por rack ≤ capacidad de fuente (P031/P070/P141/P208).
  - Cantidad de drives en bus compartido ≤ máximo permitido.
  - Coherencia entre filtros DBR y configuración de rack.
  - Derating por temperatura ambiente.
- **Entrada:** Tabla con `Rack, Slot, Drive, Motor, Continuous_Current, Peak_Current`.
- **Salida:** Reporte con luz verde/amarilla/roja por rack + recomendaciones.
- **Esfuerzo:** Medio (5 días).
- **Valor proyecto:** Alto — confirma cuantitativamente la distribución que hoy validas con criterio experto. Tu BoM ya muestra P141 + P208 distribuidos.

#### S08 — `motion-bom-builder`
- **Propósito:** A partir de la lista final de ejes con drives + fuentes + filtros + cables, genera BoM Excel formateado con códigos Rockwell, descripciones, cantidades, precios Sonepar (de catálogo cargado en el skill), totales por módulo y proyecto.
- **Entrada:** Configuración de ejes (CSV/YAML).
- **Salida:** Excel multi-hoja con BoM, cotización por proveedor, resumen ejecutivo.
- **Esfuerzo:** Bajo-medio (3–5 días).
- **Valor proyecto:** Alto — automatiza un entregable recurrente.

### 4.3 Skills de Fase 2 — Data Analytics

#### S09 — `plc-tag-to-opcua-mapper`
- **Propósito:** A partir del L5X (o tag list CSV), genera el árbol OPC UA equivalente con namespaces, browse path, displayName, dataType OPC UA, descripción enriquecida automáticamente desde patrones de nombre.
- **Entrada:** L5X o CSV de tags.
- **Salida:** Archivo de configuración OPC UA (formato dependiente del servidor; típicamente XML o JSON) + Excel de mapeo trazable.
- **Esfuerzo:** Medio (5–7 días).
- **Valor proyecto:** Crítico — ahorra cientos de horas para configurar las ~510 tags si optas por la ruta RSLinx Gateway OPC UA.

#### S10 — `telegraf-config-generator`
- **Propósito:** Genera archivo `telegraf.conf` con plugin `opcua` (o `cipanymotion` / `pycomm3` wrapper) configurado para apuntar al PLC, con las tags correctas, intervalos de muestreo diferenciados por tipo de tag (motion = 100ms, process = 1s, status = 10s), y output InfluxDB v2.
- **Entrada:** Tag list con metadata (criticidad, frecuencia deseada).
- **Salida:** `telegraf.conf` listo para deploy.
- **Esfuerzo:** Bajo-medio (3 días).
- **Valor proyecto:** Alto — encaja directo con tu stack ya seleccionado (Ubuntu + Docker + InfluxDB 2.7).

#### S11 — `pycomm3-client-scaffolder`
- **Propósito:** Genera un cliente Python `pycomm3` listo para producción con: clase wrapper, manejo de reconexión exponencial, batching de tags por límite CIP, logging estructurado, mapeo tag→variable Python automático.
- **Entrada:** Tag list + parámetros de conexión.
- **Salida:** Proyecto Python completo (modulado, con tests, Dockerfile).
- **Esfuerzo:** Medio (5–7 días).
- **Valor proyecto:** Alto — sustituye al fallback que ya tenías arquitecturado.

#### S12 — `influxdb-grafana-bootstrapper`
- **Propósito:** A partir de una tag list categorizada (motion / process / safety / production), genera:
  - Schema InfluxDB con bucket strategy, retention policies, downsampling tasks.
  - Dashboards Grafana JSON parametrizados (uno por categoría) con paneles típicos: tendencias, gauges, tablas de alarmas.
- **Entrada:** Tag list enriquecida.
- **Salida:** Conjunto de archivos JSON listos para importar.
- **Esfuerzo:** Medio-alto (7–10 días).
- **Valor proyecto:** Muy alto — acelera de manera dramática el time-to-value del piloto.

### 4.4 Skills transversales / soporte

#### S13 — `rockwell-docs-search`
- **Propósito:** Búsqueda semántica + citada en el corpus de manuales Rockwell relevantes (GMC-RM010, Motion-RM003, 2198-UM002, 1756-RM084, MOTION-AT005C, etc.) cargados como referencias del skill.
- **Entrada:** Pregunta en lenguaje natural.
- **Salida:** Respuesta con citas exactas (publicación, página, párrafo).
- **Esfuerzo:** Medio (5 días) — el reto es la curaduría del corpus.
- **Valor proyecto:** Muy alto — elimina tiempo de búsqueda manual y reduce errores de interpretación.

#### S14 — `studio5000-instructions-validator`
- **Propósito:** Valida un fragmento de ladder/ST contra la base de instrucciones oficiales (TON, MOV, MAH, MAJ, MAFR, GSV, SSV, etc.) y reporta uso correcto de operandos, sintaxis, lenguajes soportados.
- **Entrada:** Fragmento de código (texto plano o L5X).
- **Salida:** Reporte de errores/advertencias línea por línea.
- **Esfuerzo:** Medio (5–7 días).
- **Valor proyecto:** Medio — útil durante revisión de código de integradores.

#### S15 — `network-topology-mermaid`
- **Propósito:** Genera diagrama Mermaid de topología OT (PLCs + switches Stratix + ETAPs + DLR rings + adapters AENT) a partir de descripción tabular o L5X.
- **Entrada:** CSV/YAML de nodos + enlaces, o L5X.
- **Salida:** Markdown con bloques Mermaid renderizables.
- **Esfuerzo:** Bajo (2–3 días).
- **Valor proyecto:** Medio — ya produces estos diagramas, pero el skill los hace consistentes y rápidos.

---

## 5. Priorización por ROI

Matriz de priorización considerando: (a) valor para el proyecto actual, (b) esfuerzo de construcción, (c) riesgo técnico, (d) reusabilidad futura.

| Skill | Valor | Esfuerzo | Riesgo | Reusabilidad | **Prioridad** |
|-------|:-----:|:--------:|:------:|:------------:|:-------------:|
| S01 `l5x-tag-extractor` | 🟢🟢🟢 | 🟢 | 🟢 | 🟢🟢🟢 | **P0** |
| S13 `rockwell-docs-search` | 🟢🟢🟢 | 🟡 | 🟡 | 🟢🟢🟢 | **P0** |
| S03 `l5x-io-tree-builder` | 🟢🟢 | 🟡 | 🟢 | 🟢🟢 | **P1** |
| S08 `motion-bom-builder` | 🟢🟢 | 🟢 | 🟢 | 🟢🟢 | **P1** |
| S10 `telegraf-config-generator` | 🟢🟢 | 🟢 | 🟢 | 🟢🟢 | **P1** |
| S02 `l5x-motion-axis-extractor` | 🟢🟢 | 🟡 | 🟡 | 🟢🟢 | **P2** |
| S09 `plc-tag-to-opcua-mapper` | 🟢🟢🟢 | 🟡 | 🟡 | 🟢🟢 | **P2** |
| S11 `pycomm3-client-scaffolder` | 🟢🟢 | 🟡 | 🟢 | 🟢🟢 | **P2** |
| S07 `k5700-rack-validator` | 🟢🟢 | 🟡 | 🟡 | 🟢 | **P2** |
| S12 `influxdb-grafana-bootstrapper` | 🟢🟢🟢 | 🔴 | 🟡 | 🟢🟢 | **P3** |
| S04 `l5x-diff-reporter` | 🟢🟢 | 🟡 | 🟡 | 🟢🟢 | **P3** |
| S15 `network-topology-mermaid` | 🟢 | 🟢 | 🟢 | 🟢 | **P3** |
| S14 `studio5000-instructions-validator` | 🟢 | 🟡 | 🟡 | 🟢 | **P4** |
| S05 `l5x-safety-auditor` | 🟢🟢 | 🔴 | 🔴 | 🟢 | **P4** (diferir) |
| S06 `k5700-axis-template-generator` | 🟢🟢🟢 | 🔴 | 🔴 | 🟢🟢 | **P4** (diferir) |

Leyenda: 🟢 favorable · 🟡 medio · 🔴 desfavorable

**Plan recomendado de tres olas:**

- **Ola 1 (P0–P1, ~3–4 semanas de trabajo):** S01, S13, S03, S08, S10. Cubren tag extraction, búsqueda en docs, diagramas, BoM y config Telegraf. Bajo riesgo, valor inmediato en ambas fases.
- **Ola 2 (P2, ~3–4 semanas):** S02, S09, S11, S07. Profundizan en migración K5700 y plataforma de datos.
- **Ola 3 (P3–P4):** El resto. S06 (generador de eje K5700) se evalúa solo si ya tenemos confianza tras el éxito de Ola 1 y 2.

---

## 6. Limitaciones técnicas honestas

Hay barreras reales que conviene tener presentes:

**a) Generación de ladder importable es frágil.** El proyecto comunitario `studio5000-AI-Assistant` reporta problemas de formato RLL; mi recomendación es no apostar la primera ola ahí. Cuando se aborde (S06), haremos pilotos pequeños y validación manual en Studio 5000 antes de escalar.

**b) Los skills construidos para mí (Claude) NO se ejecutan directamente sobre Studio 5000.** Operan sobre archivos exportados (L5X, CSV) o generan archivos para importar. La interacción en línea con el PLC requiere que tú ejecutes un cliente (pycomm3, SDK) en tu PC con conexión a la red OT — el skill genera el cliente, no lo opera.

**c) El SDK oficial de Rockwell tiene fricción de despliegue.** Si decidimos construir skills que usan `pyldsdk` (S06 si lo abordamos), tú necesitarás Python 3.12 + Studio 5000 v36 + licencia Professional en tu máquina. No es problema técnico, pero sí gobernanza y costo.

**d) Confidencialidad y NDA.** Cualquier skill que necesite tu L5X real para validarse requiere NDA previa; yo no puedo redistribuir tu lógica, pero el flujo de trabajo de `crear skill → probar contra tu L5X → iterar` necesita que tú compartas archivos en este chat o en tu Project. Eso ya lo manejamos hoy.

**e) El cifrado `.sk` de tus rutinas safety.** S05 requiere que descifres en Studio 5000 antes de exportar a L5X plano para que yo pueda analizarlo. El skill no rompe el cifrado; opera sobre el L5X ya descifrado por ti.

**f) Schema L5X cambia entre versiones de Studio 5000.** Las herramientas funcionan razonablemente bien para v20–v37, pero futuras versiones podrían introducir cambios. Los skills deben llevar versionado y referencia a la pub `1756-RM084` para validación de schema.

---

## 7. Plan de implementación sugerido

### Etapa 0 — Decisión y alineación (1 semana)
1. Tú revisas este documento y decides qué subset abordar primero.
2. Acordamos el alcance exacto del primer skill (probable candidato: **S01 `l5x-tag-extractor`** porque tiene el mejor ratio valor/esfuerzo y sirve a ambas fases).
3. Tú me pasas un L5X de prueba (puede ser un módulo de Pañalera N2 ya migrado, p.ej. SIDE PANEL).

### Etapa 1 — Construcción del primer skill (1–2 semanas)
1. Bosquejo de SKILL.md con descripción, ejemplo de invocación, formato de salida.
2. Implementación del script Python.
3. Test con tu L5X real → revisión por tu parte → iteración.
4. Empaquetado y entrega del archivo `.skill`.

### Etapa 2 — Validación y siguiente skill (1 semana)
1. Tú usas el skill en una tarea real del proyecto.
2. Recolectamos feedback (qué falta, qué sobra, qué cambia).
3. Aplicamos el aprendizaje al siguiente skill (probable: S13 o S03).

### Etapa 3 — Ola 1 completa (~6 semanas total)
Construcción de S01, S13, S03, S08, S10 con el mismo ciclo iterativo.

### Etapa 4 — Decisión de continuar
Tras Ola 1, evaluamos si tiene sentido continuar con Ola 2 o si los resultados ya cubren tu necesidad.

---

## 8. Conclusión y siguiente paso

El terreno es viable y hay valor real por capturar — particularmente en **lectura/análisis de L5X y generación de configuraciones de plataforma de datos**. Lo que conviene **evitar al inicio** es la generación de ladder importable, donde el estado del arte es inestable.

Mi sugerencia concreta para arrancar:

> **Construir S01 `l5x-tag-extractor` como piloto**, con tu L5X de Side Panel actual (post-migración K5700) como caso de prueba. Es un skill útil para Fase 2 (genera la base para los ~510 tags de OPC UA) y también para Fase 1 (auditoría de tags migrados). Tiene esfuerzo bajo, riesgo bajo, y nos sirve para validar el flujo de trabajo de creación de skills antes de invertir en algo más grande.

Si te parece bien, en la próxima conversación puedo:
1. Hacer el bosquejo formal del SKILL.md de S01.
2. Listar las dependencias Python concretas.
3. Definir el formato de salida exacto que necesitas (CSV, Excel, JSON).
4. Pedirte el L5X de prueba.

---

## Anexo A — Referencias técnicas consultadas

| Recurso | Tipo | Aplicabilidad |
|---------|------|---------------|
| Rockwell — Logix Designer SDK Getting Results Guide (LDSDK-GR001) | Manual oficial | SDK oficial |
| PyPI — `l5x` package | Librería Python | S01–S05 |
| GitHub — `hutcheb/acd` | Librería Python | Lectura ACD |
| GitHub — `tnunnink/L5Sharp` | Librería .NET | Alternativa .NET |
| GitHub — `aawilliams85/pyldsdk` | Wrapper Python del SDK | S06 si se aborda |
| GitHub — `rivie13/studio5000-AI-Assistant` | Servidor MCP | Referencia comparativa |
| Rockwell — 2198-UM002 (Kinetix 5700 User Manual) | Manual hardware | S06, S07 |
| Rockwell — Motion-RM003 (Integrated Motion EtherNet/IP) | Manual técnico | S02, S06 |
| Rockwell — 1756-RM084Z | Schema L5X/L5K | Validación |
| Anthropic — Skill Creator documentation | Plataforma Claude | Marco de skills |

---

*Fin del documento.*
