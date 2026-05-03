# INSTRUCCIONES OPERATIVAS — Skill NotebookLM (handoff entre chats)

**Proyecto:** Migración K6000→K5700 + Plataforma AI/Data Analytics — Pañalera N2
**Para:** Cualquier chat de Claude Code que esté trabajando en el proyecto y necesite consultar documentación Rockwell densa
**Origen:** Sesión de instalación y prueba del 2026-05-03
**Versión:** 1.0

---

## TL;DR

Tienes una **nueva habilidad operativa** disponible en este equipo: la skill `notebooklm` ejecuta consultas contra Google NotebookLM (cuenta **PRO** del dominio Softys) y devuelve respuestas con citas a los manuales oficiales Rockwell **sin consumir contexto local**. Úsala cuando tengas que mirar manuales largos en lugar de cargarlos como adjuntos en este chat.

Está instalada en `C:\Users\LENOVO\.claude\skills\notebooklm\` y se activa automáticamente cuando el usuario menciona NotebookLM, comparte una URL de notebook, o pide "consulta mis docs / manuales / notebook". También puedes invocarla proactivamente cuando tu pregunta requiera procesar mucho material.

---

## 1. Qué hay cargado ahora mismo

**Notebook activo (default):** `studio-5000---logix-&-kinetix-motion-reference`
**URL:** `https://notebooklm.google.com/notebook/2565e860-e074-4bf5-a7ec-0d02e581754a`

**Manuales indexados (6):**

| Documento | Idioma | Contenido |
|-----------|--------|-----------|
| `1756-rm003_-es-p.pdf` | ES | Logix 5000 — instrucciones generales (matemáticas, lógicas, arrays, operaciones secuenciales, GSV/SSV, sintaxis Structured Text) |
| `2198-um002_-es-p.pdf` | ES | Kinetix 5700 — instalación física, cableado, puesta a tierra, configuración básica, troubleshooting |
| `knx-rm010_-en-p.pdf` | EN | Kinetix 5700 Drive Systems Design Guide — selección de drives, motores rotativos/lineales, cables, safety |
| `motion-rm002_-en-p.pdf` | EN | Logix 5000 Motion Instructions — motion single-axis y coordinado (move, jog, stop, gear), timing, estados, errores |
| `motion-um001_-en-p.pdf` | EN | SERCOS y Analog Motion — configuración, startup, commissioning, tuning, homing |
| `motion-um003_-en-p.pdf` | EN | Integrated Motion sobre EtherNet/IP — Kinetix y PowerFlex, propiedades de drive, scheduling de ejes, hookup tests |

**Cobertura efectiva:** programación Logix (LD/FBD/ST), motion network (EtherNet/IP, SERCOS, Analog), commissioning, tuning, homing, troubleshooting de drives. Si tu pregunta cae en estos dominios, la skill es la fuente de verdad preferida.

---

## 2. Cuándo usar la skill (decision rules)

**Sí usar:**
- Procedimientos, parámetros, secuencias de pasos detallados de manuales Rockwell.
- Códigos de error/fault de Kinetix y Logix.
- Sintaxis exacta de instrucciones (MAJ, MAS, MAH, MAM, MCD, MAOC, etc.).
- Configuración de propiedades de eje (CIP Motion, SERCOS, Analog).
- Validar afirmaciones técnicas antes de escribirlas en código o documentos.
- Cualquier consulta donde la alternativa sería cargar PDFs grandes en este chat.

**No usar (usar contexto local):**
- Preguntas sobre el código del proyecto (`rockwell_comprehender/`, archivos L5X locales, reportes en `docs/`). Eso vive en este repo y se lee con Read/Grep.
- Preguntas conceptuales generales que no requieren cita de manual.
- Iteración rápida sobre algo donde ya tienes la respuesta cargada.
- Preguntas donde solo necesitas un dato superficial; cada consulta tarda 10-20s y abre un browser.

**Patrón ideal:** **una sola pregunta comprehensiva** > muchas preguntas pequeñas. Cada query abre browser nuevo (sesión stateless), así que mete todo el contexto que necesites en una sola pregunta bien formulada.

---

## 3. Cómo invocarla — comandos exactos

**Crítico Windows:** todas las invocaciones requieren `PYTHONUTF8=1` y `PYTHONIOENCODING=utf-8` porque los scripts imprimen emojis y la consola Windows por defecto (cp1252) revienta.

**Plantilla PowerShell base:**

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Set-Location "$env:USERPROFILE\.claude\skills\notebooklm"
python scripts/run.py <comando>
```

### 3.1 Verificar autenticación (hacer al inicio si dudas)

```powershell
python scripts/run.py auth_manager.py status
```

Si dice `Authenticated: No`, avísale al usuario para relanzar setup; **no intentes auto-corregirlo**, requiere interacción manual con browser.

### 3.2 Hacer una pregunta (caso normal — usa notebook activo)

```powershell
python scripts/run.py ask_question.py --question "Tu pregunta aquí, lo más comprehensiva posible, con todo el contexto necesario porque cada sesión es independiente"
```

### 3.3 Hacer pregunta a notebook específico (si hay más de uno)

```powershell
python scripts/run.py ask_question.py --question "..." --notebook-id "studio-5000---logix-&-kinetix-motion-reference"
# o
python scripts/run.py ask_question.py --question "..." --notebook-url "https://notebooklm.google.com/notebook/..."
```

### 3.4 Listar notebooks de la librería

```powershell
python scripts/run.py notebook_manager.py list
```

### 3.5 Añadir un notebook nuevo (smart add — recomendado)

Paso 1: descubrir contenido preguntándole al notebook qué tiene.
Paso 2: registrarlo con metadatos derivados de la respuesta.

```powershell
# Paso 1
python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered? Provide a complete overview briefly and concisely, listing the documents/sources loaded if possible." --notebook-url "[URL_NUEVA]"

