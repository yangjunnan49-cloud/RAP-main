"""Source-bound one-case CV1 orchestration; no model inference or trajectory replay."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import importlib.metadata
import json
import resource
import shutil
import time
import traceback
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import structural_holdout_map_pilot as previous
import cross_visit_map as alg

old, plane = previous.old, previous.alg
read, save, sha, utc = previous.read, previous.save, previous.sha, previous.utc
BASE = old.MAIN/'docs/maintenance/2026-10-09/cross-visit-map-pilot-01'
AUDIT = previous.BASE/'revisit-design-audit-01/attempt-02'
FIELDS = ('counts', 'means', 'seconds', 'keys')


def verify():
    frozen = read(BASE/'freeze.json')
    for path, digest in frozen['files'].items():
        assert sha(path) == digest, path
    for package, version in frozen['packages'].items():
        assert importlib.metadata.version(package) == version
    return frozen


def freeze():
    previous.verify()
    previous.check_delivery(previous.BASE)
    binding = read(AUDIT/'results.json')
    assert read(AUDIT/'validation.json')['passed'] and binding['original_accepted_index'] == 0
    assert binding['selected']['i'] == 2429 and binding['selected']['j'] == 3373
    assert not binding['raw_coordinate_payload_parsed']
    for row in binding['raw_bindings']:
        assert sha(row['path']) == row['sha256']
    sources = [Path(__file__), Path(__file__).with_name('validate_cross_visit_map_pilot.py'),
               BASE/'PROTOCOL.md', BASE/'algorithm_staging.py', old.SLAM/'scripts/cross_visit_map.py',
               old.SLAM/'scripts/shared_plane_map.py', old.SLAM/'scripts/measured_map_reoptimization.py',
               Path(previous.__file__), Path(old.__file__), Path(previous.prior.__file__),
               Path(__file__).with_name('validate_shared_plane_map_pilot.py')]
    assert sha(BASE/'algorithm_staging.py') == sha(old.SLAM/'scripts/cross_visit_map.py')
    snapshot = BASE/'source_snapshot'
    snapshot.mkdir()
    files = sources.copy()
    for i, source in enumerate(sources):
        target = snapshot/f'{i:02d}-{source.name}'
        shutil.copyfile(source, target)
        files.append(target)
    files += [previous.BASE/name for name in ('DELIVERY_SEAL.json', 'NEXT_ROUND_PLAN.md', 'STATUS.json')]
    files += [AUDIT/name for name in ('freeze.json', 'results.json', 'validation.json', 'output_seal.json')]
    files += [old.source('00')/name for name in ('keyframes.json', 'source_frames.json', 'odom_poses.txt', 'accepted_loops.json')]
    files += [old.DATA/'poses/00.txt', old.DATA/'sequences/00/calib.txt']
    files += [Path(r['path']) for r in binding['raw_bindings']]
    save(BASE/'freeze.json', dict(utc=utc(), files={str(p): sha(p) for p in files}, binding=binding,
         packages={p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
         new_numeric_gt_parsed=False, new_raw_coordinates_parsed=False,
         exposed_development=True, new_cpu_wall_cap_s=1800, rss_cap_bytes=2*2**30, artifact_cap_bytes=512*2**20))
    (BASE/'INCOMPLETE').write_text('CV1 requires preflight and complete bank/decision validation\n')
    print('CV1 frozen', len(files), 'entries', flush=True)


def preflight():
    verify()
    rng = np.random.default_rng(202610092429)
    truth = np.repeat(np.eye(4)[None], 6, axis=0)
    for i in range(1, 6):
        truth[i] = alg.retract(truth[i], np.r_[rng.normal(0, .04, 3), rng.normal(0, 1., 3)])
    world = []
    for axis in range(3):
        p = rng.uniform(-3, 3, (100, 3))
        p[:, axis] = axis-1.
        world.append(p)
    groups = [[(p-t[:3, 3])@t[:3, :3] for t in truth] for p in world]
    stats = previous.prior.stats_from_groups(groups)
    current = truth.copy()
    for i in range(1, 6):
        current[i] = alg.retract(current[i], rng.normal(0, .005, 6))
    hc, gc = plane.plane_system(stats, current)
    hd, gd = previous.prior.explicit_system(groups, current)
    hdelta, gdelta = float(np.max(abs(hc-hd))), float(np.max(abs(gc-gd)))
    assert hdelta < 1e-8 and gdelta < 1e-9
    fd = {}
    for arm in ('F', 'J'):
        gradient = alg.system(stats, truth, current, arm, 3)[1]
        maximum = 0.
        for axis in range(len(gradient)):
            delta = np.zeros(len(gradient))
            delta[axis] = 1e-6
            plus, minus = alg.move(current, delta, arm, 3), alg.move(current, -delta, arm, 3)
            numeric = (alg.cost(stats, truth, plus, arm, 3)[0]-alg.cost(stats, truth, minus, arm, 3)[0])/2e-6
            maximum = max(maximum, abs(numeric-gradient[axis]))
        assert maximum < 1e-4
        fd[arm] = maximum
    pairs = alg.edges(6, 3)
    assert pairs == [(1, 2), (2, 0), (3, 4), (4, 5)] and (0, 3) not in pairs
    separate = current.copy()
    for ids, d in ((range(3), [.1, .05, -.02, 2., 3., -1.]), (range(3, 6), [-.08, .04, .03, -3., 1., 2.])):
        gauge = alg.retract(np.eye(4), np.array(d))
        separate[list(ids)] = gauge@separate[list(ids)]
    chain_gauge = abs(alg.prior_cost(truth, separate, 3)-alg.prior_cost(truth, current, 3))
    assert chain_gauge < 1e-9
    global_gauge = alg.retract(np.eye(4), np.array([.2, -.1, .15, 5., -2., 3.]))
    common = abs(alg.cost(stats, global_gauge@truth, global_gauge@current, 'J', 3)[0]-alg.cost(stats, truth, current, 'J', 3)[0])
    assert common < 1e-9
    moved = alg.move(current, np.array([.03, -.02, .01, .3, -.1, .2]), 'F', 3)
    shape = alg.correction(current, moved, 3)
    assert shape['internal_translation_m'] < 1e-10 and shape['internal_rotation_deg'] < 1e-10
    exact_f, _, _ = alg.optimize(stats, truth, 'F', 3)
    exact_j, _, _ = alg.optimize(stats, truth, 'J', 3)
    noop = max(float(np.max(abs(exact_f-truth))), float(np.max(abs(exact_j-truth))))
    assert noop < 1e-8
    displaced = alg.move(truth, np.array([.004, -.002, .003, .04, -.03, .02]), 'F', 3)
    recovered, _, _ = alg.optimize(stats, displaced, 'F', 3)
    recovery = float(np.max(abs(recovered-truth)))
    assert recovery < 2e-5
    planar_groups = [[(world[2]-t[:3, 3])@t[:3, :3] for t in truth]]
    planar = previous.prior.stats_from_groups(planar_groups)
    shift = np.eye(4)
    shift[:3, 3] = [.2, -.1, 0.]
    blind = truth.copy()
    blind[3:] = shift@blind[3:]
    blind_cost = alg.cost(planar, truth, blind, 'F', 3)[0]
    blind_rank = int(np.linalg.matrix_rank(alg.system(planar, truth, blind, 'F', 3)[0], tol=1e-7))
    assert blind_cost < 1e-10 and blind_rank == 3
    save(BASE/'preflight.json', dict(passed=True, compact_hessian_delta=hdelta, compact_gradient_delta=gdelta,
         fixed_and_joint_gradient_fd=fd, separate_chain_gauge_delta=chain_gauge, common_gauge_delta=common,
         gap_edge_absent=True, fixed_shape_correction=shape, perfect_noop_delta=noop,
         rigid_three_plane_recovery_delta=recovery, planar_blind_cost=blind_cost, planar_blind_rank=blind_rank,
         new_numeric_gt_parsed=False, new_raw_coordinates_parsed=False))
    print('CV1 preflight passed', fd, recovery, flush=True)


def subset(stats, mask):
    return {name: stats[name][mask] for name in FIELDS}


def hash_split(keys):
    payloads = ['CV1|00|2429|3373|2|'+','.join(str(int(x)) for x in key) for key in keys]
    numbers = np.array([int.from_bytes(hashlib.sha256(s.encode('utf-8')).digest()[:4], 'big') for s in payloads], np.uint32)
    return numbers % 4 == 0, numbers


def describe(stats, poses):
    coverage = stats['counts'].sum(0).astype(int)
    normals = plane.fit_planes(stats, poses)[1][:, :, 0] if len(stats['counts']) else None
    return dict(patches=len(stats['counts']), per_scan_points=coverage.tolist(),
                per_visit_points=[int(coverage[:8].sum()), int(coverage[8:].sum())],
                per_visit_contributing_scans=[int(np.sum(coverage[:8] > 0)), int(np.sum(coverage[8:] > 0))],
                normal_scatter_eigenvalues=np.linalg.eigvalsh(normals.T@normals/len(normals)).tolist() if normals is not None else None)


def geometry(stats, poses):
    variance = np.maximum(plane.fit_planes(stats, poses)[0][:, 0], 0.)
    return dict(rms_m=float(np.sqrt(np.mean(variance))), per_patch_variance_m2=variance.tolist())


def bank():
    frozen = verify()
    assert read(BASE/'preflight.json')['passed']
    binding = frozen['binding']
    order = [7]+list(range(7))+list(range(8, 16))
    rows = [binding['raw_bindings'][i] for i in order]
    frames = np.array([r['raw_frame'] for r in rows], np.int64)
    nodes = np.array([r['node'] for r in rows], np.int64)
    points = [old.process('00', int(frame)) for frame in frames]
    native = old.poses(old.source('00')/'odom_poses.txt')[nodes]
    proper = np.array([old.alg.proper(t) for t in native])
    native_z = np.array(binding['selected']['T_rel'], float)
    z = old.alg.proper(native_z)
    o = alg.inverse(proper[0])@proper
    o[0] = np.eye(4)
    initial = o.copy()
    local_b = alg.inverse(proper[-1])@proper[8:]
    initial[8:] = z@local_b
    initial[-1] = z
    full, info = plane.features(points, initial, 2.)
    cross = (full['counts'][:, :8].sum(1) > 0)&(full['counts'][:, 8:].sum(1) > 0)
    stats = subset(full, cross)
    remap = np.full(len(cross), -1, np.int64)
    remap[cross] = np.arange(np.sum(cross))
    labels = []
    for label in full['labels']:
        output = np.full(len(label), -1, np.int64)
        good = label >= 0
        output[good] = remap[label[good]]
        labels.append(output)
    held, integers = hash_split(stats['keys'])
    train, test = subset(stats, ~held), subset(stats, held)
    train_info, test_info = describe(train, initial), describe(test, initial)
    supported = bool(train_info['patches'] >= 10 and min(train_info['per_visit_contributing_scans']) >= 3 and
                     min(train_info['per_visit_points']) >= 100 and test_info['patches'] >= 5)
    arrays = {name: stats[name] for name in FIELDS}
    arrays.update({f'points_{i}': p for i, p in enumerate(points)})
    arrays.update({f'label_{i}': label for i, label in enumerate(labels)})
    arrays.update(O=o, B=initial, native_absolute=native, proper_absolute=proper, native_Z=native_z, Z=z,
                  frames=frames, nodes=nodes, holdout=held, hash_integers=integers)
    summary = dict(supported=supported, original_measurement_id=binding['selected']['measurement_id'],
                   full_eligible=info, cross_visit_patches=int(cross.sum()), train=train_info, holdout=test_info,
                   retained_point_counts=list(map(len, points)), projection_max_delta=float(np.max(abs(native-proper))),
                   z_projection_max_delta=float(np.max(abs(native_z-z))), edges=alg.edges(16),
                   traces={}, corrections={}, geometry={}, costs={})
    if supported:
        for arm in ('F', 'J'):
            arrays[arm], summary['traces'][arm], summary['corrections'][arm] = alg.optimize(train, initial, arm)
        for arm in ('O', 'B', 'F', 'J'):
            pose = arrays[arm]
            summary['geometry'][arm] = dict(train=geometry(train, pose), holdout=geometry(test, pose))
            summary['costs'][arm] = alg.cost(train, initial, pose, 'J')[1]
    root = BASE/'bank'
    root.mkdir()
    np.savez(root/'case.npz', **arrays)
    save(root/'summary.json', summary)
    save(BASE/'bank_seal.json', dict(utc=utc(), freeze_sha256=sha(BASE/'freeze.json'),
         new_numeric_gt_parsed=False, files={p.name: sha(p) for p in root.iterdir()}))
    verify()
    print('CV1 bank', supported, train_info, test_info, summary['corrections'], flush=True)


def metrics(truth, poses):
    reference = np.linalg.inv(truth[0])@truth
    error = np.linalg.inv(reference[-1])@poses[-1]
    result = dict(joint_aligned_ate_m=old.errors(truth, poses)['aligned_position_ate_m'],
                  endpoint_translation_m=float(np.linalg.norm(error[:3, 3])),
                  endpoint_rotation_deg=float(Rotation.from_matrix(old.alg.proper(error)[:3, :3]).magnitude()*180/np.pi), visits={})
    for name, ids in (('A', [0]+list(range(1, 8))), ('B', [15]+list(range(8, 15)))):
        local = alg.inverse(poses[ids[0]])@poses[ids]
        result['visits'][name] = old.errors(truth[ids], local)
    return result


def comparison(candidate, baseline, holdout_ratio, valid):
    denominator_names = ('joint_aligned_ate_m', 'endpoint_translation_m')
    denominators_ok = all(baseline[k] > 0 for k in denominator_names) and all(
        baseline['visits'][v][k] > 0 for v in ('A', 'B') for k in ('aligned_position_ate_m', 'relative_translation_rmse_m'))
    if not denominators_ok:
        return dict(valid=bool(valid), denominators_positive=False, eligible=False)
    gain_ate = 1-candidate['joint_aligned_ate_m']/baseline['joint_aligned_ate_m']
    gain_t = 1-candidate['endpoint_translation_m']/baseline['endpoint_translation_m']
    rotation = candidate['endpoint_rotation_deg']-baseline['endpoint_rotation_deg']
    visits = {}
    for name in ('A', 'B'):
        c, b = candidate['visits'][name], baseline['visits'][name]
        visits[name] = dict(ate_gain=1-c['aligned_position_ate_m']/b['aligned_position_ate_m'],
                           translation_gain=1-c['relative_translation_rmse_m']/b['relative_translation_rmse_m'],
                           rotation_regression_deg=c['relative_rotation_mean_deg']-b['relative_rotation_mean_deg'])
    visit_safety = all(v['ate_gain'] >= -.05 and v['translation_gain'] >= -.05 and v['rotation_regression_deg'] <= .02 for v in visits.values())
    eligible = bool(valid and gain_ate >= .05 and gain_t >= .05 and rotation <= .01 and visit_safety and holdout_ratio <= 1.01)
    return dict(valid=bool(valid), denominators_positive=True, joint_ate_gain=gain_ate, endpoint_translation_gain=gain_t,
                endpoint_rotation_regression_deg=rotation, visit_changes=visits, visit_safety=visit_safety,
                holdout_rms_ratio=float(holdout_ratio), holdout_safety=bool(holdout_ratio <= 1.01), eligible=eligible)


def evaluate():
    verify()
    assert read(BASE/'bank_validation.json')['passed']
    summary = read(BASE/'bank/summary.json')
    assert summary['supported'], 'Unsupported case stops before new reference outcomes'
    for name, digest in read(BASE/'bank_seal.json')['files'].items():
        assert sha(BASE/'bank'/name) == digest
    z = np.load(BASE/'bank/case.npz', allow_pickle=False)
    truth = old.gt('00')[z['frames']]
    rows = {arm: metrics(truth, z[arm]) for arm in ('O', 'B', 'F', 'J')}
    comparisons = {}
    for candidate, baseline in (('F', 'B'), ('J', 'B'), ('J', 'F')):
        ratio = summary['geometry'][candidate]['holdout']['rms_m']/summary['geometry'][baseline]['holdout']['rms_m']
        valid = summary['corrections'][candidate]['valid'] and (baseline == 'B' or summary['corrections'][baseline]['valid'])
        comparisons[candidate+'vs'+baseline] = comparison(rows[candidate], rows[baseline], ratio, valid)
    save(BASE/'results.json', dict(utc=utc(), rows=rows, comparisons=comparisons,
         bank_seal_sha256=sha(BASE/'bank_seal.json'), full_trajectory=False, independent_generalization=False))
    print('CV1 outcomes', {a: [r['joint_aligned_ate_m'], r['endpoint_translation_m'], r['endpoint_rotation_deg']] for a, r in rows.items()}, flush=True)
    print('CV1 comparisons', comparisons, flush=True)


def record_stage(name, callback):
    start, failure = time.perf_counter(), None
    try:
        callback()
    except Exception as error:
        failure = repr(error)
        target = BASE/f'FAILURE_{name}.json'
        if not target.exists():
            save(target, dict(error=failure, traceback=traceback.format_exc()))
        raise
    finally:
        rows = read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        rows.append(dict(stage=name, utc=utc(), wall_s=time.perf_counter()-start, peak_rss_bytes=rss, passed=failure is None))
        (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows, indent=2)+'\n')
        assert sum(r['wall_s'] for r in rows) <= 1800 and rss <= 2*2**30
        assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()) <= 512*2**20


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('freeze', 'preflight', 'bank', 'evaluate'))
    name = parser.parse_args().stage
    record_stage(name, globals()[name])
