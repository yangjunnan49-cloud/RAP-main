"""LMB0: fixed E0 odometry plus the preinstalled native KISS map/loop bundle."""
import time
START=time.monotonic()
import os
import sys
import json
import hashlib
import resource
import subprocess
import signal
import traceback
from pathlib import Path
from datetime import datetime,timezone

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-20/e0-local-map-bundle-01'
DMF=MAIN/'docs/maintenance/2026-10-20/direct-matching-factors-01'
SUP=BASE/'supervision'; DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'; SLAM=MAIN.parent/'RAP-SLAM'
KISS='/root/venvs/kiss-slam-hc1/bin/python'
SEQS=('00','05')
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def src(s): return MAIN/f'docs/maintenance/2026-09-26/e0-frontend-01/full-{s}-A'
def raw(s,i): return DATA/f'sequences/{s}/velodyne/{i:06d}.bin'
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=128*2**20
    if (SUP/'host_latest.json').exists(): assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def used():
    total=0.
    for d in SUP.glob('*'):
        if d.is_dir():
            vals=[read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]
            total+=max(vals,default=0.)
    return total
def verify():
    for p,h in read(BASE/'freeze.json')['files'].items(): assert sha(p)==h,p
def imports():
    global np
    import numpy as np
    sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]
def poses(p):
    a=np.loadtxt(p); out=np.tile(np.eye(4),(len(a),1,1)); out[:,:3]=a.reshape(-1,3,4); return out
def proper(t):
    u,_,v=np.linalg.svd(t[:,:3,:3]); d=np.tile(np.eye(3),(len(t),1,1)); d[:,-1,-1]=np.linalg.det(u@v)
    out=t.copy(); out[:,:3,:3]=u@d@v; assert np.max(abs(out-t))<=1e-5; return out
def config():
    from kiss_slam.config import load_config
    c=load_config(None); c.odometry.preprocessing.min_range=1.5; c.odometry.preprocessing.max_range=80.; c.odometry.preprocessing.deskew=False
    c.odometry.mapping.voxel_size=.8
    if (BASE/'config.json').exists(): assert c.model_dump()==read(BASE/'config.json')
    return c

class FixedOdometry:
    def __init__(self,c,o):
        from kiss_icp.kiss_icp import KissICP
        original=KissICP(c); self.local_map=original.local_map; self.preprocessor=original.preprocessor; self.voxelize=original.voxelize
        self.o=o; self.index=-1; self.anchor=0; self._pose=np.eye(4); self.last_delta=np.eye(4); self.resets=[]; self.max_relative_error=0.
    @property
    def last_pose(self): return self._pose
    @last_pose.setter
    def last_pose(self,t):
        assert np.max(abs(t-np.eye(4)))<=1e-12
        self.anchor=max(self.index,0); self._pose=np.eye(4); self.resets.append(self.anchor)
    def register_frame(self,frame,timestamps):
        self.index+=1; frame=self.preprocessor.preprocess(frame,timestamps,self.last_delta); source,down=self.voxelize(frame)
        new=np.linalg.solve(self.o[self.anchor],self.o[self.index])
        # Independent expression for this rigid relative pose.
        ai=self.o[self.anchor]; expected=np.eye(4); expected[:3,:3]=ai[:3,:3].T@self.o[self.index,:3,:3]
        expected[:3,3]=ai[:3,:3].T@(self.o[self.index,:3,3]-ai[:3,3]); self.max_relative_error=max(self.max_relative_error,float(np.max(abs(expected-new))))
        self.local_map.update(down,new); self.last_delta=np.linalg.solve(self._pose,new); self._pose=new
        return frame,source

class Recorder:
    def __init__(self,real): self.real=real; self.rows=[]
    def compute(self,*args):
        out=self.real.compute(*args); ok,i,j,z=out
        self.rows.append(dict(query_id=int(args[0]),accepted=bool(ok),source=int(i),target=int(j),pose=np.asarray(z).tolist() if z is not None else None))
        return out

