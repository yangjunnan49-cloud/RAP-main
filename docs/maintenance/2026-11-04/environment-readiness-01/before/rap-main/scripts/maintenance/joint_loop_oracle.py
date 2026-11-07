"""Separately frozen evaluator-only joint replacement of current accepted poses."""
import importlib.metadata
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
import system_opportunity as helper

MAIN=helper.MAIN; ROOT=helper.ROOT; DATA=helper.DATA; OLD=helper.BASE
BASE=MAIN/'docs/maintenance/2026-10-05/joint-loop-oracle-01'
BANK=BASE/'attempt-01'; EVAL=BASE/'evaluation-01'
SEQS=helper.SEQS
GROUPS={'development':['00','05','06'],'transfer_exposed':['07','09','10']}
read,sha,save=helper.read,helper.sha,helper.save


def now():
    from datetime import datetime,timezone
    return datetime.now(timezone.utc).isoformat()


def state(stage,**kw):
    (BASE/'STATUS.json').write_text(json.dumps(dict(stage=stage,utc=now(),**kw),indent=2)+'\n')


def paths():
    result=[BASE/'PROTOCOL.md',Path(__file__),Path(__file__).with_name('validate_joint_loop_oracle.py'),
      Path(helper.__file__),Path(__file__).with_name('validate_dense_propagation.py'),
      MAIN/'docs/maintenance/2026-10-05/dense-propagation-screen-01/validation.json',
      OLD/'freeze.json',OLD/'bank_seal.json',OLD/'validation.json',OLD/'results.json',
      ROOT/'rap_slam/pose_graph.py',ROOT/'rap_slam/real_dataset.py',ROOT/'rap_slam/trajectory_protocol.py',
      ROOT/'rap_slam/evaluate.py',ROOT/'scripts/eval_paper_metrics.py']
    for s in SEQS:
        result += [helper.source(s)/name for name in ('odom_poses.txt','optimized_poses.txt','keyframes.json','source_frames.json')]
        result += [OLD/'attempt-01'/s/name for name in ('edges.json','baseline.npy')]
        result += [DATA/'poses'/f'{s}.txt',DATA/'sequences'/s/'calib.txt']
    return result


