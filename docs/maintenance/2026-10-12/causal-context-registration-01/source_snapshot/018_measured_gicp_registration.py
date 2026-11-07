"""MGR0 CPU-only physical measurement experiment; see frozen protocol."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import hashlib
import importlib.metadata
import json
import resource
import signal
import sys
import time
import traceback
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import scan_level_graph_feasibility as old

MAIN=old.MAIN; SLAM=old.SLAM; DATA=old.DATA
BASE=MAIN/'docs/maintenance/2026-10-12/measured-gicp-registration-01'
SUP=BASE/'supervision'; INPUT=BASE/'input'; PILOT=BASE/'pilot'; BANK=BASE/'bank'
CACHE=MAIN/'docs/maintenance/2026-10-05/online-geotransformer-01'
SEQS=tuple(old.SEQS); ACTIVE=SEQS[:-1]
sys.path.insert(0,str(SLAM/'scripts'))
import geometric_loop_information as shape
from rap_slam.real_dataset import load_scans
assert o3d.__DEVICE_API__=='cpu' and o3d.__version__=='0.19.0'

read,sha,save,now=old.read,old.sha,old.save,old.now
def rigid(t): return old.proper(np.asarray([t]))[0]
def cloud(p,n=None):
    out=o3d.geometry.PointCloud(); out.points=o3d.utility.Vector3dVector(p)
    if n is not None:
        out.normals=o3d.utility.Vector3dVector(n)
        out.covariances=o3d.utility.Matrix3dVector(covariances(n))
    return out
def covariances(n): return np.eye(3)[None]-.999*np.einsum('ni,nj->nij',n,n)
def transform(p,t): return p@t[:3,:3].T+t[:3,3]
def exp(x): return old.gtsam.Pose3.Expmap(x).matrix()
def proper(t):
    return bool(np.isfinite(t).all() and t.shape==(4,4) and np.max(abs(t[3]-[0,0,0,1]))<=1e-12 and
                np.max(abs(t[:3,:3].T@t[:3,:3]-np.eye(3)))<=1e-5 and abs(np.linalg.det(t[:3,:3])-1)<=1e-5)
def rows():
    result=[]
    for s in ACTIVE:
        for k,e in enumerate(old.loop_records(s)):
            result.append(dict(seq=s,index=k,**e))
    assert len(result)==58
    return result
def pilot_rows(): return [e for e in rows() if e['seq'] in SEQS[:3] and e['index']==0]
def needed():
    result={s:sorted({e[k] for e in rows() if e['seq']==s for k in ('i','j')}) for s in ACTIVE}
    for s,ids in result.items(): assert min(ids)>=0 and max(ids)<old.SEQS[s]
    return result
def holdout_frame(i): return i-1 if i>0 else 1
def raw(s,i): return DATA/'sequences'/s/'velodyne'/f'{i:06d}.bin'
def preprocess(s,i):
    points,_=load_scans(str(raw(s,i).parent),start=i,end=i,min_range=1.5,kitti205=True)
    pc=cloud(points[0].astype(float)).voxel_down_sample(.4)
    pc,_=pc.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5)
    p=np.asarray(pc.points,dtype=np.float32)
    if len(p)>4000: p=p[np.random.default_rng(42).choice(len(p),4000,replace=False)]
    assert len(p)>=200 and np.isfinite(p).all()
    return p
def estimate(p):
    n,valid,ids=shape.measured_normals(p)
    # Flag invalid estimates; isotropic covariance there is a declared control.
    n[~valid]=0.
    return n,valid,ids
def diagnostics(t,p,q,np_,nq,vp,vq):
    mapped=transform(q,t); di,ip=cKDTree(p).query(mapped); dr,iq=cKDTree(mapped).query(p)
    keep=(di<=2.5)&vp[ip]&vq&(iq[ip]==np.arange(len(q)))
    sq=np.flatnonzero(keep); tp=ip[keep]; count=len(sq)
    if count:
        jq=np.asarray([n@t[:3,:3]@np.column_stack([-old.skew(x),np.eye(3)]) for x,n in zip(q[sq],np_[tp])])
        reverse=(p[tp]-t[:3,3])@t[:3,:3]
        jp=np.asarray([n@np.column_stack([old.skew(x),-np.eye(3)]) for x,n in zip(reverse,nq[sq])])
        h=np.vstack([jq,jp]).T@np.vstack([jq,jp]); eigen=np.linalg.eigvalsh((h+h.T)/2)
        rank=int(np.count_nonzero(eigen>max(eigen[-1],1e-30)*1e-6))
    else: h=np.zeros((6,6)); eigen=np.zeros(6); rank=0
    cq=covariances(nq); cp=covariances(np_); keep_inlier=di<=2.5; ids=np.flatnonzero(keep_inlier)
    if len(ids):
        d=mapped[ids]-p[ip[ids]]; m=cp[ip[ids]]+t[:3,:3]@cq[ids]@t[:3,:3].T
        cost=float(np.mean(np.einsum('ni,ni->n',d,np.linalg.solve(m,d[...,None])[...,0])))
    else: cost=None
    forward=float(np.mean(di<=2.5)); reverse_coverage=float(np.mean(dr<=2.5))
    score=float((np.mean(np.minimum(di,2.5)**2)+np.mean(np.minimum(dr,2.5)**2))/2)
    supported=proper(t) and count>=100 and min(forward,reverse_coverage)>=.7 and rank==6
    return dict(supported=bool(supported),mutual_valid=count,overlap_forward=forward,overlap_reverse=reverse_coverage,
                rank=rank,eigenvalues=eigen.tolist(),surface_H=h.tolist(),gicp_inlier_mean_cost=cost,
                censored_symmetric_mse=score,ip=tp.tolist(),iq=sq.tolist())
def diagnostic_objective(t,p,q,cp,cq):
    r=transform(q,t)-p; m=cp+t[:3,:3]@cq@t[:3,:3].T; v=np.linalg.solve(m,r[...,None])[...,0]
    j=np.asarray([t[:3,:3]@np.column_stack([-old.skew(x),np.eye(3)]) for x in q])
    gradient=2*np.einsum('nki,nk->i',j,v)
    for a in range(3):
        k=old.skew(np.eye(3)[a]); dm=t[:3,:3]@(k@cq-cq@k)@t[:3,:3].T
        gradient[a]-=np.einsum('ni,nij,nj->',v,dm,v)
    values,vec=np.linalg.eigh(m); w=(vec/np.sqrt(values)[:,None,:])@vec.transpose(0,2,1)
    jac=w@j; residual=(w@r[...,None])[...,0]
    return float(np.einsum('ni,ni->',r,v)),gradient,jac,residual,w
def register(p,q,np_,nq,t):
    estimator=o3d.pipelines.registration.TransformationEstimationForGeneralizedICP(.001,o3d.pipelines.registration.L2Loss())
    criterion=o3d.pipelines.registration.ICPConvergenceCriteria(relative_fitness=1e-6,relative_rmse=1e-6,max_iteration=80)
    start=time.monotonic()
    result=o3d.pipelines.registration.registration_generalized_icp(cloud(q,nq),cloud(p,np_),2.5,t,estimator,criterion)
    out=np.asarray(result.transformation); assert proper(out)
    return out,dict(wall_seconds=time.monotonic()-start,fitness=float(result.fitness),euclidean_inlier_rmse=float(result.inlier_rmse),
                    correspondence_count=len(result.correspondence_set),max_iterations=80)
def global_init(p,q,np_,nq):
    a,b=cloud(p,np_),cloud(q,nq); search=o3d.geometry.KDTreeSearchParamHybrid(radius=2.,max_nn=100)
    start=time.monotonic(); fa=o3d.pipelines.registration.compute_fpfh_feature(a,search); fb=o3d.pipelines.registration.compute_fpfh_feature(b,search)
    assert np.isfinite(fa.data).all() and np.isfinite(fb.data).all()
    o3d.utility.random.seed(20261012)
    option=o3d.pipelines.registration.FastGlobalRegistrationOption(division_factor=1.4,use_absolute_scale=True,decrease_mu=True,
        maximum_correspondence_distance=2.5,iteration_number=64,tuple_scale=.95,maximum_tuple_count=1000,tuple_test=True)
    result=o3d.pipelines.registration.registration_fgr_based_on_feature_matching(b,a,fb,fa,option)
    out=np.asarray(result.transformation); assert proper(out)
    return out,dict(wall_seconds=time.monotonic()-start,fitness=float(result.fitness),feature_dimensions=[list(fa.data.shape),list(fb.data.shape)])
def select(candidates,names,native):
    good=[name for name in names if candidates[name]['status']=='completed' and candidates[name]['diagnostics']['supported']]
    if not good: return native.copy(),dict(selected='N',fallback=True)
    chosen=min(good,key=lambda name:candidates[name]['diagnostics']['censored_symmetric_mse'])
    return np.asarray(candidates[chosen]['T']),dict(selected=chosen,fallback=False)
def fixed_inputs():
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',BASE/'SETUP_RECORD.md',BASE/'AMENDMENT_01.md',Path(__file__),Path(__file__).with_name('validate_measured_gicp.py'),
        Path(__file__).with_name('invoke_supervised_wsl_current.ps1'),SLAM/'scripts/geometric_loop_information.py',CACHE/'input_seal.json',CACHE/'input_validation.json',
        Path(o3d.pybind.__file__),Path(o3d.__file__)]
    paths += [p for p in (BASE/'prefreeze-attempt01').rglob('*') if p.is_file()]
    paths += [BASE/'FAILURE_freeze.json']+[p for p in (SUP/'freeze').rglob('*') if p.is_file()]
    for s,ids in needed().items():
        for i in sorted(set(ids+[holdout_frame(a) for a in ids])): paths.append(raw(s,i))
        paths += [CACHE/f'input-bank/{s}/{i:06d}.npy' for i in ids]
    return paths
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','open3d','gtsam','evo')}
    assert f['repositories']==old.repositories()
def freeze():
    old.verify(); files=dict(read(old.BASE/'freeze.json')['files']); seal=read(old.BASE/'DELIVERY_SEAL.json')
    for r in seal['files']:
        p=old.BASE/r['path']; assert sha(p)==r['sha256']; files[str(p)]=r['sha256']
    files[str(old.BASE/'DELIVERY_SEAL.json')]=sha(old.BASE/'DELIVERY_SEAL.json')
    inputseal=read(CACHE/'input_seal.json')
    for p in fixed_inputs():
        if CACHE/'input-bank' in p.parents: assert sha(p)==inputseal['files'][str(p.relative_to(CACHE/'input-bank'))]
        files[str(p)]=sha(p)
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for p in fixed_inputs():
        if p.suffix in ('.py','.ps1'):
            label=('open3d_entry.py' if p==Path(o3d.__file__) else p.name); (snapshot/label).write_bytes(p.read_bytes())
    api=dict(utc=now(),version=o3d.__version__,selected_device=o3d.__DEVICE_API__,binary=str(Path(o3d.pybind.__file__)),
        gicp=o3d.pipelines.registration.registration_generalized_icp.__doc__,fgr=o3d.pipelines.registration.registration_fgr_based_on_feature_matching.__doc__,
        covariances=o3d.geometry.PointCloud.covariances.__doc__)
    save(BASE/'API_RECORD.json',api)
    save(BASE/'freeze.json',dict(utc=now(),files=files,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','open3d','gtsam','evo')},
        repositories=old.repositories(),rows=rows(),pilot=pilot_rows(),cap_seconds=1800,cap_RSS_bytes=4*2**30,cap_artifact_bytes=512*2**20,
        api_sha256=sha(BASE/'API_RECORD.json'),prior_delivery_entries=seal['entries']))
    (BASE/'INCOMPLETE').write_text('MGR0 numerical and scientific comparison pending.\n')
    print('MGR0 frozen',len(files),'identities,58 fixed edges',flush=True)
def fixture():
    grid=np.asarray([[x,y] for x in np.linspace(-1,1,7) for y in np.linspace(-1,1,7)])
    a=np.column_stack([np.full(len(grid),2.),grid]); b=np.column_stack([grid[:,0],np.full(len(grid),-2.),grid[:,1]])
    c=np.column_stack([grid,np.full(len(grid),.5)])
    return np.concatenate([a,b,c]),np.repeat(np.eye(3),len(grid),axis=0)
def preflight():
    verify(); dest=BASE/'synthetic'; dest.mkdir(); q,nq=fixture(); truth=exp(np.array([.012,-.02,.018,.03,-.02,.015])); p=transform(q,truth); np_=nq@truth[:3,:3].T
    outputs={}; tests={}
    for name,a,b,na,nb,known in [('forward',p,q,np_,nq,truth),('reverse',q,p,nq,np_,np.linalg.inv(truth))]:
        fitted,info=register(a,b,na,nb,np.eye(4)); delta=float(np.max(abs(fitted-known))); assert delta<=1e-4; outputs[name]=dict(T=fitted.tolist(),diagnostics=info)
        tests[name+'_known']=delta
    gauge=exp(np.array([.11,-.09,.07,.4,.2,-.3])); ga,gb=transform(p,gauge),transform(q,gauge)
    gfit,ginfo=register(ga,gb,np_@gauge[:3,:3].T,nq@gauge[:3,:3].T,np.eye(4)); expected=gauge@truth@np.linalg.inv(gauge)
    tests['common_frame_error']=float(np.max(abs(gfit-expected))); assert tests['common_frame_error']<=1e-4
    outputs['gauge']=dict(T=gfit.tolist(),diagnostics=ginfo)
    test=truth@exp(np.array([.018,-.009,.012,.015,-.02,.01])); cp,cq=covariances(np_),covariances(nq)
    cost,grad,jac,res,w=diagnostic_objective(test,p,q,cp,cq); fd=[]; jfd=[]; h=1e-6
    for k in range(6):
        d=np.eye(6)[k]*h; plus=test@exp(d); minus=test@exp(-d)
        fd.append((diagnostic_objective(plus,p,q,cp,cq)[0]-diagnostic_objective(minus,p,q,cp,cq)[0])/(2*h))
        jfd.append((np.einsum('nij,nj->ni',w,transform(q,plus)-p)-np.einsum('nij,nj->ni',w,transform(q,minus)-p))/(2*h))
    fd=np.asarray(fd); jfd=np.stack(jfd,axis=2)
    ge=float(np.linalg.norm(fd-grad)/max(np.linalg.norm(grad),1e-30)); je=float(np.max(abs(jfd-jac)))
    assert ge<=1e-5 and je<=1e-6
    non=diagnostics(truth,p,q,np_,nq,np.ones(len(p),bool),np.ones(len(q),bool)); assert non['rank']==6
    plane=np.asarray([[x,y,0.] for x in np.linspace(-3,3,15) for y in np.linspace(-3,3,15)]); pn=np.tile([0.,0.,1.],(len(plane),1))
    planar=diagnostics(np.eye(4),plane,plane,pn,pn,np.ones(len(plane),bool),np.ones(len(plane),bool)); assert planar['rank']==3 and not planar['supported']
    periodic=np.concatenate([q+[6*k,0,0] for k in range(-2,3)]); normals=np.tile(nq,(5,1)); ambiguity=[]
    for shift in (0.,6.):
        initial=np.eye(4); initial[0,3]=shift; result,info=register(periodic,periodic,normals,normals,initial)
        dr=diagnostics(result,periodic,periodic,normals,normals,np.ones(len(periodic),bool),np.ones(len(periodic),bool))
        assert dr['supported'] and dr['gicp_inlier_mean_cost']<=1e-12
        ambiguity.append(dict(T=result.tolist(),diagnostics=dr,solver=info))
    assert np.linalg.norm(np.asarray(ambiguity[1]['T'])[:3,3]-np.asarray(ambiguity[0]['T'])[:3,3])>=5.9
    disjoint=diagnostics(np.eye(4),q+100,q,nq,nq,np.ones(len(q),bool),np.ones(len(q),bool)); assert not disjoint['supported'] and disjoint['mutual_valid']==0
    np.savez(dest/'fixture.npz',p=p,q=q,np=np_,nq=nq,truth=truth,gauge=gauge,test=test,cp=cp,cq=cq,cost=cost,gradient=grad,fd=fd,jacobian=jac,jacobian_fd=jfd,
        plane=plane,plane_normals=pn,periodic=periodic,periodic_normals=normals)
    save(dest/'results.json',dict(utc=now(),recovery_tests=tests,outputs=outputs,gradient_relative_error=ge,frozen_whitening_jacobian_max=je,
        nondegenerate=non,plane=planar,periodic=ambiguity,disjoint=disjoint))
    seal(dest,'synthetic_seal.json'); print('synthetic GICP, derivative, rank, ambiguity/support fixtures sealed',flush=True)
def seal(folder,name):
    save(BASE/name,dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder,name):
    f=read(BASE/name); assert f['freeze_sha256']==sha(BASE/'freeze.json')
    assert f['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def inputs():
    verify(); assert read(BASE/'preflight_validation.json')['passed']; INPUT.mkdir(); info=[]
    pilot_ids={(e['seq'],e[k]) for e in pilot_rows() for k in ('i','j')}
    for s,ids in needed().items():
        (INPUT/s).mkdir(); odom=old.load(old.src(s)/'odom_poses.txt')
        for i in ids:
            p=np.load(CACHE/f'input-bank/{s}/{i:06d}.npy',allow_pickle=False)
            repro=None
            if (s,i) in pilot_ids:
                rebuilt=preprocess(s,i); assert rebuilt.shape==p.shape; repro=float(np.max(abs(rebuilt-p))); assert repro<=1e-6
            n,valid,nn=estimate(p.astype(float)); np.savez(INPUT/s/f'{i:06d}.npz',points=p,normals=n,valid=valid,neighbors=nn)
            hf=holdout_frame(i); hp=preprocess(s,hf); relative=np.linalg.inv(odom[i])@odom[hf]; held=transform(hp.astype(float),relative)
            np.savez(INPUT/s/f'{i:06d}_holdout.npz',points=held,local_points=hp,relative=relative,source_frame=hf)
            info.append(dict(seq=s,frame=i,points=len(p),valid_normals=int(valid.sum()),raw_sha256=sha(raw(s,i)),
                cache_sha256=sha(CACHE/f'input-bank/{s}/{i:06d}.npy'),pilot_reprocess_max_delta=repro,holdout_frame=hf,holdout_points=len(hp)))
        cap(); print('physical inputs',s,len(ids),flush=True)
    save(INPUT/'census.json',dict(utc=now(),scans=info,rows=rows())); seal(INPUT,'input_seal.json')
    print('physical inputs and whole-scan holdout sealed',flush=True)
def predict_one(e):
    s,i,j=e['seq'],e['i'],e['j']; a=np.load(INPUT/s/f'{i:06d}.npz'); b=np.load(INPUT/s/f'{j:06d}.npz')
    p,q=a['points'].astype(float),b['points'].astype(float); np_,nq=a['normals'],b['normals']; vp,vq=a['valid'],b['valid']
    native=rigid(np.asarray(e['T_rel'])); od=old.load(old.src(s)/'odom_poses.txt'); kiss=rigid(np.linalg.inv(od[i])@od[j])
    candidates={}; starts=dict(RI=native,GI=np.eye(4),GK=kiss); f=None; finfo=None
    try:
        f,finfo=global_init(p,q,np_,nq); starts['GF']=f
    except Exception as error: candidates['GF']=dict(status='failed',error=repr(error),T=None,diagnostics=None)
    for name,t in starts.items():
        try:
            out,solver=register(p,q,np_,nq,t); diag=diagnostics(out,p,q,np_,nq,vp,vq)
            candidates[name]=dict(status='completed',T=out.tolist(),initial=t.tolist(),solver=solver,diagnostics=diag)
        except Exception as error: candidates[name]=dict(status='failed',error=repr(error),T=None,initial=t.tolist(),diagnostics=None)
    w,wi=select(candidates,('GI','GK','GF'),native); jj,ji=select(candidates,('RI','GK','GF'),native)
    predictions=dict(N=native.tolist(),K=kiss.tolist(),F=None if f is None else f.tolist(),W=w.tolist(),J=jj.tolist())
    for name,value in candidates.items(): predictions[name]=value['T']
    hpa=np.load(INPUT/s/f'{i:06d}_holdout.npz')['points']; hpb=np.load(INPUT/s/f'{j:06d}_holdout.npz')['points']; heldout={}
    for name,t in predictions.items():
        if t is not None:
            mapped=transform(hpb,np.asarray(t)); d1=cKDTree(hpa).query(mapped)[0]; d2=cKDTree(mapped).query(hpa)[0]
            heldout[name]=dict(censored_symmetric_mse=float((np.mean(np.minimum(d1,2.5)**2)+np.mean(np.minimum(d2,2.5)**2))/2),
                overlap_forward=float(np.mean(d1<=2.5)),overlap_reverse=float(np.mean(d2<=2.5)))
    return dict(seq=s,index=e['index'],i=i,j=j,measurement_id=e.get('measurement_id'),predictions=predictions,candidates=candidates,
        selector_W=wi,selector_J=ji,fgr=finfo,native_diagnostics=diagnostics(native,p,q,np_,nq,vp,vq),holdout=heldout)
def predictions(pilot=False):
    verify(); check_seal(INPUT,'input_seal.json')
    if pilot: assert read(BASE/'input_validation.json')['passed']
    else: assert read(BASE/'pilot_validation.json')['passed'] and read(BASE/'pilot_validation.json')['expansion_gate']
    dest=PILOT if pilot else BANK; dest.mkdir(); selected=pilot_rows() if pilot else rows(); outputs=[]; started=now()
    for e in selected:
        name=f"{e['seq']}_{e['index']:03d}.json"; cached=PILOT/name
        if not pilot and cached.exists():
            result=read(cached); (dest/name).write_bytes(cached.read_bytes())
        else: result=predict_one(e); save(dest/name,result)
        outputs.append(result); cap(); print('registered',e['seq'],e['index'],'RI',result['candidates']['RI']['status'],'W/J',result['selector_W'],result['selector_J'],flush=True)
    save(dest/'execution.json',dict(started_utc=started,utc=now(),edge_count=len(selected),reused_pilot_count=0 if pilot else 3))
    seal(dest,'pilot_seal.json' if pilot else 'bank_seal.json'); print('GT-free predictions sealed',len(outputs),flush=True)
def pose_error(t,truth):
    t=np.asarray(t); return dict(t=float(np.linalg.norm(t[:3,3]-truth[:3,3])),R=float(np.degrees(Rotation.from_matrix(t[:3,:3].T@truth[:3,:3]).magnitude())))
def gates(records):
    names=('N','RI','W','J'); means={a:{k:float(np.mean([r['errors'][a][k] for r in records])) for k in ('t','R')} for a in names}
    q90={a:{k:float(np.quantile([r['errors'][a][k] for r in records],.9)) for k in ('t','R')} for a in names}
    tests={}; sequence={s:{a:{k:float(np.mean([r['errors'][a][k] for r in records if r['seq']==s])) for k in ('t','R')} for a in names} for s in ACTIVE}
    for arm in ('RI','J'):
        tests[arm+'_mean_t_gain10pct']=means[arm]['t']<=.9*means['N']['t']; tests[arm+'_mean_R_nonworse']=means[arm]['R']<=means['N']['R']+1e-10
        support=sum(r['supported'][arm] for r in records); tests[arm+'_support52']=support>=52
        tests[arm+'_joint44']=sum(r['errors'][arm]['t']<=r['errors']['N']['t']+.01 and r['errors'][arm]['R']<=r['errors']['N']['R']+.01 for r in records)>=44
        for k in ('t','R'):
            tests[arm+'_q90_'+k]=q90[arm][k]<=1.05*q90['N'][k]+.01
            tests[arm+'_max_harm_'+k]=max(r['errors'][arm][k]-r['errors']['N'][k] for r in records)<=.2
        for s in ACTIVE:
            ss=[r for r in records if r['seq']==s]; tests[s+'_'+arm+'_support90']=sum(r['supported'][arm] for r in ss)>=.9*len(ss)
            for k in ('t','R'): tests[s+'_'+arm+'_'+k+'_guard']=sequence[s][arm][k]<=1.05*sequence[s]['N'][k]+.01
    increment=dict(mean_t_gain5pct=means['J']['t']<=.95*means['W']['t'],mean_R_nonworse=means['J']['R']<=means['W']['R']+1e-10)
    for s in ACTIVE:
        for k in ('t','R'): increment[s+'_'+k+'_guard']=sequence[s]['J'][k]<=1.05*sequence[s]['W'][k]+.01
    for k in ('t','R'): increment['q90_'+k]=q90['J'][k]<=1.05*q90['W'][k]+.01
    return dict(means=means,q90=q90,sequence_means=sequence,engineering_tests=tests,engineering_passed=all(tests.values()),
        increment_tests=increment,increment_passed=all(increment.values()),decision='MEASURED_REGISTRATION_ENGINEERING_HEADROOM' if all(tests.values()) else 'NO_SAFE_MEASURED_REGISTRATION_HEADROOM')
def evaluate():
    verify(); full=(BASE/'bank_seal.json').exists(); dest=BANK if full else PILOT; check_seal(dest,'bank_seal.json' if full else 'pilot_seal.json')
    if full: assert read(BASE/'bank_validation.json')['passed']
    else: assert read(BASE/'pilot_validation.json')['passed'] and not read(BASE/'pilot_validation.json')['expansion_gate']
    started=now(); selected=rows() if full else pilot_rows(); gt={}; result=[]
    from rap_slam.real_dataset import load_gt_poses
    for s in ACTIVE: gt[s]=np.asarray(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(DATA/'sequences'/s/'calib.txt'),apply_calib=True))
    for e in selected:
        pred=read(dest/f"{e['seq']}_{e['index']:03d}.json"); truth=np.linalg.inv(gt[e['seq']][e['i']])@gt[e['seq']][e['j']]
        errors={a:None if t is None else pose_error(t,truth) for a,t in pred['predictions'].items()}
        supported=dict(RI=pred['candidates']['RI']['status']=='completed' and pred['candidates']['RI']['diagnostics']['supported'],J=not pred['selector_J']['fallback'])
        # RI unsupported/no output remains in denominator with native fallback.
        if errors['RI'] is None: errors['RI']=dict(errors['N'])
        result.append(dict(seq=e['seq'],index=e['index'],i=e['i'],j=e['j'],truth=truth.tolist(),errors=errors,supported=supported,
            selectors=dict(W=pred['selector_W'],J=pred['selector_J'])))
    value=dict(utc=now(),gt_read_started_utc=started,full58=full,seal_sha256=sha(BASE/('bank_seal.json' if full else 'pilot_seal.json')),
        records=result,gate=gates(result) if full else None)
    save(BASE/'results.json',value); print('measurement evaluation',None if not full else value['gate'],flush=True)
def graph():
    verify(); assert read(BASE/'result_validation.json')['passed']; assert read(BASE/'results.json')['gate']['engineering_passed']
    dest=BASE/'graphs'; dest.mkdir(); started=now()
    for s in SEQS:
        o=old.load(old.src(s)/'odom_poses.txt'); kf=read(old.src(s)/'keyframes.json'); edges=old.loop_records(s)
        for arm in ('N','RI','W','J'):
            replaced=[]
            for k,e in enumerate(edges):
                pred=read(BANK/f'{s}_{k:03d}.json'); out=dict(e)
                if arm!='N':
                    supported=pred['candidates']['RI']['status']=='completed' and pred['candidates']['RI']['diagnostics']['supported'] if arm=='RI' else not pred['selector_'+arm]['fallback']
                    if supported: out['T_rel']=pred['predictions'][arm]
                replaced.append(out)
            full=old.native(o,kf,replaced); np.save(dest/f'{s}_{arm}.npy',full)
        cap()
    save(dest/'execution.json',dict(started_utc=started,utc=now())); seal(dest,'graph_seal.json')
    print('unchanged keyframe graph trajectories sealed',flush=True)
def graph_evaluate():
    verify(); check_seal(BASE/'graphs','graph_seal.json'); started=now()
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    output={}
    for s in SEQS:
        gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(DATA/'sequences'/s/'calib.txt'),apply_calib=True))
        tr=_read_calib_transform(str(DATA/'sequences'/s/'calib.txt')); ti=np.linalg.inv(tr); output[s]={}
        for arm in ('N','RI','W','J'):
            t=np.load(BASE/f'graphs/{s}_{arm}.npy'); lm=epm.evaluate_pair(list(gt),list(t),list(range(len(gt))))
            cm=epm.evaluate_pair(list(tr@gt@ti),list(tr@t@ti),list(range(len(gt))))
            output[s][arm]=dict(ate=lm['ape_aligned_rmse'],ter=cm['kitti_ter_pct'],rer=cm['kitti_rer_deg100m'],segments=cm['kitti_segments'])
        cap()
    means={a:{k:float(np.mean([output[s][a][k] for s in SEQS])) for k in ('ate','ter','rer')} for a in ('N','RI','W','J')}
    tests=dict(mean_ATE_gain5pct=means['J']['ate']<=.95*means['N']['ate'],mean_ter_nonworse=means['J']['ter']<=means['N']['ter']+1e-10,
        mean_rer_nonworse=means['J']['rer']<=means['N']['rer']+1e-10)
    for s in SEQS:
        tests[s+'_ATE_guard']=output[s]['J']['ate']<=1.05*output[s]['N']['ate']
        for k in ('ter','rer'): tests[s+'_'+k+'_guard']=output[s]['J'][k]-output[s]['N'][k]<=.01
    tests['10_no_op']=float(np.max(abs(np.load(BASE/'graphs/10_J.npy')-np.load(BASE/'graphs/10_N.npy'))))<=1e-5
    save(BASE/'graph_results.json',dict(utc=now(),gt_read_started_utc=started,graph_seal_sha256=sha(BASE/'graph_seal.json'),
        rows=output,means=means,tests=tests,passed=all(tests.values())))
    print('conditional graph metrics',means,tests,flush=True)
def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),neural_calls=0,CPU_binding=o3d.__DEVICE_API__)
def cap():
    u=usage(); assert u['peak_RSS_bytes']<=4*2**30 and u['artifact_bytes']<=512*2**20
    host=SUP/'host_latest.json'
    if host.exists(): assert read(host)['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic(); used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json')); assert used<1800
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('MGR0 combined payload cap'))); signal.alarm(max(1,int(1800-used)))
    ok=False; error=None
    try:
        cap()
        if stage.startswith('validate_'):
            import validate_measured_gicp as v
            dict(validate_preflight=v.preflight,validate_inputs=v.inputs,validate_pilot=lambda:v.predictions(True),
                validate_bank=lambda:v.predictions(False),validate_results=v.results,validate_graph=v.graph)[stage]()
        else: dict(freeze=freeze,freeze02=freeze,preflight=preflight,inputs=inputs,pilot=lambda:predictions(True),bank=lambda:predictions(False),evaluate=evaluate,graph=graph,graph_evaluate=graph_evaluate)[stage]()
        cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc(); save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error,**usage()))
    finally:
        signal.alarm(0); save(SUP/stage/'child_exit.json',dict(utc=now(),success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok: sys.exit(1)
if __name__=='__main__':
    sys.modules['measured_gicp_registration']=sys.modules[__name__]
    run(sys.argv[1])
