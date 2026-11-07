"""Bounded explicit-point and independent-metric validation for SMP1."""
import argparse
import json
import resource
import time
import traceback
import shared_plane_map_pilot as run
import numpy as np
from scipy.spatial.transform import Rotation


def direct_planes(points, labels, poses, feature_count, omit=None):
    result = []
    for k in range(feature_count):
        patches = []
        for i, (p, group) in enumerate(zip(points, labels)):
            q = p[group == k]
            if len(q) and i != omit:
                patches.append(q@poses[i, :3, :3].T+poses[i, :3, 3])
        center = np.mean([p.mean(0) for p in patches], axis=0)
        cov = np.mean([(p-center).T@(p-center)/len(p) for p in patches], axis=0)
        value, vector = np.linalg.eigh(cov)
        result.append((center, value, vector[:, 0]))
    return result


def bank():
    run.verify()
    seal = run.read(run.BASE/'bank_seal.json')
    for p, digest in seal['files'].items():
        assert run.sha(run.BASE/'bank'/p) == digest
    summary = run.read(run.BASE/'bank/summary.json')
    max_moment = max_cost = max_probe = max_gradient = 0.
    valid_representations = valid_predictions = 0
    for key, row in summary.items():
        source = np.load(run.old.BASE/f"bank/{row['window']}.npz", allow_pickle=False)
        z = np.load(run.BASE/f'bank/{key}.npz', allow_pickle=False)
        assert np.array_equal(z['O'], source['O']) and np.array_equal(z['frames'], source['frames'])
        points = [source[f'points_{i}'][::2] for i in range(8)]
        odd = [source[f'points_{i}'][1::2] for i in range(8)]
        labels = [z[f'label_{i}'] for i in range(8)]
        stats = run.stats_read(z)
        feature_count = len(stats['counts'])
        assert feature_count == row['features']['features']
        for k in range(feature_count):
            assert np.sum(stats['counts'][k] > 0) >= 3 and stats['counts'][k].sum() >= 40
            for i, p in enumerate(points):
                q = p[labels[i] == k]
                assert len(q) == stats['counts'][k, i]
                if len(q):
                    assert len(q) >= 6
                    max_moment = max(max_moment, float(np.max(abs(q.mean(0)-stats['means'][k, i]))),
                                     float(np.max(abs(q.T@q/len(q)-stats['seconds'][k, i]))))
                    world = q@z['O'][i, :3, :3].T+z['O'][i, :3, 3]
                    assert np.all(np.floor(world/row['scale']).astype(np.int64) == stats['keys'][k])
        if not row['features']['representation_valid']:
            assert 'G' not in z and 'P' not in z
            continue
        valid_representations += 1
        probe_labels = [z[f'probe_label_{i}'] for i in range(8)]
        initial_planes = direct_planes(points, labels, z['O'], feature_count)
        for k, (center, values, n) in enumerate(initial_planes):
            assert values[0]/values.sum() < .025+1e-12 and values[1] > .005-1e-12 and values[0] <= .015+1e-12
            for i in np.flatnonzero(stats['counts'][k] > 0):
                q = points[i][labels[i] == k]@z['O'][i, :3, :3].T+z['O'][i, :3, 3]
                assert abs(n@(q.mean(0)-center)) <= .20+1e-12
        for arm in ('O', 'G', 'P'):
            pose = z[arm]
            assert np.max(abs(pose[0]-np.eye(4))) < 1e-12
            assert np.max(abs(pose[:, :3, :3].transpose(0, 2, 1)@pose[:, :3, :3]-np.eye(3))) < 1e-10
            direct = direct_planes(points, labels, pose, feature_count)
            cost = .5*np.mean([max(x[1][0], 0.) for x in direct])/run.alg.GEOMETRY_SIGMA**2
            max_cost = max(max_cost, abs(cost-row['costs'][arm]['geometry']))
            squared = []
            for i, (p, group) in enumerate(zip(odd, probe_labels)):
                good = group >= 0
                world = p[good]@pose[i, :3, :3].T+pose[i, :3, 3]
                for x, k in zip(world, group[good]):
                    center, _, n = direct[k]
                    squared.append(float(n@(x-center))**2)
                initial_world = p[good]@z['O'][i, :3, :3].T+z['O'][i, :3, 3]
                assert np.all(np.floor(initial_world/row['scale']).astype(np.int64) == stats['keys'][group[good]])
            max_probe = max(max_probe, abs(np.sqrt(np.mean(squared))-row['probes'][arm]['odd_point_rms_m']))
            assert len(squared) == row['probes'][arm]['odd_point_count']
            if arm != 'O':
                trace = row['traces'][arm]
                assert len(trace) == 24 and all(t['after'] <= t['before']+1e-12 for t in trace)
                assert abs(trace[-1]['after']-row['costs'][arm]['combined' if arm == 'P' else 'geometry']) < 1e-9
                correction = np.stack([np.linalg.solve(a, b) for a, b in zip(z['O'], pose)])
                mt = np.max(np.linalg.norm(correction[:, :3, 3], axis=1))
                mr = np.max(Rotation.from_matrix(correction[:, :3, :3]).magnitude())*180/np.pi
                assert bool(mt <= 1. and mr <= 5.) == row['corrections'][arm]['valid']
                valid_predictions += row['corrections'][arm]['valid']
        h, gradient = run.alg.plane_system(stats, z['P'])
        for node, axis in ((1, 0), (1, 2), (1, 3), (1, 5), (6, 1), (6, 4)):
            delta = np.zeros(6)
            delta[axis] = 1e-6
            plus, minus = z['P'].copy(), z['P'].copy()
            plus[node], minus[node] = run.alg.retract(plus[node], delta), run.alg.retract(minus[node], -delta)
            fd = (run.alg.cost(stats, plus, z['O'], False)[0]-run.alg.cost(stats, minus, z['O'], False)[0])/2e-6
            max_gradient = max(max_gradient, abs(fd-gradient[6*(node-1)+axis]))
        print('SMP1 bank check', key, feature_count, flush=True)
    assert max_moment < 1e-10 and max_cost < 1e-8 and max_probe < 1e-8 and max_gradient < 1e-4
    run.save(run.BASE/'bank_validation.json', dict(passed=True, representations=len(summary),
             valid_representations=valid_representations, valid_predictions=int(valid_predictions),
             full_moment_max_delta=max_moment, explicit_plane_cost_max_delta=max_cost,
             explicit_odd_probe_max_delta=max_probe, selected_real_geometry_gradient_fd=max_gradient,
             full_optimizer_replay=False, new_numeric_gt_parsed=False))


