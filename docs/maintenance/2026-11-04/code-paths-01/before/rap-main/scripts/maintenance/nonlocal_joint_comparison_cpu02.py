"""NJE0 isolated frozen common-input comparison. No production writes/training."""
import ast,hashlib,importlib.metadata,itertools,json,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SLAM=ROOT.parent/'RAP-SLAM'
BASE=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01'
NJC=ROOT/'docs/maintenance/2026-10-15/nonlocal-joint-connectivity-01'
DATA=ROOT.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path[:0]=[str(ROOT),str(SLAM),str(ROOT/'dataset_process')]

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(name,obj):
    p=BASE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def npz(name,**obj):
    with (BASE/name).open('xb') as f:np.savez(f,**obj)
def seed(s,i,purpose):return int.from_bytes(hashlib.sha256(f'NJE0|{s}|{i}|{purpose}'.encode()).digest()[:4],'big')
def source(s):
    d='2026-09-26/e0-frontend-01' if s in ('00','05','06') else '2026-09-27/e0-heldout-01'
    return ROOT/'docs/maintenance'/d/f'full-{s}-A'
def groups():
    t=read(NJC/'topology.json');out=[]
    for s in ('05','00','07','09'):
        c=[c for row in t['sequences'] if row['sequence']==s for c in row['components'] if c['eligible']]
        assert len(c)==1;out.append(dict(sequence=s,**c[0]))
    assert sum(len(c['nodes']) for c in out)==29 and sum(len(c['edges']) for c in out)==32
    return out
def repositories():
    out={}
    for name,p in (('main',ROOT),('slam',SLAM)):
        def git(*a):return subprocess.check_output(['git','--no-optional-locks','-c',f'safe.directory={p}','-C',str(p),*a],text=True).strip()
        out[name]=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),tracked_status=git('status','--short','--untracked-files=no').splitlines())
    return out
def verify():
    f=read(BASE/'freeze.json')
    for name,r in f['files'].items():
        p=Path(name);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],name
    assert repositories()==f['repositories']
    assert f['packages']=={p:importlib.metadata.version(p) for p in f['packages']}
    return f
