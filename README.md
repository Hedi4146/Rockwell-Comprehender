# Rockwell-Comprehender

Herramienta de comprensión profunda de proyectos Rockwell Studio 5000 / RSLogix 5000 a partir de archivos `.L5X` exportados.

**Owner:** Hedi Vásquez Mayor — Softys Colombia
**Estado:** v0.1.0 (cerrado 2026-05-02) — listo para uso en Nivel 2 (Claude Code)

---

## Quickstart

```bash
# Instalar el paquete en modo desarrollo
pip install -e . --break-system-packages

# Smoke test
python -c "from rockwell_comprehender import load_project; \
  p = load_project('parque_l5x/CINTA_LAMINADA_M2_2024.L5X'); \
  print(p.mapa_mental[:1000])"
```

Esperado: Mapa Mental del proyecto CINTA TWIN cargando en <1 segundo.

---

## Estructura del repositorio

```
Rockwell-Comprehender/
├── rockwell_comprehender/        # el paquete Python instalable
├── docs/                         # documentación, decisiones, handoff
├── parque_l5x/                   # archivos L5X reales de Softys
└── reportes_generados/           # outputs (gitignore)
```

---

## Uso típico

```python
from rockwell_comprehender import load_project
from rockwell_comprehender.reporters import to_markdown, to_excel, to_mermaid

# Cargar un L5X
project = load_project("parque_l5x/CINTA_LAMINADA_M2_2024.L5X")

# Mapa Mental general (~800-1500 tokens)
print(project.mapa_mental)

# Lupa puntual
routine = project.get_routine("Axis", "Drive_Rolls")
aoi = project.get_aoi("AHT_CtcSplicer")
udt = project.get_udt("DataUnw")

# Búsqueda
hits = project.search("HmiRollDiameter")

# Reporters
to_markdown(project, "reportes_generados/cinta_completo.md")
to_excel(project, "reportes_generados/cinta_inventario.xlsx")
diagram = to_mermaid(project, kind="topology")  # o "iotree" o "tasks"
```

---

## Documentación esencial

Antes de modificar cualquier cosa del paquete, leer:

1. `docs/HANDOFF_v01_to_N2.md` ← **lee esto primero** (transición v0.1 → N2)
2. `docs/SKILL.md` ← contrato del paquete
3. `docs/01_Decisiones_Tecnicas.md` ← bitácora DT-001 a DT-010 (todas las decisiones cerradas)
4. `docs/03_Casos_de_Uso_Reales.md` ← qué problemas debe resolver

---

## Filosofía de trabajo

- **Validación empírica > diseño en abstracto.** Probar contra archivos reales antes de comprometer.
- **Documentación como subproducto.** Cada decisión técnica relevante se anota en la bitácora.
- **Stack mínimo.** Solo agregar dependencias cuando uso real lo justifica.
- **Honestidad sobre limitaciones.** Si algo no funciona como debería, decirlo explícitamente.

(Detalle completo en `docs/HANDOFF_v01_to_N2.md`.)

---

## Estado de los criterios de éxito v0.1

| Criterio | Estado |
|----------|:------:|
| Mapa Mental coherente sin intervención | ✅ |
| Preguntas estructurales sin fallar | ✅ |
| Reporters Markdown / Excel / Mermaid | ✅ |
| Caso de empalme ≤6 turnos (test funcional) | 🟡 Pendiente |

El test funcional del caso paradigma es **el primer trabajo prioritario en N2**.

---

*Para el roadmap completo (N1 → N2 → N3), ver `docs/00_Vision_y_Roadmap.md`.*
