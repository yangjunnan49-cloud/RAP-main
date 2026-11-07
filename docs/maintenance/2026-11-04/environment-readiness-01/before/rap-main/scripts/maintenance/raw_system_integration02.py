"""R0 complete fresh-raw SLAM trajectory core; fixed G versus native K."""
import time
START=time.monotonic()
import os,sys,json,hashlib,resource,signal,subprocess,traceback,importlib.util
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import e0_local_map_six as old
r=old.r
BASE=r.MAIN/'docs/maintenance/2026-10-20/raw-system-integration-01';SUP=BASE/'supervision'
SEQS=old.SEQS;CAP=7200
AD=BASE.parent/'e0-odometry-adapter-component-01';FINE=BASE.parent/'e0-anchor-capsule-01'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return r.read(p)
def save(p,x):return r.save(p,x)
def sha(p):return r.sha(p)
def used():
    total=0.
    for d in SUP.glob('*'):
        if d.is_dir():total+=max([read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0])
    return total
def cap():
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=256*2**20
def guard():
    data=read(SUP/'host_latest.json');stamp=datetime.fromisoformat(data['utc'].replace('Z','+00:00'));age=(datetime.now(timezone.utc)-stamp).total_seconds()
    assert 0<=age<=2.,('stale/unknown launch observation',age)
    assert data['headroom_bytes']>=12*2**30,('launch guard',data['headroom_bytes'])
    return dict(utc=now(),observed_utc=data['utc'],age_seconds=age,headroom_bytes=data['headroom_bytes'])
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def config(mode):
    from kiss_slam.config import load_config
    c=r.config() if mode=='G' else load_config(None)
    if (BASE/f'config_{mode}.json').exists():assert c.model_dump()==read(BASE/f'config_{mode}.json')
    return c
def verify():
    for p,h in read(BASE/'freeze.json')['files'].items():assert sha(p)==h,p
    for p,h in read(BASE/'VARIANT02_FREEZE.json')['files'].items():assert sha(p)==h,p
def freeze():
    assert read(BASE/'RUNTIME_PREFLIGHT.json')['same_frontend_config']
    import kiss_slam,kiss_icp,map_closures
    files=[Path(__file__),Path(old.__file__),Path(r.__file__),BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'RUNTIME_PREFLIGHT.json',
        AD/'fixed_odometry.py',FINE/'anchor_fine.py',FINE/'pose_graph_config.json',r.SLAM/'rap_slam/odometry.py',r.SLAM/'rap_slam/real_dataset.py',r.SLAM/'rap_slam/trajectory_protocol.py',
        r.SLAM/'scripts/eval_paper_metrics.py',Path(__file__).with_name('validate_scan_level_graph.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),
        BASE/'environment/RAP.json',BASE/'environment/KISS.json',old.ARCHIVE]
    for package in (kiss_slam,kiss_icp,map_closures):files += [p for p in Path(package.__file__).parent.rglob('*') if p.is_file() and p.suffix in ('.py','.so')]
    files += [Path(r.KISS).resolve(),Path('/root/miniconda3/envs/rap-inference/bin/python').resolve()]
    rawfiles={};counts={}
    for s in SEQS:
        src=old.src(s);manifest=read(src/'source_frames.json');ids=manifest['source_frame_ids'];assert ids==list(range(len(ids)));counts[s]=len(ids)
        prior=src.parent/'freeze.json';prior_inputs=read(prior)['inputs'];files.append(prior)
        files += [src/n for n in ('source_frames.json','odom_poses.txt','optimized_poses.txt')]
        files += [r.DATA/f'poses/{s}.txt',r.DATA/f'sequences/{s}/calib.txt',r.DATA/f'sequences/{s}/times.txt']
        for i in ids:
            p=r.raw(s,i);assert manifest['scan_files'][i]==str(p);h=sha(p);assert h==prior_inputs[str(p)];rawfiles[str(p)]=h
            if i%500==0:cap();print('freeze',s,i,flush=True)
    for m in ('G','K'):save(BASE/f'config_{m}.json',config(m).model_dump());files.append(BASE/f'config_{m}.json')
    files=list(dict.fromkeys(files));snap=BASE/'source_snapshot';snap.mkdir()
    for i,p in enumerate(files):
        if p.suffix in ('.py','.md','.ps1'):(snap/f'{i:03d}-{p.name}').write_bytes(p.read_bytes())
    schedule=[]
    for repeat in range(1,4):
        for index,s in enumerate(SEQS):
            for m in (('G','K') if (repeat+index)%2==0 else ('K','G')):schedule.append(dict(repeat=repeat,sequence=s,mode=m,key=f'r{repeat}_{s}_{m}'))
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in files},raw_files=rawfiles,counts=counts,schedule=schedule,
        relevant_env={k:v for k,v in os.environ.items() if k.startswith(('kiss_slam_','kiss_icp_','OMP_','MKL_','OPENBLAS_','CUDA_VISIBLE_DEVICES','OPEN3D_CPU_RENDERING'))},
        caps=dict(enclosing_seconds=CAP,RSS_bytes=4*2**30,dossier_bytes=256*2**20,GPU_calls=0),GT_numeric_read=False))
    (BASE/'INCOMPLETE').write_text('Pending synthetic/all36 raw predictions/independent evaluation.\n')
    print('R0 frozen',len(files),len(rawfiles),'inputs,36 cells',flush=True)
