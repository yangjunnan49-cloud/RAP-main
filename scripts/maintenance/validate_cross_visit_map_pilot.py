"""CV1 explicit geometry, source preprocessing and independent reference validation."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import numpy as np
from scipy.spatial.transform import Rotation
import cross_visit_map_pilot as run
import validate_shared_plane_map_pilot as check


def proper(t):
    t = t.copy()
    u, _, vh = np.linalg.svd(t[:3, :3])
    t[:3, :3] = u@np.diag([1., 1., np.linalg.det(u@vh)])@vh
    return t


def raw(frame):
    p = np.fromfile(run.old.rawpath('00', int(frame)), np.float32).reshape(-1, 4)[:, :3].astype(np.float64)
    assert np.isfinite(p).all()
    distance = np.sqrt(np.einsum('ij,ij->i', p, p))
    p = p[(distance >= 1.5)&(distance <= 80.)]
    q = p.copy()
    horizontal = np.hypot(p[:, 0], p[:, 1])
    good = horizontal > 1e-6
    c, s = np.cos(.205*np.pi/180), np.sin(.205*np.pi/180)
    q[good, :2] = p[good, :2]*(c-p[good, 2:3]/horizontal[good, None]*s)
    q[good, 2] = p[good, 2]*c+horizontal[good]*s
    key = np.floor(q/.5).astype(np.int64)
    order = np.lexsort((np.arange(len(key)), key[:, 2], key[:, 1], key[:, 0]))
    first = np.r_[True, np.any(key[order][1:] != key[order][:-1], axis=1)]
    result = q[order[first]]
    if len(result) > 6000:
        result = result[np.linspace(0, len(result)-1, 6000, dtype=np.int64)]
    return result


def shape_correction(initial, poses):
    internal = []
    for ids, endpoint in ((range(8), 0), (range(8, 16), 15)):
        for i in ids:
            a = np.linalg.solve(initial[endpoint], initial[i])
            b = np.linalg.solve(poses[endpoint], poses[i])
            internal.append(np.linalg.solve(a, b))
    placement = np.linalg.solve(initial[-1], poses[-1])
    mt = max(float(np.linalg.norm(e[:3, 3])) for e in internal)
    mr = max(float(Rotation.from_matrix(e[:3, :3]).magnitude()*180/np.pi) for e in internal)
    pt = float(np.linalg.norm(placement[:3, 3]))
    pr = float(Rotation.from_matrix(placement[:3, :3]).magnitude()*180/np.pi)
    return dict(internal_translation_m=mt, internal_rotation_deg=mr, endpoint_translation_m=pt,
                endpoint_rotation_deg=pr, valid=bool(mt <= 1. and mr <= 5. and pt <= 5. and pr <= 25.))


def bank():
    frozen = run.verify()
    seal = run.read(run.BASE/'bank_seal.json')
    for name, digest in seal['files'].items():
        assert run.sha(run.BASE/'bank'/name) == digest
    z = np.load(run.BASE/'bank/case.npz', allow_pickle=False)
    summary = run.read(run.BASE/'bank/summary.json')
    binding = frozen['binding']
    source_frames = run.read(run.old.source('00')/'source_frames.json')['source_frame_ids']
    permutation = [7]+list(range(7))+list(range(8, 16))
    rows = [binding['raw_bindings'][i] for i in permutation]
    assert z['nodes'].tolist() == [r['node'] for r in rows] and z['frames'].tolist() == [source_frames[r['node']] for r in rows]
    native = np.repeat(np.eye(4)[None], 16, axis=0)
    native[:, :3] = np.loadtxt(run.old.source('00')/'odom_poses.txt').reshape(-1, 3, 4)[z['nodes']]
    assert np.array_equal(native, z['native_absolute'])
    projected = np.array([proper(t) for t in native])
    initial_z = proper(np.array(binding['selected']['T_rel']))
    assert np.max(abs(projected-z['proper_absolute'])) < 1e-12 and np.max(abs(initial_z-z['Z'])) < 1e-12
    o = np.stack([np.linalg.solve(projected[0], t) for t in projected])
    b = o.copy()
    b[8:] = np.stack([initial_z@np.linalg.solve(projected[-1], t) for t in projected[8:]])
    assert np.max(abs(o-z['O'])) < 1e-10 and np.max(abs(b-z['B'])) < 1e-10
    points, raw_delta = [], 0.
    for i, frame in enumerate(z['frames']):
        p = raw(frame)
        assert p.shape == z[f'points_{i}'].shape
        raw_delta = max(raw_delta, float(np.max(abs(p-z[f'points_{i}']))))
        points.append(z[f'points_{i}'])
    assert raw_delta < 1e-10
    labels = [z[f'label_{i}'] for i in range(16)]
    stats = {name: z[name] for name in run.FIELDS}
    count = len(stats['counts'])
    direct = check.direct_planes(points, labels, z['B'], count)
    moment = geometry = prior_delta = gradient = 0.
    for k, key in enumerate(z['keys']):
        assert stats['counts'][k, :8].sum() > 0 and stats['counts'][k, 8:].sum() > 0
        assert np.sum(stats['counts'][k] > 0) >= 3 and stats['counts'][k].sum() >= 40
        text = 'CV1|00|2429|3373|2|'+','.join(str(int(v)) for v in key)
        number = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        assert number == int(z['hash_integers'][k]) and bool(number % 4 == 0) == bool(z['holdout'][k])
        center, values, normal = direct[k]
        assert values[0]/max(values.sum(), 1e-15) < .025+1e-12 and values[1] > .005-1e-12 and values[0] <= .015+1e-12
        for i, p in enumerate(points):
            q = p[labels[i] == k]
            assert len(q) == stats['counts'][k, i]
            if not len(q):
                continue
            assert len(q) >= 6
            moment = max(moment, float(np.max(abs(q.mean(0)-stats['means'][k, i]))),
                         float(np.max(abs(q.T@q/len(q)-stats['seconds'][k, i]))))
            world = q@z['B'][i, :3, :3].T+z['B'][i, :3, 3]
            assert np.all(np.floor(world/2.).astype(np.int64) == key)
            assert abs(normal@(world.mean(0)-center)) <= .20+1e-12
    masks = dict(train=~z['holdout'], holdout=z['holdout'])
    for part, mask in masks.items():
        coverage = [int(stats['counts'][mask, i].sum()) for i in range(16)]
        assert coverage == summary[part]['per_scan_points'] and int(mask.sum()) == summary[part]['patches']
        normals = np.array([entry[2] for entry, keep in zip(direct, mask) if keep])
        if len(normals):
            assert np.max(abs(np.linalg.eigvalsh(normals.T@normals/len(normals))-summary[part]['normal_scatter_eigenvalues'])) < 1e-8
        for visit, ids in enumerate((range(8), range(8, 16))):
            assert sum(coverage[i] for i in ids) == summary[part]['per_visit_points'][visit]
            assert sum(coverage[i] > 0 for i in ids) == summary[part]['per_visit_contributing_scans'][visit]
    supported = summary['train']['patches'] >= 10 and min(summary['train']['per_visit_contributing_scans']) >= 3 and min(summary['train']['per_visit_points']) >= 100 and summary['holdout']['patches'] >= 5
    assert bool(supported) == summary['supported']
    pairs = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(8,9),(9,10),(10,11),(11,12),(12,13),(13,14),(14,15)]
    assert summary['edges'] == [list(pair) for pair in pairs]
    for arm in ('O', 'B', 'F', 'J') if supported else ('O', 'B'):
        pose = z[arm]
        assert np.max(abs(pose[0]-np.eye(4))) < 1e-12
        assert np.max(abs(pose[:, :3, :3].transpose(0,2,1)@pose[:, :3, :3]-np.eye(3))) < 1e-10
        assert np.min(np.linalg.det(pose[:, :3, :3])) > .9999999999
        if not supported:
            continue
        direct_pose = check.direct_planes(points, labels, pose, count)
        for part, mask in masks.items():
            variance = np.maximum([entry[1][0] for entry, keep in zip(direct_pose, mask) if keep], 0.)
            geometry = max(geometry, float(np.max(abs(variance-summary['geometry'][arm][part]['per_patch_variance_m2']))),
                           abs(float(np.sqrt(np.mean(variance)))-summary['geometry'][arm][part]['rms_m']))
        geo_cost = .5*np.mean([max(entry[1][0], 0.) for entry, keep in zip(direct_pose, masks['train']) if keep])/run.plane.GEOMETRY_SIGMA**2
        residuals = []
        for i, j in pairs:
            measurement = np.linalg.solve(z['B'][i], z['B'][j])
            relative = np.linalg.solve(pose[i], pose[j])
            error = np.linalg.solve(measurement, relative)
            residuals.append(np.sum(Rotation.from_matrix(error[:3,:3]).as_rotvec()**2)/run.plane.PRIOR_R**2+
                             np.sum(error[:3,3]**2)/run.plane.PRIOR_T**2)
        motion = .5*float(np.mean(residuals))
        prior_delta = max(prior_delta, abs(motion-summary['costs'][arm]['motion']), abs(geo_cost-summary['costs'][arm]['geometry']))
        if arm in ('F', 'J'):
            trace = summary['traces'][arm]
            assert len(trace) == 24 and all(t['after'] <= t['before']+1e-12 for t in trace)
            assert abs(trace[-1]['after']-(geo_cost+(motion if arm == 'J' else 0.))) < 1e-8
            correction = shape_correction(z['B'], pose)
            for name, value in correction.items():
                if name == 'valid':
                    assert value == summary['corrections'][arm][name]
                else:
                    assert abs(value-summary['corrections'][arm][name]) < 1e-9
            if arm == 'F':
                assert correction['internal_translation_m'] < 1e-10 and correction['internal_rotation_deg'] < 1e-10
            train = run.subset(stats, masks['train'])
            g = run.alg.system(train, z['B'], pose, arm)[1]
            axes = range(6) if arm == 'F' else (0,3,36,39,84,87)
            for axis in axes:
                delta = np.zeros(len(g))
                delta[axis] = 1e-6
                plus, minus = run.alg.move(pose, delta, arm), run.alg.move(pose, -delta, arm)
                fd = (run.alg.cost(train, z['B'], plus, arm)[0]-run.alg.cost(train, z['B'], minus, arm)[0])/2e-6
                gradient = max(gradient, abs(fd-g[axis]))
    assert moment < 1e-10 and geometry < 1e-8 and prior_delta < 1e-8 and gradient < 1e-4
    run.save(run.BASE/'bank_validation.json', dict(passed=True, supported=bool(supported), raw_scans=16,
             retained_points=sum(map(len, points)), independent_raw_max_delta=raw_delta, moment_max_delta=moment,
             explicit_geometry_max_delta=geometry, explicit_cost_max_delta=prior_delta, selected_real_gradient_fd=gradient,
             new_numeric_gt_parsed=False, full_optimizer_replay=False, independent_rejected_feature_census=False))
    if not supported:
        assert 'F' not in z and 'J' not in z
        run.save(run.BASE/'validation.json', dict(passed=True, prerequisite_stop=True,
                 decision='INSUFFICIENT_FIXED_CROSS_VISIT_SUPPORT', new_numeric_gt_parsed=False))
        (run.BASE/'INCOMPLETE').unlink()
    print('CV1 explicit bank passed', supported, raw_delta, geometry, gradient, flush=True)


def angle(error):
    r = proper(error)[:3,:3]
    sine = np.linalg.norm([r[2,1]-r[1,2], r[0,2]-r[2,0], r[1,0]-r[0,1]])/2
    return float(np.arctan2(sine, (np.trace(r)-1)/2)*180/np.pi)


def local_metrics(truth, poses, indices):
    reference = np.stack([np.linalg.solve(truth[indices[0]], truth[i]) for i in indices])
    current = np.stack([np.linalg.solve(poses[indices[0]], poses[i]) for i in indices])
    error = [np.linalg.solve(a,b) for a,b in zip(reference,current)]
    t = np.array([np.linalg.norm(e[:3,3]) for e in error])
    r = np.array([angle(e) for e in error])
    return dict(relative_translation_rmse_m=float(np.sqrt(np.mean(t[1:]**2))), relative_rotation_mean_deg=float(r[1:].mean()),
                relative_rotation_max_deg=float(r.max()), aligned_position_ate_m=check.horn_ate(current[:,:3,3],reference[:,:3,3]),
                per_node_translation_m=t.tolist(), per_node_rotation_deg=r.tolist())


def evaluate():
    run.verify()
    result = run.read(run.BASE/'results.json')
    summary = run.read(run.BASE/'bank/summary.json')
    assert result['bank_seal_sha256'] == run.sha(run.BASE/'bank_seal.json')
    z = np.load(run.BASE/'bank/case.npz', allow_pickle=False)
    camera = np.repeat(np.eye(4)[None], 16, axis=0)
    camera[:,:3] = np.loadtxt(run.old.DATA/'poses/00.txt').reshape(-1,3,4)[z['frames']]
    tr = np.eye(4)
    line = next(s for s in (run.old.DATA/'sequences/00/calib.txt').read_text().splitlines() if s.startswith('Tr:'))
    tr[:3] = np.fromstring(line.split(':')[1], sep=' ').reshape(3,4)
    truth = np.stack([np.linalg.solve(tr, t@tr) for t in camera])
    reference = np.stack([np.linalg.solve(truth[0], t) for t in truth])
    independent, maximum = {}, 0.
    for arm in ('O','B','F','J'):
        pose = z[arm]
        e = np.linalg.solve(reference[-1], pose[-1])
        metric = dict(joint_aligned_ate_m=check.horn_ate(pose[:,:3,3], reference[:,:3,3]),
                      endpoint_translation_m=float(np.linalg.norm(e[:3,3])), endpoint_rotation_deg=angle(e), visits={})
        for name, indices in (('A', list(range(8))), ('B',[15]+list(range(8,15)))):
            metric['visits'][name] = local_metrics(truth, pose, indices)
            for key, value in metric['visits'][name].items():
                maximum = max(maximum, float(np.max(abs(np.array(value)-result['rows'][arm]['visits'][name][key]))))
        for key in ('joint_aligned_ate_m','endpoint_translation_m','endpoint_rotation_deg'):
            maximum = max(maximum, abs(metric[key]-result['rows'][arm][key]))
        independent[arm] = metric
    assert maximum < 1e-8
    conjunctions = {}
    for candidate, baseline in (('F','B'),('J','B'),('J','F')):
        c, b = independent[candidate], independent[baseline]
        recorded = result['comparisons'][candidate+'vs'+baseline]
        valid = summary['corrections'][candidate]['valid'] and (baseline == 'B' or summary['corrections'][baseline]['valid'])
        gain_ate = 1-c['joint_aligned_ate_m']/b['joint_aligned_ate_m']
        gain_t = 1-c['endpoint_translation_m']/b['endpoint_translation_m']
        rotation = c['endpoint_rotation_deg']-b['endpoint_rotation_deg']
        safety = True
        for name in ('A','B'):
            cm, bm = c['visits'][name], b['visits'][name]
            ga = 1-cm['aligned_position_ate_m']/bm['aligned_position_ate_m']
            gt = 1-cm['relative_translation_rmse_m']/bm['relative_translation_rmse_m']
            gr = cm['relative_rotation_mean_deg']-bm['relative_rotation_mean_deg']
            safety &= ga >= -.05 and gt >= -.05 and gr <= .02
            for key, value in (('ate_gain',ga),('translation_gain',gt),('rotation_regression_deg',gr)):
                assert abs(value-recorded['visit_changes'][name][key]) < 1e-8
        ratio = summary['geometry'][candidate]['holdout']['rms_m']/summary['geometry'][baseline]['holdout']['rms_m']
        eligible = bool(valid and gain_ate >= .05 and gain_t >= .05 and rotation <= .01 and safety and ratio <= 1.01)
        for key,value in (('joint_ate_gain',gain_ate),('endpoint_translation_gain',gain_t),('endpoint_rotation_regression_deg',rotation),('holdout_rms_ratio',ratio)):
            assert abs(value-recorded[key]) < 1e-8
        assert recorded['valid'] == valid and recorded['eligible'] == eligible and recorded['visit_safety'] == bool(safety)
        assert recorded['denominators_positive'] and recorded['holdout_safety'] == bool(ratio <= 1.01)
        conjunctions[candidate+'vs'+baseline] = eligible
    run.save(run.BASE/'validation.json', dict(passed=True, independent_metric_max_delta=maximum,
             complete_conjunctions_checked=conjunctions, full_optimizer_replay=False, full_sequence_metric_claim=False))
    (run.BASE/'INCOMPLETE').unlink()
    print('CV1 independent metrics passed', maximum, conjunctions, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('bank','evaluate'))
    stage = parser.parse_args().stage
    run.record_stage('validate_'+stage, globals()[stage])
