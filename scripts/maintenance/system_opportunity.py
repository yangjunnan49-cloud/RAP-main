"""Frozen-stage E0 system opportunity audit; no production code changes."""
import hashlib
import importlib.metadata
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAIN = Path('/mnt/e/githouse/RAP-main')
ROOT = MAIN.parent / 'RAP-SLAM'
DATA = MAIN.parent / 'Datasets/data_odometry_velodyne/dataset'
BASE = MAIN / 'docs/maintenance/2026-09-29/system-opportunity-audit-01'
DEV = MAIN / 'docs/maintenance/2026-09-26/e0-frontend-01'
HOLD = MAIN / 'docs/maintenance/2026-09-27/e0-heldout-01'
SEQS = {'00': 4541, '05': 2761, '06': 1101, '07': 1101, '09': 1591, '10': 1201}
ALLOW = ('i', 'j', 'T_rel', 'overlap', 'mean_dist', 'measurement_id')
ATTEMPT = BASE / 'attempt-01'
EVAL = BASE / 'evaluation-01'
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def source(seq):
    return (DEV if seq in ('00', '05', '06') else HOLD) / f'full-{seq}-A'


def poses(path, n):
    a = np.loadtxt(path).reshape(-1, 3, 4)
    assert len(a) == n and np.isfinite(a).all()
    p = np.tile(np.eye(4), (n, 1, 1))
    p[:, :3] = a
    return p


def inputs():
    paths = [BASE / 'PROTOCOL.md', Path(__file__), Path(__file__).with_name('validate_system_opportunity.py'),
             ROOT / 'rap_slam/pose_graph.py', ROOT / 'rap_slam/real_dataset.py',
             ROOT / 'rap_slam/trajectory_protocol.py', ROOT / 'rap_slam/evaluate.py',
             ROOT / 'scripts/eval_paper_metrics.py']
    for seq in SEQS:
        src = source(seq)
        paths.extend(src / n for n in ('odom_poses.txt', 'optimized_poses.txt', 'keyframes.json',
                     'accepted_loops.json', 'source_frames.json', 'verification_measurements.jsonl', 'summary.json'))
        paths.extend((DATA / 'poses' / f'{seq}.txt', DATA / 'sequences' / seq / 'calib.txt'))
    return paths


def verify_freeze():
    freeze = read(BASE / 'freeze.json')
    assert set(freeze['files']) == {str(p) for p in inputs()}
    for p, h in freeze['files'].items():
        assert sha(p) == h, p
    return freeze


def freeze():
    assert not (BASE / 'freeze.json').exists()
    assert not ATTEMPT.exists()
    paths = inputs()
    assert all(p.is_file() for p in paths)
    # Verify prior E0 identities wherever parent hash manifests exist.
    parent = read(DEV / 'artifact_hashes.json')
    for seq in ('00', '05', '06'):
        src = source(seq)
        for p in paths:
            if p.parent == src:
                assert sha(p) == parent[str(p.relative_to(DEV))], p
    save(BASE / 'freeze.json', {
        'utc': datetime.now(timezone.utc).isoformat(),
        'files': {str(p): sha(p) for p in paths},
        'cohort': list(SEQS), 'expected_attempts': 71, 'expected_edges': 58,
        'packages': {p: importlib.metadata.version(p) for p in ('numpy', 'gtsam', 'evo', 'scipy')},
        'python': sys.version, 'cap_wall_s': 3600, 'cap_peak_rss_gib': 4,
        'cap_artifact_gib': 1,
    })
    print('frozen', len(paths), 'files', flush=True)


def strip_logs(src, kf):
    events = [json.loads(line) for line in (src / 'verification_measurements.jsonl').read_text().splitlines()]
    starts = {e['attempt_id']: e for e in events if e['event'] == 'candidate_started'}
    finishes = {e['attempt_id']: e for e in events if e['event'] == 'candidate_finished'}
    generations = {e['measurement']['measurement_id']: e['measurement'] for e in events if e['event'] == 'generation'}
    assert len(starts) == len(finishes) and len(starts) == len(set(starts))
    out = []
    for aid, start in starts.items():
        end = finishes[aid]
        i, j = int(start['i']), int(start['j'])
        assert i in kf and j in kf and i < j
        assert start['source_frame_ids'] == [i, j]
        mid = end['selected_measurement_id']
        m = generations[mid]
        assert m['source_frame_ids'] == [i, j]
        out.append({'i': i, 'j': j, 'attempt_id': aid, 'status': end['status'],
                    'selected_measurement_id': mid, 'T_rel': m['T_rel'],
                    'overlap': m['overlap'], 'mean_dist': m['mean_dist']})
    assert len(out) == len(starts)
    return out


