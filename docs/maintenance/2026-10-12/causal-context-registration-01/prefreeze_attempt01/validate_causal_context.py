"""CCR0 independent raw equations, covariance/support/selection and reference metrics."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import causal_context_registration as r
import validate_measured_gicp as mv

def close(a,b,tol=1e-8):
    a,b=np.asarray(a),np.asarray(b); assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    d=float(np.max(abs(a-b))); assert d<=tol,(d,tol); return d
def intrinsic(p):
    radius=np.hypot(p[:,0],p[:,1]); axis=np.zeros_like(p); good=radius>1e-6
    axis[good,0]=p[good,1]/radius[good]; axis[good,1]=-p[good,0]/radius[good]
    a=.205*np.pi/180; out=p.copy(); out[good]=np.cos(a)*p[good]+np.sin(a)*np.cross(axis[good],p[good]); return out
def projection(poses):
    out=poses.copy()
    for a,z in enumerate(poses):
        u,_,vt=np.linalg.svd(z[:3,:3]); d=np.eye(3); d[2,2]=np.linalg.det(u@vt); out[a,:3,:3]=u@d@vt
    assert np.max(abs(out-poses))<=1e-5; return out
def raw_prefix(s,a,z):
    valid=np.all(np.isfinite(z),axis=1); radius=np.sqrt(np.einsum('ij,ij->i',z[:,:3].astype(float),z[:,:3].astype(float)))
    eligible=np.array([k for k in range(len(z)) if valid[k] and radius[k]>=1.5],dtype=np.int64)
    import hashlib
    seed=int.from_bytes(hashlib.sha256(('CCR0|'+s+'|'+str(a)).encode('utf-8')).digest()[:8],'big')
    ids=np.random.Generator(np.random.PCG64(seed)).permutation(eligible)[:12000]
    code=np.full(len(z),2,dtype=np.uint8); code[valid&(radius<1.5)]=1; code[~valid]=0
    return ids,code
def preflight():
    r.verify(); r.check_seal(r.BASE/'synthetic','synthetic_seal.json'); matrix_max=0.; correction_max=0.
    for k in range(8):
        z=np.load(r.BASE/f'synthetic/{k:02d}.npz'); poses=z['poses']; p=z['p']; t=np.linalg.solve(poses[3],poses[k%3]); matrix_max=max(matrix_max,close(t,z['local']))
        expected=(t[:3,:3]@p.T).T+t[:3,3]; close(expected,z['actual']); close(np.linalg.solve((z['gauge']@poses)[3],(z['gauge']@poses)[k%3]),t)
        ids,_=raw_prefix('fixture',k,z['raw']); assert np.array_equal(ids,z['ids']); correction_max=max(correction_max,close(intrinsic(z['raw'][ids[:100],:3]),z['corrected']))
        result=r.read(r.BASE/'synthetic/results.json')['fixtures'][k]; assert result['history0']==[0] and result['history1']==[0,1] and result['history3']==[1,2,3]
        assert result['quotas']==[[4000],[2000,2000],[1333,1333,1334]]
    z=np.load(r.BASE/'synthetic/geometry.npz'); p,q=z['p'],z['q']; cp,cq=mv.covariance(z['np']),mv.covariance(z['nq']); close(cp,z['cp']); close(cq,z['cq'])
    cost=mv.objective(z['test'],p,q,cp,cq); close(cost,z['cost']); fd=[]
    for a in range(6):
        delta=np.eye(6)[a]*1e-6; fd.append((mv.objective(z['test']@mv.exp(delta),p,q,cp,cq)-mv.objective(z['test']@mv.exp(-delta),p,q,cp,cq))/2e-6)
    error=float(np.linalg.norm(np.asarray(fd)-z['gradient'])/np.linalg.norm(z['gradient'])); assert error<=1e-5
    data=r.read(r.BASE/'synthetic/results.json')
    for key,t,pp,qq,nn,mm in [('nondegenerate',z['truth'],p,q,z['np'],z['nq']),('plane',np.eye(4),z['plane'],z['plane'],z['pn'],z['pn'])]:
        rebuilt=mv.independent_support(t,pp,qq,nn,mm,np.ones(len(pp),bool),np.ones(len(qq),bool)); compare_support(rebuilt,data[key])
    close(z['fitted'],z['truth'],1e-4); assert len(data['periodic'])==2 and data['periodic'][0]['diagnostics']['supported'] and data['periodic'][1]['diagnostics']['supported']
    assert abs(data['periodic'][1]['T'][0][3]-data['periodic'][0]['T'][0][3])>=5.9 and not data['disjoint']['supported']
    r.save(r.BASE/'preflight_validation.json',dict(utc=r.now(),passed=True,fixtures=8,transport_max_delta=matrix_max,correction_max_delta=correction_max,
        independent_Cholesky_gradient_relative_error=error,shared_PCG64_generator=True,independently_implemented_GICP=False))
def compare_support(left,right):
    for key in ('supported','mutual_valid','rank','ip','iq'): assert left[key]==right[key],key
    for key in ('overlap_forward','overlap_reverse','censored_symmetric_mse'): close(left[key],right[key])
    for key in ('surface_H','eigenvalues'):
        x,y=np.asarray(left[key]),np.asarray(right[key]); d=np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30); assert d<=1e-9,(key,d)
    if left['gicp_inlier_mean_cost'] is None: assert right['gicp_inlier_mean_cost'] is None
    else: close(left['gicp_inlier_mean_cost'],right['gicp_inlier_mean_cost'])
def inputs():
    r.verify(); r.check_seal(r.INPUT,'input_seal.json'); raw_checks=0; normal_points=0; brute_rows=0; maxpoint=0.; maxcov=0.; clocks=r.read(r.INPUT/'execution.json')
    census={(x['seq'],x['frame']):x for x in clocks['raw_census']}
    for s,ids in r.raw_needed().items():
        frames=r.read(r.m.old.src(s)/'source_frames.json'); assert frames['source_frame_ids']==list(range(r.m.old.SEQS[s]))
        for a in ids:
            z=np.fromfile(r.m.raw(s,a),dtype='<f4').reshape(-1,4); prefix,code=raw_prefix(s,a,z); stored=np.load(r.INPUT/f'raw/{s}/{a:06d}.npz')
            assert np.array_equal(prefix,stored['prefix']) and np.array_equal(code,stored['codes'])
            c=census[s,a]; assert c['total']==len(z) and c['nonfinite']==int(np.sum(code==0)) and c['below_range']==int(np.sum(code==1)) and c['eligible']==int(np.sum(code==2)); raw_checks+=1
        r.cap()
    for s,ids in r.endpoints().items():
        odom=projection(r.m.old.load(r.m.old.src(s)/'odom_poses.txt'))
        for a in ids:
            clouds={arm:np.load(r.cloud_path(s,a,arm)) for arm in r.ARMS}; n=len(range(max(0,a-2),a+1))
            assert len(clouds['S']['points'])==len(clouds['C']['points'])==4000
            assert len(clouds['F']['points'])==len(clouds['D']['points'])==4000*n
            assert set(map(tuple,clouds['S']['source_ids']))<=set(map(tuple,clouds['D']['source_ids']))
            assert set(map(tuple,clouds['C']['source_ids']))<=set(map(tuple,clouds['F']['source_ids']))
            for arm,z in clouds.items():
                p=z['points']; source=z['source_ids']; frames=list(map(int,z['frames'])); counts=list(map(int,z['counts'])); assert sum(counts)==len(p)
                if arm=='A':
                    previous=np.load(r.m.INPUT/s/f'{a:06d}.npz'); assert np.array_equal(p,previous['points'].astype(float)); assert np.array_equal(z['normals'],previous['normals']); assert np.all(source==-1)
                else:
                    assert len(np.unique(source,axis=0))==len(source) and all(0<=f<=a for f in frames)
                    expected_frames=list(range(max(0,a-2),a+1)) if arm in ('C','F') else [a]; assert frames==expected_frames
                    expected_counts=[4000//n+int(k>=n-4000%n) for k in range(n)] if arm=='C' else ([4000]*n if arm=='F' else [4000 if arm=='S' else n*4000]); assert counts==expected_counts
                    rebuilt=[]
                    for k,(h,count) in enumerate(zip(frames,counts)):
                        raw=np.fromfile(r.m.raw(s,h),dtype=np.float32).reshape(-1,4); prefix,_=raw_prefix(s,h,raw); chosen=np.sort(prefix[:count]); block=source[source[:,0]==h]; assert np.array_equal(block[:,1],chosen)
                        local=intrinsic(raw[chosen,:3].astype(float)); t=np.linalg.solve(odom[a],odom[h]); close(t,z['transforms'][k]); rebuilt.append((t[:3,:3]@local.T).T+t[:3,3])
                    maxpoint=max(maxpoint,close(np.concatenate(rebuilt),p)); assert a in frames
                neighbors=z['neighbors'].astype(int); local=p[neighbors]; centered=local-local.mean(axis=1,keepdims=True)
                values,vectors=np.linalg.eigh(np.einsum('nki,nkj->nij',centered,centered)/20)
                valid=(values[:,1]>1e-12)&(values[:,1]-values[:,0]>1e-10*np.maximum(1.,values[:,-1])); assert np.array_equal(valid,z['valid'])
                normal=vectors[:,:,0]; normal[~valid]=0.; delta=float(np.max(abs(mv.covariance(normal)-mv.covariance(z['normals'])))); assert delta<=1e-8; maxcov=max(maxcov,delta); normal_points+=len(p)
                for row in np.unique(np.linspace(0,len(p)-1,32,dtype=int)):
                    d=np.einsum('ij,ij->i',p-p[row],p-p[row]); ids2=np.lexsort((np.arange(len(p)),d))[:20]; assert np.array_equal(ids2,neighbors[row]); brute_rows+=1
                r.cap()
        print('independent CCR0 inputs',s,len(ids),flush=True)
    r.save(r.BASE/'input_validation.json',dict(utc=r.now(),passed=True,raw_frames_rebuilt=raw_checks,all_PCA_points=normal_points,brute_neighborhood_rows=brute_rows,
        point_max_delta=maxpoint,covariance_max_delta=maxcov,full_brute_neighborhood_replay=False,shared_PCG64=True,GT_read=False))
def predictions(pilot):
    r.verify(); folder=r.PILOT if pilot else r.BANK; r.check_seal(folder,'pilot_seal.json' if pilot else 'bank_seal.json'); selected=r.m.pilot_rows() if pilot else r.rows()
    checks=[]; failed=0; completed=0; replays={}; maxscore=0.
    for e in selected:
        z=r.read(folder/f"{e['seq']}_{e['index']:03d}.json"); assert (z['seq'],z['i'],z['j'],z['index'])==(e['seq'],e['i'],e['j'],e['index']) and z['GT_read'] is False
        edge_ok=True
        for arm,v in z['arms'].items():
            a=np.load(r.cloud_path(e['seq'],e['i'],arm)); b=np.load(r.cloud_path(e['seq'],e['j'],arm)); p,q=a['points'],b['points']; np_,nq=a['normals'],b['normals']; vp,vq=a['valid'],b['valid']
            assert v['point_counts']==[len(p),len(q)]
            for name,c in v['candidates'].items():
                if c['status']=='failed': assert c['error'] and c['T'] is None; failed+=1; continue
                t=np.asarray(c['T']); assert r.m.proper(t); d=mv.independent_support(t,p,q,np_,nq,vp,vq); compare_support(d,c['diagnostics']); completed+=1
                maxscore=max(maxscore,abs(d['censored_symmetric_mse']-c['diagnostics']['censored_symmetric_mse']))
            for bundle,names in [('W',('GI','GK','GF')),('J',('RI','GK','GF'))]:
                good=[key for key in names if v['candidates'][key]['status']=='completed' and v['candidates'][key]['diagnostics']['supported']]
                key=min(good,key=lambda key:v['candidates'][key]['diagnostics']['censored_symmetric_mse']) if good else 'N'
                assert v['selector_'+bundle]==dict(selected=key,fallback=not bool(good)); close(v['predictions'][bundle],v['predictions'][key])
            ri=v['candidates']['RI']; okay=ri['status']=='completed' and ri['diagnostics']['supported'] and not v['selector_J']['fallback'] and not v['selector_W']['fallback']; edge_ok=edge_ok and okay
            checks.append(dict(seq=e['seq'],index=e['index'],arm=arm,supported_prerequisite=bool(okay)))
        if not pilot and e['index']==0 and e['seq'] in r.m.SEQS[:3]:
            assert (folder/f"{e['seq']}_{e['index']:03d}.json").read_bytes()==(r.PILOT/f"{e['seq']}_{e['index']:03d}.json").read_bytes()
            # Six specified S/C arm replays; same solver, independent support equations above.
            replay=r.predict_one(e,('S','C')); deltas={}
            for arm in ('S','C'):
                for name,t in replay['arms'][arm]['predictions'].items():
                    old=z['arms'][arm]['predictions'][name]
                    if t is None: assert old is None
                    else: deltas[arm+'_'+name]=close(t,old,1e-5)
            replays[e['seq']]=deltas
        r.cap(); print('independent CCR0 predictions',e['seq'],e['index'],flush=True)
    if not pilot: assert len(selected)==58
    r.verify(); r.save(r.BASE/('pilot_validation.json' if pilot else 'bank_validation.json'),dict(utc=r.now(),passed=True,edges=len(selected),completed_candidates=completed,
        failed_candidates=failed,checks=checks,expansion_gate=all(v['supported_prerequisite'] for v in checks) if pilot else None,independent_score_max_delta=maxscore,
        shared_solver_replays=replays,independently_implemented_solver=False,GT_read=False))
def independent_pair(records,left,right,prefix):
    def data(key): return np.array([[z['errors'][key]['t'],z['errors'][key]['R']] for z in records])
    x,y=data(left),data(right); tests={prefix+'_mean_t_gain5pct':bool(np.mean(x[:,0])<=.95*np.mean(y[:,0])),prefix+'_mean_R_nonworse':bool(np.mean(x[:,1])<=np.mean(y[:,1])+1e-10),
        prefix+'_joint44':bool(sum(bool(np.all(a<=b+.01)) for a,b in zip(x,y))>=44)}
    for j,key in enumerate(('t','R')):
        tests[prefix+'_q90_'+key]=bool(np.percentile(x[:,j],90)<=1.05*np.percentile(y[:,j],90)+.01); tests[prefix+'_max_harm_'+key]=bool(max(x[:,j]-y[:,j])<=.2)
        for seq in r.m.ACTIVE:
            ix=[k for k,z in enumerate(records) if z['seq']==seq]; tests[prefix+'_'+seq+'_'+key]=bool(np.mean(x[ix,j])<=1.05*np.mean(y[ix,j])+.01)
    return tests
def results():
    r.verify(); result=r.read(r.BASE/'results.json'); full=result['full58']; folder=r.BANK if full else r.PILOT; manifest=r.BASE/('bank_seal.json' if full else 'pilot_seal.json')
    assert r.read(manifest)['utc']<result['gt_read_started_utc'] and r.sha(manifest)==result['prediction_seal_sha256']; records=[]; maximum=0.
    for row in result['records']:
        s=row['seq']; pc=r.m.old.load(r.m.DATA/'poses'/f'{s}.txt'); line=next(x for x in (r.m.DATA/'sequences'/s/'calib.txt').read_text().splitlines() if x.startswith('Tr:'))
        tr=np.eye(4); tr[:3]=np.asarray(line.split(':',1)[1].split(),float).reshape(3,4); gi=np.linalg.solve(tr,pc[row['i']]@tr); gj=np.linalg.solve(tr,pc[row['j']]@tr); truth=np.linalg.solve(gi,gj); close(truth,row['truth'])
        z=r.read(folder/f"{s}_{row['index']:03d}.json"); errors={}; support={}
        def error(t):
            t=np.asarray(t); quat=Rotation.from_matrix(t[:3,:3].T@truth[:3,:3]).as_quat(); return dict(t=float(np.sqrt(np.sum((t[:3,3]-truth[:3,3])**2))),R=float(2*np.arctan2(np.linalg.norm(quat[:3]),abs(quat[3]))*180/np.pi))
        for arm,v in z['arms'].items():
            for name in ('J','W','RI'):
                t=v['predictions'][name] if v['predictions'][name] is not None else v['predictions']['N']; key=arm+'_'+name; errors[key]=error(t)
            support[arm]=not v['selector_J']['fallback']
        errors['N']=error(z['arms']['S']['predictions']['N']); assert support==row['support']
        for key,value in errors.items():
            for metric,v in value.items(): maximum=max(maximum,close(v,row['errors'][key][metric]))
        records.append(dict(**{key:row[key] for key in ('seq','index','i','j')},errors=errors,support=support))
    if full:
        tests={}; increments={}
        for arm,control in [('C','S'),('F','D')]:
            tests.update(independent_pair(records,arm+'_J',control+'_J',arm+'_matched')); tests.update(independent_pair(records,arm+'_J','N',arm+'_native'))
            tests[arm+'_support52']=sum(z['support'][arm] for z in records)>=52
            for s in r.m.ACTIVE:
                rr=[z for z in records if z['seq']==s]; tests[arm+'_'+s+'_support90']=sum(z['support'][arm] for z in rr)>=.9*len(rr)
            increments.update(independent_pair(records,arm+'_J',arm+'_W',arm+'_initializer'))
        assert tests==result['gate']['engineering_tests'] and increments==result['gate']['initializer_tests']; assert all(tests.values())==result['gate']['engineering_passed']
        assert all(increments.values())==result['gate']['initializer_passed']
        for key in errors:
            for metric in ('t','R'):
                close(np.mean([z['errors'][key][metric] for z in records]),result['gate']['means'][key][metric])
                for s in r.m.ACTIVE: close(np.mean([z['errors'][key][metric] for z in records if z['seq']==s]),result['gate']['sequence_means'][s][key][metric])
    else: assert result['gate'] is None and not r.read(r.BASE/'pilot_validation.json')['expansion_gate']
    r.verify(); r.save(r.BASE/'result_validation.json',dict(utc=r.now(),passed=True,records=len(records),pose_metric_max_delta=maximum,full58=full,
        independent_gates=full,decision=result['decision'],physical_truth_certified=False))
    print('independent metrics/gates pass',result['decision'],flush=True)
