"""Prospective LMF1 freezer and GT-free complete prediction bank."""
import os,resource,sys,time
from pathlib import Path
import numpy as np
import local_motion_common as c
B=c.SCREEN
P=c.PREFLIGHT/'attempt-02'

def poses(path,n):
    a=np.loadtxt(path).reshape(-1,3,4);assert len(a)==n and np.isfinite(a).all()
    out=np.tile(np.eye(4),(n,1,1));out[:,:3]=a;return out
def valid(T,tol=1e-8):
    assert T.shape==(4,4) and np.isfinite(T).all() and np.array_equal(T[3],[0,0,0,1])
    R=T[:3,:3];assert abs(R.T@R-np.eye(3)).max()<tol and abs(np.linalg.det(R)-1)<tol
def cap(t):
    assert time.monotonic()-t<1800 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20<4
    assert sum(p.stat().st_size for p in B.rglob('*') if p.is_file())<250000000
def dependencies():
    files=c.frozen_sources()+[Path(__file__),Path(__file__).with_name('evaluate_local_motion_screen.py'),
        Path(__file__).with_name('validate_local_motion_screen.py'),Path(__file__).with_name('validate_local_motion_feasibility_v2.py'),
        Path(__file__).with_name('validate_local_motion_source_binding.py'),B/'PROTOCOL.md',B/'preflight.json',
        c.PREFLIGHT/'NEXT_ROUND_PLAN.md',P/'freeze.json',P/'bank_seal.json',P/'validation.json',P/'source_binding_validation.json',
        P/'supplement_freeze.json',c.DATE/'temporal-identity-audit-01/freeze.json',c.DATE/'temporal-identity-audit-01/validation.json']
    for r in c.census()['rows']:files+=list(map(Path,r['paths']))
    for s in c.SEQS:
        files += [c.source(s)/'odom_poses.txt',c.DATA/'poses'/f'{s}.txt',c.DATA/'sequences'/s/'calib.txt',P/'bank'/f'local_{s}.npz']
    return sorted(set(files))
def preflight():
    import evaluate_local_motion_screen as e
    import validate_local_motion_screen as v
    t=time.monotonic();cases=e.synthetic();maximum=0.
    for truth,pred,expected in cases:
        x=e.error(truth,pred);y=v.error(truth,pred)
        maximum=max(maximum,max(abs(x[k]-y[k]) for k in x))
        assert abs(x['translation_m']-expected[0])<1e-10 and abs(x['rotation_deg']-expected[1])<1e-8
        assert max(abs(x[k]-y[k]) for k in x)<1e-8
    cc=c.census();fake=[]
    for r in cc['rows']:
        fake.append(dict(seq=r['seq'],t=r['t'],errors={a:dict(translation_m=.02 if a=='R3' else (.035 if a=='R2' else .08),rotation_deg=.01) for a in e.ARMS}))
    good=e.aggregate(fake);assert good['decision']=='MATERIAL_CAUSAL_LOCAL_MOTION_SIGNAL'
    assert v.aggregate(fake)['gates']==good['gates']
    bad=__import__('copy').deepcopy(fake)
    for r in bad:r['errors']['R2']['translation_m']=.02
    assert e.aggregate(bad)['decision']=='NO_CAUSAL_LOCAL_MOTION_SIGNAL'
    unsafe=__import__('copy').deepcopy(fake)
    for r in unsafe:
        if r['seq']=='00':r['errors']['R3']['translation_m']=.10
    assert e.aggregate(unsafe)['decision']=='NO_CAUSAL_LOCAL_MOTION_SIGNAL'
    assert v.aggregate(unsafe)['gates']==e.aggregate(unsafe)['gates']
    c.save(B/'preflight.json',dict(utc=c.now(),passed=True,synthetic_pose_cases=len(cases),decision_cases=3,
        max_independent_error_delta=maximum,wall_s=time.monotonic()-t,gt_files_read=False))
    print('LMF1 synthetic evaluator/decision preflight passed',maximum,flush=True)
def freeze():
    assert not (B/'freeze.json').exists() and not (B/'bank').exists()
    assert c.read(B/'preflight.json')['passed'] and c.read(P/'validation.json')['passed'] and c.read(P/'source_binding_validation.json')['passed']
    prior=c.check_freeze(P);c.check_seal(P);cc=c.census();assert cc==prior['census']
    old=c.read(c.DATE/'temporal-identity-audit-01/freeze.json')['files']
    for s in c.SEQS:
        path=c.source(s)/'odom_poses.txt';assert c.sha(path)==old[str(path)]
    files=dependencies();c.save(B/'freeze.json',dict(utc=c.now(),census=cc,files={str(p):c.sha(p) for p in files},
        primary_controls=['KISS','G2','G3'],margins=dict(translation_m=.01,relative=.10,positive_fraction=.60,
        context_translation_m=.005,sequence_mean_translation_regression_m=.01,sequence_paired_rotation_regression_deg=.05)))
    c.status(B,'FROZEN');print('LMF1 frozen',len(files),'identities',len(cc['rows']),'windows',flush=True)
def bank():
    import torch
    t=time.monotonic();f=c.check_freeze(B);assert os.environ['OMP_NUM_THREADS']=='1' and os.environ['OPENBLAS_NUM_THREADS']=='1'
    (B/'bank').mkdir();(B/'INCOMPLETE').write_text('Complete prediction bank and independent validation pending\n');start=c.now();c.status(B,'BANK_RUNNING')
    b,audit=c.make_backend();torch.cuda.reset_peak_memory_stats();od={s:poses(c.source(s)/'odom_poses.txt',n) for s,n in c.SEQS.items()};rows=[]
    for i,r in enumerate(f['census']['rows']):
        arrays,trace=c.inference_row(b,r);arrays['KISS_pose']=np.linalg.inv(od[r['seq']][r['t']-1])@od[r['seq']][r['t']]
        for a in ['R3','R2','G2','G3','support']:valid(arrays[a+'_pose'])
        valid(arrays['KISS_pose'],1e-5)
        assert all(np.isfinite(v).all() for v in arrays.values())
        replay=None
        if r['t']==200:
            with np.load(P/'bank'/f"local_{r['seq']}.npz",allow_pickle=False) as z:
                replay=max(float(np.max(np.abs(arrays[k]-z[k]))) for k in z.files)
            assert replay<=1e-5
        np.savez_compressed(B/'bank'/f"{r['seq']}_{r['t']:06d}.npz",**arrays)
        rows.append(dict(**r,icp_trace=trace,engineering_replay_max_delta=replay));cap(t)
        assert torch.cuda.max_memory_allocated()/2**30<12
        if r['t']==200 or i%10==9:print('LMF1 bank',i+1,'of58',r['seq'],r['t'],round(time.monotonic()-t,2),flush=True)
    assert len(rows)==58;c.check_freeze(B);cap(t)
    c.save(B/'bank.json',dict(started_utc=start,completed_utc=c.now(),rows=rows,checkpoint=audit,gt_files_read=False,
        wall_s=time.monotonic()-t,peak_allocated_gib=torch.cuda.max_memory_allocated()/2**30,
        peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    c.seal(B);c.status(B,'BANK_SEALED');print('complete58 bank sealed',flush=True)
if __name__=='__main__':
    try:{'preflight':preflight,'freeze':freeze,'bank':bank}[sys.argv[1]]()
    except Exception as ex:c.status(B,'STOPPED',error=repr(ex));raise
