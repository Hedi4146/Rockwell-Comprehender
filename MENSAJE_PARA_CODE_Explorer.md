# MENSAJE PARA COPIAR A CODE — Construcción del Explorer HTML

**Cómo usarlo:**
1. Guarda el archivo `06_Especificacion_Explorer_HTML.md` en `docs/` del repo local
2. Haz commit del archivo: `git add docs/06_Especificacion_Explorer_HTML.md && git commit -m "Add: especificación Explorer HTML v0.1"`
3. Abre Claude Code en el repo
4. Pega el mensaje siguiente

---

## MENSAJE PARA COPIAR Y PEGAR

```
Tengo la siguiente prioridad para esta sesión: construir el Explorer HTML 
v0.1 del paquete rockwell_comprehender. Es un nuevo reporter que expone 
visualmente la estructura del proyecto en un único archivo HTML estático, 
replicando el Controller Organizer de Studio 5000 pero con vista de experto 
integrada.

La especificación completa está en `docs/06_Especificacion_Explorer_HTML.md`. 
Léela ANTES de hacer cualquier otra cosa — define alcance, restricciones, 
arquitectura, paneles esperados, qué incluir y qué dejar fuera.

Después de leer la especificación, dame:

1. Confirmación de que entendiste el alcance y las restricciones (3-5 líneas):
   - Para qué sirve el Explorer
   - Cuál es el caso paradigma motivador (servomotor↔servodrive)
   - Qué NO está en alcance v0.1
   - Las dos restricciones técnicas más importantes

2. Tu plan de implementación incremental siguiendo la regla 6.5 de la spec:
   "Iterar sobre lo simple primero". Específicamente:
   - Paso 1: árbol estático sin paneles
   - Paso 2: panel derecho con vista por defecto
   - Paso 3: vistas individuales (empezando por Eje)
   - Paso 4 en adelante: refinamientos

   Para cada paso indica qué archivos vas a crear/modificar y qué validación
   harás antes de pasar al siguiente.

3. Cualquier duda técnica que tengas sobre la especificación — pregúntala 
   antes de codificar.

Recordatorios importantes:
- DT-010: si vas a agregar una nueva dependencia (ej: librería de tree),
  valida primero con uso concreto antes de comprometerla en pyproject.toml.
- DT-009: schemas crecen aditivamente, código se construye cuando se 
  necesita. No crees stubs vacíos para futuras versiones.
- HANDOFF, sección 6 (anti-patrones): NO inventar datos. Si un dato no 
  está en el modelo del paquete v0.1, mostrar "—" o "no disponible".
- Reusa helpers existentes: la inferencia funcional ya está en mapamental.py
  (_TAG_NAME_HINTS, _infer_from_tag_name, _build_axis_to_module). Importa, 
  no reimplementes.

Validación final: cuando termines un nivel funcional mínimo, generar el HTML 
para CINTA_LAMINADA_M2_2024.L5X y para AQL_M2.L5X. Yo (Hedi) los abriré en 
navegador y veré si el caso paradigma se resuelve con un click.

Procede.
```

---

## Por qué este mensaje funciona

**1. Forza lectura de la especificación primero.** Code es ejecutivo por naturaleza. Sin esta orden explícita podría empezar a codificar sin contexto completo.

**2. Pide demostración de comprensión.** Las 4 sub-preguntas (alcance, caso paradigma, no-alcance, restricciones) verifican que Code entendió, no solo escaneó.

**3. Pide plan de implementación incremental.** Code va a tender a "construir todo de una vez". La regla 6.5 de la especificación dice "iterar sobre lo simple primero" — el mensaje refuerza eso.

**4. Activa los anti-patrones del HANDOFF.** Específicamente DT-009, DT-010 y "no inventar datos". Esto previene tres errores comunes: agregar dependencias sin validación, crear stubs, alucinar información.

**5. Recuerda reusar helpers existentes.** Si Code reimplementa `_infer_from_tag_name`, generamos código duplicado y posibles inconsistencias. Mejor que use lo que ya está validado.

**6. Define validación clara.** Generar HTML para los dos L5X y abrirlos en navegador. Es el criterio de éxito objetivo.

---

## Después del primer mensaje

Si Code responde bien:
- Confirma comprensión correcta del alcance
- Plantea plan incremental razonable
- Hace preguntas técnicas pertinentes (no excesivas)

Entonces respondes: *"Procede con el paso 1"* o respondes sus preguntas técnicas y luego *"Procede"*.

Si Code se desvía:
- *"Detente. Revisa la sección X de la especificación y confírmame qué dice sobre Y."*
- *"Estás violando la regla 6.5 (incremental). Reformula el plan."*

---

## Cuando Code entregue el primer HTML funcional

1. Lo abres en navegador
2. Vas directo al caso paradigma: busca `S04N86_DANCER_DEBO_TNT` en AQL_M2 y haz click
3. Verifica que en el panel derecho aparezca:
   - Función inferida: Dancer / control de tensión
   - Drive físico: M16_514U1 (2094-BM02)
   - Canal: Ch27
4. Si esto está → caso paradigma resuelto, dirección correcta
5. Si falla algo → traes el resultado a Claude.ai web y vemos cómo ajustar

---

## Cuando termines la sesión con Code

Trae aquí (a Claude.ai web del Project nuevo cuando lo configures, o aquí mismo si todavía no tienes el Project nuevo):
1. El HTML generado (al menos uno de los dos como muestra)
2. El reporte que te dio Code de qué construyó
3. Tu opinión sobre si funciona como esperabas

Lo revisamos juntos antes de pasar al siguiente paso.
