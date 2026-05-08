---
description: Explica un tag, AOI o program específico — datatype, rol semántico, references, evidence
argument-hint: <target> [L5X]
---

# /explain — Explicación de un identifier específico

Identifier a explicar: **$ARGUMENTS**

Sintaxis: `/explain <NombreIdentifier>` o `/explain <NombreIdentifier> <L5X>`. Si no se especifica L5X, usar `parque_l5x/CINTA_LAMINADA_M2_2024.L5X` por default.

## Instrucciones

1. Cargar el L5X.
2. Invocar `project.ask("qué hace <target>")` — el agent determinístico decide automáticamente si el target es tag, AOI o program y aplica el handler correspondiente.
3. Mostrar el `answer` consolidado, que incluye:
   - **Si es AOI:** parameters count, routines, complexity.
   - **Si es Program:** rol funcional inferido + evidence + main_routine.
   - **Si es Tag:** datatype, scope, rol semántico, references_of (top 5), trace_back si aplica.
4. Si confidence < 0.5, sugerir verificar el nombre del target (puede tener typo) o ejecutar `/audit` para ver el inventario completo.

## Output esperado

Ficha técnica del identifier con todo lo que el toolkit puede inferir empíricamente. Útil para onboarding rápido sobre componentes desconocidos del proyecto.

## Determinismo

`agent.ask` es determinístico — misma `(L5X, target)` retorna mismo output.
