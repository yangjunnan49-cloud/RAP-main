"""Source-bound CPU stages for the MMR0 joint measured-map exploration."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import importlib.metadata
import json
import resource
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

MAIN = Path(__file__).resolve().parents[2]
SLAM = MAIN.parent/'RAP-SLAM'
ROOT_BASE = MAIN/'docs/maintenance/2026-10-09/measured-map-reoptimization-01'
BASE = ROOT_BASE/'attempt-02'
DATA = MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path.insert(0, str(SLAM/'scripts'))
import measured_map_reoptimization as alg

WINDOWS = [('00', 200), ('00', 800), ('05', 200), ('06', 200)]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def source(seq):
    return MAIN/f'docs/maintenance/2026-09-26/e0-frontend-01/full-{seq}-A'


def rawpath(seq, frame):
    return DATA/f'sequences/{seq}/velodyne/{frame:06d}.bin'


def frames(seq, boundary):
    selected = [int(k) for k in read(source(seq)/'keyframes.json') if k <= boundary][-8:]
    assert len(selected) == 8
    return selected


def poses(path):
    rows = np.loadtxt(path).reshape(-1, 3, 4)
    result = np.tile(np.eye(4), (len(rows), 1, 1))
    result[:, :3] = rows
    return result


def process(seq, frame):
    cloud = np.fromfile(rawpath(seq, frame), dtype=np.float32).reshape(-1, 4)[:, :3].astype(float)
    assert np.isfinite(cloud).all()
    ranges = np.linalg.norm(cloud, axis=1)
    cloud = cloud[(ranges >= 1.5) & (ranges <= 80.)]
    angle = np.deg2rad(.205)
    x, y, z = cloud.T
    rho = np.hypot(x, y)
    safe = rho > 1e-6
    corrected = cloud.copy()
    corrected[safe, 0] = x[safe]*np.cos(angle)-x[safe]*z[safe]/rho[safe]*np.sin(angle)
    corrected[safe, 1] = y[safe]*np.cos(angle)-y[safe]*z[safe]/rho[safe]*np.sin(angle)
    corrected[safe, 2] = z[safe]*np.cos(angle)+rho[safe]*np.sin(angle)
    _, indices = np.unique(np.floor(corrected/.5).astype(np.int64), axis=0, return_index=True)
    result = corrected[indices]
    if len(result) > 6000:
        result = result[np.linspace(0, len(result)-1, 6000, dtype=np.int64)]
    assert len(result) >= 200
    return result


def verify():
    frozen = read(BASE/'freeze.json')
    for path, digest in frozen['files'].items():
        assert sha(path) == digest, path
    for package, version in frozen['packages'].items():
        assert importlib.metadata.version(package) == version
    return frozen


def freeze():
    files = [ROOT_BASE/name for name in ('PROTOCOL.md', 'OWNER_SCOPE.md', 'algorithm_staging.py',
             'AMENDMENT_01.md', 'freeze.json', 'preflight.json', 'FAILURE_bank.json', 'RESOURCE_LOG.json')]
    files += [Path(__file__), Path(__file__).with_name('validate_measured_map_exploration_attempt02.py'),
             Path(__file__).with_name('measured_map_exploration.py'),
             Path(__file__).with_name('validate_measured_map_exploration.py'),
             SLAM/'scripts/measured_map_reoptimization.py', SLAM/'rap_slam/real_dataset.py']
    selected = {}
    for seq, boundary in WINDOWS:
        selected[f'{seq}-{boundary}'] = frames(seq, boundary)
    for seq in ('00', '05', '06'):
        files += [source(seq)/name for name in ('odom_poses.txt', 'keyframes.json', 'source_frames.json')]
        files += [DATA/f'poses/{seq}.txt', DATA/f'sequences/{seq}/calib.txt']
    files += [rawpath(seq, frame) for seq, boundary in WINDOWS for frame in selected[f'{seq}-{boundary}']]
    assert selected == read(ROOT_BASE/'freeze.json')['selected']
    assert sha(ROOT_BASE/'algorithm_staging.py') == sha(SLAM/'scripts/measured_map_reoptimization.py')
    save(BASE/'freeze.json', dict(utc=utc(), selected=selected,
         files={str(path): sha(path) for path in sorted(set(files))},
         packages={p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
         numeric_gt_parsed=False))
    (BASE/'INCOMPLETE').write_text('MMR0 geometry and evaluation validation pending\n')
    print('MMR0 frozen', selected, flush=True)


def preflight():
    verify()
    rng = np.random.default_rng(20261009)
    points = [rng.normal(size=(60, 3))*3 for _ in range(2)]
    normal = [rng.normal(size=(60, 3)) for _ in range(2)]
    normal = [n/np.linalg.norm(n, axis=1)[:, None] for n in normal]
    trial = np.tile(np.eye(4), (2, 1, 1))
    for p in trial:
        p[:3, :3] = Rotation.from_rotvec(rng.normal(size=3)*.3).as_matrix()
        p[:3, 3] = rng.normal(size=3)
    match = (0, 1, np.arange(60), np.arange(60))
    residual, ja, jb = alg.residual_jacobian(points, normal, trial, match)
    fd_max = 0.
    for node, expected in ((0, ja), (1, jb)):
        for axis in range(6):
            delta = np.zeros(6)
            delta[axis] = 1e-6
            plus, minus = trial.copy(), trial.copy()
            plus[node], minus[node] = alg.retract(trial[node], delta), alg.retract(trial[node], -delta)
            actual = (alg.residual_jacobian(points, normal, plus, match)[0]-alg.residual_jacobian(points, normal, minus, match)[0])/2e-6
            fd_max = max(fd_max, float(np.max(np.abs(actual-expected[:, axis]))))
    assert fd_max < 1e-7
    gauge = alg.retract(np.eye(4), np.array([.2, -.1, .1, 3., 4., -2.]))
    gauge_delta = float(np.max(np.abs(alg.residual_jacobian(points, normal, gauge@trial, match)[0]-residual)))
    assert gauge_delta < 1e-12
    world = rng.uniform(-4, 4, size=(600, 3))
    world_normal = np.zeros_like(world)
    for face in range(3):
        indices = np.arange(face*200, (face+1)*200)
        world[indices, face] = face-1.
        world_normal[indices, face] = 1.
    truth = np.tile(np.eye(4), (3, 1, 1))
    truth[1] = alg.retract(truth[1], np.array([.1, -.05, .02, 1., .3, -.1]))
    truth[2] = alg.retract(truth[2], np.array([-.05, .03, .08, 2., -.2, .2]))
    measured = [(world-p[:3, 3])@p[:3, :3] for p in truth]
    normals = [world_normal@p[:3, :3] for p in truth]
    valid = [np.ones(600, bool) for _ in truth]
    matches = [(a, b, np.arange(600), np.arange(600)) for a, b in alg.edge_list(3)]
    exact, _, _ = alg.optimize(measured, normals, valid, truth, False, matches)
    noop_delta = float(np.max(np.abs(exact-truth)))
    assert noop_delta < 1e-10
    initial = truth.copy()
    for node in (1, 2):
        initial[node] = alg.retract(initial[node], np.array([.003, -.002, .002, .06, -.04, .02])*node)
    recovered, _, _ = alg.optimize(measured, normals, valid, initial, False, matches)
    recovery_delta = float(np.max(np.abs(recovered-truth)))
    assert recovery_delta < 1e-6
    plane = world.copy()
    plane[:, 2] = 0.
    plane_n = np.tile([0., 0., 1.], (600, 1))
    blind = np.tile(np.eye(4), (2, 1, 1))
    blind[1, :3, 3] = [.2, -.1, 0.]
    blind_matches = [(0, 1, np.arange(600), np.arange(600)), (1, 0, np.arange(600), np.arange(600))]
    blind_cost = alg.cost([plane, plane], [plane_n, plane_n], blind, blind_matches)
    h, _ = alg.system([plane, plane], [plane_n, plane_n], blind, blind_matches)
    blind_rank = int(np.linalg.matrix_rank(h, tol=1e-8))
    assert blind_cost < 1e-15 and blind_rank == 3
    save(BASE/'preflight.json', dict(passed=True, jacobian_fd_max=fd_max, gauge_residual_delta=gauge_delta,
         perfect_noop_delta=noop_delta, known_correspondence_recovery_delta=recovery_delta,
         planar_wrong_translation_m=float(np.linalg.norm(blind[1, :3, 3])),
         planar_wrong_cost=blind_cost, planar_rank=blind_rank, real_gt_read=False))
    print('MMR0 preflight passed', fd_max, recovery_delta, flush=True)


def bank():
    verify()
    assert read(BASE/'preflight.json')['passed']
    root = BASE/'bank'
    root.mkdir()
    summary = {}
    for seq, boundary in WINDOWS:
        key = f'{seq}-{boundary}'
        ids = frames(seq, boundary)
        native = poses(source(seq)/'odom_poses.txt')[ids]
        absolute = np.array([alg.proper(t) for t in native])
        change = float(np.max(np.abs(native-absolute)))
        assert change < 1e-5
        initial = alg.inverse(absolute[0])@absolute
        initial[0] = np.eye(4)
        clouds = [process(seq, frame) for frame in ids]
        n_valid = [alg.normals(p) for p in clouds]
        n = [x[0] for x in n_valid]
        v = [x[1] for x in n_valid]
        p_opt, p_probe = [p[::2] for p in clouds], [p[1::2] for p in clouds]
        nn, vv = [p[::2] for p in n], [p[::2] for p in v]
        outputs = {'O': initial}
        traces, corrections = {}, {}
        for arm, refresh in (('F', False), ('R', True)):
            outputs[arm], traces[arm], corrections[arm] = alg.optimize(p_opt, nn, vv, initial, refresh)
        arrays = {f'{label}_{i}': a for label, values in (('points', clouds), ('normals', n), ('valid', v))
                  for i, a in enumerate(values)}
        np.savez(root/f'{key}.npz', **arrays, initial=initial,
                 native_absolute=native, proper_absolute=absolute, frames=np.array(ids),
                 **{arm: pose for arm, pose in outputs.items()})
        probes = {arm: alg.probe(p_probe, pose) for arm, pose in outputs.items()}
        summary[key] = dict(seq=seq, boundary=boundary, frames=ids, proper_rotation_change=change,
                            probes=probes, traces=traces, corrections=corrections,
                            point_counts=[len(p) for p in clouds], valid_normal_counts=[int(x.sum()) for x in v])
        print('MMR0 bank', key, {arm: probes[arm]['mean_nn_m'] for arm in outputs}, corrections, flush=True)
    save(root/'summary.json', summary)
    save(BASE/'bank_seal.json', dict(utc=utc(), numeric_gt_parsed=False, freeze_sha256=sha(BASE/'freeze.json'),
         files={str(p.relative_to(root)): sha(p) for p in root.iterdir()}))
    verify()


def gt(seq):
    result = poses(DATA/f'poses/{seq}.txt')
    calibration = DATA/f'sequences/{seq}/calib.txt'
    for line in calibration.read_text().splitlines():
        if line.startswith('Tr:'):
            tr = np.eye(4)
            tr[:3] = np.array([float(x) for x in line.split(':', 1)[1].split()]).reshape(3, 4)
            return np.linalg.inv(tr)@result@tr
    raise ValueError('Missing Tr calibration')


def errors(truth, predicted):
    reference = np.linalg.inv(truth[0])@truth
    delta = np.linalg.inv(reference)@predicted
    translation = np.linalg.norm(delta[:, :3, 3], axis=1)
    rotation = np.array([Rotation.from_matrix(alg.proper(t)[:3, :3]).magnitude()*180/np.pi for t in delta])
    x, y = predicted[:, :3, 3], reference[:, :3, 3]
    cx, cy = x.mean(0), y.mean(0)
    u, _, vh = np.linalg.svd((x-cx).T@(y-cy))
    r = vh.T@np.diag([1., 1., np.linalg.det(vh.T@u.T)])@u.T
    aligned = (x-cx)@r.T+cy-y
    return dict(relative_translation_rmse_m=float(np.sqrt(np.mean(translation[1:]**2))),
                relative_rotation_mean_deg=float(rotation[1:].mean()), relative_rotation_max_deg=float(rotation.max()),
                aligned_position_ate_m=float(np.sqrt(np.mean(np.sum(aligned**2, axis=1)))),
                per_node_translation_m=translation.tolist(), per_node_rotation_deg=rotation.tolist())


def evaluate():
    verify()
    assert read(BASE/'bank_validation.json')['passed']
    root = BASE/'bank'
    seal = read(BASE/'bank_seal.json')
    for path, digest in seal['files'].items():
        assert sha(root/path) == digest
    rows = {}
    summary = read(root/'summary.json')
    for seq, boundary in WINDOWS:
        key = f'{seq}-{boundary}'
        z = np.load(root/f'{key}.npz', allow_pickle=False)
        truth = gt(seq)[z['frames']]
        row = {arm: errors(truth, z[arm]) for arm in ('O', 'F', 'R')}
        for arm in ('F', 'R'):
            baseline, current = row['O'], row[arm]
            current['translation_improvement_fraction'] = 1-current['relative_translation_rmse_m']/baseline['relative_translation_rmse_m']
            current['local_pose_signal'] = bool(current['translation_improvement_fraction'] >= .05 and current['relative_rotation_mean_deg'] <= baseline['relative_rotation_mean_deg'])
            current['probe_improvement_fraction'] = 1-summary[key]['probes'][arm]['mean_nn_m']/summary[key]['probes']['O']['mean_nn_m']
            current['probe_signal'] = bool(current['probe_improvement_fraction'] >= .05)
        rows[key] = row
        print('MMR0 local evaluation', key, {arm: [row[arm]['relative_translation_rmse_m'], row[arm]['relative_rotation_mean_deg']] for arm in row}, flush=True)
    save(BASE/'results.json', dict(utc=utc(), bank_seal_sha256=sha(BASE/'bank_seal.json'), rows=rows,
         signals={arm: dict(local_pose=sum(r[arm]['local_pose_signal'] for r in rows.values()),
                           probe=sum(r[arm]['probe_signal'] for r in rows.values())) for arm in ('F', 'R')},
         full_system_metrics_computed=False))


def run_stage(stage):
    start = time.perf_counter()
    previous = read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
    failed = None
    try:
        globals()[stage]()
    except Exception as error:
        failed = repr(error)
        path = BASE/f'FAILURE_{stage}.json'
        if not path.exists():
            save(path, dict(utc=utc(), error=failed, traceback=traceback.format_exc()))
        raise
    finally:
        wall = time.perf_counter()-start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        previous.append(dict(stage=stage, utc=utc(), wall_s=wall, peak_rss_bytes=rss, passed=failed is None))
        log = BASE/'RESOURCE_LOG.json'
        log.write_text(json.dumps(previous, indent=2, allow_nan=False)+'\n')
        artifacts = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
        old = read(ROOT_BASE/'RESOURCE_LOG.json')
        total_artifacts = sum(p.stat().st_size for p in ROOT_BASE.rglob('*') if p.is_file())
        assert sum(x['wall_s'] for x in previous+old) <= 1800 and rss <= 2*2**30 and total_artifacts <= 512*2**20


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('freeze', 'preflight', 'bank', 'evaluate'))
    run_stage(parser.parse_args().stage)
