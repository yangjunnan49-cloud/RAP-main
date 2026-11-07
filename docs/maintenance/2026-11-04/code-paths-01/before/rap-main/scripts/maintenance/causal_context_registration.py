"""CCR0 isolated causal-return experiment. See prospective protocol; old sources read-only."""
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
from datetime import datetime, timezone
from pathlib import Path

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-12/causal-context-registration-01'
SUP=BASE/'supervision'; INPUT=BASE/'input'; PILOT=BASE/'pilot'; BANK=BASE/'bank'
RPC=MAIN/'docs/maintenance/2026-10-12/reference-physical-consistency-01'
ARMS=('A','S','C','D','F'); CAP_SECONDS=5400; START=None

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,value):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(value,f,indent=2,allow_nan=False); f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def history(a): return list(range(max(0,a-2),a+1))
def seed(s,a): return int.from_bytes(hashlib.sha256(f'CCR0|{s}|{a}'.encode()).digest()[:8],'big')
def quotas(n): return [4000//n+int(k>=n-4000%n) for k in range(n)]
def rows(): return m.rows()
def endpoints(): return m.needed()
def raw_needed(): return {s:sorted({h for a in ids for h in history(a)}) for s,ids in endpoints().items()}
def select_raw(s,a,z):
    finite=np.isfinite(z).all(1); radius=np.linalg.norm(z[:,:3].astype(float),axis=1)
    eligible=np.flatnonzero(finite&(radius>=1.5)); assert len(eligible)>=12000,(s,a,len(eligible))
    prefix=np.random.Generator(np.random.PCG64(seed(s,a))).permutation(eligible)[:12000]
    return prefix,dict(total=len(z),nonfinite=int((~finite).sum()),below_range=int((finite&(radius<1.5)).sum()),eligible=len(eligible))
def corrected(p):
    x,y,z=p.T; rho=np.hypot(x,y); good=rho>1e-6; a=np.deg2rad(.205)
    out=p.copy(); out[good,0]=x[good]*np.cos(a)-x[good]*z[good]/rho[good]*np.sin(a)
    out[good,1]=y[good]*np.cos(a)-y[good]*z[good]/rho[good]*np.sin(a)
    out[good,2]=z[good]*np.cos(a)+rho[good]*np.sin(a); return out
def seal(folder,name):
    save(BASE/name,dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
def check_seal(folder,name):
    z=read(BASE/name); assert z['freeze_sha256']==sha(BASE/'freeze.json')
    assert z['files']=={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def verify():
    f=read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['repositories']==m.old.repositories()
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','open3d')}
def freeze():
    files=dict(read(RPC/'freeze.json')['files'])
    amendment=read(RPC/'VALIDATION_AMENDMENT_FREEZE02.json')
    original_path=amendment['original_validator_path']; original_snapshot=amendment['original_validator_snapshot']
    assert files[original_path]==amendment['original_validator_sha256']==sha(original_snapshot)
    original_hash=files.pop(original_path); files[original_snapshot]=original_hash
    for p,h in amendment['files'].items(): assert sha(p)==h,p; files[p]=h
    files[str(RPC/'VALIDATION_AMENDMENT_FREEZE02.json')]=sha(RPC/'VALIDATION_AMENDMENT_FREEZE02.json')
    for folder in (RPC,MAIN/'docs/maintenance/2026-10-12/conversation-handoff-01',MAIN/'docs/maintenance/2026-10-12/reference-physical-consistency-delivery-note-01'):
        for v in read(folder/'DELIVERY_SEAL.json')['files']:
            p=folder/v['path']; assert sha(p)==v['sha256']; files[str(p)]=v['sha256']
        files[str(folder/'DELIVERY_SEAL.json')]=sha(folder/'DELIVERY_SEAL.json')
    paths=[BASE/n for n in ('OWNER_SCOPE.md','PROTOCOL.md','AMENDMENT_01.md','FAILURE_freeze.json')]
    paths += [p for folder in (BASE/'prefreeze_attempt01',SUP/'freeze') for p in sorted(folder.rglob('*')) if p.is_file()]
    paths += [Path(__file__),Path(__file__).with_name('validate_causal_context.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),Path(m.__file__),Path(m.o3d.pybind.__file__),Path(m.o3d.__file__)]
    for s,ids in raw_needed().items():
        paths += [m.raw(s,a) for a in ids]
        paths += [m.old.src(s)/n for n in ('source_frames.json','summary.json','odom_poses.txt','accepted_loops.json')]
        paths += [m.DATA/'sequences'/s/n for n in ('calib.txt','times.txt')]+[m.DATA/'poses'/f'{s}.txt']
    for s,ids in endpoints().items(): paths += [m.INPUT/s/f'{a:06d}.npz' for a in ids]
    for p in paths: files[str(p)]=sha(p)
    for p,h in files.items(): assert sha(p)==h,p
    repositories=m.old.repositories(); assert repositories==read(RPC/'freeze.json')['repositories']
    snapshot=BASE/'source_snapshot'; snapshot.mkdir()
    for k,p in enumerate(paths):
        if p.suffix in ('.py','.ps1'):
            q=snapshot/f'{k:03d}_{p.name}'; q.write_bytes(p.read_bytes()); assert sha(q)==sha(p)
    save(BASE/'freeze.json',dict(utc=now(),files=files,repositories=repositories,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','open3d')},
        rows=rows(),endpoints=endpoints(),raw_needed=raw_needed(),history_length=3,arms=ARMS,cap_seconds=CAP_SECONDS,cap_RSS_bytes=4*2**30,cap_artifact_bytes=2**30,
        original_RPC0_validator_alias=dict(original_path=original_path,original_sha256=original_hash,snapshot=original_snapshot),retained_prefreeze_failure=True))
    (BASE/'INCOMPLETE').write_text('CCR0 scientific prerequisites/comparison/independent validation pending.\n')
    print('CCR0 frozen',len(files),'identities;',sum(map(len,raw_needed().values())),'causal raw frames',flush=True)
def preflight():
    verify(); dest=BASE/'synthetic'; dest.mkdir(); rng=np.random.default_rng(20261012); results=[]
    for k in range(8):
        poses=np.asarray([m.exp(rng.normal(size=6)*.3) for _ in range(4)]); gauge=m.exp(rng.normal(size=6)*.3); p=rng.normal(size=(80,3))
        local=np.linalg.inv(poses[3])@poses[k%3]; actual=m.transform(p,local); gauged=np.linalg.inv(gauge@poses[3])@(gauge@poses[k%3]); assert np.max(abs(local-gauged))<=1e-8
        assert np.max(abs(m.transform(actual,np.linalg.inv(local))-p))<=1e-8
        assert np.max(abs(m.transform(p,np.linalg.inv(poses[3])@poses[3])-p))<=1e-8
        z=np.column_stack([rng.uniform(-30,30,(15000,3)),rng.uniform(size=15000)]); ids,census=select_raw('fixture',k,z)
        assert len(np.unique(ids))==12000 and set(ids[:4000])<=set(ids)
        cp=corrected(z[ids[:100],:3]); reference=m.old.SLAM
        from rap_slam.real_dataset import kitti_vertical_correction
        assert np.max(abs(cp-kitti_vertical_correction(z[ids[:100],:3],.205)))<=1e-8
        np.savez(dest/f'{k:02d}.npz',poses=poses,gauge=gauge,p=p,local=local,actual=actual,raw=z,ids=ids,corrected=cp)
        results.append(dict(index=k,census=census,history0=history(0),history1=history(1),history3=history(3),quotas=[quotas(n) for n in (1,2,3)]))
    q,nq=m.fixture(); truth=m.exp(np.array([.012,-.02,.018,.03,-.02,.015])); p=m.transform(q,truth); np_=nq@truth[:3,:3].T
    fitted,solver=m.register(p,q,np_,nq,np.eye(4)); assert np.max(abs(fitted-truth))<=1e-4
    test=truth@m.exp(np.array([.018,-.009,.012,.015,-.02,.01])); cp,cq=m.covariances(np_),m.covariances(nq)
    cost,grad,jac,res,w=m.diagnostic_objective(test,p,q,cp,cq); fd=[]
    for a in range(6):
        d=np.eye(6)[a]*1e-6; fd.append((m.diagnostic_objective(test@m.exp(d),p,q,cp,cq)[0]-m.diagnostic_objective(test@m.exp(-d),p,q,cp,cq)[0])/2e-6)
    assert np.linalg.norm(np.asarray(fd)-grad)/np.linalg.norm(grad)<=1e-5
    plane=np.asarray([[x,y,0.] for x in np.linspace(-3,3,15) for y in np.linspace(-3,3,15)]); pn=np.tile([0.,0.,1.],(len(plane),1))
    plane_diag=m.diagnostics(np.eye(4),plane,plane,pn,pn,np.ones(len(plane),bool),np.ones(len(plane),bool)); assert plane_diag['rank']==3 and not plane_diag['supported']
    non=m.diagnostics(truth,p,q,np_,nq,np.ones(len(p),bool),np.ones(len(q),bool)); assert non['supported']
    periodic=np.concatenate([q+[6*a,0,0] for a in range(-2,3)]); normals=np.tile(nq,(5,1)); ambiguity=[]
    for x in (0.,6.):
        init=np.eye(4); init[0,3]=x; fit,info=m.register(periodic,periodic,normals,normals,init)
        diag=m.diagnostics(fit,periodic,periodic,normals,normals,np.ones(len(periodic),bool),np.ones(len(periodic),bool)); assert diag['supported'] and diag['gicp_inlier_mean_cost']<=1e-12
        ambiguity.append(dict(T=fit.tolist(),diagnostics=diag,solver=info))
    assert abs(ambiguity[1]['T'][0][3]-ambiguity[0]['T'][0][3])>=5.9
    disjoint=m.diagnostics(np.eye(4),q+100,q,nq,nq,np.ones(len(q),bool),np.ones(len(q),bool)); assert not disjoint['supported']
    np.savez(dest/'geometry.npz',p=p,q=q,np=np_,nq=nq,truth=truth,fitted=fitted,test=test,cp=cp,cq=cq,cost=cost,gradient=grad,fd=fd,plane=plane,pn=pn)
    save(dest/'results.json',dict(utc=now(),fixtures=results,solver=solver,nondegenerate=non,plane=plane_diag,periodic=ambiguity,disjoint=disjoint))
    seal(dest,'synthetic_seal.json'); print('causal/gauge/IDs/derivatives/rank/alias fixtures sealed',flush=True)
def cloud_path(s,a,arm): return INPUT/s/f'{a:06d}_{arm}.npz'
def inputs():
    verify(); assert read(BASE/'preflight_validation.json')['passed']; INPUT.mkdir(); corpus=INPUT/'raw'; corpus.mkdir(); census=[]; clocks=[]
    for s,ids in raw_needed().items():
        (corpus/s).mkdir(); clock=time.monotonic()
        for a in ids:
            z=np.fromfile(m.raw(s,a),dtype=np.float32).reshape(-1,4); prefix,info=select_raw(s,a,z)
            np.savez(corpus/s/f'{a:06d}.npz',prefix=prefix,codes=np.where(~np.isfinite(z).all(1),0,np.where(np.linalg.norm(z[:,:3].astype(float),axis=1)<1.5,1,2)).astype(np.uint8))
            census.append(dict(seq=s,frame=a,**info)); cap()
        clocks.append(dict(seq=s,raw_read_selection_seconds=time.monotonic()-clock))
    for s,ids in endpoints().items():
        (INPUT/s).mkdir(); odom=m.old.proper(m.old.load(m.old.src(s)/'odom_poses.txt'))
        for a in ids:
            start=time.monotonic(); hs=history(a); local={}; prefixes={}; transforms={}
            for h in hs:
                z=np.fromfile(m.raw(s,h),dtype=np.float32).reshape(-1,4); prefix=np.load(corpus/s/f'{h:06d}.npz')['prefix']; prefixes[h]=prefix
                transforms[h]=np.linalg.inv(odom[a])@odom[h]; local[h]=corrected(z[:,:3].astype(float))
            info=[]
            for arm in ARMS:
                construct=time.monotonic()
                if arm=='A':
                    z=np.load(m.INPUT/s/f'{a:06d}.npz'); points=z['points'].astype(float); normals=z['normals']; valid=z['valid']; neighbors=z['neighbors']; source=np.full((len(points),2),-1,dtype=np.int64)
                    hs_used=[a]; ns=[len(points)]; normal_time=0.
                else:
                    hs_used=hs if arm in ('C','F') else [a]
                    ns=quotas(len(hs)) if arm=='C' else ([4000]*len(hs) if arm=='F' else [4000 if arm=='S' else 4000*len(hs)])
                    pp=[]; ii=[]
                    for h,n in zip(hs_used,ns):
                        chosen=np.sort(prefixes[h][:n]); pp.append(m.transform(local[h][chosen],transforms[h])); ii.append(np.column_stack([np.full(n,h),chosen]))
                    points=np.concatenate(pp); source=np.concatenate(ii); assert len(np.unique(source,axis=0))==len(source)
                    nt=time.monotonic(); normals,valid,neighbors=m.estimate(points); normal_time=time.monotonic()-nt
                np.savez(cloud_path(s,a,arm),points=points,normals=normals,valid=valid,neighbors=neighbors.astype(np.int32),source_ids=source,
                    frames=np.asarray(hs_used),counts=np.asarray(ns),transforms=np.asarray([transforms[h] for h in hs_used]))
                info.append(dict(arm=arm,points=len(points),valid_normals=int(valid.sum()),frames=hs_used,counts=ns,normal_seconds=normal_time,construction_seconds=time.monotonic()-construct))
            clocks.append(dict(seq=s,endpoint=a,all_arms_seconds=time.monotonic()-start,arms=info)); cap()
        print('causal inputs',s,len(ids),'endpoints',flush=True)
    save(INPUT/'execution.json',dict(utc=now(),raw_census=census,timings=clocks,endpoints=endpoints(),raw_needed=raw_needed(),GT_read=False)); seal(INPUT,'input_seal.json')
def predict_one(e,arms=ARMS):
    s,a,b=e['seq'],e['i'],e['j']; native=m.rigid(np.asarray(e['T_rel'])); odom=m.old.proper(m.old.load(m.old.src(s)/'odom_poses.txt')); kiss=m.rigid(np.linalg.inv(odom[a])@odom[b]); outputs={}
    for arm in arms:
        start=time.monotonic(); za=np.load(cloud_path(s,a,arm)); zb=np.load(cloud_path(s,b,arm)); p,q=za['points'],zb['points']; np_,nq=za['normals'],zb['normals']; vp,vq=za['valid'],zb['valid']
        candidates={}; starts=dict(RI=native,GI=np.eye(4),GK=kiss); f=None; finfo=None
        try: f,finfo=m.global_init(p,q,np_,nq); starts['GF']=f
        except Exception as err: candidates['GF']=dict(status='failed',error=repr(err),T=None,diagnostics=None)
        for name,t in starts.items():
            try:
                out,solver=m.register(p,q,np_,nq,t); diag=m.diagnostics(out,p,q,np_,nq,vp,vq)
                candidates[name]=dict(status='completed',T=out.tolist(),initial=t.tolist(),solver=solver,diagnostics=diag)
            except Exception as err: candidates[name]=dict(status='failed',error=repr(err),T=None,initial=t.tolist(),diagnostics=None)
        select_start=time.monotonic(); w,wi=m.select(candidates,('GI','GK','GF'),native); j,ji=m.select(candidates,('RI','GK','GF'),native)
        outputs[arm]=dict(candidates=candidates,predictions=dict(N=native.tolist(),K=kiss.tolist(),F_init=None if f is None else f.tolist(),W=w.tolist(),J=j.tolist(),**{name:v['T'] for name,v in candidates.items()}),
            selector_W=wi,selector_J=ji,fgr=finfo,point_counts=[len(p),len(q)],selection_seconds=time.monotonic()-select_start,all_seconds=time.monotonic()-start)
        cap()
    return dict(seq=s,index=e['index'],i=a,j=b,measurement_id=e.get('measurement_id'),arms=outputs,GT_read=False)
def predictions(pilot=False):
    verify(); check_seal(INPUT,'input_seal.json'); assert read(BASE/'input_validation.json')['passed']
    if not pilot: assert read(BASE/'pilot_validation.json')['expansion_gate']
    dest=PILOT if pilot else BANK; dest.mkdir(); selected=m.pilot_rows() if pilot else rows(); started=now()
    for e in selected:
        name=f"{e['seq']}_{e['index']:03d}.json"
        if not pilot and (PILOT/name).exists(): (dest/name).write_bytes((PILOT/name).read_bytes())
        else: save(dest/name,predict_one(e))
        print('registered',e['seq'],e['index'],'five observation arms',flush=True); cap()
    save(dest/'execution.json',dict(utc=now(),started_utc=started,edges=len(selected),GT_read=False,pilot_reused=0 if pilot else 3)); seal(dest,'pilot_seal.json' if pilot else 'bank_seal.json')
def pair_tests(records,left,right,prefix):
    result={}; errors=lambda key:np.asarray([[z['errors'][key]['t'],z['errors'][key]['R']] for z in records])
    x,y=errors(left),errors(right); result[prefix+'_mean_t_gain5pct']=bool(x[:,0].mean()<=.95*y[:,0].mean()); result[prefix+'_mean_R_nonworse']=bool(x[:,1].mean()<=y[:,1].mean()+1e-10)
    result[prefix+'_joint44']=bool(np.count_nonzero(np.all(x<=y+.01,axis=1))>=44)
    for a,k in enumerate(('t','R')):
        result[prefix+'_q90_'+k]=bool(np.quantile(x[:,a],.9)<=1.05*np.quantile(y[:,a],.9)+.01)
        result[prefix+'_max_harm_'+k]=bool(np.max(x[:,a]-y[:,a])<=.2)
        for s in m.ACTIVE:
            ids=[j for j,z in enumerate(records) if z['seq']==s]; result[prefix+'_'+s+'_'+k]=bool(x[ids,a].mean()<=1.05*y[ids,a].mean()+.01)
    return result
def gates(records):
    tests={}
    for arm,control in (('C','S'),('F','D')):
        tests.update(pair_tests(records,arm+'_J',control+'_J',arm+'_matched')); tests.update(pair_tests(records,arm+'_J','N',arm+'_native'))
        tests[arm+'_support52']=sum(z['support'][arm] for z in records)>=52
        for s in m.ACTIVE:
            rr=[z for z in records if z['seq']==s]; tests[arm+'_'+s+'_support90']=sum(z['support'][arm] for z in rr)>=.9*len(rr)
    increment={}
    for arm in ('C','F'): increment.update(pair_tests(records,arm+'_J',arm+'_W',arm+'_initializer'))
    keys=list(records[0]['errors']); means={key:{k:float(np.mean([z['errors'][key][k] for z in records])) for k in ('t','R')} for key in keys}
    seq={s:{key:{k:float(np.mean([z['errors'][key][k] for z in records if z['seq']==s])) for k in ('t','R')} for key in keys} for s in m.ACTIVE}
    return dict(engineering_tests=tests,engineering_passed=all(tests.values()),initializer_tests=increment,initializer_passed=all(increment.values()),means=means,sequence_means=seq,
        decision='SAFE_CAUSAL_CONTEXT_HEADROOM' if all(tests.values()) else 'NO_SAFE_CAUSAL_CONTEXT_HEADROOM')
def evaluate():
    verify(); full=(BASE/'bank_seal.json').exists(); folder=BANK if full else PILOT; manifest='bank_seal.json' if full else 'pilot_seal.json'; check_seal(folder,manifest)
    assert read(BASE/('bank_validation.json' if full else 'pilot_validation.json'))['passed']
    if not full: assert not read(BASE/'pilot_validation.json')['expansion_gate']
    started=now(); gt={}; records=[]
    from rap_slam.real_dataset import load_gt_poses
    for s in m.ACTIVE: gt[s]=np.asarray(load_gt_poses(str(m.DATA/'poses'/f'{s}.txt'),str(m.DATA/'sequences'/s/'calib.txt'),apply_calib=True))
    for e in rows() if full else m.pilot_rows():
        z=read(folder/f"{e['seq']}_{e['index']:03d}.json"); truth=np.linalg.inv(gt[e['seq']][e['i']])@gt[e['seq']][e['j']]; errors={}; support={}
        for arm,v in z['arms'].items():
            for name in ('J','W','RI'):
                t=v['predictions'][name] if v['predictions'][name] is not None else v['predictions']['N']; errors[arm+'_'+name]=m.pose_error(t,truth)
            support[arm]=not v['selector_J']['fallback']
        errors['N']=m.pose_error(z['arms']['S']['predictions']['N'],truth)
        records.append(dict(seq=e['seq'],index=e['index'],i=e['i'],j=e['j'],truth=truth.tolist(),errors=errors,support=support))
    save(BASE/'results.json',dict(utc=now(),gt_read_started_utc=started,prediction_seal_sha256=sha(BASE/manifest),full58=full,records=records,gate=gates(records) if full else None,
        decision=gates(records)['decision'] if full else 'PILOT_SUPPORT_PREREQUISITE_STOP',physical_cause_resolved=False,system_metrics_executed=False))
    print('sealed measurement decision',read(BASE/'results.json')['decision'],flush=True)
def usage():
    return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        artifact_bytes=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()),GPU_calls=0,imports_included_in_time=True)
def cap():
    u=usage(); assert u['peak_RSS_bytes']<=4*2**30 and u['artifact_bytes']<=2**30,u
    if (SUP/'host_latest.json').exists(): assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START,np,m
    START=time.monotonic(); ok=False; error=None
    used=sum(read(p)['wall_seconds'] for p in SUP.glob('*/child_exit.json')); assert used<CAP_SECONDS
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('CCR0 combined scientific child cap'))); signal.alarm(max(1,int(CAP_SECONDS-used)))
    try:
        import numpy as np
        import measured_gicp_registration as m
        assert m.o3d.__DEVICE_API__=='cpu'; cap()
        if stage.startswith('validate_'):
            import validate_causal_context as v
            dict(validate_preflight=v.preflight,validate_inputs=v.inputs,validate_pilot=lambda:v.predictions(True),validate_bank=lambda:v.predictions(False),validate_results=v.results)[stage]()
        else: dict(freeze=freeze,freeze02=freeze,preflight=preflight,inputs=inputs,pilot=lambda:predictions(True),bank=lambda:predictions(False),evaluate=evaluate)[stage]()
        cap(); ok=True
    except BaseException as e:
        error=repr(e); traceback.print_exc(); save(BASE/f'FAILURE_{stage}.json',dict(utc=now(),error=error,**usage()))
    finally:
        signal.alarm(0); save(SUP/stage/'child_exit.json',dict(utc=now(),success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok: sys.exit(1)
if __name__=='__main__':
    sys.modules['causal_context_registration']=sys.modules[__name__]; run(sys.argv[1])
