"""D1 bounded shared-identity engineering, no evaluator GT or graph code."""
from __future__ import annotations
import argparse,hashlib,json,os,random,resource,sys,time
from pathlib import Path
import numpy as np
import local_motion_common as c
from shared_identity_projector import project,fit,apply,inverse

MAIN=c.MAIN
BASE=MAIN/'docs/maintenance/2026-10-06/shared-identity-engineering-01'
SID0=MAIN/'docs/maintenance/2026-10-06/shared-identity-equations-01'
CAPS=np.array([2000,1000,1000,2000,1000,1000])
LAYOUTS={'L':[0,1,2,3],'R':[0,3,4,5],'U':[0,1,2,3,4,5]}
PAIR_IDS={'00':['00_24_629','00_210_1656'],'08':['08_569_1554','08_583_802']}
ARMS=('I','P','C','U')


def save(p,x):
    if p.exists(): raise RuntimeError('Cannot overwrite '+str(p))
    p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def stage(name,**kw):
    (BASE/'STATUS.json').write_text(json.dumps(dict(stage='D1',status=name,utc=c.now(),**kw),indent=2)+'\n')


def seed(pair,w):
    return int.from_bytes(hashlib.sha256(f'SID1|{pair}|{w}'.encode()).digest()[:4],'big')%(2**31)


def prepare():
    assert not (BASE/'freeze.json').exists()
    rows=[]; cb=c.read(c.C1/'bank.json')
    for seq,expected in PAIR_IDS.items():
        parents=c.read(c.F2/f'inputs_{seq}.json')
        assert [r['key'] for r in parents[:2]]==expected
        old_hashes=c.read(c.F2/f'{seq}_frozen.json')
        for parent in parents[:2]:
            pair=parent['key']; scans=[]
            for e in parent['scans']:
                path=Path(e['path'])
                assert c.sha(path)==e['sha256']
                scans.append(dict(path=str(path),sha256=e['sha256'],id=int(path.stem)))
            assert len(scans)==6
            folder=c.F2/seq/pair
            for name in ('inputs.npz','N0.npz'):
                assert c.sha(folder/name)==old_hashes[f'{pair}/{name}']
            features=c.C1/seq/f'{pair}.npz'
            cached=next(r for r in cb if r['sequence']==seq and r['pair']==pair)
            assert c.sha(features)==cached['sha256']
            rows.append(dict(seq=seq,pair=pair,parent_seed=int(parent['seeds'][0]),scans=scans,
                old_inputs=str(folder/'inputs.npz'),old_native=str(folder/'N0.npz'),features=str(features),
                noise_seeds={w:seed(pair,w) for w in ('L','R')}))
    save(BASE/'manifest.json',dict(stage='D1',pairs=rows,counts=CAPS.tolist(),layouts=LAYOUTS,
         input_whitelist=['points','cond','centers','scale','counts','noise'],feature_whitelist=['features'],
         native_whitelist=['end_point_trajectory','trajectory'],selection='first two original input rows per00/08; no labels'))
    stage('PREPARED_NOT_FROZEN',pairs=4,gt_read=False,inference=False)