def proper_one(t):return r.proper(t[None])[0]
def synthetic():
    verify();from kiss_slam.slam import KissSLAM
    fixed_module=module('raw_fixed_odometry',AD/'fixed_odometry.py');fine_module=module('raw_anchor_fine',FINE/'anchor_fine.py')
    from rap_slam.odometry import KissOdometry
    from rap_slam.real_dataset import kitti_vertical_correction
    rng=np.random.default_rng(20261020);points=rng.uniform([5,-8,-2],[25,8,3],(5000,3)).astype(np.float32)
    body=np.column_stack([points,np.zeros(len(points),np.float32)]).astype(np.float32).tobytes();decoded=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3];assert np.array_equal(decoded,points)
    corrected=kitti_vertical_correction(decoded.copy());assert corrected.dtype==np.float32
    original=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False)
    o=np.tile(np.eye(4),(4,1,1));slam=KissSLAM(config('G'));fixed=fixed_module.FixedOdometry(config('G').kiss_icp_config(),o);slam.odometry=fixed;slam.compute_closures=lambda *args:None
    maximum=0.
    for i in range(4):
        pose=original.register(corrected.copy());o[i]=proper_one(pose.copy());slam.process_scan(corrected.copy(),np.array([]));maximum=max(maximum,float(np.max(abs(np.asarray(slam.poses)-o[:i+1]))))
    assert maximum<=1e-5
    known=np.tile(np.eye(4),(14,1,1));known[:,0,3]=np.arange(14)*40.;known[:,1,3]=np.arange(14)*.2
    smoke=KissSLAM(config('G'));adapter=fixed_module.FixedOdometry(config('G').kiss_icp_config(),known);smoke.odometry=adapter;smoke.compute_closures=lambda *args:None
    frame_ref=[-1];events=[];observe_generate(smoke,frame_ref,events)
    for i in range(14):frame_ref[0]=i;smoke.process_scan(corrected.copy(),np.array([]))
    smoke.generate_new_node();smoke.local_map_graph.erase_last_local_map()
    assert events==adapter.resets==[3,6,9,12,13] and np.max(abs(np.asarray(smoke.poses)-known))<=1e-5
    # Noncommuting/no-op fine graph and frontend's independent absolute pose are separate contracts.
    from scipy.spatial.transform import Rotation
    q=np.tile(np.eye(4),(12,1,1))
    for i in range(12):q[i,:3,:3]=Rotation.from_euler('xyz',[.07*i,.13*np.sin(i),-.09*i]).as_matrix();q[i,:3,3]=[i,.2*i*i,np.sin(i)]
    t=fine_module.fine(q,q,[0,4,8],q[[0,4,8]],config('G').pose_graph_optimizer);error=float(np.max(abs(t-q)));assert error<=1e-7
    save(BASE/'synthetic.json',dict(utc=now(),passed=True,fresh_frontend_map_pose_max=maximum,noncommuting_fine_noop_max=error,real_raw_scans_read=0,GT_numeric_read=False))
