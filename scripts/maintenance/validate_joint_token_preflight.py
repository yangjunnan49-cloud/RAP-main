"""Independent raw/descriptor/noise, Horn, row/time and RNG TR0 validator.

Never imports the new extractor or reruns RAP. Existing reference validators
provide independent input normalization and quaternion pose reconstruction.
"""
import os
import resource
import sys
import time
from pathlib import Path
import numpy as np
import local_motion_common as c
from validate_local_motion_source_binding import reconstruct
from validate_local_motion_feasibility_v2 import normalize, decode

B = c.MAIN / 'docs/maintenance/2026-10-07/joint-token-preflight-01'


def validate():
    import torch
    from dataset_process.extract_sample_features import FeatureExtractor
    start = time.monotonic()
    f = c.check_freeze(B)
    seal = c.check_seal(B)
    bank = c.read(B / 'bank.json')
    assert not bank['gt_files_read'] and not bank['training']
    assert bank['checkpoint']['strict'] and bank['checkpoint']['weights_only']
    assert bank['checkpoint']['rap_keys'] == 344 and bank['checkpoint']['descriptor_keys'] == 58
    assert len(seal['files']) == 20 and [r['seq'] for r in f['rows']] == ['00', '05', '06', '07']
    assert all(os.environ[k] == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    prior = c.read(c.SCREEN / 'freeze.json')
    model = FeatureExtractor(model_config=dict(num_points_per_patch=512, is_aligned_to_global_z=True, des_r=5.),
        des_r=5., is_aligned_to_global_z=True, checkpoint_path=None, device='cuda').model
    weights = torch.load(c.MAIN / 'weights/mini_spinnet_t.pth', map_location='cpu', weights_only=True)
    desc = {k[5:]: v for k, v in weights.items() if k.startswith('Desc.')}
    expected = model.state_dict()
    assert len(desc) == 58 and set(desc) == set(expected)
    assert all(v.shape == expected[k].shape and v.dtype == expected[k].dtype and torch.isfinite(v).all() for k, v in desc.items())
    model.load_state_dict(desc, strict=True)
    model.eval()
    torch.cuda.reset_peak_memory_stats()
    maximum = 0.
    rows = []
    for r, record in zip(f['rows'], bank['rows']):
        assert r == {k: record[k] for k in r}
        assert r == next(q for q in prior['census']['rows'] if q['seq'] == r['seq'])
        assert r['ids'] == [199, 200, 198] and r['t'] == 200 and r['seed'] == c.seed(r['seq'], 200)
        source = c.read(c.source(r['seq']) / 'source_frames.json')
        timestamps = np.loadtxt(c.DATA / 'sequences' / r['seq'] / 'times.txt')
        assert r['paths'] == [source['scan_files'][i] for i in r['ids']]
        assert r['times'] == timestamps[r['ids']].tolist() and r['times'][2] < r['times'][0] < r['times'][1]
        stem = f"{r['seq']}_{r['t']:06d}"
        with np.load(B / 'bank' / (stem + '_N.npz'), allow_pickle=False) as n, \
             np.load(c.SCREEN / 'bank' / (stem + '.npz'), allow_pickle=False) as old:
            for key in n.files:
                assert np.isfinite(n[key]).all()
            assert np.array_equal(n['part_scan_ids'], r['ids']) and np.array_equal(n['point_rows'], np.arange(1000))
            assert int(n['seed']) == r['seed']
            for k, path in enumerate(r['paths']):
                points = reconstruct(path)
                assert np.array_equal(points, n['points'][k*1000:(k+1)*1000])
                tensor = torch.tensor(points, device='cuda').unsqueeze(0)
                with c.rng(r['seed']), torch.no_grad():
                    features = model(pts=tensor, kpts=tensor.clone(), des_r=5., is_aligned_to_global_z=True)['desc'].squeeze(0).cpu().numpy()
                assert features.shape == (1000, 32) and np.array_equal(features, n['features'][k*1000:(k+1)*1000])
            with c.rng(r['seed']):
                noise = torch.randn((3000, 3), device='cuda').cpu().numpy()
            assert np.array_equal(noise, n['noise'])
            cond, scale, centers, counts = normalize(np.split(n['points'], 3))
            assert np.array_equal(cond, n['cond']) and np.array_equal(counts, n['counts'])
            assert abs(scale - float(n['scale'])) < f['tolerances']['normalization_center_scale']
            assert abs(centers - n['centers']).max() < f['tolerances']['normalization_center_scale']
            parts = decode(dict(cond=cond, raw=n['end_point_trajectory'][-1], centers=n['centers'], counts=counts, scale=scale))
            pose = np.linalg.solve(parts[0], parts[1])
            delta = max(float(abs(parts-n['parts']).max()), float(abs(pose-n['pose']).max()))
            maximum = max(maximum, delta)
            assert delta < f['tolerances']['independent_pose']
            for T in parts:
                assert abs(T[:3,:3].T @ T[:3,:3] - np.eye(3)).max() < f['tolerances']['rigid_rotation']
                assert abs(np.linalg.det(T[:3,:3]) - 1) < f['tolerances']['rigid_rotation']
            for key in ('points', 'features', 'noise'):
                assert np.array_equal(n[key], old[key])
            for key in ('cond', 'scale', 'centers', 'counts', 'parts', 'pose', 'trajectory', 'end_point_trajectory'):
                assert np.array_equal(n[key], old['R3_'+key])
            assert np.array_equal(n['placeholder_gt'], n['cond'])
            # Independent source-defined RNG transition: one unused CUDA draw.
            with torch.random.fork_rng(devices=[0]):
                torch.set_rng_state(torch.tensor(n['rng_before_cpu'], dtype=torch.uint8))
                torch.cuda.set_rng_state(torch.tensor(n['rng_before_cuda'], dtype=torch.uint8), 0)
                torch.rand(1, device='cuda')
                assert np.array_equal(torch.get_rng_state().cpu().numpy(), n['rng_after_cpu'])
                assert np.array_equal(torch.cuda.get_rng_state(0).cpu().numpy(), n['rng_after_cuda'])
            assert np.array_equal(n['rng_before_cpu'], n['rng_after_cpu'])
            assert not np.array_equal(n['rng_before_cuda'], n['rng_after_cuda'])
            native_meta = record['modes'][0]
            assert native_meta['before'] == native_meta['after']
            tokens = None
            for mode, meta in zip(('N', 'E', 'H', 'R', 'D'), record['modes']):
                assert meta['mode'] == mode and meta['outer_rng_restored'] and meta['parameters_and_modes_unchanged']
                assert meta['before'] == native_meta['before'] and meta['after'] == native_meta['after']
                with np.load(B / 'bank' / (stem + '_' + mode + '.npz'), allow_pickle=False) as z:
                    assert all(np.isfinite(z[k]).all() for k in z.files)
                    for key in ('trajectory', 'end_point_trajectory', 'parts', 'pose', 'rng_before_cpu', 'rng_after_cpu', 'rng_before_cuda', 'rng_after_cuda'):
                        assert np.array_equal(z[key], n[key]), (mode, key)
                    if mode == 'N':
                        assert 'tokens' not in z.files
                        continue
                    assert z['tokens'].shape == (3, 1000, 512) and z['tokens'].dtype == np.float32
                    if mode == 'E':
                        tokens = z['tokens'].copy()
                    else:
                        assert np.array_equal(tokens, z['tokens'])
                    if mode == 'H':
                        assert meta['hooked_flow_calls'] == 5
                        assert np.array_equal(z['tokens'], z['hook_tokens'])
                        assert np.array_equal(z['flow_inputs'][0], n['noise'])
                        assert np.array_equal(z['flow_inputs'][1:], n['trajectory'][:-1])
                        assert z['flow_inputs'].shape == (5, 3000, 3)
                        assert np.array_equal(z['flow_times'], np.array([[1.], [.8], [.6], [.4], [.2]], np.float32))
                        for key, expected_value in dict(cond_coord=n['cond'], local_features=n['features'],
                            scales=np.array([n['scale']], np.float32), anchor_indices=np.arange(3000)<1000,
                            cu_seqlens_part=np.array([0,1000,2000,3000], np.int32),
                            cu_seqlens_batch=np.array([0,3000], np.int32)).items():
                            assert np.array_equal(z['hook_'+key], expected_value), key
                    if mode == 'D':
                        expected_dummy = (np.arange(9000, dtype=np.float32).reshape(3000, 3) * np.float32(.01)) + np.float32(10.)
                        assert np.array_equal(z['placeholder_gt'], expected_dummy)
                        assert not np.array_equal(z['placeholder_gt'], n['cond'])
                    else:
                        assert np.array_equal(z['placeholder_gt'], n['cond'])
        rows.append(dict(seq=r['seq'], t=r['t'], raw_scans=3, points=3000,
            descriptor_values=96000, joint_token_values=1536000, independent_pose_max_delta=delta,
            native_replay_and_controls_exact=True, hook_and_tokens_exact=True, rng_transition_exact=True))
        print('TR0 independent source/token/RNG validation', r['seq'], flush=True)
    assert len(rows) == 4 and len(bank['rows']) == 4
    c.check_freeze(B)
    c.check_seal(B)
    elapsed = time.monotonic() - start
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    gpu = torch.cuda.max_memory_allocated() / 2**30
    size = sum(p.stat().st_size for p in B.rglob('*') if p.is_file())
    assert elapsed < f['caps']['stage_wall_s'] and rss < f['caps']['rss_gib'] and gpu < f['caps']['gpu_gib'] and size < f['caps']['artifact_bytes']
    c.save(B / 'validation.json', dict(utc=c.now(), passed=True, decision='PASS_JOINT_TOKEN_EXTRACTION_INVARIANCE',
        windows=4, raw_scans=12, points=12000, descriptor_values=384000, unique_joint_token_values=6144000,
        bank_npzs=20, rows=rows, source_feature_noise_token_delta=0., native_toggle_repeat_dummy_delta=0.,
        independent_pose_max_delta=maximum, rng_expected_unused_cuda_draws_per_call=1,
        gt_files_read=False, flow_inference_rerun=False, training=False,
        wall_s=elapsed, peak_rss_gib=rss, peak_allocated_gib=gpu, artifact_bytes_before_report=size,
        checks=['prospective freeze and complete bank seal', 'fixed census/causal ID/path/time selection',
                'direct raw preprocessing/descriptor/noise reconstruction', 'independent normalization and Horn SE3',
                'saved native replay and all raw/state/pose controls', 'exact last-layer hook/export and row/part bindings',
                'last input nominal t=.2 and exactly five hooked flow calls',
                'native CUDA RNG transition and enclosing-context restoration', 'dummy-placeholder invariance and unchanged parameter/mode metadata',
                'predeclared resource caps']))
    c.save(B / 'validation_seal.json', dict(utc=c.now(), validation_sha256=c.sha(B / 'validation.json'),
        freeze_sha256=c.sha(B / 'freeze.json'), bank_seal_sha256=c.sha(B / 'bank_seal.json')))
    c.status(B, 'VALIDATED', decision='PASS_JOINT_TOKEN_EXTRACTION_INVARIANCE', accuracy_established=False, training=False)
    (B / 'INCOMPLETE').unlink()
    print('TR0 VALIDATED; independent pose max delta', maximum, 'wall', elapsed, flush=True)


if __name__ == '__main__':
    try:
        validate()
    except Exception as ex:
        c.status(B, 'STOPPED_VALIDATION', error=repr(ex))
        raise
