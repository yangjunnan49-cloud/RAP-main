"""Independent action-order residual and line-search audit of saved refit traces."""
import math
import statistics
from pathlib import Path
import baseline_lib as lib


def verify(predictions, raw_rows, root, np):
    inputs = lib.load(root / 'PREDICTION_INPUTS.json')
    invs = {e['sequence']: np.linalg.inv(lib.camera(np, e['path'])) for e in inputs['calibrations']}
    checked = 0
    largest_relative_cost_delta = 0.

    def skew(v):
        return np.asarray([[0., -v[2], v[1]], [v[2], 0., -v[0]], [-v[1], v[0], 0.]])

    def move(rotation, direction, step):
        omega = np.asarray(step[:3])
        magnitude = math.sqrt(sum(float(x) ** 2 for x in omega))
        w = skew(omega)
        a = 1. if magnitude < 1e-12 else math.sin(magnitude) / magnitude
        b = .5 if magnitude < 1e-12 else (1 - math.cos(magnitude)) / magnitude ** 2
        changed = (np.eye(3) + a * w + b * (w @ w)) @ rotation
        unit = np.eye(3)[min(range(3), key=lambda i: abs(direction[i]))]
        tangent_one = np.cross(direction, unit)
        tangent_one /= math.sqrt(sum(float(x) ** 2 for x in tangent_one))
        tangent_two = np.cross(direction, tangent_one)
        new_direction = direction + step[3] * tangent_one + step[4] * tangent_two
        new_direction /= math.sqrt(sum(float(x) ** 2 for x in new_direction))
        return changed, new_direction

    for pred in predictions:
        trace = pred['refinement']['trace']
        if not trace:
            continue
        invk = invs[pred['sequence']]
        with np.load(root / 'runtime03/predict' / pred['evidence'], allow_pickle=False) as data:
            keep = data['essential_mask'] != 0
            p1, p2 = data['first'][keep], data['second'][keep]
        one = np.column_stack((p1, np.ones(len(p1)))) @ invk.T
        two = np.column_stack((p2, np.ones(len(p2)))) @ invk.T

        def residual(rotation, direction):
            essential = skew(direction) @ rotation
            e_one, et_two = one @ essential.T, two @ essential
            numerator = np.einsum('ij,ij->i', two, e_one)
            gradient_two, gradient_one = e_one @ invk, et_two @ invk
            denominator = np.sqrt(np.einsum('ij,ij->i', gradient_two[:, :2], gradient_two[:, :2]) + np.einsum('ij,ij->i', gradient_one[:, :2], gradient_one[:, :2]))
            return numerator / np.maximum(denominator, 1e-12)

        for entry in trace:
            rotation, direction = np.asarray(entry['R_before']), np.asarray(entry['t_before'])
            old_residual = residual(rotation, direction)
            scale = max(1e-6, 1.4826 * statistics.median(abs(float(v)) for v in old_residual))
            assert abs(scale - entry['scale_px']) < 2e-10 * max(1., scale)
            weights = np.asarray([(1 - (float(v) / (4.685 * scale)) ** 2) ** 2 if abs(float(v)) < 4.685 * scale else 0. for v in old_residual])
            assert int(np.count_nonzero(weights)) == entry['positive_weights']
            old_cost = math.fsum(float(w) * float(v) ** 2 for w, v in zip(weights, old_residual))
            tolerance = 2e-9 * max(1e-10, old_cost)
            assert abs(old_cost - entry['old_cost']) <= tolerance
            step = np.asarray(entry['step'])
            assert np.linalg.norm(step) <= .1 + 1e-12
            for index, attempt in enumerate(entry['line_search']):
                assert attempt['fraction'] == 2. ** (-index) and index < 8
                candidate_r, candidate_t = move(rotation, direction, attempt['fraction'] * step)
                errors = residual(candidate_r, candidate_t)
                cost = math.fsum(float(w) * float(v) ** 2 for w, v in zip(weights, errors))
                tol = 2e-9 * max(1e-10, old_cost, cost)
                assert abs(cost - attempt['cost']) <= tol, (pred['key'], index, cost, attempt['cost'])
                largest_relative_cost_delta = max(largest_relative_cost_delta, abs(cost - attempt['cost']) / max(1e-10, old_cost, cost))
                if index < len(entry['line_search']) - 1:
                    assert attempt['cost'] >= entry['old_cost']
                checked += 1
            if entry['accepted']:
                assert np.max(np.abs(candidate_r - entry['R_after'])) < 1e-12
                assert np.max(np.abs(candidate_t - entry['t_after'])) < 1e-12
                assert entry['new_cost'] == entry['line_search'][-1]['cost'] < entry['old_cost']
    groups = lib.load(root / 'runtime03/evaluate/INITIAL_SUMMARY.json')['groups']
    for group in groups:
        name = group['group']
        if name == 'all_200':
            data = raw_rows
        else:
            seq, category = name.split('/')
            data = [r for r in raw_rows if r['sequence'] == seq]
            if category == 'original_positive_75':
                data = [r for r in data if r['stratum'] != 'confuser']
            elif category == 'confuser_25':
                data = [r for r in data if r['stratum'] == 'confuser']
            elif category != 'all_100':
                data = [r for r in data if r['stratum'] == category]
        valid = [r for r in data if r['status'] == 'POSE']
        assert group['pairs'] == group['bin_denominator_all_pairs'] == len(data)
        assert group['pose_predictions'] == len(valid)
        for name, rlim, tlim in [('rotation_le_5', 5, None), ('rotation_le_10', 10, None), ('direction_le_15', None, 15), ('direction_le_30', None, 30), ('joint_5_15', 5, 15), ('joint_10_30', 10, 30)]:
            count = sum((rlim is None or r['rotation_error_deg'] <= rlim) and (tlim is None or (r['direction_error_deg'] is not None and r['direction_error_deg'] <= tlim)) for r in valid)
            assert group['unconditional_bin_success_counts'][name] == count
    return {'independent_line_search_costs_verified': checked, 'largest_scaled_cost_difference': largest_relative_cost_delta,
            'initial_complete_summary_groups_verified': len(groups)}
