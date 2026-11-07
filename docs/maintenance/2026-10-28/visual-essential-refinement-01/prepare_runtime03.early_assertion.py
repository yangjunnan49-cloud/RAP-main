"""Freeze the final lazy-module correction and byte-preserving seven-row resume."""
import ast
import datetime as dt
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def npy(content):
    assert content[:6] == b'\x93NUMPY'
    version = content[6:8]
    assert version in (b'\x01\x00', b'\x02\x00')
    n = 2 if version == b'\x01\x00' else 4
    length = int.from_bytes(content[8:8+n], 'little')
    header = ast.literal_eval(content[8+n:8+n+length].decode('latin-1'))
    assert not header['fortran_order'] and 'O' not in header['descr']
    return header, content[8+n+length:]


assert not (ROOT / 'RUNTIME03_FREEZE.json').exists()
for freeze in ('SOURCE_FREEZE.json', 'RUNTIME02_FREEZE.json'):
    for e in json.loads((ROOT / freeze).read_text())['files']:
        assert sha(ROOT / e['path']) == e['sha256']
failed = ROOT / 'runtime02/predict'
receipt = json.loads((failed / 'HOST_EXIT.json').read_text(encoding='utf-8-sig'))
assert receipt['exit_code'] == 1 and receipt['no_live_owned_process'] and not receipt['passed']
assert not (failed / 'PREDICTIONS.json').exists()
files = sorted(failed.glob('*.npz'))
pairs = json.loads((ROOT / 'PREDICTION_INPUTS.json').read_text())['pairs']
assert len(files) == 7 and {p.stem for p in files} == {r['key'] for r in pairs[:7]}
entries = []
for pair in pairs[:7]:
    p = failed / (pair['key'] + '.npz')
    with zipfile.ZipFile(p) as z:
        arrays = {Path(name).stem: npy(z.read(name)) for name in z.namelist()}
    n = arrays['indices'][0]['shape'][0]
    assert arrays['indices'][0]['shape'] == (n, 2) and 0 <= n < 8
    assert arrays['first'][0]['shape'] == arrays['second'][0]['shape'] == (n, 2)
    assert arrays['E'][0]['shape'] == (0, 3) and not arrays['E'][1]
    for name in ('essential_mask', 'cheirality_mask'):
        assert arrays[name][0]['shape'] == (n,) and not any(arrays[name][1])
    seed = int(hashlib.sha256(('VB1:' + pair['key']).encode('ascii')).hexdigest()[:8], 16) % 2147483647
    initial = {'status': 'NO_EVIDENCE_INSUFFICIENT_MATCHES', 'matches': n, 'essential_inliers': 0,
        'cheirality_inliers': 0, 'candidate_counts': [], 'seed': seed, 'R_i_to_j': None, 'unit_t_i_to_j': None}
    row = {**pair, **initial, 'initial_pose': initial.copy(), 'refinement': {'state': 'RAW_NO_EVIDENCE', 'trace': []}, 'evidence': p.name}
    entries.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p), 'record': row,
        'reconstruction_proof': 'n<8, empty E, zero masks, source-frozen early-return branch; no solver/pixel replay'})
save('RUNTIME03_PARTIAL_INDEX.json', {'entries': entries, 'preserved_pairs': 7, 'missing_pairs': 193,
    'selection': 'Exact completed files in first seven original positions, not accuracy/outcome selection'})
(ROOT / 'runtime03').mkdir(exist_ok=False)
resume_before = "    allowed = list(cache.values()) + [e['path'] for e in inputs['calibrations']]"
resume_after = "    partials = lib.load(lib.ROOT / 'RUNTIME03_PARTIAL_INDEX.json')['entries']\n    prior = {e['record']['key']: e for e in partials}\n" + resume_before + " + [e['path'] for e in partials]"
loop_before = "    for pair in inputs['pairs']:\n"
loop_after = loop_before + "        if pair['key'] in prior:\n            entry = prior[pair['key']]\n            payload = Path(entry['path']).read_bytes()\n            assert len(payload) == entry['bytes'] and lib.hashlib.sha256(payload).hexdigest() == entry['sha256']\n            with (OUT / entry['record']['evidence']).open('xb') as handle:\n                handle.write(payload)\n            predictions.append(entry['record'])\n            continue\n"
proof = []
for name in ('predict', 'evaluate', 'audit', 'audit_refit'):
    old = ROOT / (name + '_runtime02.py')
    text = old.read_text()
    changed = text.replace('runtime02/', 'runtime03/').replace('RUNTIME02_FREEZE', 'RUNTIME03_FREEZE').replace('audit_refit_runtime02', 'audit_refit_runtime03')
    if name == 'predict':
        assert changed.count(resume_before) == changed.count(loop_before) == 1
        changed = changed.replace(resume_before, resume_after).replace(loop_before, loop_after)
        marker = "    for encoding in ('ascii', 'cp437', 'utf-8', 'latin-1'):\n        codecs.lookup(encoding)"
        assert changed.count(marker) == 1
        changed = changed.replace(marker, marker + '\n    import numpy.ma')
    restored = changed.replace('runtime03/', 'runtime02/').replace('RUNTIME03_FREEZE', 'RUNTIME02_FREEZE').replace('audit_refit_runtime03', 'audit_refit_runtime02')
    if name == 'predict':
        restored = restored.replace(resume_after, resume_before).replace(loop_after, loop_before).replace('\n    import numpy.ma', '')
    assert restored == text
    new = ROOT / (name + '_runtime03.py')
    with new.open('x', encoding='utf-8', newline='\n') as f:
        f.write(changed)
    ast.parse(changed)
    proof.append({'original': old.name, 'new': new.name, 'old_sha256': sha(old), 'new_sha256': sha(new), 'reverse_transform_recovers_exact_source': True})