def bankseal():
    dest=BASE/'bank';expected={z['key'] for z in read(BASE/'freeze.json')['schedule']};assert {p.name for p in dest.iterdir()}==expected
    for z in expected:assert read(dest/z/'worker_exit.json')['success']
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()},cells=36,GT_numeric_read=False))
def observe_generate(slam,frame_ref,events):
    original=slam.generate_new_node
    def wrapped():
        value=original();events.append(int(frame_ref[0]));return value
    slam.generate_new_node=wrapped
def worker(cell):
    verify();from kiss_slam.slam import KissSLAM
    from rap_slam.real_dataset import kitti_vertical_correction
    s=cell['sequence'];m=cell['mode'];key=cell['key'];f=read(BASE/'freeze.json');n=f['counts'][s];dest=BASE/'bank'/key;dest.mkdir()
    c=config(m);slam=KissSLAM(c);recorder=r.Recorder(slam.closer);slam.closer=recorder
    membership={};chain=hashlib.sha256();timing=[];begin=time.monotonic();o=np.tile(np.eye(4),(n,1,1));rows={}
    if m=='G':
        from rap_slam.odometry import KissOdometry
        front=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False);fixed_module=module('raw_fixed_odometry',AD/'fixed_odometry.py');fixed=fixed_module.FixedOdometry(c.kiss_icp_config(),o);slam.odometry=fixed
    else:
        from kiss_icp.pybind import kiss_icp_pybind as binding
    frame_ref=[-1];reset_events=[];observe_generate(slam,frame_ref,reset_events)
    for i in range(n):
        frame_ref[0]=i
        start=time.perf_counter();p=r.raw(s,i);body=p.read_bytes();h=hashlib.sha256(body).hexdigest();assert h==f['raw_files'][str(p)];chain.update(f'{i} {h}\n'.encode());after_read=time.perf_counter()
        raw=np.frombuffer(body,np.float32).reshape(-1,4)[:,:3];assert np.isfinite(raw).all()
        if m=='G':
            distance=np.linalg.norm(raw,axis=1);front_points=kitti_vertical_correction(raw[distance>=1.5].copy()).astype(np.float32);map_points=kitti_vertical_correction(raw[(distance>=1.5)&(distance<=80.)].copy());timestamps=np.array([])
        else:
            map_points=np.asarray(binding._correct_kitti_scan(binding._Vector3dVector(raw.astype(np.float64))));timestamps=np.array([])
        after_preprocess=time.perf_counter()
        if m=='G':o[i]=proper_one(front.register(front_points).copy())
        after_front=time.perf_counter();mid=slam.local_map_graph.last_id;membership.setdefault(str(mid),[]).append(i);slam.process_scan(map_points,timestamps);after_map=time.perf_counter()
        timing.append([after_read-start,after_preprocess-after_read,after_front-after_preprocess,after_map-after_front,after_map-start])
        if i%250==0:cap();print(key,i,'maps',slam.local_map_graph.last_id,'loops',len(slam.closures),flush=True)
    slam.generate_new_node();slam.local_map_graph.erase_last_local_map();initial=np.asarray(slam.poses);fine_begin=time.monotonic();frontend_delta=None;anchor_max=None;reconstruction=None
    if m=='G':
        reference=r.proper(r.poses(old.src(s)/'odom_poses.txt'));frontend_delta=float(np.max(abs(reference-o)));assert frontend_delta<=1e-5,('E0 frontend correspondence failed',frontend_delta)
        anchors=[];coarse=[];reconstruction=0.
        for mid,frames in membership.items():
            a=0 if int(mid)==0 else fixed.resets[int(mid)-1];p=initial[frames[0]]@np.linalg.solve(o[frames[0]],o[a]);anchors.append(a);coarse.append(p)
            for i in frames:reconstruction=max(reconstruction,float(np.max(abs(p@np.linalg.solve(o[a],o[i])-initial[i]))))
        assert reconstruction<=1e-8 and anchors==sorted(set(anchors)) and anchors[0]==0
        coarse=np.asarray(coarse);fine_module=module('raw_anchor_fine',FINE/'anchor_fine.py');t=fine_module.fine(o,initial,anchors,coarse,c.pose_graph_optimizer);anchor_max=float(np.max(abs(t[anchors]-coarse)));assert anchor_max<=1e-8
        anchor_record=dict(anchor_frames=anchors,coarse_poses=coarse.tolist(),maximum_reconstruction=reconstruction,maximum_preservation=anchor_max)
        resets=fixed.resets;relative=fixed.max_relative_error;assert relative<=1e-9 and resets==reset_events
    else:
        t,pgo=slam.fine_grained_optimization();t=np.asarray(t);resets=reset_events;relative=None
    fine_seconds=time.monotonic()-fine_begin;serialization_begin=time.monotonic()
    if m=='G':
        np.save(dest/'odometry.npy',o);np.save(dest/'before_fine.npy',initial);save(dest/'anchors.json',anchor_record)
    else:pgo.write_graph(str(dest/'trajectory.g2o'))
    assert t.shape==(n,4,4) and np.isfinite(t).all();rot=t[:,:3,:3];assert np.max(abs(rot.transpose(0,2,1)@rot-np.eye(3)))<=1e-5 and np.max(abs(np.linalg.det(rot)-1))<=1e-5
    assert sorted(i for group in membership.values() for i in group)==list(range(n));np.save(dest/'poses.npy',t);np.save(dest/'frame_timing.npy',np.asarray(timing));slam.optimizer.write_graph(str(dest/'map_graph.g2o'))
    save(dest/'source_binding.json',dict(source_frame_ids=list(range(n)),map_consumed_frames=membership,reset_anchors=resets,consumed_ordered_hash_chain=chain.hexdigest(),per_return_voxel_lineage=False,
        inherited_voxel_conservative_prefixes=[[0,i] for i in resets] if resets is not None else None,loop_attempts=recorder.rows,frontend_reference_max=frontend_delta,adapter_relative_max=relative,
        anchor_preservation_max=anchor_max,coarse_reconstruction_max=reconstruction,GT_numeric_read=False))
    save(dest/'execution.json',dict(utc=now(),cell=cell,frames=n,local_maps=len(membership),closures=len(slam.closures),loop_calls=len(recorder.rows),raw_loop_and_finalize_seconds=time.monotonic()-begin,
        fine_seconds=fine_seconds,serialization_seconds=time.monotonic()-serialization_begin,private_evidence_outputs_identical=False,frame_timing_columns=['read_hash','preprocess','E0_frontend_separate_G_only','native_process_scan','frame_total'],new_raw_frontend=True,large_map_exports=False))
    cap();print('complete',key,'frontend_max',frontend_delta,'loops',len(slam.closures),flush=True)
