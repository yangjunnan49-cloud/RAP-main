"""MGR0 independent physical support, full objective derivatives and metric/gate audit."""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
import measured_gicp_registration as r

def skew(w):
    x,y,z=w; return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
def exp(x):
    omega=x[:3]; theta=np.linalg.norm(omega); k=skew(omega)
    if theta<1e-5: a=.5-theta**2/24; b=1/6-theta**2/120
    else: a=(1-np.cos(theta))/theta**2; b=(theta-np.sin(theta))/theta**3
    t=np.eye(4); t[:3,:3]=Rotation.from_rotvec(omega).as_matrix(); t[:3,3]=(np.eye(3)+a*k+b*k@k)@x[3:]; return t
def close(a,b,tol=1e-8):
    a=np.asarray(a); b=np.asarray(b); assert np.isfinite(a).all() and np.isfinite(b).all()
    assert a.shape==b.shape and np.max(abs(a-b))<=tol,(a.shape,b.shape,float(np.max(abs(a-b))),tol)
def covariance(n): return np.asarray([np.eye(3)-.999*np.outer(v,v) for v in n])
def objective(t,p,q,cp,cq):
    points=(t[:3,:3]@q.T).T+t[:3,3]; result=0.
    for pp,qq,c1,c2 in zip(p,points,cp,cq):
        d=qq-pp; m=c1+t[:3,:3]@c2@t[:3,:3].T
        ch=np.linalg.cholesky(m); white=np.linalg.solve(ch,d); result+=float(white@white)
    return result
def independent_support(t,p,q,np_,nq,vp,vq):
    qq=(t[:3,:3]@q.T).T+t[:3,3]; forward,nearest_p=cKDTree(p).query(qq); reverse,nearest_q=cKDTree(qq).query(p)
    ix=np.asarray([k for k in range(len(q)) if forward[k]<=2.5 and vp[nearest_p[k]] and vq[k] and nearest_q[nearest_p[k]]==k],dtype=int)
    iy=nearest_p[ix]; h=np.zeros((6,6))
    for qi,pi in zip(ix,iy):
        j1=np_[pi]@t[:3,:3]@np.column_stack([-skew(q[qi]),np.eye(3)])
        back=np.linalg.solve(t[:3,:3],p[pi]-t[:3,3]); j2=nq[qi]@np.column_stack([skew(back),-np.eye(3)])
        h+=np.outer(j1,j1)+np.outer(j2,j2)
    eigen=np.linalg.eigvalsh((h+h.T)/2); rank=int(np.count_nonzero(eigen>max(eigen[-1],1e-30)*1e-6))
    pairs=np.flatnonzero(forward<=2.5)
    cost=objective(t,p[nearest_p[pairs]],q[pairs],covariance(np_)[nearest_p[pairs]],covariance(nq)[pairs])/len(pairs) if len(pairs) else None
    ov1=float(np.mean(forward<=2.5)); ov2=float(np.mean(reverse<=2.5)); mse=float((np.mean(np.clip(forward,0,2.5)**2)+np.mean(np.clip(reverse,0,2.5)**2))/2)
    supported=len(ix)>=100 and min(ov1,ov2)>=.7 and rank==6
    return dict(supported=bool(supported),mutual_valid=len(ix),overlap_forward=ov1,overlap_reverse=ov2,rank=rank,
        eigenvalues=eigen.tolist(),surface_H=h.tolist(),gicp_inlier_mean_cost=cost,censored_symmetric_mse=mse,ip=iy.tolist(),iq=ix.tolist())
def compare_support(left,right):
    for k in ('supported','mutual_valid','rank','ip','iq'): assert left[k]==right[k],k
    for k in ('overlap_forward','overlap_reverse','censored_symmetric_mse'): close(left[k],right[k],1e-10)
    close(left['surface_H'],right['surface_H'],2e-6); close(left['eigenvalues'],right['eigenvalues'],2e-6)
    if left['gicp_inlier_mean_cost'] is None: assert right['gicp_inlier_mean_cost'] is None
    else: close(left['gicp_inlier_mean_cost'],right['gicp_inlier_mean_cost'],1e-8)
