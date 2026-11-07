"""GT evaluator, invoked only after complete GT-free bank validation seal."""
import resource,sys,time
import numpy as np
from scipy.spatial.transform import Rotation
import local_motion_common as c
B=c.SCREEN
ARMS=('R3','R2','G2','G3','KISS')
CONTROLS=('KISS','G2','G3')
COUNTS=dict(zip(c.SEQS,[22,13,5,5,7,6]))

def error(truth,pred):
    E=np.linalg.inv(truth)@pred;u,_,vt=np.linalg.svd(E[:3,:3]);R=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
    return dict(translation_m=float(np.linalg.norm(E[:3,3])),rotation_deg=float(np.degrees(Rotation.from_matrix(R).magnitude())))
def stats(rows):
    return {a:{k:dict(mean=float(np.mean([r['errors'][a][k] for r in rows])),median=float(np.median([r['errors'][a][k] for r in rows])),
        p90=float(np.quantile([r['errors'][a][k] for r in rows],.9))) for k in ['translation_m','rotation_deg']} for a in ARMS}
def aggregate(rows):
    assert len(rows)==58 and {s:sum(r['seq']==s for r in rows) for s in c.SEQS}==COUNTS
    primary={};gates={};safety={};per_seq={}
    for a in CONTROLS+('R2',):
        ctrl=np.array([r['errors'][a]['translation_m'] for r in rows]);r3=np.array([r['errors']['R3']['translation_m'] for r in rows]);gain=ctrl-r3
        x=dict(median_paired_gain_m=float(np.median(gain)),median_paired_relative_gain=float(np.median(gain/np.maximum(ctrl,1e-6))),
            positive_count=int((gain>0).sum()),positive_fraction=float((gain>0).mean()))
        x['gate']=bool(x['median_paired_gain_m']>=(.005 if a=='R2' else .01) and x['positive_fraction']>=.60 and
            (a=='R2' or x['median_paired_relative_gain']>=.10))
        primary[a]=x;gates[a]=x['gate']
    for s in c.SEQS:
        rr=[r for r in rows if r['seq']==s];per_seq[s]=dict(n=len(rr),arms=stats(rr));safety[s]={}
        for a in CONTROLS:
            td=float(np.mean([r['errors']['R3']['translation_m']-r['errors'][a]['translation_m'] for r in rr]))
            rd=float(np.median([r['errors']['R3']['rotation_deg']-r['errors'][a]['rotation_deg'] for r in rr]))
            safety[s][a]=dict(mean_translation_regression_m=td,median_paired_rotation_regression_deg=rd,gate=bool(td<=.01 and rd<=.05))
    gates['coverage']=True;gates['sequence_safety']=all(x['gate'] for v in safety.values() for x in v.values())
    macro={a:{k:float(np.mean([per_seq[s]['arms'][a][k]['mean'] for s in c.SEQS])) for k in ['translation_m','rotation_deg']} for a in ARMS}
    return dict(primary=primary,gates=gates,sequence_safety=safety,per_sequence=per_seq,pooled=stats(rows),equal_sequence_mean=macro,
        decision='MATERIAL_CAUSAL_LOCAL_MOTION_SIGNAL' if all(gates.values()) else 'NO_CAUSAL_LOCAL_MOTION_SIGNAL')
def synthetic():
    truth=np.eye(4);truth[:3,:3]=Rotation.from_rotvec([.2,-.1,.4]).as_matrix();truth[:3,3]=[3.,-2.,.7]
    cases=[]
    for angle,trans in [(0.,[0.,0.,0.]),(.3,[.12,-.07,.04]),(2.8,[1.,2.,-.2])]:
        E=np.eye(4);E[:3,:3]=Rotation.from_rotvec([0,0,angle]).as_matrix();E[:3,3]=trans
        cases.append((truth,truth@E,(float(np.linalg.norm(trans)),float(np.degrees(angle)))))
    E=np.eye(4);E[:3,:3]=Rotation.from_rotvec([0,0,.3]).as_matrix()@np.diag([1+1e-7,1-2e-7,1+1e-7]);E[:3,3]=[.1,.2,.3]
    cases.append((truth,truth@E,(float(np.linalg.norm(E[:3,3])),float(np.degrees(.3)))))
    # Calibration and relative direction algebra, using invented poses only.
    tr=np.eye(4);tr[:3,:3]=Rotation.from_rotvec([-.7,.2,.1]).as_matrix();tr[:3,3]=[.3,.8,-.1]
    camera=tr@truth@np.linalg.inv(tr);recovered=np.linalg.inv(tr)@camera@tr
    assert abs(recovered-truth).max()<1e-12
    a=np.eye(4);a[:3,3]=[.5,0,0];b=truth;rel=np.linalg.inv(a)@b
    point=np.array([1.,2.,3.,1.]);assert abs(a@(rel@point)-b@point).max()<1e-12
    assert np.linalg.norm(np.linalg.inv(rel)@point-rel@point)>1
    return cases
def evaluate():
    from rap_slam.real_dataset import load_gt_poses
    t=time.monotonic();f=c.check_freeze(B);seal=c.check_seal(B);vs=c.read(B/'bank_validation_seal.json')
    assert c.read(B/'bank_validation.json')['passed'] and c.sha(B/'bank_validation.json')==vs['validation_sha256']
    assert c.sha(B/'bank_seal.json')==vs['bank_seal_sha256']
    started=c.now();assert f['utc']<c.read(B/'bank.json')['started_utc']<seal['utc']<vs['utc']<started
    c.status(B,'EVALUATING');gt={}
    for s,n in c.SEQS.items():
        gt[s]=load_gt_poses(str(c.DATA/'poses'/f'{s}.txt'),str(c.DATA/'sequences'/s/'calib.txt'),apply_calib=True)
        assert len(gt[s])==n and np.isfinite(gt[s]).all()
    rows=[]
    for r in f['census']['rows']:
        truth=np.linalg.inv(gt[r['seq']][r['t']-1])@gt[r['seq']][r['t']]
        with np.load(B/'bank'/f"{r['seq']}_{r['t']:06d}.npz",allow_pickle=False) as z:
            ee={a:error(truth,z[a+'_pose']) for a in ARMS}
        assert all(np.isfinite(list(v.values())).all() for v in ee.values())
        rows.append(dict(seq=r['seq'],t=r['t'],T_GT=truth.tolist(),errors=ee))
    summary=aggregate(rows);c.check_freeze(B);c.check_seal(B)
    c.save(B/'results.json',dict(gt_read_started_utc=started,completed_utc=c.now(),bank_seal_sha256=c.sha(B/'bank_seal.json'),
        bank_validation_seal_sha256=c.sha(B/'bank_validation_seal.json'),rows=rows,summary=summary,
        wall_s=time.monotonic()-t,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    c.status(B,'EVALUATED',decision=summary['decision']);print(summary['decision'],summary['primary'],flush=True)
if __name__=='__main__':evaluate()