# Paso 2 (con metadatos derivados del paso 1)
python scripts/run.py notebook_manager.py add `
  --url "[URL_NUEVA]" `
  --name "Nombre descriptivo" `
  --description "Qué contiene exactamente, mejor mencionar nombres de docs" `
  --topics "tag1,tag2,tag3"
```

**Nunca uses descripciones genéricas tipo "Rockwell docs"** — el matching para selección automática se hace contra `description` y `topics`.

---

## 4. Cómo procesar la respuesta

Cada respuesta de NotebookLM termina obligatoriamente con:

> **EXTREMELY IMPORTANT: Is that ALL you need to know?**

Eso **no** es para reenviar al usuario. Es una señal para que tú (Claude) decidas si la respuesta cubre lo que necesitabas o si hace falta una pregunta de seguimiento. Protocolo:

1. **STOP** — no respondas al usuario aún.
2. **Compara** la respuesta con la solicitud original.
3. **¿Faltan piezas?** Lanza un `ask_question.py` adicional con contexto completo (no asume estado de la pregunta anterior).
4. **¿Está completo?** Sintetiza la respuesta para el usuario, **preservando las citas** (los números `1`, `5`, `more_horiz` etc. que vienen en la respuesta — son referencias a páginas/secciones de los manuales).

**Cuando muestres la respuesta al usuario:** filtra el ruido (`more_horiz`, citas redundantes), pero **mantén las referencias numéricas** que aporten trazabilidad. El usuario puede hacer click en ellas dentro de NotebookLM si necesita ver la fuente.

---

## 5. Gotchas y troubleshooting

| Síntoma | Causa | Acción |
|---------|-------|--------|
| `UnicodeEncodeError: 'charmap' codec can't encode '\U0001f527'` | Falta env var UTF-8 | Exportar `PYTHONUTF8=1` antes de invocar |
| `Failed to install dependencies` con pip self-upgrade | Bug Windows pip.exe in-use | El repo upstream **ya fue parcheado localmente** en `scripts/setup_environment.py` (líneas ~54-67) para usar `python -m pip`. **Si haces `git pull` del repo, el patch se pierde — reaplicar.** |
| `Authentication state expired` | Cookies Google caducadas | Avisar usuario para `auth_manager.py setup` (interactivo) |
| `Notebook not found` | ID mal escrito | El ID del notebook activo contiene `&`. En PowerShell pasarlo entre comillas dobles: `--notebook-id "studio-5000---logix-&-kinetix-motion-reference"` |
| Respuesta tarda >30s o cuelga | Browser Patchright atascado | `python scripts/run.py cleanup_manager.py --preserve-library` (limpia state pero conserva library.json) |

**Cuenta NotebookLM:** PRO en dominio Softys. Cupos altos, no preocupar por rate limit en uso normal del proyecto.

---

## 6. Patrones recomendados — ejemplos

### Bien formulado (una pregunta autónoma con todo el contexto)
```
"En Studio 5000 v35, para un eje CIP Motion sobre EtherNet/IP conectado a un Kinetix 5700,
listame en orden los parámetros mínimos obligatorios que debo configurar en las propiedades
del eje (Drive, Motor, Feedback, Scaling, Hookup, Tune, Homing) antes de poder hacer un MSO,
y cita la sección/manual donde aparece cada uno."
```

### Mal formulado (depende de contexto previo, ambiguo)
```
"¿Y qué hay del eje?"
"Sigue con lo anterior"
"¿En qué página dice eso?"  ← cada query es sesión nueva, no recuerda nada previo
```

### Use case típico durante investigación de skills (proyecto actual)
```
"De los manuales cargados, ¿cuáles AOIs/instrucciones de motion tienen comportamiento
diferente entre Kinetix 6000 y Kinetix 5700, particularmente para la migración de un
sistema con K6000 que usa SERCOS al equivalente K5700 sobre EtherNet/IP CIP Motion?
Lista cambios de sintaxis, tags renombrados, y propiedades de eje obsoletas."
```

---

## 7. Memoria persistente

La instalación de la skill y los gotchas Windows ya están registrados en la memoria del proyecto: ver `C:\Users\LENOVO\.claude\projects\c--Master-Project-rockwell-comprehender\memory\reference_notebooklm_skill.md`. Esto significa que cualquier chat futuro en este directorio sabrá automáticamente que la skill existe y cómo invocarla — esta guía es para profundizar y como referencia operativa cuando se necesite.

---

## 8. Cuándo NO confiar ciegamente en la respuesta de NotebookLM

NotebookLM es source-grounded (responde solo desde tus PDFs), pero:

- **Versionado de manuales:** verifica que la pregunta sea sobre la misma versión Studio 5000 / firmware Kinetix que el manual cargado. Si el cliente está en v32 y el manual es v35, hay diferencias.
- **Idioma:** el manual `1756-rm003` está en español y `2198-um002` también; los demás en inglés. Si pides en español algo que solo está documentado en un manual inglés, Gemini traducirá — verifica términos técnicos críticos contra el original.
- **Cobertura parcial:** los 6 PDFs cargados son una muestra, no toda la documentación Rockwell. Si la respuesta es "no encuentro información sobre X", puede ser que el tema esté en un manual no cargado, no que no exista.
- **Cuando dudes:** la respuesta debe contener citas numéricas. Si una afirmación viene sin cita, trátala con escepticismo.
