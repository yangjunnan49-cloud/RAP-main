"""Independent E0 opportunity audit checks; reads frozen bank and evaluator output."""
import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

import numpy as np

MAIN = Path('/mnt/e/githouse/RAP-main')
ROOT = MAIN.parent / 'RAP-SLAM'
DATA = MAIN.parent / 'Datasets/data_odometry_velodyne/dataset'
BASE = MAIN / 'docs/maintenance/2026-09-29/system-opportunity-audit-01'
BANK = BASE / 'attempt-01'
EVAL = BASE / 'evaluation-01'
SEQS = ('00', '05', '06', '07', '09', '10')
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def check_close(a, b, tol=1e-8):
    assert math.isfinite(float(a)) and math.isfinite(float(b))
    assert abs(float(a) - float(b)) <= tol, (a, b)


def source(seq):
    p = '2026-09-26/e0-frontend-01' if seq in SEQS[:3] else '2026-09-27/e0-heldout-01'
    return MAIN / 'docs/maintenance' / p / f'full-{seq}-A'


def load_pose_txt(p):
    a = np.loadtxt(p).reshape(-1, 3, 4)
    out = np.tile(np.eye(4), (len(a), 1, 1))
    out[:, :3] = a
    return out


def compact_metric(gt, tr, est):
    import eval_paper_metrics as epm
    lidar = epm.evaluate_pair(list(gt), list(est), list(range(len(gt))))
    cg, ce = tr @ gt @ np.linalg.inv(tr), tr @ est @ np.linalg.inv(tr)
    camera = epm.evaluate_pair(list(cg), list(ce), list(range(len(gt))))
    return {'ate': lidar['ape_aligned_rmse'], 'ter': camera['kitti_ter_pct'],
            'rer': camera['kitti_rer_deg100m'], 'segment_count': camera['kitti_segments']}


