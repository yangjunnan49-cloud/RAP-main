"""Independent saved-evidence audit; no new visual predictions or fitting."""
import collections
from decimal import Decimal, localcontext
import math
import os
import statistics
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import numpy as np

OUT = lib.ROOT / 'audit'


def independent_solve(left, right):
    a = [[*left[i], *right[i]] for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(a[r][col]))
        assert a[pivot][col] != 0
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [x / scale for x in a[col]]
        for row in range(4):
            if row != col:
                factor = a[row][col]
                a[row] = [x - factor * y for x, y in zip(a[row], a[col])]
    return [[float(x) for x in row[4:]] for row in a]


def independent_angles(rotation, direction, q):
    delta = [[sum(rotation[i][k] * q[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
    sine = math.sqrt(sum(v * v for v in (delta[2][1] - delta[1][2], delta[0][2] - delta[2][0], delta[1][0] - delta[0][1]))) / 2
    cosine = (sum(delta[i][i] for i in range(3)) - 1) / 2
    r = math.atan2(sine, cosine) * 180 / math.pi
    norm = math.sqrt(sum(q[i][3] ** 2 for i in range(3)))
    t = None if norm <= 1e-9 else math.acos(max(-1., min(1., sum(direction[i] * q[i][3] for i in range(3)) / norm))) * 180 / math.pi
    return r, t


def samples(size, matched):
    ordinary = [i * (size - 1) // 9 for i in range(min(10, size))] if size else []
    chosen = [matched[i * (len(matched) - 1) // 9] for i in range(min(10, len(matched)))] if len(matched) else []
    return sorted(set(ordinary + [int(x) for x in chosen]))


def nearest(query, table):
    difference = table.astype(np.float64) - query.astype(np.float64)
    squared = np.einsum('ij,ij->i', difference, difference)
    order = np.argsort(squared, kind='stable')[:2]
    distance = np.sqrt(squared[order])
    allowance = 256 * np.finfo(np.float32).eps * max(1., float(distance[-1]))
    clear = abs(float(distance[0] - .75 * distance[1])) > allowance and float(distance[1] - distance[0]) > allowance
    return int(order[0]), bool(distance[0] < .75 * distance[1]), clear


try:
    frozen = lib.verify_freeze('audit')
    for stage in ('controls', 'features', 'predict', 'evaluate'):
        lib.verify_seal(lib.ROOT / stage)
        assert lib.load(lib.ROOT / stage / 'RESULT.json')['passed']
    inputs = lib.load(lib.ROOT / 'PREDICTION_INPUTS.json')
    binding = lib.load(lib.ROOT / 'EVALUATION_INPUTS.json')
    predictions = lib.load(lib.ROOT / 'predict/PREDICTIONS.json')
    rows = lib.load(lib.ROOT / 'evaluate/ROWS.json')
    assert len(predictions) == len(rows) == 200
    assert [p['key'] for p in predictions] == [p['key'] for p in inputs['pairs']] == [r['key'] for r in rows]
    normalize = lambda p: os.path.normcase(str(Path(p).resolve()))
    feature_result = lib.load(lib.ROOT / 'features/RESULT.json')
    predict_result = lib.load(lib.ROOT / 'predict/RESULT.json')
    assert set(feature_result['audited_read_paths']) == {normalize(r['path']) for r in inputs['images']}
    feature_index = lib.load(lib.ROOT / 'features/INDEX.json')
    allowed = {normalize(lib.ROOT / 'features' / e['cache']) for e in feature_index} | {normalize(e['path']) for e in inputs['calibrations']}
    assert set(predict_result['audited_read_paths']) == allowed
    begin = lib.load(lib.ROOT / 'evaluate/REFERENCE_READ_BEGIN.json')
    pred_seal = lib.load(lib.ROOT / 'predict/SEAL.json')
    assert begin['utc'] > pred_seal['sealed_utc'] > predict_result['completed_utc']
    assert begin['prediction_seal_sha256'] == lib.sha(lib.ROOT / 'predict/SEAL.json')
    caches = {}
    image_map = {(r['sequence'], r['frame']): r for r in inputs['images']}
    for e in feature_index:
        with np.load(lib.ROOT / 'features' / e['cache'], allow_pickle=False) as data:
            xy, desc, kp = data['xy'], data['descriptors'], data['keypoints']
        image = image_map[(e['sequence'], e['frame'])]
        assert desc.dtype == np.float32 and desc.shape == (e['keypoints'], 128)
        assert xy.dtype == np.float64 and xy.shape == (len(desc), 2) and kp.shape == (len(desc), 7)
        assert np.isfinite(kp).all() and np.isfinite(desc).all() and np.array_equal(kp[:, :2], xy)
        assert np.all(xy >= 0) and np.all(xy[:, 0] < image['width']) and np.all(xy[:, 1] < image['height'])
        assert e['image_sha256'] == image['sha256']
        caches[(e['sequence'], e['frame'])] = (xy, desc)
    checked, ambiguous = 0, 0
    for p in predictions:
        ax, ad = caches[(p['sequence'], p['source_i'].zfill(6))]
        bx, bd = caches[(p['sequence'], p['source_j'].zfill(6))]
        with np.load(lib.ROOT / 'predict' / p['evidence'], allow_pickle=False) as data:
            indices, first, second = data['indices'], data['first'], data['second']
            em, cm, essential = data['essential_mask'], data['cheirality_mask'], data['E']
        assert indices.shape == (p['matches'], 2) and len(set(map(tuple, indices))) == len(indices)
        assert np.array_equal(indices, np.asarray(sorted(map(tuple, indices)), dtype=np.int32).reshape(-1, 2))
        assert len(set(indices[:, 0])) == len(indices) and len(set(indices[:, 1])) == len(indices)
        assert np.array_equal(first, ax[indices[:, 0]]) and np.array_equal(second, bx[indices[:, 1]])
        assert int(em.sum()) == p['essential_inliers'] and int(cm.sum()) == p['cheirality_inliers'] and np.all(cm <= em)
        matchset = set(map(tuple, indices))
        if len(ad) >= 2 and len(bd) >= 2:
            for source, target, transpose in ((ad, bd, False), (bd, ad, True)):
                selected = samples(len(source), indices[:, 1 if transpose else 0])
                for i in selected:
                    j, good, clear = nearest(source[i], target)
                    back, reverse_good, reverse_clear = nearest(target[j], source)
                    expected = good and reverse_good and back == i
                    actual = ((j, i) if transpose else (i, j)) in matchset
                    if clear and reverse_clear:
                        assert actual == expected, (p['key'], i, transpose)
                        checked += 1
                    else:
                        ambiguous += 1
        if p['status'] == 'POSE':
            rotation = np.asarray(p['R_i_to_j'])
            direction = np.asarray(p['unit_t_i_to_j'])
            assert p['matches'] >= 8 and p['essential_inliers'] >= 8 and p['cheirality_inliers'] >= 8
            assert np.max(np.abs(rotation.T @ rotation - np.eye(3))) < 1e-6 and abs(np.linalg.det(rotation) - 1) < 1e-6
            assert abs(np.linalg.norm(direction) - 1) < 1e-12
            x, y, z = direction
            cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
            analytic = cross @ rotation
            start = p['selected_essential_index'] * 3
            selected_e = essential[start:start + 3]
            one = selected_e / np.linalg.norm(selected_e)
            two = analytic / np.linalg.norm(analytic)
            assert min(np.linalg.norm(one - two), np.linalg.norm(one + two)) < 1e-6
        else:
            assert p['R_i_to_j'] is None and p['unit_t_i_to_j'] is None
    decimal_tables = {}
    for entry in binding['poses']:
        assert lib.sha(entry['path']) == entry['sha256']
        decimal_tables[entry['sequence']] = [[Decimal(token) for token in line.split()] for line in Path(entry['path']).read_text().splitlines()]

    def matrix(seq, frame):
        a = decimal_tables[seq][int(frame)]
        return [a[:4], a[4:8], a[8:12], [Decimal(0), Decimal(0), Decimal(0), Decimal(1)]]

    max_matrix, max_rotation, max_direction = 0., 0., 0.
    with localcontext() as context:
        context.prec = 60
        for p, row in zip(predictions, rows):
            q = independent_solve(matrix(p['sequence'], p['source_j']), matrix(p['sequence'], p['source_i']))
            difference = max(abs(q[i][j] - row['reference_Q_i_to_j'][i][j]) for i in range(4) for j in range(4))
            max_matrix = max(max_matrix, difference)
            assert difference < 5e-11
            if p['status'] == 'POSE':
                r, t = independent_angles(p['R_i_to_j'], p['unit_t_i_to_j'], q)
                max_rotation = max(max_rotation, abs(r - row['rotation_error_deg']))
                assert abs(r - row['rotation_error_deg']) < 1e-6
                if t is None:
                    assert row['direction_error_deg'] is None
                else:
                    max_direction = max(max_direction, abs(t - row['direction_error_deg']))
                    assert abs(t - row['direction_error_deg']) < 1e-6
            else:
                assert row['rotation_error_deg'] is None and row['direction_error_deg'] is None
    summaries = lib.load(lib.ROOT / 'evaluate/SUMMARY.json')['groups']
    for group in summaries:
        if group['group'] == 'all_200':
            data = rows
        else:
            seq, category = group['group'].split('/')
            data = [r for r in rows if r['sequence'] == seq]
            if category == 'original_positive_75':
                data = [r for r in data if r['stratum'] != 'confuser']
            elif category == 'confuser_25':
                data = [r for r in data if r['stratum'] == 'confuser']
            elif category != 'all_100':
                data = [r for r in data if r['stratum'] == category]
        valid = [r for r in data if r['status'] == 'POSE']
        assert group['pairs'] == group['bin_denominator_all_pairs'] == len(data)
        assert group['pose_predictions'] == len(valid) and group['no_evidence'] == len(data) - len(valid)
        assert group['status_counts'] == dict(collections.Counter(r['status'] for r in data))
        for key, rlim, tlim in [('rotation_le_5', 5, None), ('rotation_le_10', 10, None),
                ('direction_le_15', None, 15), ('direction_le_30', None, 30), ('joint_5_15', 5, 15), ('joint_10_30', 10, 30)]:
            count = sum((rlim is None or r['rotation_error_deg'] <= rlim) and (tlim is None or (r['direction_error_deg'] is not None and r['direction_error_deg'] <= tlim)) for r in valid)
            assert group['unconditional_bin_success_counts'][key] == count
    lib.complete(OUT, {'source_freeze_sha256': frozen, 'complete_images': 273, 'complete_pairs': 200,
        'independent_clear_nearest_ratio_checks': checked, 'numerically_ambiguous_checks_retained': ambiguous,
        'Decimal60_reference_transforms': 200, 'max_reference_element_difference': max_matrix,
        'max_rotation_metric_difference_deg': max_rotation, 'max_direction_metric_difference_deg': max_direction,
        'prediction_reference_separation_verified': True, 'summary_groups_verified': len(summaries)})
    print('audit PASS: 273 caches, 200 pairs, %d independent descriptor checks, 200 Decimal transforms' % checked)
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
