"""Freeze codec-only and output-routing correction; preserve all old bytes."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


assert not (ROOT / 'RUNTIME02_FREEZE.json').exists()
original = json.loads((ROOT / 'SOURCE_FREEZE.json').read_text())
for entry in original['files']:
    assert sha(ROOT / entry['path']) == entry['sha256']
failure = json.loads((ROOT / 'predict/HOST_EXIT.json').read_text(encoding='utf-8-sig'))
assert failure['exit_code'] == 1 and not failure['passed'] and failure['no_live_owned_process']
assert not list((ROOT / 'predict').glob('*.npz')) and not (ROOT / 'predict/PREDICTIONS.json').exists()
(ROOT / 'runtime02').mkdir(exist_ok=False)
(ROOT / 'runtime02/synthetic_calib.txt').write_text('P0: 700 0 620 0 0 700 180 0 0 0 1 0\n', encoding='utf-8')
proof = []
for original_name in ('predict.py', 'evaluate.py', 'audit.py', 'audit_refit.py'):
    text = (ROOT / original_name).read_text()
    changed = text
    insertion = ''
    warmup = "\n    import codecs\n    for encoding in ('ascii', 'cp437', 'utf-8', 'latin-1'):\n        codecs.lookup(encoding)"
    # Directory literals only: production data, math, settings and pair order unchanged.
    changed = changed.replace("'predict'", "'runtime02/predict'").replace("'evaluate'", "'runtime02/evaluate'")
    changed = changed.replace('predict/SEAL.json', 'runtime02/predict/SEAL.json').replace('predict/RESULT.json', 'runtime02/predict/RESULT.json').replace('predict/PREDICTIONS.json', 'runtime02/predict/PREDICTIONS.json')
    changed = changed.replace('evaluate/ROWS.json', 'runtime02/evaluate/ROWS.json').replace('evaluate/SUMMARY.json', 'runtime02/evaluate/SUMMARY.json').replace('evaluate/INITIAL_ROWS.json', 'runtime02/evaluate/INITIAL_ROWS.json').replace('evaluate/INITIAL_SUMMARY.json', 'runtime02/evaluate/INITIAL_SUMMARY.json').replace('evaluate/REFERENCE_READ_BEGIN.json', 'runtime02/evaluate/REFERENCE_READ_BEGIN.json')
    if original_name == 'audit.py':
        changed = changed.replace('import audit_refit', 'import audit_refit_runtime02 as audit_refit')
        changed = changed.replace("OUT = lib.ROOT / 'audit'", "OUT = lib.ROOT / 'runtime02/audit'")
    if original_name != 'audit_refit.py':
        before = '    cv2, np = lib.runtime()'
        if before in changed:
            changed = changed.replace(before, before + warmup, 1)
        insertion = "\nextra = lib.load(lib.ROOT / 'RUNTIME02_FREEZE.json')\nfor item in extra['files']:\n    assert lib.sha(lib.ROOT / item['path']) == item['sha256']\n"
        changed = changed.replace('\nOUT = ', insertion + '\nOUT = ', 1)
    name = Path(original_name).stem + '_runtime02.py'
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as f:
        f.write(changed)
    restored = changed.replace('runtime02/', '').replace('import audit_refit_runtime02 as audit_refit', 'import audit_refit')
    if insertion:
        restored = restored.replace(insertion, '', 1)
    restored = restored.replace(warmup, '', 1)
    assert restored == text, 'Only declared non-mathematical changes permitted'
    # Numeric function bodies, where present, are unchanged except directory strings in audit helper.
    old_functions = {n.name: n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    new_functions = {n.name: n for n in ast.parse(changed).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    identical = [k for k in old_functions if ast.dump(old_functions[k]) == ast.dump(new_functions[k])]
    proof.append({'original': original_name, 'new': name, 'original_sha256': sha(ROOT / original_name),
                  'new_sha256': sha(ROOT / name), 'exact_unchanged_functions': identical,
                  'function_count': len(old_functions), 'exact_reverse_transform_recovers_original_source': True})
save('RUNTIME02_TRANSFORM_PROOF.json', {'changes': 'Standard codec warmup, exact source verification, output-directory routing, audit module name only',
    'files': proof, 'original_prediction_failed_seconds_charged': failure['elapsed_seconds'],
    'original_source_freeze_sha256': sha(ROOT / 'SOURCE_FREEZE.json'),
    'math_libraries_and_parameters_changed': False, 'partial_predictions_exist': False})
names = ['RUNTIME02_PLAN.md', 'prepare_runtime02.py', 'cold_probe_runtime02.py', 'host_runtime02.ps1',
         'predict_runtime02.py', 'evaluate_runtime02.py', 'audit_runtime02.py', 'audit_refit_runtime02.py',
         'RUNTIME02_TRANSFORM_PROOF.json', 'runtime02/synthetic_calib.txt']
for name in names:
    if name.endswith('.py'):
        ast.parse((ROOT / name).read_text(encoding='utf-8'), filename=name)
save('RUNTIME02_FREEZE.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'files': [{'path': n, 'bytes': (ROOT / n).stat().st_size, 'sha256': sha(ROOT / n)} for n in names],
    'original_scope_origin_and_caps_retained': True, 'reference_read_allowlist_unchanged': True})
print('Codec/routing correction frozen; no numeric work or original file edit')
