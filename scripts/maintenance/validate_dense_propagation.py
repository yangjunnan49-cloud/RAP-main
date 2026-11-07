"""Independent analytic interpolation and trajectory-metric validation.

Does not import the screen runner or its interpolation/metric/gate functions.
"""
import hashlib
import importlib.metadata
import json
import math
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

MAIN=Path('/mnt/e/githouse/RAP-main')
BASE=MAIN/'docs/maintenance/2026-10-05/dense-propagation-screen-01'
OLD=MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
BANK=BASE/'attempt-01'
SEQS=('00','05','06','07','09','10')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for part in iter(lambda:f.read(1048576),b''): h.update(part)
    return h.hexdigest()


def write(p,obj):
    with Path(p).open('x',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,allow_nan=False); f.write('\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def src(s):
    folder='2026-09-26/e0-frontend-01' if s in SEQS[:3] else '2026-09-27/e0-heldout-01'
    return MAIN/'docs/maintenance'/folder/f'full-{s}-A'


def load(p):
    a=np.loadtxt(p)
    t=np.repeat(np.eye(4)[None],len(a),axis=0)
    t[:,:3]=a.reshape(-1,3,4)
    return t


def skew(w):
    x,y,z=w
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])


def jacobian(w):
    theta=np.linalg.norm(w); k=skew(w)
    if theta < 1e-5:
        a=.5-theta**2/24+theta**4/720
        b=1/6-theta**2/120+theta**4/5040
    else:
        a=(1-np.cos(theta))/theta**2
        b=(theta-np.sin(theta))/theta**3
    return np.eye(3)+a*k+b*(k@k)


def independent_interp(a,b,t):
    if t == 0: return a.copy()
    if t == 1: return b.copy()
    relative=np.linalg.solve(a,b)
    omega=Rotation.from_matrix(relative[:3,:3]).as_rotvec()
    velocity=np.linalg.solve(jacobian(omega),relative[:3,3])
    e=np.eye(4)
    e[:3,:3]=Rotation.from_rotvec(t*omega).as_matrix()
    e[:3,3]=jacobian(t*omega)@(t*velocity)
    return a@e


def reconstruct(o,k,ids):
    c={a:k[a]@np.linalg.inv(o[a]) for a in ids}
    p=np.empty_like(o); s=np.empty_like(o)
    for a,b in zip(ids[:-1],ids[1:]):
        for f in range(a,b):
            p[f]=c[a]@o[f]
            s[f]=independent_interp(c[a],c[b],(f-a)/(b-a))@o[f]
    p[-1]=c[ids[-1]]@o[-1]
    s[ids]=k[ids]
    return p,s


def close(a,b,tol=1e-8):
    assert math.isfinite(float(a)) and math.isfinite(float(b))
    assert abs(float(a)-float(b)) <= tol,(a,b,tol)


def preflight():
    begin=time.monotonic(); record=read(BASE/'preflight.json'); largest=0.
    assert len(record['cases']) == 64
    for case in record['cases']:
        a,b,g=(np.asarray(case[key]) for key in ('ca','cb','gauge'))
        for key,matrix in case['samples'].items():
            value=independent_interp(a,b,float(key))
            largest=max(largest,float(np.max(np.abs(value-np.asarray(matrix)))))
            np.testing.assert_allclose(value,matrix,atol=2e-6,rtol=0)
        np.testing.assert_allclose(independent_interp(g@a,g@b,.37),g@independent_interp(a,b,.37),rtol=0,atol=1e-9)
        np.testing.assert_allclose(independent_interp(a,a,.37),a,rtol=0,atol=1e-12)
    o,k=load(src('10')/'odom_poses.txt'),load(src('10')/'optimized_poses.txt')
    p,s=reconstruct(o,k,read(src('10')/'keyframes.json'))
    assert np.max(np.abs(s-p)) <= 1e-5 and np.max(np.abs(s-o)) <= 1e-5
    for key,a,b in [('S_P',s,p),('S_odom',s,o),('P_odom',p,o)]:
        close(float(np.max(np.abs(a-b))),record['sequence10_identity'][key],2e-6)
    write(BASE/'preflight_validation.json',dict(passed=True,utc=now(),synthetic_pairs=64,
          independent_analytic_max_delta=largest,sequence10_identity=True,wall_s=time.monotonic()-begin))
    print('independent preflight passed; max interpolation delta',largest,flush=True)


def geometry(t):
    assert np.isfinite(t).all() and t.ndim==3 and t.shape[1:]==(4,4)
    r=t[:,:3,:3]
    assert np.max(np.abs(r.transpose(0,2,1)@r-np.eye(3))) <= 1e-5
    assert np.max(np.abs(np.linalg.det(r)-1)) <= 1e-5
    assert np.max(np.abs(t[:,3]-[0,0,0,1])) <= 1e-12