def replay(odom, kf, edges):
    from rap_slam import pose_graph
    opt = pose_graph.optimize_pose_graph(list(odom), kf, edges)
    result = np.asarray(pose_graph.propagate_to_full_trajectory(list(odom), kf, opt))
    assert result.shape == odom.shape and np.isfinite(result).all()
    return result


def bank():
    verify_freeze()
    assert not ATTEMPT.exists()
    ATTEMPT.mkdir()
    (BASE / 'INCOMPLETE').write_text('Bank/evaluator/validation pending\n')
    begin = time.monotonic()
    counts = {}
    for seq, n in SEQS.items():
        src = source(seq)
        dest = ATTEMPT / seq
        dest.mkdir()
        odom = poses(src / 'odom_poses.txt', n)
        kf = read(src / 'keyframes.json')
        assert kf == sorted(set(kf)) and kf[0] == 0 and kf[-1] == n - 1
        assert read(src / 'source_frames.json')['source_frame_ids'] == list(range(n))
        edges = [{key: e[key] for key in ALLOW} for e in read(src / 'accepted_loops.json')]
        assert all(e['i'] in kf and e['j'] in kf for e in edges)
        candidates = strip_logs(src, set(kf))
        accepted = {c['selected_measurement_id']: c for c in candidates if c['status'] == 'accepted'}
        assert len(accepted) == len(edges)
        for edge in edges:
            c = accepted[edge['measurement_id']]
            assert (edge['i'], edge['j']) == (c['i'], c['j']) and edge['T_rel'] == c['T_rel']
        save(dest / 'edges.json', edges)
        save(dest / 'candidates.json', candidates)
        full = replay(odom, kf, edges)
        delta = float(np.max(np.abs(full - poses(src / 'optimized_poses.txt', n))))
        assert delta <= 1e-5, (seq, delta)
        np.save(dest / 'baseline.npy', full)
        for idx in range(len(edges)):
            assert time.monotonic() - begin < 3600
            np.save(dest / f'omit-{idx:03d}.npy', replay(odom, kf, edges[:idx] + edges[idx+1:]))
        counts[seq] = {'attempts': len(candidates), 'accepted': len(edges), 'baseline_delta': delta}
        print('bank', seq, counts[seq], flush=True)
    assert sum(v['attempts'] for v in counts.values()) == 71
    assert sum(v['accepted'] for v in counts.values()) == 58
    assert counts['10'] == {'attempts': 11, 'accepted': 0, 'baseline_delta': counts['10']['baseline_delta']}
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    assert peak < 4
    save(ATTEMPT / 'bank_execution.json', {'counts': counts, 'wall_s': time.monotonic() - begin,
                                           'peak_rss_gib': peak})
    files = [p for p in ATTEMPT.rglob('*') if p.is_file()]
    save(BASE / 'bank_seal.json', {'files': {str(p.relative_to(ATTEMPT)): sha(p) for p in files},
                                  'freeze_sha256': sha(BASE / 'freeze.json')})
    verify_freeze()
    print('bank sealed', len(files), 'files', flush=True)


def verify_bank():
    verify_freeze()
    seal = read(BASE / 'bank_seal.json')
    assert seal['freeze_sha256'] == sha(BASE / 'freeze.json')
    assert set(seal['files']) == {str(p.relative_to(ATTEMPT)) for p in ATTEMPT.rglob('*') if p.is_file()}
    for p, h in seal['files'].items():
        assert sha(ATTEMPT / p) == h, p


def metric(gt, tr, est, segments=False):
    import eval_paper_metrics as epm
    gc = tr @ gt @ np.linalg.inv(tr)
    ec = tr @ est @ np.linalg.inv(tr)
    lm = epm.evaluate_pair(list(gt), list(est), list(range(len(gt))))
    cm = epm.evaluate_pair(list(gc), list(ec), list(range(len(gt))))
    result = {'ate': lm['ape_aligned_rmse'], 'ter': cm['kitti_ter_pct'],
              'rer': cm['kitti_rer_deg100m'], 'segment_count': cm['kitti_segments']}
    return (result, cm['kitti_segment_records']) if segments else result