def freeze():
    assert read(DMF/'metric_validation.json')['passed'] and not read(DMF/'metric_validation.json')['scientific_gate_passed']
    import importlib.metadata as md
    import kiss_slam,kiss_icp,map_closures
    oldfreeze=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01/freeze.json'; prior_raw=read(oldfreeze)['inputs']
    paths=[Path(__file__),oldfreeze,Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),Path(__file__).with_name('validate_scan_level_graph.py'),
        BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',DMF/'metric_validation.json',DMF/'results.json',SLAM/'rap_slam/real_dataset.py',SLAM/'scripts/eval_paper_metrics.py']
    for package in (kiss_slam,kiss_icp,map_closures):
        root=Path(package.__file__).parent
        paths += [p for p in root.rglob('*') if p.is_file() and (p.suffix in ('.py','.so'))]
    paths.append(Path(KISS).resolve()); rawfiles={}
    for s in SEQS:
        manifest=read(src(s)/'source_frames.json'); ids=manifest['source_frame_ids']; assert ids==list(range(len(ids)))
        paths += [src(s)/n for n in ('source_frames.json','odom_poses.txt','optimized_poses.txt')]
        paths += [DATA/f'poses/{s}.txt',DATA/f'sequences/{s}/calib.txt']
        for i in ids:
            p=raw(s,i); assert str(p)==manifest['scan_files'][i]; rawfiles[str(p)]=sha(p); assert rawfiles[str(p)]==prior_raw[str(p)]
            if i%500==0: cap(); print('freeze raw',s,i,flush=True)
    paths=list(dict.fromkeys(paths)); snap=BASE/'source_snapshot'; snap.mkdir()
    for i,p in enumerate(paths):
        if p.suffix in ('.py','.ps1','.md'): (snap/f'{i:03d}-{p.name}').write_bytes(p.read_bytes())
    save(BASE/'config.json',config().model_dump()); paths.append(BASE/'config.json')
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in paths},raw_files=rawfiles,python=sys.version,
        packages={n:md.version(n) for n in ('kiss-slam','kiss-icp','map-closures','numpy','open3d')},caps=dict(seconds=1800,rss=4*2**30,dossier=128*2**20,gpu=0)))
    (BASE/'INCOMPLETE').write_text('Pending synthetic, complete bank and independent metric validation.\n')
    print('LMB0 frozen',len(paths),'sources and',len(rawfiles),'raw files',flush=True)

def synthetic():
    verify(); from kiss_slam.slam import KissSLAM
    rng=np.random.default_rng(20261020); o=np.tile(np.eye(4),(14,1,1)); o[:,0,3]=np.arange(14)*40.; o[:,1,3]=np.arange(14)*.2
    slam=KissSLAM(config()); fixed=FixedOdometry(config().kiss_icp_config(),o); slam.odometry=fixed
    slam.compute_closures=lambda *a:None
    p=rng.uniform([5,-8,-2],[25,8,3],(5000,3))
    for i in range(len(o)): slam.process_scan(p,np.array([]))
    direct=np.asarray(slam.poses); assert direct.shape==o.shape; before=float(np.max(abs(direct-o))); assert before<=1e-5,before
    slam.generate_new_node(); slam.local_map_graph.erase_last_local_map(); result,_=slam.fine_grained_optimization(); result=np.asarray(result)
    assert result.shape==o.shape; error=float(np.max(abs(result-o))); assert error<=1e-5,error
    assert fixed.resets==[3,6,9,12,13] and fixed.max_relative_error<=1e-10
    save(BASE/'synthetic.json',dict(utc=now(),passed=True,frame_count=len(o),reset_anchors=fixed.resets,relative_pose_max=fixed.max_relative_error,
        no_loop_before_fine_max=before,no_loop_after_fine_max=error,odometry_alignment_calls=0))
    print('Fixed-E0 adapter/no-loop synthetic pass',error,flush=True)

