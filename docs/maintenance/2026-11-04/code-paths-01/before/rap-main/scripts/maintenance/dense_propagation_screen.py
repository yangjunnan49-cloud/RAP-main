"""Fixed offline correction screen with explicitly separated frozen stages."""
import hashlib
import importlib.metadata
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import gtsam
import numpy as np

MAIN = Path('/mnt/e/githouse/RAP-main')
ROOT = MAIN.parent / 'RAP-SLAM'
DATA = MAIN.parent / 'Datasets/data_odometry_velodyne/dataset'
BASE = MAIN / 'docs/maintenance/2026-10-05/dense-propagation-screen-01'
OLD = MAIN / 'docs/maintenance/2026-09-29/system-opportunity-audit-01'
BANK = BASE / 'attempt-01'
EV = BASE / 'evaluation-01'
SEQS = {'00':4541, '05':2761, '06':1101, '07':1101, '09':1591, '10':1201}
GROUPS = {'development':['00','05','06'], 'transfer_exposed':['07','09','10']}
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(p, obj):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def status(stage, **info):
    (BASE / 'STATUS.json').write_text(json.dumps(dict(stage=stage, utc=utc(), **info), indent=2)+'\n')


def source(s):
    folder = '2026-09-26/e0-frontend-01' if s in GROUPS['development'] else '2026-09-27/e0-heldout-01'
    return MAIN / 'docs/maintenance' / folder / f'full-{s}-A'


def poses(p):
    a = np.loadtxt(p).reshape(-1,3,4)
    out = np.tile(np.eye(4),(len(a),1,1))
    out[:,:3] = a
    return out


def se3_check(p):
    assert np.isfinite(p).all() and p.ndim == 3 and p.shape[1:] == (4,4)
    r = p[:,:3,:3]
    orth = float(np.max(np.abs(r.transpose(0,2,1) @ r - np.eye(3))))
    det = float(np.max(np.abs(np.linalg.det(r)-1)))
    assert orth <= 1e-5 and det <= 1e-5
    assert np.max(np.abs(p[:,3] - [0,0,0,1])) <= 1e-12
    return dict(max_orthogonality_error=orth, max_determinant_error=det)


def between(ca, cb, alpha):
    if alpha == 0:
        return ca.copy()
    if alpha == 1:
        return cb.copy()
    delta = gtsam.Pose3.Logmap(gtsam.Pose3(np.linalg.inv(ca) @ cb))
    return ca @ gtsam.Pose3.Expmap(alpha*delta).matrix()


def smooth(odom, kf, opt):
    c = {a: opt[a] @ np.linalg.inv(odom[a]) for a in kf}
    result = np.empty_like(odom)
    for a,b in zip(kf[:-1],kf[1:]):
        twist = gtsam.Pose3.Logmap(gtsam.Pose3(np.linalg.inv(c[a]) @ c[b]))
        for s in range(a,b):
            result[s] = c[a] @ gtsam.Pose3.Expmap((s-a)/(b-a)*twist).matrix() @ odom[s]
    result[kf] = opt[kf]
    return result


def native(odom,kf,opt):
    from rap_slam.pose_graph import propagate_to_full_trajectory
    return np.asarray(propagate_to_full_trajectory(list(odom),kf,{a:opt[a] for a in kf}))


def input_paths(include_preflight=True):
    paths = [BASE/'PROTOCOL.md', Path(__file__), Path(__file__).with_name('validate_dense_propagation.py'),
             OLD/'freeze.json', OLD/'results.json', OLD/'validation.json',
             ROOT/'rap_slam/pose_graph.py', ROOT/'rap_slam/real_dataset.py',
             ROOT/'rap_slam/trajectory_protocol.py', ROOT/'rap_slam/evaluate.py',
             ROOT/'scripts/eval_paper_metrics.py']
    for s in SEQS:
        paths += [source(s)/name for name in ('odom_poses.txt','optimized_poses.txt','keyframes.json','source_frames.json')]
        paths += [DATA/'poses'/f'{s}.txt', DATA/'sequences'/s/'calib.txt']
    if include_preflight:
        paths += [BASE/'preflight.json', BASE/'preflight_validation.json']
    return paths


def prior_identity():
    old = read(OLD/'freeze.json')['files']
    assert read(OLD/'validation.json')['passed']
    for p in input_paths(False):
        if str(p) in old:
            assert sha(p) == old[str(p)], p


def verify_freeze():
    f = read(BASE/'freeze.json')
    assert set(f['files']) == {str(p) for p in input_paths()}
    for p,h in f['files'].items():
        assert sha(p) == h, p
    assert f['packages'] == {p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}
    return f


