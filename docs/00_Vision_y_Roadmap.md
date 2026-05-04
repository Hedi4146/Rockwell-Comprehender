# 00 · VISIÓN Y ROADMAP

**Proyecto:** Rockwell Project Comprehender
**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Iniciado:** Mayo 2026
**Estado:** Diseño activo · Pre-construcción de v0.1

---

## Visión

Construir, de forma gradual e iterativa, una herramienta que permita a un asistente de IA **comprender un proyecto de automatización Rockwell con la profundidad de un ingeniero senior** — no solo leer archivos, sino entender la arquitectura, trazar relaciones, identificar causas, sugerir mejoras y dialogar sobre el sistema con autonomía técnica.

La meta no es reemplazar al ingeniero, es darle un par adicional de ojos que **siempre tiene presente la estructura completa del proyecto** y puede ayudar a diagnosticar, documentar, migrar y optimizar más rápido.

---

## Por qué este proyecto

A día de hoy no existe ninguna herramienta open-source ni comercial que ofrezca **comprensión real** de proyectos Logix. Lo que existe es:

- **Parsers de archivos** (l5x, acd-tools) — leen estructura pero no comprenden
- **Generadores de código** (studio5000-AI-Assistant) — producen output pero con limitaciones reales
- **Herramientas de diff/merge** (Copia) — útiles para versionado, no para comprensión
- **Studio 5000 nativo** — excelente para escribir y ejecutar, no para análisis estructural cruzado

El gap es real. La oportunidad es real. La construcción es factible — pero requiere paciencia y disciplina técnica.

---

## Tres niveles de madurez

```
NIVEL 1 — Skill en Claude web                 [punto de partida]
└─ Subes L5X, conversas, analizas
└─ Sin instalación, sin servidor, sin UI
└─ Esfuerzo total estimado: ~5-15 días iterativos
└─ Valor: comprensión profunda en conversación

         ↓

NIVEL 2 — Integración en Claude Code           [evolución natural]
└─ Acceso directo a archivos locales del parque
└─ Repo Git con skills, scripts y proyectos versionados
└─ Iteración rápida en workflow real
└─ Esfuerzo incremental: ~1 semana adicional
└─ Valor: workflow continuo de desarrollo

         ↓

NIVEL 3 — Aplicación web propia                [meta de largo plazo]
└─ Frontend dedicado, backend, base de datos
└─ UI específica para flujos repetitivos
└─ Multi-usuario, eventualmente multi-planta
└─ Posible producto comercializable Softys u otros
└─ Esfuerzo: 3-6 meses de desarrollo dedicado
└─ Valor: herramienta institucional / producto
```

**Principio clave:** cada nivel se construye sobre el anterior sin desperdiciar trabajo. El código del Nivel 1 corre tal cual en Nivel 2 y forma el backend del Nivel 3.

---

## Filosofía de trabajo

1. **Construcción gradual.** No comprometer stack pesado antes de validar necesidad. Empezar simple y agregar complejidad solo cuando los datos reales lo justifiquen.

2. **Cada decisión documentada.** Bitácora viva con justificación, no decisiones implícitas que se pierden entre conversaciones.

3. **Validación contra casos reales.** Cada capacidad se prueba con archivos del parque real antes de construir la siguiente. Sin demos sintéticos.

4. **Reuso pragmático.** Aprovechar lo que existe (`l5x` de jvalenzuela como base de parsing) sin reinventar parsing maduro. Construir desde cero solo lo que ningún proyecto open-source ofrece — que es justamente la comprensión.

5. **Honestidad técnica.** Decir lo que no funciona, lo que falta, lo que tiene riesgo. Sin sobreventa.

6. **Arquitectura limpia desde día uno.** El código se organiza como paquete instalable con interfaces claras, no como scripts sueltos. Eso permite que el mismo código corra en Claude web, Claude Code, y eventualmente backend de web app.

---

## Arquitectura central: "Mapa Mental + Lupa"

