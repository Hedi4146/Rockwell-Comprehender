---
description: Auditoría completa de un L5X (mapa mental + smells + motion patterns + program inference + dead code)
argument-hint: <L5X path>
---

# /audit — Auditoría completa de un L5X

L5X a auditar: **$ARGUMENTS**

Si no se especifica path, usar `parque_l5x/CINTA_LAMINADA_M2_2024.L5X` por default.

## Instrucciones

1. Cargar el L5X con `load_project()`.
2. Ejecutar y reportar al usuario:
   - **Identidad** (`project.identity`): target_name, processor_type, software_revision.
   - **KPIs** (counts): modules, AOIs, programs, routines, tags, UDTs, tasks.
   - **Mapa Mental** (primeras 60 líneas de `project.mapa_mental`).
   - **Program inference** (`project.program_inference()`): tabla de programs con role inferido + confidence.
   - **Smells** (`project.detect_smells()`): conteo por severidad + top 10 reglas activadas.
   - **Motion patterns** (`project.detect_motion_patterns()`): conteo por pattern, top 5 high-confidence matches.
   - **Tag dictionary** (`project.tag_dictionary()`): distribución por rol semántico.
3. Si el usuario quiere reporte exportable, ofrecer generar:
   - `to_tdr_html(project, "reportes_generados/<name>_TDR.html")` — TDR navegable
   - `to_html_explorer(project, "reportes_generados/<name>_explorer.html")` — Explorer interactivo

## Output esperado

Síntesis estructurada de la salud y semántica del proyecto en un único informe consolidado. Determinístico: misma L5X → mismo informe.