def bank():
    verify(); assert read(BASE/'synthetic.json')['passed']; from kiss_slam.slam import KissSLAM
    from rap_slam.real_dataset import kitti_vertical_correction
    dest=BASE/'bank'; dest.mkdir(); f=read(BASE/'freeze.json'); started=now(); summary={}
    for s in SEQS:
        d=dest/s; d.mkdir(); o=proper(poses(src(s)/'odom_poses.txt')); slam=KissSLAM(config()); fixed=FixedOdometry(config().kiss_icp_config(),o); slam.odometry=fixed
        recorder=Recorder(slam.closer); slam.closer=recorder; membership={}; consumed={}; begin=time.monotonic()
        for i in range(len(o)):
            p=raw(s,i); body=p.read_bytes(); identity=hashlib.sha256(body).hexdigest(); assert identity==f['raw_files'][str(p)]; consumed[str(p)]=identity
            points=np.frombuffer(body,dtype=np.float32).reshape(-1,4)[:,:3].copy(); ranges=np.linalg.norm(points,axis=1); points=points[(ranges>=1.5)&(ranges<=80.)]
            points=kitti_vertical_correction(points); mapid=slam.local_map_graph.last_id; membership.setdefault(str(mapid),[]).append(i)
            slam.process_scan(points,np.array([]))
            if i%250==0: cap(); print('mapping',s,i,'maps',slam.local_map_graph.last_id,'closures',len(slam.closures),flush=True)
        slam.generate_new_node(); slam.local_map_graph.erase_last_local_map(); intermediate=np.asarray(slam.poses); output,pgo=slam.fine_grained_optimization(); output=np.asarray(output)
        assert output.shape==intermediate.shape==o.shape and fixed.index==len(o)-1 and fixed.max_relative_error<=1e-9
        assert sorted(i for group in membership.values() for i in group)==list(range(len(o)))
        r=output[:,:3,:3]; assert np.max(abs(r.transpose(0,2,1)@r-np.eye(3)))<=1e-5 and np.max(abs(np.linalg.det(r)-1))<=1e-5
        np.save(d/'M.npy',output); np.save(d/'before_fine.npy',intermediate)
        save(d/'source_binding.json',dict(source_frame_ids=list(range(len(o))),map_consumed_frames=membership,reset_anchors=fixed.resets,raw_sha256=consumed,
            inherited_voxel_conservative_source_prefixes=[[0,i] for i in fixed.resets],per_return_voxel_lineage=False,
            relative_pose_max=fixed.max_relative_error,odometry_alignment_calls=0,loop_attempts=recorder.rows))
        pgo.write_graph(str(d/'trajectory.g2o')); slam.optimizer.write_graph(str(d/'local_map_graph.g2o'))
        summary[s]=dict(frames=len(o),local_maps=len(list(slam.local_map_graph.local_maps())),closures=len(slam.closures),loop_calls=len(recorder.rows),
            wall_seconds=time.monotonic()-begin,maximum_adapter_relative_error=fixed.max_relative_error)
        cap(); print('mapping complete',s,summary[s],flush=True)
    save(dest/'execution.json',dict(started_utc=started,utc=now(),rows=summary))
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()}))
    print('Both complete local-map trajectories sealed before GT',flush=True)
def verify_bank():
    verify(); f=read(BASE/'bank_seal.json'); assert f['freeze_sha256']==sha(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(BASE/'bank'/p)==h,p
def gates(rows):
    mean={a:{k:float(np.mean([rows[s][a][k] for s in SEQS])) for k in ('ate','ter','rer')} for a in ('B','M')}; tests={}
    tests['mean_ATE_gain5pct']=mean['M']['ate']<=.95*mean['B']['ate']+1e-10
    for k in ('ter','rer'): tests[f'mean_{k}_nonworse']=mean['M'][k]<=mean['B'][k]+1e-10
    for s in SEQS:
        tests[f'{s}_ATE_improves']=rows[s]['M']['ate']<rows[s]['B']['ate']; tests[f'{s}_ATE_harm5pct']=rows[s]['M']['ate']<=1.05*rows[s]['B']['ate']+1e-10
        for k in ('ter','rer'): tests[f'{s}_{k}_harm']=rows[s]['M'][k]<=rows[s]['B'][k]+.01+1e-10
    return dict(means=mean,tests=tests,passed=all(tests.values()))
def evaluate():
    verify_bank(); from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    started=now(); dest=BASE/'evaluation'; dest.mkdir(); rows={}
    for s in SEQS:
        (dest/s).mkdir(); tr=_read_calib_transform(str(DATA/f'sequences/{s}/calib.txt')); ti=np.linalg.inv(tr)
        gt=np.asarray(load_gt_poses(str(DATA/f'poses/{s}.txt'),str(DATA/f'sequences/{s}/calib.txt'),apply_calib=True)); rows[s]={}
        for a in ('B','M'):
            t=poses(src(s)/'optimized_poses.txt') if a=='B' else np.load(BASE/f'bank/{s}/M.npy')
            ids=list(range(len(t))); lidar=epm.evaluate_pair(list(gt),list(t),ids); camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
            rows[s][a]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segments=camera['kitti_segments']); save(dest/s/f'{a}_segments.json',camera['kitti_segment_records'])
    save(BASE/'results.json',dict(utc=now(),gt_read_started_utc=started,rows=rows,gate=gates(rows))); print(json.dumps(rows),flush=True)