def run_bank():
    verify();assert read(BASE/'synthetic.json')['passed'];(BASE/'bank').mkdir();f=read(BASE/'freeze.json');left=CAP-used();begin=time.monotonic()
    for cell in f['schedule']:
        launch=guard();cell_dir=SUP/'run'/cell['key'];cell_dir.mkdir();save(cell_dir/'launch_guard.json',launch);remaining=left-(time.monotonic()-begin);assert remaining>1
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OPEN3D_CPU_RENDERING']='true';env['PYTHONDONTWRITEBYTECODE']='1'
        started=now();t=time.monotonic()
        with (cell_dir/'stdout.log').open('x') as out,(cell_dir/'stderr.log').open('x') as err:
            result=subprocess.run([r.KISS,'-u','-B',__file__,'--worker',json.dumps(cell)],env=env,stdout=out,stderr=err,timeout=remaining-1)
        receipt=read(BASE/'bank'/cell['key']/'worker_exit.json') if (BASE/'bank'/cell['key']/'worker_exit.json').exists() else None
        save(cell_dir/'controller_exit.json',dict(utc=now(),started_utc=started,returncode=result.returncode,wall_seconds=time.monotonic()-t,worker_receipt_present=receipt is not None))
        assert result.returncode==0 and receipt and receipt['success'],cell
        assert receipt['peak_RSS_bytes']<=4*2**30;cap();print('sealed cell',cell['key'],receipt['wall_seconds'],flush=True)
    bankseal();print('ALL36 raw predictions sealed before GT',flush=True)