def preflight():
    r.verify(); r.check_seal(r.BASE/'synthetic','synthetic_seal.json'); z=np.load(r.BASE/'synthetic/fixture.npz'); out=r.read(r.BASE/'synthetic/results.json')
    p,q,np_,nq=z['p'],z['q'],z['np'],z['nq']; t=z['test']; truth=z['truth']; cp,cq=z['cp'],z['cq']; close(cp,covariance(np_)); close(cq,covariance(nq))
    close((truth[:3,:3]@q.T).T+truth[:3,3],p,1e-12); close(objective(t,p,q,cp,cq),z['cost'],1e-9)
    fd=[]; jfd=[]; eps=1e-6; weights=[]; analytic=[]
    for a,b,ca,cb in zip(p,q,cp,cq):
        m=ca+t[:3,:3]@cb@t[:3,:3].T; lam,v=np.linalg.eigh(m); w=v@np.diag(1/np.sqrt(lam))@v.T; weights.append(w)
        analytic.append(w@t[:3,:3]@np.column_stack([-skew(b),np.eye(3)]))
    weights=np.asarray(weights); analytic=np.asarray(analytic)
    for k in range(6):
        d=np.eye(6)[k]*eps; tp=t@exp(d); tm=t@exp(-d)
        fd.append((objective(tp,p,q,cp,cq)-objective(tm,p,q,cp,cq))/(2*eps))
        rp=(tp[:3,:3]@q.T).T+tp[:3,3]-p; rm=(tm[:3,:3]@q.T).T+tm[:3,3]-p
        jfd.append(np.einsum('nij,nj->ni',weights,(rp-rm)/(2*eps)))
    fd=np.asarray(fd); jacfd=np.stack(jfd,axis=2); relative=float(np.linalg.norm(fd-z['gradient'])/np.linalg.norm(z['gradient']))
    assert relative<=1e-5; close(analytic,z['jacobian'],1e-8); close(jacfd,analytic,1e-6)
    compare_support(independent_support(truth,p,q,np_,nq,np.ones(len(p),bool),np.ones(len(q),bool)),out['nondegenerate'])
    plane=z['plane']; pn=z['plane_normals']; compare_support(independent_support(np.eye(4),plane,plane,pn,pn,np.ones(len(plane),bool),np.ones(len(plane),bool)),out['plane'])
    for item in out['periodic']:
        pp=z['periodic']; nn=z['periodic_normals']; compare_support(independent_support(np.asarray(item['T']),pp,pp,nn,nn,np.ones(len(pp),bool),np.ones(len(pp),bool)),item['diagnostics'])
    compare_support(independent_support(np.eye(4),q+100,q,nq,nq,np.ones(len(q),bool),np.ones(len(q),bool)),out['disjoint'])
    replay={}
    for name,a,b,na,nb,known in [('forward',p,q,np_,nq,truth),('reverse',q,p,nq,np_,np.linalg.inv(truth))]:
        actual,_=r.register(a,b,na,nb,np.eye(4)); close(actual,out['outputs'][name]['T'],1e-8); close(actual,known,1e-4); replay[name]=float(np.max(abs(actual-np.asarray(out['outputs'][name]['T']))))
    gg=z['gauge']; actual,_=r.register((gg[:3,:3]@p.T).T+gg[:3,3],(gg[:3,:3]@q.T).T+gg[:3,3],np_@gg[:3,:3].T,nq@gg[:3,:3].T,np.eye(4))
    close(actual,gg@truth@np.linalg.inv(gg),1e-4); close(actual,out['outputs']['gauge']['T'],1e-8)
    r.save(r.BASE/'preflight_validation.json',dict(utc=r.now(),passed=True,independent_gradient_FD_relative=relative,
        independent_frozen_weight_jacobian_max=float(np.max(abs(jacfd-analytic))),shared_solver_replay=replay,
        independently_implemented_GICP=False,rank_and_ambiguity_reconstructed=True))
    print('independent GICP diagnostic mathematics and fixtures pass',flush=True)
