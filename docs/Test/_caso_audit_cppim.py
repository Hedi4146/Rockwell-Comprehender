"""B.2 — Caso audit contra CPPIM_BD800_1.L5X (Amantrini v33).

Ejecuta los 6 casos de uso del catálogo contra CPPIM y reporta veredicto
por caso. Output usa solo ASCII para evitar problemas de codificación
en consolas Windows cp1252.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rockwell_comprehender import load_project

PATH = 'parque_l5x/CPPIM_BD800_1.L5X'

print('=' * 78)
print(f'B.2 AUDIT CPPIM - {PATH}')
print('=' * 78)

p = load_project(PATH)
print(f'\nCARGA OK target={p.identity.target_name} sw={p.identity.software_revision} proc={p.identity.processor_type}')
print(f'  modules={len(p.modules)} aois={len(p.aois)} programs={len(p.programs)} routines={len(p.routines)} tags={len(p.tags)} udts={len(p.udts)}')

# --- CASO 1 ---
print('\n[CASO 1: Empalme]')
hits = p.identify_domain('problema en empalme')
for h in hits[:5]:
    print(f'  {h.confidence:.2f}  {h.target_kind:8s}  {h.target_name}')
splicer_aois = [a.name for a in p.aois if 'splic' in a.name.lower() or 'ctc' in a.name.lower()]
unwinder_things = [a.name for a in p.aois if 'unwind' in a.name.lower()]
dancer_things = [a.name for a in p.aois if 'dancer' in a.name.lower()]
print(f'  splice/ctc AOIs: {splicer_aois or "ninguno"}')
print(f'  unwinder AOIs: {unwinder_things}')
print(f'  dancer AOIs: {dancer_things}')

# --- CASO 2 ---
print('\n[CASO 2: Mapa Mental]')
mm = p.mapa_mental
print(f'  Mapa Mental: {len(mm)} chars, {len(mm.splitlines())} lineas')

# --- CASO 4 ---
print('\n[CASO 4: BoM K6000 -> K5700]')
k6000 = [m for m in p.modules if '2094' in (m.catalog_number or '')]
k5700 = [m for m in p.modules if '2198' in (m.catalog_number or '')]
print(f'  K6000 (2094): {len(k6000)}')
print(f'  K5700 (2198): {len(k5700)}')
for m in k5700[:8]:
    print(f'    {m.name}: {m.catalog_number}')

# --- CASO 5 ---
print('\n[CASO 5: Codigo muerto]')
SKIP = ('AXIS_', 'MOTION_GROUP', 'COORDINATE_SYSTEM', 'TASK', 'PROGRAM', 'ROUTINE', 'MODULE', 'MESSAGE', 'CONNECTION_STATUS', 'ALARM')
controller_tags = [t for t in p.tags if t.scope == 'controller']
analyzable = [t for t in controller_tags if not any(t.datatype.startswith(s) for s in SKIP) and not t.motion_module]
print(f'  Tags controller: {len(controller_tags)}, analyzable: {len(analyzable)}')
sample = analyzable[:100]
orphans = 0
errors = 0
for t in sample:
    try:
        refs = p.references_of(t.name)
        if not refs:
            orphans += 1
    except Exception:
        errors += 1
print(f'  Sample 100: orphans={orphans}, errors={errors}')

# --- CASO 6 ---
print('\n[CASO 6: TDR Markdown]')
try:
    from rockwell_comprehender.reporters import markdown as md
    md_text = md.to_markdown(p)
    print(f'  Markdown: {len(md_text)} chars')
except Exception as e:
    print(f'  FAIL: {type(e).__name__}: {e}')

# --- Gaps Amantrini ---
print('\n[Gaps Amantrini]')
rac_aois = [a for a in p.aois if a.name.lower().startswith('rac_')]
print(f'  raC_* libraries: {len(rac_aois)}')
for a in rac_aois[:5]:
    print(f'    {a.name}')
protected_aois = [a.name for a in p.aois if any(not r.code for r in a.routines.values())]
print(f'  AOIs con routine sin codigo (Protected potential): {len(protected_aois)}')
for n in protected_aois[:5]:
    print(f'    {n}')

print('\nB.2 AUDIT COMPLETO')