def freeze():
    assert not (BASE/'freeze.json').exists()
    m=c.read(BASE/'manifest.json')
    paths=[BASE/'PROTOCOL.md',BASE/'manifest.json',Path(__file__),
        Path(__file__).with_name('validate_shared_identity_engineering.py'),
        Path(__file__).with_name('validate_shared_identity_source_binding.py'),
        Path(__file__).with_name('shared_identity_projector.py'),
        Path(__file__).with_name('validate_shared_identity_equations.py'),
        Path(__file__).with_name('local_motion_common.py'),
        SID0/'freeze.json',SID0/'validation.json',SID0/'validation_seal.json',
        MAIN/'docs/maintenance/2026-10-06/shared-identity-design-01/PLAN.md',
        c.SLAM/'rap_slam/rap_backend.py',c.SLAM/'rap_slam/rap_precision.py',
        c.SLAM/'rap_slam/structured_motion.py',c.SLAM/'rap_slam/real_dataset.py',
        c.SLAM/'rap_slam/trajectory_protocol.py',MAIN/'weights/rap_model_12.ckpt',
        MAIN/'weights/mini_spinnet_t.pth',Path(sys.executable)]
    paths+=list((MAIN/'rectified_point_flow').rglob('*.py'))+list((MAIN/'dataset_process').rglob('*.py'))+list((MAIN/'config').rglob('*.yaml'))
    paths += [c.F2/f'inputs_{s}.json' for s in PAIR_IDS]+[c.F2/f'{s}_frozen.json' for s in PAIR_IDS]+[c.C1/'bank.json']
    for row in m['pairs']:
        paths += [Path(row[k]) for k in ('old_inputs','old_native','features')]+[Path(e['path']) for e in row['scans']]
    # Assert the math code remains the original independently validated SID0.
    original=c.read(SID0/'freeze.json')
    for name in ('shared_identity_projector.py','validate_shared_identity_equations.py'):
        entry=next(e for e in original['sources'] if Path(e['path'].replace('\\','/')).name==name)
        assert c.sha(Path(__file__).with_name(name))==entry['sha256']
    import torch,open3d
    assert torch.cuda.is_available() and os.environ['OMP_NUM_THREADS']=='1' and os.environ['OPENBLAS_NUM_THREADS']=='1'
    save(BASE/'freeze.json',dict(stage='D1',utc=c.now(),pairs=m['pairs'],layouts=LAYOUTS,counts=CAPS.tolist(),
       files={str(p):c.sha(p) for p in sorted(set(paths))},
       runtime=dict(python=sys.version,executable=sys.executable,numpy=np.__version__,torch=torch.__version__,cuda=torch.version.cuda,open3d=open3d.__version__,gpu=torch.cuda.get_device_name(0)),
       limits=dict(wall_s=1800,gpu_bytes=12*2**30,rss_bytes=8*2**30,artifact_bytes=10**9),
       gates=dict(native_normalized_clean_tol=2e-5,native_metric_pose_tol=5e-4,double_pose_tol=1e-7,
                  proper_rotation_tol=1e-10,cast_clean_tol=5e-7,state_recurrence_tol=2e-5,
                  response_multiplier=10.,raw_normalized_floor=2e-5,pose_floor=5e-4,
                  cases_required=4,response_cases_required=4,repeat_exact=True,dummy_exact=True,old_replay_exact=True)))
    stage('FROZEN',pairs=4,gt_read=False,inference=False)


def verify():
    f=c.read(BASE/'freeze.json')
    for p,h in f['files'].items(): assert c.sha(p)==h,p
    return f


def rng_state(b=None):
    import torch
    h=hashlib.sha256()
    for arr in (torch.get_rng_state().cpu().numpy(),torch.cuda.get_rng_state().cpu().numpy(),np.random.get_state()[1]): h.update(arr.tobytes())
    h.update(repr(random.getstate()).encode());h.update(repr(np.random.get_state()[2:]).encode())
    return dict(rng=h.hexdigest(),precision=torch.get_float32_matmul_precision(),backend_seed=None if b is None else b.seed)


def scoped(b,s,fn,*args,**kw):
    from rap_slam.rap_precision import ieee_matmul
    import torch
    before=rng_state(b)
    with c.rng(s),ieee_matmul(),torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
        result=fn(*args,**kw)
    torch.cuda.synchronize()
    after=rng_state(b);assert before==after,(before,after)
    return result,dict(before=before,after=after)


