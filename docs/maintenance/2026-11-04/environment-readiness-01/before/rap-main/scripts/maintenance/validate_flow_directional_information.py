"""FDI1 independent complete extraction, geometry and evaluator verification."""
import time,resource,math
import numpy as np
import flow_directional_information as h
import flow_directional_response as f
from validate_flow_directional_response import recompute,tangent

def geometric(x,T):
    matrices=[]
    for cloud in x:
        Js=[]
        for u,v,w in cloud:
            Js.append(np.array([[0,w,-v,1,0,0],[-w,0,u,0,1,0],[v,-u,0,0,0,1]]))
        J=np.concatenate(Js,axis=0); matrices.append(np.linalg.solve(J.T@J,np.eye(6)))
    R=T[:3,:3].T; t=-R@T[:3,3]; cross=np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]])
    A=np.block([[R,np.zeros((3,3))],[cross@R,R]])
    return A@matrices[0]@A.T+matrices[1]
def truth(s):
    C=np.eye(4)
    for row in (h.DATA/'sequences'/s/'calib.txt').read_text().splitlines():
        if row.split(':')[0]=='Tr': C[:3,:]=np.fromstring(row.split(':')[1],sep=' ').reshape(3,4)
    out=[]
    for line in (h.DATA/'poses'/f'{s}.txt').read_text().splitlines():
        P=np.eye(4); P[:3,:]=np.fromstring(line,sep=' ').reshape(3,4); out.append(np.linalg.solve(C,P@C))
    return np.array(out)
def strict(T,G):
    cost=float((sum(np.diag(T[:3,:3].T@G[:3,:3]))-1)/2); cost=min(1,max(-1,cost)); angle=math.degrees(math.atan2(math.sqrt(max(0,1-cost*cost)),cost))
    return math.dist(T[:3,3],G[:3,3])<=1 and angle<=5
def capture(e,C):
    N=np.diag(1/f.D)@C@np.diag(1/f.D); norm=sum(float(v*v) for v in e); trace=sum(np.diag(N))
    if norm<1e-12 or trace<1e-16: return None
    result=float(np.dot(e,N@e)/(norm*trace)); assert -1e-8<=result<=1+1e-8; return result