def freeze():
    prior=read(NJC/'freeze.json');files=dict(prior['files'])
    paths=[NJC/n for n in ('topology.json','validation.json','REPORT.md','CHECKS.json','DELIVERY_SEAL.json')]
    paths += [BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('run_nonlocal_joint_comparison.py'),
      Path(__file__).with_name('validate_nonlocal_joint_comparison.py'),Path(__file__).with_name('local_motion_common.py')]
    paths += [ROOT/'weights'/n for n in ('rap_model_12.ckpt','mini_spinnet_t.pth')]
    paths += [SLAM/'rap_slam'/n for n in ('rap_backend.py','rap_precision.py','real_dataset.py','trajectory_protocol.py')]
    for directory in ('rectified_point_flow','config','dataset_process/utils'):
        paths += [p for p in (ROOT/directory).rglob('*') if p.suffix in ('.py','.yaml','.yml')]
    paths += [ROOT/'dataset_process/extract_sample_features.py']
    sgc=read(ROOT/'docs/maintenance/2026-10-12/scan-level-graph-feasibility-01/freeze.json')
    for c in groups():
        s=c['sequence']
        for p in (source(s)/'odom_poses.txt',DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt'):
            assert sha(p)==sgc['files'][str(p)];paths.append(p)
    for p in sorted(set(paths)):
        files[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
        if p.suffix in ('.py','.yaml','.yml','.ps1'):
            rel=p.relative_to(ROOT.parent);q=BASE/'source_snapshot'/rel;q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as out:out.write(p.read_bytes())
    for name,r in files.items():assert sha(name)==r['sha256'] and Path(name).stat().st_size==r['bytes']
    repos=repositories();assert repos==prior['repositories']
    save('freeze.json',dict(files=files,repositories=repos,groups=groups(),packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','torch','open3d','gtsam','hydra-core')},
      cap_seconds=2400,cap_RSS_bytes=6*2**30,cap_GPU_bytes=8*2**30,cap_artifact_bytes=256*2**20))
    save('INCOMPLETE',dict(pending='common inputs, controls, all predictions, seal, references and independent validation'))
    print('NJE0 frozen',len(files),'identities',flush=True)

def inv(t):
    z=np.eye(4);z[:3,:3]=t[:3,:3].T;z[:3,3]=-z[:3,:3]@t[:3,3];return z
def proper(t,tol=1e-5):
    assert t.shape==(4,4) and np.isfinite(t).all()
    assert np.max(abs(t[3]-[0,0,0,1]))<=1e-12
    assert np.max(abs(t[:3,:3].T@t[:3,:3]-np.eye(3)))<=tol and abs(np.linalg.det(t[:3,:3])-1)<=tol
    return t
def svd_fit(x,y):
    a=x.mean(0);b=y.mean(0);u,_,vt=np.linalg.svd((x-a).T@(y-b))
    z=np.eye(4);z[:3,:3]=vt.T@np.diag([1,1,np.linalg.det(vt.T@u.T)])@u.T;z[:3,3]=b-z[:3,:3]@a
    return proper(z)
def horn_fit(x,y):
    a=x.mean(0);b=y.mean(0);h=(x-a).T@(y-b);tr=np.trace(h)
    d=np.array([h[1,2]-h[2,1],h[2,0]-h[0,2],h[0,1]-h[1,0]])
    k=np.empty((4,4));k[0,0]=tr;k[0,1:]=k[1:,0]=d;k[1:,1:]=h+h.T-tr*np.eye(3)
    _,v=np.linalg.eigh(k);w,xq,yq,zq=v[:,-1]
    r=np.array([[1-2*(yq*yq+zq*zq),2*(xq*yq-w*zq),2*(xq*zq+w*yq)],
      [2*(xq*yq+w*zq),1-2*(xq*xq+zq*zq),2*(yq*zq-w*xq)],
      [2*(xq*zq-w*yq),2*(yq*zq+w*xq),1-2*(xq*xq+yq*yq)]])
    t=np.eye(4);t[:3,:3]=r;t[:3,3]=b-r@a;return proper(t)
def load_poses(p):
    a=np.loadtxt(p);out=np.repeat(np.eye(4)[None],len(a),axis=0);out[:,:3]=a.reshape(-1,3,4)
    for t in out:proper(t,1e-4)
    return out
def synchronize(nodes,edges):
    import gtsam
    # Deterministic maximum-support forest initialization; no target values.
    parent={i:i for i in nodes};initial={};adj={i:[] for i in nodes};tree=[]
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    for e in sorted(edges,key=lambda e:(-e['support'],e['i'],e['j'])):
        a,b=find(e['i']),find(e['j'])
        if a!=b:
            parent[b]=a;tree.append(e)
            adj[e['i']].append((e['j'],np.asarray(e['T'])));adj[e['j']].append((e['i'],inv(np.asarray(e['T']))))
    roots=[];component={}
    for root in nodes:
        if root in initial:continue
        roots.append(root);initial[root]=np.eye(4);component[root]=root;queue=[root]
        for i in queue:
            for j,t in adj[i]:
                if j not in initial:initial[j]=initial[i]@t;component[j]=root;queue.append(j)
    graph=gtsam.NonlinearFactorGraph();values=gtsam.Values()
    for i in nodes:values.insert(i,gtsam.Pose3(initial[i]))
    for i in roots:graph.add(gtsam.PriorFactorPose3(i,gtsam.Pose3(np.eye(4)),gtsam.noiseModel.Diagonal.Sigmas(np.full(6,1e-6))))
    noise=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1.345),gtsam.noiseModel.Diagonal.Sigmas(np.array([.1]*3+[.5]*3)))
    for e in edges:graph.add(gtsam.BetweenFactorPose3(e['i'],e['j'],gtsam.Pose3(np.asarray(e['T'])),noise))
    params=gtsam.LevenbergMarquardtParams();params.setMaxIterations(100)
    opt=gtsam.LevenbergMarquardtOptimizer(graph,values,params);result=opt.optimize()
    out={i:proper(result.atPose3(i).matrix()) for i in nodes}
    assert graph.error(result)<=graph.error(values)+1e-6
    return out,component,dict(edges=len(edges),components=len(roots),iterations=opt.iterations(),initial_cost=graph.error(values),final_cost=graph.error(result))

