"""Matched fixed ICP comparison; see the preregistered maintenance protocol."""
import hashlib
import json
from pathlib import Path
import sys
import time
from collections import Counter
from types import SimpleNamespace
import numpy as np
import open3d as o3d

ROOT = Path('/mnt/e/githouse/RAP-SLAM')
BASE = Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-13')
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from rap_slam.rap_backend import RAPBackend
from rap_slam.measurement import make_measurement, rotation_validity
from rap_slam import pose_graph, sequence
import eval_paper_metrics as metrics

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def cloud(points):
    result = o3d.geometry.PointCloud()
    result.points = o3d.utility.Vector3dVector(points.astype(float))
    return result

def register(a, b, initial):
    return o3d.pipelines.registration.registration_icp(
        cloud(b), cloud(a), 2.5, initial,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(
            relative_fitness=1e-6, relative_rmse=1e-6, max_iteration=100)).transformation

def main():
    source = BASE / 'optimization-o3-01'
    out = BASE / 'o3-comparator-01'
    out.mkdir(exist_ok=False)
    (out / 'INCOMPLETE').write_text('Running\n')
    inputs = {}
    def track(path, expected=None):
        digest = sha(path)
        if expected is not None and digest != expected:
            raise ValueError(f'Input identity mismatch: {path}')
        inputs[str(path)] = digest
    for path in [Path(__file__), BASE/'O3_COMPARATOR_PROTOCOL.md',
                 ROOT/'rap_slam/rap_backend.py', ROOT/'rap_slam/measurement.py',
                 ROOT/'rap_slam/pose_graph.py', ROOT/'scripts/eval_paper_metrics.py']:
        track(path)
    rng = np.random.default_rng(7)
    b = rng.normal(size=(500,3))
    angle = .04
    known = np.eye(4)
    known[:3,:3] = [[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]]
    known[:3,3] = [.03,-.02,.01]
    a = b @ known[:3,:3].T + known[:3,3]
    np.testing.assert_allclose(register(a,b,np.eye(4)),known,atol=1e-8,rtol=0)
    prep = SimpleNamespace(voxel_size=.4,remove_outliers=True,max_points_per_scan=4000,
                           seed=42,feature_extractor=None)
    rows=[]
    assert o3d.__version__ == '0.19.0'
    assert not (source/'INCOMPLETE').exists()
    source_identity=json.loads((source/'source_manifest.json').read_text())
    track(source/'source_manifest.json')
    track(Path(__file__).with_name('validate_o3_comparator.py'))
    for path in (ROOT/'rap_slam').glob('*.py'):
        track(path,source_identity.get(str(path)))
    for path,digest in list(inputs.items()):
        if path in source_identity:
            assert digest==source_identity[path],path
    for name in ['poss','kitti06','kitti05','kitti00']:
        src=source/name/'12'
        parent=BASE.parent/'2026-09-11'/('full-'+name+'-01')/'pipeline'
        dest=out/name; dest.mkdir()
        assert not (parent/'INCOMPLETE').exists() and not (parent.parent/'INCOMPLETE').exists()
        for file in ['candidates.json','metrics.json','verification_measurements.jsonl']:
            track(src/file)
        for file in ['summary.json','source_frames.json','odom_poses.txt','keyframes.json']:
            track(parent/file,source_identity[str(parent/file)])
        frames=json.loads((parent/'source_frames.json').read_text())
        ids=frames['source_frame_ids']; paths=frames['scan_files']
        oldhash=source_identity
        candidates=json.loads((src/'candidates.json').read_text())['merged']
        odom=metrics.load_kitti_format(str(parent/'odom_poses.txt'))
        gt=metrics.gt_from_summary(str(parent)); kfs=json.loads((parent/'keyframes.json').read_text())
        cfg=json.loads((parent/'summary.json').read_text())['config']
        for path in [Path(cfg['real_root'])/'dataset/poses'/(cfg['real_seq']+'.txt'),Path(cfg['real_root'])/'dataset/sequences'/cfg['real_seq']/'calib.txt']:
            track(path,source_identity[str(path)])
        assert len(ids)==len(odom)==len(gt)
        def evaluate(poses):
            result=metrics.evaluate_pair(gt,poses,ids)
            if cfg['real_apply_calib']:
                tr=metrics.real_dataset._read_calib_transform(str(Path(cfg['real_root'])/'dataset/sequences'/cfg['real_seq']/'calib.txt'))
                inv=np.linalg.inv(tr)
                result['camera_kitti']=metrics.kitti_drift([tr@p@inv for p in gt],[tr@p@inv for p in poses],source_frame_ids=ids)
            return result
        cache={}; point_hashes={}
        for index in sorted({i for pair in candidates for i in pair}):
            path=paths[index]; track(path,oldhash[path])
            points=np.frombuffer(Path(path).read_bytes(),dtype=np.float32).reshape(-1,4)[:,:3]
            points=points[np.linalg.norm(points,axis=1)>=1.5]
            cache[index]=RAPBackend.preprocess(prep,points)[0]
            point_hashes[str(index)]=hashlib.sha256(cache[index].tobytes()).hexdigest()
        (dest/'preprocessed_hashes.json').write_text(json.dumps(point_hashes,indent=2))
        row={'sequence':name,'odometry':evaluate(odom),
             'rap':json.loads((src/'metrics.json').read_text())['metrics'],'arms':{}}
        for arm in ['identity','odometry']:
            edges=[]; records=[]
            with (dest/(arm+'_attempts.jsonl')).open('x') as stream:
                for i,j in candidates:
                    initial=np.eye(4) if arm=='identity' else np.linalg.inv(odom[i])@odom[j]
                    start=time.perf_counter()
                    try:
                        transform=register(cache[i],cache[j],initial)
                        elapsed=time.perf_counter()-start
                        overlap,dist=RAPBackend._alignment_metrics(cache[i],cache[j],transform)
                        record=make_measurement('o3-comparator-01-'+arm,
                            'kitti' if cfg['real_apply_calib'] else 'poss',cfg['real_seq'],
                            [ids[i],ids[j]],0,dict(T_rel=transform,overlap=overlap,mean_dist=dist),
                            np.linalg.inv(gt[i])@gt[j],dict(method='Open3D point-to-point ICP',version=o3d.__version__))
                        accepted=rotation_validity(transform)['valid'] and overlap>=.7 and dist<=2.5
                        record.update(i=i,j=j,initial=initial.tolist(),accepted=bool(accepted),registration_seconds=elapsed,status='completed')
                        if accepted:
                            edges.append(dict(i=i,j=j,T_rel=transform.tolist(),overlap=overlap,mean_dist=dist,measurement_id=record['measurement_id']))
                    except Exception as error:
                        record=dict(i=i,j=j,initial=initial.tolist(),accepted=False,status='failed',error=repr(error))
                    stream.write(json.dumps(record,allow_nan=False)+'\n'); stream.flush(); records.append(record)
            (dest/(arm+'_edges.json')).write_text(json.dumps(edges,indent=2))
            graph_edges=[dict(e,T_rel=np.asarray(e['T_rel'])) for e in edges]
            optimized=pose_graph.optimize_pose_graph(odom,kfs,graph_edges,loop_weighting='relfloor',robust_kernel='huber',loop_nms_width=0)
            full=np.asarray(pose_graph.propagate_to_full_trajectory(odom,kfs,optimized))
            assert np.isfinite(full).all()
            sequence.save_kitti_poses(full,str(dest/(arm+'_poses.txt')))
            values=dict(candidates=len(candidates),accepted=len(edges),failed=sum(r['status']=='failed' for r in records),
                labels=dict(Counter(r['labels']['label'] for r in records if r['status']=='completed')),
                accepted_labels=dict(Counter(r['labels']['label'] for r in records if r['accepted'])),
                metrics=evaluate(metrics.load_kitti_format(str(dest/(arm+'_poses.txt')))),
                registration_seconds=sum(r.get('registration_seconds',0) for r in records))
            row['arms'][arm]=values
            print(f"{name} {arm}: {len(edges)}/{len(candidates)} accepted, APE {values['metrics']['ape_unaligned_rmse']:.6f}",flush=True)
        (dest/'metrics.json').write_text(json.dumps(row,indent=2)); rows.append(row)
    for path,digest in inputs.items():
        assert sha(path)==digest,path
    (out/'source_manifest.json').write_text(json.dumps(inputs,indent=2))
    (out/'summary.json').write_text(json.dumps(rows,indent=2))
    (out/'validation.json').write_text(json.dumps(dict(synthetic_direction_check=True,input_hashes_rechecked=len(inputs),open3d=o3d.__version__),indent=2))
    lines=['# Matched ICP comparator','', 'First-pose LiDAR APE RMSE (m); frozen frontend and candidate cohort.','',
           '| Sequence | Odometry | RAP | ICP identity (accepted) | ICP odometry (accepted) |','|---|---:|---:|---:|---:|']
    for row in rows:
        cells=[row['sequence'],f"{row['odometry']['ape_unaligned_rmse']:.6f}",f"{row['rap']['ape_unaligned_rmse']:.6f}"]
        for arm in ['identity','odometry']:
            v=row['arms'][arm];cells.append(f"{v['metrics']['ape_unaligned_rmse']:.6f} ({v['accepted']}/{v['candidates']})")
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['','This development cohort is correlated and already observed. ICP odometry uses an additional pose prior. Identity ICP and RAP share no external pose prior but have different internal initialization. Results do not establish superiority over global classical registration. Runtime fields cover ICP registration only. See per-arm logs for all labels, rejected attempts and failures.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    from validate_o3_comparator import validate
    validate(out)
    (out/'INCOMPLETE').unlink()

if __name__=='__main__':
    main()
