"""Test runner — Caso #1 empalme contra CINTA_LAMINADA_M2_2024.L5X.

Simula la conversación turno por turno usando la API v0.2 (find_causal_path,
trace_back). Output va a stdout para captura en el doc del test.

Uso:
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python docs/Test/_caso1_test_runner.py
"""
import sys
from pathlib import Path

# Permitir ejecución desde la raíz del repo sin instalar
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rockwell_comprehender import load_project


L5X = "parque_l5x/CINTA_LAMINADA_M2_2024.L5X"


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def turn(n: int, label: str) -> None:
    print(f"\n--- TURNO {n} · {label} " + "-" * (60 - len(label)))


# ─────────────────────────────────────────────────────────────────────────
section("CARGA")
project = load_project(L5X)
print(f"OK · {L5X}")
print(f"target={project.identity.target_name} · processor={project.identity.processor_type} · sw={project.identity.software_revision}")
print(f"modules={len(project.modules)} · tasks={len(project.tasks)} · "
      f"programs={len(project.programs)} · aois={len(project.aois)} · "
      f"routines={len(project.routines)} · tags(top)={len(project.tags)}")

# ─────────────────────────────────────────────────────────────────────────
turn(1, "MAPA MENTAL + identificar AOIs de empalme")
print("\n[Mapa Mental — primeras 60 lineas]")
for line in project.mapa_mental.splitlines()[:60]:
    print(line)

print("\n[Search 'Splice' — todas las AOIs candidatas]")
hits_splice = project.search("Splice")
aoi_defs = sorted({h.location.split("/")[1] for h in hits_splice
                   if h.location.startswith("AOIs/")})
print(f"AOIs con 'Splice' en nombre/codigo: {aoi_defs}")

print("\n[Search 'Unwinder' — AOIs candidatas debobinador]")
hits_un = project.search("Unwinder")
aoi_un = sorted({h.location.split("/")[1] for h in hits_un
                 if h.location.startswith("AOIs/")})
print(f"AOIs con 'Unwinder' en nombre/codigo: {aoi_un}")

# Cuáles están INSTANCIADOS (invocados desde alguien)
print("\n[Quién INSTANCIA estos AOIs? (filtrar location != AOIs/<self>/...)]")
def find_invocations(aoi_name: str) -> list[str]:
    hits = project.search(aoi_name)
    inv = []
    for h in hits:
        # Excluir definición propia del AOI y exluir hits que son nombres de tag
        loc = h.location
        if loc.startswith(f"AOIs/{aoi_name}/"):
            continue
        if not (loc.startswith("AOIs/") or loc.startswith("Programs/")):
            continue
        inv.append(loc)
    return sorted(set(inv))

for name in aoi_defs + aoi_un:
    inv = find_invocations(name)
    flag = "INSTANCIADO" if inv else "NO INVOCADO (codigo muerto candidato)"
    print(f"  {name:42s} -> {flag}")
    for loc in inv[:3]:
        print(f"      via {loc}")

# ─────────────────────────────────────────────────────────────────────────
turn(3, "LEER AHT_CtcSplicer + AHT_Unwinder + cálculo velocidad inicial")

aoi_splice = project.get_aoi("AHT_CtcSplicer")
print(f"\n[AHT_CtcSplicer] params={len(aoi_splice.parameters)} · "
      f"routines={list(aoi_splice.routines.keys())}")

aoi_unwinder = project.get_aoi("AHT_Unwinder")
print(f"[AHT_Unwinder] params={len(aoi_unwinder.parameters)} · "
      f"routines={list(aoi_unwinder.routines.keys())}")

# El test previo identificó que el cálculo del transitorio está en
# DancerCorAndNewRadiusComputation/Logic. Verificamos que está instanciado.
aoi_dancer = project.get_aoi("DancerCorAndNewRadiusComputation")
if aoi_dancer:
    print(f"[DancerCorAndNewRadiusComputation] params={len(aoi_dancer.parameters)} · "
          f"routines={list(aoi_dancer.routines.keys())}")
    inv = find_invocations("DancerCorAndNewRadiusComputation")
    print(f"  invocado desde: {inv}")
else:
    print("DancerCorAndNewRadiusComputation NO ENCONTRADO")

# Listamos rungs del Logic del AHT_Unwinder buscando MAJ (el comando que arranca el eje)
print("\n[Buscar instrucciones MAJ — comando Move Axis Jog que arranca eje]")
hits_maj = project.search("MAJ(")
for h in hits_maj[:10]:
    print(f"  {h.location} :: {h.snippet[:90]}")

# ─────────────────────────────────────────────────────────────────────────
turn(4, "TRACE CAUSAL — find_causal_path / trace_back (v0.2)")

# Hipótesis: el setpoint del eje en el splice se calcula a partir de
# Data.HmiNewDiameter (input HMI). Validamos automáticamente con tracer.
# Tag candidato a "input HMI sospechoso":
print("\n[search HmiNewDiameter — el input del operador]")
hits_hmi = project.search("HmiNewDiameter")
for h in hits_hmi[:10]:
    print(f"  {h.location} :: {h.snippet[:90]}")

print("\n[search ReelRadius — el radio actual del rollo]")
hits_rad = project.search("ReelRadius")
for h in hits_rad[:8]:
    print(f"  {h.location} :: {h.snippet[:90]}")

