"""PFG0 orchestration: analytic inputs only, no evaluator or real scans."""
from pathlib import Path
import argparse,hashlib,importlib.metadata,json,resource,sys,time,traceback
from datetime import datetime,timezone
import numpy as np
import gtsam
MAIN=Path(__file__).resolve().parents[2];SLAM=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-preflight-01'
sys.path.insert(0,str(SLAM/'scripts'))
import geometric_loop_information as a
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stamp():return datetime.now(timezone.utc).isoformat()
def verify():
    for p,h in read(BASE/'freeze.json')['files'].items():assert sha(p)==h,p
def freeze():
    assert read(MAIN/'docs/maintenance/2026-10-07/measurement-source-audit-01/validation.json')['passed']
    files=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_geometric_information_preflight.py'),SLAM/'scripts/geometric_loop_information.py']
    save(BASE/'freeze.json',dict(utc=stamp(),files={str(p):sha(p) for p in files},packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','gtsam']}))
    (BASE/'INCOMPLETE').write_text('PFG0 independent validation pending\n')
    print('PFG0 frozen',len(files),'identities',flush=True)
def bank():
    verify();start=time.perf_counter();out=BASE/'bank';out.mkdir();files={};checks=[]
    grid=np.array([[x,y,0.] for x in np.linspace(-3,3,8) for y in np.linspace(-3,3,8)])
    normal=np.tile([0.,0.,1.],(len(grid),1));Sigma=np.diag([.03**2]*3+[.2**2]*3)
    for count in [1,2,3]:
        q=np.vstack([grid[:,np.roll(np.arange(3),i)] for i in range(count)])
        nj=np.vstack([normal[:,np.roll(np.arange(3),i)] for i in range(count)])
        for index in range(4):
            T=gtsam.Pose3.Expmap(np.array([.12,-.23,.31,1.4,-.7,.2])*index/3).matrix();R=T[:3,:3]
            p=q@R.T+T[:3,3];ni=nj@R.T
            J=a.surface_jacobians(T,p,q,ni,nj);r=a.normalized_information(J,Sigma)
            expected=[3,5,6][count-1];assert r['rank']==expected
            h=1e-6;fd=[]
            for k in range(6):
                d=np.eye(6)[k]*h
                def residual(sign):
                    W=T@gtsam.Pose3.Expmap(sign*d).matrix();forward=q@W[:3,:3].T+W[:3,3]-p
                    backward=(p-W[:3,3])@W[:3,:3]-q
                    return np.r_[np.sum(ni*forward,axis=1),np.sum(nj*backward,axis=1)]
                fd.append((residual(1)-residual(-1))/(2*h))
            fd=np.column_stack(fd);assert np.max(abs(fd-J))<2e-8
            inv=np.linalg.inv(T);Ji=a.surface_jacobians(inv,q,p,nj,ni);Ad=a.adjoint(T);Si=Ad@Sigma@Ad.T
            ri=a.normalized_information(Ji,Si);Ai=np.linalg.inv(Ad)
            assert np.max(abs(ri['Omega']-Ai.T@r['Omega']@Ai))<1e-8
            F=gtsam.Pose3.Expmap(np.array([.17,-.08,.21,2.,-.3,.6])).matrix()
            G=gtsam.Pose3.Expmap(np.array([-.13,.24,.04,-1.,.8,.5])).matrix()
            transformed=F@T@np.linalg.inv(G);p2=p@F[:3,:3].T+F[:3,3];q2=q@G[:3,:3].T+G[:3,3]
            B=a.adjoint(G);Bi=np.linalg.inv(B)
            shifted=a.normalized_information(a.surface_jacobians(transformed,p2,q2,ni@F[:3,:3].T,nj@G[:3,:3].T),B@Sigma@B.T)
            assert np.max(abs(shifted['Omega']-Bi.T@r['Omega']@Bi))<1e-8
            Tmm=T.copy();Tmm[:3,3]*=1000;C=np.diag([1.]*3+[1000.]*3);Ci=np.linalg.inv(C)
            mm=a.normalized_information(a.surface_jacobians(Tmm,p*1000,q*1000,ni,nj),C@Sigma@C.T)
            assert np.max(abs(mm['Omega']-Ci.T@r['Omega']@Ci))<1e-8
            for altered in [J[::-1],-J,np.vstack([J,J])]:assert np.max(abs(a.normalized_information(altered,Sigma)['Omega']-r['Omega']))<1e-8
            noise=gtsam.noiseModel.Gaussian.SqrtInformation(r['A']);e=np.array([.07,-.09,.13,.8,-.4,.6])
            whiten=noise.whiten(e);assert abs(whiten@whiten-e@r['Omega']@e)<1e-8
            values=gtsam.Values();values.insert(0,gtsam.Pose3());values.insert(1,gtsam.Pose3(T) .compose(gtsam.Pose3.Expmap(e)))
            factor=gtsam.BetweenFactorPose3(0,1,gtsam.Pose3(T),noise);cost=float(factor.error(values))
            assert abs(2*cost-e@r['Omega']@e)<1e-8
            f=out/f'{count}_{index}.npz';np.savez(f,T=T,p=p,q=q,ni=ni,nj=nj,Sigma=Sigma,J=J,fd=fd,whiten=whiten,e=e,cost=cost,**r)
            files[f.name]=sha(f);checks.append(dict(case=f.name,rank=expected))
    line=np.column_stack((np.arange(25.),np.zeros((25,2))));ln,lv,li=a.measured_normals(line);assert not lv.any()
    normals,valid,neighbors=a.measured_normals(grid);assert valid.all() and np.max(abs(normals[:,:2]))<1e-10
    shape=a.geometry_information(np.eye(4),grid,grid,normals,valid,normals,valid,Sigma)
    assert shape['supported'] and shape['rank']==3 and len(shape['ip'])==len(grid)
    tie_src=np.array([[0.,0.,0.],[3.,0.,0.]]);tie_dst=np.array([[-1.,0.,0.],[1.,0.,0.],[5.,0.,0.]])
    ties=a.nearest_indices(tie_src,tie_dst);assert np.array_equal(ties,[0,1])
    np.savez(out/'estimator.npz',grid=grid,normals=normals,valid=valid,neighbors=neighbors,line=line,line_valid=lv,tie_src=tie_src,tie_dst=tie_dst,ties=ties,Sigma=Sigma,shape_H=shape['H'],shape_Omega=shape['Omega'],shape_ip=shape['ip'],shape_iq=shape['iq'])
    files['estimator.npz']=sha(out/'estimator.npz')
    try:a.normalized_information(np.empty((0,6)),Sigma)
    except ValueError:pass
    else:raise AssertionError('Empty support did not reject')
    wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    assert wall<=120 and rss<=2**30 and sum(p.stat().st_size for p in out.iterdir())<10*2**20
    verify();save(BASE/'bank_seal.json',dict(utc=stamp(),files=files,wall_s=wall,peak_rss_bytes=rss,checks=checks,empty_reject=True,gt_read=False))
    print('PFG0 sealed',len(files),'files',flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','bank']);args=parser.parse_args()
    try:globals()[args.stage]()
    except Exception as e:
        p=BASE/f'FAILURE_{args.stage}.json'
        if not p.exists():save(p,dict(error=repr(e),traceback=traceback.format_exc()))
        raise
