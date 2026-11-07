"""Synthetic functional controls; no measured image/reference input."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_lib as lib
import refine_lib

OUT = lib.ROOT / 'controls'
checks = []


def check(name, condition, **evidence):
    checks.append({'name': name, 'passed': bool(condition), **evidence})
    lib.save(OUT / ('check_%02d.json' % len(checks)), checks[-1])
    assert condition, name


try:
    frozen = lib.verify_freeze('controls')
    cv2, np = lib.runtime()
    method = lib.load(lib.ROOT / 'METHOD.json')
    rng = np.random.default_rng(80421)
    xyz = rng.uniform([-4, -2, 8], [4, 2, 24], size=(120, 3))
    angle = np.deg2rad(7.)
    r = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])
    t = np.array([1.2, .15, .3])
    k = np.array([[700., 0., 620.], [0., 700., 180.], [0., 0., 1.]])

    def project(points):
        uv = points @ k.T
        return np.ascontiguousarray(uv[:, :2] / uv[:, 2:3])

    first, second = project(xyz), project(xyz @ r.T + t)
    target = np.eye(4)
    target[:3, :3], target[:3, 3] = r, t
    pred, arrays = refine_lib.estimate(cv2, np, first, second, k, method, 'synthetic_forward')
    check('nonplanar_calibrated_pose_available', pred['status'] == 'POSE', status=pred['status'])
    err = lib.angles(np, np.asarray(pred['R_i_to_j']), np.asarray(pred['unit_t_i_to_j']), target, 1e-9)
    check('forward_direction_rotation_and_signed_translation', err[0] < .01 and err[1] < .01, angle_errors_deg=err)
    check('unit_translation', abs(np.linalg.norm(pred['unit_t_i_to_j']) - 1) < 1e-12)
    reverse, _ = refine_lib.estimate(cv2, np, second, first, k, method, 'synthetic_reverse')
    reverse_ref = np.linalg.inv(target)
    re = lib.angles(np, np.asarray(reverse['R_i_to_j']), np.asarray(reverse['unit_t_i_to_j']), reverse_ref, 1e-9)
    check('reverse_pose_is_inverse', reverse['status'] == 'POSE' and re[0] < .01 and re[1] < .01, angle_errors_deg=re)
    check('positive_common_scale_leaves_pixels_unchanged', np.allclose(project(xyz * 7.3), first, atol=1e-12, rtol=0) and np.allclose(project(xyz * 7.3 @ r.T + t * 7.3), second, atol=1e-12, rtol=0))
    opposite = lib.angles(np, np.asarray(pred['R_i_to_j']), -np.asarray(pred['unit_t_i_to_j']), target, 1e-9)
    check('translation_sign_is_not_discarded', opposite[1] > 179.99)
    again, again_arrays = refine_lib.estimate(cv2, np, first, second, k, method, 'synthetic_forward')
    check('fixed_seed_reproduction', pred == again and all(np.array_equal(arrays[n], again_arrays[n]) for n in arrays))
    corrupt = second.copy()
    corrupt[-24:] = corrupt[np.arange(24)[::-1]]
    robust, _ = refine_lib.estimate(cv2, np, first, corrupt, k, method, 'synthetic_outliers')
    er = lib.angles(np, np.asarray(robust['R_i_to_j']), np.asarray(robust['unit_t_i_to_j']), target, 1e-9)
    check('fixed_outlier_geometry_control', robust['status'] == 'POSE' and er[0] < .1 and er[1] < .5, angle_errors_deg=er)
    a = np.eye(8, 128, dtype=np.float32) * 10
    b = a + np.float32(.001)
    matches = lib.mutual_matches(cv2, np, a, b, .75)
    check('mutual_ratio_exact_descriptor_identity', np.array_equal(matches, np.column_stack((np.arange(8), np.arange(8)))))
    check('ratio_ties_rejected', len(lib.mutual_matches(cv2, np, np.zeros_like(a), np.zeros_like(b), .75)) == 0)
    check('short_descriptor_input_has_no_matches', len(lib.mutual_matches(cv2, np, a[:1], b, .75)) == 0)
    sift = cv2.SIFT_create(**method['sift'])
    kp, desc = sift.detectAndCompute(np.zeros((120, 160), dtype=np.uint8), None)
    check('blank_image_has_no_features', len(kp) == 0 and desc is None)
    small, _ = refine_lib.estimate(cv2, np, first[:7], second[:7], k, method, 'short')
    check('insufficient_matches_explicit_no_pose', small['status'] == 'NO_EVIDENCE_INSUFFICIENT_MATCHES' and small['R_i_to_j'] is None and small['unit_t_i_to_j'] is None)
    line = np.column_stack((np.arange(12, dtype=float), np.arange(12, dtype=float)))
    degenerate, _ = refine_lib.estimate(cv2, np, line, line, k, method, 'line')
    check('collinear_input_explicit_no_pose', degenerate['status'] == 'NO_EVIDENCE_DEGENERATE_COORDINATES')
    bad = first.copy()
    bad[0, 0] = np.nan
    invalid, _ = refine_lib.estimate(cv2, np, bad, second, k, method, 'nonfinite')
    check('nonfinite_input_explicit_no_pose', invalid['status'] == 'NO_EVIDENCE_NONFINITE_MATCHES')
    pi = np.eye(4)
    pj = np.linalg.inv(target)
    q = np.linalg.solve(pj, pi)
    check('camera_to_first_reference_composition', np.allclose(q, target, atol=1e-14, rtol=0))
    rr, tt = lib.angles(np, np.eye(3), np.array([1., 0., 0.]), np.eye(4), 1e-9)
    check('zero_reference_translation_direction_is_null', rr == 0 and tt is None)
    cache = OUT / 'synthetic_cache.npz'
    with cache.open('xb') as handle:
        np.savez(handle, xy=first, descriptors=a)
    with np.load(cache, allow_pickle=False) as data:
        check('numpy_cache_no_pickle_roundtrip', np.array_equal(data['xy'], first) and np.array_equal(data['descriptors'], a))
    # Last: exercise the same audit-hook policy used by actual prediction workers.
    raw = robust['initial_pose']
    raw_err = lib.angles(np, np.asarray(raw['R_i_to_j']), np.asarray(raw['unit_t_i_to_j']), target, 1e-9)
    check('raw_outlier_failure_retained_same_seed_and_fixture', abs(raw_err[0] - 0.113146318316918) < 1e-9 and raw_err[0] >= .1, raw_angle_errors_deg=raw_err)
    trace = robust['refinement']['trace']
    check('robust_refit_has_strict_fixed_weight_cost_decrease', any(e['accepted'] for e in trace) and all(not e['accepted'] or e['new_cost'] < e['old_cost'] for e in trace), iterations=len(trace))
    test_step = np.array([.01, -.005, .003, .02, -.01])
    ur, ut = refine_lib.update(np, r, t / np.linalg.norm(t), test_step)
    check('refit_update_stays_proper_and_unit', np.max(np.abs(ur.T @ ur - np.eye(3))) < 1e-12 and abs(np.linalg.det(ur) - 1) < 1e-12 and abs(np.linalg.norm(ut) - 1) < 1e-12)
    lib.read_gate([cache], OUT)
    denied = False
    try:
        (lib.ROOT / 'EVALUATION_INPUTS.json').read_bytes()
    except PermissionError:
        denied = True
    check('prediction_gate_denies_reference_binding', denied)
    with np.load(cache, allow_pickle=False) as data:
        check('allowlisted_numpy_cache_read_after_gate', np.array_equal(data['xy'], first))
    lib.complete(OUT, {'controls': checks, 'control_count': len(checks), 'source_freeze_sha256': frozen,
                 'measured_image_reads': 0, 'supplied_reference_reads': 0})
    print('VB1 controls PASS: %d' % len(checks))
except BaseException as exc:
    lib.failure(OUT, exc)
    raise
