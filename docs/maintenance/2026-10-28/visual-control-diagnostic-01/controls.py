"""Unreached interface controls and one analytic certificate; no solver replay."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'controls'
old = ROOT.parent / 'visual-baseline-execution-01'
binding = json.loads((ROOT / 'ORIGINAL_BINDING.json').read_text())
for e in binding['files']:
    assert hashlib.sha256(Path(e['path']).read_bytes()).hexdigest() == e['sha256']
spec = importlib.util.spec_from_file_location('vb1_frozen_lib', old / 'baseline_lib.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
checks = []


def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    lib.save(OUT / ('check_%02d.json' % len(checks)), checks[-1])
    assert condition, name


try:
    cv2, np = lib.runtime()
    method = lib.load(old / 'METHOD.json')
    a = np.eye(8, 128, dtype=np.float32) * 10
    b = a + np.float32(.001)
    indices = lib.mutual_matches(cv2, np, a, b, .75)
    check('mutual_identity', np.array_equal(indices, np.column_stack((np.arange(8), np.arange(8)))))
    check('strict_ratio_ties', len(lib.mutual_matches(cv2, np, np.zeros_like(a), np.zeros_like(b), .75)) == 0)
    check('short_descriptors', len(lib.mutual_matches(cv2, np, a[:1], b, .75)) == 0)
    points, descriptors = cv2.SIFT_create(**method['sift']).detectAndCompute(np.zeros((120, 160), dtype=np.uint8), None)
    check('blank_image', len(points) == 0 and descriptors is None)
    line = np.column_stack((np.arange(12, dtype=float), np.arange(12, dtype=float)))
    k = np.array([[700., 0., 620.], [0., 700., 180.], [0., 0., 1.]])
    p, _ = lib.estimate(cv2, np, line[:7], line[:7], k, method, 'short')
    check('insufficient_no_pose', p['status'] == 'NO_EVIDENCE_INSUFFICIENT_MATCHES' and p['R_i_to_j'] is None)
    p, _ = lib.estimate(cv2, np, line, line, k, method, 'line')
    check('collinear_no_pose', p['status'] == 'NO_EVIDENCE_DEGENERATE_COORDINATES')
    bad = line.copy()
    bad[0, 0] = np.nan
    p, _ = lib.estimate(cv2, np, bad, line, k, method, 'nonfinite')
    check('nonfinite_no_pose', p['status'] == 'NO_EVIDENCE_NONFINITE_MATCHES')
    rng = np.random.default_rng(80421)
    xyz = rng.uniform([-4, -2, 8], [4, 2, 24], size=(120, 3))[:96]
    t = np.array([1.2, .15, .3])

    def yaw(degrees):
        x = np.deg2rad(degrees)
        return np.array([[np.cos(x), 0, np.sin(x)], [0, 1, 0], [-np.sin(x), 0, np.cos(x)]])

    r, candidate = yaw(7.), yaw(7.2)
    target = np.eye(4)
    target[:3, :3], target[:3, 3] = r, t
    check('reference_composition', np.allclose(np.linalg.solve(np.linalg.inv(target), np.eye(4)), target, atol=1e-14, rtol=0))
    rr, tt = lib.angles(np, np.eye(3), np.array([1., 0., 0.]), np.eye(4), 1e-9)
    check('zero_translation_null', rr == 0 and tt is None)

    def project(x):
        y = x @ k.T
        return np.column_stack((y[:, :2] / y[:, 2:3], np.ones(len(y))))

    first, second = project(xyz), project(xyz @ r.T + t)
    x, y, z = t
    cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    invk = np.linalg.inv(k)

    def distances(rotation):
        f = invk.T @ cross @ rotation @ invk
        l2, l1 = first @ f.T, second @ f
        numerator = np.abs(np.sum(second * l2, axis=1))
        n1, n2 = np.linalg.norm(l1[:, :2], axis=1), np.linalg.norm(l2[:, :2], axis=1)
        return {'forward_max_px': float(np.max(numerator / n2)),
                'reverse_max_px': float(np.max(numerator / n1)),
                'Sampson_max_px': float(np.max(numerator / np.sqrt(n1 ** 2 + n2 ** 2)))}

    truth, alternate = distances(r), distances(candidate)
    error, direction = lib.angles(np, candidate, t / np.linalg.norm(t), target, 1e-9)
    established = max(alternate['forward_max_px'], alternate['reverse_max_px']) < 1 and error > .1
    lib.save(OUT / 'CONSENSUS_CERTIFICATE.json', {'status': 'ESTABLISHED' if established else 'NOT_ESTABLISHED',
        'clean_correspondences': 96, 'truth_distances': truth, 'candidate_distances': alternate,
        'candidate_rotation_error_deg': error, 'candidate_direction_error_deg': direction,
        'native_pose_estimator_replays': 0, 'parameters_searched': 0,
        'claim': 'A 1-pixel epipolar consensus condition alone does not certify rotation error <0.1 degrees' if established else 'Single proposed certificate not established'})
    check('analytic_truth_epipolar_identity', max(truth.values()) < 1e-10)
    cache = OUT / 'cache.npz'
    with cache.open('xb') as handle:
        np.savez(handle, xy=first, descriptors=a)
    with np.load(cache, allow_pickle=False) as data:
        check('no_pickle_cache_roundtrip', np.array_equal(data['xy'], first))
    lib.read_gate([cache], OUT)
    denied = False
    try:
        (old / 'EVALUATION_INPUTS.json').read_bytes()
    except PermissionError:
        denied = True
    check('reference_binding_denied', denied)
    with np.load(cache, allow_pickle=False) as data:
        check('allowlisted_cache_after_audit_hook', np.array_equal(data['xy'], first))
    lib.complete(OUT, {'controls': checks, 'control_count': len(checks),
        'consensus_certificate_established': established, 'VB1_remains_closed_fail': True,
        'real_image_prediction_admitted': False, 'measured_image_reference_reads': 0})
    print('CD1 synthetic diagnostic complete; VB1 unchanged')
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