def preflight():
    verify();import gtsam
    rng=np.random.default_rng(20261015);x=rng.normal(size=(1000,3));t=gtsam.Pose3.Expmap(np.array([.17,-.12,.07,2.,-.5,.3])).matrix();y=x@t[:3,:3].T+t[:3,3]
    a=svd_fit(x,y);b=horn_fit(x,y);assert np.max(abs(a-t))<1e-12 and np.max(abs(b-t))<1e-12
    poses=[np.eye(4),t,t@gtsam.Pose3.Expmap(np.array([.02,.03,-.01,.5,.2,-.4])).matrix()]
    ee=[dict(i=i,j=j,T=(inv(poses[i])@poses[j]).tolist(),support=1.) for i,j in itertools.combinations(range(3),2)]
    fitted,_,diag=synchronize(list(range(3)),ee);err=max(np.max(abs(fitted[i]-poses[i])) for i in range(3));assert err<1e-8
    tree=ast.parse((SLAM/'rap_slam/rap_backend.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RAPBackend')
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_normalize_parts');fn.decorator_list=[]
    ns={'np':np};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'bound_backend_normalization','exec'),ns)
    inp=read(NJC/'topology.json')['caches'];arrays={};manifest=[];max_norm_error=0.
    for c in groups():
        s=c['sequence'];q=[];centers=[]
        for i in c['nodes']:
            key=f'{s}/{i:06d}';p=np.load(inp[key]['path'],allow_pickle=False)
            assert p.shape==(4000,3) and p.dtype==np.float32 and np.isfinite(p).all() and len(np.unique(p,axis=0))==len(p)
            rows=np.sort(np.random.default_rng(seed(s,i,'rows')).choice(len(p),1000,replace=False));selected=p[rows]
            noise=np.random.default_rng(seed(s,i,'noise')).standard_normal((1000,3)).astype(np.float32)
            tag=f'{s}_{i}';arrays[tag+'_full']=p;arrays[tag+'_rows']=rows;arrays[tag+'_q']=selected;arrays[tag+'_noise']=noise
            q.append(selected);centers.append(selected.astype(float).mean(0))
            manifest.append(dict(sequence=s,frame=i,cache=inp[key]['path'],cache_sha256=sha(inp[key]['path']),selected_rows=rows.tolist(),noise_seed=seed(s,i,'noise')))
        cond,scale,offset,counts,anchor=ns['_normalize_parts'](q)
        assert anchor==0 and np.all(counts==1000)
        for k,i in enumerate(c['nodes']):
            manual=((q[k].astype(float)-centers[k])/scale).astype(np.float32)
            e=float(np.max(abs(cond[k*1000:(k+1)*1000]-manual)));max_norm_error=max(max_norm_error,e);assert e<1e-6
            assert np.max(abs(offset[k]-centers[k]))<1e-10
            arrays[f'{s}_{i}_cond']=manual;arrays[f'{s}_{i}_center']=centers[k]
        arrays[f'{s}_scale']=np.array([scale]);assert scale>0 and np.isfinite(scale)
    npz('inputs.npz',**arrays)
    save('inputs.json',dict(views=manifest,groups=groups(),inputs_sha256=sha(BASE/'inputs.npz'),no_reference_values_read=True))
    save('preflight.json',dict(horn_error=float(np.max(abs(b-t))),svd_error=float(np.max(abs(a-t))),pose_graph_error=float(err),backend_normalization_error=max_norm_error,synthetic_graph=diag,passed=True))
    print('NJE0 common inputs/preflight pass:29 views,4 groups',flush=True)