Inspirada en cómo trabaja un ingeniero senior real — no se memoriza el proyecto, tiene un mapa estructural siempre presente y sabe dónde profundizar cuando algo lo requiere.

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1 · Mapa Mental general (~800–1500 tokens, siempre cargado)│
│  ↳ Identidad, arquitectura física y lógica, mapa funcional   │
│    de ejes, patrones de código, observaciones clave          │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2 · Mapas funcionales (cargados bajo demanda)          │
│  ↳ Empalme, control tensión, habilitación, scheduling, etc. │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3 · Lupa puntual (cargada bajo demanda)                │
│  ↳ Código específico de rutina/AOI, miembros de UDT          │
├─────────────────────────────────────────────────────────────┤
│  CAPA 4 · Trace de variables (calculado bajo demanda)        │
│  ↳ Cadenas de escritura/lectura, grafos de dependencia       │
└─────────────────────────────────────────────────────────────┘
```

---

## Caso paradigmático de uso

Diagnóstico causal estilo:

> "Tenemos problema en empalme: el debobinador arranca muy rápido y se enreda."

→ Localizar lógica de empalme → identificar cálculo de velocidad inicial → trazar inputs del cálculo (diámetro estimado, posición danzarín, referencia máquina) → identificar que el diámetro es input HMI → concluir: operador cargó valor menor al real.

**Cinco niveles de profundidad descendente, navegando relaciones reales del código.** Cada paso localizado pero encadenado al anterior por dependencias semánticas en el proyecto.

Si el sistema resuelve este caso bien, está logrado.

---

## Roadmap por capacidades

### v0.1 — Lector inteligente (próximo sprint, ~5 días)
- Parser L5X completo
- Mapa Mental general (capa 1)
- Búsqueda full-text en código
- Lupa puntual sobre rutinas/AOIs/tags
- **Cubre:** preguntas estructurales, exploración guiada, primeras consultas
- **Limitación:** trace de dependencias requiere navegación manual con Claude

### v0.2 — Trace automático (~5 días adicionales)
- Grafos de dependencias bidireccionales
- "¿De dónde viene este valor?" automático
- "¿Qué afecta este tag?" automático
- **Cubre:** diagnósticos causales en menos turnos

### v0.3 — Comprensión por dominio (~5 días adicionales)
- Detección automática de dominios funcionales
- Diccionario semántico (HmiRollDiameter → "diámetro de rollo, input operador")
- Cadenas causales pre-construidas
- **Cubre:** preguntas tipo "qué pasa cuando..." prácticamente directas

### Futuro (Nivel 2)
- Empaquetado como skill descargable para Claude Code
- Integración con repo Git de proyectos
- Workflow batch para análisis de múltiples L5X
- Generación de documentación masiva del parque

### Futuro (Nivel 3) — solo si el uso valida la inversión
- Frontend web dedicado
- Backend con persistencia
- Multi-usuario, multi-proyecto
- UI para flujos específicos detectados durante uso de N1+N2

---

## Criterios de éxito por hito

**v0.1 logrado cuando:**
- ✅ Cargo un L5X arbitrario del parque y produzco Mapa Mental coherente sin intervención
- ✅ Respondo preguntas estructurales sobre el proyecto sin fallar
- ✅ El caso de empalme se resuelve en ≤6 turnos de conversación (validado 2026-05-03 — 3 turnos efectivos con tracer v0.2)

**Status:** ✅ v0.1 oficialmente cerrado (2026-05-03).

**v0.2 logrado cuando:**
- "¿De dónde viene el valor de X?" se responde en 1 turno con trace completo
- Detecto al menos 3 patrones de dependencia útiles automáticamente

**v0.3 logrado cuando:**
- Sin guía manual, identifico que el caso de empalme involucra dominio "splice + unwinder"
- Genero la cadena causal en 1-2 turnos con confianza alta

**Nivel 2 logrado cuando:**
- Ejecuto análisis sobre archivos del parque sin que se suban manualmente
- Múltiples sesiones de Claude Code mantienen continuidad del análisis

**Nivel 3 logrado cuando:**
- Otro ingeniero (no Hedi) usa la herramienta sin curva de aprendizaje significativa
- Hay al menos un caso documentado de problema diagnosticado más rápido que sin la herramienta

---

## Lo que este proyecto NO es (para evitar scope creep)

- **No** es un generador de código ladder/ST. Eso lo hace mal todo el ecosistema y no es nuestra apuesta.
- **No** es un reemplazo de Studio 5000. Es un complemento de comprensión.
- **No** es un simulador de PLC. Eso lo hace FactoryTalk Logix Echo.
- **No** es una herramienta de versionado/merge. Eso lo hace Copia.
- **No** depende del SDK oficial de Rockwell. Trabaja sobre L5X exportados.

---

## Ritmo de trabajo

- **Conversaciones de 1-3 horas** según disponibilidad de Hedi
- **Cada conversación entrega algo concreto** — código, decisión documentada, hallazgo
- **Validación inmediata** contra archivos reales cuando sea posible
- **Documentación como subproducto** — no se hace al final, se hace mientras se trabaja
- **Sin presión de tiempo** — calidad sobre velocidad

---

*Documento vivo. Última actualización: 2026-05-01*
