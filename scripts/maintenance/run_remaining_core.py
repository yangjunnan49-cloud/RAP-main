"""Execute and validate the predeclared complete KITTI 06 core pipeline."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from collections import Counter
import numpy as np

ROOT=Path('/mnt/e/githouse/RAP-SLAM')
BASE=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-11')
DATA=Path('/mnt/e/githouse/Datasets/data_odometry_velodyne')
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import eval_paper_metrics as metrics
from rap_slam.measurement import transform_label

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def run(name, data_root, sequence_id, first, last, apply_calib):
    out=BASE/('full-'+name+'-01');out.mkdir(exist_ok=False)
    (out/'INCOMPLETE').write_text('Pipeline and validation pending\n')
    dest=out/'pipeline'
    data=Path(data_root); seq=data/'dataset/sequences'/sequence_id; ids=list(range(first,last+1))
    scans=[seq/'velodyne'/f'{i:06d}.bin' for i in ids]
    sources=list((ROOT/'rap_slam').glob('*.py'))+[ROOT/'scripts/run_pipeline.py',ROOT/'scripts/eval_paper_metrics.py',
        Path(__file__),BASE/'FULL_CORE_COMPLETION_PROTOCOL.md',seq/'calib.txt',data/'dataset/poses'/(sequence_id+'.txt')]
    sources+=list(Path('/mnt/e/githouse/RAP-main/rectified_point_flow').rglob('*.py'))
    sources+=list(Path('/mnt/e/githouse/RAP-main/config').rglob('*.yaml'))
    sources+=[Path('/mnt/e/githouse/RAP-main/weights')/n for n in ['rap_model_12.ckpt','mini_spinnet_t.pth']]
    if (seq/'times.txt').exists():sources.append(seq/'times.txt')
    identities={str(p):sha(p) for p in sources+scans}
    (out/'input_manifest.json').write_text(json.dumps(identities,indent=2))
    cmd=[sys.executable,'-B',str(ROOT/'scripts/run_pipeline.py'),
         '--output',str(dest),'--source','real','--real-root',str(data),'--real-seq',sequence_id,
         '--real-start',str(first),'--real-end',str(last),'--real-stride','1',
         '--odom-max-range','80','--kf-trans','6','--kf-rot','12','--loop-method','both',
         '--loop-dist','15','--loop-sep','200','--max-candidates','12',
         '--sc-dist-thresh','.25','--sc-shortlist','10','--sc-rings','20','--sc-sectors','60','--sc-max-radius','80',
         '--seed','42','--rap-steps','5','--rap-max-points','4000','--rap-voxel','.4',
         '--multigen-k','1','--gate-mode','heuristic','--min-overlap','.7','--max-mean-dist','2.5',
         '--loop-weighting','relfloor','--relfloor-ref','1','--relfloor-cap','3',
         '--robust-kernel','huber','--huber-k','1','--loop-nms-width','0']
    if apply_calib: cmd.append('--real-apply-calib')
    (out/'command.json').write_text(json.dumps(dict(argv=cmd,cwd=str(ROOT),threads={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS']}),indent=2))
    print('Preflight hashes complete; starting full pipeline',flush=True)
    start=time.perf_counter()
    with (out/'pipeline.log').open('x') as log:
        result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    wall=time.perf_counter()-start
    (out/'process.json').write_text(json.dumps(dict(returncode=result.returncode,wall_seconds=wall),indent=2))
    result.check_returncode()
    assert not (dest/'INCOMPLETE').exists()
    summary=json.loads((dest/'summary.json').read_text())
    frames=json.loads((dest/'source_frames.json').read_text())
    assert frames['source_frame_ids']==ids
    assert frames['scan_files']==list(map(str,scans))
    if frames['timestamps'] is not None:
        np.testing.assert_array_equal(frames['timestamps'],np.loadtxt(seq/'times.txt')[ids])
    assert summary['n_scans']==len(ids) and summary['odometry_backend']=='kiss-icp'
    kfs=json.loads((dest/'keyframes.json').read_text());assert kfs[-1]==len(ids)-1
    events=[json.loads(s) for s in (dest/'verification_measurements.jsonl').read_text().splitlines()]
    starts={e['attempt_id']:e for e in events if e['event']=='candidate_started'}
    ends={e['attempt_id']:e for e in events if e['event']=='candidate_finished'}
    generations={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
    assert starts.keys()==ends.keys() and len(starts)==summary['n_loop_candidates']
    assert all(e['status'] in ['accepted','rejected'] for e in ends.values())
    edges=json.loads((dest/'accepted_loops.json').read_text())
    assert {e['measurement_id'] for e in edges}=={e['selected_measurement_id'] for e in ends.values() if e['status']=='accepted'}
    gt=metrics.gt_from_summary(str(dest))
    for e in edges:
        r=generations[e['measurement_id']]
        np.testing.assert_array_equal(e['T_rel'],r['T_rel'])
        assert r['source_frame_ids']==[ids[e['i']],ids[e['j']]]
    for r in generations.values():
        i,j=[v-first for v in r['source_frame_ids']];label=transform_label(r['T_rel'],np.linalg.inv(gt[i])@gt[j])
        assert label['validity']['valid'] and label['label']==r['labels']['label']
    evaluated=metrics.eval_offline(str(dest))
    assert evaluated['frame_binding']=='persisted_source_frame_ids'
    for arm,key in [('odometry','odometry'),('pgo','optimized')]:
        np.testing.assert_allclose(evaluated[arm]['ape_unaligned_rmse'],summary['metrics'][key]['ape_rmse'],atol=1e-6,rtol=0)
    (out/'paper_metrics.json').write_text(json.dumps(evaluated,indent=2))
    for path,digest in identities.items():assert sha(path)==digest,path
    validation=dict(frames=len(ids),attempts=len(starts),measurements=len(generations),accepted=len(edges),
                    labels=dict(Counter(r['labels']['label'] for r in generations.values())),
                    input_hashes_rechecked=len(identities),source_frame_binding_exact=True,
                    same_measurement_edges_exact=True,metrics_recomputed=True)
    (out/'validation.json').write_text(json.dumps(validation,indent=2))
    lines=['# Full '+name+' core rerun','', f'{len(ids)} raw scans, source IDs {first}-{last}; fresh KISS-ICP, retrieval, RAP and PGO.','',
           '| Metric | Odometry | RAP + PGO |','|---|---:|---:|']
    for key in ['ape_unaligned_rmse','ape_aligned_rmse']:
        lines.append(f"| {key} (LiDAR m) | {evaluated['odometry'][key]:.6f} | {evaluated['pgo'][key]:.6f} |")
    lines+=['',f"Keyframes: {len(kfs)}. Candidates/accepted: {len(starts)}/{len(edges)}. Labels: {validation['labels']}.",
            '', 'Production stage wall times (seconds):', '', '| Stage | Seconds |','|---|---:|']
    for name,value in summary['timings_s'].items():lines.append(f'| {name} | {value:.2f} |')
    lines += [f"| Pipeline total | {summary['total_runtime_s']:.2f} |",f'| Subprocess including startup | {wall:.2f} |','',
              'Loop closure timing includes retrieval, model loading, hashing and inference; evaluation includes map exports. Preflight hashing warms file reads. One run, not a cold-cache or real-time latency benchmark. Separate camera-frame KITTI drift is saved in paper_metrics.json. This remains development evidence, not independent calibration.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (out/'INCOMPLETE').unlink()
    print('\n'.join(lines),flush=True)

if __name__=='__main__':
    run('poss','/mnt/e/githouse/RAP-SLAM/data/poss','00',3850,5268,False)
    run('kitti05',str(DATA),'05',0,2760,True)
    run('kitti00',str(DATA),'00',0,4540,True)

