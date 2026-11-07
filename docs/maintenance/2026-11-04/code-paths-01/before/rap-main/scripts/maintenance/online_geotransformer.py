"""All71 comparator: frozen GT-free inputs/predictions then evaluator."""
import sys,time,json,resource,importlib.metadata
from pathlib import Path
import numpy as np
import system_opportunity as h
import geotransformer_preflight as geo
BASE=h.MAIN/'docs/maintenance/2026-10-05/online-geotransformer-01'
INPUT=BASE/'input-bank'; BANK=BASE/'prediction-bank'; EVAL=BASE/'evaluation-01'
read,sha,save=h.read,h.sha,h.save
def now():
    from datetime import datetime,timezone
    return datetime.now(timezone.utc).isoformat()
def state(stage,**kw): (BASE/'STATUS.json').write_text(json.dumps(dict(stage=stage,utc=now(),**kw),indent=2)+'\n')
def attempts(): return {s:read(h.BASE/'attempt-01'/s/'candidates.json') for s in h.SEQS}
def scanpath(s,i): return h.DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def paths():
    p=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_online_inputs.py'),Path(__file__).with_name('validate_online_geotransformer.py'),Path(h.__file__),Path(geo.__file__),Path(__file__).with_name('validate_joint_loop_oracle.py'),Path(__file__).with_name('validate_dense_propagation.py'),geo.B/'preflight_freeze.json',geo.B/'preflight_results.json',geo.B/'validation.json',h.BASE/'freeze.json',h.BASE/'bank_seal.json',h.BASE/'validation.json',h.ROOT/'rap_slam/real_dataset.py',h.ROOT/'rap_slam/rap_backend.py',h.ROOT/'rap_slam/rap_precision.py',h.ROOT/'rap_slam/pose_graph.py',h.ROOT/'scripts/run_pipeline.py']
    for s,rows in attempts().items():
        p += [h.BASE/'attempt-01'/s/n for n in ['candidates.json','edges.json','baseline.npy']]
        p += [h.source(s)/n for n in ['summary.json','inference_provenance.json','verification_measurements.jsonl','odom_poses.txt','optimized_poses.txt','keyframes.json','source_frames.json']]
        p += [scanpath(s,i) for i in sorted({r[k] for r in rows for k in ['i','j']})]
        p += [h.DATA/'poses'/f'{s}.txt',h.DATA/'sequences'/s/'calib.txt']
    return sorted(set(p))
def verify():
    f=read(BASE/'freeze.json'); assert f['files']=={str(p):sha(p) for p in paths()}
    assert f['packages']=={n:importlib.metadata.version(n) for n in f['packages']}; geo.verify()
def cap(t):
    assert time.monotonic()-t<1800 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20<6
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<2*2**30
def seal(folder,name): save(BASE/name,dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def verify_seal(folder,name):
    s=read(BASE/name); assert s['freeze_sha256']==sha(BASE/'freeze.json')
    assert s['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def freeze():
    geo.verify(); assert read(geo.B/'validation.json')['passed']; assert not INPUT.exists() and not BANK.exists()
    oldf=read(h.BASE/'freeze.json')['files']; olds=read(h.BASE/'bank_seal.json')['files']
    for p in paths():
        if str(p) in oldf: assert sha(p)==oldf[str(p)]
        if h.BASE/'attempt-01' in p.parents: assert sha(p)==olds[str(p.relative_to(h.BASE/'attempt-01'))]
    pkgs=('numpy','scipy','torch','open3d','gtsam','evo')
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in paths()},packages={p:importlib.metadata.version(p) for p in pkgs},attempts=71,current_edges=58))
    state('FROZEN'); print('all-online protocol frozen',len(paths()),flush=True)
