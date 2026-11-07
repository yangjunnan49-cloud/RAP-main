"""Read-only RAP handoff audit. Writes only beside this audit script."""
import ast
import collections
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys
import traceback
import numpy as np

OUT = Path(__file__).resolve().parent
SLAM = Path('/mnt/e/githouse/RAP-SLAM')
RAP = Path('/mnt/e/githouse/RAP-main')
sys.path[:0] = [str(SLAM), str(SLAM / 'scripts'), str(RAP)]
report = {}
def run(name, fn):
    try:
        report[name] = fn()
    except Exception:
        report[name] = {'error': traceback.format_exc()}
    print(name, json.dumps(report[name], default=str), flush=True)
    (OUT / 'audit_results.json').write_text(json.dumps(report, indent=2, default=str))

def inventory():
    result = {}
    manifests = []
    for root in (RAP, SLAM):
        git = ['git', '-c', f'safe.directory={root}', '-C', str(root)]
        files = subprocess.check_output(git + ['ls-files'], text=True).splitlines()
        py = [f for f in files if f.endswith('.py') and '/_vendor/' not in f]
        errors = []
        for f in py:
            try: ast.parse((root / f).read_text(encoding='utf-8-sig'), filename=f)
            except Exception as e: errors.append([f, str(e)])
        result[root.name] = {'head': subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip(),
                             'status':subprocess.check_output(git+['status','--short'],text=True),
                             'tracked':len(files),'python_parsed':len(py),'syntax_errors':errors}
        for f in files:
            p = root / f
            if p.is_file() and p.stat().st_size < 2_000_000:
                manifests.append({'path':str(p),'bytes':p.stat().st_size,
                                  'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    for p in SLAM.glob('output*/**/*'):
        if p.is_file() and p.suffix in ('.json','.txt','.md') and p.stat().st_size < 10_000_000:
            manifests.append({'path':str(p),'bytes':p.stat().st_size,
                              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (OUT/'manifest.json').write_text(json.dumps(manifests,indent=2))
    result['manifest_entries'] = len(manifests)
    result['versions'] = {p:metadata.version(p) for p in
        ('numpy','scipy','torch','kiss-icp','gtsam','evo','scikit-learn','open3d','lightning','hydra-core')}
    return result

def feature_split():
    from eval_conformal_s1 import stratified_split, feat_vec, GATE_BASIC, GATE_EXTRA
    from build_s1_features import CAND_REF
    c = json.loads((SLAM/'output_s1/candidates.json').read_text())
    valid = [r for r in c if r.get('sc_margin') is not None]
    pool = [r for r in c if r['label'] in ('safe','dangerous') and feat_vec(r,GATE_BASIC+GATE_EXTRA) is not None]
    split = stratified_split(pool,42)
    def key(r): return CAND_REF[r['ds']],r['i'],r['j']
    sets = [set(map(key,s)) for s in split]
    return {'records':len(c),'margin_equals_negative_d1':sum(abs(r['sc_margin']+r['sc_d1'])<1e-5 for r in valid),
            'feature_records':len(valid),'split_sizes':list(map(len,split)),
            'physical_pair_overlap_fit_calib':len(sets[0]&sets[1]),
            'physical_pair_overlap_fit_test':len(sets[0]&sets[2]),
            'physical_pair_overlap_calib_test':len(sets[1]&sets[2]),
            'test_records_with_pair_in_fit':sum(key(r) in sets[0] for r in split[2]),
            'labels':dict(collections.Counter(r['label'] for r in c))}

def multigen_label():
    c=json.loads((SLAM/'output_s1/candidates.json').read_text())
    mg=json.loads((SLAM/'output_multigen/multigen_samples.json').read_text())['entries']
    from eval_paper_metrics import gt_for_live
    gt={'kitti02':gt_for_live('kitti','02',4661),'poss':gt_for_live('poss','A',1419)}
    names={'kitti02_true':'multigen_k02true','kitti02_false':'multigen_k02false','poss_true':'multigen_poss'}
    lut={(r['ds'],r['i'],r['j']):r for r in c}
    mismatches=[]; metric_mismatch=0; error_diffs=[]; total=0
    for e in mg:
        if e['ds'] not in names: continue
        r=lut[(names[e['ds']],e['i'],e['j'])]
        g=gt['poss' if e['ds']=='poss_true' else 'kitti02']
        best=max(e['gens'],key=lambda x:(x['overlap'],-x['mean_dist']))
        metric_mismatch += abs(best['mean_dist']-r['mean_dist'])>1e-8
        T=np.linalg.inv(g[e['i']])@g[e['j']]
        err=np.linalg.inv(T)@np.array(best['T_rel'])
        te=float(np.linalg.norm(err[:3,3])); re=float(np.rad2deg(np.arccos(np.clip((np.trace(err[:3,:3])-1)/2,-1,1))))
        actual='safe' if te<=5 and re<=10 else 'dangerous'
        if actual!=r['label']: mismatches.append({'ds':r['ds'],'i':r['i'],'j':r['j'],'saved':r['label'],'best_gen':actual,'te':te,'re':re})
        if r.get('gt_te') is not None: error_diffs.append(abs(te-r['gt_te']))
        total+=1
    return {'records':total,'best_overlap_mean_dist_not_same_generation':int(metric_mismatch),
            'best_gen_vs_saved_label_mismatches':mismatches,
            'median_abs_gt_te_difference':float(np.median(error_diffs))}

def goldens():
    from eval_calibrated_weighting import GOLDENS,load_poses_auto
    from eval_paper_metrics import gt_for_live,gt_from_summary,evaluate_pair
    from rap_slam.pose_graph import optimize_pose_graph,propagate_to_full_trajectory
    results={}
    ref=json.loads((SLAM/'output_s1/s1_report.json').read_text())['pgo']
    for name,(odom_f,kf_f,loops_f,source,seq,nms) in GOLDENS.items():
        odom=load_poses_auto(str(SLAM/odom_f)); kfs=json.loads((SLAM/kf_f).read_text()); loops=json.loads((SLAM/loops_f).read_text())
        matrices=np.array([x['T_rel'] for x in loops])
        gt=gt_for_live(source,seq,len(odom)) if source else gt_from_summary(str((SLAM/odom_f).parent))
        for lc in loops: lc['T_rel']=np.array(lc['T_rel'])
        opt=optimize_pose_graph(odom,kfs,loops,loop_nms_width=nms)
        full=propagate_to_full_trajectory(odom,kfs,opt)
        m=evaluate_pair(gt,full)
        results[name]={'n_odom':len(odom),'n_gt':len(gt),'n_kf':len(kfs),'loops':len(loops),'nms':nms,
                       'ape':m['ape_unaligned_rmse'],'reference':ref[name]['relfloor_rerun'],
                       'delta':m['ape_unaligned_rmse']-ref[name]['relfloor_rerun'],
                       'finite_edges':bool(np.isfinite(matrices).all()),
                       'max_rotation_orth_error':float(np.max(np.abs(matrices[:,:3,:3].transpose(0,2,1)@matrices[:,:3,:3]-np.eye(3))))}
        print('golden',name,results[name],flush=True)
    return results

def small_checks():
    from rap_slam import real_dataset,pose_graph
    from eval_paper_metrics import evaluate_pair
    from eval_map_consistency import crispness
    base=OUT/'fixture'; scans=base/'dataset/sequences/00/velodyne'; scans.mkdir(parents=True,exist_ok=True)
    poses=base/'dataset/poses'; poses.mkdir(exist_ok=True)
    gt=np.tile(np.eye(4),(6,1,1)); gt[:,0,3]=np.arange(6)
    np.savetxt(poses/'00.txt',gt[:,:3,:].reshape(6,12))
    for i in (0,2,3,4,5): np.array([[float(i),0,0,1]],dtype=np.float32).tofile(scans/f'{i:06d}.bin')
    loaded=real_dataset.load_real_sequence(str(base),start=0,end=5,stride=2)
    pts=np.array([[0,0,0]]+[[0.001*i,0,0] for i in range(1,10)]+[[0.05,0,0]],dtype=float)
    labels=np.array([0]*10+[1]); approx=crispness(pts,labels)[0]
    exact=float(np.mean([min(1,float(np.min(np.linalg.norm(pts[labels!=labels[i]]-p,axis=1)))) for i,p in enumerate(pts)]))
    bent=gt.copy(); bent[:,1,3]=np.arange(6)**2*0.1
    trunc=evaluate_pair(list(bent),list(bent[:4]))
    try:
        pose_graph.optimize_pose_graph(list(gt),[0,5],[],loop_clique_width=10)
        clique='no error'
    except Exception as e: clique=type(e).__name__+': '+str(e)
    return {'stride_missing_frame_scan_ids':[Path(p).stem for p in loaded['scan_files']],
            'stride_missing_frame_gt_x':loaded['gt_poses'][:,0,3].tolist(),
            'mismatched_trajectory_silently_accepted':trunc['n_frames'],
            'crispness_approx':approx,'crispness_exact':exact,'clique_no_loops':clique}

def metric_comparison():
    from eval_paper_metrics import gt_for_live,load_tum,kitti_drift
    rows={}
    for seq in ('01','02','03','04','06'):
        est=load_tum(str(SLAM/f'output_ros2/live_poses_kitti{seq}.txt')); gt=gt_for_live('kitti',seq,len(est))
        cum=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.array(gt)[:,:3,3],axis=0),axis=1))]
        vals=[]; counts={}
        for L in range(100,801,100):
            n=0
            for a in range(0,len(gt),10):
                b=int(np.searchsorted(cum,cum[a]+L,side='right'))
                if b>=len(gt): continue
                dg=np.linalg.inv(gt[a])@gt[b]; de=np.linalg.inv(est[a])@est[b]
                d=np.linalg.inv(de)@dg
                vals.append(np.linalg.norm(d[:3,3])/L*100); n+=1
            counts[L]=n
        rows[seq]={'current_length_macro_ter':kitti_drift(gt,est)['kitti_ter_pct'],
                   'pooled_segment_ter_same_lidar_frame':float(np.mean(vals)),
                   'segment_counts':counts}
    return rows