def calibration(s):
    lines=(DATA/'sequences'/s/'calib.txt').read_text().splitlines()
    line=[line for line in lines if line.split(':')[0]=='Tr'][0]
    tr=np.eye(4); tr[:3]=np.asarray([float(v) for v in line.split(':',1)[1].split()]).reshape(3,4)
    return tr


def aligned_rmse(g,e):
    # Match the documented first-pose convention, then fit one proper rigid
    # transform to translations. No scale fit and no evo metric dependency.
    g=np.linalg.inv(g[0])@g; e=np.linalg.inv(e[0])@e
    x=e[:,:3,3]; y=g[:,:3,3]
    xc=x-x.mean(0); yc=y-y.mean(0)
    u,_,vt=np.linalg.svd(xc.T@yc)
    d=np.eye(3); d[-1,-1]=np.linalg.det(vt.T@u.T)
    r=vt.T@d@u.T
    residual=xc@r.T-yc
    return float(np.sqrt(np.mean(np.sum(residual**2,axis=1))))


def segments(g,e,ids):
    g=np.linalg.inv(g[0])@g; e=np.linalg.inv(e[0])@e
    length=np.zeros(len(g))
    for i in range(1,len(g)): length[i]=length[i-1]+np.linalg.norm(g[i,:3,3]-g[i-1,:3,3])
    out=[]
    for first in range(0,len(g),10):
        for nominal in range(100,801,100):
            candidates=np.flatnonzero(length[first+1:]>length[first]+nominal)
            if not len(candidates): continue
            last=first+1+int(candidates[0])
            dg=np.linalg.solve(g[first],g[last]); de=np.linalg.solve(e[first],e[last])
            error=np.linalg.solve(de,dg)
            out.append(dict(first=first,last=last,source_first=int(ids[first]),source_last=int(ids[last]),length_m=nominal,
                 translation_fraction=float(np.linalg.norm(error[:3,3])/nominal),
                 rotation_rad_per_m=float(np.arccos(np.clip((np.trace(error[:3,:3])-1)/2,-1,1))/nominal),
                 speed_mps=float(nominal/(.1*(ids[last]-ids[first]+1)))))
    return out