def rebuild_normals(p):
    normals=[]; flags=[]; neighbors=[]
    for offset in range(0,len(p),64):
        block=p[offset:offset+64]; squared=np.sum((block[:,None]-p[None])**2,axis=2)
        ordered=np.argsort(squared,axis=1,kind='stable')[:,:20]
        for ids in ordered:
            v=p[ids]-p[ids].mean(0); values,vec=np.linalg.eigh(v.T@v/20)
            good=bool(values[1]>1e-12 and values[1]-values[0]>1e-10*max(1.,values[-1]))
            normals.append(vec[:,0] if good else np.zeros(3)); flags.append(good); neighbors.append(ids)
    return np.asarray(normals),np.asarray(flags),np.asarray(neighbors)
def independent_preprocess(s,i):
    import open3d as o
    raw=np.fromfile(r.raw(s,i),dtype=np.float32).reshape(-1,4)[:,:3]; raw=raw[np.sqrt(np.sum(raw*raw,axis=1))>=1.5]
    x,y,z=raw.T.copy(); rho=np.sqrt(x*x+y*y); mask=rho>1e-6; angle=np.deg2rad(.205); corrected=raw.copy()
    corrected[:,0]=np.where(mask,x*np.cos(angle)-np.where(mask,x*z/np.maximum(rho,1e-6),0)*np.sin(angle),x)
    corrected[:,1]=np.where(mask,y*np.cos(angle)-np.where(mask,y*z/np.maximum(rho,1e-6),0)*np.sin(angle),y)
    corrected[:,2]=np.where(mask,z*np.cos(angle)+np.where(mask,rho,0)*np.sin(angle),z)
    pc=o.geometry.PointCloud(); pc.points=o.utility.Vector3dVector(corrected.astype(float)); pc=pc.voxel_down_sample(.4)
    pc,_=pc.remove_statistical_outlier(nb_neighbors=20,std_ratio=2.5); p=np.asarray(pc.points,dtype=np.float32)
    if len(p)>4000: p=p[np.random.default_rng(42).choice(len(p),4000,replace=False)]
    return p
def inputs():
    r.verify(); r.check_seal(r.INPUT,'input_seal.json'); count=0; maxcov=0.; rawchecks=[]
    for s,ids in r.needed().items():
        for i in ids:
            z=np.load(r.INPUT/s/f'{i:06d}.npz'); original=np.load(r.CACHE/f'input-bank/{s}/{i:06d}.npy'); assert np.array_equal(z['points'],original)
            n,v,idx=rebuild_normals(z['points'].astype(float)); assert np.array_equal(v,z['valid']) and np.array_equal(idx,z['neighbors'])
            delta=float(np.max(abs(covariance(n)-covariance(z['normals'])))); assert delta<=1e-8; maxcov=max(maxcov,delta); count+=1
        r.cap(); print('independent physical normal caches',s,len(ids),flush=True)
    # Independent raw/vertical-correction equations; Open3D voxel/outlier/cap remain shared library.
    for e in r.pilot_rows():
        for i in (e['i'],e['j']):
            local=independent_preprocess(e['seq'],i-1); held=np.load(r.INPUT/e['seq']/f'{i:06d}_holdout.npz')
            close(local,held['local_points'],1e-6)
            odom=r.old.load(r.old.src(e['seq'])/'odom_poses.txt'); relative=np.linalg.solve(odom[i],odom[i-1]); close(relative,held['relative'],1e-9)
            expected=(relative[:3,:3]@local.astype(float).T).T+relative[:3,3]; close(expected,held['points'],1e-6)
            rawchecks.append(dict(seq=e['seq'],frame=i-1,max_point_delta=float(np.max(abs(local-held['local_points'])))))
    r.save(r.BASE/'input_validation.json',dict(utc=r.now(),passed=True,independent_normal_caches=count,independent_covariance_max_delta=maxcov,
        independent_raw_equation_holdout_checks=rawchecks,shared_Open3D_downsampling=True,full_raw_input_replay=False))
    print('input normal/covariance and six heldout raw equations validated',flush=True)