def get_cache(b,row):
    import torch
    from rap_slam.real_dataset import load_scans
    from rap_slam.rap_precision import ieee_matmul
    scans=[]
    for e in row['scans']:
        assert c.sha(e['path'])==e['sha256']
        loaded,_=load_scans(str(Path(e['path']).parent),start=e['id'],end=e['id'],min_range=1.5,kitti205=True)
        scans.append(loaded[0])
    before=rng_state(b)
    with c.rng(row['parent_seed']),ieee_matmul(),torch.inference_mode():
        b.seed=42;points=[];features=[]
        for scan,n in zip(scans,CAPS):
            p,f=b.preprocess(scan,max_points=int(n));assert len(p)==n and f.shape==(n,32)
            points.append(p);features.append(f)
    after=rng_state(b);assert before==after
    with np.load(row['old_inputs'],allow_pickle=False) as z:
        old={k:z[k] for k in ('points','cond','centers','scale','counts','noise')}
    with np.load(row['features'],allow_pickle=False) as z: cached_features=z['features']
    assert np.array_equal(np.concatenate(points),old['points'])
    assert np.array_equal(np.concatenate(features),cached_features)
    assert np.array_equal(CAPS,old['counts'])
    arrays=dict(points=old['points'],features=cached_features,counts=CAPS.copy(),ids=np.array([e['id'] for e in row['scans']]),old_noise=old['noise'][0])
    batches={}
    for w,ids in LAYOUTS.items():
        bb,s,centers,counts=c.batch(b,[points[i] for i in ids],[features[i] for i in ids]);batches[w]=bb
        arrays.update({w+'_cond':bb['pointclouds'].cpu().numpy(),w+'_features':bb['features'].cpu().numpy(),w+'_scale':np.array(s),w+'_centers':centers,w+'_counts':counts})
    for k in ('cond','centers','scale','counts'): assert np.array_equal(arrays['U_'+k],old[k])
    for w in ('L','R'):
        with c.rng(row['noise_seeds'][w]): noise=torch.randn((6000,3),device='cuda')
        arrays['noise_'+w]=noise.cpu().numpy()
    arrays['noise_U']=np.concatenate([arrays['noise_L'],arrays['noise_R'][4000:]])
    return arrays,batches,dict(before=before,after=after)


def joint_input(cache,raw):
    scans=np.array(LAYOUTS['L']+LAYOUTS['R']);counts=CAPS[scans]
    return dict(points=cache['points'].astype(np.float64),point_counts=CAPS.copy(),
        factor_scans=scans,factor_windows=np.repeat([0,1],4),factor_offsets=np.r_[0,np.cumsum(counts)],
        factor_rows=np.concatenate([np.arange(n) for n in counts]),
        scales=np.array([cache['L_scale'],cache['R_scale']]),centers=np.concatenate([cache['L_centers'],cache['R_centers']]),
        cond=np.concatenate([cache['L_cond'],cache['R_cond']]),raw=raw.astype(np.float64))


def solve(cache,raw):
    data=joint_input(cache,raw);t=time.perf_counter();result=project(data)
    assert bool(result['converged']),'SID0 64-sweep nonconvergence'
    result['rel01']=result.pop('rel');result['rel']=inverse(result['Z'][0])@result['Z'][3]
    result['solver_seconds']=np.array(time.perf_counter()-t);data.update(result)
    return data


def cpu_native(cache,raw):
    src=joint_input(cache,raw);parts=[]
    starts=np.r_[0,np.cumsum(CAPS)]
    for f,(i,w) in enumerate(zip(src['factor_scans'],src['factor_windows'])):
        sl=slice(src['factor_offsets'][f],src['factor_offsets'][f+1]);p=src['points'][starts[i]:starts[i+1]]
        T=fit(p,src['raw'][sl]*src['scales'][w]);parts.append(apply(T,p)/src['scales'][w])
    return np.concatenate(parts)


def numpy_dict(result):
    return {k:v.detach().float().cpu().numpy() for k,v in result.items()}


