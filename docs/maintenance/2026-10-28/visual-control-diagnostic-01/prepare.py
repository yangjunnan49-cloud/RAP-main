import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
old = ROOT.parent / 'visual-baseline-execution-01'
assert not (ROOT / 'SOURCE_FREEZE.json').exists()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


oldfreeze = json.loads((old / 'SOURCE_FREEZE.json').read_text())
for e in oldfreeze['files']:
    assert sha(old / e['path']) == e['sha256']
save('ORIGINAL_BINDING.json', {'files': [{'path': str(old / n), 'sha256': sha(old / n)}
    for n in ('baseline_lib.py', 'METHOD.json', 'SOURCE_FREEZE.json', 'controls/check_08.json', 'controls/HOST_EXIT.json', 'STATUS.json')]})
with (ROOT / 'host.ps1').open('xb') as f:
    f.write((old / 'host.ps1').read_bytes())
method = json.loads((old / 'METHOD.json').read_text())
method.update(scope_origin_utc='2026-10-28T06:58:25+00:00', whole_scope_seconds=900, dossier_bytes=16777216,
              stage_seconds={'controls': 60})
save('METHOD.json', method)
entries = []
for name in ('PROTOCOL.md', 'controls.py', 'prepare.py', 'ORIGINAL_BINDING.json', 'host.ps1', 'METHOD.json'):
    p = ROOT / name
    if p.suffix == '.py':
        ast.parse(p.read_text(encoding='utf-8'))
    entries.append({'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'role': 'controls'})
save('SOURCE_FREEZE.json', {'files': entries, 'VB1_unchanged': True, 'native_solver_replay_admitted': False})
print('CD1 source freeze complete')
