"""Test runner — Caso #1 empalme parametrizado por L5X.

Parametrizado en B.1 (Sprint 3, 2026-05-06) para soportar validación
cruzada CINTA + AQL. Cada L5X expone los identifiers análogos via la
configuración `PROJECT_CONFIGS`.

Uso:
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python docs/Test/_caso1_test_runner.py [CINTA|AQL]

Default: CINTA (compatibilidad con script original).
"""
import sys
from pathlib import Path

# Permitir ejecución desde la raíz del repo sin instalar
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rockwell_comprehender import load_project


# ─────────────────────────────────────────────────────────────────────────
# Configuración por L5X
# ─────────────────────────────────────────────────────────────────────────
#
# Cada L5X tiene identifiers ligeramente distintos (CINTA usa prefijo AHT_,
# AQL usa Diatec legacy sin prefijo). Esta tabla mapea cada caso.

PROJECT_CONFIGS = {
    "CINTA": {
        "path":          "parque_l5x/CINTA_LAMINADA_M2_2024.L5X",
        "splice_aoi":    "AHT_CtcSplicer",
        "unwinder_aoi":  "AHT_Unwinder",
        "dancer_aoi":    "DancerCorAndNewRadiusComputation",
        "radius_aoi":    "RadiusComputation",
        "hmi_diameter_tag": "Data.HmiNewDiameter",
        "reel_radius_tag":  "Data.ReelRadiusA",
        "loc_correction":   "LocCorrection",
    },
    "AQL": {
        "path":          "parque_l5x/AQL_M2.L5X",
        "splice_aoi":    "CtcDiatecSplicer",
        "unwinder_aoi":  "Unwinder",
        "dancer_aoi":    "DancerCorAndNewRadiusComputation",
        "radius_aoi":    "RadiusComputation",
        "hmi_diameter_tag": "Data.HmiNewDiameter",
        "reel_radius_tag":  "Data.ReelRadiusA",
        "loc_correction":   "LocCorrection",
    },
}


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def turn(n: int, label: str) -> None:
    print(f"\n--- TURNO {n} | {label} " + "-" * max(0, 60 - len(label)))


# ─────────────────────────────────────────────────────────────────────────
# Selección del caso
# ─────────────────────────────────────────────────────────────────────────

case = sys.argv[1].upper() if len(sys.argv) > 1 else "CINTA"
if case not in PROJECT_CONFIGS:
    print(f"ERROR: caso {case!r} no en PROJECT_CONFIGS. Opciones: {list(PROJECT_CONFIGS)}")
    sys.exit(1)
cfg = PROJECT_CONFIGS[case]


# ─────────────────────────────────────────────────────────────────────────
section(f"CARGA · {case}")
project = load_project(cfg["path"])
print(f"OK | {cfg['path']}")
print(f"target={project.identity.target_name} | processor={project.identity.processor_type} | sw={project.identity.software_revision}")
print(f"modules={len(project.modules)} | tasks={len(project.tasks)} | "
      f"programs={len(project.programs)} | aois={len(project.aois)} | "
      f"routines={len(project.routines)} | tags(top)={len(project.tags)}")

# ─────────────────────────────────────────────────────────────────────────
turn(1, "MAPA MENTAL + identify_domain('empalme')")
print("\n[Mapa Mental | primeras 40 lineas]")
for line in project.mapa_mental.splitlines()[:40]:
    print(line)

print("\n[identify_domain('problema en empalme') | top 8]")
hits_dom = project.identify_domain("problema en empalme")
for h in hits_dom[:8]:
    print(f"  {h.confidence:.2f}  {h.target_kind:8s}  {h.target_name}  kw={h.match_keywords}")

# ─────────────────────────────────────────────────────────────────────────
turn(2, f"AOIs core: {cfg['splice_aoi']} + {cfg['unwinder_aoi']} + {cfg['dancer_aoi']}")

for aoi_key in ("splice_aoi", "unwinder_aoi", "dancer_aoi", "radius_aoi"):
    name = cfg[aoi_key]
    aoi = project.get_aoi(name)
    if aoi is None:
        print(f"  [{aoi_key:13s}] {name}: NO ENCONTRADO")
        continue
    print(f"  [{aoi_key:13s}] {name}: params={len(aoi.parameters)} | routines={list(aoi.routines.keys())}")


def find_invocations(aoi_name: str) -> list[str]:
    hits = project.search(aoi_name)
    inv = []
    for h in hits:
        loc = h.location
        if loc.startswith(f"AOIs/{aoi_name}/"):
            continue
        if not (loc.startswith("AOIs/") or loc.startswith("Programs/")):
            continue
        inv.append(loc)
    return sorted(set(inv))


print(f"\n[Invocaciones de los AOIs core]")
for aoi_key in ("splice_aoi", "unwinder_aoi", "dancer_aoi", "radius_aoi"):
    name = cfg[aoi_key]
    inv = find_invocations(name)
    flag = f"INSTANCIADO en {len(inv)}" if inv else "NO INVOCADO"
    print(f"  {name:42s} -> {flag}")
    for loc in inv[:3]:
        print(f"      via {loc}")

