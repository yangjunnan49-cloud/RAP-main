"""PFG1 frozen cached-geometry/graph screen with GT separation."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.metadata,json,resource,sys,time,traceback
import numpy as np
import gtsam
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM';DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
ROOTBASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BASE=ROOTBASE/'attempt-02';BANK=ROOTBASE/'bank';EV=BASE/'evaluation'
OLD=MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01';CACHE=MAIN/'docs/maintenance/2026-10-05/online-geotransformer-01'
PRE=MAIN/'docs/maintenance/2026-10-07/geometric-information-preflight-01'
SEQS={'00':4541,'05':2761,'06':1101,'07':1101,'09':1591,'10':1201}
GROUPS={'development':['00','05','06'],'transfer_exposed':['07','09','10']};ARMS=['N','S','Q']
sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]
import geometric_loop_information as alg
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def src(s):return MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in GROUPS['development'] else '2026-09-27/e0-heldout-01'}/full-{s}-A"
def poses(p):
    x=np.loadtxt(p).reshape(-1,3,4);o=np.tile(np.eye(4),(len(x),1,1));o[:,:3]=x;return o
def cap(start):assert time.perf_counter()-start<=3600 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
def freeze():
    assert read(PRE/'validation.json')['passed'] and read(CACHE/'input_validation.json')['passed'] and read(OLD/'validation.json')['passed']
    for p,h in read(PRE/'freeze.json')['files'].items():assert sha(p)==h
    files=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_geometric_information_screen_v2.py'),Path(__file__).with_name('validate_dense_propagation.py'),SLAM/'scripts/geometric_loop_information.py',SLAM/'rap_slam/pose_graph.py',SLAM/'rap_slam/real_dataset.py',SLAM/'rap_slam/trajectory_protocol.py',SLAM/'rap_slam/evaluate.py',SLAM/'scripts/eval_paper_metrics.py']
    files += [PRE/x for x in ['freeze.json','validation.json','validation_seal.json']] + [OLD/x for x in ['freeze.json','bank_seal.json','validation.json','results.json']] + [CACHE/x for x in ['input_seal.json','input_validation.json']]
    for p,h in read(CACHE/'input_seal.json')['files'].items():
        path=CACHE/'input-bank'/p;assert sha(path)==h;files.append(path)
    old=read(OLD/'freeze.json')['files']
    for s in SEQS:
        files += [src(s)/n for n in ['odom_poses.txt','optimized_poses.txt','keyframes.json','source_frames.json','accepted_loops.json','summary.json']]
        files += [DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt']
    for p in files:
        if str(p) in old:assert sha(p)==old[str(p)],p
    files += [ROOTBASE/'freeze.json',ROOTBASE/'bank_seal.json',ROOTBASE/'FAILURE_validation_bank.json',ROOTBASE/'AMENDMENT_01.md'] + [p for p in BANK.rglob('*') if p.is_file()]
    for p,h in read(ROOTBASE/'freeze.json')['files'].items():assert sha(p)==h,p
    save(BASE/'freeze.json',dict(utc=utc(),files={str(p):sha(p) for p in files},packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','gtsam','evo']},sequences=SEQS,original_loop_seconds=154.09,permutation=[1,2,0,4,5,3]))
    (BASE/'INCOMPLETE').write_text('PFG1 pending independent bank and metric validation\n')
    print('PFG1 frozen',len(set(files)),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in f['packages']}
def seal_verify():
    verify();seal=read(ROOTBASE/'bank_seal.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items():assert sha(BANK/p)==h,p
def graph(odom,kf,edges,shapes,arm):
    from rap_slam.pose_graph import optimize_pose_graph,propagate_to_full_trajectory
    if arm=='N':opt=optimize_pose_graph(list(odom),kf,edges)
    else:
        g=gtsam.NonlinearFactorGraph();values=gtsam.Values()
        for k in kf:values.insert(k,gtsam.Pose3(odom[k]))
        g.add(gtsam.PriorFactorPose3(kf[0],gtsam.Pose3(odom[kf[0]]),gtsam.noiseModel.Diagonal.Sigmas(np.full(6,.01))))
        od=gtsam.noiseModel.Diagonal.Sigmas(np.array([.05]*3+[.30]*3))
        for a,b in zip(kf[:-1],kf[1:]):g.add(gtsam.BetweenFactorPose3(a,b,gtsam.Pose3(np.linalg.inv(odom[a])@odom[b]),od))
        for e,d in zip(edges,shapes):
            noise=gtsam.noiseModel.Gaussian.SqrtInformation(d['A' if arm=='S' else 'AQ'])
            noise=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1.),noise)
            g.add(gtsam.BetweenFactorPose3(e['i'],e['j'],gtsam.Pose3(np.array(e['T_rel'])),noise))
        params=gtsam.LevenbergMarquardtParams();params.setMaxIterations(100);result=gtsam.LevenbergMarquardtOptimizer(g,values,params).optimize()
        opt={k:result.atPose3(k).matrix() for k in kf}
    full=np.asarray(propagate_to_full_trajectory(list(odom),kf,opt));return full,np.array([opt[k] for k in kf])
def bank():
    verify();started=utc();start=time.perf_counter();BANK.mkdir();normal_time=shape_time=system_time=0.;rows={};normal_count=0
    P=np.eye(6)[[1,2,0,4,5,3]]
    for s,n in SEQS.items():
        root=BANK/s;root.mkdir();(root/'normals').mkdir();(root/'shapes').mkdir()
        odom=poses(src(s)/'odom_poses.txt');kf=read(src(s)/'keyframes.json');frames=read(src(s)/'source_frames.json')['source_frame_ids'];assert frames==list(range(n))
        edges=[{k:e[k] for k in ['i','j','T_rel','mean_dist','overlap','measurement_id']} for e in read(src(s)/'accepted_loops.json')]
        save(root/'frames.json',dict(source_frame_ids=frames,keyframes=kf));save(root/'edges.json',edges)
        points={};normals={};supports=[];t=time.perf_counter()
        for frame in sorted({e[k] for e in edges for k in ['i','j']}):
            points[frame]=np.load(CACHE/f'input-bank/{s}/{frame:06d}.npy',allow_pickle=False).astype(float)
            normals[frame]=alg.measured_normals(points[frame]);nn,v,ids=normals[frame]
            np.savez(root/f'normals/{frame:06d}.npz',normals=nn,valid=v,neighbors=ids);normal_count+=1
        normal_time+=time.perf_counter()-t;t=time.perf_counter()
        for index,e in enumerate(edges):
            i,j=e['i'],e['j'];scale=np.clip(e['mean_dist'],1.,3.);sig=np.array([.03]*3+[.20]*3)*scale;Sigma=np.diag(sig**2)
            r=alg.geometry_information(np.array(e['T_rel']),points[i],points[j],*normals[i][:2],*normals[j][:2],Sigma)
            if not r['supported']:r.update(H=np.zeros((6,6)),Omega=np.diag(1/sig**2),A=np.diag(1/sig),rank=6)
            M=sig[:,None]*r['Omega']*sig[None,:];OmegaQ=(P@M@P.T)/sig[:,None]/sig[None,:]
            lam,V=np.linalg.eigh(OmegaQ);AQ=np.sqrt(np.maximum(lam,0))[:,None]*V.T
            d=dict(**r,Sigma=Sigma,OmegaQ=OmegaQ,AQ=AQ);np.savez(root/f'shapes/{index:03d}.npz',**d);supports.append(d)
        shape_time+=time.perf_counter()-t
        for arm in ARMS:
            t=time.perf_counter();full,keys=graph(odom,kf,edges,supports,arm)
            if arm=='S':system_time+=time.perf_counter()-t
            np.save(root/f'{arm}.npy',full);np.save(root/f'{arm}_keys.npy',keys)
        assert np.max(abs(np.load(root/'N.npy')-poses(src(s)/'optimized_poses.txt')))<1e-5
        rows[s]=dict(edges=len(edges),supported=sum(bool(x['supported']) for x in supports),matches=[len(x['ip']) for x in supports],ranks=[int(x['rank']) for x in supports])
        print('PFG1 bank',s,rows[s],flush=True);cap(start)
    assert sum(r['edges'] for r in rows.values())==58
    verify();wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    save(BANK/'execution.json',dict(started_utc=started,utc=utc(),rows=rows,normal_scans=normal_count,wall_s=wall,peak_rss_bytes=rss,normal_s=normal_time,shape_s=shape_time,S_graph_propagation_s=system_time,S_incremental_s=normal_time+shape_time+system_time,gt_read=False))
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<300*2**20
    save(BASE/'bank_seal.json',dict(utc=utc(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(BANK)):sha(p) for p in BANK.rglob('*') if p.is_file()}))
    print('PFG1 complete GT-free bank sealed',flush=True)
def gates(rows,means,execution):
    tests={}
    for name,m in means.items():
        tests[name+'_ter_gain']=m['N']['ter']-m['S']['ter']>=.01
        tests[name+'_ATE_gain']=1-m['S']['ate']/m['N']['ate']>=.05
        tests[name+'_direction_ter']=m['S']['ter']<m['Q']['ter']
        tests[name+'_direction_ATE']=m['S']['ate']<m['Q']['ate']
    for s,r in rows.items():tests[s+'_ter_safety']=r['S']['ter']<=r['N']['ter']+.01;tests[s+'_ATE_safety']=r['S']['ate']<=1.05*r['N']['ate']
    tests['10_noop']=float(np.max(abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/N.npy'))))<=1e-5
    tests['cost']=execution['S_incremental_s']<=.25*154.09
    return dict(tests=tests,decision='MEASURED_INFORMATION_SHAPE_ENGINEERING_SIGNAL' if all(tests.values()) else 'NO_MEASURED_INFORMATION_SHAPE_SIGNAL')
def evaluate():
    seal_verify();assert read(BASE/'bank_validation.json')['passed'];assert sha(BASE/'bank_validation.json')==read(BASE/'bank_validation_seal.json')['validation_sha256']
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    start=time.perf_counter();gt_start=utc();EV.mkdir();rows={};old=read(OLD/'results.json')
    for s,n in SEQS.items():
        dest=EV/s;dest.mkdir();calib=DATA/'sequences'/s/'calib.txt';gt=np.array(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(calib),apply_calib=True));tr=_read_calib_transform(str(calib));ti=np.linalg.inv(tr);ids=read(BANK/s/'frames.json')['source_frame_ids'];rows[s]={}
        for arm in ARMS:
            est=np.load(BANK/s/f'{arm}.npy');lidar=epm.evaluate_pair(list(gt),list(est),ids);camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@est@ti),ids)
            rows[s][arm]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segment_count=camera['kitti_segments'])
            save(dest/f'{arm}_segments.json',camera['kitti_segment_records'])
            if arm=='N':assert all(abs(rows[s][arm][k]-old['rows'][s]['full'][k])<=1e-5 for k in rows[s][arm])
        print('PFG1 evaluated',s,rows[s],flush=True);cap(start)
    means={g:{arm:{k:float(np.mean([rows[s][arm][k] for s in ss])) for k in ['ate','ter','rer']} for arm in ARMS} for g,ss in GROUPS.items()}
    save(BASE/'results.json',dict(utc=utc(),gt_read_started_utc=gt_start,bank_seal_sha256=sha(ROOTBASE/'bank_seal.json'),bank_validation_seal_sha256=sha(BASE/'bank_validation_seal.json'),rows=rows,cohort_means=means,gate=gates(rows,means,read(BANK/'execution.json')),wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    seal_verify();print('PFG1 evaluation',read(BASE/'results.json')['gate'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','evaluate']);a=p.parse_args()
    try:globals()[a.stage]()
    except Exception as e:
        path=BASE/f'FAILURE_{a.stage}.json'
        if not path.exists():save(path,dict(error=repr(e),traceback=traceback.format_exc()))
        raise
