"""Non-destructive legacy-versus-v2 trajectory evaluation evidence."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
HOME = Path('/mnt/e/githouse/RAP-main')
sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
import eval_paper_metrics as new

def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
    legacy = HOME/'.maintenance-archive/2026-09-09-m0/files/RAP-SLAM/scripts/eval_paper_metrics.py'
    spec = importlib.util.spec_from_file_location('legacy_metrics',legacy)
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    rows, details, identities = [], {}, []
    def consume(name, result, gt, files):
        details[name] = result
        for key,path in files.items():
            if key not in result:
                continue
            identities.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            est = new.load_tum(str(path)) if result['kind']=='live' else new.load_kitti_format(str(path))
            legacy_m = old.evaluate_pair(gt,est)
            m = result[key]
            assert abs(legacy_m['ape_unaligned_rmse']-m['ape_unaligned_rmse']) < 1e-9
            assert abs(legacy_m['ape_aligned_rmse']-m['ape_aligned_rmse']) < 1e-9
            rows.append(dict(run=name,trajectory=key,frames=m['n_frames'],
                             ape_first=m['ape_unaligned_rmse'],ape_aligned=m['ape_aligned_rmse'],
                             legacy_lidar_ter=legacy_m['kitti_ter_pct'],new_lidar_ter=m['kitti_ter_pct'],
                             camera_ter=m.get('camera_kitti',{}).get('kitti_ter_pct'),
                             segments=m['kitti_segments'],frame_binding=result['frame_binding']))
    for name,d in [('poss_off','output_prods/poss'),('kitti06_off','output_prods/kitti06'),
                   ('kitti05','output_prods/kitti05'),('kitti00_bb','output_prods/kitti00_bb')]:
        d = ROOT/d
        consume(name,new.eval_offline(str(d)),new.gt_from_summary(str(d)),
                dict(odometry=d/'odom_poses.txt',pgo=d/'optimized_poses.txt'))
    for name,odom,mapped,source,seq in new.LIVE_RUNS:
        if name not in ['step3_poss_current','step3_kitti02_current','step3_kitti06_current','step3_kitti03','step3_kitti04']:
            continue
        odom,mapped = ROOT/odom,ROOT/mapped
        res = new.eval_live(name,str(odom),str(mapped),source,seq,allow_legacy_index=True)
        gt = new.gt_for_live(source,seq,len(new.load_tum(str(odom))))
        consume(name,res,gt,dict(odometry=odom,pgo=mapped))
    for item in identities:
        assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
    report = dict(status='passed',scope='Saved trajectories only; RAP edges and PGO not regenerated',
                  protocol='APE remains LiDAR; camera KITTI uses Tr @ T_lidar @ inv(Tr); v2 all-segment weighting and strict endpoints',
                  frame_limit='Legacy bindings are assumptions, not newly proven acquisition identities. New live evaluations require manifests unless explicitly legacy.',
                  cross_sequence_rule='Report each sequence. Any pooled score must pool segment records; no implicit mean of sequence means.',
                  rows=rows,inputs=identities,details=details)
    (out/'results.json').write_text(json.dumps(report,indent=2))
    lines=['# M2 saved-trajectory metric comparison','',
           'Historical edges and trajectories are unchanged. New metrics are not a full repaired-inference experiment.',
           'APE is the LiDAR first-pose/aligned convention. KITTI camera drift is separately reported.',
           'Live frame identity uses an explicit historical contiguous-index assumption; see JSON bindings.','',
           '| Run | Trajectory | First APE m | Aligned APE m | Legacy LiDAR ter % | V2 LiDAR ter % | Camera ter % | Segments |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        camera='—' if r['camera_ter'] is None else f"{r['camera_ter']:.4f}"
        lines.append(f"| {r['run']} | {r['trajectory']} | {r['ape_first']:.4f} | {r['ape_aligned']:.4f} | {r['legacy_lidar_ter']:.4f} | {r['new_lidar_ter']:.4f} | {camera} | {r['segments']} |")
    (out/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':
    main()
