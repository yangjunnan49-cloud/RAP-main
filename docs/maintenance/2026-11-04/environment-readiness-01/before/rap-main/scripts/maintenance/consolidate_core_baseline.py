"""Freeze the completed four-sequence baseline and reconcile existing metrics."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
BASE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-11')
ROOT=Path('/mnt/e/githouse/RAP-SLAM')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import eval_paper_metrics as metrics

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compact(m):
    return {k:v for k,v in m.items() if k in ['ape_unaligned_rmse','ape_aligned_rmse','kitti_ter_pct','kitti_rer_deg100m','kitti_segments','n_frames']}

def main():
    out=BASE/'core-baseline-v1';out.mkdir(exist_ok=False)
    (out/'INCOMPLETE').write_text('Consolidation pending\n')
    rows=[];identities={}
    for name,legacy,replay in [('poss','poss','poss_off'),('kitti06','kitti06','kitti06_off'),('kitti05','kitti05','kitti05'),('kitti00','kitti00_bb','kitti00')]:
        run=BASE/('full-'+name+'-01');pipeline=run/'pipeline';parent=ROOT/'output_prods'/legacy
        assert not (run/'INCOMPLETE').exists() and not (pipeline/'INCOMPLETE').exists()
        val=json.loads((run/'validation.json').read_text());m=json.loads((run/'paper_metrics.json').read_text())
        summary=json.loads((pipeline/'summary.json').read_text())
        fresh_odom=metrics.load_kitti_format(str(pipeline/'odom_poses.txt'))
        old_odom=metrics.load_kitti_format(str(parent/'odom_poses.txt'))
        old=json.loads((BASE/'legacy-metric-recheck-01/results.json').read_text())
        oldname={'poss':'poss_off','kitti06':'kitti06_off','kitti05':'kitti05','kitti00':'kitti00_bb'}[name]
        previous=json.loads((BASE/'m3-logging/core-replay-01'/replay/'metrics.json').read_text())
        fresh_edges=json.loads((pipeline/'accepted_loops.json').read_text())
        prior_pairs=json.loads((BASE/'m3-logging/core-replay-01'/replay/'candidates.json').read_text())['merged']
        events=[json.loads(s) for s in (pipeline/'verification_measurements.jsonl').read_text().splitlines()]
        starts=[e for e in events if e['event']=='candidate_started']
        pairs=[[e['i'],e['j']] for e in starts]
        gen={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
        for e in events:
            if e['event']=='candidate_finished':
                r=gen[e['selected_measurement_id']]
                assert (e['status']=='accepted')==(r['overlap']>=.7 and r['mean_dist']<=2.5)
        row=dict(sequence=name,run=str(run),frames=val['frames'],accepted=val['accepted'],
            odometry=compact(m['odometry']),pgo=compact(m['pgo']),
            camera_odometry=compact(m['odometry'].get('camera_kitti',{})),camera_pgo=compact(m['pgo'].get('camera_kitti',{})),
            legacy_pgo=compact(old['details'][oldname]['pgo']),replay_pgo=compact(previous['fresh_pgo']),
            odometry_max_abs_delta=float(np.max(np.abs(np.asarray(fresh_odom)-np.asarray(old_odom)))),
            odometry_file_identical=sha(pipeline/'odom_poses.txt')==sha(parent/'odom_poses.txt'),
            candidates_match_replay=pairs==prior_pairs,
            timings_s=summary['timings_s'],total_runtime_s=summary['total_runtime_s'],
            subprocess_monotonic_seconds=json.loads((run/'process.json').read_text())['wall_seconds'],
            validation=val,config=summary['config'])
        rows.append(row)
        for p in [run/'validation.json',run/'input_manifest.json',run/'paper_metrics.json',pipeline/'summary.json',pipeline/'odom_poses.txt',pipeline/'optimized_poses.txt',pipeline/'accepted_loops.json',pipeline/'source_frames.json']:
            identities[str(p)]=sha(p)
    old=json.loads((BASE/'legacy-metric-recheck-01/results.json').read_text())
    prior=json.loads((BASE.parent/'2026-09-10/m2-evaluation/recompute-01/results.json').read_text())
    assert len(old['rows'])==len(prior['rows'])
    for a,b in zip(old['rows'],prior['rows']):
        assert (a['run'],a['trajectory'])==(b['run'],b['trajectory'])
        for key in ['ape_first','ape_aligned','legacy_lidar_ter','new_lidar_ter','camera_ter','segments']:
            if a[key] is None:assert b[key] is None
            else:np.testing.assert_allclose(a[key],b[key],atol=1e-9,rtol=0)
    identities[str(BASE/'legacy-metric-recheck-01/results.json')]=sha(BASE/'legacy-metric-recheck-01/results.json')
    (out/'registry.json').write_text(json.dumps(dict(baseline='core-offline-v1',sequences=rows,legacy_rows_rechecked=len(old['rows']),source_hashes=identities),indent=2))
    lines=['# Core offline optimization baseline v1','',
       'Audit-only work is closed for the scoped four-sequence offline core. All raw-scan reruns and necessary metric checks passed. Optimize against this baseline; keep legacy live/Spires/statistical claims deferred.','',
       '| Sequence | Frames | Loops | Odom APE m | RAP APE m | Aligned RAP APE m | Pipeline s |','|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['sequence']} | {r['frames']} | {r['accepted']} | {r['odometry']['ape_unaligned_rmse']:.6f} | {r['pgo']['ape_unaligned_rmse']:.6f} | {r['pgo']['ape_aligned_rmse']:.6f} | {r['total_runtime_s']:.2f} |")
    lines+=['','APE uses LiDAR first-pose alignment; aligned APE is a separate metric. No sequence pooling.','',
        '| Sequence | Drift frame | Odom translation % | RAP translation % | RAP rotation deg/100m | Segments |','|---|---|---:|---:|---:|---:|']
    for r in rows:
        a,b=(r['camera_odometry'],r['camera_pgo']) if r['camera_pgo'] else (r['odometry'],r['pgo'])
        frame='camera' if r['camera_pgo'] else 'LiDAR (custom POSS)'
        lines.append(f"| {r['sequence']} | {frame} | {a['kitti_ter_pct']:.6f} | {b['kitti_ter_pct']:.6f} | {b['kitti_rer_deg100m']:.6f} | {b['kitti_segments']} |")
    lines+=['','## Legacy reconciliation','',f"All {len(old['rows'])} saved-trajectory metric rows reproduce the earlier M2 corrected values within 1e-9. No new ROS/live acquisition identity is claimed.",'',
        '| Sequence | Legacy PGO APE | Fresh frozen replay APE | Full rerun APE | Odom max element change | Same candidate order |','|---|---:|---:|---:|---:|---|']
    for r in rows:lines.append(f"| {r['sequence']} | {r['legacy_pgo']['ape_unaligned_rmse']:.6f} | {r['replay_pgo']['ape_unaligned_rmse']:.6f} | {r['pgo']['ape_unaligned_rmse']:.6f} | {r['odometry_max_abs_delta']:.3g} | {r['candidates_match_replay']} |")
    lines+=['','KITTI 00 legacy used budget 40; new core uses 12. This difference cannot be attributed to a numerical repair. Old drift used length-macro aggregation; use the M2 v2 all-segment values. Old map/crispness, conformal and N-way conclusions remain legacy unless independently regenerated.','',
        'Single-run timings include map export and warm reads. Production stages use time.time; differences from the monotonic subprocess duration (also saved in registry.json) indicate clock-accounting uncertainty. Do not use these stage totals as a precise throughput benchmark or rerun solely to improve timing precision. These are development sequences; no generalization guarantee. Source/config/input identities are in registry.json and each run manifest.','',
        'Next: optimize measured trajectory quality. First bounded experiment: RAP-initialized local ICP refinement with same candidates and remeasured gate diagnostics; then candidate coverage/budget if useful. Do not spend more time tuning robust kernels on this clean cohort (previous ablation was negligible).']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n');(out/'INCOMPLETE').unlink()
    print('\n'.join(lines),flush=True)

if __name__=='__main__':main()