def main():
    B=h.B; t=time.monotonic(); h.verify(); seal=f.read(B/'bank_seal.json'); assert seal['freeze_sha256']==f.sha(B/'freeze.json') and seal['files']=={p.name:f.sha(p) for p in (B/'bank').iterdir()}
    # Explicit geometric identity check: centered symmetric cloud, identity relative pose.
    q=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],float)
    expected=np.diag([.5]*3+[1/3]*3); assert np.max(np.abs(geometric([q,q],np.eye(4))-expected))<1e-12
    shift=np.array([4.,-2.,1.]); G=np.eye(4); G[:3,3]=shift
    assert np.max(np.abs(geometric([q+shift,q],G)-expected))<1e-12
    result=f.read(B/'results.json'); assert result['bank_seal_sha256']==f.sha(B/'bank_seal.json') and result['gt_read_started_utc']>seal['utc']; saved={r['key']:r for r in result['rows']}; gt={s:truth(s) for s in ['00','08']}; rows=[]; max_array=0.; max_metric=0.
    for k,r in enumerate(h.selection()):
        x,ys,T=f.sources(r); expected=recompute(x,ys); expected['C_geometry']=geometric(x,expected['full'][-1])
        with np.load(B/'bank'/f"{r['key']}.npz",allow_pickle=False) as a:
            for name,v in expected.items():
                delta=float(np.max(np.abs(v-a[name]))); assert delta<=1e-7,(r['key'],name,delta); max_array=max(max_array,delta)
            for name in ['C_total','C_control','C_time','C_joint','C_independent','C_geometry']:
                assert np.all(np.isfinite(a[name])) and np.max(np.abs(a[name]-a[name].T))<1e-8*max(1,np.trace(a[name])) and np.linalg.eigvalsh(a[name]).min()>=-1e-8*max(1,np.trace(a[name]))
            assert np.array_equal(T,a['N0_T']) and np.max(np.abs(T-a['full'][-1]))<=2e-4
            for seed in range(4):
                with np.load(f.OLD/r['seq']/r['key']/f'N{seed}.npz',allow_pickle=False) as original: assert np.array_equal(original['T'],a['native_T'][seed])
            GT=np.linalg.solve(gt[r['seq']][r['i']],gt[r['seq']][r['j']]); e=tangent(np.linalg.solve(expected['full'][-1],GT))/f.D
            score={c:capture(e,a[name]) for c,name in dict(J='C_total',I='C_control',G='C_geometry',T='C_time').items()}; score['S']=1/6 if np.linalg.norm(e)>=1e-6 else None
            row=dict(r,positive=bool(math.dist(GT[:3,3],[0,0,0])<=15),native_available=any(strict(A,GT) for A in a['native_T']),N0_strict=strict(T,GT),scores=score); rows.append(row); old=saved[r['key']]
            for field in ['positive','native_available','N0_strict']: assert old[field]==row[field],(r['key'],field)
            for arm,v in score.items():
                if v is None: assert old['scores'][arm] is None
                else:
                    delta=abs(v-old['scores'][arm]); assert delta<1e-7; max_metric=max(max_metric,delta)
            assert np.max(np.abs(e-old['e_normalized']))<1e-6
        if (k+1)%25==0: print('independent',k+1,'/200',flush=True)
    summary={}
    for s in ['00','08']:
        positives=[r for r in rows if r['seq']==s and r['positive']]; assert len(positives)==75
        cohorts=dict(positive=positives,hard=[r for r in positives if not r['native_available']],available=[r for r in positives if r['native_available']],negative=[r for r in rows if r['seq']==s and not r['positive']])
        if s=='08': assert len(cohorts['hard'])==41
        for label,cohort in cohorts.items():
            valid=[r for r in cohort if all(v is not None for v in r['scores'].values())]; metrics={}
            for arm in ['S','G','I','T']:
                differences=sorted(r['scores']['J']-r['scores'][arm] for r in valid); n=len(differences); median=(differences[n//2]+differences[(n-1)//2])/2 if n else None; fraction=sum(v>0 for v in differences)/n if n else None; metrics[arm]=dict(median_paired_gain=median,positive_fraction=fraction)
            summary[s+'_'+label]=dict(n=len(cohort),valid=len(valid),coverage=len(valid)/len(cohort) if cohort else 0,controls=metrics)
    hard=summary['08_hard']; safe=summary['00_positive']; gates=dict(primary_coverage=hard['coverage']>=.9,safety_coverage=safe['coverage']>=.9)
    for arm,margin in [('S',.05),('G',.05),('I',.03),('T',.02)]: gates['hard_'+arm]=hard['controls'][arm]['median_paired_gain'] is not None and hard['controls'][arm]['median_paired_gain']>=margin
    for arm in ['G','I','T']: gates['hard_sign_'+arm]=hard['controls'][arm]['positive_fraction'] is not None and hard['controls'][arm]['positive_fraction']>=.6
    for arm in ['S','G','I','T']: gates['safety_'+arm]=safe['controls'][arm]['median_paired_gain'] is not None and safe['controls'][arm]['median_paired_gain']>=-.03
    for label,m in summary.items():
        old=result['summary'][label]; assert old['n']==m['n'] and old['valid']==m['valid'] and old['coverage']==m['coverage']
        for arm in m['controls']:
            for field,value in m['controls'][arm].items(): assert abs(value-old['controls'][arm][field])<1e-7
    decision='MATERIAL_JOINT_DIRECTIONAL_INFORMATION' if all(gates.values()) else 'NO_MATERIAL_JOINT_DIRECTIONAL_INFORMATION'; assert gates==result['gates'] and decision==result['decision']
    execution=f.read(B/'bank/execution.json'); wall=execution['wall_s']+result['wall_s']+time.monotonic()-t; peak=max(execution['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20); size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()); assert wall<900 and peak<1 and size<20000000; h.verify()
    f.save(B/'validation.json',dict(passed=True,decision=decision,utc=f.now(),pairs=200,primary_hard08=41,positive_per_sequence=75,max_array_delta=max_array,max_score_delta=max_metric,total_wall_s=wall,peak_rss_gib=peak,artifact_bytes_before_report=size,checks=['freeze/original 1000 NPZ identities/stage ordering/seal','all 200 Horn fits/matrix-log full spatial responses','all direct-Jacobian geometric matrices and two analytic lever-arm controls','all native poses/decode tolerances/finite PSD','independent raw GT calibration and strict labels','all error-direction scores/cohorts/aggregates/material/safety gates','resource caps and final identity']))
    h.state('VALIDATED',decision=decision,report='pending'); print('validated',decision,flush=True)
if __name__=='__main__': main()