def evaluate():
    verify();seal=read(BASE/'bank_seal.json');assert seal['cells']==36
    for p,h in seal['files'].items():assert sha(BASE/'bank'/p)==h,p
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    import validate_scan_level_graph as v
    started=now();assert seal['utc']<started;dest=BASE/'evaluation';dest.mkdir();rows=[];maximum=0.;segments=0
    for cell in read(BASE/'freeze.json')['schedule']:
        key=cell['key'];s=cell['sequence'];t=np.load(BASE/'bank'/key/'poses.npy');binding=read(BASE/'bank'/key/'source_binding.json');n=len(t);assert binding['source_frame_ids']==list(range(n))
        assert sorted(i for group in binding['map_consumed_frames'].values() for i in group)==list(range(n))
        f=read(BASE/'freeze.json');chain=hashlib.sha256()
        for i in range(n):chain.update(f"{i} {f['raw_files'][str(r.raw(s,i))]}\n".encode())
        assert binding['consumed_ordered_hash_chain']==chain.hexdigest()
        tr=_read_calib_transform(str(r.DATA/f'sequences/{s}/calib.txt'));ti=np.linalg.inv(tr);gt=np.asarray(load_gt_poses(str(r.DATA/f'poses/{s}.txt'),str(r.DATA/f'sequences/{s}/calib.txt'),apply_calib=True));assert gt.shape==t.shape
        ids=list(range(n));li=epm.evaluate_pair(list(gt),list(t),ids);ca=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),ids)
        a=dict(ate=li['ape_aligned_rmse'],ter=ca['kitti_ter_pct'],rer=ca['kitti_rer_deg100m'],segments=ca['kitti_segments'])
        cg=v.load(r.DATA/f'poses/{s}.txt');ct=v.calibration(s);seg=v.segments(cg,ct@t@np.linalg.inv(ct));segments+=len(seg);assert len(seg)==len(ca['kitti_segment_records'])
        b=dict(ate=v.horn_rmse(np.linalg.inv(ct)@cg@ct,t),ter=float(np.mean([p['translation_fraction'] for p in seg])*100),rer=float(np.mean([p['rotation_rad_per_m'] for p in seg])*180/np.pi*100),segments=len(seg))
        for k in a:maximum=max(maximum,abs(a[k]-b[k]));assert abs(a[k]-b[k])<=1e-8
        for p,q in zip(seg,ca['kitti_segment_records']):
            for k in ('first','last','source_first','source_last','length_m'):assert p[k]==q[k]
            for k in ('translation_fraction','rotation_rad_per_m','speed_mps'):maximum=max(maximum,abs(p[k]-q[k]));assert abs(p[k]-q[k])<=2e-10
        save(dest/f'{key}_segments.json',ca['kitti_segment_records']);execution=read(BASE/'bank'/key/'execution.json');receipt=read(BASE/'bank'/key/'worker_exit.json');tm=np.load(BASE/'bank'/key/'frame_timing.npy')
        rows.append(dict(**cell,**a,frames=n,worker_seconds=receipt['wall_seconds'],RSS_bytes=receipt['peak_RSS_bytes'],fine_seconds=execution['fine_seconds'],closures=execution['closures'],local_maps=execution['local_maps'],
            frame_latency=dict(median=float(np.median(tm[:,-1])),p95=float(np.quantile(tm[:,-1],.95)),p99=float(np.quantile(tm[:,-1],.99)),maximum=float(np.max(tm[:,-1])),over100ms=int(np.sum(tm[:,-1]>.1))),frontend_reference_max=binding['frontend_reference_max']))
        cap()
    per={};means={}
    for s in SEQS:
        per[s]={}
        for m in ('G','K'):
            subset=[z for z in rows if z['sequence']==s and z['mode']==m];assert len(subset)==3
            per[s][m]={k:dict(mean=float(np.mean([z[k] for z in subset])),std=float(np.std([z[k] for z in subset],ddof=1)),minimum=float(min(z[k] for z in subset)),maximum=float(max(z[k] for z in subset))) for k in ('ate','ter','rer','worker_seconds','RSS_bytes')}
    for m in ('G','K'):means[m]={k:float(np.mean([per[s][m][k]['mean'] for s in SEQS])) for k in ('ate','ter','rer')}
    primary=dict(mean_ATE_better=means['G']['ate']<means['K']['ate'],mean_ter_nonworse=means['G']['ter']<=means['K']['ter']+1e-5)
    safety={f'{s}_{k}':per[s]['G'][k]['mean']<=per[s]['K'][k]['mean']+.01 for s in SEQS for k in ('ter','rer')}
    save(BASE/'results.json',dict(utc=now(),GT_read_started_utc=started,bank_seal_sha256=sha(BASE/'bank_seal.json'),rows=rows,per_sequence=per,means=means,primary=primary,primary_passed=all(primary.values()),
        safety=safety,safety_passed=all(safety.values()),independent_validation_passed=True,independent_segments=segments,maximum_metric_delta=maximum,old_G_screen_not_revised=True,
        scope='Complete fresh-raw trajectory core/minimal common outputs; not native CLI all side products or new RAP benchmark'))
    print('R0 validated',means,primary,'safety',safety,'segments',segments,maximum,flush=True)