def validate():
    begin=time.monotonic(); started=now()
    freeze,seal,result=(read(BASE/name) for name in ('freeze.json','bank_seal.json','results.json'))
    for name,h in freeze['files'].items(): assert digest(name)==h,name
    assert freeze['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}
    assert seal['freeze_sha256']==digest(BASE/'freeze.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for name,h in seal['files'].items(): assert digest(BANK/name)==h,name
    assert result['bank_seal_sha256']==digest(BASE/'bank_seal.json')
    assert freeze['utc'] < read(BANK/'execution.json')['started_utc'] < seal['utc'] < result['gt_read_started_utc'] < started
    assert list(result['rows'])==list(SEQS)
    checks=['freeze, packages, bank inventory/hashes and stage ordering']
    old=read(OLD/'results.json'); actual={}; differences={}; independent_segments=0
    for seq in SEQS:
        o,k=load(src(seq)/'odom_poses.txt'),load(src(seq)/'optimized_poses.txt')
        ids=read(src(seq)/'source_frames.json')['source_frame_ids']; kf=read(src(seq)/'keyframes.json')
        frames=read(BANK/seq/'frames.json')
        assert frames==dict(source_frame_ids=ids,keyframes=kf) and ids==list(range(len(o)))
        assert kf==sorted(set(kf)) and kf[0]==0 and kf[-1]==len(o)-1
        p,s=np.load(BANK/seq/'P.npy'),np.load(BANK/seq/'S.npy')
        rp,rs=reconstruct(o,k,kf)
        assert p.shape==s.shape==o.shape
        np.testing.assert_allclose(rp,p,atol=1e-9,rtol=0)
        np.testing.assert_allclose(rs,s,atol=2e-6,rtol=0)
        assert np.array_equal(s[kf],k[kf]) and np.max(np.abs(p-k)) <= 1e-5
        for trajectory in (o,k,p,s): geometry(trajectory)
        differences[seq]=dict(independent_S_max_delta=float(np.max(np.abs(rs-s))),native_saved_max_delta=float(np.max(np.abs(p-k))))
        execution=read(BANK/'execution.json')['rows'][seq]
        close(differences[seq]['native_saved_max_delta'],execution['native_saved_max_delta'])
        # Independently verify every descriptive correction step in the bank.
        diag=read(BANK/seq/'correction_steps.json')
        for arm,est in [('P',p),('S',s)]:
            c=est@np.linalg.inv(o); step=np.linalg.solve(c[:-1],c[1:])
            t=np.linalg.norm(step[:,:3,3],axis=1)
            r=np.degrees(np.arccos(np.clip((np.trace(step[:,:3,:3],axis1=1,axis2=2)-1)/2,-1,1)))
            assert len(diag[arm]['boundaries'])==len(kf)-1
            for b,row in zip(kf[1:],diag[arm]['boundaries']):
                assert row['frame']==b
                close(row['translation_m'],t[b-1],1e-8); close(row['rotation_deg'],r[b-1],1e-5)
            for key,val in [('max_translation_m',t.max()),('median_translation_m',np.median(t)),('max_rotation_deg',r.max()),('median_rotation_deg',np.median(r))]:
                close(diag[arm]['all_adjacent'][key],val,1e-5)
        tr=calibration(seq); ti=np.linalg.inv(tr)
        gt_camera=load(DATA/'poses'/f'{seq}.txt'); gt=ti@gt_camera@tr
        assert gt.shape==o.shape
        actual[seq]={}
        for arm,est in [('odom',o),('P',p),('S',s)]:
            records=segments(tr@gt@ti,tr@est@ti,ids)
            saved=read(BASE/'evaluation-01'/seq/f'{arm}_segments.json')
            assert len(records)==len(saved)>0
            independent_segments+=len(records)
            for a,b in zip(records,saved):
                assert set(a)==set(b)
                for key in ('first','last','source_first','source_last','length_m'): assert a[key]==b[key]
                close(a['translation_fraction'],b['translation_fraction'],1e-9)
                close(a['rotation_rad_per_m'],b['rotation_rad_per_m'],1e-8)
                close(a['speed_mps'],b['speed_mps'])
            m=dict(ate=aligned_rmse(gt,est),ter=float(np.mean([r['translation_fraction'] for r in records])*100),
                   rer=float(np.mean([r['rotation_rad_per_m'] for r in records])*180/np.pi*100),segment_count=len(records))
            actual[seq][arm]=m
            for key in m: close(m[key],result['rows'][seq][arm][key],2e-6)
            if arm in ('odom','P'):
                for key in m: close(m[key],old['rows'][seq]['odom' if arm=='odom' else 'full'][key],1e-5)
        checks.append(seq+': analytic trajectory/anchors/SE3, correction steps, independent ATE/segments, audit reproduction')
        assert time.monotonic()-begin < 1200
    means={g:{arm:{k:float(np.mean([actual[s][arm][k] for s in seqs])) for k in ('ate','ter','rer')} for arm in ('odom','P','S')}
           for g,seqs in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    guards={}
    for group,m in means.items():
        for arm in m:
            for key in m[arm]: close(m[arm][key],result['cohort_means'][group][arm][key],2e-6)
        guards[group+'_ter_gain']=m['S']['ter'] <= m['P']['ter']-.01
        guards[group+'_ATE_guard']=m['S']['ate']/m['P']['ate'] <= 1.02
    for seq,row in actual.items():
        guards[seq+'_ter_guard']=row['S']['ter'] <= row['P']['ter']+.01
        guards[seq+'_ATE_guard']=row['S']['ate']/row['P']['ate'] <= 1.05
    d10=float(np.max(np.abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/P.npy'))))
    guards['10_identity']=d10<=1e-5
    assert np.max(np.abs(np.load(BANK/'10/S.npy')-load(src('10')/'odom_poses.txt'))) <= 1e-5
    decision='ENGINEERING_PROPAGATION_SIGNAL' if all(guards.values()) else 'NO_FIXED_INTERPOLATION_SIGNAL'
    assert guards==result['gate']['tests'] and decision==result['gate']['decision']
    checks.append('independent cohort arithmetic and all seventeen prospective gates')
    total=read(BANK/'execution.json')['wall_s']+result['wall_s']+time.monotonic()-begin
    peak=max(read(BANK/'execution.json')['peak_rss_gib'],result['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    size=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert total<1200 and peak<2 and size<500000000
    for name,h in freeze['files'].items(): assert digest(name)==h
    for name,h in seal['files'].items(): assert digest(BANK/name)==h
    write(BASE/'validation.json',dict(passed=True,utc=now(),check_groups=checks,independent_segment_records=independent_segments,
          decision=decision,trajectory_crosscheck=differences,sequence10_P_S_max_delta=d10,
          wall_s=time.monotonic()-begin,total_screen_wall_s=total,maximum_stage_peak_rss_gib=peak,artifact_bytes_before_report=size))
    (BASE/'STATUS.json').write_text(json.dumps(dict(stage='VALIDATED',utc=now(),decision=decision,report='pending finalization'),indent=2)+'\n')
    print('validated',decision,'segments',independent_segments,'wall',total,flush=True)


if __name__=='__main__':
    {'preflight':preflight,'validate':validate}[sys.argv[1]]()
