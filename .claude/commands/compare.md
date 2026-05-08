---
description: Comparación automática entre 2 L5X — diff de modules, AOIs, UDTs, programs, routines, tags, tasks
argument-hint: <L5X_old> <L5X_new>
---

# /compare — Comparación automática entre 2 proyectos

L5X a comparar: **$ARGUMENTS**

Esperado: dos paths separados por espacio. Si solo se da uno, pedir el segundo. Si no se da nada, ofrecer comparar el parque (CINTA → AQL, o AQL → CPPIM por default).

## Instrucciones

1. Cargar ambos L5X con `load_project()`.
2. Invocar `from rockwell_comprehender.project_diff import diff_projects; d = diff_projects(p_old, p_new)`.
3. Mostrar al usuario:
   - `d.summary()` — resumen una línea: `+N/-M/~K` por categoría.
   - Tablas detalladas por sección (modules, AOIs, UDTs, programs, routines, tags, tasks).
   - Énfasis en `changed` (catalog change, param count diff) — son los más relevantes para review.
4. Si el diff es grande (>500 entries), ofrecer guardar el reporte completo a `docs/Análisis/diff_<old>_to_<new>.md` vía `d.to_markdown()`.

## Cuándo usar

- Comparar 2 versiones del mismo proyecto (auditoría de cambios entre releases).
- Comparar 2 proyectos similares (cross-product análisis del parque).
- Comparar pre/post migración K6000→K5700.

## Determinismo

`diff_projects` es puramente funcional — misma input → mismo output.