def preflight():
    prior_identity()
    assert not (BASE/'freeze.json').exists() and not BANK.exists()
    start = time.monotonic()
    rng = np.random.default_rng(20261005)
    cases=[]
    for i in range(64):
        wa,wb = rng.normal(size=6),rng.normal(size=6)
        wa[:3] *= .35
        wb[:3] *= .35
        if i == 0:
            wa *= 0; wb *= 0
        if i == 1:
            wa *= 0; wb[:3] = [np.pi-1e-5,0,0]
        ca,cb = (gtsam.Pose3.Expmap(w).matrix() for w in (wa,wb))
        gauge = gtsam.Pose3.Expmap(rng.normal(size=6)*.2).matrix()
        samples = {str(a):between(ca,cb,a).tolist() for a in (0.,1e-8,.25,.5,.75,1.-1e-8,1.)}
        assert np.max(np.abs(between(ca,cb,0)-ca)) == 0
        assert np.max(np.abs(between(ca,cb,1)-cb)) == 0
        assert np.max(np.abs(between(ca,cb,1e-8)-ca)) < 1e-6
        assert np.max(np.abs(between(ca,cb,1-1e-8)-cb)) < 1e-6
        assert np.max(np.abs(between(ca,ca,.37)-ca)) < 1e-12
        covariance = between(gauge@ca,gauge@cb,.37)
        assert np.max(np.abs(covariance-gauge@between(ca,cb,.37))) < 1e-9
        se3_check(np.asarray(list(samples.values())))
        cases.append(dict(ca=ca.tolist(),cb=cb.tolist(),gauge=gauge.tolist(),samples=samples))
    src=source('10')
    o,k,kf=poses(src/'odom_poses.txt'),poses(src/'optimized_poses.txt'),read(src/'keyframes.json')
    p,s=native(o,kf,k),smooth(o,kf,k)
    d={name:float(np.max(np.abs(x-y))) for name,x,y in [('S_P',s,p),('S_odom',s,o),('P_odom',p,o)]}
    assert max(d.values()) <= 1e-5
    save(BASE/'preflight.json',dict(utc=utc(),cases=cases,sequence10_identity=d,wall_s=time.monotonic()-start))
    status('PREFLIGHT_PENDING_INDEPENDENT_CHECK')
    print('synthetic and GT-free sequence10 preflight complete',flush=True)


def freeze():
    prior_identity()
    assert not BANK.exists() and read(BASE/'preflight_validation.json')['passed']
    save(BASE/'freeze.json',dict(utc=utc(),files={str(p):sha(p) for p in input_paths()},
         packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')},
         python=sys.version,cohort=SEQS,cap_wall_s=1200,cap_peak_rss_gib=2,cap_artifact_bytes=500000000))
    status('FROZEN',freeze_sha256=sha(BASE/'freeze.json'))
    print('frozen',len(input_paths()),'identities',flush=True)


def cap(start):
    assert time.monotonic()-start < 1200
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20 < 2
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file()) < 500000000


def diagnostics(o,p,s,kf):
    result={}
    for label,trajectory in [('P',p),('S',s)]:
        c=trajectory @ np.linalg.inv(o)
        step=np.linalg.inv(c[:-1]) @ c[1:]
        trans=np.linalg.norm(step[:,:3,3],axis=1)
        rot=np.degrees(np.arccos(np.clip((np.trace(step[:,:3,:3],axis1=1,axis2=2)-1)/2,-1,1)))
        result[label]=dict(all_adjacent=dict(max_translation_m=float(trans.max()),median_translation_m=float(np.median(trans)),
              max_rotation_deg=float(rot.max()),median_rotation_deg=float(np.median(rot))),
              boundaries=[dict(frame=int(b),translation_m=float(trans[b-1]),rotation_deg=float(rot[b-1])) for b in kf[1:]])
    return result


def bank():
    verify_freeze()
    (BASE/'INCOMPLETE').write_text('Frozen propagation screen pending evaluation and independent validation\n')
    BANK.mkdir()
    status('BANK_RUNNING')
    begin=time.monotonic()
    started=utc()
    info={}
    for seq,n in SEQS.items():
        src=source(seq); dest=BANK/seq; dest.mkdir()
        o,k=poses(src/'odom_poses.txt'),poses(src/'optimized_poses.txt')
        kf=read(src/'keyframes.json'); ids=read(src/'source_frames.json')['source_frame_ids']
        assert o.shape == k.shape == (n,4,4) and ids == list(range(n))
        assert kf == sorted(set(kf)) and kf[0] == 0 and kf[-1] == n-1
        se3_check(o); se3_check(k)
        p,s=native(o,kf,k),smooth(o,kf,k)
        delta=float(np.max(np.abs(p-k)))
        assert delta <= 1e-5 and np.array_equal(s[kf],k[kf])
        identity=float(np.max(np.abs(s-p)))
        if seq == '10': assert identity <= 1e-5 and np.max(np.abs(s-o)) <= 1e-5
        np.save(dest/'P.npy',p); np.save(dest/'S.npy',s)
        save(dest/'frames.json',dict(source_frame_ids=ids,keyframes=kf))
        save(dest/'correction_steps.json',diagnostics(o,p,s,kf))
        info[seq]=dict(native_saved_max_delta=delta,S_P_max_delta=identity,anchors_exact=True,
                       P_se3=se3_check(p),S_se3=se3_check(s))
        cap(begin)
        print('bank',seq,'native delta',delta,flush=True)
    save(BANK/'execution.json',dict(started_utc=started,completed_utc=utc(),wall_s=time.monotonic()-begin,
         peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,rows=info))
    verify_freeze()
    save(BASE/'bank_seal.json',dict(utc=utc(),freeze_sha256=sha(BASE/'freeze.json'),
         files={str(p.relative_to(BANK)):sha(p) for p in sorted(BANK.rglob('*')) if p.is_file()}))
    status('BANK_SEALED',bank_seal_sha256=sha(BASE/'bank_seal.json'))
    print('complete GT-free bank sealed',flush=True)


