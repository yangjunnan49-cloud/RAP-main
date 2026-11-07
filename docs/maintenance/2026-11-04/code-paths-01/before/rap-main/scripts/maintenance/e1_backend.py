"""E1 frozen orchestration of existing backend; no production algorithm edits."""
import hashlib, json, os, sys, time, zipfile, importlib.metadata
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

MAIN=Path('/mnt/e/githouse/RAP-main'); ROOT=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-09-27/e1-backend-01'
E0=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
COUNTS={'00':4541,'05':2761,'06':1101}
ARMS={'O':{},'W1':dict(loop_sigmas=[1.]*6,loop_weighting='fixed',robust_kernel=None),
      'W2':dict(robust_kernel='gnc_tls',gnc_prob=.99,gnc_mu_step=1.4,gnc_max_iterations=100),
      'E1':dict(loop_nms_width=10.)}
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x') as f: json.dump(v,f,indent=2,allow_nan=False)
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
def freeze():
    parent=read(E0/'artifact_hashes.json'); old=read(E0/'freeze.json')
    files=[BASE/'PROTOCOL.md',BASE/'PROTOCOL_DRAFT.md',Path(__file__),Path(__file__).with_name('validate_e1_backend.py'),E0/'artifact_hashes.json']
    files+=list((ROOT/'rap_slam').glob('*.py'))+[ROOT/'scripts/eval_paper_metrics.py']
    for seq in COUNTS:
        for name in ['odom_poses.txt','optimized_poses.txt','keyframes.json','accepted_loops.json','verification_measurements.jsonl','summary.json','source_frames.json']:
            p=E0/f'full-{seq}-A'/name; assert sha(p)==parent[str(p.relative_to(E0))];files.append(p)
        for p in [DATA/'poses'/f'{seq}.txt',DATA/'sequences'/seq/'calib.txt']:
            assert sha(p)==old['inputs'][str(p)];files.append(p)
    p=E0/'development_baseline_v2.json';assert sha(p)==parent[p.name];files.append(p)
    for p in files:
        if str(p) in old['sources']: assert sha(p)==old['sources'][str(p)],p
    with zipfile.ZipFile(BASE/'source_snapshot.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files:
            if p.suffix=='.py': z.write(p,str(p.relative_to(MAIN.parent)))
    save(BASE/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),files={str(p):sha(p) for p in files},arms=ARMS,
        python=sys.version,packages={p:importlib.metadata.version(p) for p in ['numpy','gtsam','evo','scipy']}))
    print('Freeze verified',len(files),flush=True)
def run():
    from rap_slam import pose_graph
    verify();out=BASE/'attempt-01';out.mkdir();(BASE/'INCOMPLETE').write_text('Execution/validation pending\n')
    start=time.monotonic();stats={}
    for seq,n in COUNTS.items():
        src=E0/f'full-{seq}-A'; a=np.loadtxt(src/'odom_poses.txt').reshape(-1,3,4)
        odom=np.tile(np.eye(4),(n,1,1));odom[:,:3]=a
        kf=read(src/'keyframes.json');assert kf==sorted(set(kf)) and kf[0]==0 and kf[-1]==n-1
        assert read(src/'source_frames.json')['source_frame_ids']==list(range(n))
        # Explicit allowlist excludes all saved evaluator/GT diagnostics.
        loops=[{k:e[k] for k in ['i','j','T_rel','overlap','mean_dist','measurement_id']} for e in read(src/'accepted_loops.json')]
        assert all(e['i'] in kf and e['j'] in kf for e in loops)
        for arm in ['O','O-repeat','W1','W2','E1']:
            assert time.monotonic()-start<1800
            dest=out/f'{seq}-{arm}';dest.mkdir();t=time.monotonic();diag={}
            kw=ARMS['O' if arm=='O-repeat' else arm]
            opt=pose_graph.optimize_pose_graph(list(odom),kf,loops,gnc_out=diag,**kw)
            full=np.asarray(pose_graph.propagate_to_full_trajectory(list(odom),kf,opt))
            assert np.isfinite(full).all();np.save(dest/'poses.npy',full)
            save(dest/'source_ids.json',list(range(n)))
            kept=pose_graph.nms_loop_edges(loops,10) if arm=='E1' else loops
            save(dest/'edges.json',kept)
            for k,v in list(diag.items()):
                if isinstance(v,np.ndarray):diag[k]=v.tolist()
            save(dest/'diagnostics.json',diag)
            delta=None
            if arm=='O':
                ref=np.loadtxt(src/'optimized_poses.txt').reshape(-1,3,4)
                delta=float(np.max(np.abs(full[:,:3]-ref)));assert delta<=1e-5,delta
            if arm=='O-repeat':assert np.array_equal(full,np.load(out/f'{seq}-O/poses.npy'))
            stats[f'{seq}-{arm}']=dict(wall_s=time.monotonic()-t,baseline_delta=delta,edges=len(kept))
            print(seq,arm,stats[f'{seq}-{arm}'],flush=True)
    verify();save(out/'execution.json',dict(cells=stats,wall_s=time.monotonic()-start,utc=datetime.now(timezone.utc).isoformat()))
if __name__=='__main__': {'freeze':freeze,'run':run}[sys.argv[1]]()
