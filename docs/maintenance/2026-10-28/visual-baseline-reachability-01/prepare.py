import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAY = ROOT.parent
ER = DAY / 'visual-essential-refinement-01'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


assert not (ROOT / 'SOURCE_FREEZE.json').exists()
bindings = {}
for key, parent, name in [('ER1_rows', ER, 'runtime03/evaluate/ROWS.json'),
                         ('CF1_rows', DAY/'camera-frustum-support-01', 'ROWS.json')]:
    seal = json.loads((parent/'DELIVERY_SEAL.json').read_text(encoding='utf-8-sig'))
    entry = next(e for e in seal['files'] if e['path'] == name)
    p = parent / name
    assert p.stat().st_size == entry['bytes'] and sha(p) == entry['sha256']
    bindings[key] = {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
prior = DAY.parent/'2026-10-26/camera-strategy-reachability-01'
seal = json.loads((prior/'DELIVERY_SEAL.json').read_text())
entry = next(e for e in seal['files'] if e['path'] == 'FREEZE.json')
assert sha(prior/'FREEZE.json') == entry['sha256']
old = json.loads((prior/'FREEZE.json').read_text())
p = Path(old['old_analysis'])
entry = next(e for e in old['files'] if Path(e['path']) == p)
assert sha(p) == entry['sha256']
bindings['old_analysis'] = {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
save('INPUT_BINDING.json', bindings)
with (ROOT/'host.ps1').open('xb') as f:
    f.write((ER/'host.ps1').read_bytes())
method = json.loads((ER/'METHOD.json').read_text())
method.update(scope_origin_utc='2026-10-28T07:22:18+00:00',whole_scope_seconds=900,dossier_bytes=16777216,stage_seconds={'controls':30})
save('METHOD.json', method)
names = [ROOT/n for n in ('PROTOCOL.md','controls.py','prepare.py','host.ps1','METHOD.json','INPUT_BINDING.json')]+[ER/'baseline_lib.py']
for p in names:
    if p.suffix == '.py':
        ast.parse(p.read_text(encoding='utf-8'))
save('SOURCE_FREEZE.json', {'files': [{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in names]})
print('VR1 frozen before categorical join')