# ─────────────────────────────────────────────────────────────────────────
turn(3, "TRACE CAUSAL · find_causal_path / writers / readers (v0.2)")

print(f"\n[search '{cfg['hmi_diameter_tag']}']")
hits_hmi = project.search(cfg["hmi_diameter_tag"])
for h in hits_hmi[:6]:
    print(f"  {h.location} :: {h.snippet[:80]}")

print(f"\n[v0.2 | writers_of('{cfg['reel_radius_tag']}')]")
writers = project.writers_of(cfg["reel_radius_tag"])
for w in writers[:8]:
    print(f"  WRITE  loc={w.location}  op={w.operator}  operand={w.operand}({w.operand_kind})")

print(f"\n[v0.2 | writers_of('{cfg['hmi_diameter_tag']}')]")
writers_hmi = project.writers_of(cfg["hmi_diameter_tag"])
for w in writers_hmi[:8]:
    print(f"  WRITE  loc={w.location}  op={w.operator}  operand={w.operand}({w.operand_kind})")

print(f"\n[v0.2 | readers_of('{cfg['hmi_diameter_tag']}')]")
readers_hmi = project.readers_of(cfg["hmi_diameter_tag"])
for r in readers_hmi[:8]:
    print(f"  READ   loc={r.location}  op={r.operator}  operand={r.operand}({r.operand_kind})")

print(f"\n[v0.2 | find_causal_path('{cfg['reel_radius_tag']}' <- '{cfg['hmi_diameter_tag']}') depth=8]")
path = project.find_causal_path(cfg["reel_radius_tag"], cfg["hmi_diameter_tag"],
                                 max_depth=8, direction="back")
if path is None:
    print("  NO PATH FOUND (depth=8)")
elif not path:
    print("  PATH VACIO (from==to)")
else:
    print(f"  PATH ENCONTRADO | {len(path)} steps:")
    for i, step in enumerate(path):
        v = step.via
        print(f"   [{i}] -> {step.target}")
        print(f"        via {v.operator} en {v.location} (operand={v.operand}/{v.operand_kind})")

print(f"\n[v0.2 | trace_back('{cfg['reel_radius_tag']}', depth=4)]")
tree = project.trace_back(cfg["reel_radius_tag"], depth=4, max_branches=10)


def print_tree(node, indent=0):
    pad = "  " * indent
    via_txt = ""
    if node.via:
        via_txt = f"  <- via {node.via.operator}@{node.via.location}"
    trunc_txt = f"  [TRUNC:{node.truncated}]" if node.truncated else ""
    print(f"{pad}{node.operand}{via_txt}{trunc_txt}")
    for c in node.children[:5]:
        print_tree(c, indent + 1)


print_tree(tree)

# ─────────────────────────────────────────────────────────────────────────
turn(4, "VEREDICTO")

verdict_lines = []
splice_aoi = project.get_aoi(cfg["splice_aoi"])
unwinder_aoi = project.get_aoi(cfg["unwinder_aoi"])
dancer_aoi = project.get_aoi(cfg["dancer_aoi"])

n_aois_present = sum(1 for a in (splice_aoi, unwinder_aoi, dancer_aoi) if a is not None)
verdict_lines.append(f"AOIs core presentes: {n_aois_present}/3")
verdict_lines.append(f"  - {cfg['splice_aoi']}: {'OK' if splice_aoi else 'AUSENTE'}")
verdict_lines.append(f"  - {cfg['unwinder_aoi']}: {'OK' if unwinder_aoi else 'AUSENTE'}")
verdict_lines.append(f"  - {cfg['dancer_aoi']}: {'OK' if dancer_aoi else 'AUSENTE'}")

verdict_lines.append(f"\nidentify_domain('empalme'): {len(hits_dom)} hits, top conf={hits_dom[0].confidence:.2f}" if hits_dom else "identify_domain: 0 hits (FAIL)")
verdict_lines.append(f"writers_of({cfg['reel_radius_tag']!r}): {len(writers)} hits")
verdict_lines.append(f"writers_of({cfg['hmi_diameter_tag']!r}): {len(writers_hmi)} hits")
verdict_lines.append(f"find_causal_path({cfg['reel_radius_tag']!r} <- {cfg['hmi_diameter_tag']!r}): "
                    f"{'PATH ' + str(len(path)) + ' steps' if path else 'NO PATH'}")

for line in verdict_lines:
    print(line)

# Verdict summary
ok_count = (
    (1 if n_aois_present == 3 else 0)
    + (1 if hits_dom and hits_dom[0].confidence >= 0.7 else 0)
    + (1 if writers else 0)
    + (1 if path else 0)
)
total = 4
if ok_count == total:
    verdict = "PASS - generaliza completamente"
elif ok_count >= 3:
    verdict = f"PARCIAL - {ok_count}/{total} criterios"
else:
    verdict = f"FAIL - solo {ok_count}/{total} criterios"

print(f"\nVEREDICTO {case}: {verdict}")
print("\n[FIN DEL TEST]")