def geometry():
    import os;os.environ['CUDA_VISIBLE_DEVICES']=''
    verify();assert read(BASE/'preflight.json')['passed'];import open3d as o3d
    from scipy.spatial import cKDTree
    assert o3d.__version__=='0.19.0' and o3d.__DEVICE_API__=='cpu'
    data=np.load(BASE/'inputs.npz',allow_pickle=False);results=[];total=time.monotonic();counts={'FGR':0,'GICP':0,'graphs':0}
    def cloud(p,n=None):
        z=o3d.geometry.PointCloud();z.points=o3d.utility.Vector3dVector(p)
        if n is not None:
            z.normals=o3d.utility.Vector3dVector(n);z.covariances=o3d.utility.Matrix3dVector(np.eye(3)[None]-.999*np.einsum('ni,nj->nij',n,n))
        return z
    def feature(f):z=o3d.pipelines.registration.Feature();z.data=f;return z
    def diag(p,q,t):
        mapped=q@t[:3,:3].T+t[:3,3];a=cKDTree(p).query(mapped)[0];b=cKDTree(mapped).query(p)[0]
        return dict(score=float((np.mean(np.minimum(a,2.5)**2)+np.mean(np.minimum(b,2.5)**2))/2),support=float(min(np.mean(a<=2.5),np.mean(b<=2.5))))
    for c in groups():
        start=time.monotonic();s=c['sequence'];odom=load_poses(source(s)/'odom_poses.txt');views={};outputs={};work={}
        for i in c['nodes']:
            tag=f'{s}_{i}';p=data[tag+'_full'].astype(float);pc=cloud(p);pc.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=20));pc.orient_normals_towards_camera_location(np.zeros(3))
            n=np.asarray(pc.normals).copy();assert np.isfinite(n).all()
            f=np.asarray(o3d.pipelines.registration.compute_fpfh_feature(pc,o3d.geometry.KDTreeSearchParamHybrid(radius=2.,max_nn=100)).data).copy();assert np.isfinite(f).all()
            rows=data[tag+'_rows'];views[i]=dict(G=(p[rows],n[rows],f[:,rows]),W=(p,n,f))
        for method in ('G','W'):
            all_pairs=[];lookup={};method_start=time.monotonic()
            for i,j in itertools.combinations(c['nodes'],2):
                p,na,fa=views[i][method];q,nb,fb=views[j][method];a,b=cloud(p,na),cloud(q,nb)
                o3d.utility.random.seed(20261015)
                option=o3d.pipelines.registration.FastGlobalRegistrationOption(division_factor=1.4,use_absolute_scale=True,decrease_mu=True,maximum_correspondence_distance=2.5,iteration_number=64,tuple_scale=.95,maximum_tuple_count=1000,tuple_test=True)
                init=proper(np.asarray(o3d.pipelines.registration.registration_fgr_based_on_feature_matching(b,a,feature(fb),feature(fa),option).transformation).copy());counts['FGR']+=1
                starts=[np.eye(4),init]
                if method=='W':starts.append(inv(odom[i])@odom[j])
                candidates=[]
                for k,initial in enumerate(starts):
                    estimator=o3d.pipelines.registration.TransformationEstimationForGeneralizedICP(.001,o3d.pipelines.registration.L2Loss())
                    criterion=o3d.pipelines.registration.ICPConvergenceCriteria(relative_fitness=1e-6,relative_rmse=1e-6,max_iteration=80)
                    r=o3d.pipelines.registration.registration_generalized_icp(b,a,2.5,initial,estimator,criterion);counts['GICP']+=1
                    t=proper(np.asarray(r.transformation).copy());d=diag(p,q,t);candidates.append(dict(start=k,T=t.tolist(),**d))
                chosen=min(candidates,key=lambda e:(e['score'],e['start']))
                row=dict(i=i,j=j,**chosen,candidates=candidates);all_pairs.append(row);lookup[(i,j)]=row
            admitted=[e for e in all_pairs if e['support']>=.30];poses,component,sd=synchronize(c['nodes'],admitted);counts['graphs']+=1
            direct=[];synced=[];fallback=0
            for e in c['edges']:
                i,j=e['i'],e['j'];t=np.asarray(lookup[(i,j)]['T']);direct.append(dict(**e,T=t.tolist()))
                linked=component[i]==component[j];z=inv(poses[i])@poses[j] if linked else t;fallback+=not linked
                synced.append(dict(**e,T=proper(z).tolist(),direct_fallback=not linked))
            outputs[method+'d']=direct;outputs[method+'s']=synced
            work[method]=dict(all_pairs=all_pairs,synchronization=sd,fallbacks=fallback,wall_seconds=time.monotonic()-method_start)
        row=dict(sequence=s,outputs=outputs,work=work,wall_seconds=time.monotonic()-start);save(f'geometry_{s}.json',row);results.append(s)
        print('NJE0 geometry complete',s,flush=True)
    assert counts==dict(FGR=210,GICP=525,graphs=8)
    save('geometry.json',dict(completed=results,counts=counts,wall_seconds=time.monotonic()-total,no_reference_values_read=True))

