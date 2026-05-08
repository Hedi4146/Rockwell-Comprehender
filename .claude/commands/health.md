---
description: Salud general de un L5X — KPIs + smells por severidad + motion overview + program roles
argument-hint: [L5X path]
---

# /health — Reporte de salud general

L5X: **$ARGUMENTS**

Si no se especifica, usar `parque_l5x/CINTA_LAMINADA_M2_2024.L5X` por default.

## Instrucciones

1. Cargar el L5X con `load_project()`.
2. Invocar `project.ask("salud general del proyecto")` — el agent ejecuta el handler `general_health`.
3. Mostrar al usuario el `answer` (sección consolidada con KPIs, smells por severidad, motion patterns, program roles).
4. Resaltar visualmente:
   - **Críticos:** smells de severidad `high`, programs sin task asignada.
   - **Atención:** smells `medium`, AOIs no invocadas.
   - **Info:** counts generales.

## Cuándo usar

- Primer encuentro con un L5X desconocido — establece baseline rápido.
- Verificar estado tras cambios — comparar dos `/health` runs identifica regresiones.
- Reporte ejecutivo — el output es navegable y exportable.

## Reproducibilidad

Salida consistente entre runs (toolkit determinístico). Si quiere persistir en formato exportable: `to_tdr_html(project, "<path>.html")`.