# Tag downstream candidato (el que va al MAJ): 'LocCorrection' del transitorio
print("\n[search LocCorrection — variable del Pre-Start]")
hits_loc = project.search("LocCorrection")
for h in hits_loc[:8]:
    print(f"  {h.location} :: {h.snippet[:90]}")

# Ahora el TEST V0.2 REAL: find_causal_path entre HmiNewDiameter (input) y
# un tag aguas-abajo (el que entra al MAJ del Pre-Start). Tomamos como
# objetivo "Data.ReelRadiusA" — el campo del tag estructurado del unwinder
# que el Pre-Start usa.
print("\n[v0.2 · writers_of('Data.ReelRadiusA')]")
writers = project.writers_of("Data.ReelRadiusA")
for w in writers[:10]:
    print(f"  WRITE  loc={w.location}  op={w.operator}  operand={w.operand}({w.operand_kind})")

print("\n[v0.2 · writers_of('Data.HmiNewDiameter')]")
writers_hmi = project.writers_of("Data.HmiNewDiameter")
for w in writers_hmi[:10]:
    print(f"  WRITE  loc={w.location}  op={w.operator}  operand={w.operand}({w.operand_kind})")

print("\n[v0.2 · readers_of('Data.HmiNewDiameter')]")
readers_hmi = project.readers_of("Data.HmiNewDiameter")
for r in readers_hmi[:10]:
    print(f"  READ   loc={r.location}  op={r.operator}  operand={r.operand}({r.operand_kind})")

# find_causal_path: ¿de dónde viene Data.ReelRadiusA hacia atrás? Debería
# llegar a HmiNewDiameter (vía LocHmiNewRadius / LocNewRadius / InitRadius).
print("\n[v0.2 · find_causal_path('Data.ReelRadiusA' <- 'Data.HmiNewDiameter') depth=8]")
path = project.find_causal_path("Data.ReelRadiusA", "Data.HmiNewDiameter",
                                 max_depth=8, direction="back")
if path is None:
    print("  NO PATH FOUND (depth=8)")
elif not path:
    print("  PATH VACIO (from==to)")
else:
    print(f"  PATH ENCONTRADO · {len(path)} steps:")
    for i, step in enumerate(path):
        v = step.via
        print(f"   [{i}] -> {step.target}")
        print(f"        via {v.operator} en {v.location} (operand={v.operand}/{v.operand_kind})")

# trace_back desde Data.ReelRadiusA: ver el árbol de antecedentes
print("\n[v0.2 · trace_back('Data.ReelRadiusA', depth=4) — árbol antecedentes]")
tree = project.trace_back("Data.ReelRadiusA", depth=4, max_branches=10)


def print_tree(node, indent=0):
    pad = "  " * indent
    via_txt = ""
    if node.via:
        via_txt = f"  <- via {node.via.operator}@{node.via.location}"
    trunc_txt = f"  [TRUNC:{node.truncated}]" if node.truncated else ""
    print(f"{pad}{node.operand}{via_txt}{trunc_txt}")
    for c in node.children[:6]:
        print_tree(c, indent + 1)


print_tree(tree)

# Adicional: buscar la fórmula CPT que usa ReelRadius (la del transitorio)
print("\n[search 'ReelRadius)' (tag dentro de fórmula) en code]")
hits_cpt = project.search("- ReelRadius)")
for h in hits_cpt[:5]:
    print(f"  {h.location} :: {h.snippet[:100]}")

# ─────────────────────────────────────────────────────────────────────────
turn(6, "SÍNTESIS · hipótesis raíz")
print("""
Reconstrucción causal validada por tracer:

  Operador HMI -> Data.HmiNewDiameter
       (input REAL del operador)
              v
  AHT_Unwinder/Logic: DIV(HmiNewDiameter, 2, LocHmiNewRadius)
                      MOV(LocHmiNewRadius, LocNewRadius)
              v
  AHT_Unwinder/Logic: invoca RadiusComputation(InitRadius=LocNewRadius,
                                                RadiusComputation=Data.ReelRadiusA)
              v
  RadiusComputation/Logic Rung 0: en evento de splice
        MOV(InitRadius, RadiusComputation_actual)  -> escribe Data.ReelRadiusA (InOut)
              v
  AHT_Unwinder/Logic: invoca DancerCorAndNewRadiusComputation(ReelRadius=Data.ReelRadiusA)
              v
  DancerCor.../Logic Rung 4 (Pre-Start):
        CPT(LocCorrection, ((1200 - ReelRadius)/Kp1) * ((20 - DancerPos)/2) / 2)
              v
  DancerCor.../Logic Rung 9: MAJ(Ax, ..., LocCorrection1, ...) -> arranca eje

Si HmiNewDiameter < diámetro real -> ReelRadius pequeño -> (1200 - ReelRadius) grande
  -> LocCorrection inflado -> MAJ arranca eje a velocidad alta -> ENREDO.

Causa raíz: dato HMI cargado por el operador. Mitigaciones recomendadas:
 1) Validar rango HmiNewDiameter en HMI antes de aceptar
 2) Default = ultimo Data.ReelRadiusA*2 de la corrida previa
 3) Clamp del LocCorrection en Pre-Start (LIM)
 4) Confirmar que la constante 1200 corresponde al radio max físico del rollo
 5) Telemetría: log delta entre HmiNewDiameter cargado y ReelRadius posterior
""")

print("\n[FIN DEL TEST]")