def inputs():
    verify(); INPUT.mkdir(); (BASE/'INCOMPLETE').write_text('Comparator pending complete independent validation\n')
    state('INPUT_BUILDING'); t=time.monotonic(); started=now()
    from rap_slam.real_dataset import load_scans
    from rap_slam.rap_backend import RAPBackend
    backend=RAPBackend.__new__(RAPBackend); backend.feature_extractor=None
    configs={}; rows=attempts(); census=[]
    for s,rr in rows.items():
        cfg=read(h.source(s)/'summary.json')['config']; configs[s]={k:cfg[k] for k in ['seed','rap_max_points','rap_voxel','odom_min_range','apply_kitti_205','min_overlap','max_mean_dist']}
        assert configs[s]==dict(seed=42,rap_max_points=4000,rap_voxel=.4,odom_min_range=1.5,apply_kitti_205=True,min_overlap=.7,max_mean_dist=2.5)
        prov=read(h.source(s)/'inference_provenance.json')['source_sha256']; assert sha(h.ROOT/'rap_slam/rap_backend.py')==prov['rap_slam/rap_backend.py']
        backend.voxel_size=.4; backend.max_points_per_scan=4000; backend.remove_outliers=True; backend.seed=42
        dest=INPUT/s; dest.mkdir()
        for i in sorted({r[k] for r in rr for k in ['i','j']}):
            raw,_=load_scans(str(scanpath(s,i).parent),start=i,end=i,min_range=1.5,kitti205=True)
            points,_=backend.preprocess(raw[0]); np.save(dest/f'{i:06d}.npy',points); census.append(dict(seq=s,frame=i,points=len(points)))
        for r in rr:
            a=np.load(dest/f"{r['i']:06d}.npy"); b=np.load(dest/f"{r['j']:06d}.npy"); ov,md=backend._alignment_metrics(a,b,np.array(r['T_rel']))
            assert abs(ov-r['overlap'])<=1e-6 and abs(md-r['mean_dist'])<=1e-6,(s,r['i'],r['j'],ov,md,r['overlap'],r['mean_dist'])
            assert (ov>=.7 and md<=2.5)==(r['status']=='accepted')
        cap(t); print('online inputs reproduced',s,len(rr),flush=True)
    save(INPUT/'attempts.json',rows); save(INPUT/'configs.json',configs); save(INPUT/'scan_census.json',census)
    torch,cfg,create,collate,to_cuda=geo.setup()
    from geotransformer.utils.data import calibrate_neighbors_stack_mode
    ds=[]
    for s,rr in rows.items():
        for r in rr:
            a=np.load(INPUT/s/f"{r['i']:06d}.npy"); b=np.load(INPUT/s/f"{r['j']:06d}.npy")
            ds.append(dict(ref_points=a,src_points=b,ref_feats=np.ones((len(a),1),dtype='float32'),src_feats=np.ones((len(b),1),dtype='float32'),transform=np.eye(4,dtype='float32')))
    limits=calibrate_neighbors_stack_mode(ds,collate,5,.3,1.275,keep_ratio=.8,sample_threshold=2000)
    save(INPUT/'neighbor_limits.json',dict(limits=limits.tolist(),keep_ratio=.8,sample_threshold=2000,pair_order=[dict(seq=s,attempt_id=r['attempt_id']) for s,rr in rows.items() for r in rr]))
    save(INPUT/'execution.json',dict(started_utc=started,completed_utc=now(),wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    verify(); cap(t); seal(INPUT,'input_seal.json'); state('INPUT_SEALED'); print('GT-free inputs and neighbor limits sealed',limits,flush=True)
def predictions():
    verify(); verify_seal(INPUT,'input_seal.json'); assert read(BASE/'input_validation.json')['passed']
    BANK.mkdir(); state('PREDICTIONS_RUNNING'); started=now(); t=time.monotonic()
    torch,cfg,create,collate,to_cuda=geo.setup(); model=create(cfg).cuda().eval()
    ckpt=torch.load(geo.B/'geotransformer-kitti.pth.tar',map_location='cpu',weights_only=True); model.load_state_dict(ckpt['model'],strict=True); del ckpt
    limits=read(INPUT/'neighbor_limits.json')['limits']; rows=read(INPUT/'attempts.json'); output={}; repeats={}
    from rap_slam.rap_backend import RAPBackend
    def infer(a,b):
        d=collate([dict(ref_points=a,src_points=b,ref_feats=np.ones((len(a),1),dtype='float32'),src_feats=np.ones((len(b),1),dtype='float32'),transform=np.eye(4,dtype='float32'))],5,.3,1.275,limits)
        with torch.inference_mode(): out=model(to_cuda(d))
        torch.cuda.synchronize(); pose=out['estimated_transform'].cpu().numpy().astype('float64'); conf=out['corr_scores'].cpu().numpy()
        assert pose.shape==(4,4) and np.isfinite(pose).all() and np.isfinite(conf).all()
        assert np.max(np.abs(pose[:3,:3].T@pose[:3,:3]-np.eye(3)))<1e-4 and abs(np.linalg.det(pose[:3,:3])-1)<1e-4
        return pose,dict(correspondences=len(conf),confidence_sum=float(conf.sum()),confidence_mean=float(conf.mean()) if len(conf) else 0,hierarchy_counts=[x.cpu().tolist() for x in d['lengths']])
    torch.cuda.reset_peak_memory_stats()
    for s,rr in rows.items():
        output[s]=[]
        for k,r in enumerate(rr):
            a=np.load(INPUT/s/f"{r['i']:06d}.npy"); b=np.load(INPUT/s/f"{r['j']:06d}.npy")
            pstart=time.monotonic(); pose,diagnostic=infer(a,b); wall=time.monotonic()-pstart; ov,md=RAPBackend._alignment_metrics(a,b,pose)
            output[s].append(dict(attempt_id=r['attempt_id'],i=r['i'],j=r['j'],T_rel=pose.tolist(),overlap=ov,mean_dist=md,accepted=bool(ov>=.7 and md<=2.5),wall_s=wall,diagnostic=diagnostic))
            if k==0:
                repeat,_=infer(a,b); delta=float(np.max(np.abs(repeat-pose))); assert delta<=1e-6; repeats[s]=dict(attempt_id=r['attempt_id'],max_pose_delta=delta,repeat=repeat.tolist())
            assert torch.cuda.max_memory_allocated()/2**30<8; cap(t); print('registered',s,k+1,'/',len(rr),'gate',output[s][-1]['accepted'],flush=True)
        save(BANK/f'{s}.json',output[s])
    assert sum(map(len,output.values()))==71
    save(BANK/'repeatability.json',repeats); save(BANK/'execution.json',dict(started_utc=started,completed_utc=now(),wall_s=time.monotonic()-t,peak_gpu_gib=torch.cuda.max_memory_allocated()/2**30,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,neighbor_limits=limits,input_validation_sha256=sha(BASE/'input_validation.json')))
    verify(); verify_seal(INPUT,'input_seal.json'); seal(BANK,'bank_seal.json'); state('BANK_SEALED'); print('all71 predictions sealed before evaluator GT',flush=True)
def branches(means):
    return {g:dict(ATE_path=m['C']['ate']<=.95*m['P']['ate'] and m['C']['ter']<=m['P']['ter']+.01,ter_path=m['C']['ter']<=m['P']['ter']-.01 and m['C']['ate']<=1.02*m['P']['ate']) for g,m in means.items()}
def evaluate():
    verify(); verify_seal(INPUT,'input_seal.json'); verify_seal(BANK,'bank_seal.json')
    EVAL.mkdir(); state('EVALUATING'); t=time.monotonic(); gt_start=now(); results={}; pairs={}; edgecounts={}
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    total_native=total_geo=0
    for s,n in h.SEQS.items():
        dest=EVAL/s; dest.mkdir(); cal=h.DATA/'sequences'/s/'calib.txt'; tr=_read_calib_transform(str(cal))
        gt=np.asarray(load_gt_poses(str(h.DATA/'poses'/f'{s}.txt'),str(cal),apply_calib=True)); o=h.poses(h.source(s)/'odom_poses.txt',n); keys=read(h.source(s)/'keyframes.json')
        native=read(INPUT/'attempts.json')[s]; pred=read(BANK/f'{s}.json'); saved=read(h.BASE/'attempt-01'/s/'edges.json'); fixed=[]; common=[]; pairs[s]=[]; by={r['attempt_id']:r for r in pred}
        for e in saved:
            r=next(r for r in native if r['selected_measurement_id']==e['measurement_id']); replacement=dict(e); replacement['T_rel']=by[r['attempt_id']]['T_rel']; fixed.append(replacement)
        for r,g in zip(native,pred):
            assert r['attempt_id']==g['attempt_id']; truth=np.linalg.inv(gt[r['i']])@gt[r['j']]
            pair=dict(attempt_id=r['attempt_id'],i=r['i'],j=r['j'],GT_far=bool(np.linalg.norm(gt[r['i'],:3,3]-gt[r['j'],:3,3])>15),native_accepted=r['status']=='accepted',geo_accepted=g['accepted'])
            for arm,pose in [('RAP',np.array(r['T_rel'])),('Geo',np.array(g['T_rel']))]:
                trans=float(np.linalg.norm(pose[:3,3]-truth[:3,3])); rot=float(np.degrees(np.arccos(np.clip((np.trace(pose[:3,:3].T@truth[:3,:3])-1)/2,-1,1))))
                pair[arm]=dict(translation_m=trans,rotation_deg=rot,strict=bool(trans<=1 and rot<=5),paper_threshold=bool(trans<=2 and rot<=5))
            total_native+=pair['RAP']['strict']; total_geo+=pair['Geo']['strict']; pairs[s].append(pair)
            if g['accepted']: common.append(dict(i=g['i'],j=g['j'],T_rel=g['T_rel'],overlap=g['overlap'],mean_dist=g['mean_dist'],measurement_id=g['attempt_id']))
        save(dest/'G_edges.json',fixed); save(dest/'C_edges.json',common); edgecounts[s]=dict(P=len(saved),G=len(fixed),C=len(common)); results[s]={}
        for arm,edges in [('P',saved),('G',fixed),('C',common)]:
            trajectory=h.replay(o,keys,edges); np.save(dest/f'{arm}.npy',trajectory)
            if arm=='P': assert np.max(np.abs(trajectory-np.load(h.BASE/'attempt-01'/s/'baseline.npy')))<=1e-9
            m,seg=h.metric(gt,tr,trajectory,True); results[s][arm]=m; save(dest/f'{arm}_segments.json',seg)
        cap(t); print('system metrics complete',s,edgecounts[s],flush=True)
    means={group:{a:{k:float(np.mean([results[s][a][k] for s in seqs])) for k in ['ate','ter','rer']} for a in ['P','G','C']} for group,seqs in [('development',list(h.SEQS)[:3]),('transfer_exposed',list(h.SEQS)[3:])]}
    gates=branches(means); safety={s:dict(ATE=results[s]['C']['ate']<=1.1*results[s]['P']['ate'],ter=results[s]['C']['ter']<=results[s]['P']['ter']+.03) for s in h.SEQS}
    signal=any(any(v.values()) for v in gates.values()) and all(all(v.values()) for v in safety.values()); decision='MATERIAL_COMMON_GATE_SYSTEM_SIGNAL' if signal else 'NO_MATERIAL_COMMON_GATE_SYSTEM_SIGNAL'
    save(BASE/'pair_outcomes.json',pairs); save(BASE/'results.json',dict(utc=now(),gt_read_started_utc=gt_start,bank_seal_sha256=sha(BASE/'bank_seal.json'),rows=results,cohort_means=means,edge_counts=edgecounts,opportunity=gates,safety=safety,candidate_strict=dict(RAP=total_native,Geo=total_geo,signal=total_geo>=total_native+5),decision=decision,wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    state('EVALUATED',decision=decision); print(decision,flush=True)
if __name__=='__main__':
    try: {'freeze':freeze,'inputs':inputs,'predictions':predictions,'evaluate':evaluate}[sys.argv[1]]()
    except Exception as e: state('STOPPED',failed_stage=sys.argv[1],error=repr(e)); raise
