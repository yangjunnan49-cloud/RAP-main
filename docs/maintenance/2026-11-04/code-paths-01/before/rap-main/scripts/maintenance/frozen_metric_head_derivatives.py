"""FHR0 CPU metric-SE3 head derivatives and active-column interface; zero fitting."""
import importlib.metadata,math,os,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_prefix_storage_codec as s
ROOT=s.ROOT;PRIOR=ROOT/'docs/maintenance/2026-10-13/frozen-context-extraction-01'
BASE=ROOT/'docs/maintenance/2026-10-13/frozen-metric-head-derivatives-01';SUP=BASE/'supervision';START=None
read,sha,save=s.read,s.sha,s.save
def freeze():
    f=read(PRIOR/'freeze.json');files=dict(f['files']);v=read(PRIOR/'validation.json');assert v['passed'];delivery=read(PRIOR/'DELIVERY_SEAL.json');assert delivery['entries']==67
    for x in delivery['files']:
        q=(PRIOR/x['path'].replace(chr(92),'/')).resolve();assert PRIOR.resolve() in q.parents and sha(q)==x['sha256'];files[str(q)]=x['sha256']
    sources=[PRIOR/'DELIVERY_SEAL.json',Path(__file__),Path(__file__).with_name('validate_frozen_metric_head.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md']
    snap=BASE/'source_snapshot';snap.mkdir()
    for q in sources:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert s.repositories()==f['repositories']
    save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],packages=f['packages'],head_shape=[6,1025],nominal_head_parameters=6150,feature_arms=['D_pointwise','I_separated','J_joint'],noise_names=['fit_00','eval_00'],metric_scale=[.05]*3+[math.radians(.2)]*3,dense_direction_seed=2026101315,cotangent_seed=2026101316,FD_steps=[1e-4,1e-5],cap_seconds=600,cap_RSS_bytes=2*2**30,cap_GPU_bytes=0,cap_artifact_bytes=64*2**20,no_neural_backbone_or_fitting=True))
    (BASE/'INCOMPLETE').write_text('FHR0 zero-update CPU residual-head derivatives/active-column prerequisites pending.\n');print('FHR0 frozen',len(files),'identities',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'] and f['packages']=={x:importlib.metadata.version(x) for x in ('torch','numpy','scipy')}
    assert (s.OLD/'INCOMPLETE').exists() and not (s.OLD/'prediction_seal.json').exists()
def load(q):
    import numpy as np
    with np.load(q,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def bases(observations,x,velocity):
    import numpy as np
    endpoint=x.astype(float)-velocity.astype(float);ps=[];singular=[]
    for k in range(3):
        a=observations['cond'][k*1000:(k+1)*1000].astype(float);b=endpoint[k*1000:(k+1)*1000];ma=a.mean(0);mb=b.mean(0)
        u,sv,vh=np.linalg.svd((a-ma).T@(b-mb));R=vh.T@np.diag([1.,1.,np.linalg.det(vh.T@u.T)])@u.T;t=mb-R@ma
        T=np.eye(4);T[:3,:3]=R;T[:3,3]=float(observations['scale'])*t-R@observations['centers'][k].astype(float);ps.append(T);singular.append(sv)
    relative=np.array([np.linalg.solve(ps[0],ps[k]) for k in (1,2)]);relative[:,3,:]=[0.,0.,0.,1.]
    return relative,np.array(ps),np.array(singular)
def probe():
    verify();os.environ['CUDA_VISIBLE_DEVICES']=''
    import numpy as np,torch
    assert not torch.cuda.is_initialized() and torch.get_num_threads()==1
    f=read(BASE/'freeze.json');d=torch.tensor(f['metric_scale'],dtype=torch.float64);folder=BASE/'traces';folder.mkdir();pool=load(PRIOR/'pooled_features.npz');obs=load(PRIOR/'features/observations.npz')
    rng=np.random.default_rng(f['dense_direction_seed']);vectors=[]
    for _ in range(3):
        a=rng.choice([-1.,1.],size=(6,1025));a/=np.linalg.norm(a);vectors.append(a)
    for j in range(6):
        a=np.zeros((6,1025));a[j,-1]=1.;vectors.append(a)
    np.savez(folder/'directions.npz',**{f'direction_{i}':v for i,v in enumerate(vectors)})
    rng=np.random.default_rng(f['cotangent_seed']);cots={noise:rng.normal(size=(2,4,4)) for noise in f['noise_names']};np.savez(folder/'cotangents.npz',**cots)
    def pose(theta,h,base):
        v=(h@theta.T)*d;zero=torch.zeros_like(v[:,0]);rx,ry,rz=v[:,3],v[:,4],v[:,5]
        row0=torch.stack([zero,-rz,ry,v[:,0]],1);row1=torch.stack([rz,zero,-rx,v[:,1]],1);row2=torch.stack([-ry,rx,zero,v[:,2]],1);row3=torch.zeros_like(row0)
        return base@torch.matrix_exp(torch.stack([row0,row1,row2,row3],1))
    records=[];FD=[];forwards=backwards=0
    for noise in f['noise_names']:
        inputs=load(PRIOR/f'features/{noise}_J_joint/inputs.npz');hook=load(PRIOR/f'features/{noise}_J_joint/hook.npz');T,ps,sv=bases(obs,inputs['x'],hook['velocity']);np.savez(folder/f'{noise}_base.npz',relative=T,absolute=ps,cross_covariance_singular_values=sv)
        for arm in f['feature_arms']:
            means=pool[f'{noise}_{arm}'];h=np.array([np.concatenate([means[0],means[k],[1.]]) for k in (1,2)]);assert h.shape==(2,1025) and np.isfinite(h).all();dest=folder/f'{noise}_{arm}';dest.mkdir();np.save(dest/'inputs.npy',h)
            ht=torch.tensor(h,dtype=torch.float64);bt=torch.tensor(T,dtype=torch.float64);ct=torch.tensor(cots[noise],dtype=torch.float64)
            for rep in (1,2):
                theta=torch.zeros((6,1025),dtype=torch.float64,requires_grad=True);out=pose(theta,ht,bt);forwards+=1;loss=(out*ct).sum();loss.backward();backwards+=1
                assert out.detach().numpy().tobytes()==T.tobytes() and not torch.count_nonzero(theta).item()
                np.savez(dest/f'probe{rep}.npz',pose=out.detach().numpy(),gradient=theta.grad.detach().numpy(),parameters=theta.detach().numpy());cap()
            for j,vector in enumerate(vectors):
                for step in f['FD_steps']:
                    for sign in (-1,1):
                        theta=torch.tensor(sign*step*vector,dtype=torch.float64);out=pose(theta,ht,bt);forwards+=1;name=f'direction_{j}_{step:g}_{sign:+d}';np.save(dest/(name+'.npy'),out.numpy());FD.append(dict(noise=noise,arm=arm,direction=j,step=step,sign=sign,path=str((dest/(name+'.npy')).relative_to(BASE))))
            # Shared-head row permutation and common external left-frame convention.
            theta=torch.tensor(1e-4*vectors[0],dtype=torch.float64);out=pose(theta,ht,bt);swapped=pose(theta,ht.flip(0),bt.flip(0));forwards+=2;assert torch.equal(swapped,out.flip(0))
            G=torch.eye(4,dtype=torch.float64);G[:3,:3]=torch.tensor([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]],dtype=torch.float64);G[:3,3]=torch.tensor([1.,-2.,3.],dtype=torch.float64)
            framed=pose(theta,ht,G@bt);forwards+=1;np.savez(dest/'convention.npz',pose=out.numpy(),swapped=swapped.numpy(),G=G.numpy(),framed=framed.numpy());assert np.max(abs(framed.numpy()-(G@out).numpy()))<=1e-12
            records.append(dict(noise=noise,arm=arm,nominal_head_parameters=6150,base_common_across_arms=True,parameters_initial_zero=True,head_fits=0));print('FHR0 zero-update head derivative probes',noise,arm,flush=True)
    assert forwards==246 and backwards==12 and len(FD)==216 and not torch.cuda.is_initialized()
    save(folder/'execution.json',dict(records=records,FD_trials=FD,CPU_head_forwards=forwards,CPU_head_backwards=backwards,native_model_loads=0,native_backwards=0,native_forwards=0,optimizer_calls=0,retained_updates=0,GT_pose_errors=0,teacher_or_truth_loaded=False,head_parameters_remain_zero=True))
    save(BASE/'trace_seal.json',dict(freeze_sha256=sha(BASE/'freeze.json'),files={str(q.relative_to(folder)):sha(q) for q in sorted(folder.rglob('*')) if q.is_file()}));verify()
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=64*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<600
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('FHR0 aggregate child time cap')));signal.alarm(max(1,int(600-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='probe':probe()
        elif stage=='validate':
            import validate_frozen_metric_head as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['frozen_metric_head_derivatives']=sys.modules[__name__];run(sys.argv[1])