def verify():
    f=read(BASE/'freeze.json')
    assert set(f['files'])=={str(p) for p in paths()}
    for p,h in f['files'].items(): assert sha(p)==h,p
    assert f['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}


def freeze():
    assert not BANK.exists() and not EVAL.exists()
    old=read(OLD/'freeze.json')['files']; seal=read(OLD/'bank_seal.json')['files']
    assert read(OLD/'validation.json')['passed']
    assert read(MAIN/'docs/maintenance/2026-10-05/dense-propagation-screen-01/validation.json')['decision']=='NO_FIXED_INTERPOLATION_SIGNAL'
    for p in paths():
        if str(p) in old: assert sha(p)==old[str(p)],p
        if OLD/'attempt-01' in p.parents: assert sha(p)==seal[str(p.relative_to(OLD/'attempt-01'))],p
    save(BASE/'freeze.json',dict(utc=now(),files={str(p):sha(p) for p in paths()},
         packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')},
         cap_wall_s=1200,cap_peak_rss_gib=2,cap_artifact_bytes=500000000))
    state('FROZEN'); print('frozen',len(paths()),'identities',flush=True)


def cap(t):
    assert time.monotonic()-t < 1200
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20 < 2
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<500000000


def bank():
    verify(); assert not BANK.exists()
    (BASE/'INCOMPLETE').write_text('Joint evaluator-only diagnostic pending validation\n')
    BANK.mkdir(); state('BANK_RUNNING'); t=time.monotonic(); started=now(); rows={}
    for s,n in SEQS.items():
        dest=BANK/s; dest.mkdir(); src=helper.source(s)
        o=helper.poses(src/'odom_poses.txt',n); kf=read(src/'keyframes.json')
        ids=read(src/'source_frames.json')['source_frame_ids']; assert ids==list(range(n))
        edges=read(OLD/'attempt-01'/s/'edges.json')
        assert all(set(e)==set(helper.ALLOW) for e in edges)
        p=helper.replay(o,kf,edges)
        d=float(np.max(np.abs(p-helper.poses(src/'optimized_poses.txt',n))))
        assert d<=1e-5 and np.max(np.abs(p-np.load(OLD/'attempt-01'/s/'baseline.npy')))<=1e-9
        np.save(dest/'P.npy',p); save(dest/'edges.json',edges); save(dest/'frames.json',dict(source_frame_ids=ids,keyframes=kf))
        rows[s]=dict(edges=len(edges),native_saved_max_delta=d)
        cap(t)
    assert sum(r['edges'] for r in rows.values())==58
    save(BANK/'execution.json',dict(started_utc=started,completed_utc=now(),rows=rows,wall_s=time.monotonic()-t,
         peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    verify()
    save(BASE/'bank_seal.json',dict(utc=now(),freeze_sha256=sha(BASE/'freeze.json'),
         files={str(p.relative_to(BANK)):sha(p) for p in sorted(BANK.rglob('*')) if p.is_file()}))
    state('BANK_SEALED'); print('six native graphs and 58 GT-free edges sealed',flush=True)


def verify_bank():
    verify(); seal=read(BASE/'bank_seal.json')
    assert seal['freeze_sha256']==sha(BASE/'freeze.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items(): assert sha(BANK/p)==h,p


def evaluate():
    verify_bank(); EVAL.mkdir(); state('EVALUATING'); gt_read=now(); t=time.monotonic()
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    rows={}
    for s,n in SEQS.items():
        dest=EVAL/s; dest.mkdir(); src=helper.source(s)
        cal=DATA/'sequences'/s/'calib.txt'
        gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{s}.txt'),str(cal),apply_calib=True)); tr=_read_calib_transform(str(cal))
        o=helper.poses(src/'odom_poses.txt',n); kf=read(src/'keyframes.json')
        edges=read(BANK/s/'edges.json'); oracle=[]
        for edge in edges:
            e=dict(edge); e['T_rel']=(np.linalg.inv(gt[e['i']])@gt[e['j']]).tolist(); oracle.append(e)
        save(dest/'oracle_edges.json',oracle)
        j=helper.replay(o,kf,oracle); np.save(dest/'J.npy',j)
        rows[s]={}
        for arm,est in [('odom',o),('P',np.load(BANK/s/'P.npy')),('J',j)]:
            m,seg=helper.metric(gt,tr,est,True); rows[s][arm]=m; save(dest/f'{arm}_segments.json',seg)
        cap(t); print('joint oracle',s,rows[s],flush=True)
    means={g:{a:{k:float(np.mean([rows[s][a][k] for s in seqs])) for k in ('ate','ter','rer')} for a in ('odom','P','J')} for g,seqs in GROUPS.items()}
    opportunity={}
    for g,m in means.items():
        p,j=m['P'],m['J']
        opportunity[g]=dict(ter_path=p['ter']-j['ter']>=.01 and j['ate']<=1.02*p['ate'],
                            ATE_path=j['ate']<=.95*p['ate'] and j['ter']-p['ter']<=.01)
    decision='MATERIAL_CURRENT_EDGE_JOINT_HEADROOM' if any(any(v.values()) for v in opportunity.values()) else 'NO_MATERIAL_COHORT_JOINT_SIGNAL'
    save(BASE/'results.json',dict(utc=now(),gt_read_started_utc=gt_read,bank_seal_sha256=sha(BASE/'bank_seal.json'),
         rows=rows,cohort_means=means,opportunity=opportunity,decision=decision,wall_s=time.monotonic()-t,
         peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20))
    verify_bank(); state('EVALUATED',decision=decision,independent_validation='pending'); print(decision,flush=True)


if __name__=='__main__':
    try: {'freeze':freeze,'bank':bank,'evaluate':evaluate}[sys.argv[1]]()
    except Exception as exc:
        state('STOPPED',failed_stage=sys.argv[1],error=repr(exc)); raise