def predictions(pilot):
    r.verify(); folder=r.PILOT if pilot else r.BANK; seal='pilot_seal.json' if pilot else 'bank_seal.json'; r.check_seal(folder,seal)
    selected=r.pilot_rows() if pilot else r.rows(); checks=[]; maxcost=0.; replays={}
    for e in selected:
        data=r.read(folder/f"{e['seq']}_{e['index']:03d}.json"); a=np.load(r.INPUT/e['seq']/f"{e['i']:06d}.npz"); b=np.load(r.INPUT/e['seq']/f"{e['j']:06d}.npz")
        p,q=a['points'].astype(float),b['points'].astype(float); np_,nq=a['normals'],b['normals']; vp,vq=a['valid'],b['valid']
        nd=independent_support(np.asarray(data['predictions']['N']),p,q,np_,nq,vp,vq); compare_support(nd,data['native_diagnostics'])
        for name,value in data['candidates'].items():
            if value['status']=='failed': assert value['T'] is None and value['error']; continue
            t=np.asarray(value['T']); assert r.proper(t); support=independent_support(t,p,q,np_,nq,vp,vq); compare_support(support,value['diagnostics'])
            if support['gicp_inlier_mean_cost'] is not None: maxcost=max(maxcost,abs(support['gicp_inlier_mean_cost']-value['diagnostics']['gicp_inlier_mean_cost']))
        for name,choices in [('W',('GI','GK','GF')),('J',('RI','GK','GF'))]:
            good=[v for v in choices if data['candidates'][v]['status']=='completed' and data['candidates'][v]['diagnostics']['supported']]
            chosen=min(good,key=lambda v:data['candidates'][v]['diagnostics']['censored_symmetric_mse']) if good else 'N'
            assert data['selector_'+name]==dict(selected=chosen,fallback=not bool(good))
            close(data['predictions'][name],data['predictions'][chosen],1e-12)
        hpa=np.load(r.INPUT/e['seq']/f"{e['i']:06d}_holdout.npz")['points']; hpb=np.load(r.INPUT/e['seq']/f"{e['j']:06d}_holdout.npz")['points']
        for name,t in data['predictions'].items():
            if t is None: continue
            t=np.asarray(t); mapped=(t[:3,:3]@hpb.T).T+t[:3,3]; d1=cKDTree(hpa).query(mapped)[0]; d2=cKDTree(mapped).query(hpa)[0]
            values=dict(censored_symmetric_mse=float((np.mean(np.minimum(d1,2.5)**2)+np.mean(np.minimum(d2,2.5)**2))/2),overlap_forward=float(np.mean(d1<=2.5)),overlap_reverse=float(np.mean(d2<=2.5)))
            for key,val in values.items(): close(val,data['holdout'][name][key],1e-8)
        ri=data['candidates']['RI']; prerequisite=ri['status']=='completed' and ri['diagnostics']['supported'] and not data['selector_W']['fallback'] and not data['selector_J']['fallback']
        checks.append(dict(seq=e['seq'],index=e['index'],supported_prerequisite=bool(prerequisite)))
        if e['index']==0 and e['seq'] in r.SEQS[:3]:
            replay=r.predict_one(e); deltas={}
            for name,t in replay['predictions'].items():
                if t is None: assert data['predictions'][name] is None
                else: close(t,data['predictions'][name],1e-5); deltas[name]=float(np.max(abs(np.asarray(t)-data['predictions'][name])))
            replays[e['seq']]=deltas
        r.cap()
    if not pilot:
        assert len(selected)==58
        for e in r.pilot_rows(): assert (folder/f"{e['seq']}_{e['index']:03d}.json").read_bytes()==(r.PILOT/f"{e['seq']}_{e['index']:03d}.json").read_bytes()
    r.verify()
    r.save(r.BASE/('pilot_validation.json' if pilot else 'bank_validation.json'),dict(utc=r.now(),passed=True,edge_count=len(selected),
        expansion_gate=all(v['supported_prerequisite'] for v in checks) if pilot else None,checks=checks,independent_cost_max_delta=maxcost,
        shared_library_pilot_replay_deltas=replays,independently_implemented_solver=False,GT_read=False))
    print('prediction/support/selection/holdout validation passed; expansion',all(v['supported_prerequisite'] for v in checks) if pilot else 'full58',flush=True)