def run(b,batches,cache,arm,dummy=False):
    import torch
    from rectified_point_flow.procrustes import rigidify_prediction_with_procrustes
    windows=['U'] if arm=='U' else ['L','R']
    prepared=[];noises=[];x=[]
    for w in windows:
        bb=dict(batches[w])
        if dummy: bb['pointclouds_gt']=torch.full_like(bb['pointclouds_gt'],123.)
        prepared.append(b.model._prepare_data(bb))
        noises.append(torch.tensor(cache['noise_'+w],device='cuda'));x.append(noises[-1].clone())
    steps={k:[] for k in ('raw','clean','state_before','state_after','velocity')};solvers=[];solver_wall=0.
    for k in range(5):
        t=1-k*.2;before=[v.clone() for v in x];raw=[];vel=[]
        for q,xx in zip(prepared,x):
            _,cond,features,scales,_,anchor,counts,cu,parts=q
            v=b.model.flow_model(x=xx,timesteps=torch.full((len(cu)-1,),t,device=xx.device),cond_coord=cond,
                local_features=features,latent_features=None,scales=scales,anchor_indices=anchor,
                cu_seqlens_batch=cu,cu_seqlens_part=parts)
            vel.append(v);raw.append(xx-v*t)
        if arm=='C':
            solution=solve(cache,torch.cat(raw).float().cpu().numpy());solvers.append(solution)
            clean=list(torch.tensor(solution['clean'].astype(np.float32),device='cuda').split(6000));solver_wall+=float(solution['solver_seconds'])
        elif arm=='P':
            st=time.perf_counter();cl=cpu_native(cache,torch.cat(raw).float().cpu().numpy())
            clean=list(torch.tensor(cl.astype(np.float32),device='cuda').split(6000));solver_wall+=time.perf_counter()-st
        else:
            clean=[rigidify_prediction_with_procrustes(r,q[1],q[6],q[7]) for r,q in zip(raw,prepared)]
        x=[cl*(1-t+.2)+n*(t-.2) for cl,n in zip(clean,noises)]
        for name,vals in [('raw',raw),('clean',clean),('state_before',before),('state_after',x),('velocity',vel)]:
            steps[name].append(torch.cat(vals).detach().clone())
    result={name:torch.stack(vals).float().cpu().numpy() for name,vals in steps.items()}
    result['noise']=torch.cat(noises).float().cpu().numpy();result['solver_seconds']=np.array(solver_wall)
    if arm=='C':
        result['joint_relative_pose']=solvers[-1]['rel']
        result['joint_G']=solvers[-1]['G'];result['joint_Z']=solvers[-1]['Z']
    return result,solvers


def decode(b,batches,cache,arm,arrays):
    import torch
    from rap_slam.structured_motion import decode_parts
    from rap_slam.rap_precision import ieee_matmul
    parts=[];rels=[];windows=['U'] if arm=='U' else ['L','R']
    for wi,w in enumerate(windows):
        raw=arrays['raw'][-1] if arm=='U' else arrays['raw'][-1,6000*wi:6000*(wi+1)]
        with ieee_matmul(),torch.inference_mode():
            pp=decode_parts(batches[w],torch.tensor(raw,device='cuda'),cache[w+'_centers'],float(cache[w+'_scale']))
        parts.append(pp);j=1 if w=='R' else 3;rels.append(np.linalg.inv(pp[0])@pp[j])
    arrays['parts']=np.concatenate(parts);arrays['relative_poses']=np.array(rels)


def cap(start,f):
    import torch
    assert time.monotonic()-start<=f['limits']['wall_s'],'wall cap'
    assert torch.cuda.max_memory_allocated()<=f['limits']['gpu_bytes'],'GPU cap'
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=f['limits']['rss_bytes'],'RSS cap'
    assert sum(p.stat().st_size for p in BASE.rglob('*.npz'))<=f['limits']['artifact_bytes'],'artifact cap'


