"""Frozen small development pilot for shared map planes and motion constraints."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import importlib.metadata
import json
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import measured_map_exploration_attempt02 as old

BASE = old.MAIN/'docs/maintenance/2026-10-09/shared-plane-map-pilot-01'
SCALES = (2., 4.)
sys.path.insert(0, str(old.SLAM/'scripts'))
import shared_plane_map as alg
read, save, sha, utc = old.read, old.save, old.sha, old.utc


def verify():
    frozen = read(BASE/'freeze.json')
    for path, digest in frozen['files'].items():
        assert sha(path) == digest, path
    for p, v in frozen['packages'].items():
        assert importlib.metadata.version(p) == v
    return frozen


def freeze():
    old.verify()
    prior_seal = read(old.BASE/'bank_seal.json')
    for path, digest in prior_seal['files'].items():
        assert sha(old.BASE/'bank'/path) == digest
    assert read(old.BASE/'bank_validation.json')['passed'] and read(old.BASE/'validation.json')['passed']
    sources = [Path(__file__), Path(__file__).with_name('validate_shared_plane_map_pilot.py'),
               BASE/'PROTOCOL.md', BASE/'algorithm_staging.py',
               old.SLAM/'scripts/shared_plane_map.py', old.SLAM/'scripts/measured_map_reoptimization.py',
               Path(old.__file__)]
    snapshot = BASE/'source_snapshot'
    snapshot.mkdir()
    files = list(sources)
    for i, source in enumerate(sources):
        target = snapshot/f'{i:02d}-{source.name}'
        shutil.copyfile(source, target)
        files.append(target)
    files += [old.BASE/name for name in ('bank_seal.json', 'bank_validation.json', 'validation.json')]
    files += list((old.BASE/'bank').iterdir())
    files += [old.DATA/f'poses/{s}.txt' for s in ('00', '05', '06')]
    files += [old.DATA/f'sequences/{s}/calib.txt' for s in ('00', '05', '06')]
    assert sha(BASE/'algorithm_staging.py') == sha(old.SLAM/'scripts/shared_plane_map.py')
    save(BASE/'freeze.json', dict(utc=utc(), files={str(p): sha(p) for p in files},
         packages={p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
         scales=SCALES, windows=old.WINDOWS, previously_exposed_development=True, new_numeric_gt_parsed=False))
    (BASE/'INCOMPLETE').write_text('Shared-plane map pilot requires full-bank and accuracy validation\n')
    print('SMP1 frozen', len(files), 'source/input entries', flush=True)


def stats_from_groups(groups):
    count = np.array([[len(p) for p in row] for row in groups])
    means = np.array([[p.mean(0) for p in row] for row in groups])
    seconds = np.array([[p.T@p/len(p) for p in row] for row in groups])
    return dict(counts=count, means=means, seconds=seconds)


def explicit_system(groups, poses):
    stats = stats_from_groups(groups)
    values, vectors, center, _, _ = alg.fit_planes(stats, poses)
    dimension = 6*(len(poses)-1)
    h, g = np.zeros((dimension, dimension)), np.zeros(dimension)
    for k, group in enumerate(groups):
        normal, tangent = vectors[k, :, 0], vectors[k, :, 1:3]
        hx, hf, hff = np.zeros_like(h), np.zeros((dimension, 3)), np.zeros((3, 3))
        gx, gf = np.zeros(dimension), np.zeros(3)
        for i, p in enumerate(group):
            x = p@poses[i, :3, :3].T+poses[i, :3, 3]
            r = (x-center[k])@normal
            jf = np.c_[(x-center[k])@tangent, np.ones(len(p))]
            weight = 1/(len(groups)*len(group)*len(p)*alg.GEOMETRY_SIGMA**2)
            hff += weight*jf.T@jf
            gf += weight*jf.T@r
            if i:
                nb = poses[i, :3, :3].T@normal
                j = np.c_[np.cross(p, nb), np.tile(nb, (len(p), 1))]
                block = slice(6*(i-1), 6*i)
                hx[block, block] += weight*j.T@j
                hf[block] += weight*j.T@jf
                gx[block] += weight*j.T@r
        h += hx-hf@np.linalg.solve(hff, hf.T)
        g += gx-hf@np.linalg.solve(hff, gf)
    return h, g


def preflight():
    verify()
    rng = np.random.default_rng(2026100902)
    world = []
    for axis in range(3):
        p = rng.uniform(-3, 3, size=(160, 3))
        p[:, axis] = axis-1.
        world.append(p)
    truth = np.tile(np.eye(4), (3, 1, 1))
    truth[1] = alg.retract(truth[1], np.array([.1, -.04, .02, 1., .3, -.1]))
    truth[2] = alg.retract(truth[2], np.array([-.05, .03, .08, 2., -.2, .2]))
    groups = [[(p-t[:3, 3])@t[:3, :3] for t in truth] for p in world]
    stats = stats_from_groups(groups)
    current = truth.copy()
    for i in (1, 2):
        current[i] = alg.retract(current[i], np.array([.003, -.002, .001, .04, -.03, .02])*i)
    h, g = alg.plane_system(stats, current)
    hx, gx = explicit_system(groups, current)
    moment_h = float(np.max(abs(h-hx)))
    moment_g = float(np.max(abs(g-gx)))
    assert moment_h < 1e-8 and moment_g < 1e-9
    fd = {}
    for prior in (False, True):
        gradient = g.copy()
        if prior:
            gradient += alg.prior_system(truth, current)[1]
        maximum = 0.
        for node in (1, 2):
            for axis in range(6):
                delta = np.zeros(6)
                delta[axis] = 1e-6
                plus, minus = current.copy(), current.copy()
                plus[node], minus[node] = alg.retract(current[node], delta), alg.retract(current[node], -delta)
                actual = (alg.cost(stats, plus, truth, prior)[0]-alg.cost(stats, minus, truth, prior)[0])/2e-6
                maximum = max(maximum, abs(actual-gradient[6*(node-1)+axis]))
        assert maximum < 1e-5
        fd[str(prior)] = maximum
    prior_fd = 0.
    _, ja, jb = alg.prior_edge(truth, current, 1, 2)
    for node, jac in ((1, ja), (2, jb)):
        for axis in range(6):
            delta = np.zeros(6)
            delta[axis] = 1e-7
            plus, minus = current.copy(), current.copy()
            plus[node], minus[node] = alg.retract(current[node], delta), alg.retract(current[node], -delta)
            actual = (alg.prior_edge(truth, plus, 1, 2)[0]-alg.prior_edge(truth, minus, 1, 2)[0])/2e-7
            prior_fd = max(prior_fd, float(np.max(abs(actual-jac[:, axis]))))
    assert prior_fd < 1e-6
    gauge = alg.retract(np.eye(4), np.array([.2, -.1, .1, 3., -2., 4.]))
    gauge_delta = abs(alg.cost(stats, gauge@current, gauge@truth, True)[0]-alg.cost(stats, current, truth, True)[0])
    assert gauge_delta < 1e-9
    exact, _, _ = alg.optimize(stats, truth, False)
    recovered, _, _ = alg.optimize(stats, truth, False, current)
    no_op = float(np.max(abs(exact-truth)))
    recovery = float(np.max(abs(recovered-truth)))
    assert no_op < 1e-10 and recovery < 2e-5
    planar = stats_from_groups([[world[2], world[2]]])
    blind = np.tile(np.eye(4), (2, 1, 1))
    blind[1, :3, 3] = [.2, -.1, 0.]
    blind_cost = alg.cost(planar, blind, blind, False)[0]
    blind_rank = int(np.linalg.matrix_rank(alg.plane_system(planar, blind)[0], tol=1e-7))
    assert blind_cost < 1e-12 and blind_rank == 3
    save(BASE/'preflight.json', dict(passed=True, compact_hessian_delta=moment_h, compact_gradient_delta=moment_g,
         geometry_and_prior_gradient_fd=fd, prior_edge_jacobian_fd=prior_fd, common_gauge_delta=gauge_delta,
         perfect_noop_delta=no_op, three_plane_recovery_delta=recovery, planar_blind_cost=blind_cost,
         planar_blind_rank=blind_rank, new_numeric_gt_parsed=False))
    print('SMP1 preflight passed', fd, prior_fd, recovery, flush=True)


def bank():
    verify()
    assert read(BASE/'preflight.json')['passed']
    root = BASE/'bank'
    root.mkdir()
    summary = {}
    for seq, boundary in old.WINDOWS:
        window = f'{seq}-{boundary}'
        z = np.load(old.BASE/f'bank/{window}.npz', allow_pickle=False)
        initial = z['O']
        opt = [z[f'points_{i}'][::2] for i in range(8)]
        odd = [z[f'points_{i}'][1::2] for i in range(8)]
        for scale in SCALES:
            key = f'{window}-s{int(scale)}'
            stats, info = alg.features(opt, initial, scale)
            arrays = {name: stats[name] for name in ('counts', 'means', 'seconds', 'keys')}
            arrays.update({f'label_{i}': x for i, x in enumerate(stats['labels'])})
            outputs = dict(O=initial)
            row = dict(window=window, scale=scale, features=info, traces={}, corrections={}, probes={}, costs={})
            if info['representation_valid']:
                labels = alg.probe_labels(odd, initial, stats, scale)
                arrays.update({f'probe_label_{i}': x for i, x in enumerate(labels)})
                for arm, prior in (('G', False), ('P', True)):
                    outputs[arm], row['traces'][arm], row['corrections'][arm] = alg.optimize(stats, initial, prior)
                for arm, pose in outputs.items():
                    row['probes'][arm] = alg.probe(odd, labels, stats, pose)
                    row['costs'][arm] = dict(geometry=alg.cost(stats, pose, initial, False)[0],
                                             combined=alg.cost(stats, pose, initial, True)[0])
            np.savez(root/f'{key}.npz', **arrays, **outputs, frames=z['frames'])
            summary[key] = row
            print('SMP1 bank', key, info, row['corrections'], flush=True)
    save(root/'summary.json', summary)
    save(BASE/'bank_seal.json', dict(utc=utc(), freeze_sha256=sha(BASE/'freeze.json'),
         new_numeric_gt_parsed=False, files={p.name: sha(p) for p in root.iterdir()}))
    verify()


def stats_read(z):
    return {key: z[key] for key in ('counts', 'means', 'seconds', 'keys')}


def evaluate():
    verify()
    assert read(BASE/'bank_validation.json')['passed']
    seal = read(BASE/'bank_seal.json')
    for p, digest in seal['files'].items():
        assert sha(BASE/'bank'/p) == digest
    summary = read(BASE/'bank/summary.json')
    rows = {}
    for key, data in summary.items():
        z = np.load(BASE/f'bank/{key}.npz', allow_pickle=False)
        seq = data['window'].split('-')[0]
        truth = old.gt(seq)[z['frames']]
        row = dict(O=old.errors(truth, z['O']), scale=data['scale'], window=data['window'], arms={})
        if data['features']['representation_valid']:
            stats = stats_read(z)
            reference = np.array([old.alg.proper(t) for t in np.linalg.inv(truth[0])@truth])
            reference[0] = np.eye(4)
            row['reference_geometry_cost'] = alg.cost(stats, reference, z['O'], False)[0]
            for arm in ('G', 'P'):
                metrics = old.errors(truth, z[arm])
                metrics.update(valid=data['corrections'][arm]['valid'],
                    aligned_ate_gain=1-metrics['aligned_position_ate_m']/row['O']['aligned_position_ate_m'],
                    translation_gain=1-metrics['relative_translation_rmse_m']/row['O']['relative_translation_rmse_m'],
                    rotation_regression_deg=metrics['relative_rotation_mean_deg']-row['O']['relative_rotation_mean_deg'])
                row['arms'][arm] = metrics
        rows[key] = row
        print('SMP1 evaluation', key, {a: [m['aligned_ate_gain'], m['translation_gain'], m['rotation_regression_deg']] for a, m in row['arms'].items()}, flush=True)
    gates = {}
    for scale in SCALES:
        selected = [r for r in rows.values() if r['scale'] == scale]
        gate = {'all_valid': all('P' in r['arms'] and r['arms']['P']['valid'] for r in selected)}
        if gate['all_valid']:
            p = [r['arms']['P'] for r in selected]
            gate.update(ate_improved_windows=sum(m['aligned_ate_gain'] > 0 for m in p),
                        mean_fractional_ate_gain=float(np.mean([m['aligned_ate_gain'] for m in p])),
                        ate_safety=all(m['aligned_ate_gain'] >= -.05 for m in p),
                        translation_safety=all(m['translation_gain'] >= -.05 for m in p),
                        rotation_safety=all(m['rotation_regression_deg'] <= .02 for m in p))
            keys = [k for k, r in rows.items() if r['scale'] == scale]
            ratio = np.mean([summary[k]['probes']['P']['odd_point_rms_m'] for k in keys])/np.mean([summary[k]['probes']['O']['odd_point_rms_m'] for k in keys])
            gate.update(mean_odd_rms_ratio=float(ratio), odd_safety=bool(ratio <= 1.01))
            gate['eligible'] = bool(gate['ate_improved_windows'] >= 3 and gate['mean_fractional_ate_gain'] >= .05 and
                                     gate['ate_safety'] and gate['translation_safety'] and gate['rotation_safety'] and gate['odd_safety'])
        else:
            gate['eligible'] = False
        gates[str(int(scale))] = gate
    chosen = next((scale for scale in SCALES if gates[str(int(scale))]['eligible']), None)
    save(BASE/'results.json', dict(utc=utc(), rows=rows, gates=gates, selected_for_revisit_design_scale=chosen,
         bank_seal_sha256=sha(BASE/'bank_seal.json'), full_sequence_metrics=False, independent_generalization=False))


def run_stage(stage):
    start = time.perf_counter()
    rows = read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
    failure = None
    try:
        globals()[stage]()
    except Exception as error:
        failure = repr(error)
        target = BASE/f'FAILURE_{stage}.json'
        if not target.exists():
            save(target, dict(error=failure, traceback=traceback.format_exc()))
        raise
    finally:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        rows.append(dict(stage=stage, utc=utc(), wall_s=time.perf_counter()-start, peak_rss_bytes=rss, passed=failure is None))
        (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows, indent=2)+'\n')
        artifacts = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
        assert sum(r['wall_s'] for r in rows) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('freeze', 'preflight', 'bank', 'evaluate'))
    run_stage(parser.parse_args().stage)
