"""Explicit-point geometry and independent pose-reference checks for SMP2."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import numpy as np
from scipy.spatial.transform import Rotation
import structural_holdout_map_pilot as run
import validate_shared_plane_map_pilot as previous


def bank():
    run.verify()
    seal = run.read(run.BASE/'bank_seal.json')
    for name, digest in seal['files'].items():
        assert run.sha(run.BASE/'bank'/name) == digest
    summary = run.read(run.BASE/'bank/summary.json')
    moment = cost = gradient = prior_cost = 0.
    supported = valid = point_rows = 0
    for window, row in summary.items():
        source = np.load(run.old.BASE/f'bank/{window}.npz', allow_pickle=False)
        z = np.load(run.BASE/f'bank/{window}.npz', allow_pickle=False)
        assert np.array_equal(source['O'], z['O']) and np.array_equal(source['frames'], z['frames'])
        points = [source[f'points_{i}'] for i in range(8)]
        point_rows += sum(map(len, points))
        labels = [z[f'label_{i}'] for i in range(8)]
        stats = {name: z[name] for name in run.FIELDS}
        count = len(stats['counts'])
        assert count == row['full_features']['features']
        direct_initial = previous.direct_planes(points, labels, z['O'], count)
        for k, key in enumerate(stats['keys']):
            payload = 'SMP2|'+window+'|2|'+','.join(str(int(a)) for a in key)
            number = int(hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8], 16)
            assert number == int(z['hash_integers'][k]) and bool(number % 4 == 0) == bool(z['holdout'][k])
            assert np.sum(stats['counts'][k] > 0) >= 3 and stats['counts'][k].sum() >= 40
            center, values, normal = direct_initial[k]
            assert values[0]/max(values.sum(), 1e-15) < .025+1e-12 and values[1] > .005-1e-12 and values[0] <= .015+1e-12
            for i, p in enumerate(points):
                q = p[labels[i] == k]
                assert len(q) == stats['counts'][k, i]
                if not len(q):
                    continue
                assert len(q) >= 6
                moment = max(moment, float(np.max(abs(q.mean(0)-stats['means'][k, i]))),
                             float(np.max(abs(q.T@q/len(q)-stats['seconds'][k, i]))))
                world = q@z['O'][i, :3, :3].T+z['O'][i, :3, 3]
                assert np.all(np.floor(world/2.).astype(np.int64) == key)
                assert abs(normal@(world.mean(0)-center)) <= .20+1e-12
        masks = dict(train=~z['holdout'], holdout=z['holdout'])
        for part, mask in masks.items():
            coverage = []
            for i, label in enumerate(labels):
                used = label >= 0
                chosen = used.copy()
                chosen[used] = mask[label[used]]
                coverage.append(int(chosen.sum()))
            assert coverage == row[part]['per_scan_points'] and int(mask.sum()) == row[part]['patches']
            if np.any(mask):
                normals = np.array([p[2] for p, keep in zip(direct_initial, mask) if keep])
                eigen = np.linalg.eigvalsh(normals.T@normals/len(normals))
                assert np.max(abs(eigen-row[part]['normal_scatter_eigenvalues'])) < 1e-8
        ok = row['train']['patches'] >= 10 and min(row['train']['per_scan_points']) >= 100 and row['holdout']['patches'] >= 5 and min(row['holdout']['per_scan_points']) > 0
        assert bool(ok) == row['supported']
        if not ok:
            assert 'P' not in z and row['trace'] is None
            continue
        supported += 1
        for arm in ('O', 'P'):
            pose = z[arm]
            assert np.max(abs(pose[0]-np.eye(4))) < 1e-12
            assert np.max(abs(pose[:, :3, :3].transpose(0, 2, 1)@pose[:, :3, :3]-np.eye(3))) < 1e-10
            assert np.min(np.linalg.det(pose[:, :3, :3])) > .9999999999
            direct = previous.direct_planes(points, labels, pose, count)
            for part, mask in masks.items():
                variance = np.maximum([p[1][0] for p, keep in zip(direct, mask) if keep], 0.)
                cost = max(cost, abs(float(np.sqrt(np.mean(variance)))-row['geometry'][arm][part]['scan_balanced_patch_rms_m']),
                           float(np.max(abs(variance-row['geometry'][arm][part]['per_patch_variance_m2']))))
            geometry = .5*np.mean([max(p[1][0], 0.) for p, keep in zip(direct, masks['train']) if keep])/run.alg.GEOMETRY_SIGMA**2
            edge = []
            for i in range(7):
                za = np.linalg.solve(z['O'][i], z['O'][i+1])
                actual = np.linalg.solve(pose[i], pose[i+1])
                e = np.linalg.solve(za, actual)
                edge.append(np.sum(Rotation.from_matrix(e[:3, :3]).as_rotvec()**2)/run.alg.PRIOR_R**2+
                            np.sum(e[:3, 3]**2)/run.alg.PRIOR_T**2)
            motion = .5*float(np.mean(edge))
            prior_cost = max(prior_cost, abs(geometry-row['costs'][arm]['geometry']), abs(motion-row['costs'][arm]['motion']))
        assert len(row['trace']) == 24 and all(t['after'] <= t['before']+1e-12 for t in row['trace'])
        final = row['costs']['P']['geometry']+row['costs']['P']['motion']
        assert abs(final-row['trace'][-1]['after']) < 1e-9
        correction = np.stack([np.linalg.solve(a, b) for a, b in zip(z['O'], z['P'])])
        mt = float(np.max(np.linalg.norm(correction[:, :3, 3], axis=1)))
        mr = float(np.max(Rotation.from_matrix(correction[:, :3, :3]).magnitude())*180/np.pi)
        assert abs(mt-row['correction']['max_translation_m']) < 1e-10 and abs(mr-row['correction']['max_rotation_deg']) < 1e-10
        assert bool(mt <= 1. and mr <= 5.) == row['correction']['valid']
        valid += row['correction']['valid']
        train = run.subset(stats, masks['train'])
        g = run.alg.plane_system(train, z['P'])[1]
        for node, axis in ((1, 0), (1, 3), (6, 1), (6, 4)):
            delta = np.zeros(6)
            delta[axis] = 1e-6
            plus, minus = z['P'].copy(), z['P'].copy()
            plus[node] = run.alg.retract(plus[node], delta)
            minus[node] = run.alg.retract(minus[node], -delta)
            fd = (run.alg.cost(train, plus, z['O'], False)[0]-run.alg.cost(train, minus, z['O'], False)[0])/2e-6
            gradient = max(gradient, abs(fd-g[6*(node-1)+axis]))
        print('SMP2 explicit bank check', window, count, flush=True)
    assert moment < 1e-10 and cost < 1e-8 and prior_cost < 1e-8 and gradient < 1e-4
    run.save(run.BASE/'bank_validation.json', dict(passed=True, supported_windows=supported, valid_predictions=int(valid),
             retained_point_rows=point_rows, moment_max_delta=moment, explicit_geometry_max_delta=cost,
             explicit_prior_and_geometry_cost_max_delta=prior_cost, selected_train_gradient_fd=gradient,
             new_numeric_gt_parsed=False, full_optimizer_replay=False,
             independent_full_rejected_feature_census=False))


def evaluate():
    run.verify()
    result = run.read(run.BASE/'results.json')
    summary = run.read(run.BASE/'bank/summary.json')
    assert result['bank_seal_sha256'] == run.sha(run.BASE/'bank_seal.json')
    maximum = gain_delta = 0.
    independent = {}
    for window, row in result['rows'].items():
        seq = window.split('-')[0]
        z = np.load(run.BASE/f'bank/{window}.npz', allow_pickle=False)
        cam = np.loadtxt(run.old.DATA/f'poses/{seq}.txt').reshape(-1, 3, 4)[z['frames']]
        camera = np.repeat(np.eye(4)[None], 8, axis=0)
        camera[:, :3] = cam
        tr = np.eye(4)
        line = next(x for x in (run.old.DATA/f'sequences/{seq}/calib.txt').read_text().splitlines() if x.startswith('Tr:'))
        tr[:3] = np.fromstring(line.split(':')[1], sep=' ').reshape(3, 4)
        lidar = np.stack([np.linalg.solve(tr, q@tr) for q in camera])
        truth = np.stack([np.linalg.solve(lidar[0], q) for q in lidar])
        current = {}
        for arm in row:
            error = np.stack([np.linalg.solve(a, b) for a, b in zip(truth, z[arm])])
            angles = []
            for e in error:
                u, _, vh = np.linalg.svd(e[:3, :3])
                r = u@np.diag([1., 1., np.linalg.det(u@vh)])@vh
                sine = np.linalg.norm([r[2, 1]-r[1, 2], r[0, 2]-r[2, 0], r[1, 0]-r[0, 1]])/2
                angles.append(np.arctan2(sine, (np.trace(r)-1)/2)*180/np.pi)
            t = np.linalg.norm(error[:, :3, 3], axis=1)
            metrics = dict(relative_translation_rmse_m=float(np.sqrt(np.mean(t[1:]**2))),
                           relative_rotation_mean_deg=float(np.mean(angles[1:])), relative_rotation_max_deg=float(np.max(angles)),
                           aligned_position_ate_m=previous.horn_ate(z[arm][:, :3, 3], truth[:, :3, 3]),
                           per_node_translation_m=t.tolist(), per_node_rotation_deg=list(map(float, angles)))
            for name, value in metrics.items():
                maximum = max(maximum, float(np.max(abs(np.array(value)-row[arm][name]))))
            current[arm] = metrics
        if 'P' in current:
            p, o = current['P'], current['O']
            p.update(valid=summary[window]['correction']['valid'],
                     aligned_ate_gain=1-p['aligned_position_ate_m']/o['aligned_position_ate_m'],
                     translation_gain=1-p['relative_translation_rmse_m']/o['relative_translation_rmse_m'],
                     rotation_regression_deg=p['relative_rotation_mean_deg']-o['relative_rotation_mean_deg'])
            gain_delta = max(gain_delta, max(abs(p[k]-row['P'][k]) for k in ('aligned_ate_gain', 'translation_gain', 'rotation_regression_deg')))
        independent[window] = current
    assert maximum < 1e-8 and gain_delta < 1e-8
    p = [r.get('P') for r in independent.values()]
    all_valid = len(p) == 4 and all(m is not None and m['valid'] for m in p)
    if all_valid:
        ratio = np.mean([summary[k]['geometry']['P']['holdout']['scan_balanced_patch_rms_m'] for k in independent])/np.mean(
                        [summary[k]['geometry']['O']['holdout']['scan_balanced_patch_rms_m'] for k in independent])
        checks = dict(all_four_supported_valid=True, ate_improved_windows=sum(m['aligned_ate_gain'] > 0 for m in p),
                      mean_fractional_ate_gain=float(np.mean([m['aligned_ate_gain'] for m in p])),
                      ate_safety=all(m['aligned_ate_gain'] >= -.05 for m in p), translation_safety=all(m['translation_gain'] >= -.05 for m in p),
                      rotation_safety=all(m['rotation_regression_deg'] <= .02 for m in p), mean_holdout_rms_ratio=float(ratio), holdout_safety=bool(ratio <= 1.01))
        checks['eligible'] = bool(checks['ate_improved_windows'] >= 3 and checks['mean_fractional_ate_gain'] >= .05 and
                                 checks['ate_safety'] and checks['translation_safety'] and checks['rotation_safety'] and checks['holdout_safety'])
    else:
        checks = dict(all_four_supported_valid=False, eligible=False)
    assert set(checks) == set(result['gates'])
    for name, value in checks.items():
        if isinstance(value, float):
            assert abs(value-result['gates'][name]) < 1e-8
        else:
            assert value == result['gates'][name]
    run.save(run.BASE/'validation.json', dict(passed=True, independent_metric_max_delta=maximum,
             independent_gain_max_delta=gain_delta, complete_conjunction_checked=True, eligible=checks['eligible'], full_optimizer_replay=False))
    (run.BASE/'INCOMPLETE').unlink()
    print('SMP2 independent metrics/gates passed', maximum, gain_delta, checks, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('bank', 'evaluate'))
    stage = parser.parse_args().stage
    run.record_stage('validate_'+stage, globals()[stage])