def results():
    r.verify(); value=r.read(r.BASE/'results.json'); full=value['full58']; folder=r.BANK if full else r.PILOT
    seal=r.read(r.BASE/('bank_seal.json' if full else 'pilot_seal.json')); assert seal['utc']<value['gt_read_started_utc']
    assert value['seal_sha256']==r.sha(r.BASE/('bank_seal.json' if full else 'pilot_seal.json'))
    records=[]; maximum=0.
    for row in value['records']:
        s=row['seq']; pc=r.old.load(r.DATA/'poses'/f'{s}.txt'); line=next(v for v in (r.DATA/'sequences'/s/'calib.txt').read_text().splitlines() if v.startswith('Tr:'))
        tr=np.eye(4); tr[:3]=np.asarray([float(x) for x in line.split(':',1)[1].split()]).reshape(3,4)
        gi=np.linalg.solve(tr,pc[row['i']]@tr); gj=np.linalg.solve(tr,pc[row['j']]@tr); truth=np.linalg.solve(gi,gj); close(truth,row['truth'],1e-9)
        pred=r.read(folder/f"{s}_{row['index']:03d}.json"); errors={}
        for name,t in pred['predictions'].items():
            if t is None:
                if name!='RI': assert row['errors'][name] is None; errors[name]=None; continue
                t=pred['predictions']['N']
            t=np.asarray(t); d=t[:3,:3].T@truth[:3,:3]; q=Rotation.from_matrix(d).as_quat(); angle=float(2*np.arctan2(np.linalg.norm(q[:3]),abs(q[3]))*180/np.pi)
            error=dict(t=float(np.sqrt(np.sum((t[:3,3]-truth[:3,3])**2))),R=angle); errors[name]=error
            for k in ('t','R'): maximum=max(maximum,abs(error[k]-row['errors'][name][k])); close(error[k],row['errors'][name][k],1e-8)
        records.append(dict(row,errors=errors))
    gate=None
    if full:
        # Independent arithmetic/gates, not calling runner.gates.
        arms=('N','RI','W','J'); means={a:{k:float(np.mean([v['errors'][a][k] for v in records])) for k in ('t','R')} for a in arms}
        tails={a:{k:float(np.percentile([v['errors'][a][k] for v in records],90)) for k in ('t','R')} for a in arms}
        seq={s:{a:{k:float(np.mean([v['errors'][a][k] for v in records if v['seq']==s])) for k in ('t','R')} for a in arms} for s in r.ACTIVE}
        tests={}
        for a in ('RI','J'):
            tests[a+'_mean_t_gain10pct']=means[a]['t']<=.9*means['N']['t']; tests[a+'_mean_R_nonworse']=means[a]['R']<=means['N']['R']+1e-10
            tests[a+'_support52']=sum(v['supported'][a] for v in records)>=52
            tests[a+'_joint44']=sum(v['errors'][a]['t']<=v['errors']['N']['t']+.01 and v['errors'][a]['R']<=v['errors']['N']['R']+.01 for v in records)>=44
            for k in ('t','R'):
                tests[a+'_q90_'+k]=tails[a][k]<=1.05*tails['N'][k]+.01; tests[a+'_max_harm_'+k]=max(v['errors'][a][k]-v['errors']['N'][k] for v in records)<=.2
            for s in r.ACTIVE:
                subset=[v for v in records if v['seq']==s]; tests[s+'_'+a+'_support90']=sum(v['supported'][a] for v in subset)>=.9*len(subset)
                for k in ('t','R'): tests[s+'_'+a+'_'+k+'_guard']=seq[s][a][k]<=1.05*seq[s]['N'][k]+.01
        increment=dict(mean_t_gain5pct=means['J']['t']<=.95*means['W']['t'],mean_R_nonworse=means['J']['R']<=means['W']['R']+1e-10)
        for s in r.ACTIVE:
            for k in ('t','R'): increment[s+'_'+k+'_guard']=seq[s]['J'][k]<=1.05*seq[s]['W'][k]+.01
        for k in ('t','R'): increment['q90_'+k]=tails['J'][k]<=1.05*tails['W'][k]+.01
        expected=value['gate']; assert tests==expected['engineering_tests'] and increment==expected['increment_tests']
        assert all(tests.values())==expected['engineering_passed'] and all(increment.values())==expected['increment_passed']
        for a in arms:
            for k in ('t','R'): close(means[a][k],expected['means'][a][k],1e-8); close(tails[a][k],expected['q90'][a][k],1e-8)
        for s in r.ACTIVE:
            for a in arms:
                for k in ('t','R'): close(seq[s][a][k],expected['sequence_means'][s][a][k],1e-8)
        gate=dict(engineering_tests=tests,increment_tests=increment,engineering_passed=all(tests.values()),increment_passed=all(increment.values()))
    r.verify(); r.save(r.BASE/'result_validation.json',dict(utc=r.now(),passed=True,relative_pose_records=len(records),independent_metric_max_delta=maximum,
        independently_recomputed_gate=gate,old_reference_is_not_physical_truth=True,scientific_measurement_gate_passed=None if not full else gate['engineering_passed']))
    print('independent reference-pose metric and gate audit passed',flush=True)
