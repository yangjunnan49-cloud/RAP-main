"""Independent PFG1 brute-force surfaces, explicit graphs and scalar metrics."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,resource,sys,time,traceback
import numpy as np
import gtsam
from scipy.spatial.distance import cdist
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM';DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
ROOTBASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-screen-01';BASE=ROOTBASE/'attempt-02';BANK=ROOTBASE/'bank'
CACHE=MAIN/'docs/maintenance/2026-10-05/online-geotransformer-01/input-bank'
SEQS=['00','05','06','07','09','10'];ARMS=['N','S','Q']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def src(s):return MAIN/f"docs/maintenance/{'2026-09-26/e0-frontend-01' if s in SEQS[:3] else '2026-09-27/e0-heldout-01'}/full-{s}-A"
def pose(p):
    x=np.loadtxt(p).reshape(-1,3,4);a=np.tile(np.eye(4),(len(x),1,1));a[:,:3]=x;return a
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def verify():
    f=read(BASE/'freeze.json');seal=read(ROOTBASE/'bank_seal.json')
    for p,h in f['files'].items():assert sha(p)==h,p
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items():assert sha(BANK/p)==h,p
    assert seal['freeze_sha256']==sha(ROOTBASE/'freeze.json')
def nearby(p,k=20):
    indices=[]
    for begin in range(0,len(p),100):
        d=cdist(p[begin:begin+100],p,metric='sqeuclidean')
        indices.extend(np.argsort(d,axis=1,kind='stable')[:,:k])
    normals=[];valid=[]
    for ids in indices:
        local=p[ids];center=local.mean(axis=0);_,sing,Vt=np.linalg.svd(local-center,full_matrices=False);lam=sing[::-1]**2/k
        normals.append(Vt[-1]);valid.append(lam[1]>1e-12 and lam[1]-lam[0]>1e-10*max(1.,lam[-1]))
    return np.array(normals),np.array(valid),np.array(indices)
def closest(x,y):
    out=[]
    for begin in range(0,len(x),100):out.extend(np.argmin(cdist(x[begin:begin+100],y,'sqeuclidean'),axis=1))
    return np.array(out)
def graph(odom,kf,edges,infos):
    factors=gtsam.NonlinearFactorGraph();initial=gtsam.Values()
    for k in kf:initial.insert(k,gtsam.Pose3(odom[k]))
    factors.add(gtsam.PriorFactorPose3(kf[0],gtsam.Pose3(odom[kf[0]]),gtsam.noiseModel.Diagonal.Sigmas(np.repeat(.01,6))))
    for a,b in zip(kf[:-1],kf[1:]):
        relative=np.linalg.solve(odom[a],odom[b]);factors.add(gtsam.BetweenFactorPose3(a,b,gtsam.Pose3(relative),gtsam.noiseModel.Diagonal.Sigmas(np.array([.05,.05,.05,.30,.30,.30]))))
    for e,info in zip(edges,infos):
        lam,V=np.linalg.eigh(info);root=np.diag(np.sqrt(np.maximum(lam,0)))@V.T
        gaussian=gtsam.noiseModel.Gaussian.SqrtInformation(root);robust=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1),gaussian)
        factors.add(gtsam.BetweenFactorPose3(e['i'],e['j'],gtsam.Pose3(np.array(e['T_rel'])),robust))
    parameters=gtsam.LevenbergMarquardtParams();parameters.setMaxIterations(100);result=gtsam.LevenbergMarquardtOptimizer(factors,initial,parameters).optimize()
    keys=np.array([result.atPose3(k).matrix() for k in kf]);full=np.empty_like(odom)
    for index,k in enumerate(kf):
        end=kf[index+1] if index+1<len(kf) else len(odom);correction=keys[index]@np.linalg.inv(odom[k]);full[k:end]=correction@odom[k:end]
    return keys,full
def cap(start):assert time.perf_counter()-start<=3600 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=4*2**30
def bank():
    start=time.perf_counter();verify();execution=read(BANK/'execution.json');max_shape_delta=0.;max_pose_delta=0.;matches=0;normals_count=0;distances=0;loopcount=0;rows={};max_serialized_orth_error=0.;max_rigid_inverse_delta=0.
    P=np.eye(6)[[1,2,0,4,5,3]]
    for s in SEQS:
        root=BANK/s;edges=read(root/'edges.json');original=read(src(s)/'accepted_loops.json');expected=[{k:e[k] for k in ['i','j','T_rel','mean_dist','overlap','measurement_id']} for e in original];assert edges==expected
        odom=pose(src(s)/'odom_poses.txt');frames=read(root/'frames.json');kf=read(src(s)/'keyframes.json');assert frames==dict(source_frame_ids=list(range(len(odom))),keyframes=kf)
        points={};normals={};infos={a:[] for a in ARMS}
        for frame in sorted({e[k] for e in edges for k in ['i','j']}):
            p=np.load(CACHE/f'{s}/{frame:06d}.npy',allow_pickle=False).astype(float);points[frame]=p
            nn,v,ids=nearby(p);normals[frame]=(nn,v);saved=load(root/f'normals/{frame:06d}.npz')
            assert np.array_equal(ids,saved['neighbors']) and np.array_equal(v,saved['valid'])
            difference=np.max(abs(nn[v,:,None]*nn[v,None,:]-saved['normals'][v,:,None]*saved['normals'][v,None,:]));assert difference<1e-8
            normals_count+=1;distances+=len(p)**2
        for index,e in enumerate(edges):
            d=load(root/f'shapes/{index:03d}.npz');p=points[e['i']];q=points[e['j']];ni,vi=normals[e['i']];nj,vj=normals[e['j']];T=np.array(e['T_rel']);qp=q@T[:3,:3].T+T[:3,3]
            rigid=np.eye(4);rigid[:3,:3]=T[:3,:3].T;rigid[:3,3]=-T[:3,:3].T@T[:3,3]
            orth=float(np.max(abs(T[:3,:3].T@T[:3,:3]-np.eye(3))));max_serialized_orth_error=max(max_serialized_orth_error,orth);assert orth<1e-5
            assert np.max(abs(rigid-gtsam.Pose3(T).inverse().matrix()))<1e-12
            max_rigid_inverse_delta=max(max_rigid_inverse_delta,float(np.max(abs(rigid-np.linalg.inv(T)))))
            iq_to_ip=closest(qp,p);ip_to_iq=closest(p,qp);iq=np.arange(len(q));ip=iq_to_ip
            keep=(ip_to_iq[ip]==iq)&vi[ip]&vj&(np.sum((qp-p[ip])**2,axis=1)<=1.0);ip=ip[keep];iq=iq[keep]
            assert np.array_equal(ip,d['ip']) and np.array_equal(iq,d['iq']);matches+=len(ip);distances+=2*len(p)*len(q)
            sigma=np.array([.03]*3+[.20]*3)*min(max(float(e['mean_dist']),1.),3.);Sigma=np.diag(sigma*sigma);assert np.array_equal(Sigma,d['Sigma'])
            infoN=np.diag(1/(sigma*sigma));H=np.zeros((6,6));rowsJ=[]
            for pi,qj in zip(ip,iq):
                n=T[:3,:3].T@ni[pi];x=q[qj];rowsJ.append(np.r_[np.cross(x,n),n])
            inv=np.linalg.inv(T)
            for pi,qj in zip(ip,iq):
                y=T[:3,:3].T@(p[pi]-T[:3,3]);n=nj[qj];rowsJ.append(np.r_[np.cross(n,y),-n])
            for row in rowsJ:H+=np.outer(row,row)
            denominator=np.trace(Sigma@H);supported=len(ip)>0 and denominator>1e-20;assert supported==bool(d['supported'])
            if supported:
                assert np.allclose(H,d['H'],atol=1e-7,rtol=1e-9);info=6*H/denominator
                # Normal signs may flip; each row's outer product is invariant.
                J=np.array(rowsJ);assert J.shape==d['J'].shape
                assert np.allclose(J[:,:,None]*J[:,None,:],d['J'][:,:,None]*d['J'][:,None,:],atol=1e-7,rtol=1e-9)
            else:info=infoN;assert np.max(abs(d['H']))==0
            eig=np.linalg.eigvalsh(info);rank=int(np.count_nonzero(eig>1e-10*eig[-1]));assert rank==int(d['rank'])
            infoQ=(P@(sigma[:,None]*info*sigma[None,:])@P.T)/sigma[:,None]/sigma[None,:]
            for actual,saved in [(info,d['Omega']),(infoQ,d['OmegaQ']),(info,d['A'].T@d['A']),(infoQ,d['AQ'].T@d['AQ'])]:
                error=float(np.max(abs(actual-saved)));max_shape_delta=max(max_shape_delta,error);assert error<1e-7
            assert abs(np.trace(Sigma@info)-6)<1e-8 and abs(np.trace(Sigma@infoQ)-6)<1e-8
            assert np.max(abs(np.linalg.eigvalsh(sigma[:,None]*info*sigma[None,:])-np.linalg.eigvalsh(sigma[:,None]*infoQ*sigma[None,:])))<1e-8
            infos['N'].append(infoN);infos['S'].append(info);infos['Q'].append(infoQ);loopcount+=1
        rows[s]={}
        for arm in ARMS:
            keys,full=graph(odom,kf,edges,infos[arm]);saved_keys=np.load(root/f'{arm}_keys.npy');saved_full=np.load(root/f'{arm}.npy')
            error=max(float(np.max(abs(keys-saved_keys))),float(np.max(abs(full-saved_full))));max_pose_delta=max(max_pose_delta,error);assert error<1e-5,(s,arm,error)
            assert np.isfinite(saved_full).all() and np.max(abs(saved_full[:,3]-np.array([0,0,0,1])))<1e-10
            R=saved_full[:,:3,:3];assert np.max(abs(R.transpose(0,2,1)@R-np.eye(3)))<1e-5 and np.max(abs(np.linalg.det(R)-1))<1e-5
            rows[s][arm]=error
        assert np.max(abs(np.load(root/'N.npy')-pose(src(s)/'optimized_poses.txt')))<1e-5
        print('PFG1 independent bank',s,'edges',len(edges),'trajectory delta',rows[s],flush=True);cap(start)
    assert loopcount==58 and normals_count==execution['normal_scans'];verify()
    save(BASE/'bank_validation.json',dict(utc=utc(),passed=True,normal_scans=normals_count,loops=loopcount,matches=matches,brute_force_distances=distances,max_information_delta=max_shape_delta,max_trajectory_delta=max_pose_delta,trajectory_deltas=rows,max_serialized_orth_error=max_serialized_orth_error,max_rigid_vs_matrix_inverse_delta=max_rigid_inverse_delta,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,gt_read=False))
    save(BASE/'bank_validation_seal.json',dict(utc=utc(),validation_sha256=sha(BASE/'bank_validation.json'),bank_seal_sha256=sha(ROOTBASE/'bank_seal.json')))
    print('PFG1 independent GT-free bank validated',flush=True)
def evaluate():
    start=time.perf_counter();verify();result=read(BASE/'results.json');assert read(BASE/'bank_validation.json')['passed']
    assert read(ROOTBASE/'freeze.json')['utc']<read(BANK/'execution.json')['started_utc']<read(ROOTBASE/'bank_seal.json')['utc']<read(BASE/'bank_validation_seal.json')['utc']<result['gt_read_started_utc']
    assert read(BASE/'freeze.json')['utc']<read(BASE/'bank_validation.json')['utc']
    assert result['bank_validation_seal_sha256']==sha(BASE/'bank_validation_seal.json') and result['bank_seal_sha256']==sha(ROOTBASE/'bank_seal.json')
    # These historical independent functions use scalar segment logic and one
    # proper rigid alignment; they import no new runner/algorithm or evo metric.
    sys.path.insert(0,str(Path(__file__).parent))
    from validate_dense_propagation import segments,aligned_rmse,calibration
    actual={};records=0;max_metric_delta=0.;old=read(MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01/results.json')
    for s in SEQS:
        cam=pose(DATA/'poses'/f'{s}.txt');tr=calibration(s);ti=np.linalg.inv(tr);gt=ti@cam@tr;ids=read(BANK/s/'frames.json')['source_frame_ids'];actual[s]={}
        for arm in ARMS:
            est=np.load(BANK/s/f'{arm}.npy');rows=segments(cam,tr@est@ti,ids);saved=read(BASE/f'evaluation/{s}/{arm}_segments.json');assert len(rows)==len(saved)
            for a,b in zip(rows,saved):
                for k in ['first','last','source_first','source_last','length_m']:assert a[k]==b[k]
                assert abs(a['translation_fraction']-b['translation_fraction'])<1e-9 and abs(a['rotation_rad_per_m']-b['rotation_rad_per_m'])<1e-8 and abs(a['speed_mps']-b['speed_mps'])<1e-8
            records+=len(rows);m=dict(ate=aligned_rmse(gt,est),ter=float(np.mean([x['translation_fraction'] for x in rows])*100),rer=float(np.mean([x['rotation_rad_per_m'] for x in rows])*180/np.pi*100),segment_count=len(rows));actual[s][arm]=m
            for k,v in m.items():error=abs(v-result['rows'][s][arm][k]);max_metric_delta=max(max_metric_delta,error);assert error<1e-6
            if arm=='N':assert all(abs(m[k]-old['rows'][s]['full'][k])<1e-5 for k in m)
        print('PFG1 independent metrics',s,flush=True);cap(start)
    means={g:{a:{k:float(np.mean([actual[s][a][k] for s in ss])) for k in ['ate','ter','rer']} for a in ARMS} for g,ss in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    tests={}
    for g,m in means.items():
        for a in ARMS:
            for k in m[a]:assert abs(m[a][k]-result['cohort_means'][g][a][k])<1e-6
        tests[g+'_ter_gain']=m['N']['ter']-m['S']['ter']>=.01;tests[g+'_ATE_gain']=1-m['S']['ate']/m['N']['ate']>=.05
        tests[g+'_direction_ter']=m['S']['ter']<m['Q']['ter'];tests[g+'_direction_ATE']=m['S']['ate']<m['Q']['ate']
    for s,r in actual.items():tests[s+'_ter_safety']=r['S']['ter']<=r['N']['ter']+.01;tests[s+'_ATE_safety']=r['S']['ate']<=1.05*r['N']['ate']
    delta10=float(np.max(abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/N.npy'))));tests['10_noop']=delta10<=1e-5
    execution=read(BANK/'execution.json');tests['cost']=execution['S_incremental_s']<=154.09*.25
    decision='MEASURED_INFORMATION_SHAPE_ENGINEERING_SIGNAL' if all(tests.values()) else 'NO_MEASURED_INFORMATION_SHAPE_SIGNAL';assert tests==result['gate']['tests'] and decision==result['gate']['decision']
    verify();save(BASE/'validation.json',dict(utc=utc(),passed=True,decision=decision,independent_segment_records=records,max_metric_delta=max_metric_delta,sequence10_delta=delta10,wall_s=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    save(BASE/'validation_seal.json',dict(utc=utc(),validation_sha256=sha(BASE/'validation.json'),results_sha256=sha(BASE/'results.json'),evaluation_files={str(p.relative_to(BASE/'evaluation')):sha(p) for p in (BASE/'evaluation').rglob('*') if p.is_file()}))
    (BASE/'INCOMPLETE').unlink();print('PFG1 fully validated',decision,records,'segments',flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['bank','evaluate']);args=parser.parse_args()
    try:globals()[args.stage]()
    except Exception as e:
        p=BASE/f'FAILURE_validation_{args.stage}.json'
        if not p.exists():save(p,dict(error=repr(e),traceback=traceback.format_exc()))
        raise
