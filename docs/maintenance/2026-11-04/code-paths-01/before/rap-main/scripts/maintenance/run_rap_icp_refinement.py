"""O1 fixed RAP-initialized ICP arm on the complete fresh core baseline."""
import json
from pathlib import Path
import time
from collections import Counter
import numpy as np
from run_registration_comparator import ROOT,BASE,sha,register,RAPBackend,pose_graph,sequence,metrics
from rap_slam.measurement import make_measurement,rotation_validity
from types import SimpleNamespace

def main():
    out=BASE/'optimization-o1-01';out.mkdir(exist_ok=False)
    (out/'INCOMPLETE').write_text('Refinement pending\n')
    identities={str(p):sha(p) for p in [Path(__file__),BASE/'OPTIMIZATION_ENTRY_PROTOCOL.md',Path(__file__).with_name('run_registration_comparator.py'),ROOT/'rap_slam/rap_backend.py',ROOT/'rap_slam/pose_graph.py',ROOT/'rap_slam/measurement.py',ROOT/'scripts/eval_paper_metrics.py']}
    rows=[]
    prep=SimpleNamespace(voxel_size=.4,remove_outliers=True,max_points_per_scan=4000,seed=42,feature_extractor=None)
    for name in ['poss','kitti06','kitti05','kitti00']:
        parent=BASE/('full-'+name+'-01');src=parent/'pipeline';dest=out/name;dest.mkdir()
        assert not (parent/'INCOMPLETE').exists()
        cfg=json.loads((src/'summary.json').read_text())['config']
        frames=json.loads((src/'source_frames.json').read_text());ids=frames['source_frame_ids']
        events=[json.loads(s) for s in (src/'verification_measurements.jsonl').read_text().splitlines()]
        starts={e['attempt_id']:e for e in events if e['event']=='candidate_started'}
        measurements={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
        selected=[(starts[e['attempt_id']],measurements[e['selected_measurement_id']]) for e in events if e['event']=='candidate_finished']
        gt=metrics.gt_from_summary(str(src));odom=metrics.load_kitti_format(str(src/'odom_poses.txt'))
        kfs=json.loads((src/'keyframes.json').read_text());cache={}
        input_hashes=json.loads((parent/'input_manifest.json').read_text())
        for file in ['summary.json','verification_measurements.jsonl','source_frames.json','odom_poses.txt','keyframes.json']:
            identities[str(src/file)]=sha(src/file)
        for index in sorted({v for a,r in selected for v in [a['i'],a['j']]}):
            path=frames['scan_files'][index];digest=sha(path);assert digest==input_hashes[path];identities[path]=digest
            points=np.frombuffer(Path(path).read_bytes(),dtype=np.float32).reshape(-1,4)[:,:3]
            cache[index]=RAPBackend.preprocess(prep,points[np.linalg.norm(points,axis=1)>=1.5])[0]
        records=[];edges=[]
        with (dest/'measurements.jsonl').open('x') as stream:
            for attempt,original in selected:
                i,j=attempt['i'],attempt['j'];start=time.perf_counter()
                transform=register(cache[i],cache[j],np.asarray(original['T_rel']))
                elapsed=time.perf_counter()-start
                overlap,dist=RAPBackend._alignment_metrics(cache[i],cache[j],transform)
                record=make_measurement('optimization-o1-01','kitti' if cfg['real_apply_calib'] else 'poss',cfg['real_seq'],[ids[i],ids[j]],0,
                    dict(T_rel=transform,overlap=overlap,mean_dist=dist),np.linalg.inv(gt[i])@gt[j],
                    dict(method='RAP initialized ICP',parent_measurement_id=original['measurement_id']))
                assert rotation_validity(transform)['valid']
                accepted=overlap>=.7 and dist<=2.5
                record.update(i=i,j=j,accepted=accepted,registration_seconds=elapsed,initial_T_rel=original['T_rel'])
                stream.write(json.dumps(record)+'\n');stream.flush();records.append(record)
                if accepted:edges.append(dict(i=i,j=j,T_rel=transform.tolist(),overlap=overlap,mean_dist=dist,measurement_id=record['measurement_id']))
        (dest/'accepted_loops.json').write_text(json.dumps(edges,indent=2))
        optimized=pose_graph.optimize_pose_graph(odom,kfs,[dict(e,T_rel=np.asarray(e['T_rel'])) for e in edges],loop_weighting='relfloor',robust_kernel='huber',loop_nms_width=0)
        full=np.asarray(pose_graph.propagate_to_full_trajectory(odom,kfs,optimized));assert np.isfinite(full).all()
        sequence.save_kitti_poses(full,str(dest/'optimized_poses.txt'))
        baseline=json.loads((parent/'paper_metrics.json').read_text())['pgo']
        result=metrics.evaluate_pair(gt,full,ids)
        if cfg['real_apply_calib']:
            tr=metrics.real_dataset._read_calib_transform(str(Path(cfg['real_root'])/'dataset/sequences'/cfg['real_seq']/'calib.txt'));inv=np.linalg.inv(tr)
            result['camera_kitti']=metrics.kitti_drift([tr@p@inv for p in gt],[tr@p@inv for p in full],source_frame_ids=ids)
        row=dict(sequence=name,baseline=baseline,refined=result,accepted=len(edges),attempts=len(records),
            accepted_labels=dict(Counter(r['labels']['label'] for r in records if r['accepted'])),
            refinement_seconds=sum(r['registration_seconds'] for r in records))
        (dest/'metrics.json').write_text(json.dumps(row,indent=2));rows.append(row)
        print(name,baseline['ape_unaligned_rmse'],result['ape_unaligned_rmse'],flush=True)
    for p,h in identities.items():assert sha(p)==h
    changes=[r['refined']['ape_unaligned_rmse']/r['baseline']['ape_unaligned_rmse']-1 for r in rows]
    passed=sum(v<0 for v in changes)>=3 and max(changes)<=.05 and all(r['accepted_labels'].get('dangerous',0)==0 for r in rows)
    (out/'summary.json').write_text(json.dumps(dict(screen_passed=passed,relative_ape_changes=changes,sequences=rows,source_hashes=identities),indent=2))
    lines=['# O1: RAP-initialized ICP refinement','',f'Predeclared practical screen passed: {passed}. Production default unchanged.','',
        '| Sequence | RAP first APE m | Refined first APE m | RAP aligned APE m | Refined aligned APE m | Accepted |','|---|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['sequence']} | {r['baseline']['ape_unaligned_rmse']:.6f} | {r['refined']['ape_unaligned_rmse']:.6f} | {r['baseline']['ape_aligned_rmse']:.6f} | {r['refined']['ape_aligned_rmse']:.6f} | {r['accepted']}/{r['attempts']} |")
    lines+=['','| Sequence | Drift frame | RAP translation % | Refined translation % | Additional ICP seconds |','|---|---|---:|---:|---:|']
    for r in rows:
        a=r['baseline'].get('camera_kitti',r['baseline']);b=r['refined'].get('camera_kitti',r['refined'])
        frame='camera' if 'camera_kitti' in r['baseline'] else 'LiDAR (POSS)'
        lines.append(f"| {r['sequence']} | {frame} | {a['kitti_ter_pct']:.6f} | {b['kitti_ter_pct']:.6f} | {r['refinement_seconds']:.3f} |")
    lines+=['','Same pairs, fixed local refinement, freshly measured gate diagnostics, same backend. No GT-based selection. See JSON for individual measurements. This development screen is not independent validation. Refinement runtime excludes loading/preprocessing and is additional to baseline registration.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n');(out/'INCOMPLETE').unlink();print('\n'.join(lines))

if __name__=='__main__':main()
