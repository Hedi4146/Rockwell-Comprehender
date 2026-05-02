# 03 · CASOS DE USO REALES

Catálogo de casos reales del trabajo de Hedi que la herramienta debe poder resolver. Cada caso incluye la situación, el flujo de razonamiento esperado, y los criterios de éxito para diferentes versiones del skill.

---

## Caso #1 — El empalme con velocidad excesiva (CASO PARADIGMA)

**Reportado por:** Hedi Vásquez
**Tipo:** Diagnóstico causal
**Proyecto referenciado:** CINTA_LAMINADA_M2_2024 o similar (debobinador con bailarina)

### Situación

> "Tenemos un problema: al realizar el empalme, el debobinador arranca con mucha velocidad y se enreda."

### Flujo de razonamiento esperado del ingeniero

```
SÍNTOMA: empalme → debobinador arranca rápido → enreda
   ↓
NIVEL 1: ¿qué subsistemas tocan esto?
   → Empalme + control velocidad debobinador
   ↓
NIVEL 2: ¿dónde está la lógica de empalme?
   → Buscar AOI/rutina de splice
   ↓
NIVEL 3: ¿cómo se calcula la velocidad inicial del nuevo rollo?
   → Leer fórmula en código
   ↓
NIVEL 4: ¿qué entra a esa fórmula?
   → diámetro inicial + posición danzarín + referencia máquina
   ↓
NIVEL 5: ¿de dónde viene el diámetro inicial?
   → Trazar origen del valor
   ↓
HIPÓTESIS: diámetro inicial es input HMI → operador lo cargó mal
   ↓
CONCLUSIÓN: causa raíz identificada — error humano de carga, no falla técnica
```

### Por qué este caso es paradigma

Combina las cuatro capacidades clave del skill:
1. **Mapa Mental general** — saber que "empalme" y "debobinador" son dominios del proyecto
2. **Navegación dirigida** — encontrar la AOI relevante sin búsqueda exhaustiva
3. **Lupa puntual** — leer el cálculo específico
4. **Trace causal** — rastrear inputs hasta su origen

Si el sistema resuelve esto bien, está logrado en lo esencial.

### Criterios de éxito por versión

| Versión | Comportamiento esperado | Turnos estimados |
|---------|--------------------------|------------------:|
| **v0.1** | Resuelve con guía manual de Claude. Usuario describe síntoma, Claude pide aclaraciones, navega capa por capa con consultas explícitas, llega a conclusión. | 5-7 turnos |
| **v0.2** | Trace automático de dependencias acelera la fase 5. Claude conecta el cálculo con sus inputs sin guía manual. | 3-4 turnos |
| **v0.3** | Detección automática de dominio "empalme" carga el mapa funcional relevante de inmediato. Claude propone hipótesis con confianza alta desde el segundo turno. | 1-2 turnos |

### Conversación tipo esperada (v0.1)

```
Hedi: Tenemos problema en empalme: el debobinador arranca muy rápido 
       y se enreda al cargar el rollo nuevo.

Claude: Cargo el proyecto y reviso. [carga L5X, genera mapa mental]
        El proyecto tiene varias AOIs relacionadas con empalme:
        AHT_CtcSplicer, CtcDiatecSplicer, FullSpeedSplicer. Veo dos
        debobinadores (M1 y M2) usando AHT_Unwinder.
        
        ¿El comportamiento ocurre solo en empalme con la máquina ya 
        andando, o también en arranque desde cero?

Hedi: Solo en empalme con máquina andando.

Claude: Eso apunta a la lógica de transición entre rollos. Voy a leer
        AHT_CtcSplicer para ver cómo calcula el setpoint inicial del 
        debobinador nuevo.
        [navigator.get_aoi_full("AHT_CtcSplicer")]
        
        Veo que usa una fórmula tipo: V_new = V_master × (D_master / D_new)
        donde D_new viene del input HmiRollDiameter del nuevo rollo.
        
        Antes de que el dancer empiece a corregir, el sistema usa el 
        diámetro estimado por el operador. Si ese valor es menor al 
        real → el ratio se infla → arranca con velocidad alta.

Hedi: Así parece...

Claude: Sí, la causa más probable es input HMI incorrecto. Mientras el
        operador no cargue D_new correctamente, el transitorio inicial
        siempre será inestable. Recomendaría:
        a) Validar procedimiento de carga de diámetro
        b) Considerar usar como default el último D_unwinder de la corrida
           anterior, en lugar de un valor fijo
        c) Limitar la velocidad de transitorio inicial (clamp) hasta que
           el dancer estabilice
```

### Validación

**Status:** Pendiente — caso a probar contra v0.1 cuando esté construida y validada en arquitecturas distintas.

---

## Caso #2 — Auditoría rápida de proyecto desconocido

**Reportado por:** Hedi
**Tipo:** Análisis estructural

### Situación

> "Me llega un L5X de una máquina que no conozco. Necesito en 5 minutos saber qué tipo de máquina es, cuántos ejes maneja, qué arquitectura usa, qué patrones de código sigue."

### Capacidades requeridas

- Carga rápida del L5X
- Generación inmediata de Mapa Mental
- Output legible y conciso

### Criterios de éxito

| Versión | Comportamiento |
|---------|----------------|
| **v0.1** | Mapa Mental generado en < 30 segundos cubre las 4 preguntas: tipo de máquina (inferido), N° ejes, arquitectura, framework |

