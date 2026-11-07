"""Audit existing sealed products; never import a runner or update scientific files."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[name] = "1"
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path
import numpy as np

MAIN = Path('/mnt/e/githouse/RAP-main')
OLD = MAIN / 'docs/maintenance/2026-10-09'
OUT = Path(__file__).resolve().parent
CV2 = OLD / 'rotation-protected-map-pilot-01'
DATA = Path('/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset')
CACHE = {}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    path = Path(path).resolve()
    if path not in CACHE:
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(2**20), b''):
                h.update(block)
        CACHE[path] = h.hexdigest()
    return CACHE[path]


def check_map(entries, base):
    if isinstance(entries, list):
        entries = {e['path']: e['sha256'] for e in entries}
    for name, digest in entries.items():
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        assert sha(path) == digest, str(path)
    return len(entries)


def angle(matrix):
    skew = np.array([matrix[2, 1]-matrix[1, 2], matrix[0, 2]-matrix[2, 0], matrix[1, 0]-matrix[0, 1]])
    return float(np.degrees(np.arctan2(np.linalg.norm(skew)/2, (np.trace(matrix)-1)/2)))


def ate(predicted, target):
    p, q = predicted-predicted.mean(0), target-target.mean(0)
    u, _, vt = np.linalg.svd(p.T @ q)
    d = np.eye(3)
    d[-1, -1] = np.linalg.det(u @ vt)
    error = p @ (u @ d @ vt)-q
    return float(np.sqrt(np.mean(np.sum(error**2, axis=1))))


def reference(seq, frames):
    camera = np.repeat(np.eye(4)[None], len(frames), axis=0)
    camera[:, :3] = np.loadtxt(DATA / f'poses/{seq}.txt').reshape(-1, 3, 4)[frames]
    line = next(x for x in (DATA / f'sequences/{seq}/calib.txt').read_text().splitlines() if x.startswith('Tr:'))
    tr = np.eye(4)
    tr[:3] = np.fromstring(line.split(':', 1)[1], sep=' ').reshape(3, 4)
    lidar = np.stack([np.linalg.solve(tr, x @ tr) for x in camera])
    return np.stack([np.linalg.solve(lidar[0], x) for x in lidar])


def metrics(poses, ref):
    end = np.linalg.solve(ref[-1], poses[-1])
    result = dict(joint_aligned_ate_m=ate(poses[:, :3, 3], ref[:, :3, 3]),
                  endpoint_translation_m=float(np.linalg.norm(end[:3, 3])),
                  endpoint_rotation_deg=angle(end[:3, :3]), visits={})
    for name, ids in [('A', list(range(8))), ('B', [15]+list(range(8, 15)))]:
        p, g = poses[ids], ref[ids]
        p = np.stack([np.linalg.solve(p[0], x) for x in p])
        g = np.stack([np.linalg.solve(g[0], x) for x in g])
        errors = np.stack([np.linalg.solve(a, b) for a, b in zip(g, p)])
        t = np.linalg.norm(errors[:, :3, 3], axis=1)
        r = np.array([angle(x[:3, :3]) for x in errors])
        result['visits'][name] = dict(relative_translation_rmse_m=float(np.sqrt(np.mean(t*t))),
            relative_rotation_mean_deg=float(r.mean()), relative_rotation_max_deg=float(r.max()),
            aligned_position_ate_m=ate(p[:, :3, 3], g[:, :3, 3]),
            per_node_translation_m=t.tolist(), per_node_rotation_deg=r.tolist())
    return result


def difference(a, b):
    if isinstance(a, dict):
        assert set(a) == set(b)
        return max(difference(a[k], b[k]) for k in a)
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))


def variances(z, poses):
    # Explicit points, centered covariance, equal mass per contributing scan.
    groups = [[] for _ in range(len(z['counts']))]
    for i in range(16):
        labels, points = z[f'label_{i}'], z[f'points_{i}']
        for k in np.unique(labels[labels >= 0]):
            q = points[labels == k] @ poses[i, :3, :3].T + poses[i, :3, 3]
            groups[int(k)].append(q)
    values = []
    for scans in groups:
        center = np.mean([q.mean(0) for q in scans], axis=0)
        covariance = np.mean([(q-center).T @ (q-center)/len(q) for q in scans], axis=0)
        values.append(max(float(np.linalg.eigvalsh(covariance)[0]), 0.0))
    return np.array(values)


def main():
    started = time.monotonic()
    checks = dict(scope='Existing artifact identity and bounded numerical re-audit',
                  scientific_products_written=False, optimizer_calls=0,
                  new_memberships=0, raw_preprocessing_replayed=False,
                  full_optimizer_replay=False, independent_rejected_census=False)
    names = ['measured-map-reoptimization-01', 'shared-plane-map-pilot-01',
             'structural-holdout-map-pilot-01', 'cross-visit-map-pilot-01',
             'rotation-protected-map-pilot-01']
    checks['delivery_entries'] = {n: check_map(read(OLD/n/'DELIVERY_SEAL.json')['files'], OLD/n) for n in names}
    freezes = ['measured-map-reoptimization-01/freeze.json',
        'measured-map-reoptimization-01/attempt-02/freeze.json',
        'shared-plane-map-pilot-01/freeze.json', 'structural-holdout-map-pilot-01/freeze.json',
        'cross-visit-map-pilot-01/freeze.json', 'cross-visit-map-pilot-01/attempt-02/freeze.json',
        'rotation-protected-map-pilot-01/freeze.json',
        'rotation-protected-map-pilot-01/objective-diagnosis-01/freeze.json']
    checks['freeze_entries'] = {n: check_map(read(OLD/n)['files'], (OLD/n).parent) for n in freezes}
    rlp2 = MAIN/'docs/maintenance/2026-10-08/motion-supervised-readout-01'
    entries = read(rlp2/'DELIVERY_SEAL.json')['files']
    subset = {p: h for p, h in entries.items() if Path(p).parent == rlp2}
    checks['RLP2_top_level_delivery_entries_checked'] = check_map(subset, rlp2)
    checks['RLP2_full_stage_bank_rehashed'] = False
    models = read(CV2/'CHECKS.json')
    checks['model_config_entries_checked'] = check_map({x['path']: x['sha256'] for x in models['model_source_checks']}, MAIN)
    checks['opaque_checkpoint_sha256'] = sha(MAIN/'weights/rap_model_12.ckpt')
    assert checks['opaque_checkpoint_sha256'] == models['opaque_checkpoint_sha256']
    checks['checkpoint_deserialized'] = False
    expected = read(CV2/'REPOSITORY_STATE.json')['repositories']
    repos = []
    for name, wanted in zip(('RAP-main', 'RAP-SLAM'), expected):
        directory = MAIN.parent/name
        def git(*args):
            return subprocess.check_output(['git', '-c', f'safe.directory={directory}', '-C', str(directory), *args], text=True).rstrip('\n')
        actual = dict(root=wanted['root'], HEAD=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
                      tracked_dirty=git('status', '--porcelain', '--untracked-files=no').splitlines())
        assert actual == wanted, actual
        repos.append(actual)
    checks['repositories'] = repos
    result, summary = read(CV2/'results.json'), read(CV2/'bank/summary.json')
    metric_delta = geometry_delta = 0.0
    rows = {}
    for seq, recorded in result['rows'].items():
        with np.load(CV2/f'bank/{seq}.npz', allow_pickle=False) as z:
            ref = reference(seq, z['frames'])
            independent = {}
            geometry = {}
            for arm in ('O', 'B', 'F', 'T'):
                independent[arm] = metrics(z[arm], ref)
                metric_delta = max(metric_delta, difference(independent[arm], recorded['arms'][arm]))
                v = variances(z, z[arm])
                geometry[arm] = {}
                for part, mask in [('train', ~z['holdout']), ('holdout', z['holdout'])]:
                    rms = float(np.sqrt(v[mask].mean()))
                    geometry[arm][part] = rms
                    saved = summary[seq]['geometry'][arm][part]
                    geometry_delta = max(geometry_delta, abs(rms-saved['rms_m']),
                                         difference(v[mask], saved['per_patch_variance_m2']))
            b, t = independent['B'], independent['T']
            rotation_exact = z['B'][:, :3, :3].tobytes() == z['T'][:, :3, :3].tobytes()
            shift = z['T'][8:, :3, 3]-z['B'][8:, :3, 3]
            shape_shift_delta = float(np.max(np.abs(shift-shift[-1])))
            assert np.array_equal(z['B'][:8], z['T'][:8]) and shape_shift_delta < 1e-9
            safety = all(t['visits'][v]['aligned_position_ate_m'] <= 1.05*b['visits'][v]['aligned_position_ate_m'] and
                t['visits'][v]['relative_translation_rmse_m'] <= 1.05*b['visits'][v]['relative_translation_rmse_m'] and
                t['visits'][v]['relative_rotation_mean_deg'] <= b['visits'][v]['relative_rotation_mean_deg']+.02 for v in ('A', 'B'))
            rows[seq] = dict(ate_gain=1-t['joint_aligned_ate_m']/b['joint_aligned_ate_m'],
                translation_gain=1-t['endpoint_translation_m']/b['endpoint_translation_m'],
                ate_harm_m=t['joint_aligned_ate_m']-b['joint_aligned_ate_m'],
                endpoint_translation_harm_m=t['endpoint_translation_m']-b['endpoint_translation_m'],
                rotation_byte_identical=rotation_exact, translation_shape_delta_m=shape_shift_delta,
                endpoint_rotation_change_deg=t['endpoint_rotation_deg']-b['endpoint_rotation_deg'],
                visit_safety=bool(safety), holdout_ratio=geometry['T']['holdout']/geometry['B']['holdout'],
                supported=bool(summary[seq]['supported']), valid=bool(summary[seq]['corrections']['T']['valid']))
            if seq == '00':
                with np.load(OLD/'cross-visit-map-pilot-01/attempt-02/bank/case.npz', allow_pickle=False) as previous:
                    fields = ('counts','means','seconds','keys','O','B','F','frames','nodes','holdout','hash_integers')
                    assert all(np.array_equal(z[k], previous[k]) for k in fields)
                    checks['CV1_CV2_00_fields_array_equal'] = list(fields)
    assert metric_delta < 1e-8 and geometry_delta < 1e-8
    primary = list(rows.values())
    gate = dict(all_three_supported_valid=len(primary)==3 and all(x['supported'] and x['valid'] for x in primary),
        joint_ate_improved_cases=sum(x['ate_gain']>0 for x in primary), endpoint_t_improved_cases=sum(x['translation_gain']>0 for x in primary),
        paired_improved_cases=sum(x['ate_gain']>0 and x['translation_gain']>0 for x in primary),
        mean_fractional_joint_ate_gain=float(np.mean([x['ate_gain'] for x in primary])),
        mean_fractional_endpoint_t_gain=float(np.mean([x['translation_gain'] for x in primary])),
        joint_ate_safety=all(x['ate_gain']>=-.05 for x in primary), endpoint_t_safety=all(x['translation_gain']>=-.05 for x in primary),
        rotation_invariance=all(x['rotation_byte_identical'] and abs(x['endpoint_rotation_change_deg'])<=1e-8 for x in primary),
        visit_safety=all(x['visit_safety'] for x in primary), holdout_safety=all(x['holdout_ratio']<=1.01 for x in primary))
    gate['eligible'] = bool(gate['all_three_supported_valid'] and gate['paired_improved_cases']>=2 and
        gate['mean_fractional_joint_ate_gain']>=.05 and gate['mean_fractional_endpoint_t_gain']>=.05 and
        all(gate[k] for k in ('joint_ate_safety','endpoint_t_safety','rotation_invariance','visit_safety','holdout_safety')))
    for key, value in gate.items():
        if isinstance(value, float):
            assert abs(value-result['primary_gate'][key]) < 1e-8
        else:
            assert value == result['primary_gate'][key]
    checks.update(independent_metric_max_delta=metric_delta, explicit_frozen_point_geometry_max_delta=geometry_delta,
                  CV2_rows=rows, CV2_primary_gate=gate)
    diagnostic = read(CV2/'objective-diagnosis-01/results.json')
    assert diagnostic['optimizer_calls'] == 0 and not diagnostic['performance_gain_claim']
    checks['diagnostic_full_reference_cost_higher_cases'] = [s for s, r in diagnostic['rows'].items() if all(
        r['reference_shape__full_reference_placement'][p+'_rms_m'] > r['Oshape__native_placement'][p+'_rms_m'] for p in ('train', 'holdout'))]
    checks['diagnostic_05_slopes'] = [diagnostic['rows']['05'][k]['cost_slope_towards_reference_per_m'] for k in
        ('Oshape__native_placement', 'reference_shape__native_placement')]
    checks['diagnostic_cost_gradient_replayed'] = False
    ledger = read(CV2/'RESOURCE_LOG.json')
    audit = read(CV2/'RESOURCE_AUDIT.json')
    total = sum(x['wall_s'] for x in ledger)
    peak = max(x['peak_rss_bytes'] for x in ledger)
    assert len(ledger) == audit['recorded_stages'] and all(x['passed'] for x in ledger)
    assert abs(total-audit['total_accounted_wall_s']) < 1e-12 and peak == audit['peak_rss_bytes']
    assert sha(CV2/'RESOURCE_LOG.json') == audit['stage_ledger_sha256']
    assert total <= audit['wall_cap_s'] and peak <= audit['rss_cap_bytes']
    size = sum(p.stat().st_size for p in CV2.rglob('*') if p.is_file())
    assert size < audit['artifact_cap_bytes']
    checks['CV2_resource_recount'] = dict(stages=len(ledger), accounted_wall_s=total, peak_rss_bytes=peak, current_dossier_bytes=size)
    checks['SMP2_missing_failed_RSS_preserved'] = read(OLD/'structural-holdout-map-pilot-01/RESOURCE_AUDIT.json')['all_attempted_rss_cap_fully_verified'] is False
    checks['original_failure_markers_preserved'] = {n: (OLD/n/'INCOMPLETE').exists() for n in
        ('measured-map-reoptimization-01', 'cross-visit-map-pilot-01', 'structural-holdout-map-pilot-01/revisit-design-audit-01')}
    assert all(checks['original_failure_markers_preserved'].values())
    checks['unique_files_hashed'] = len(CACHE)
    checks['input_identities'] = {str(p): digest for p, digest in sorted(CACHE.items())}
    checks['audit_process_wall_s'] = time.monotonic()-started
    checks['audit_peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    checks['audit_cost_excluded_from_historical_resource_ledgers'] = True
    checks['all_requested_checks_passed'] = True
    target = OUT/'CHECKS.json'
    assert not target.exists(), 'Use a separate attempt; never overwrite an audit.'
    target.write_text(json.dumps(checks, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in checks.items() if k not in ('input_identities','repositories','CV1_CV2_00_fields_array_equal')}, indent=2))


if __name__ == '__main__':
    main()