def datasets():
    root=Path('/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset/sequences')
    result={}
    for d in sorted(root.iterdir()):
        files=list((d/'velodyne').glob('*.bin'))
        ids=sorted(int(p.stem) for p in files if p.stem.isdigit())
        result[d.name]={'count':len(files),'non_numeric':len(files)-len(ids),
                        'first':ids[0] if ids else None,'last':ids[-1] if ids else None,
                        'contiguous':bool(ids and len(ids)==ids[-1]-ids[0]+1),
                        'sample_sizes_multiple_16':all(p.stat().st_size%16==0 for p in files[::max(1,len(files)//10)])}
    sp=Path('/mnt/e/githouse/Datasets/oxford_spires')
    result['spires']={'gt_files':len(list((sp/'gt').glob('*.txt'))),
                       'pcd_files':len(list(sp.glob('sequences/*/raw/lidar-clouds/*.pcd')))}
    return result

def rotation_audit():
    from eval_calibrated_weighting import GOLDENS
    from eval_paper_metrics import gt_for_live,gt_from_summary
    result={}
    for name,(odom_f,kf_f,loops_f,source,seq,nms) in GOLDENS.items():
        loops=json.loads((SLAM/loops_f).read_text())
        gt=gt_for_live(source,seq,4661 if seq=='02' else 1419 if source=='poss' else 1101) if source else gt_from_summary(str((SLAM/odom_f).parent))
        raw=[]; projected=[]
        for lc in loops:
            R=np.array(lc['T_rel'])[:3,:3]; Rg=(np.linalg.inv(gt[lc['i']])@gt[lc['j']])[:3,:3]
            u,s,v=np.linalg.svd(R); Q=u@np.diag([1,1,np.linalg.det(u@v)])@v
            angle=lambda m:float(np.rad2deg(np.arccos(np.clip((np.trace(m)-1)/2,-1,1))))
            raw.append(angle(Rg.T@R)); projected.append(angle(Rg.T@Q))
        result[name]={'raw_zero_count':sum(x==0 for x in raw),'n':len(raw),
                      'max_angle_change_deg':float(np.max(np.abs(np.array(raw)-projected))),
                      'median_raw_deg':float(np.median(raw)),'median_projected_deg':float(np.median(projected))}
    return result

def gpu_micro():
    import torch
    from rectified_point_flow.procrustes import solve_procrustes
    from rectified_point_flow.flow_model.layer import _flash_attn_varlen
    result={'cuda':torch.cuda.is_available()}
    if not result['cuda']: return result
    result['gpu']=torch.cuda.get_device_name(0)
    torch.manual_seed(42)
    x=torch.randn(4000,3,device='cuda')
    R=torch.tensor([[0.8,-0.6,0],[0.6,0.8,0],[0,0,1]],device='cuda')
    torch.backends.cuda.matmul.allow_tf32=False
    y=x@R.T+torch.tensor([0.1,0.2,0.3],device='cuda')
    for flag in (True,False):
        torch.backends.cuda.matmul.allow_tf32=flag
        r,t=solve_procrustes(x,y)
        rn=r.cpu().numpy().astype(float)
        result[f'tf32_{flag}']={'orth_error':float(np.max(np.abs(rn.T@rn-np.eye(3)))),
                                 'max_rotation_error':float(np.max(np.abs(rn-R.cpu().numpy())))}
    qkv=torch.randn(20,3,2,8,device='cuda'); cu=torch.tensor([0,7,20],dtype=torch.int32,device='cuda')
    got=_flash_attn_varlen(qkv,cu,13).float()
    expected=[]
    for a,b in ((0,7),(7,20)):
        q,k,v=qkv[a:b].unbind(1)
        scores=torch.einsum('ihd,jhd->hij',q,k)/(8**0.5)
        expected.append(torch.einsum('hij,jhd->ihd',scores.softmax(-1),v))
    result['attention_reference_max_diff']=float((got-torch.cat(expected)).abs().max())
    return result

def core_smoke():
    import runpy
    from rap_slam.scan_context import sc_distance,sc_distances_batch
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.cluster_gate import ClusterGate
    from rap_slam.pose_graph import nms_loop_edges
    rng=np.random.default_rng(8)
    db=rng.uniform(0,5,(6,20,60)); q=rng.uniform(0,5,(20,60)); db[:,:,:3]=0; q[:,:3]=0
    batch,shifts=sc_distances_batch(db,q)
    scalar=[sc_distance(x,q) for x in db]
    parts=[rng.normal(size=(300,3))*3+10,rng.normal(size=(200,3))-4]
    cond,s,cs,counts,anchor=RAPBackend._normalize_parts(parts)
    offset=0; errs=[]
    for p,c,n in zip(parts,cs,counts):
        errs.append(float(np.max(np.abs(cond[offset:offset+n]*s+c-p)))); offset+=n
    gate=ClusterGate()
    immediate=gate.add(0,300,1,0.2)
    strong=gate.add(1,301,0,0.05)
    nms=nms_loop_edges([{'i':0,'j':300,'overlap':0.8},{'i':1,'j':301,'overlap':0.9}],10)
    runpy.run_path(str(RAP/'test_smoke.py'),run_name='__main__')
    return {'sc_batch_scalar_max_diff':float(np.max(np.abs(batch-np.array(scalar)[:,0]))),
            'sc_shifts_match':bool(np.array_equal(shifts,np.array(scalar)[:,1])),
            'normalization_roundtrip_max_error':max(errs),'cluster_immediate_count':len(immediate),
            'cluster_strong_count':len(strong),'nms_retains_highest_overlap':nms[0]['overlap']==0.9,
            'existing_model_smoke':'completed; original smoke prints shapes, does not assert values'}

def shell_checks():
    out={}
    for root in (RAP,SLAM):
        git=['git','-c',f'safe.directory={root}','-C',str(root)]
        files=subprocess.check_output(git+['ls-files'],text=True).splitlines()
        paths=[root/f for f in files if f.endswith('.sh')]
        failures=[]
        for p in paths:
            r=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
            if r.returncode: failures.append({'path':str(p),'error':r.stderr})
        out[root.name]={'shells_checked':len(paths),'syntax_failures':failures}
    return out

if __name__=='__main__':
    checks={'inventory':inventory,'feature_split':feature_split,'multigen_label':multigen_label,
            'small_checks':small_checks,'metric_comparison':metric_comparison,'goldens':goldens,
            'datasets':datasets,'rotation_audit':rotation_audit,'gpu_micro':gpu_micro,
            'core_smoke':core_smoke,'shell_checks':shell_checks}
    if len(sys.argv)>1 and (OUT/'audit_results.json').exists():
        report=json.loads((OUT/'audit_results.json').read_text())
    for name in (sys.argv[1:] or ['inventory','feature_split','multigen_label','small_checks','metric_comparison','goldens']):
        run(name,checks[name])
