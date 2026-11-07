"""SMP2 orchestration: complete-patch split, unchanged shared-plane optimizer."""
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
import shared_plane_map_pilot as prior

old, alg = prior.old, prior.alg
read, save, sha, utc = prior.read, prior.save, prior.sha, prior.utc
BASE = old.MAIN/'docs/maintenance/2026-10-09/structural-holdout-map-pilot-01'
FIELDS = ('counts', 'means', 'seconds', 'keys')


def verify():
    frozen = read(BASE/'freeze.json')
    for path, digest in frozen['files'].items():
        assert sha(path) == digest, path
    for package, version in frozen['packages'].items():
        assert importlib.metadata.version(package) == version
    return frozen


def check_delivery(root):
    seal = read(root/'DELIVERY_SEAL.json')
    for item in seal['files']:
        assert sha(root/item['path']) == item['sha256'], item['path']
    return len(seal['files'])


def freeze():
    prior.verify()
    check_delivery(prior.BASE)
    check_delivery(old.ROOT_BASE)
    sources = [Path(__file__), Path(__file__).with_name('validate_structural_holdout_map_pilot.py'),
               BASE/'PROTOCOL.md', Path(prior.__file__),
               Path(__file__).with_name('validate_shared_plane_map_pilot.py'), Path(old.__file__),
               old.SLAM/'scripts/shared_plane_map.py', old.SLAM/'scripts/measured_map_reoptimization.py']
    snapshot = BASE/'source_snapshot'
    snapshot.mkdir()
    files = list(sources)
    for i, source in enumerate(sources):
        target = snapshot/f'{i:02d}-{source.name}'
        shutil.copyfile(source, target)
        files.append(target)
    files += [prior.BASE/name for name in ('DELIVERY_SEAL.json', 'freeze.json', 'preflight.json', 'validation.json')]
    files += [old.BASE/name for name in ('bank_seal.json', 'bank_validation.json', 'validation.json')]
    files += list((old.BASE/'bank').iterdir())
    files += [old.DATA/f'poses/{s}.txt' for s in ('00', '05', '06')]
    files += [old.DATA/f'sequences/{s}/calib.txt' for s in ('00', '05', '06')]
    save(BASE/'freeze.json', dict(utc=utc(), files={str(p): sha(p) for p in files},
         packages={p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
         windows=old.WINDOWS, scale=2, hash_format='SMP2|{window}|2|{kx},{ky},{kz}',
         hash_byte_order='big', holdout_modulo4_remainder=0,
         numeric_gt_parsed=False, exposed_development=True))
    (BASE/'INCOMPLETE').write_text('SMP2 requires bank and metric validation\n')
    print('SMP2 frozen', len(files), 'entries', flush=True)


def split(stats, window):
    payloads = [f'SMP2|{window}|2|{int(x)},{int(y)},{int(z)}' for x, y, z in stats['keys']]
    integers = np.array([int.from_bytes(hashlib.sha256(x.encode('utf-8')).digest()[:4], 'big') for x in payloads], np.uint32)
    return integers % 4 == 0, integers


def subset(stats, mask):
    return {name: stats[name][mask] for name in FIELDS}


def description(stats, poses):
    count = len(stats['counts'])
    coverage = stats['counts'].sum(0).astype(int).tolist()
    if count:
        normals = alg.fit_planes(stats, poses)[1][:, :, 0]
        spectrum = np.linalg.eigvalsh(normals.T@normals/count).tolist()
    else:
        spectrum = None
    return dict(patches=count, per_scan_points=coverage, normal_scatter_eigenvalues=spectrum)


def geometry(stats, poses):
    values = np.maximum(alg.fit_planes(stats, poses)[0][:, 0], 0.)
    return dict(scan_balanced_patch_rms_m=float(np.sqrt(np.mean(values))),
                per_patch_variance_m2=values.tolist())


def preflight():
    verify()
    assert read(prior.BASE/'preflight.json')['passed']
    # Synthetic split identities, including negative keys; no new real bank/GT.
    keys = np.array([[i-17, -i, i % 7] for i in range(50)], np.int64)
    synthetic = dict(keys=keys)
    held, numbers = split(synthetic, '00-200')
    reverse, reversed_numbers = split(dict(keys=keys[::-1]), '00-200')
    assert np.array_equal(held, reverse[::-1]) and np.array_equal(numbers, reversed_numbers[::-1])
    assert held.any() and (~held).any()
    for key, value in zip(keys, numbers):
        payload = 'SMP2|00-200|2|'+','.join(str(int(x)) for x in key)
        independent = int(hashlib.sha256(payload.encode()).hexdigest()[:8], 16)
        assert int(value) == independent
    rng = np.random.default_rng(10209)
    poses = np.repeat(np.eye(4)[None], 3, axis=0)
    poses[1, :3, 3] = [.1, .2, .3]
    groups = [[rng.normal(size=(30+i, 3)) for i in range(3)] for _ in keys]
    stats = prior.stats_from_groups(groups)
    stats['keys'] = keys
    max_h = max_g = 0.
    for mask in (held, ~held):
        current = subset(stats, mask)
        selected = [g for g, good in zip(groups, mask) if good]
        hc, gc = alg.plane_system(current, poses)
        hd, gd = prior.explicit_system(selected, poses)
        max_h = max(max_h, float(np.max(abs(hc-hd))))
        max_g = max(max_g, float(np.max(abs(gc-gd))))
    assert max_h < 1e-8 and max_g < 1e-8
    save(BASE/'preflight.json', dict(passed=True, synthetic_patches=50, whole_patch_hash_order_invariant=True,
         independently_checked_big_endian_hash=True, subset_explicit_hessian_max_delta=max_h,
         subset_explicit_gradient_max_delta=max_g, unchanged_solver_preflight_sha256=sha(prior.BASE/'preflight.json'),
         new_numeric_gt_parsed=False))
    print('SMP2 preflight passed', max_h, max_g, flush=True)


def bank():
    verify()
    assert read(BASE/'preflight.json')['passed']
    root = BASE/'bank'
    root.mkdir()
    summary = {}
    for seq, boundary in old.WINDOWS:
        window = f'{seq}-{boundary}'
        z = np.load(old.BASE/f'bank/{window}.npz', allow_pickle=False)
        points = [z[f'points_{i}'] for i in range(8)]
        initial = z['O']
        stats, info = alg.features(points, initial, 2.)
        held, numbers = split(stats, window)
        train, test = subset(stats, ~held), subset(stats, held)
        train_info, test_info = description(train, initial), description(test, initial)
        supported = bool(train_info['patches'] >= 10 and min(train_info['per_scan_points']) >= 100 and
                         test_info['patches'] >= 5 and min(test_info['per_scan_points']) > 0)
        arrays = {name: stats[name] for name in FIELDS}
        arrays.update({f'label_{i}': x for i, x in enumerate(stats['labels'])})
        arrays.update(holdout=held, hash_integers=numbers, O=initial, frames=z['frames'])
        row = dict(window=window, full_features=info, train=train_info, holdout=test_info,
                   supported=supported, geometry={}, costs={}, trace=None, correction=None)
        if supported:
            candidate, trace, correction = alg.optimize(train, initial, True)
            arrays['P'] = candidate
            row.update(trace=trace, correction=correction)
            for arm, pose in (('O', initial), ('P', candidate)):
                row['geometry'][arm] = dict(train=geometry(train, pose), holdout=geometry(test, pose))
                row['costs'][arm] = alg.cost(train, pose, initial, True)[1]
        np.savez(root/f'{window}.npz', **arrays)
        summary[window] = row
        print('SMP2 bank', window, train_info['patches'], test_info['patches'], supported, row['correction'], flush=True)
    save(root/'summary.json', summary)
    save(BASE/'bank_seal.json', dict(utc=utc(), freeze_sha256=sha(BASE/'freeze.json'),
         new_numeric_gt_parsed=False, files={p.name: sha(p) for p in root.iterdir()}))
    verify()


def gates(rows, summary):
    result = dict(all_four_supported_valid=len(rows) == 4 and all('P' in r and r['P']['valid'] for r in rows.values()))
    if result['all_four_supported_valid']:
        p = [r['P'] for r in rows.values()]
        ratio = np.mean([summary[k]['geometry']['P']['holdout']['scan_balanced_patch_rms_m'] for k in rows])/np.mean(
                        [summary[k]['geometry']['O']['holdout']['scan_balanced_patch_rms_m'] for k in rows])
        result.update(ate_improved_windows=sum(m['aligned_ate_gain'] > 0 for m in p),
                      mean_fractional_ate_gain=float(np.mean([m['aligned_ate_gain'] for m in p])),
                      ate_safety=all(m['aligned_ate_gain'] >= -.05 for m in p),
                      translation_safety=all(m['translation_gain'] >= -.05 for m in p),
                      rotation_safety=all(m['rotation_regression_deg'] <= .02 for m in p),
                      mean_holdout_rms_ratio=float(ratio), holdout_safety=bool(ratio <= 1.01))
        result['eligible'] = bool(result['ate_improved_windows'] >= 3 and result['mean_fractional_ate_gain'] >= .05 and
                                 result['ate_safety'] and result['translation_safety'] and result['rotation_safety'] and result['holdout_safety'])
    else:
        result['eligible'] = False
    return result


def evaluate():
    verify()
    assert read(BASE/'bank_validation.json')['passed']
    seal = read(BASE/'bank_seal.json')
    for name, digest in seal['files'].items():
        assert sha(BASE/'bank'/name) == digest
    summary, rows = read(BASE/'bank/summary.json'), {}
    for window, data in summary.items():
        z = np.load(BASE/f'bank/{window}.npz', allow_pickle=False)
        truth = old.gt(window.split('-')[0])[z['frames']]
        row = dict(O=old.errors(truth, z['O']))
        if data['supported']:
            metrics = old.errors(truth, z['P'])
            metrics.update(valid=data['correction']['valid'],
                           aligned_ate_gain=1-metrics['aligned_position_ate_m']/row['O']['aligned_position_ate_m'],
                           translation_gain=1-metrics['relative_translation_rmse_m']/row['O']['relative_translation_rmse_m'],
                           rotation_regression_deg=metrics['relative_rotation_mean_deg']-row['O']['relative_rotation_mean_deg'])
            row['P'] = metrics
            print('SMP2 evaluation', window, metrics['aligned_ate_gain'], metrics['translation_gain'], metrics['rotation_regression_deg'], flush=True)
        rows[window] = row
    save(BASE/'results.json', dict(utc=utc(), rows=rows, gates=gates(rows, summary),
         bank_seal_sha256=sha(BASE/'bank_seal.json'), independent_generalization=False, full_sequence_metrics=False))


def record_stage(name, callback):
    start, failure = time.perf_counter(), None
    try:
        callback()
    except Exception as error:
        failure = repr(error)
        path = BASE/f'FAILURE_{name}.json'
        if not path.exists():
            save(path, dict(error=failure, traceback=traceback.format_exc()))
        raise
    finally:
        rows = read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        rows.append(dict(stage=name, utc=utc(), wall_s=time.perf_counter()-start, peak_rss_bytes=rss, passed=failure is None))
        (BASE/'RESOURCE_LOG.json').write_text(json.dumps(rows, indent=2)+'\n')
        artifacts = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
        assert sum(r['wall_s'] for r in rows) <= 1800 and rss <= 2*2**30 and artifacts <= 512*2**20


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('freeze', 'preflight', 'bank', 'evaluate'))
    stage = parser.parse_args().stage
    record_stage(stage, globals()[stage])