def neural():
    verify();assert read(BASE/'preflight.json')['passed'];import torch
    free,total=torch.cuda.mem_get_info();save('GPU_PRESTART.json',dict(free_bytes=free,total_bytes=total,required_free_bytes=9*2**30))
    if free<9*2**30:
        save('GPU_WAITING.json',dict(model_loaded=False,reference_read=False,reason='shared GPU free memory below prospective9GiB gate'));print('NJE0 waiting shared GPU, no model loaded',flush=True);return
    import local_motion_common as reviewed
    from rap_slam.rap_precision import ieee_matmul
    from rectified_point_flow.procrustes import fit_transformations
    start=time.monotonic();b,loading=reviewed.make_backend();assert b.model.inference_sampling_steps==5 and not b.model.training
    for model in (b.model,b.feature_extractor.model):
        for p in model.parameters():p.requires_grad_(False)
    save('loading.json',loading);data=np.load(BASE/'inputs.npz',allow_pickle=False);features={};feature_work=[]
    for c in groups():
        s=c['sequence']
        for i in c['nodes']:
            tick=time.monotonic();tag=f'{s}_{i}';torch.manual_seed(seed(s,i,'descriptor'));torch.cuda.manual_seed_all(seed(s,i,'descriptor'))
            with torch.inference_mode(),ieee_matmul():
                out=b.feature_extractor.model(pts=torch.from_numpy(data[tag+'_full'][None]).cuda(),kpts=torch.from_numpy(data[tag+'_q'][None]).cuda(),des_r=5.,is_aligned_to_global_z=True)['desc']
            torch.cuda.synchronize();a=out.squeeze(0).float().cpu().numpy();assert a.shape==(1000,32) and np.isfinite(a).all() and np.all(np.linalg.norm(a,axis=1)>0)
            features[tag]=a;feature_work.append(dict(sequence=s,frame=i,wall_seconds=time.monotonic()-tick));del out
    npz('descriptors.npz',**features);save('descriptors.json',dict(work=feature_work,calls=29,sha256=sha(BASE/'descriptors.npz')))
    def generate(c,ids,name):
        tick=time.monotonic();s=c['sequence'];tags=[f'{s}_{i}' for i in ids];cond=np.concatenate([data[t+'_cond'] for t in tags]);noise=np.concatenate([data[t+'_noise'] for t in tags]);n=len(cond)
        batch=dict(pointclouds=torch.from_numpy(cond).cuda(),pointclouds_gt=torch.from_numpy(cond).cuda(),features=torch.from_numpy(np.concatenate([features[t] for t in tags])).cuda(),scales=torch.tensor(data[s+'_scale'],dtype=torch.float32,device='cuda'),anchor_indices=torch.arange(n,device='cuda')<1000,points_per_part=torch.full((1,len(ids)),1000,dtype=torch.int64,device='cuda'),cu_seqlens=torch.tensor([0,n],dtype=torch.int64,device='cuda'))
        with torch.inference_mode(),ieee_matmul(),torch.autocast('cuda',dtype=torch.float16):
            out=b.model.sample_rectified_flow(batch,None,x_1=torch.from_numpy(noise).cuda(),return_tarjectory=True)
            pred=out['end_point_trajectory'][-1];r,t=fit_transformations(batch['pointclouds'],pred,batch['points_per_part'],batch['cu_seqlens'].to(torch.int32))
        torch.cuda.synchronize();end=pred.float().cpu().numpy();rr=r[0].float().cpu().numpy();tt=t[0].float().cpu().numpy();parts=[];saved={};maximum=0.
        for k,tag in enumerate(tags):
            x=cond[k*1000:(k+1)*1000].astype(float);y=end[k*1000:(k+1)*1000].astype(float);a=svd_fit(x,y);h=horn_fit(x,y)
            assert np.max(abs(a-h))<1e-4
            native=np.eye(4);native[:3,:3]=rr[k];native[:3,3]=tt[k];proper(native)
            delta=float(np.max(abs(native-a)));maximum=max(maximum,delta);assert delta<1e-3
            meter=native.copy();meter[:3,3]=float(data[s+'_scale'][0])*native[:3,3]-native[:3,:3]@data[tag+'_center'];parts.append(proper(meter))
            saved[f'part{k}_cond']=x;saved[f'part{k}_end']=y;saved[f'part{k}_native']=native;saved[f'part{k}_horn']=h;saved[f'part{k}_meter']=meter
        npz(f'{s}_{name}_fit.npz',**saved)
        assert torch.cuda.max_memory_allocated()<=8*2**30 and torch.cuda.max_memory_reserved()<=8*2**30
        return parts,dict(ids=ids,wall_seconds=time.monotonic()-tick,flow_calls=5,n_points=n,native_fit_max_error=maximum,fit_file=f'{s}_{name}_fit.npz')
    for c in groups():
        s=c['sequence'];direct=[];work=[]
        for k,e in enumerate(c['edges']):
            ids=[e['i'],e['j']];parts,w=generate(c,ids,f'P{k:02d}');direct.append(dict(**e,T=proper(inv(parts[0])@parts[1]).tolist()));work.append(w)
        joint,jw=generate(c,c['nodes'],'J');lookup=dict(zip(c['nodes'],joint));jrows=[dict(**e,T=proper(inv(lookup[e['i']])@lookup[e['j']]).tolist()) for e in c['edges']]
        sync,component,sd=synchronize(c['nodes'],[dict(**e,support=1.) for e in direct]);ps=[dict(**e,T=proper(inv(sync[e['i']])@sync[e['j']]).tolist()) for e in c['edges']]
        save(f'neural_{s}.json',dict(sequence=s,outputs=dict(P=direct,Ps=ps,J=jrows),pair_work=work,joint_work=jw,pair_sync=sd))
        print('NJE0 native forward complete',s,flush=True)
    save('neural.json',dict(groups=4,pair_generations=32,joint_generations=4,flow_calls=180,descriptor_calls=29,wall_seconds=time.monotonic()-start,backwards=0,updates=0,reference_values_read=False))