def bank():
    import torch
    f=verify();assert torch.cuda.is_available();assert not (BASE/'bank').exists()
    (BASE/'bank').mkdir();(BASE/'INCOMPLETE').write_text('D1 bank and both independent validations pending\n');stage('RUNNING')
    started=time.monotonic();active=None;rows=[]
    try:
        initial=rng_state()
        with c.rng(42): b,audit=c.make_backend()
        b.max_points_per_scan=4000;b.feature_extractor.model.eval()
        assert initial==rng_state();assert audit['rap_keys']==344 and audit['descriptor_keys']==58
        torch.cuda.reset_peak_memory_stats()
        for row in f['pairs']:
            active=row['pair'];cache,batches,input_state=get_cache(b,row);np.savez_compressed(BASE/'bank'/f'{active}_input.npz',**cache)
            files=[f'bank/{active}_input.npz'];audits=[];data={}
            # Original noise has its own provenance; never substitute new trial noise.
            old,st=scoped(b,row['parent_seed'],b.model.sample_rectified_flow,batches['U'],None,
                          x_1=torch.tensor(cache['old_noise'],device='cuda'),return_tarjectory=True)
            old=numpy_dict(old)
            with np.load(row['old_native'],allow_pickle=False) as z:
                assert np.array_equal(old['end_point_trajectory'],z['end_point_trajectory'])
                assert np.array_equal(old['trajectory'],z['trajectory'])
            name=f'bank/{active}_old_native.npz';np.savez_compressed(BASE/name,raw=old['end_point_trajectory'],state_after=old['trajectory']);files.append(name);audits.append(dict(operation='old_native',restored_state=st))
            for arm in ARMS:
                stt=time.monotonic();(a,solvers),st=scoped(b,row['parent_seed'],run,b,batches,cache,arm)
                a['wall_seconds']=np.array(time.monotonic()-stt);decode(b,batches,cache,arm,a);data[arm]=a
                name=f'bank/{active}_{arm}.npz';np.savez_compressed(BASE/name,**a);files.append(name)
                for k,solution in enumerate(solvers):
                    sn=f'bank/{active}_C_s{k}.npz';np.savez_compressed(BASE/sn,**solution);files.append(sn)
                audits.append(dict(operation=arm,restored_state=st))
                for tag,dummy in [('repeat',False),('dummy',True)]:
                    (other,_),st=scoped(b,row['parent_seed'],run,b,batches,cache,arm,dummy)
                    decode(b,batches,cache,arm,other)
                    for key in ('raw','clean','state_before','state_after','velocity','noise','parts','relative_poses')+ (('joint_relative_pose','joint_G','joint_Z') if arm=='C' else ()):
                        assert np.array_equal(a[key],other[key]),(active,arm,tag,key)
                    sn=f'bank/{active}_{arm}_{tag}.npz';np.savez_compressed(BASE/sn,**other);files.append(sn)
                    audits.append(dict(operation=arm+'_'+tag,restored_state=st))
                cap(started,f)
            for w in ('L','R','U'):
                native,st=scoped(b,row['parent_seed'],b.model.sample_rectified_flow,batches[w],None,
                    x_1=torch.tensor(cache['noise_'+w],device='cuda'),return_tarjectory=True)
                native=numpy_dict(native);which=data['U'] if w=='U' else data['I'];sl=slice(None) if w=='U' else slice(0,6000) if w=='L' else slice(6000,12000)
                assert np.array_equal(native['end_point_trajectory'],which['raw'][:,sl])
                assert np.array_equal(native['trajectory'],which['state_after'][:,sl])
                sn=f'bank/{active}_native_{w}.npz';np.savez_compressed(BASE/sn,raw=native['end_point_trajectory'],state_after=native['trajectory']);files.append(sn)
                audits.append(dict(operation='native_'+w,restored_state=st))
            for terminal,parent in [('F','I'),('PF','P')]:
                solution=solve(cache,data[parent]['raw'][-1]);sn=f'bank/{active}_{terminal}.npz';np.savez_compressed(BASE/sn,**solution);files.append(sn)
            rows.append(dict(pair=active,seq=row['seq'],files=files,rng_precision_audits=audits,input_rng_precision=input_state,
                primary_neural_calls=dict(I=10,P=10,C=10,U=5,F=0,PF=0),standalone_neural_calls=dict(F=10,PF=10)))
            print('D1 sealed pair output',active,'elapsed',round(time.monotonic()-started,2),flush=True);cap(started,f)
        verify()
        save(BASE/'bank.json',dict(stage='D1',rows=rows,checkpoint=audit,wall_s=time.monotonic()-started,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            dataset_gt_read=False,pose_accuracy_computed=False))
        files=sorted((BASE/'bank').glob('*.npz'))
        save(BASE/'bank_seal.json',dict(stage='D1',utc=c.now(),freeze_sha256=c.sha(BASE/'freeze.json'),bank_sha256=c.sha(BASE/'bank.json'),
            files={p.relative_to(BASE).as_posix():c.sha(p) for p in files}))
        stage('BANK_SEALED',pairs=4,gt_read=False)
        print('D1 complete bank sealed',len(files),flush=True)
    except Exception as exc:
        save(BASE/'FAILURE_01.json',dict(stage='BANK_FAILED',pair=active,completed_pairs=len(rows),error=repr(exc),wall_s=time.monotonic()-started))
        stage('INCOMPLETE_BANK_FAILED',error=repr(exc),pair=active);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','freeze','bank']);args=parser.parse_args()
    {'prepare':prepare,'freeze':freeze,'bank':bank}[args.stage]()
