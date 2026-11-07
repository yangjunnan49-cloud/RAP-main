"""Complete sealed-prediction readout against supplied camera poses only."""
import collections
import math
import statistics
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import numpy as np

extra = lib.load(lib.ROOT / 'RUNTIME03_FREEZE.json')
for item in extra['files']:
    assert lib.sha(lib.ROOT / item['path']) == item['sha256']

OUT = lib.ROOT / 'runtime03/evaluate'


def summary(rows, name):
    available = [r for r in rows if r['status'] == 'POSE']
    rotation = [r['rotation_error_deg'] for r in available]
    direction = [r['direction_error_deg'] for r in available if r['direction_error_deg'] is not None]
    bins = {'rotation_le_5': sum(x <= 5 for x in rotation), 'rotation_le_10': sum(x <= 10 for x in rotation),
            'direction_le_15': sum(x <= 15 for x in direction), 'direction_le_30': sum(x <= 30 for x in direction),
            'joint_5_15': sum(r['rotation_error_deg'] <= 5 and r['direction_error_deg'] is not None and r['direction_error_deg'] <= 15 for r in available),
            'joint_10_30': sum(r['rotation_error_deg'] <= 10 and r['direction_error_deg'] is not None and r['direction_error_deg'] <= 30 for r in available)}
    return {'group': name, 'pairs': len(rows), 'pose_predictions': len(available),
            'no_evidence': len(rows) - len(available), 'status_counts': dict(collections.Counter(r['status'] for r in rows)),
            'reference_direction_defined': sum(r['reference_translation_norm_m'] > 1e-9 for r in rows),
            'rotation_error_denominator': len(rotation), 'direction_error_denominator': len(direction),
            'rotation_error_mean_deg': statistics.mean(rotation) if rotation else None,
            'rotation_error_median_deg': statistics.median(rotation) if rotation else None,
            'direction_error_mean_deg': statistics.mean(direction) if direction else None,
            'direction_error_median_deg': statistics.median(direction) if direction else None,
            'unconditional_bin_success_counts': bins, 'bin_denominator_all_pairs': len(rows)}


try:
    frozen = lib.verify_freeze('evaluation')
    seal = lib.verify_seal(lib.ROOT / 'runtime03/predict')
    prediction_seal_sha = lib.sha(lib.ROOT / 'runtime03/predict/SEAL.json')
    result = lib.load(lib.ROOT / 'runtime03/predict/RESULT.json')
    assert result['passed'] and result['pairs'] == 200
    lib.save(OUT / 'REFERENCE_READ_BEGIN.json', {'utc': lib.stamp(), 'prediction_seal_sha256': prediction_seal_sha,
             'prediction_sealed_utc': seal['sealed_utc'], 'all_predictions_complete': True})
    binding = lib.load(lib.ROOT / 'EVALUATION_INPUTS.json')
    method = lib.load(lib.ROOT / 'METHOD.json')
    inputs = lib.load(lib.ROOT / 'PREDICTION_INPUTS.json')
    predictions = lib.load(lib.ROOT / 'runtime03/predict/PREDICTIONS.json')
    assert [p['key'] for p in predictions] == [p['key'] for p in inputs['pairs']]
    tables, source_errors = {}, {}
    for item in binding['poses']:
        p = Path(item['path'])
        assert p.stat().st_size == item['bytes'] and lib.sha(p) == item['sha256']
        data = np.loadtxt(p, dtype=np.float64)
        assert data.shape == ({'00': 4541, '08': 4071}[item['sequence']], 12) and np.isfinite(data).all()
        table = np.tile(np.eye(4), (len(data), 1, 1))
        table[:, :3] = data.reshape(-1, 3, 4)
        selected = sorted({int(p[f]) for p in inputs['pairs'] if p['sequence'] == item['sequence'] for f in ('source_i', 'source_j')})
        rotations = table[selected, :3, :3]
        orth = float(np.max(np.abs(np.swapaxes(rotations, 1, 2) @ rotations - np.eye(3))))
        det = float(np.max(np.abs(np.linalg.det(rotations) - 1)))
        assert orth < method['reference_validity_tolerance'] and det < method['reference_validity_tolerance']
        tables[item['sequence']] = table
        source_errors[item['sequence']] = {'max_abs_RtR_minus_I': orth, 'max_abs_det_minus_1': det, 'reference_not_projected': True}
    labels = {}
    for item in binding['labels']:
        p = Path(item['path'])
        assert p.stat().st_size == item['bytes'] and lib.sha(p) == item['sha256']
        rows = lib.load(p)
        assert len(rows) == 100
        for row in rows:
            key = '%s_%s_%s' % (row['sequence'], row['source_i'], row['source_j'])
            assert key not in labels
            labels[key] = row['stratum']
    assert set(labels) == {p['key'] for p in predictions}
    rows = []
    for p in predictions:
        table = tables[p['sequence']]
        q = np.linalg.solve(table[int(p['source_j'])], table[int(p['source_i'])])
        assert np.isfinite(q).all() and np.array_equal(q[3], [0., 0., 0., 1.])
        deviation = float(np.max(np.abs(q[:3, :3].T @ q[:3, :3] - np.eye(3))))
        assert deviation < method['reference_validity_tolerance']
        norm = float(np.linalg.norm(q[:3, 3]))
        identity_error, _ = lib.angles(np, np.eye(3), np.array([1., 0., 0.]), q, method['reference_translation_epsilon_m'])
        r, t = (None, None)
        if p['status'] == 'POSE':
            r, t = lib.angles(np, np.asarray(p['R_i_to_j']), np.asarray(p['unit_t_i_to_j']), q, method['reference_translation_epsilon_m'])
            assert math.isfinite(r) and (t is None or math.isfinite(t))
        rows.append({**{k: p[k] for k in ('key', 'sequence', 'source_i', 'source_j', 'status', 'matches', 'essential_inliers', 'cheirality_inliers')},
            'stratum': labels[p['key']], 'reference_translation_norm_m': norm,
            'reference_rotation_magnitude_deg': identity_error, 'reference_RtR_deviation': deviation,
            'reference_Q_i_to_j': q.tolist(), 'rotation_error_deg': r, 'direction_error_deg': t})
    groups = [summary(rows, 'all_200')]
    for seq in ('00', '08'):
        data = [r for r in rows if r['sequence'] == seq]
        assert len(data) == 100
        groups.append(summary(data, seq + '/all_100'))
        positives = [r for r in data if r['stratum'] != 'confuser']
        confusers = [r for r in data if r['stratum'] == 'confuser']
        assert len(positives) == 75 and len(confusers) == 25
        groups.extend([summary(positives, seq + '/original_positive_75'), summary(confusers, seq + '/confuser_25')])
        for stratum in sorted({r['stratum'] for r in data}):
            cell = [r for r in data if r['stratum'] == stratum]
            assert len(cell) == 25
            groups.append(summary(cell, seq + '/' + stratum))
    initial_rows = []
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
    lib.save(OUT / 'ROWS.json', rows)
    lib.save(OUT / 'SUMMARY.json', {'groups': groups, 'source_reference_precision': source_errors,
             'role': 'Descriptive exposed-cohort camera 5DoF; no RAP increment, metric scale, physical truth or generalization'})
    lib.complete(OUT, {'pairs': 200, 'source_freeze_sha256': frozen, 'prediction_seal_sha256': prediction_seal_sha,
             'reference_read_after_full_prediction_seal': True, 'new_RAP_training': False})
    print('evaluation complete 200/200; all denominators retained', flush=True)
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
