"""Frozen E0 engineering screen. Explicit configuration; no production edits."""
import hashlib, json, os, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

MAIN=Path('/mnt/e/githouse/RAP-main')
ROOT=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01'
OLD=MAIN/'docs/maintenance/2026-09-11'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from rap_slam import real_dataset, odometry
import eval_paper_metrics as epm
ARMS={'O':(False,80.,1.5,.8),'A':(True,80.,1.5,.8),
      'B':(False,100.,0.,1.),'C':(True,100.,0.,1.)}
COUNTS={'00':4541,'05':2761,'06':1101}
KEYS=['ape_unaligned_rmse','ape_aligned_rmse','kitti_ter_pct','kitti_rer_deg100m']

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(2**20),b''):h.update(v)
    return h.hexdigest()
def evaluate(seq,poses):
    calib=DATA/'sequences'/seq/'calib.txt'
    gt=np.asarray(real_dataset.load_gt_poses(str(DATA/'poses'/f'{seq}.txt'),str(calib),apply_calib=True))
    assert len(gt)==len(poses)==COUNTS[seq]
    lidar=epm.evaluate_pair(list(gt),list(poses),source_frame_ids=list(range(len(gt))))
    tr=real_dataset._read_calib_transform(str(calib))
    cam=epm.evaluate_pair(list(tr@gt@np.linalg.inv(tr)),list(tr@poses@np.linalg.inv(tr)),source_frame_ids=list(range(len(gt))))
    return {'lidar':{k:lidar[k] for k in KEYS},'camera':{k:cam[k] for k in KEYS}}
def verify_geometry(p):
    assert np.isfinite(p).all()
    r=p[:,:3,:3]
    assert np.max(np.abs(r.transpose(0,2,1)@r-np.eye(3)))<1e-4
    assert np.max(np.abs(np.linalg.det(r)-1))<1e-4
def freeze():
    files=list((ROOT/'rap_slam').glob('*.py'))+[ROOT/'scripts/run_pipeline.py',ROOT/'scripts/eval_paper_metrics.py',Path(__file__),BASE/'PROTOCOL.md']
    files+=list((MAIN/'rectified_point_flow').rglob('*.py'))+list((MAIN/'config').rglob('*.yaml'))
    sources={str(p):sha(p) for p in files}
    sources.update({str(MAIN/'weights'/n):sha(MAIN/'weights'/n) for n in ['rap_model_12.ckpt','mini_spinnet_t.pth']})
    inputs={}
    for seq,n in COUNTS.items():
        parent=read(OLD/f'full-kitti{seq}-01/input_manifest.json')
        required=[DATA/'sequences'/seq/'velodyne'/f'{i:06d}.bin' for i in range(n)]
        required += [DATA/'poses'/f'{seq}.txt',DATA/'sequences'/seq/'calib.txt',DATA/'sequences'/seq/'times.txt']
        for p in required:
            h=sha(p);assert h==parent[str(p)],str(p);inputs[str(p)]=h
        for name in ['odom_poses.txt','summary.json','source_frames.json']:
            p=OLD/f'full-kitti{seq}-01/pipeline'/name;inputs[str(p)]=sha(p)
    with zipfile.ZipFile(BASE/'source_snapshot.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files:
            if p!=BASE/'PROTOCOL.md':z.write(p,str(p.relative_to(MAIN.parent)))
    save(BASE/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),sources=sources,inputs=inputs,
        branches='codex/e0-f1-20260926',prior_branch='meeting_20260921',prior_combined_results_observed=True))
    print('E0 source/input freeze complete',len(inputs),flush=True)
def verify_freeze(raw=False):
    f=read(BASE/'freeze.json')
    for p,h in f['sources'].items():assert sha(p)==h,p
    if raw:
        for p,h in f['inputs'].items():assert sha(p)==h,p
