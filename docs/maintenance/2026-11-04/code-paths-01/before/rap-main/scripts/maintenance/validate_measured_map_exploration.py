"""Bounded MMR0 source/geometry/metric checks; no optimizer replay."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import json
import resource
import time
import traceback
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import measured_map_exploration as run


def world_residual(points, normal, poses, match):
    a, b, ia, ib = match
    target = points[a][ia]@poses[a, :3, :3].T+poses[a, :3, 3]
    source = points[b][ib]@poses[b, :3, :3].T+poses[b, :3, 3]
    normal_world = normal[a][ia]@poses[a, :3, :3].T
    return np.sum(normal_world*(source-target), axis=1)


def independent_scan(seq, frame):
    raw = np.fromfile(run.rawpath(seq, frame), dtype='<f4').reshape(-1, 4)[:, :3].astype(float)
    radius = np.sqrt(np.sum(raw*raw, axis=1))
    p = raw[(radius >= 1.5) & (radius <= 80.)]
    axes = np.cross(p, np.tile([0., 0., 1.], (len(p), 1)))
    length = np.linalg.norm(axes, axis=1)
    good = length > 1e-6
    rotvec = np.zeros_like(axes)
    rotvec[good] = axes[good]/length[good, None]*np.deg2rad(.205)
    corrected = Rotation.from_rotvec(rotvec).apply(p)
    first = {}
    for index, voxel in enumerate(np.floor(corrected/.5).astype(np.int64)):
        first.setdefault(tuple(voxel), index)
    representatives = corrected[[first[v] for v in sorted(first)]]
    if len(representatives) > 6000:
        representatives = representatives[np.linspace(0, len(representatives)-1, 6000, dtype=np.int64)]
    return representatives


def bank():
    run.verify()
    pre = run.read(run.BASE/'preflight.json')
    assert pre['passed'] and pre['planar_rank'] == 3 and pre['planar_wrong_translation_m'] > .2
    seal = run.read(run.BASE/'bank_seal.json')
    root = run.BASE/'bank'
    for name, digest in seal['files'].items():
        assert run.sha(root/name) == digest
    summary = run.read(root/'summary.json')
    max_residual = max_fd = max_scan = max_normal = max_probe = 0.
    verified_scans = set()
    for key, row in summary.items():
        z = np.load(root/f'{key}.npz', allow_pickle=False)
        assert list(z['frames']) == run.read(run.BASE/'freeze.json')['selected'][key]
        points, normal = z['points'][:, ::2], z['normals'][:, ::2]
        valid = z['valid'][:, ::2]
        for arm in ('O', 'F', 'R'):
            T = z[arm]
            assert np.max(abs(T[0]-np.eye(4))) < 1e-12
            assert np.max(abs(T[:, :3, :3].transpose(0, 2, 1)@T[:, :3, :3]-np.eye(3))) < 1e-10
            assert np.min(np.linalg.det(T[:, :3, :3])) > .999999999
            world_probe = np.einsum('npj,nij->npi', z['points'][:, 1::2], T[:, :3, :3])+T[:, None, :3, 3]
            trees = [cKDTree(p) for p in world_probe]
            pair_mean, pair_p95, pair_coverage = [], [], []
            for a in range(len(T)):
                for b in range(len(T)):
                    if 1 <= abs(a-b) <= 2:
                        distances, _ = trees[a].query(world_probe[b], k=1, workers=1)
                        pair_mean.append(float(distances.mean()))
                        pair_p95.append(float(np.quantile(distances, .95)))
                        pair_coverage.append(float(np.mean(distances < 1.)))
            computed = dict(mean_nn_m=np.mean(pair_mean), mean_pair_p95_m=np.mean(pair_p95),
                            mean_1m_coverage=np.mean(pair_coverage))
            for name, value in computed.items():
                max_probe = max(max_probe, abs(float(value)-row['probes'][arm][name]))
            max_probe = max(max_probe, float(np.max(abs(np.array(pair_mean)-row['probes'][arm]['pair_mean_nn_m']))))
            for match in run.alg.associations(points, normal, valid, T):
                native, ja, jb = run.alg.residual_jacobian(points, normal, T, match)
                alternate = world_residual(points, normal, T, match)
                max_residual = max(max_residual, float(np.max(abs(native-alternate))))
            match = run.alg.associations(points, normal, valid, T)[0]
            short = (match[0], match[1], match[2][:8], match[3][:8])
            _, ja, jb = run.alg.residual_jacobian(points, normal, T, short)
            for node, jac in ((short[0], ja), (short[1], jb)):
                for axis in range(6):
                    delta = np.zeros(6)
                    delta[axis] = 1e-6
                    plus, minus = T.copy(), T.copy()
                    plus[node] = run.alg.retract(T[node], delta)
                    minus[node] = run.alg.retract(T[node], -delta)
                    fd = (world_residual(points, normal, plus, short)-world_residual(points, normal, minus, short))/2e-6
                    max_fd = max(max_fd, float(np.max(abs(fd-jac[:, axis]))))
        for arm in ('F', 'R'):
            trace = row['traces'][arm]
            assert len(trace) == 24
            assert all(t['after'] <= t['before']+1e-13 for t in trace)
            assert all(min(t['counts']) >= 50 for t in trace)
        seq = row['seq']
        if seq not in verified_scans:
            reconstructed = independent_scan(seq, row['frames'][0])
            assert reconstructed.shape == z['points'][0].shape
            max_scan = max(max_scan, float(np.max(abs(reconstructed-z['points'][0]))))
            p = z['points'][0]
            for index in range(0, 32, 2):
                distances = np.sum((p-p[index])**2, axis=1)
                ids = np.argsort(distances, kind='stable')[:20]
                q = p[ids]-p[ids].mean(axis=0)
                values, vectors = np.linalg.eigh(q.T@q/20)
                n = vectors[:, 0]
                expected_valid = values[0]/max(values.sum(), 1e-15) < .05 and values[1] > 1e-6
                assert bool(z['valid'][0, index]) == expected_valid
                max_normal = max(max_normal, float(np.max(abs(np.outer(n, n)-np.outer(z['normals'][0, index], z['normals'][0, index])))))
            verified_scans.add(seq)
    assert max_residual < 1e-10 and max_fd < 1e-7 and max_scan < 1e-10 and max_normal < 1e-8 and max_probe < 1e-8
    run.save(run.BASE/'bank_validation.json', dict(passed=True, windows=len(summary),
             world_residual_max_delta=max_residual, real_jacobian_fd_max=max_fd,
             independent_scan_max_delta=max_scan, normal_projector_max_delta=max_normal,
             probe_world_coordinate_max_delta=max_probe,
             independently_reconstructed_raw_scans=len(verified_scans),
             full_optimizer_replayed=False, numeric_gt_parsed=False))
    print('MMR0 bank validation passed', max_residual, max_fd, max_scan, flush=True)


def horn_ate(predicted, reference):
    x, y = predicted-predicted.mean(0), reference-reference.mean(0)
    h = x.T@y
    xx, xy, xz, yx, yy, yz, zx, zy, zz = h.ravel()
    k = np.array([[xx+yy+zz, yz-zy, zx-xz, xy-yx],
                  [yz-zy, xx-yy-zz, xy+yx, zx+xz],
                  [zx-xz, xy+yx, -xx+yy-zz, yz+zy],
                  [xy-yx, zx+xz, yz+zy, -xx-yy+zz]])
    _, v = np.linalg.eigh(k)
    w, a, b, c = v[:, -1]
    r = np.array([[1-2*(b*b+c*c), 2*(a*b-w*c), 2*(a*c+w*b)],
                  [2*(a*b+w*c), 1-2*(a*a+c*c), 2*(b*c-w*a)],
                  [2*(a*c-w*b), 2*(b*c+w*a), 1-2*(a*a+b*b)]])
    return float(np.sqrt(np.mean(np.sum((x@r.T-y)**2, axis=1))))


def evaluate():
    run.verify()
    result = run.read(run.BASE/'results.json')
    assert result['bank_seal_sha256'] == run.sha(run.BASE/'bank_seal.json')
    max_error = 0.
    for key, row in result['rows'].items():
        seq = key.split('-')[0]
        z = np.load(run.BASE/f'bank/{key}.npz', allow_pickle=False)
        camera = np.loadtxt(run.DATA/f'poses/{seq}.txt').reshape(-1, 3, 4)
        truth = np.repeat(np.eye(4)[None], len(z['frames']), axis=0)
        truth[:, :3] = camera[z['frames']]
        calib = next(line for line in (run.DATA/f'sequences/{seq}/calib.txt').read_text().splitlines() if line.startswith('Tr:'))
        tr = np.eye(4)
        tr[:3] = np.fromstring(calib.split(':')[1], sep=' ').reshape(3, 4)
        lidar = np.stack([np.linalg.solve(tr, p@tr) for p in truth])
        reference = np.stack([np.linalg.solve(lidar[0], p) for p in lidar])
        for arm in ('O', 'F', 'R'):
            error = np.stack([np.linalg.solve(p, q) for p, q in zip(reference, z[arm])])
            t = np.sqrt(np.sum(error[:, :3, 3]**2, axis=1))
            angles = []
            for e in error:
                u, _, vh = np.linalg.svd(e[:3, :3])
                r = u@np.diag([1., 1., np.linalg.det(u@vh)])@vh
                sine = np.linalg.norm([r[2, 1]-r[1, 2], r[0, 2]-r[2, 0], r[1, 0]-r[0, 1]])/2
                angles.append(np.arctan2(sine, (np.trace(r)-1)/2)*180/np.pi)
            metrics = dict(relative_translation_rmse_m=float(np.sqrt(np.mean(t[1:]**2))),
                           relative_rotation_mean_deg=float(np.mean(angles[1:])),
                           relative_rotation_max_deg=float(np.max(angles)),
                           aligned_position_ate_m=horn_ate(z[arm][:, :3, 3], reference[:, :3, 3]))
            for name, value in metrics.items():
                max_error = max(max_error, abs(value-row[arm][name]))
        for arm in ('F', 'R'):
            signal = row[arm]['relative_translation_rmse_m'] <= .95*row['O']['relative_translation_rmse_m'] and row[arm]['relative_rotation_mean_deg'] <= row['O']['relative_rotation_mean_deg']
            assert signal == row[arm]['local_pose_signal']
    assert max_error < 1e-8
    run.save(run.BASE/'validation.json', dict(passed=True, local_metric_max_delta=max_error,
             windows=len(result['rows']), full_system_metric_claim=False, independent_optimizer_replay=False))
    (run.BASE/'INCOMPLETE').unlink()
    print('MMR0 evaluation validation passed', max_error, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('bank', 'evaluate'))
    stage = parser.parse_args().stage
    start = time.perf_counter()
    failed = None
    try:
        globals()[stage]()
    except Exception as error:
        failed = repr(error)
        path = run.BASE/f'FAILURE_validate_{stage}.json'
        if not path.exists():
            run.save(path, dict(error=failed, traceback=traceback.format_exc()))
        raise
    finally:
        log = run.BASE/'RESOURCE_LOG.json'
        rows = run.read(log)
        rows.append(dict(stage=f'validate_{stage}', utc=run.utc(), wall_s=time.perf_counter()-start,
                         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024, passed=failed is None))
        log.write_text(json.dumps(rows, indent=2)+'\n')
        artifacts = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
        assert sum(x['wall_s'] for x in rows) <= 1800
        assert rows[-1]['peak_rss_bytes'] <= 2*2**30 and artifacts <= 512*2**20