def evaluator():
    verify_bank()
    assert not (BASE / 'results.json').exists()
    assert not EVAL.exists()
    EVAL.mkdir()
    from rap_slam.real_dataset import load_gt_poses, _read_calib_transform
    begin = time.monotonic()
    rows = {}
    all_segments = {}
    for seq, n in SEQS.items():
        src, dest = source(seq), ATTEMPT / seq
        evdir = EVAL / seq
        evdir.mkdir()
        calib = DATA / 'sequences' / seq / 'calib.txt'
        gt = np.asarray(load_gt_poses(str(DATA / 'poses' / f'{seq}.txt'), str(calib), apply_calib=True))
        assert gt.shape == (n, 4, 4)
        tr = _read_calib_transform(str(calib))
        odom = poses(src / 'odom_poses.txt', n)
        full = np.load(dest / 'baseline.npy')
        om, os = metric(gt, tr, odom, True)
        fm, fs = metric(gt, tr, full, True)
        assert len(os) == len(fs) and len(os) > 0
        seg = []
        for a, b in zip(os, fs):
            assert (a['first'], a['last'], a['length_m']) == (b['first'], b['last'], b['length_m'])
            seg.append({'first': a['first'], 'last': a['last'], 'length_m': a['length_m'],
                        'odom_ter_pct': 100 * a['translation_fraction'],
                        'full_ter_pct': 100 * b['translation_fraction'],
                        'odom_rer_deg100m': a['rotation_rad_per_m'] * 180 / np.pi * 100,
                        'full_rer_deg100m': b['rotation_rad_per_m'] * 180 / np.pi * 100})
        save(evdir / 'segments.json', seg)
        all_segments[seq] = seg
        edges = read(dest / 'edges.json')
        leaves, oracles = [], []
        for idx, edge in enumerate(edges):
            assert time.monotonic() - begin < 3600
            leave = metric(gt, tr, np.load(dest / f'omit-{idx:03d}.npy'))
            leaves.append({'edge_index': idx, 'i': edge['i'], 'j': edge['j'], 'metrics': leave,
                           'included_minus_omitted': {k: fm[k] - leave[k] for k in ('ate', 'ter', 'rer')}})
            truth = np.linalg.inv(gt[edge['i']]) @ gt[edge['j']]
            oracle_edges = [dict(e) for e in edges]
            oracle_edges[idx]['T_rel'] = truth.tolist()
            assert np.max(np.abs(np.asarray(oracle_edges[idx]['T_rel']) - truth)) < 1e-6
            op = replay(odom, read(src / 'keyframes.json'), oracle_edges)
            np.save(evdir / f'oracle-{idx:03d}.npy', op)
            val = metric(gt, tr, op)
            measured = np.asarray(edge['T_rel'])
            diff = np.linalg.inv(measured) @ truth
            oracles.append({'edge_index': idx, 'i': edge['i'], 'j': edge['j'], 'metrics': val,
                            'oracle_minus_baseline': {k: val[k] - fm[k] for k in ('ate', 'ter', 'rer')},
                            'measured_pose_error_m': float(np.linalg.norm(diff[:3, 3])),
                            'measured_pose_error_deg': float(np.degrees(np.arccos(np.clip((np.trace(diff[:3, :3]) - 1) / 2, -1, 1))))})
        candidates = []
        for c in read(dest / 'candidates.json'):
            i, j = c['i'], c['j']
            truth = np.linalg.inv(gt[i]) @ gt[j]
            diff = np.linalg.inv(np.asarray(c['T_rel'])) @ truth
            pe = float(np.linalg.norm(diff[:3, 3]))
            re = float(np.degrees(np.arccos(np.clip((np.trace(diff[:3, :3]) - 1) / 2, -1, 1))))
            distance = float(np.linalg.norm(gt[i, :3, 3] - gt[j, :3, 3]))
            candidates.append({'i': i, 'j': j, 'status': c['status'],
                               'place_distance_m': distance, 'near_place': distance <= read(src / 'summary.json')['config']['loop_dist'],
                               'pose_error_m': pe, 'pose_error_deg': re, 'strict_pose': pe < 1 and re < 5})
        ordered = sorted((s['odom_ter_pct'] for s in seg), reverse=True)
        top = max(1, int(np.ceil(.1 * len(ordered))))
        concentration = float(sum(ordered[:top]) / sum(ordered))
        rows[seq] = {'odom': om, 'full': fm, 'segment_top_decile_error_share': concentration,
                     'leave_one_out': leaves, 'same_endpoint_gt_oracle': oracles,
                     'attempted_candidates': candidates}
        print('evaluated', seq, len(seg), 'segments', len(edges), 'edges', flush=True)
    means = {group: {arm: {k: float(np.mean([rows[s][arm][k] for s in seqs])) for k in ('ate', 'ter', 'rer')}
                     for arm in ('odom', 'full')} for group, seqs in
             {'development': ('00', '05', '06'), 'transfer_exposed': ('07', '09', '10')}.items()}
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
    assert peak < 4
    save(BASE / 'results.json', {'rows': rows, 'cohort_means': means,
                                'bank_seal_sha256': sha(BASE / 'bank_seal.json'),
                                'wall_s': time.monotonic() - begin, 'peak_rss_gib': peak})
    verify_bank()
    print('evaluated all; independent validation pending', flush=True)


if __name__ == '__main__':
    {'freeze': freeze, 'bank': bank, 'evaluate': evaluator}[sys.argv[1]]()