def run():
    verify_freeze();(BASE/'INCOMPLETE').write_text('E0 running\n')
    start=time.monotonic();results={};deltas={}
    for seq,n in COUNTS.items():
        results[seq]={}
        for arm,(correction,maximum,minimum,voxel) in ARMS.items():
            assert time.monotonic()-start<7200
            out=BASE/f'odom-{seq}-{arm}';out.mkdir(exist_ok=False)
            engine=odometry.KissOdometry(max_range=maximum,min_range=minimum,voxel_size=voxel,deskew=False)
            poses=[];t=time.monotonic()
            for i in range(n):
                p=np.fromfile(DATA/'sequences'/seq/'velodyne'/f'{i:06d}.bin',np.float32).reshape(-1,4)[:,:3]
                assert np.isfinite(p).all()
                if minimum>0:p=p[np.linalg.norm(p,axis=1)>=minimum]
                if correction:p=real_dataset.kitti_vertical_correction(p)
                poses.append(engine.register(p.astype(np.float32)).copy())
            poses=np.asarray(poses);verify_geometry(poses)
            np.save(out/'poses.npy',poses)
            save(out/'source_ids.json',list(range(n)))
            m=evaluate(seq,poses);m.update(wall_s=time.monotonic()-t,config=ARMS[arm])
            save(out/'metrics.json',m);results[seq][arm]=m
            if arm=='O':
                ref=np.asarray(epm.load_kitti_format(str(OLD/f'full-kitti{seq}-01/pipeline/odom_poses.txt')))
                delta=float(np.max(np.abs(ref-poses)));deltas[seq]=delta
                assert delta<=1e-5,('baseline reproduction',seq,delta)
            print('E0',seq,arm,m['camera']['kitti_ter_pct'],m['lidar']['ape_aligned_rmse'],round(m['wall_s'],1),flush=True)
    means={a:dict(ter=float(np.mean([results[s][a]['camera']['kitti_ter_pct'] for s in COUNTS])),
                  ate=float(np.mean([results[s][a]['lidar']['ape_aligned_rmse'] for s in COUNTS]))) for a in ARMS}
    eligible=[a for a in 'ABC' if means[a]['ter']<=means['O']['ter']-.02 and means[a]['ate']<=1.1*means['O']['ate']
              and all(results[s][a]['camera']['kitti_ter_pct']<=results[s]['O']['camera']['kitti_ter_pct']+.05 for s in COUNTS)]
    selected=min(eligible,key=lambda a:(means[a]['ter'],means[a]['ate'],a)) if eligible else None
    save(BASE/'selection.json',dict(means=means,eligible=eligible,selected=selected,baseline_deltas=deltas,
        frozen_before_full_utc=datetime.now(timezone.utc).isoformat()))
    print('E0 selected',selected,means,flush=True)
    if selected:
        correction,maximum,minimum,voxel=ARMS[selected];full_start=time.monotonic()
        for seq,n in COUNTS.items():
            assert time.monotonic()-start<7200 and time.monotonic()-full_start<1800
            dest=BASE/f'full-{seq}-{selected}'
            cmd=[sys.executable,'-B',str(ROOT/'scripts/run_pipeline.py'),'--output',str(dest),
                 '--source','real','--real-root',str(DATA.parent),'--real-seq',seq,'--real-start','0','--real-end',str(n-1),
                 '--real-stride','1','--real-apply-calib','--apply-kitti-205' if correction else '--no-apply-kitti-205',
                 '--odom-max-range',str(maximum),'--odom-min-range',str(minimum),'--odom-voxel',str(voxel),
                 '--kf-trans','6','--kf-rot','12','--loop-method','both','--loop-dist','15','--loop-sep','200',
                 '--max-candidates','12','--sc-dist-thresh','.25','--sc-shortlist','10','--sc-rings','20','--sc-sectors','60',
                 '--sc-max-radius','80','--seed','42','--rap-steps','5','--rap-max-points','4000','--rap-voxel','.4',
                 '--multigen-k','1','--gate-mode','heuristic','--min-overlap','.7','--max-mean-dist','2.5',
                 '--loop-weighting','relfloor','--relfloor-ref','1','--relfloor-cap','3','--robust-kernel','huber',
                 '--huber-k','1','--loop-nms-width','0']
            save(BASE/f'command-{seq}.json',cmd)
            with (BASE/f'full-{seq}.log').open('x') as log:
                subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=min(1800-(time.monotonic()-full_start),7200-(time.monotonic()-start)))
            print('Full complete',seq,flush=True)
    save(BASE/'execution.json',dict(wall_s=time.monotonic()-start,completed_utc=datetime.now(timezone.utc).isoformat()))
    verify_freeze(raw=True)
    print('E0 execution complete; independent validation pending',flush=True)
if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
