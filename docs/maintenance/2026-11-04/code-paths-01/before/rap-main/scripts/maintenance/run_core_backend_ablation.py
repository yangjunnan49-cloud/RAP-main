"""Controlled backend ablation on fixed fresh RAP measurements; no inference."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-11')
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from rap_slam import pose_graph, sequence
import eval_paper_metrics as metrics

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source = BASE / 'm3-logging/core-replay-01'
    out = BASE / 'backend-ablation-01'
    out.mkdir(exist_ok=False)
    (out / 'INCOMPLETE').write_text('Running\n')
    inputs = [BASE / 'CORE_PAPER_PROTOCOL.md', Path(__file__), ROOT / 'rap_slam/pose_graph.py', ROOT / 'scripts/eval_paper_metrics.py']
    rows = []
    arms = [('fixed_plain', 'fixed', None), ('fixed_huber', 'fixed', 'huber'),
            ('relfloor_plain', 'relfloor', None), ('relfloor_huber', 'relfloor', 'huber')]
    for name, folder in [('poss_off','poss'), ('kitti06_off','kitti06'), ('kitti05','kitti05'), ('kitti00','kitti00_bb')]:
        parent = ROOT / 'output_prods' / folder
        edgefile = source / name / 'accepted_loops.json'
        inputs += [edgefile, parent / 'odom_poses.txt', parent / 'keyframes.json', source / name / 'source_frames.json']
        odom = metrics.load_kitti_format(str(parent / 'odom_poses.txt'))
        gt = metrics.gt_from_summary(str(parent))
        kfs = json.loads((parent / 'keyframes.json').read_text())
        edges = json.loads(edgefile.read_text())
        for edge in edges:
            edge['T_rel'] = np.asarray(edge['T_rel'])
        ids = json.loads((source / name / 'source_frames.json').read_text())['source_frame_ids']
        dest = out / name
        dest.mkdir()
        values = {'odometry': metrics.evaluate_pair(gt, odom, ids)}
        for label, weighting, kernel in arms:
            optimized = pose_graph.optimize_pose_graph(odom, kfs, edges, loop_weighting=weighting, robust_kernel=kernel, loop_nms_width=0)
            full = np.asarray(pose_graph.propagate_to_full_trajectory(odom, kfs, optimized))
            assert np.isfinite(full).all()
            if label == 'relfloor_huber':
                previous = metrics.load_kitti_format(str(source / name / 'optimized_poses.txt'))
                np.testing.assert_allclose(full, previous, atol=1e-8, rtol=0)
            sequence.save_kitti_poses(full, str(dest / (label + '.txt')))
            values[label] = metrics.evaluate_pair(gt, full, ids)
        (dest / 'metrics.json').write_text(json.dumps(values, indent=2))
        rows.append({'sequence': name, 'first_pose_ape_m': {k:v['ape_unaligned_rmse'] for k,v in values.items()}, 'aligned_ape_m': {k:v['ape_aligned_rmse'] for k,v in values.items()}})
    (out / 'source_manifest.json').write_text(json.dumps({str(p):sha(p) for p in inputs}, indent=2))
    (out / 'summary.json').write_text(json.dumps(rows, indent=2))
    lines = ['# Controlled backend ablation', '', 'First-pose LiDAR APE RMSE (m). Same fresh edges and frozen frontend in every arm.', '', '| Sequence | Odometry | Fixed | Fixed + Huber | Relfloor | Relfloor + Huber |', '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        lines.append('| ' + row['sequence'] + ' | ' + ' | '.join(f'{v:.6f}' for v in row['first_pose_ape_m'].values()) + ' |')
    lines += ['', 'All four default-arm trajectories reproduce core-replay-01 within 1e-8 absolute tolerance. All 40 input edges are labeled safe; this is not a false-loop robustness test.']
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    (out / 'INCOMPLETE').unlink()
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