host = (ROOT / 'host_runtime02.ps1').read_text()
new_host = host.replace("'runtime02'", "'runtime03'").replace('RUNTIME02_FREEZE.json', 'RUNTIME03_FREEZE.json').replace("'runtime02/", "'runtime03/").replace('_runtime02.py', '_runtime03.py')
charged_marker = "$taskCharged=[double]$taskOldFailure.elapsed_seconds"
extra_charge = charged_marker + "\nforeach($taskOldRel in @('runtime02/probe/HOST_EXIT.json','runtime02/predict/HOST_EXIT.json')){$taskOldAttempt=Get-Content -LiteralPath (Join-Path $taskRoot $taskOldRel) -Raw|ConvertFrom-Json;if(-not $taskOldAttempt.no_live_owned_process){throw 'Unreaped earlier child'};$taskCharged+=[double]$taskOldAttempt.elapsed_seconds}"
assert new_host.count(charged_marker) == 1
new_host = new_host.replace(charged_marker, extra_charge)
with (ROOT / 'host_runtime03.ps1').open('x', encoding='utf-8', newline='\n') as f:
    f.write(new_host)
probe = (ROOT / 'cold_probe_runtime02.py').read_text().replace('runtime02/probe', 'runtime03/probe').replace('RUNTIME02_FREEZE', 'RUNTIME03_FREEZE')
probe = probe.replace('import baseline_lib as lib', 'import baseline_lib as lib\nimport refine_lib')
probe = probe.replace('    cv2, np = lib.runtime()', '    cv2, np = lib.runtime()\n    import numpy.ma')
full = '''    da = np.eye(8, 128, dtype=np.float32) * 10
    assert len(lib.mutual_matches(cv2, np, da, da + np.float32(.001), .75)) == 8
    xyz = np.asarray([[x, y, z] for z in (8., 12., 18.) for y in (-1., 0., 1.) for x in (-2., -1., 0., 1., 2.)])
    angle = np.deg2rad(7.)
    rotation = np.array([[np.cos(angle), 0., np.sin(angle)], [0., 1., 0.], [-np.sin(angle), 0., np.cos(angle)]])
    translation = np.array([1.2, .15, .3])
    p1 = xyz @ k.T
    p2 = (xyz @ rotation.T + translation) @ k.T
    method = extra_method
    result, evidence = refine_lib.estimate(cv2, np, np.ascontiguousarray(p1[:, :2]/p1[:, 2:3]), np.ascontiguousarray(p2[:, :2]/p2[:, 2:3]), k, method, 'cold_full_path')
    reference = np.eye(4)
    reference[:3, :3], reference[:3, 3] = rotation, translation
    assert result['status'] == 'POSE'
    errors = lib.angles(np, np.asarray(result['R_i_to_j']), np.asarray(result['unit_t_i_to_j']), reference, 1e-9)
    assert errors[0] < .1 and errors[1] < .5
'''
probe = probe.replace('    lib.read_gate([cache, calibration], OUT)', "    extra_method = lib.load(lib.ROOT / 'METHOD.json')\n    lib.read_gate([cache, calibration], OUT)")
probe = probe.replace('    denied = False', full + '    denied = False')
probe = probe.replace("'RANSAC_recoverPose_or_refit_calls': 0", "'synthetic_complete_pose_path': 'PASS', 'real_pose_calls': 0")
with (ROOT / 'cold_probe_runtime03.py').open('x', encoding='utf-8', newline='\n') as f:
    f.write(probe)
ast.parse(probe)
save('RUNTIME03_TRANSFORM_PROOF.json', {'files': proof, 'seven_completed_evidence_files_preserved': True,
    'new_math_or_parameter_change': False, 'same_numerical_original_scope_and_caps': True})
names = ['RUNTIME03_PLAN.md', 'prepare_runtime03.py', 'host_runtime03.ps1', 'cold_probe_runtime03.py',
    'predict_runtime03.py', 'evaluate_runtime03.py', 'audit_runtime03.py', 'audit_refit_runtime03.py',
    'RUNTIME03_PARTIAL_INDEX.json', 'RUNTIME03_TRANSFORM_PROOF.json']
save('RUNTIME03_FREEZE.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'files': [{'path': n, 'bytes': (ROOT/n).stat().st_size, 'sha256': sha(ROOT/n)} for n in names],
    'remaining_pairs': 193, 'original_prediction_cap_seconds': 300, 'new_numeric_parameters': False})
print('Final cold-path correction frozen; exact seven-row evidence retained; 193 missing')
