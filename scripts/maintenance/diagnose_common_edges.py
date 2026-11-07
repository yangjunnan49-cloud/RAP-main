"""Post-hoc O3 common-measurement-fixed PGO; no GT-based selection."""
from run_budget_comparison import ROOT, HOME, BASE, sha, save, metrics, pose_graph, sequence
from pathlib import Path
import json
import numpy as np


def main():
    out = BASE/'o3-common-fixed-01'
    out.mkdir(exist_ok=False)
    (out/'INCOMPLETE').write_text('Diagnostic pending\n')
    inputs = {str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('run_budget_comparison.py'),
        BASE/'O3_DIAGNOSTIC_PROTOCOL.md',ROOT/'rap_slam/pose_graph.py',ROOT/'scripts/eval_paper_metrics.py']}
    rows=[]
    for name in ['poss','kitti06','kitti05','kitti00']:
        parent = HOME/'docs/maintenance/2026-09-11'/('full-'+name+'-01')/'pipeline'
        a = BASE/'optimization-o2-01'/name/'12'
        b = BASE/'optimization-o3-01'/name/'12'
        for directory in [BASE/'optimization-o2-01',BASE/'optimization-o3-01']:
            assert not (directory/'INCOMPLETE').exists()
        for p in [a/'accepted_loops.json',b/'accepted_loops.json',a/'metrics.json',b/'metrics.json',parent/'summary.json',parent/'odom_poses.txt',parent/'keyframes.json',parent/'source_frames.json']:
            inputs[str(p)]=sha(p)
        old={(e['i'],e['j']):e for e in json.loads((a/'accepted_loops.json').read_text())}
        proposed=json.loads((b/'accepted_loops.json').read_text())
        reused=[old.get((e['i'],e['j']),e) for e in proposed]
        edges=[e for e in reused if e['overlap']>=.7 and e['mean_dist']<=2.5]
        dest=out/name;dest.mkdir()
        save(dest/'reused_edges.json',edges)
        odom=metrics.load_kitti_format(str(parent/'odom_poses.txt'))
        gt=metrics.gt_from_summary(str(parent))
        kfs=json.loads((parent/'keyframes.json').read_text())
        ids=json.loads((parent/'source_frames.json').read_text())['source_frame_ids']
        cfg=json.loads((parent/'summary.json').read_text())['config']
        for p in [Path(cfg['real_root'])/'dataset/poses'/(cfg['real_seq']+'.txt'),Path(cfg['real_root'])/'dataset/sequences'/cfg['real_seq']/'calib.txt']:
            inputs[str(p)]=sha(p)
        optimized=pose_graph.optimize_pose_graph(odom,kfs,[dict(e,T_rel=np.asarray(e['T_rel'])) for e in edges],loop_weighting='relfloor',robust_kernel='huber',loop_nms_width=0)
        full=np.asarray(pose_graph.propagate_to_full_trajectory(odom,kfs,optimized))
        assert np.isfinite(full).all()
        sequence.save_kitti_poses(full,str(dest/'optimized_poses.txt'))
        saved=metrics.load_kitti_format(str(dest/'optimized_poses.txt'))
        m=metrics.evaluate_pair(gt,saved,ids)
        if cfg['real_apply_calib']:
            tr=metrics.real_dataset._read_calib_transform(str(Path(cfg['real_root'])/'dataset/sequences'/cfg['real_seq']/'calib.txt'))
            inv=np.linalg.inv(tr)
            m['camera_kitti']=metrics.kitti_drift([tr@p@inv for p in gt],[tr@p@inv for p in saved],source_frame_ids=ids)
        row=dict(sequence=name,baseline=json.loads((a/'metrics.json').read_text())['metrics'],
            o3=json.loads((b/'metrics.json').read_text())['metrics'],common_fixed=m,accepted=len(edges),
            common_reused=sum((e['i'],e['j']) in old for e in proposed))
        save(dest/'metrics.json',row);rows.append(row)
    for p,h in inputs.items():assert sha(p)==h
    save(out/'summary.json',dict(sequences=rows,input_hashes=inputs))
    lines=['# Post-hoc common-edge-fixed O3 diagnostic','',
        'Same O3 selected pairs; common edges use exact O2 measurements. New pairs keep O3 measurements. No new RAP inference, GT selection or production change. All original attempts were accepted; no rejected candidate is omitted in this cohort. This is a diagnostic, not the preregistered O3 arm.','',
        '| Sequence | O2 first APE m | O3 first APE m | Common-fixed first APE m |','|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['sequence']} | {r['baseline']['ape_unaligned_rmse']:.6f} | {r['o3']['ape_unaligned_rmse']:.6f} | {r['common_fixed']['ape_unaligned_rmse']:.6f} |")
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (out/'INCOMPLETE').unlink()
    print('\n'.join(lines))


if __name__=='__main__':main()