def graph():
    r.verify(); r.check_seal(r.BASE/'graphs','graph_seal.json'); value=r.read(r.BASE/'graph_results.json')
    assert value['graph_seal_sha256']==r.sha(r.BASE/'graph_seal.json') and r.read(r.BASE/'graph_seal.json')['utc']<value['gt_read_started_utc']
    import validate_scan_level_graph as metric
    count=0; maximum=0.; actual={}; replays={}
    for s in r.SEQS:
        gt=metric.load(r.DATA/'poses'/f'{s}.txt'); tr=metric.calibration(s); ti=np.linalg.inv(tr); lidar=ti@gt@tr
        o=r.old.load(r.old.src(s)/'odom_poses.txt'); kf=r.read(r.old.src(s)/'keyframes.json'); edges=r.old.loop_records(s); actual[s]={}
        for arm in ('N','RI','W','J'):
            replaced=[]
            for k,e in enumerate(edges):
                entry=r.read(r.BANK/f'{s}_{k:03d}.json'); edge=dict(e)
                if arm=='RI': supported=entry['candidates']['RI']['status']=='completed' and entry['candidates']['RI']['diagnostics']['supported']
                else: supported=arm!='N' and not entry['selector_'+arm]['fallback']
                if supported: edge['T_rel']=entry['predictions'][arm]
                replaced.append(edge)
            t=np.load(r.BASE/f'graphs/{s}_{arm}.npy'); replay=r.old.native(o,kf,replaced); close(t,replay,1e-8); replays[s+'_'+arm]=float(np.max(abs(t-replay)))
            seg=metric.segments(gt,tr@t@ti); count+=len(seg)
            computed=dict(ate=metric.horn_rmse(lidar,t),ter=float(np.mean([v['translation_fraction'] for v in seg])*100),
                rer=float(np.mean([v['rotation_rad_per_m'] for v in seg])*180/np.pi*100),segments=len(seg)); actual[s][arm]=computed
            for k,val in computed.items(): maximum=max(maximum,abs(val-value['rows'][s][arm][k])); close(val,value['rows'][s][arm][k],1e-8)
    means={a:{k:float(np.mean([actual[s][a][k] for s in r.SEQS])) for k in ('ate','ter','rer')} for a in ('N','RI','W','J')}
    checks=dict(mean_ATE_gain5pct=means['J']['ate']<=.95*means['N']['ate'],mean_ter_nonworse=means['J']['ter']<=means['N']['ter']+1e-10,
        mean_rer_nonworse=means['J']['rer']<=means['N']['rer']+1e-10)
    for s in r.SEQS:
        checks[s+'_ATE_guard']=actual[s]['J']['ate']<=1.05*actual[s]['N']['ate']
        for k in ('ter','rer'): checks[s+'_'+k+'_guard']=actual[s]['J'][k]-actual[s]['N'][k]<=.01
    checks['10_no_op']=float(np.max(abs(np.load(r.BASE/'graphs/10_J.npy')-np.load(r.BASE/'graphs/10_N.npy'))))<=1e-5
    assert checks==value['tests'] and all(checks.values())==value['passed']; r.verify()
    r.save(r.BASE/'graph_validation.json',dict(utc=r.now(),passed=True,scientific_graph_gate_passed=all(checks.values()),
        independent_segments=count,independent_metric_max_delta=maximum,shared_optimizer_replay_deltas=replays))
