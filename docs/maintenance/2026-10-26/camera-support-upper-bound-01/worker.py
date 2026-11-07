"""Reference-conditioned forward-depth support census, never a predictor."""
import datetime
import hashlib
import json
import math
import time
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

START = time.monotonic()
ROOT = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def within_time():
    assert time.monotonic() - START < 290, 'worker_time_guard'


ok = False
error = None
rows = []
try:
    frozen = json.loads((ROOT / 'FREEZE.json').read_text(encoding='utf-8'))
    assert sha(ROOT / 'worker.py') == frozen['worker_sha256']
    for item in frozen['metadata'] + frozen['calibrations'] + frozen['poses'] + frozen['raw']:
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], str(path)
        within_time()
    import numpy as np

    def rotation_check(matrix):
        assert matrix.shape == (4, 4) and np.isfinite(matrix).all()
        assert np.array_equal(matrix[3], np.array([0., 0., 0., 1.]))
        rotation = matrix[:3, :3]
        assert np.max(np.abs(rotation.T @ rotation - np.eye(3))) < 1e-3
        assert abs(np.linalg.det(rotation) - 1) < 1e-3

    def depths(xyz, tr, q):
        assert xyz.ndim == 2 and xyz.shape[1] == 3 and np.isfinite(xyz).all()
        h = np.column_stack((xyz, np.ones(len(xyz))))
        cam = h @ tr.T
        target = cam @ q.T
        composed = q @ tr
        source_plane = xyz @ tr[2, :3] + tr[2, 3]
        target_plane = xyz @ composed[2, :3] + composed[2, 3]
        source_scale = np.abs(xyz) @ np.abs(tr[2, :3]) + abs(tr[2, 3]) + 1
        target_scale = (np.abs(xyz) @ (np.abs(q[2, :3]) @ np.abs(tr[:3, :3]))
                        + np.abs(q[2, :3]) @ np.abs(tr[:3, 3]) + abs(q[2, 3]) + 1)
        eps = np.finfo(np.float64).eps * 256
        source_guard, target_guard = eps * source_scale, eps * target_scale
        assert np.all(np.abs(cam[:, 2] - source_plane) <= source_guard)
        assert np.all(np.abs(target[:, 2] - target_plane) <= target_guard)
        first = (cam[:, 2] > 0) & (target[:, 2] > 0)
        second = (source_plane > 0) & (target_plane > 0)
        near = (np.abs(source_plane) <= source_guard) | (np.abs(target_plane) <= target_guard)
        assert not np.any((first != second) & ~near)
        return dict(source=cam[:, 2], target=target[:, 2], source_plane=source_plane,
                    target_plane=target_plane, source_guard=source_guard,
                    target_guard=target_guard, first=first, second=second, near=near,
                    composed=composed)

    identity = np.eye(4)
    fixture = np.array([[0., 0., 1.], [0., 0., -1.], [1., 0., 0.], [0., 0., 2.]])
    checks = []
    checks.append(int(depths(fixture, identity, identity)['first'].sum()) == 2)
    opposed = np.diag([-1., 1., -1., 1.])
    checks.append(int(depths(fixture, identity, opposed)['first'].sum()) == 0)
    shifted = identity.copy(); shifted[2, 3] = 2.
    checks.append(int(depths(fixture, identity, shifted)['first'].sum()) == 2)
    permutation = np.array([[0., -1., 0., 0.], [0., 0., -1., 0.],
                            [1., 0., 0., 0.], [0., 0., 0., 1.]])
    checks.append(int(depths(np.array([[1., 0., 0.], [-1., 0., 0.]]),
                            permutation, identity)['first'].sum()) == 1)
    rz = np.array([[0., -1., 0., 0.], [1., 0., 0., 0.],
                   [0., 0., 1., 0.], [0., 0., 0., 1.]])
    ry = np.array([[0., 0., 1., 0.], [0., 1., 0., 0.],
                   [-1., 0., 0., 0.], [0., 0., 0., 1.]])
    a = depths(fixture, permutation, rz @ ry)
    b = depths(fixture, permutation, ry @ rz)
    checks.append(not np.array_equal(a['target'], b['target']))
    checks.append(not bool(depths(np.zeros((1, 3)), identity, identity)['first'][0]))
    rejected = False
    try:
        depths(np.array([[math.nan, 0., 1.]]), identity, identity)
    except AssertionError:
        rejected = True
    checks.append(rejected)
    assert all(checks)
    write('PREFLIGHT.json', dict(passed=True, checks=len(checks),
        real_point_or_pose_decoding_before_preflight=False,
        numpy_version=np.__version__, zero_threshold_unchanged=True))

    manifest = json.loads(Path(frozen['cohort_path']).read_text(encoding='utf-8'))
    pairs = manifest['pairs']
    assert len(pairs) == 200
    calibrations = {}
    trajectories = {}
    for item in frozen['calibrations']:
        record = {}
        for line in Path(item['path']).read_text(encoding='utf-8').splitlines():
            name, value = line.split(':', 1)
            record[name] = np.array([float(token) for token in value.split()], dtype=np.float64)
        assert record['Tr'].shape == (12,) and record['P0'].shape == (12,)
        p0 = record['P0'].reshape(3, 4)
        assert np.isfinite(p0).all() and np.array_equal(p0[2], [0., 0., 1., 0.])
        tr = identity.copy(); tr[:3] = record['Tr'].reshape(3, 4)
        rotation_check(tr)
        calibrations[item['sequence']] = tr
    for item in frozen['poses']:
        table = np.loadtxt(item['path'], dtype=np.float64)
        assert table.ndim == 2 and table.shape[1] == 12 and np.isfinite(table).all()
        matrices = np.tile(identity, (len(table), 1, 1))
        matrices[:, :3] = table.reshape(-1, 3, 4)
        for matrix in matrices:
            rotation_check(matrix)
        trajectories[item['sequence']] = matrices
    paths = {(item['sequence'], item['frame']): Path(item['path']) for item in frozen['raw']}
    decimal_points = 0
    max_decimal_depth_delta = Decimal(0)
    for pair in pairs:
        seq = pair['sequence']; tr = calibrations[seq]
        for source_name, target_name, label in (
                ('source_i', 'source_j', 'i_to_j'), ('source_j', 'source_i', 'j_to_i')):
            source = pair[source_name]; target = pair[target_name]
            source_id, target_id = int(source), int(target)
            poses = trajectories[seq]
            assert source_id < len(poses) and target_id < len(poses)
            q = np.linalg.solve(poses[target_id], poses[source_id])
            assert np.isfinite(q).all()
            path = paths[(seq, source.zfill(6))]
            assert path.stat().st_size % 16 == 0 and path.stat().st_size > 0
            raw = np.fromfile(path, dtype='<f4').reshape(-1, 4)
            xyz = raw[:, :3].astype(np.float64)
            result = depths(xyz, tr, q)
            lower = ((result['source_plane'] > result['source_guard'])
                     & (result['target_plane'] > result['target_guard']))
            upper = ((result['source_plane'] >= -result['source_guard'])
                     & (result['target_plane'] >= -result['target_guard']))
            count1, count2 = int(result['first'].sum()), int(result['second'].sum())
            assert int(lower.sum()) <= count1 <= int(upper.sum())
            assert int(lower.sum()) <= count2 <= int(upper.sum())
            indices = sorted({k * (len(xyz) - 1) // 15 for k in range(16)})
            with localcontext() as context:
                context.prec = 60
                for index in indices:
                    point = [Decimal.from_float(float(v)) for v in xyz[index]] + [Decimal(1)]
                    for coefficients, actual, guard in (
                            (tr[2], result['source_plane'][index], result['source_guard'][index]),
                            (result['composed'][2], result['target_plane'][index], result['target_guard'][index])):
                        exact = sum((Decimal.from_float(float(c)) * p
                                     for c, p in zip(coefficients, point)), Decimal(0))
                        delta = abs(exact - Decimal.from_float(float(actual)))
                        assert delta <= Decimal.from_float(float(guard))
                        max_decimal_depth_delta = max(max_decimal_depth_delta, delta)
                    decimal_points += 1
            rows.append(dict(key=pair['key'], sequence=seq, direction=label,
                source_frame=source.zfill(6), target_frame=target.zfill(6),
                point_occurrences=len(xyz), source_positive=int((result['source'] > 0).sum()),
                target_positive=int((result['target'] > 0).sum()),
                joint_positive_route1=count1, joint_positive_route2=count2,
                numerical_lower_count=int(lower.sum()), numerical_upper_count=int(upper.sum()),
                near_plane_occurrences=int(result['near'].sum()),
                route_sign_disagreements=int((result['first'] != result['second']).sum()),
                fraction_of_source_occurrences=count1 / len(xyz)))
            del raw, xyz, result, lower, upper
            within_time()
    assert len(rows) == 400 and len({(r['key'], r['direction']) for r in rows}) == 400
    summaries = []
    for seq in ('00', '08'):
        selected = [row for row in rows if row['sequence'] == seq]
        assert len(selected) == 200
        fractions = [row['fraction_of_source_occurrences'] for row in selected]
        summaries.append(dict(sequence=seq, directions=len(selected),
            point_occurrences=sum(row['point_occurrences'] for row in selected),
            joint_positive_occurrences=sum(row['joint_positive_route1'] for row in selected),
            directions_with_zero_numerical_upper=sum(row['numerical_upper_count'] == 0 for row in selected),
            fraction_min=min(fractions), fraction_median=float(np.median(fractions)),
            fraction_max=max(fractions), near_plane_occurrences=sum(row['near_plane_occurrences'] for row in selected)))
    write('ROWS.json', rows)
    write('RESULTS.json', dict(
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=True,
        decision='REFERENCE_CONDITIONED_FORWARD_DEPTH_UPPER_BOUND_ONLY',
        complete_pairs=200, directional_records=400, unique_source_scans=len(paths),
        summaries=summaries, independent_affine_route_all_occurrences=True,
        Decimal_points=decimal_points, max_Decimal_depth_delta=str(max_decimal_depth_delta),
        actual_image_support_or_information_established=False,
        pose_accuracy_metric_or_candidate_selection=False,
        model_forward_backward_optimizer_calls=0, image_or_network_calls=0,
        reference_role='Exposed local supplied KITTI camera reference; no physical authentication',
        elapsed_seconds=time.monotonic() - START))
    assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) < 16777216
    ok = True
except BaseException as caught:
    error = repr(caught)
    write('FAILURE.json', dict(error=error, traceback=traceback.format_exc(),
                              completed_directional_records=len(rows), no_retry=True))
    raise
finally:
    write('WORKER_EXIT.json', dict(success=ok, error=error,
        elapsed_seconds=time.monotonic() - START, directional_records=len(rows),
        numeric_scope='Reference-conditioned geometry only; no image or efficacy computation'))
