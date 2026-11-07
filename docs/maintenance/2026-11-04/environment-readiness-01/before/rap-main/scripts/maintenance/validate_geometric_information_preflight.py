"""PFG0 independent explicit residual/exponential/outer-product validation."""
from pathlib import Path
import hashlib,json,resource,time,traceback
import numpy as np
from scipy.linalg import expm
import gtsam
MAIN=Path(__file__).resolve().parents[2];BASE=MAIN/'docs/maintenance/2026-10-07/geometric-information-preflight-01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def cross(x):return np.array([[0.,-x[2],x[1]],[x[2],0.,-x[0]],[-x[1],x[0],0.]])
def tangent_exp(e):
    M=np.zeros((4,4));M[:3,:3]=cross(e[:3]);M[:3,3]=e[3:];return expm(M)
def transport(T):
    A=np.zeros((6,6));A[:3,:3]=T[:3,:3];A[3:,3:]=T[:3,:3];A[3:,:3]=cross(T[:3,3])@T[:3,:3];return A
def residual(T,p,q,ni,nj):
    inv=np.linalg.inv(T)
    return np.r_[[float(n@(T[:3,:3]@x+T[:3,3]-y)) for n,x,y in zip(ni,q,p)],
        [float(n@(inv[:3,:3]@x+inv[:3,3]-y)) for n,x,y in zip(nj,p,q)]]
def run():
    start=time.perf_counter();freeze=read(BASE/'freeze.json');seal=read(BASE/'bank_seal.json');delta=0.;fdmax=0.;cases=0
    for p,h in freeze['files'].items():assert sha(p)==h,p
    for name,hashvalue in seal['files'].items():
        path=BASE/'bank'/name;assert sha(path)==hashvalue
        with np.load(path,allow_pickle=False) as z:d={k:z[k] for k in z.files}
        if name=='estimator.npz':
            grid=d['grid'];K=20
            for i,x in enumerate(grid):
                distances=np.array([sum((a-b)**2 for a,b in zip(x,y)) for y in grid])
                order=sorted(range(len(grid)),key=lambda j:(distances[j],j))[:K]
                assert np.array_equal(order,d['neighbors'][i]);points=grid[order];centered=points-points.mean(axis=0)
                _,s,Vt=np.linalg.svd(centered,full_matrices=False);normal=Vt[-1]
                assert np.max(abs(np.outer(normal,normal)-np.outer(d['normals'][i],d['normals'][i])))<1e-10
            assert d['valid'].all() and not d['line_valid'].any()
            ties=[min(range(len(d['tie_dst'])),key=lambda j:(sum((x-d['tie_dst'][j])**2),j)) for x in d['tie_src']]
            assert np.array_equal(ties,d['ties']);assert np.array_equal(d['shape_ip'],np.arange(len(grid))) and np.array_equal(d['shape_iq'],d['shape_ip'])
            columns=np.column_stack((grid[:,1],-grid[:,0],np.zeros((len(grid),3)),np.ones(len(grid))))
            H=2*columns.T@columns
            assert np.max(abs(H-d['shape_H']))<1e-10
            assert np.max(abs(6*H/np.trace(d['Sigma']@H)-d['shape_Omega']))<1e-10
            continue
        T,p,q,ni,nj,Sigma=[d[k] for k in ['T','p','q','ni','nj','Sigma']];R=T[:3,:3]
        rows=[]
        for x,n in zip(q,ni):
            row=np.r_[np.cross(x,R.T@n),R.T@n];rows.append(row)
        inv=np.linalg.inv(T)
        for x,n in zip(p,nj):
            y=inv[:3,:3]@x+inv[:3,3];rows.append(np.r_[np.cross(n,y),-n])
        J=np.array(rows);H=sum((np.outer(x,x) for x in rows),start=np.zeros((6,6)));Omega=6*H/np.trace(Sigma@H)
        delta=max(delta,float(np.max(abs(J-d['J']))),float(np.max(abs(Omega-d['Omega']))))
        assert np.max(abs(H-d['H']))<1e-9 and np.max(abs(J-d['J']))<1e-10
        assert np.max(abs(d['A'].T@d['A']-Omega))<1e-8 and abs(np.trace(Sigma@Omega)-6)<1e-9
        expected={1:3,2:5,3:6}[int(name.split('_')[0])]
        eig=np.linalg.eigvalsh(Omega);assert np.count_nonzero(eig>1e-10*eig[-1])==expected==int(d['rank'])
        fd=np.column_stack([(residual(T@tangent_exp(np.eye(6)[k]*1e-6),p,q,ni,nj)-residual(T@tangent_exp(-np.eye(6)[k]*1e-6),p,q,ni,nj))/(2e-6) for k in range(6)])
        fdmax=max(fdmax,float(np.max(abs(fd-J))));assert np.max(abs(fd-J))<2e-8 and np.max(abs(fd-d['fd']))<2e-8
        assert abs(float(d['e']@Omega@d['e'])-2*float(d['cost']))<1e-8
        assert abs(d['whiten']@d['whiten']-d['e']@Omega@d['e'])<1e-8
        if expected==3:
            wrong=T@tangent_exp(np.array([0.,0.,0.,2.,0.,0.]));r=residual(wrong,p,q,ni,nj)
            assert np.max(abs(r))<1e-10 and np.linalg.norm(wrong[:3,3]-T[:3,3])>1.999999
            assert np.max(abs(Omega@np.array([0.,0.,0.,2.,0.,0.])))<1e-8
        # World gauge on both node poses cancels in their relative transform.
        world=tangent_exp(np.array([.3,.4,-.2,10.,-3.,5.]));Xi=tangent_exp(np.array([.2,-.1,.3,4.,5.,1.]));Xj=Xi@T
        assert np.max(abs(np.linalg.inv(world@Xi)@(world@Xj)-T))<1e-12
        cases+=1
    assert cases==12 and seal['empty_reject'];assert delta<1e-8
    wall=time.perf_counter()-start;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;assert wall<=120 and rss<=2**30
    save(BASE/'validation.json',dict(passed=True,cases=cases,files=len(seal['files']),max_array_delta=delta,max_fd_delta=fdmax,wall_s=wall,peak_rss_bytes=rss,wrong_consistent_plane_blindspot=True,gt_read=False))
    save(BASE/'validation_seal.json',dict(validation_sha256=sha(BASE/'validation.json'),bank_seal_sha256=sha(BASE/'bank_seal.json')))
    (BASE/'INCOMPLETE').unlink();print('PFG0 independent passed',cases,'cases, FD delta',fdmax,flush=True)
try:run()
except Exception as e:
    path=BASE/'FAILURE_validation.json'
    if not path.exists():save(path,dict(error=repr(e),traceback=traceback.format_exc()))
    raise