def prediction_seal():
    verify();assert (BASE/'neural.json').exists() and (BASE/'geometry.json').exists()
    names=['inputs.npz','inputs.json','descriptors.npz','descriptors.json','geometry.json','neural.json','preflight.json','loading.json','GPU_PRESTART.json']
    names += [f'{kind}_{c["sequence"]}.json' for c in groups() for kind in ('geometry','neural')]
    names += [p.name for p in BASE.glob('*_fit.npz')]
    assert len(list(BASE.glob('*_fit.npz')))==36
    for c in groups():
        combined={**read(BASE/f'geometry_{c["sequence"]}.json')['outputs'],**read(BASE/f'neural_{c["sequence"]}.json')['outputs']}
        assert set(combined)=={'Gd','Gs','Wd','Ws','P','Ps','J'}
        for method,rows in combined.items():
            assert [(r['i'],r['j'],r['measurement_id']) for r in rows]==[(r['i'],r['j'],r['measurement_id']) for r in c['edges']]
            for r in rows:proper(np.asarray(r['T']))
    save('PREDICTION_SEAL.json',dict(files={name:dict(bytes=(BASE/name).stat().st_size,sha256=sha(BASE/name)) for name in names},groups=4,edges=32,methods=7,reference_values_read=False))
    print('NJE0 all predictions sealed before references',flush=True)

