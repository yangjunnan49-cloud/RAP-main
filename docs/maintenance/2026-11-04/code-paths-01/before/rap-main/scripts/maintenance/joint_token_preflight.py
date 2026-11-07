"""TR0 prospective freeze and four-window GT-free token/invariance bank."""
import os
import resource
import sys
import time
from pathlib import Path
import numpy as np
import local_motion_common as c

B = c.MAIN / 'docs/maintenance/2026-10-07/joint-token-preflight-01'
HELPER = c.SLAM / 'scripts/joint_token_extraction.py'
MODES = ('N', 'E', 'H', 'R', 'D')


def runtime():
    import torch, scipy, open3d, hydra
    return dict(python=sys.version, torch=torch.__version__, numpy=np.__version__,
        scipy=scipy.__version__, open3d=open3d.__version__, hydra=hydra.__version__,
        cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version(),
        device=torch.cuda.get_device_name(0),
        threads={k: os.environ[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})


def prior_selection():
    old = c.read(c.SCREEN / 'freeze.json')
    seal = c.read(c.SCREEN / 'bank_seal.json')
    valid_seal = c.read(c.SCREEN / 'bank_validation_seal.json')
    assert seal['freeze_sha256'] == c.sha(c.SCREEN / 'freeze.json')
    assert seal['results_sha256'] == c.sha(c.SCREEN / 'bank.json')
    assert valid_seal['bank_seal_sha256'] == c.sha(c.SCREEN / 'bank_seal.json')
    assert valid_seal['validation_sha256'] == c.sha(c.SCREEN / 'bank_validation.json')
    assert c.read(c.SCREEN / 'bank_validation.json')['passed']
    rows = [next(r for r in old['census']['rows'] if r['seq'] == s) for s in ('00', '05', '06', '07')]
    for r in rows:
        assert r['t'] == 200 and r['ids'] == [199, 200, 198] and r['seed'] == c.seed(r['seq'], r['t'])
        assert r['times'][2] < r['times'][0] < r['times'][1]
        p = c.SCREEN / 'bank' / f"{r['seq']}_{r['t']:06d}.npz"
        assert c.sha(p) == seal['files'][str(p.relative_to(c.SCREEN))]
    return old, rows


def freeze():
    assert not (B / 'freeze.json').exists() and not (B / 'bank').exists()
    old, rows = prior_selection()
    native = c.frozen_sources()
    native += [Path(p) for r in rows for p in r['paths']]
    files = native + [Path(__file__), HELPER, Path(__file__).with_name('validate_joint_token_preflight.py'),
        B / 'PROTOCOL.md', c.MAIN / 'docs/maintenance/2026-10-07/metric-conflict-decomposition-01/NEXT_ROUND_PLAN.md',
        c.MAIN / 'docs/maintenance/2026-10-07/learned-measurement-design-01/SOURCE_AUDIT.json',
        Path(__file__).with_name('validate_local_motion_source_binding.py'),
        Path(__file__).with_name('validate_local_motion_feasibility_v2.py')]
    files += [c.SCREEN / name for name in ('freeze.json', 'bank.json', 'bank_seal.json', 'bank_validation.json', 'bank_validation_seal.json')]
    files += [c.SCREEN / 'bank' / f"{r['seq']}_{r['t']:06d}.npz" for r in rows]
    files = sorted(set(files))
    hashes = {str(p): c.sha(p) for p in files}
    for p in native:
        assert hashes[str(p)] == old['files'][str(p)], f'Changed native dependency: {p}'
    rt = runtime()
    assert rt['threads'] == dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    assert (rt['torch'], rt['numpy'], rt['open3d'], rt['device']) == (
        '2.7.0+cu128', '1.26.4', '0.19.0', 'NVIDIA GeForce RTX 5070')
    c.save(B / 'freeze.json', dict(utc=c.now(), stage='TR0', files=hashes, rows=rows,
        runtime=rt, modes=list(MODES), expected_npzs=20, expected_flow_calls=100,
        token_shape=[3, 1000, 512], integration_times=[1., .8, .6, .4, .2],
        caps=dict(stage_wall_s=600, gpu_gib=3, rss_gib=4, artifact_bytes=200 * 2**20),
        tolerances=dict(native_and_token_delta=0., independent_pose=1e-8,
                        normalization_center_scale=1e-12, rigid_rotation=1e-8),
        gt_files_read=False, selected_from_errors=False, training=False,
        rng_policy='Native transition preserved; unused one-element CUDA uniform draw is expected; enclosing seeded context restores all RNGs'))
    c.status(B, 'FROZEN', scientific_status='PROSPECTIVE', windows=4)
    print('TR0 frozen', len(files), 'identities / four fixed windows', flush=True)


def cap(start, freeze):
    import torch
    limits = freeze['caps']
    assert time.monotonic() - start < limits['stage_wall_s']
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20 < limits['rss_gib']
    assert torch.cuda.max_memory_allocated() / 2**30 < limits['gpu_gib']
    assert sum(p.stat().st_size for p in B.rglob('*') if p.is_file()) < limits['artifact_bytes']


def bank():
    import torch
    sys.path.insert(0, str(c.SLAM / 'scripts'))
    from joint_token_extraction import extract, snapshot, same_rng
    start = time.monotonic()
    f = c.check_freeze(B)
    assert runtime() == f['runtime']
    (B / 'bank').mkdir()
    (B / 'INCOMPLETE').write_text('Complete token bank and independent validation pending.\n')
    c.status(B, 'BANK_RUNNING')
    b, audit = c.make_backend()
    torch.cuda.reset_peak_memory_stats()
    records = []
    for r in f['rows']:
        points, features = c.get_points(b, r)
        bb, scale, centers, counts = c.batch(b, points, features)
        cond = bb['pointclouds'].cpu().numpy()
        with c.rng(r['seed']):
            noise = torch.randn((3000, 3), device='cuda')
        input_arrays = dict(points=np.concatenate(points), features=np.concatenate(features),
            noise=noise.cpu().numpy(), cond=cond, scale=scale, centers=centers, counts=counts,
            part_scan_ids=np.array(r['ids'], dtype=np.int64),
            point_rows=np.arange(1000, dtype=np.int64), seed=np.array(r['seed'], dtype=np.int64))
        native = None
        token_reference = None
        mode_records = []
        for mode in MODES:
            batch = dict(bb)
            if mode == 'D':
                batch['pointclouds_gt'] = torch.arange(9000, device='cuda', dtype=torch.float32).reshape(3000, 3) * .01 + 10.
            outer_before = snapshot()
            with c.rng(r['seed']):
                arrays, meta = extract(b.model, batch, noise, export=mode != 'N', hook=mode == 'H')
            assert same_rng(outer_before, snapshot()), 'Seeded context failed to restore outer RNGs'
            parts = c.decode(cond, arrays['end_point_trajectory'][-1], centers, counts, scale)
            arrays.update(parts=parts, pose=np.linalg.inv(parts[0]) @ parts[1],
                          placeholder_gt=batch['pointclouds_gt'].cpu().numpy())
            if mode == 'N':
                arrays.update(input_arrays)
                with np.load(c.SCREEN / 'bank' / f"{r['seq']}_{r['t']:06d}.npz", allow_pickle=False) as old:
                    for k in ('points', 'features', 'noise'):
                        assert np.array_equal(arrays[k], old[k]), k
                    for k in ('cond', 'scale', 'centers', 'counts', 'parts', 'pose', 'trajectory', 'end_point_trajectory'):
                        assert np.array_equal(arrays[k], old['R3_' + k]), k
                native = arrays
                native_meta = meta
            else:
                for k in ('trajectory', 'end_point_trajectory', 'parts', 'pose', 'rng_before_cpu', 'rng_before_cuda', 'rng_after_cpu', 'rng_after_cuda'):
                    assert np.array_equal(arrays[k], native[k]), (mode, k)
                assert meta['before'] == native_meta['before'] and meta['after'] == native_meta['after']
                assert arrays['tokens'].shape == (3, 1000, 512)
                if mode == 'E':
                    token_reference = arrays['tokens']
                else:
                    assert np.array_equal(arrays['tokens'], token_reference), (mode, 'tokens')
                if mode == 'H':
                    assert np.array_equal(arrays['tokens'], arrays['hook_tokens'])
                    assert np.array_equal(arrays['flow_inputs'][0], input_arrays['noise'])
                    assert np.array_equal(arrays['flow_inputs'][1:], native['trajectory'][:-1])
                    assert np.array_equal(arrays['flow_times'].ravel(), np.array([1., .8, .6, .4, .2], np.float32))
                    assert np.array_equal(arrays['hook_cond_coord'], cond)
                    assert np.array_equal(arrays['hook_local_features'], input_arrays['features'])
            assert all(np.isfinite(v).all() for v in arrays.values())
            np.savez_compressed(B / 'bank' / f"{r['seq']}_{r['t']:06d}_{mode}.npz", **arrays)
            mode_records.append(dict(mode=mode, outer_rng_restored=True, **meta))
            cap(start, f)
        records.append(dict(**r, native_replay_max_delta=0., control_output_max_delta=0.,
                            control_token_max_delta=0., modes=mode_records))
        print('TR0 complete window', r['seq'], r['t'], round(time.monotonic() - start, 2), 's', flush=True)
    assert len(list((B / 'bank').glob('*.npz'))) == f['expected_npzs']
    c.check_freeze(B)
    cap(start, f)
    c.save(B / 'bank.json', dict(utc=c.now(), rows=records, checkpoint=audit,
        windows=4, native_replay=True, expected_flow_calls=100, measured_hook_flow_calls=20,
        gt_files_read=False, training=False, wall_s=time.monotonic() - start,
        peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
        peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20))
    c.seal(B)
    c.status(B, 'BANK_SEALED', scientific_status='INDEPENDENT_VALIDATION_PENDING')
    print('TR0 20-file GT-free bank sealed', flush=True)


if __name__ == '__main__':
    try:
        {'freeze': freeze, 'bank': bank}[sys.argv[1]]()
    except Exception as ex:
        c.status(B, 'STOPPED', error=repr(ex))
        raise