def verify_bank():
    verify_freeze()
    seal=read(BASE/'bank_seal.json')
    assert seal['freeze_sha256'] == sha(BASE/'freeze.json')
    assert set(seal['files']) == {str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items(): assert sha(BANK/p) == h,p


def gate(rows,means):
    tests={}
    for group,m in means.items():
        tests[group+'_ter_gain']=m['P']['ter']-m['S']['ter'] >= .01
        tests[group+'_ATE_guard']=m['S']['ate'] <= 1.02*m['P']['ate']
    for s,r in rows.items():
        tests[s+'_ter_guard']=r['S']['ter']-r['P']['ter'] <= .01
        tests[s+'_ATE_guard']=r['S']['ate'] <= 1.05*r['P']['ate']
    tests['10_identity']=float(np.max(np.abs(np.load(BANK/'10/S.npy')-np.load(BANK/'10/P.npy')))) <= 1e-5
    return dict(tests=tests,decision='ENGINEERING_PROPAGATION_SIGNAL' if all(tests.values()) else 'NO_FIXED_INTERPOLATION_SIGNAL')


def evaluate():
    verify_bank()
    EV.mkdir()
    status('EVALUATING',bank_seal_sha256=sha(BASE/'bank_seal.json'))
    # Numerical GT access begins only after the complete bank seal has verified.
    gt_read_utc=utc()
    from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
    import eval_paper_metrics as epm
    begin=time.monotonic(); rows={}
    old=read(OLD/'results.json')
    for seq,n in SEQS.items():
        dest=EV/seq; dest.mkdir()
        calib=DATA/'sequences'/seq/'calib.txt'
        gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{seq}.txt'),str(calib),apply_calib=True))
        tr=_read_calib_transform(str(calib)); ti=np.linalg.inv(tr)
        ids=read(BANK/seq/'frames.json')['source_frame_ids']
        assert gt.shape == (n,4,4)
        rows[seq]={}
        for arm,est in [('odom',poses(source(seq)/'odom_poses.txt')),('P',np.load(BANK/seq/'P.npy')),('S',np.load(BANK/seq/'S.npy'))]:
            lidar=epm.evaluate_pair(list(gt),list(est),ids)
            camera=epm.evaluate_pair(list(tr@gt@ti),list(tr@est@ti),ids)
            rows[seq][arm]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],segment_count=camera['kitti_segments'])
            save(dest/f'{arm}_segments.json',camera['kitti_segment_records'])
            if arm in ('odom','P'):
                prev=old['rows'][seq]['odom' if arm=='odom' else 'full']
                for key in ('ate','ter','rer','segment_count'): assert abs(rows[seq][arm][key]-prev[key]) <= 1e-5,(seq,arm,key)
        cap(begin)
        print('evaluated',seq,rows[seq],flush=True)
    means={g:{a:{key:float(np.mean([rows[s][a][key] for s in seqs])) for key in ('ate','ter','rer')} for a in ('odom','P','S')} for g,seqs in GROUPS.items()}
    result=dict(utc=utc(),gt_read_started_utc=gt_read_utc,bank_seal_sha256=sha(BASE/'bank_seal.json'),rows=rows,cohort_means=means,
                gate=gate(rows,means),wall_s=time.monotonic()-begin,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    save(BASE/'results.json',result)
    verify_bank()
    status('EVALUATED',decision=result['gate']['decision'],independent_validation='pending')
    print(result['gate'],flush=True)


if __name__ == '__main__':
    stage=sys.argv[1]
    try:
        {'preflight':preflight,'freeze':freeze,'bank':bank,'evaluate':evaluate}[stage]()
    except Exception as exc:
        status('STOPPED',failed_stage=stage,error=repr(exc))
        raise