def metrics():
    verify();seal=read(BASE/'PREDICTION_SEAL.json')
    for name,r in seal['files'].items():assert sha(BASE/name)==r['sha256'] and (BASE/name).stat().st_size==r['bytes']
    allrows=[];group_stats=[]
    for c in groups():
        s=c['sequence'];camera=load_poses(DATA/'poses'/f'{s}.txt');calib=DATA/'sequences'/s/'calib.txt';lines=calib.read_text().splitlines();tr=np.eye(4)
        line=next(l for l in lines if l.startswith('Tr:'));tr[:3]=np.asarray([float(v) for v in line.split(':',1)[1].split()]).reshape(3,4);proper(tr,1e-4)
        truth=np.linalg.inv(tr)@camera@tr;odom=load_poses(source(s)/'odom_poses.txt')
        outputs={**read(BASE/f'geometry_{s}.json')['outputs'],**read(BASE/f'neural_{s}.json')['outputs']}
        outputs['O']=[dict(**e,T=(inv(odom[e['i']])@odom[e['j']]).tolist()) for e in c['edges']]
        stats={}
        for name,rows in outputs.items():
            metrics=[]
            for e in rows:
                gt=np.linalg.inv(truth[e['i']])@truth[e['j']];p=np.asarray(e['T']);r=gt[:3,:3].T@p[:3,:3]
                sine=np.linalg.norm([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])/2;cosine=(np.trace(r)-1)/2
                m=dict(sequence=s,method=name,i=e['i'],j=e['j'],RTE=float(np.linalg.norm(p[:3,3]-gt[:3,3])),RRE_deg=float(np.degrees(np.arctan2(sine,cosine))));metrics.append(m);allrows.append(m)
            stats[name]={key:float(np.mean([m[key] for m in metrics])) for key in ('RTE','RRE_deg')}
        group_stats.append(dict(sequence=s,edges=len(c['edges']),means=stats))
    means={method:{key:float(np.mean([r[key] for r in allrows if r['method']==method])) for key in ('RTE','RRE_deg')} for method in ('J','P','Ps','Gd','Gs','Wd','Ws','O')}
    controls=('P','Ps','Gd','Gs','Wd','Ws');gates=dict(aggregate_RTE=all(means['J']['RTE']<=.95*means[m]['RTE'] for m in controls),aggregate_RRE=all(means['J']['RRE_deg']<=means[m]['RRE_deg']+.05 for m in controls),every_group_RTE=all(g['means']['J']['RTE']<=min(g['means'][m]['RTE'] for m in controls)+.005 for g in group_stats))
    save('metrics.json',dict(prediction_seal_sha256=sha(BASE/'PREDICTION_SEAL.json'),rows=allrows,groups=group_stats,means=means,gates=gates,engineering_admitted=all(gates.values()),sequence09_interpretation_unknown=True,exposed_population=True,no_system_or_novelty_claim=True))
    print(json.dumps(dict(means=means,gates=gates)),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    {'freeze':freeze,'preflight':preflight,'geometry':geometry,'neural':neural,'seal':prediction_seal,'metrics':metrics}[action]()