### Validación

**Status:** ✅ Logrado en v0.1. Validado contra `CINTA_LAMINADA_M2_2024.L5X` (1.2 MB) y `AQL_M2.L5X` (2.9 MB) — Mapa Mental coherente generado en <1 segundo en ambos casos.

---

## Caso #3 — Comparación entre proyectos

**Reportado por:** Hedi (para flota Softys)
**Tipo:** Análisis cruzado

### Situación

> "Tengo dos máquinas similares: Pañalera 1 y Pañalera 2. Quiero saber qué difiere entre ambas — código, configuración, arquitectura."

### Capacidades requeridas

- Cargar dos proyectos en paralelo
- Generar diff estructural (tags, AOIs, programas, modules)
- Identificar diferencias relevantes vs ruido

### Criterios de éxito

| Versión | Comportamiento |
|---------|----------------|
| **v0.1** | Comparación manual guiada por Claude usando consultas a ambos proyectos |
| **v0.2+** | Reporte de diff automático con clasificación de diferencias |

### Validación

**Status:** Capacidad básica disponible en v0.1 vía carga de dos `Project` paralelos. Diff automático diferido a v0.2.

---

## Caso #4 — Plan de migración K6000 → K5700

**Reportado por:** Hedi (proyecto activo de Pañalera 2)
**Tipo:** Generación informada

### Situación

> "Tengo el L5X de la máquina actual con drives K6000 SERCOS. Quiero generar el plan de configuración equivalente con K5700 EtherNet/IP, manteniendo la lógica."

### Capacidades requeridas

- Identificar todos los ejes y su configuración actual
- Mapear motores físicos a drives K5700 apropiados
- Detectar dependencias en código que asumen SERCOS
- Generar tabla de equivalencias

### Criterios de éxito

| Versión | Comportamiento |
|---------|----------------|
| **v0.1** | Inventario completo de ejes con datos de migración. Plan generado por Claude leyendo el modelo. |
| **Futuro** | Generación semi-automática de fragmentos L5X para los ejes nuevos (ojo: esta capacidad tiene riesgos — ver decisión técnica DT-003) |

### Validación

**Status:** ✅ Logrado en v0.1. La hoja `Axes` del Excel incluye `motion_module`, catálogo, canal y función inferida de cada eje — directamente útil como BoM de migración.

---

## Caso #5 — Detección de código muerto y mejoras

**Reportado por:** Hedi
**Tipo:** Code review

### Situación

> "Quiero saber qué código del proyecto es legacy / no se usa / podría limpiarse antes de migrar."

### Capacidades requeridas

- Tags declarados pero no referenciados
- AOIs definidas pero no invocadas
- Rutinas no llamadas desde ningún Task
- AOIs duplicadas (como detectamos `Unwinder` vs `AHT_Unwinder`)
- Inconsistencias de nomenclatura

### Criterios de éxito

| Versión | Comportamiento |
|---------|----------------|
| **v0.1** | Detección manual con queries a la base de modelo |
| **v0.2** | Reporte de "limpieza" automático con lista priorizada |

### Validación

**Status:** Parcialmente logrado en v0.1. Las AOIs duplicadas se detectan automáticamente (categoría `aoi_naming_collision` en `project.observations`). Detección completa de código muerto requiere v0.2.

---

## Caso #6 — Documentación técnica del proyecto

**Reportado por:** Hedi (para entrega ejecutiva)
**Tipo:** Generación de documentación

### Situación

> "Necesito un documento técnico (TDR) profesional describiendo el proyecto: arquitectura, configuración, lógica de control, parámetros críticos."

### Capacidades requeridas

- Mapa Mental como base
- Diagramas Mermaid de arquitectura
- Tablas de configuración formateadas
- Descripción narrativa de la lógica principal

### Criterios de éxito

| Versión | Comportamiento |
|---------|----------------|
| **v0.1** | Documento Markdown generado, exportable a Word vía pandoc |
| **Futuro** | Plantillas TDR específicas Softys, exportación directa a docx con formato corporativo |

### Validación

**Status:** ✅ Logrado en v0.1. `to_markdown()` genera reporte completo (~200-500 KB) con Mapa Mental + tags + AOIs + rutinas + UDTs + módulos + observations. `to_excel()` produce BoM multi-sheet. `to_mermaid()` produce diagramas de topology/iotree/tasks.

---

## Casos a recolectar (TODO)

A medida que vayamos usando v0.1 con archivos reales, agregar aquí:

- Casos de diagnóstico que aparezcan en operación
- Preguntas frecuentes que Hedi haga durante el uso
- Errores comunes que el sistema deba detectar

---

## Plantilla para nuevos casos

```markdown
## Caso #N — Título descriptivo

**Reportado por:** 
**Tipo:** [Diagnóstico | Análisis estructural | Generación | Comparación | etc.]
**Proyecto referenciado:** 

### Situación
[Descripción del problema/necesidad en palabras del usuario]

### Capacidades requeridas
[Lista]

### Criterios de éxito por versión
[Tabla por versión del skill]

### Validación
[Status: Pendiente | Probado | Logrado]
```

---

*Documento vivo. Se enriquece con cada caso real que aparezca.*

*Última actualización: 2026-05-02 (cierre v0.1)*