def run(stage,native):
    left=CAP-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('R0 cumulative cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        if stage in ('freeze','synthetic') and not native:
            env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OPEN3D_CPU_RENDERING']='true';p=subprocess.run([r.KISS,'-u','-B',__file__,stage,'--native'],env=env,timeout=left-1)
            receipt=read(SUP/stage/'native_exit.json');peak=receipt['peak_RSS_bytes'];assert p.returncode==0 and receipt['success']
        else:{'freeze':freeze,'synthetic':synthetic,'run':run_bank,'evaluate':evaluate}[stage]()
        cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc();save(BASE/f'FAILURE_{stage}_{"native" if native else "wrapper"}.json',dict(utc=now(),error=err))
    finally:
        signal.alarm(0);save(SUP/stage/('native_exit.json' if native else 'child_exit.json'),dict(utc=now(),success=ok,error=err,wall_seconds=time.monotonic()-START,
            peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0,overlapping_native_clock_not_added=True))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--worker' in sys.argv:
        cell=json.loads(sys.argv[-1]);dest=BASE/'bank'/cell['key'];good=False;error=None
        try:worker(cell);good=True
        except BaseException as e:error=repr(e);traceback.print_exc()
        finally:
            dest.mkdir(exist_ok=True);save(dest/'worker_exit.json',dict(utc=now(),success=good,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
        if not good:sys.exit(1)
    else:run(sys.argv[1],'--native' in sys.argv)
