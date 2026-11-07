"""Frozen FDI1: all saved F2 native-N0 directions, GT only after seal."""
import sys,time,resource
from pathlib import Path
import numpy as np
import flow_directional_response as f

B=f.MAIN/'docs/maintenance/2026-10-05/flow-directional-information-01'
DATA=f.MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
def selection(): return [dict(seq=s,key=r['key'],i=r['source_i'],j=r['source_j']) for s in ['00','08'] for r in f.read(f.OLD/f'inputs_{s}.json')]
def files():
    p=[B/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_flow_directional_information.py'),Path(f.__file__),Path(f.__file__).with_name('validate_flow_directional_response.py'),f.B/'freeze.json',f.B/'bank_seal.json',f.B/'validation.json',f.OLD/'artifact_hashes.json',f.OLD/'validation.json']
    p += [f.OLD/f'inputs_{s}.json' for s in ['00','08']]
    p += [f.OLD/r['seq']/r['key']/n for r in selection() for n in ['inputs.npz','N0.npz','N1.npz','N2.npz','N3.npz']]
    p += [DATA/'poses'/f'{s}.txt' for s in ['00','08']]+[DATA/'sequences'/s/'calib.txt' for s in ['00','08']]
    return sorted(set(p))
def state(stage,**kw): (B/'STATUS.json').write_text(__import__('json').dumps(dict(stage=stage,utc=f.now(),**kw),indent=2)+'\n')
def verify():
    for p,h in f.read(B/'freeze.json')['files'].items(): assert f.sha(p)==h,p
def freeze():
    assert not (B/'bank').exists() and f.read(f.B/'validation.json')['passed']
    identities={str(p):f.sha(p) for p in files()}; old=f.read(f.OLD/'artifact_hashes.json')
    for p,h in identities.items():
        if p.endswith('.npz') and str(f.OLD) in p: assert h==old[str(Path(p).relative_to(f.OLD))],p
    f.save(B/'freeze.json',dict(utc=f.now(),files=identities,selection=selection(),preflight_exposed_pairs=[r['key'] for r in f.selection()])); state('FROZEN'); print('frozen',len(identities),'identities, 200 pairs',flush=True)
def skew(x): return np.array([[0,-x[2],x[1]],[x[2],0,-x[0]],[-x[1],x[0],0]])
def adj(T):
    A=np.zeros((6,6)); R=T[:3,:3]; A[:3,:3]=R; A[3:,3:]=R; A[3:,:3]=skew(T[:3,3])@R; return A
def conditioning(x,T):
    K=[]
    for p in x:
        n=len(p); H=np.zeros((6,6)); H[:3,:3]=np.eye(3)*np.sum(p*p)-p.T@p; H[:3,3:]=skew(p.sum(0)); H[3:,:3]=-skew(p.sum(0)); H[3:,3:]=n*np.eye(3); K.append(np.linalg.inv(H))
    A=adj(f.inv(T)); return A@K[0]@A.T+K[1]
def bank():
    verify(); t=time.monotonic(); (B/'bank').mkdir(); (B/'INCOMPLETE').write_text('FDI1 independent validation pending\n'); state('BANK_RUNNING'); decode=0.; minimum=2000
    for n,r in enumerate(selection()):
        x,ys,T=f.sources(r); a=f.extract(x,ys); delta=np.max(np.abs(T-a['full'][-1])); assert delta<=2e-4,(r['key'],delta); decode=max(decode,float(delta)); minimum=min(minimum,int(a['remaining'].min())); a['C_geometry']=conditioning(x,a['full'][-1])
        a['native_T']=np.array([np.load(f.OLD/r['seq']/r['key']/f'N{k}.npz',allow_pickle=False)['T'] for k in range(4)]); a['N0_T']=T
        np.savez_compressed(B/'bank'/f"{r['key']}.npz",**a)
        if (n+1)%25==0: print('bank',n+1,'/200',flush=True)
    verify(); f.save(B/'bank/execution.json',dict(wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,max_decode_delta=decode,min_retained=minimum,gt_files_read=False))
    f.save(B/'bank_seal.json',dict(utc=f.now(),freeze_sha256=f.sha(B/'freeze.json'),files={p.name:f.sha(p) for p in (B/'bank').iterdir()})); state('BANK_SEALED')
def gt(s):
    tr=[line for line in (DATA/'sequences'/s/'calib.txt').read_text().splitlines() if line.startswith('Tr:')][0]; C=np.eye(4); C[:3]=np.array([float(v) for v in tr.split(':')[1].split()]).reshape(3,4)
    P=np.tile(np.eye(4),(len(np.loadtxt(DATA/'poses'/f'{s}.txt')),1,1)); P[:,:3]=np.loadtxt(DATA/'poses'/f'{s}.txt').reshape(-1,3,4); return np.linalg.inv(C)[None]@P@C[None]
def strict(T,G):
    t=np.linalg.norm(T[:3,3]-G[:3,3]); angle=np.rad2deg(np.arccos(np.clip((np.trace(T[:3,:3].T@G[:3,:3])-1)/2,-1,1))); return bool(t<=1 and angle<=5)
def score(e,C):
    C=C/f.D[:,None]/f.D[None,:]; norm=float(e@e); trace=float(np.trace(C))
    return float(e@C@e/norm/trace) if norm>=1e-12 and trace>=1e-16 else None
def aggregate(rows):
    output={}
    for s in ['00','08']:
        allpos=[r for r in rows if r['seq']==s and r['positive']]; hard=[r for r in allpos if not r['native_available']]; assert len(allpos)==75 and (s!='08' or len(hard)==41),(s,len(allpos),len(hard))
        for title,cohort in [('positive',allpos),('hard',hard),('available',[r for r in allpos if r['native_available']]),('negative',[r for r in rows if r['seq']==s and not r['positive']])]:
            eligible=[r for r in cohort if all(v is not None for v in r['scores'].values())]; metrics={}
            for ctrl in ['S','G','I','T']:
                d=np.array([r['scores']['J']-r['scores'][ctrl] for r in eligible]); metrics[ctrl]=dict(median_paired_gain=float(np.median(d)) if len(d) else None,positive_fraction=float(np.mean(d>0)) if len(d) else None)
            output[s+'_'+title]=dict(n=len(cohort),valid=len(eligible),coverage=len(eligible)/len(cohort) if cohort else 0,controls=metrics)
    hard=output['08_hard']; safe=output['00_positive']; gates=dict(primary_coverage=hard['coverage']>=.9,safety_coverage=safe['coverage']>=.9)
    for c,m in dict(S=.05,G=.05,I=.03,T=.02).items(): gates['hard_'+c]=hard['controls'][c]['median_paired_gain'] is not None and hard['controls'][c]['median_paired_gain']>=m
    for c in ['G','I','T']: gates['hard_sign_'+c]=hard['controls'][c]['positive_fraction'] is not None and hard['controls'][c]['positive_fraction']>=.6
    for c in ['S','G','I','T']: gates['safety_'+c]=safe['controls'][c]['median_paired_gain'] is not None and safe['controls'][c]['median_paired_gain']>=-.03
    return output,gates,'MATERIAL_JOINT_DIRECTIONAL_INFORMATION' if all(gates.values()) else 'NO_MATERIAL_JOINT_DIRECTIONAL_INFORMATION'
def evaluate():
    verify(); seal=f.read(B/'bank_seal.json'); assert seal['files']=={p.name:f.sha(p) for p in (B/'bank').iterdir()}; start=f.now(); t=time.monotonic(); state('EVALUATING'); truth={s:gt(s) for s in ['00','08']}; rows=[]
    for r in selection():
        G=np.linalg.inv(truth[r['seq']][r['i']])@truth[r['seq']][r['j']]
        with np.load(B/'bank'/f"{r['key']}.npz",allow_pickle=False) as a:
            e=f.log(np.linalg.inv(a['full'][-1])@G)/f.D; scores={c:score(e,a[k]) for c,k in dict(J='C_total',I='C_control',G='C_geometry',T='C_time').items()}; scores['S']=1/6 if float(e@e)>=1e-12 else None
            rows.append(dict(r,positive=bool(np.linalg.norm(G[:3,3])<=15),native_available=any(strict(T,G) for T in a['native_T']),N0_strict=strict(a['N0_T'],G),e_normalized=e.tolist(),scores=scores))
    summary,gates,decision=aggregate(rows); f.save(B/'results.json',dict(gt_read_started_utc=start,completed_utc=f.now(),bank_seal_sha256=f.sha(B/'bank_seal.json'),rows=rows,summary=summary,gates=gates,decision=decision,wall_s=time.monotonic()-t)); state('EVALUATED',decision=decision); print(decision,summary['08_hard'],flush=True)
if __name__=='__main__': {'freeze':freeze,'bank':bank,'evaluate':evaluate}[sys.argv[1]]()
