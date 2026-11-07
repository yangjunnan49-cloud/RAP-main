"""Prospective ER1 source preparation; no pixel/reference numeric decode."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'visual-baseline-execution-01'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    with (ROOT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def text(name, content):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as f:
        f.write(content)


def replace_once(content, before, after):
    assert content.count(before) == 1, before[:100]
    return content.replace(before, after, 1)


assert not (ROOT / 'SOURCE_FREEZE.json').exists(), 'No re-freeze'
assert (dt.datetime.now(dt.timezone.utc) - dt.datetime(2026, 10, 28, 7, 1, 26, tzinfo=dt.timezone.utc)).total_seconds() < 1800
oldfreeze = json.loads((OLD / 'SOURCE_FREEZE.json').read_text())
for e in oldfreeze['files']:
    assert (OLD / e['path']).stat().st_size == e['bytes'] and sha(OLD / e['path']) == e['sha256']
copies = ['baseline_lib.py', 'features.py', 'host.ps1', 'PREDICTION_INPUTS.json', 'EVALUATION_INPUTS.json']
for name in copies:
    with (ROOT / name).open('xb') as f:
        f.write((OLD / name).read_bytes())
with (ROOT / 'REFERENCE_PROTOCOL.md').open('xb') as f:
    f.write((OLD / 'PROTOCOL.md').read_bytes())
method = json.loads((OLD / 'METHOD.json').read_text())
method['scope_origin_utc'] = '2026-10-28T07:01:26+00:00'
method['refinement'] = {'iterations': 30, 'scale_floor_px': 1e-6, 'median_multiplier': 1.4826,
    'cutoff_multiplier': 4.685, 'derivative_step_rad': 1e-6, 'step_stop_rad': 1e-10,
    'maximum_step_rad': .1, 'backtracks': 8}
save('METHOD.json', method)
control = (OLD / 'controls.py').read_text()
control = replace_once(control, 'import baseline_lib as lib', 'import baseline_lib as lib\nimport refine_lib')
control = control.replace('lib.estimate(', 'refine_lib.estimate(')
extra = '''    raw = robust['initial_pose']
    raw_err = lib.angles(np, np.asarray(raw['R_i_to_j']), np.asarray(raw['unit_t_i_to_j']), target, 1e-9)
    check('raw_outlier_failure_retained_same_seed_and_fixture', abs(raw_err[0] - 0.113146318316918) < 1e-9 and raw_err[0] >= .1, raw_angle_errors_deg=raw_err)
    trace = robust['refinement']['trace']
    check('robust_refit_has_strict_fixed_weight_cost_decrease', any(e['accepted'] for e in trace) and all(not e['accepted'] or e['new_cost'] < e['old_cost'] for e in trace), iterations=len(trace))
    test_step = np.array([.01, -.005, .003, .02, -.01])
    ur, ut = refine_lib.update(np, r, t / np.linalg.norm(t), test_step)
    check('refit_update_stays_proper_and_unit', np.max(np.abs(ur.T @ ur - np.eye(3))) < 1e-12 and abs(np.linalg.det(ur) - 1) < 1e-12 and abs(np.linalg.norm(ut) - 1) < 1e-12)
'''
control = replace_once(control, '    lib.read_gate([cache], OUT)', extra + '    lib.read_gate([cache], OUT)')
text('controls.py', control)
prediction = (OLD / 'predict.py').read_text()
prediction = replace_once(prediction, 'import baseline_lib as lib', 'import baseline_lib as lib\nimport refine_lib')
prediction = prediction.replace('lib.estimate(', 'refine_lib.estimate(')
text('predict.py', prediction)
evaluation = (OLD / 'evaluate.py').read_text()
evaluation = replace_once(evaluation, "    lib.save(OUT / 'ROWS.json', rows)", '''    initial_rows = []
    for pred, row in zip(predictions, rows):
        initial = pred['initial_pose']
        ri, ti = None, None
        if initial['status'] == 'POSE':
            ri, ti = lib.angles(np, np.asarray(initial['R_i_to_j']), np.asarray(initial['unit_t_i_to_j']), np.asarray(row['reference_Q_i_to_j']), method['reference_translation_epsilon_m'])
        initial_rows.append({**row, 'status': initial['status'], 'rotation_error_deg': ri, 'direction_error_deg': ti})
    initial_groups = [summary(initial_rows, 'all_200')]
    for seq in ('00', '08'):
        data = [r for r in initial_rows if r['sequence'] == seq]
        initial_groups.append(summary(data, seq + '/all_100'))
        initial_groups.append(summary([r for r in data if r['stratum'] != 'confuser'], seq + '/original_positive_75'))
        initial_groups.append(summary([r for r in data if r['stratum'] == 'confuser'], seq + '/confuser_25'))
        for stratum in sorted({r['stratum'] for r in data}):
            initial_groups.append(summary([r for r in data if r['stratum'] == stratum], seq + '/' + stratum))
    lib.save(OUT / 'INITIAL_ROWS.json', initial_rows)
    lib.save(OUT / 'INITIAL_SUMMARY.json', {'groups': initial_groups, 'role': 'Raw proposal retained as complete descriptive comparator; VB1 control remains failed'})
    lib.save(OUT / 'ROWS.json', rows)''')
text('evaluate.py', evaluation)
audit = (OLD / 'audit.py').read_text()
audit = replace_once(audit, "    lib.complete(OUT, {'source_freeze_sha256': frozen", '''    raw_rows = lib.load(lib.ROOT / 'evaluate/INITIAL_ROWS.json')
    trace_steps = 0
    for pred, row in zip(predictions, raw_rows):
        initial = pred['initial_pose']
        assert row['key'] == pred['key'] and row['status'] == initial['status']
        if initial['status'] == 'POSE':
            rr, tt = independent_angles(initial['R_i_to_j'], initial['unit_t_i_to_j'], row['reference_Q_i_to_j'])
            assert abs(rr - row['rotation_error_deg']) < 1e-6
            assert (tt is None and row['direction_error_deg'] is None) or (tt is not None and abs(tt - row['direction_error_deg']) < 1e-6)
        for entry in pred['refinement']['trace']:
            assert entry['positive_weights'] >= 8 and math.isfinite(entry['old_cost']) and entry['scale_px'] >= 1e-6
            for key in ('R_before', 'R_after'):
                if key in entry:
                    matrix_r = np.asarray(entry[key])
                    assert np.max(np.abs(matrix_r.T @ matrix_r - np.eye(3))) < 1e-6 and abs(np.linalg.det(matrix_r) - 1) < 1e-6
            for key in ('t_before', 't_after'):
                if key in entry:
                    assert abs(np.linalg.norm(entry[key]) - 1) < 1e-12
            if entry['accepted']:
                assert entry['new_cost'] < entry['old_cost'] and entry['line_search'][-1]['cost'] == entry['new_cost']
            trace_steps += 1
    import audit_refit
    independent_refit = audit_refit.verify(predictions, raw_rows, lib.ROOT, np)
    lib.save(OUT / 'REFIT_TRACE_AUDIT.json', {'raw_pose_metrics_verified': 200, 'finite_manifold_trace_steps': trace_steps, 'all_accepted_recorded_costs_strictly_decrease': True, **independent_refit})
    lib.complete(OUT, {'source_freeze_sha256': frozen''')
text('audit.py', audit)
save('ORIGINAL_BINDING.json', {'source_freeze_sha256': sha(OLD / 'SOURCE_FREEZE.json'),
    'unchanged_copies': [{'path': name, 'sha256': sha(OLD / name)} for name in copies],
    'original_failed_control_sha256': sha(OLD / 'controls/check_08.json'),
    'original_status_sha256': sha(OLD / 'STATUS.json'),
    'changes': ['New explicit robust geometric refit', 'Prediction/control call refit wrapper', 'Preserve and evaluate all initial poses', 'Audit initial metrics and refinement traces'],
    'original_gate_parameters_seed_fixture_unchanged': True})
roles = {'baseline_lib.py': 'shared', 'refine_lib.py': 'shared', 'METHOD.json': 'shared', 'PROTOCOL.md': 'shared',
    'REFERENCE_PROTOCOL.md': 'shared', 'ORIGINAL_BINDING.json': 'shared', 'controls.py': 'controls',
    'features.py': 'prediction', 'predict.py': 'prediction', 'PREDICTION_INPUTS.json': 'prediction',
    'evaluate.py': 'evaluation', 'EVALUATION_INPUTS.json': 'evaluation', 'audit.py': 'audit',
    'host.ps1': 'host', 'prepare.py': 'preparation', 'audit_refit.py': 'audit'}
entries = []
for name, role in roles.items():
    p = ROOT / name
    if p.suffix == '.py':
        ast.parse(p.read_text(encoding='utf-8'), filename=name)
    entries.append({'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'role': role})
save('SOURCE_FREEZE.json', {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'files': entries,
    'measured_image_feature_or_pose_calls': 0, 'supplied_reference_decodes': 0,
    'original_VB1_fail_unchanged': True, 'refit_parameters_frozen_before_controls_and_images': True})
print('ER1 source freeze complete; no measured pixels or pose values read')
