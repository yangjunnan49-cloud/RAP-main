"""MF0 bounded oracle membership diagnostic. No optimizer or accuracy method."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import hashlib
import importlib.metadata
import json
import resource
import shutil
import signal
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

MAIN = Path('/mnt/e/githouse/RAP-main')
SLAM = Path('/mnt/e/githouse/RAP-SLAM')
BASE = MAIN/'docs/maintenance/2026-10-10/membership-formation-diagnosis-01'
CV2 = MAIN/'docs/maintenance/2026-10-09/rotation-protected-map-pilot-01'
DATA = Path('/mnt/e/githouse/Datasets/data_odometry_velodyne/dataset')
sys.path.insert(0, str(SLAM/'scripts'))
import membership_formation as alg
SEQUENCES = ('00', '05', '06')
WALL, RSS, BYTES = 1800, 2*2**30, 512*2**20


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    assert not path.exists(), f'Never overwrite {path}'
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def verify():
    freeze = read(BASE/'freeze.json')
    for name, digest in freeze['files'].items():
        assert sha(name) == digest, name
    for name, version in freeze['packages'].items():
        assert importlib.metadata.version(name) == version
    return freeze


def check_delivery(base):
    rows = read(base/'DELIVERY_SEAL.json')['files']
    if isinstance(rows, dict):
        rows = [dict(path=p, sha256=h) for p, h in rows.items()]
    for row in rows:
        p = Path(row['path'])
        assert sha(p if p.is_absolute() else base/p) == row['sha256'], str(p)
    return len(rows)


def freeze():
    assert not (BASE/'freeze.json').exists()
    check_delivery(CV2)
    previous = read(CV2/'freeze.json')
    sources = [Path(__file__), Path(__file__).with_name('validate_membership_formation.py'),
               SLAM/'scripts/membership_formation.py', BASE/'algorithm_staging.py', BASE/'PROTOCOL.md', BASE/'OWNER_SCOPE.md']
    assert sha(sources[2]) == sha(sources[3])
    snap = BASE/'source_snapshot'
    snap.mkdir()
    files = list(previous['files'])
    files += [str(CV2/p) for p in ('freeze.json','bank_seal.json','bank_validation.json','results.json','validation.json',
                                  'DELIVERY_SEAL.json','CHECKS.json','REPOSITORY_STATE.json','bank/summary.json')]
    files += [str(CV2/f'bank/{s}.npz') for s in SEQUENCES]
    files += [str(CV2/'objective-diagnosis-01'/p) for p in ('freeze.json','results.json','validation.json','output_seal.json')]
    files += [str(MAIN/x['path']) for x in read(CV2/'CHECKS.json')['model_source_checks']]
    files += [str(MAIN/'weights/rap_model_12.ckpt')]
    files += [str(MAIN/'docs/maintenance/2026-10-10/experiment-review-01'/p) for p in ('REPORT.md','CHECKS.json','DELIVERY_SEAL.json')]
    for i, p in enumerate(sources):
        target = snap/f'{i:02d}-{p.name}'
        shutil.copyfile(p, target)
        files += [str(p), str(target)]
    assert sha(MAIN/'weights/rap_model_12.ckpt') == read(CV2/'CHECKS.json')['opaque_checkpoint_sha256']
    save(BASE/'freeze.json', dict(utc=utc(), files={p:sha(p) for p in dict.fromkeys(files)},
        bindings=previous['bindings'], packages={'numpy':importlib.metadata.version('numpy')},
        owner_instruction='启动新实验', post_outcome=True, oracle_diagnostic_only=True,
        optimizer_calls=0, new_memberships_formed=False, new_reference_payload_parsed=False,
        cpu_wall_cap_s=WALL, rss_cap_bytes=RSS, artifact_cap_bytes=BYTES))
    (BASE/'INCOMPLETE').write_text('MF0 requires complete membership and cost validation\n')
    print('MF0 frozen', len(set(files)), 'identities', flush=True)


def preflight():
    verify()
    rng = np.random.default_rng(20261010)
    poses = np.repeat(np.eye(4)[None], 16, axis=0)
    points = []
    for i in range(16):
        q = rng.uniform(.2, 1.8, (60, 3))
        q[:, 2] = 1.
        points.append(q)
    output, info = alg.form(points, poses, 'fixture', (1, 2))
    assert info['accepted_cross_patches'] == 1
    assert np.array_equal(output['counts'], np.full((1, 16), 60))
    assert all(np.all(output[f'label_{i}'] == 0) for i in range(16))
    shift = poses.copy(); shift[8:, 2, 3] = .04
    mask = np.ones(1, bool)
    g = alg.gradient(output, shift, mask)
    fd = []
    for axis in range(3):
        plus, minus = shift.copy(), shift.copy()
        plus[8:, axis, 3] += 1e-5; minus[8:, axis, 3] -= 1e-5
        fd.append((alg.costs(output, plus, mask)['cost']-alg.costs(output, minus, mask)['cost'])/2e-5)
    delta = float(np.max(np.abs(g-fd)))
    assert delta < 1e-5
    gauge = shift.copy(); gauge[:, :3, 3] += np.array([6., -4., 2.])
    gauge_delta = abs(alg.costs(output, shift, mask)['cost']-alg.costs(output, gauge, mask)['cost'])
    assert gauge_delta < 1e-9
    formation_gauge = poses.copy(); formation_gauge[:, :3, 3] += np.array([6., -4., 2.])
    gauged, _ = alg.form(points, formation_gauge, 'fixture', (1, 2))
    assert np.array_equal(gauged['keys'], output['keys']+np.array([3,-2,1]))
    assert all(np.array_equal(gauged[f'label_{i}'], output[f'label_{i}']) for i in range(16))
    sparse = [p[:2] for p in points]
    _, sparse_info = alg.form(sparse, poses, 'fixture', (1,2))
    assert sparse_info['rejected_support'] == 1
    single = [p if i < 8 else p+np.array([10.,0.,0.]) for i,p in enumerate(points)]
    _, single_info = alg.form(single, poses, 'fixture', (1,2))
    assert single_info['rejected_single_visit'] == 2
    volume = [rng.uniform(.2,1.8,(60,3)) for _ in range(16)]
    _, volume_info = alg.form(volume, poses, 'fixture', (1,2))
    assert volume_info['rejected_plane'] == 1
    save(BASE/'preflight.json', dict(passed=True, gradient_fd_max_delta=delta, fixed_membership_gauge_cost_delta=gauge_delta,
        accepted_fixture=info, support_rejection=sparse_info, plane_rejection=volume_info, single_visit_rejection=single_info,
        integer_voxel_translation_equivariance=True, optimizer_calls=0, real_payload_parsed=False))
    print('MF0 preflight passed', delta, flush=True)


def full_reference(seq, frames):
    camera = np.repeat(np.eye(4)[None], len(frames), axis=0)
    camera[:, :3] = np.loadtxt(DATA/f'poses/{seq}.txt').reshape(-1,3,4)[frames]
    line = next(x for x in (DATA/f'sequences/{seq}/calib.txt').read_text().splitlines() if x.startswith('Tr:'))
    tr = np.eye(4); tr[:3] = np.fromstring(line.split(':',1)[1], sep=' ').reshape(3,4)
    truth = np.linalg.inv(tr)@camera@tr
    ref = np.linalg.inv(truth[0])@truth
    for t in ref:
        u, _, vt = np.linalg.svd(t[:3,:3]); t[:3,:3] = u@np.diag([1.,1.,np.linalg.det(u@vt)])@vt
    ref[0] = np.eye(4)
    return ref


def overlap(left, right, points):
    matrix = np.zeros((len(left['keys']),len(right['keys'])),np.int64)
    counts = []; shared = []
    for i,p in enumerate(points):
        a, b = left[f'label_{i}'],right[f'label_{i}']
        ca, cb = a>=0,b>=0; both = ca&cb; union = ca|cb
        np.add.at(matrix,(a[both],b[both]),1)
        shared.append(both)
        counts.append(dict(total=len(p), B=int(ca.sum()), G=int(cb.sum()), intersection=int(both.sum()),
            B_only=int((ca&~cb).sum()),G_only=int((cb&~ca).sum()),union=int(union.sum())))
    edges = matrix > 0
    return matrix, shared, dict(per_scan=counts, intersection_points=sum(x['intersection'] for x in counts),
        union_points=sum(x['union'] for x in counts), jaccard=(float(sum(x['intersection'] for x in counts)/sum(x['union'] for x in counts)) if sum(x['union'] for x in counts) else None),
        B_split_patches=int(np.sum(edges.sum(1)>1)),G_merge_patches=int(np.sum(edges.sum(0)>1)),
        B_patches_with_no_shared_rows=int(np.sum(edges.sum(1)==0)),G_patches_with_no_shared_rows=int(np.sum(edges.sum(0)==0)),
        same_key_pairs=sum(tuple(k) in {tuple(x) for x in right['keys']} for k in left['keys']))


def bank():
    verify(); assert read(BASE/'preflight.json')['passed']
    root = BASE/'bank'; root.mkdir(); summary={}
    for seq in SEQUENCES:
        with np.load(CV2/f'bank/{seq}.npz',allow_pickle=False) as old:
            points=[old[f'points_{i}'] for i in range(16)]
            endpoint=read(CV2/'bank/summary.json')[seq]['endpoints']
            poses={k:old[k].copy() for k in ('B','F','T')}; poses['G']=full_reference(seq,old['frames'])
            source={}
            metadata={}
            for name in ('B','G'):
                source[name],census=alg.form(points,poses[name],seq,endpoint)
                entry=source[name]
                train,test=alg.describe(entry,~entry['holdout']),alg.describe(entry,entry['holdout'])
                supported=train['patches']>=10 and min(train['per_visit_scans'])>=3 and min(train['per_visit_points'])>=100 and test['patches']>=5
                metadata[name]=dict(census=census,train=train,holdout=test,supported=bool(supported))
                if name=='B':
                    for k in (*alg.FIELDS,'holdout','hash_integers',*[f'label_{i}' for i in range(16)]):
                        assert np.array_equal(entry[k],old[k]),f'CV2 B reproduction {seq}/{k}'
                np.savez(root/f'{seq}-{name}.npz',**entry)
            matrix,shared,coverage=overlap(source['B'],source['G'],points)
            arrays={**poses,'frames':old['frames'],'nodes':old['nodes'],'overlap_counts':matrix}
            arrays.update({f'points_{i}':p for i,p in enumerate(points)})
            arrays.update({f'row_id_{i}':np.arange(len(p),dtype=np.int64) for i,p in enumerate(points)})
            arrays.update({f'intersection_{i}':mask for i,mask in enumerate(shared)})
            for name in ('B','G'):
                entry=source[name]; labels=[entry[f'label_{i}'] for i in range(16)]
                stats,kept=alg.intersection_stats(points,labels,shared,entry['keys'])
                for k in alg.FIELDS:arrays[f'intersection_{name}_{k}']=stats[k]
                arrays[f'intersection_{name}_original_patch_ids']=kept
                metadata[name]['intersection']=dict(nonempty_patches=len(kept), omitted_empty_patches=len(entry['keys'])-len(kept),
                    single_scan_patches=int(np.sum((stats['counts']>0).sum(1)==1)),per_scan_points=stats['counts'].sum(0).tolist())
            np.savez(root/f'{seq}-inputs.npz',**arrays)
            summary[seq]=dict(endpoints=endpoint,memberships=metadata,coverage=coverage)
            print('MF0 formed',seq,{n:m['census'] for n,m in metadata.items()},flush=True)
    save(root/'summary.json',summary)
    save(BASE/'bank_seal.json',dict(utc=utc(),files={p.name:sha(p) for p in root.iterdir()},
        freeze_sha256=sha(BASE/'freeze.json'),costs_not_evaluated=True,optimizer_calls=0))
    verify()


def evaluate():
    verify(); assert read(BASE/'bank_validation.json')['passed']
    summary=read(BASE/'bank/summary.json'); rows={}
    for seq in SEQUENCES:
        with np.load(BASE/f'bank/{seq}-inputs.npz',allow_pickle=False) as inputs:
            rows[seq]={}
            for name in ('B','G'):
                with np.load(BASE/f'bank/{seq}-{name}.npz',allow_pickle=False) as m:
                    entry=dict(costs={},supported=summary[seq]['memberships'][name]['supported'])
                    for part,mask in (('train',~m['holdout']),('holdout',m['holdout']),('all',np.ones(len(m['keys']),bool))):
                        entry['costs'][part]={pose:alg.costs(m,inputs[pose],mask) for pose in ('B','G','F','T')}
                    mask=~m['holdout']; gradient=alg.gradient(m,inputs['B'],mask)
                    displacement=inputs['B'][-1,:3,:3].T@(inputs['G'][-1,:3,3]-inputs['B'][-1,:3,3])
                    length=float(np.linalg.norm(displacement))
                    entry['B_translation_gradient_body']=None if gradient is None else gradient.tolist()
                    entry['reference_endpoint_translation_distance_m']=length
                    entry['B_cost_slope_towards_G_per_m']=None if gradient is None or length<=1e-12 else float(gradient@(displacement/length))
                    b,g=entry['costs']['train']['B'],entry['costs']['train']['G']
                    delta=None if b is None or g is None else g['cost']-b['cost']
                    entry['train_G_minus_B_cost']=delta
                    entry['train_preference']='MISSING' if delta is None else ('B' if delta>1e-10 else ('G' if delta< -1e-10 else 'TIE'))
                    intersection={k:inputs[f'intersection_{name}_{k}'] for k in alg.FIELDS}
                    entry['intersection_costs']={pose:alg.costs(intersection,inputs[pose],np.ones(len(intersection['keys']),bool)) for pose in ('B','G')}
                    rows[seq][name]=entry
            left,right=rows[seq]['B'],rows[seq]['G']
            rows[seq]['formation_pattern']=('INSUFFICIENT_SUPPORT' if not (left['supported'] and right['supported']) else
                'OPPOSING_FORMATION_PREFERENCES' if left['train_preference']=='B' and right['train_preference']=='G' else
                'PERSISTENT_B_PREFERENCE' if left['train_preference']==right['train_preference']=='B' else 'OTHER_OR_MIXED')
            print('MF0 costs',seq,{n:[rows[seq][n]['train_preference'],rows[seq][n]['B_cost_slope_towards_G_per_m']] for n in ('B','G')},rows[seq]['formation_pattern'],flush=True)
    save(BASE/'results.json',dict(utc=utc(),rows=rows,optimizer_calls=0,oracle_diagnostic_only=True,performance_gain_claim=False,
        bank_seal_sha256=sha(BASE/'bank_seal.json'),new_pose_errors_computed=False))
    save(BASE/'result_seal.json',dict(files={'results.json':sha(BASE/'results.json')},validation_pending=True))


def record(stage, callback):
    ledger=read(BASE/'RESOURCE_LOG.json') if (BASE/'RESOURCE_LOG.json').exists() else []
    remaining=WALL-sum(x['wall_s'] for x in ledger)
    assert remaining>0
    def alarm(signum, frame):raise TimeoutError('MF0 combined measured CPU wall ceiling')
    signal.signal(signal.SIGALRM,alarm); signal.setitimer(signal.ITIMER_REAL,remaining)
    start=time.perf_counter(); failure=None
    try:
        callback()
    except BaseException as error:
        failure=repr(error)
        save(BASE/f'FAILURE_{stage}.json',dict(error=failure,traceback=traceback.format_exc(),stage=stage))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        ledger.append(dict(stage=stage,utc=utc(),wall_s=time.perf_counter()-start,peak_rss_bytes=rss,passed=failure is None))
        (BASE/'RESOURCE_LOG.json').write_text(json.dumps(ledger,indent=2)+'\n')
        assert sum(x['wall_s'] for x in ledger)<=WALL and rss<=RSS
        assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=BYTES


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('freeze','preflight','bank','evaluate'))
    stage=parser.parse_args().stage; record(stage,globals()[stage])