def main():
    from rap_slam import pose_graph
    from rap_slam.real_dataset import load_gt_poses, _read_calib_transform
    begin = time.monotonic()
    freeze, seal, result = (read(BASE / n) for n in ('freeze.json', 'bank_seal.json', 'results.json'))
    assert list(result['rows']) == list(SEQS)
    for p, h in freeze['files'].items():
        assert digest(p) == h, p
    assert seal['freeze_sha256'] == digest(BASE / 'freeze.json')
    assert result['bank_seal_sha256'] == digest(BASE / 'bank_seal.json')
    files = {str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    assert files == set(seal['files'])
    for rel, h in seal['files'].items():
        assert digest(BANK / rel) == h, rel
    checks = ['frozen identity and sealed GT-free bank hashes']
    attempts = accepted = 0
    for seq in SEQS:
        src, bd, ed = source(seq), BANK / seq, EVAL / seq
        odom = load_pose_txt(src / 'odom_poses.txt')
        full = np.load(bd / 'baseline.npy')
        saved = load_pose_txt(src / 'optimized_poses.txt')
        assert odom.shape == full.shape == saved.shape
        assert np.max(np.abs(full - saved)) <= 1e-5
        assert read(src / 'source_frames.json')['source_frame_ids'] == list(range(len(odom)))
        kf = read(src / 'keyframes.json')
        edges = read(bd / 'edges.json')
        candidates = read(bd / 'candidates.json')
        assert all(set(e) == {'i', 'j', 'T_rel', 'overlap', 'mean_dist', 'measurement_id'} for e in edges)
        assert all(set(c) == {'i', 'j', 'attempt_id', 'status', 'selected_measurement_id', 'T_rel', 'overlap', 'mean_dist'} for c in candidates)
        assert all(e['i'] in kf and e['j'] in kf for e in edges)
        assert sum(c['status'] == 'accepted' for c in candidates) == len(edges)
        assert len({c['attempt_id'] for c in candidates}) == len(candidates)
        assert len({e['measurement_id'] for e in edges}) == len(edges)
        attempts += len(candidates)
        accepted += len(edges)
        row = result['rows'][seq]
        assert len(row['leave_one_out']) == len(row['same_endpoint_gt_oracle']) == len(edges)
        assert len(row['attempted_candidates']) == len(candidates)
        calib = DATA / 'sequences' / seq / 'calib.txt'
        gt = np.asarray(load_gt_poses(str(DATA / 'poses' / f'{seq}.txt'), str(calib), apply_calib=True))
        tr = _read_calib_transform(str(calib))
        assert gt.shape == full.shape
        for label, trajectory in (('odom', odom), ('full', full)):
            actual = compact_metric(gt, tr, trajectory)
            for key in actual:
                check_close(actual[key], row[label][key])
        segments = read(ed / 'segments.json')
        assert len(segments) == row['full']['segment_count'] == row['odom']['segment_count']
        check_close(np.mean([s['odom_ter_pct'] for s in segments]), row['odom']['ter'])
        check_close(np.mean([s['full_ter_pct'] for s in segments]), row['full']['ter'])
        check_close(np.mean([s['odom_rer_deg100m'] for s in segments]), row['odom']['rer'])
        check_close(np.mean([s['full_rer_deg100m'] for s in segments]), row['full']['rer'])
        ordered = sorted((s['odom_ter_pct'] for s in segments), reverse=True)
        top = max(1, math.ceil(.1 * len(ordered)))
        check_close(sum(ordered[:top]) / sum(ordered), row['segment_top_decile_error_share'])
        if edges:
            idx = 0
            opt = pose_graph.optimize_pose_graph(list(odom), kf, edges[1:])
            repro = np.asarray(pose_graph.propagate_to_full_trajectory(list(odom), kf, opt))
            np.testing.assert_allclose(repro, np.load(bd / 'omit-000.npy'), rtol=0, atol=1e-9)
            leave = compact_metric(gt, tr, repro)
            for key in leave:
                check_close(leave[key], row['leave_one_out'][idx]['metrics'][key])
            oracle = [dict(e) for e in edges]
            truth = np.linalg.inv(gt[oracle[0]['i']]) @ gt[oracle[0]['j']]
            oracle[0]['T_rel'] = truth.tolist()
            opt = pose_graph.optimize_pose_graph(list(odom), kf, oracle)
            repro = np.asarray(pose_graph.propagate_to_full_trajectory(list(odom), kf, opt))
            np.testing.assert_allclose(repro, np.load(ed / 'oracle-000.npy'), rtol=0, atol=1e-9)
            val = compact_metric(gt, tr, repro)
            for key in val:
                check_close(val[key], row['same_endpoint_gt_oracle'][idx]['metrics'][key])
        else:
            assert seq == '10' and len(list(ed.glob('oracle-*.npy'))) == 0
        for c, label in zip(candidates, row['attempted_candidates']):
            assert (c['i'], c['j'], c['status']) == (label['i'], label['j'], label['status'])
            truth = np.linalg.inv(gt[c['i']]) @ gt[c['j']]
            diff = np.linalg.inv(np.asarray(c['T_rel'])) @ truth
            trans = np.linalg.norm(diff[:3, 3])
            rot = np.degrees(np.arccos(np.clip((np.trace(diff[:3, :3]) - 1) / 2, -1, 1)))
            place = np.linalg.norm(gt[c['i'], :3, 3] - gt[c['j'], :3, 3])
            check_close(trans, label['pose_error_m'])
            check_close(rot, label['pose_error_deg'])
            check_close(place, label['place_distance_m'])
            assert label['near_place'] == (place <= read(src / 'summary.json')['config']['loop_dist'])
            assert label['strict_pose'] == (trans < 1 and rot < 5)
        checks.append(f'{seq}: baseline/segments/candidates and first edge omission+oracle')
    assert attempts == 71 and accepted == 58
    assert len(read(BANK / '10/candidates.json')) == 11 and len(read(BANK / '10/edges.json')) == 0
    for group, seqs in (('development', SEQS[:3]), ('transfer_exposed', SEQS[3:])):
        for arm in ('odom', 'full'):
            for key in ('ate', 'ter', 'rer'):
                check_close(np.mean([result['rows'][s][arm][key] for s in seqs]),
                            result['cohort_means'][group][arm][key])
    total_wall = read(BANK / 'bank_execution.json')['wall_s'] + result['wall_s'] + time.monotonic() - begin
    peak_gib = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20,
                   read(BANK / 'bank_execution.json')['peak_rss_gib'], result['peak_rss_gib'])
    bytes_used = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert total_wall < 3600 and peak_gib < 4 and bytes_used < 2**30
    for p, h in freeze['files'].items():
        assert digest(p) == h, p
    report = ['# E0 A full-system metric opportunity audit', '',
              'Status: **VALIDATED evaluator-only diagnostic**. No new RAP inference, training or production edit.', '',
              '| Sequence | Accepted/attempted | Odom ter % | Full ter % | Odom ATE m | Full ATE m |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for seq in SEQS:
        r = result['rows'][seq]
        report.append(f"| {seq} | {len(r['same_endpoint_gt_oracle'])}/{len(r['attempted_candidates'])} | "
                      f"{r['odom']['ter']:.6f} | {r['full']['ter']:.6f} | "
                      f"{r['odom']['ate']:.6f} | {r['full']['ate']:.6f} |")
    report += ['', 'Segment, leave-one-edge-out, same-endpoint GT replacement and online attempted-candidate'
               ' records are in `results.json` and `evaluation-01`. Omission effects are nonadditive;'
               ' oracle replacements are not executable improvements or a global ceiling.',
               'The verification log covers RAP attempts, not the complete retrieval shortlist.'
               ' F2 balanced pairs are a different distribution from this online E0 arm.',
               f'Independent validator passed {len(checks)} check groups. Bank+evaluator+validator wall '
               f'{total_wall:.2f}s; maximum stage peak RSS {peak_gib:.3f}GiB; audit artifact size '
               f'{bytes_used/2**20:.2f}MiB. These resources exclude prior E0 generation.',
               'The owner requires an original RAP-centred metric improvement; this diagnostic alone makes no method claim.']
    (BASE / 'REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    with (BASE / 'validation.json').open('x') as f:
        json.dump({'passed': True, 'check_groups': checks, 'attempts': attempts, 'accepted': accepted,
                   'wall_s': total_wall, 'maximum_stage_peak_rss_gib': peak_gib,
                   'audit_artifact_bytes_before_report': bytes_used}, f, indent=2)
    (BASE / 'INCOMPLETE').unlink()
    print('validated', len(checks), 'groups; wall', total_wall, flush=True)


if __name__ == '__main__':
    main()