def horn_ate(x, y):
    x, y = x-x.mean(0), y-y.mean(0)
    h = x.T@y
    xx, xy, xz, yx, yy, yz, zx, zy, zz = h.ravel()
    k = np.array([[xx+yy+zz, yz-zy, zx-xz, xy-yx],
                  [yz-zy, xx-yy-zz, xy+yx, zx+xz],
                  [zx-xz, xy+yx, -xx+yy-zz, yz+zy],
                  [xy-yx, zx+xz, yz+zy, -xx-yy+zz]])
    _, vectors = np.linalg.eigh(k)
    w, a, b, c = vectors[:, -1]
    r = np.array([[1-2*(b*b+c*c), 2*(a*b-w*c), 2*(a*c+w*b)],
                  [2*(a*b+w*c), 1-2*(a*a+c*c), 2*(b*c-w*a)],
                  [2*(a*c-w*b), 2*(b*c+w*a), 1-2*(a*a+b*b)]])
    return float(np.sqrt(np.mean(np.sum((x@r.T-y)**2, axis=1))))


def evaluate():
    run.verify()
    result = run.read(run.BASE/'results.json')
    summary = run.read(run.BASE/'bank/summary.json')
    assert result['bank_seal_sha256'] == run.sha(run.BASE/'bank_seal.json')
    maximum = 0.
    for key, row in result['rows'].items():
        seq = row['window'].split('-')[0]
        z = np.load(run.BASE/f'bank/{key}.npz', allow_pickle=False)
        camera = np.loadtxt(run.old.DATA/f'poses/{seq}.txt').reshape(-1, 3, 4)
        t = np.repeat(np.eye(4)[None], 8, axis=0)
        t[:, :3] = camera[z['frames']]
        tr = np.eye(4)
        line = next(x for x in (run.old.DATA/f'sequences/{seq}/calib.txt').read_text().splitlines() if x.startswith('Tr:'))
        tr[:3] = np.fromstring(line.split(':')[1], sep=' ').reshape(3, 4)
        lidar = np.stack([np.linalg.solve(tr, q@tr) for q in t])
        reference = np.stack([np.linalg.solve(lidar[0], q) for q in lidar])
        for arm in ['O']+list(row['arms']):
            recorded = row['O'] if arm == 'O' else row['arms'][arm]
            errors = np.stack([np.linalg.solve(a, b) for a, b in zip(reference, z[arm])])
            angles = []
            for e in errors:
                u, _, vh = np.linalg.svd(e[:3, :3])
                r = u@np.diag([1., 1., np.linalg.det(u@vh)])@vh
                sine = np.linalg.norm([r[2, 1]-r[1, 2], r[0, 2]-r[2, 0], r[1, 0]-r[0, 1]])/2
                angles.append(np.arctan2(sine, (np.trace(r)-1)/2)*180/np.pi)
            translations = np.linalg.norm(errors[:, :3, 3], axis=1)
            metrics = dict(relative_translation_rmse_m=float(np.sqrt(np.mean(translations[1:]**2))),
                           relative_rotation_mean_deg=float(np.mean(angles[1:])), relative_rotation_max_deg=float(np.max(angles)),
                           aligned_position_ate_m=horn_ate(z[arm][:, :3, 3], reference[:, :3, 3]))
            maximum = max(maximum, max(abs(metrics[k]-recorded[k]) for k in metrics))
    assert maximum < 1e-8
    for scale in run.SCALES:
        rows = [x for x in result['rows'].values() if x['scale'] == scale]
        gate = result['gates'][str(int(scale))]
        if gate['all_valid']:
            p = [x['arms']['P'] for x in rows]
            keys = [k for k, x in result['rows'].items() if x['scale'] == scale]
            ratio = np.mean([summary[k]['probes']['P']['odd_point_rms_m'] for k in keys])/np.mean([summary[k]['probes']['O']['odd_point_rms_m'] for k in keys])
            eligible = (sum(m['aligned_ate_gain'] > 0 for m in p) >= 3 and np.mean([m['aligned_ate_gain'] for m in p]) >= .05 and
                        all(m['aligned_ate_gain'] >= -.05 and m['translation_gain'] >= -.05 and m['rotation_regression_deg'] <= .02 for m in p) and ratio <= 1.01)
            assert bool(eligible) == gate['eligible']
    chosen = next((s for s in run.SCALES if result['gates'][str(int(s))]['eligible']), None)
    assert result['selected_for_revisit_design_scale'] == chosen
    run.save(run.BASE/'validation.json', dict(passed=True, independent_metric_max_delta=maximum,
             gates_checked=True, full_optimizer_replay=False, full_sequence_metric_claim=False))
    (run.BASE/'INCOMPLETE').unlink()
    print('SMP1 independent metrics/gates passed', maximum, chosen, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('bank', 'evaluate'))
    stage = parser.parse_args().stage
    start = time.perf_counter()
    failure = None
    try:
        globals()[stage]()
    except Exception as error:
        failure = repr(error)
        path = run.BASE/f'FAILURE_validate_{stage}.json'
        if not path.exists():
            run.save(path, dict(error=failure, traceback=traceback.format_exc()))
        raise
    finally:
        rows = run.read(run.BASE/'RESOURCE_LOG.json')
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        rows.append(dict(stage=f'validate_{stage}', utc=run.utc(), wall_s=time.perf_counter()-start,
                         peak_rss_bytes=rss, passed=failure is None))
        (run.BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows, indent=2)+'\n')
        artifacts = sum(p.stat().st_size for p in run.BASE.rglob('*') if p.is_file())
        assert sum(r['wall_s'] for r in rows) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20