def validate():
    verify_bank(); import validate_scan_level_graph as m
    result=read(BASE/'results.json'); assert read(BASE/'bank_seal.json')['utc']<result['gt_read_started_utc']; maximum=0.; count=0; actual={}; frozen=read(BASE/'freeze.json')
    for s in SEQS:
        camera=m.load(DATA/f'poses/{s}.txt'); tr=m.calibration(s); ti=np.linalg.inv(tr); lidar=ti@camera@tr; actual[s]={}
        binding=read(BASE/f'bank/{s}/source_binding.json'); assert binding['source_frame_ids']==list(range(len(camera)))
        assert binding['raw_sha256']=={str(raw(s,i)):frozen['raw_files'][str(raw(s,i))] for i in range(len(camera))}
        assert sorted(i for v in binding['map_consumed_frames'].values() for i in v)==list(range(len(camera)))
        for a in ('B','M'):
            t=poses(src(s)/'optimized_poses.txt') if a=='B' else np.load(BASE/f'bank/{s}/M.npy'); seg=m.segments(camera,tr@t@ti); saved=read(BASE/f'evaluation/{s}/{a}_segments.json'); assert len(seg)==len(saved); count+=len(seg)
            for x,y in zip(seg,saved):
                for k in ('first','last','source_first','source_last','length_m'): assert x[k]==y[k]
                for k in ('translation_fraction','rotation_rad_per_m','speed_mps'): maximum=max(maximum,abs(x[k]-y[k])); assert abs(x[k]-y[k])<=2e-10
            actual[s][a]=dict(ate=m.horn_rmse(lidar,t),ter=float(np.mean([v['translation_fraction'] for v in seg])*100),rer=float(np.mean([v['rotation_rad_per_m'] for v in seg])*180/np.pi*100),segments=len(seg))
            for k in actual[s][a]: maximum=max(maximum,abs(actual[s][a][k]-result['rows'][s][a][k])); assert abs(actual[s][a][k]-result['rows'][s][a][k])<=1e-8
    independent=gates(actual); assert independent['tests']==result['gate']['tests'] and independent['passed']==result['gate']['passed']
    save(BASE/'validation.json',dict(utc=now(),passed=True,independent_metric_max=maximum,independent_segments=count,scientific_gate_passed=independent['passed'],
        independent_nonlinear_optimizer=False,raw_identity_checked_at_consumption=True,independent_raw_preprocessing=False,rows=actual))
    print('LMB0 independent metrics validated',count,maximum,independent['passed'],flush=True)

def run(stage,native):
    remaining=1800-used(); assert remaining>0; signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('LMB cumulative cap'))); signal.alarm(max(1,int(remaining)))
    ok=False; error=None; peak=None
    try:
        if stage in ('freeze','synthetic','bank') and not native:
            env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']=''; env['OPEN3D_CPU_RENDERING']='true'
            result=subprocess.run([KISS,'-u','-B',str(Path(__file__)),stage,'--native'],env=env,timeout=remaining-1)
            receipt=read(SUP/stage/'native_exit.json'); peak=receipt['peak_RSS_bytes']; assert result.returncode==0 and receipt['success']
        else:
            imports(); {'freeze':freeze,'synthetic':synthetic,'bank':bank,'evaluate':evaluate,'validate':validate}[stage]()
        cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc(); save(BASE/f'FAILURE_{stage}_{"native" if native else "wrapper"}.json',dict(utc=now(),error=error))
    finally:
        signal.alarm(0); save(SUP/stage/('native_exit.json' if native else 'child_exit.json'),dict(utc=now(),success=ok,error=error,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak or 0),GPU_calls=0,overlapping_native_clock_not_added=not native))
    if not ok: sys.exit(1)
if __name__=='__main__': run(sys.argv[1],'--native' in sys.argv)
