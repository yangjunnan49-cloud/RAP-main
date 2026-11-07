"""RLP1 prospective identity, split, sealing and resource bookkeeping."""
import time
PROCESS_START = time.monotonic()
import json
import os
import resource
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c

B = c.MAIN/'docs/maintenance/2026-10-08/readout-pilot-01'
TR = c.MAIN/'docs/maintenance/2026-10-07/joint-token-preflight-01'
DS = c.MAIN/'docs/maintenance/2026-10-07/readout-supervision-design-01'
RV = c.MAIN/'docs/maintenance/2026-10-08/readout-pilot-review-01'
HELPER = c.SLAM/'scripts/measured_point_readout.py'
ENG = B/'engineering-preflight'
WEAK = B/'weak-label-preflight'
FULL = B/'full-bank'
LAB = B/'full-labels'
FIT = B/'fits'
EVAL = B/'evaluation'
sys.path.insert(0, str(c.SLAM/'scripts'))


def rows():
    draft = c.read(DS/'WINDOW_MANIFEST_DRAFT.json')
    audit = c.read(DS/'DATA_AUDIT.json')
    ns = {x['sequence']: x['raw_scans'] for x in audit['kitti']}
    output, seen = [], set()
    for w in draft['windows']:
        s, t, ids = w['sequence'], w['t'], w['ids']
        assert ids == [t-1, t, t-2] and max(ids) < ns[s]
        role = 'fit' if int(s) <= 5 else 'development' if s == '06' else 'exposed_evaluation'
        assert role == w['role']
        ts = np.loadtxt(c.DATA/'sequences'/s/'times.txt')
        for i in ids:
            assert (s, i) not in seen; seen.add((s, i))
        output.append(dict(seq=s, t=t, ids=ids, role=role, seed=c.seed(s, t),
                           paths=[str(c.raw(s, i)) for i in ids], times=ts[ids].tolist()))
    assert len(output) == 204 and len(seen) == 612
    for s, n in ns.items():
        rr = [r for r in output if r['seq'] == s]; m = 24 if int(s) <= 5 else 12
        assert len(rr) == m
        assert [r['t'] for r in rr] == [2+(j*(n-3))//(m-1) for j in range(m)]
    return output


def stem(r):
    return f"{r['seq']}_{r['t']:06d}"


def runtime():
    import torch
    import open3d
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    return dict(python=sys.version, torch=torch.__version__, numpy=np.__version__,
                open3d=open3d.__version__, gpu=torch.cuda.get_device_name(0), threads=torch.get_num_threads())


def files_for(selected, script, validator, gt=False, references=False):
    files = c.frozen_sources() + [HELPER, c.SLAM/'scripts/joint_token_extraction.py', Path(__file__),
        Path(script), Path(validator), B/'PROTOCOL.md', B/'OWNER_AUTHORIZATION.md',
        RV/'REVIEWED_SCOPE.md', DS/'TRAINING_ANNEX_DRAFT.md', DS/'WINDOW_MANIFEST_DRAFT.json']
    files += [Path(p) for r in selected for p in r['paths']]
    for s in sorted({r['seq'] for r in selected}):
        files += [c.DATA/'sequences'/s/'times.txt', c.DATA/'sequences'/s/'calib.txt']
        if gt:
            files += [c.DATA/'poses'/f'{s}.txt']
    if references:
        for s in ('06','07','09','10'):
            files += [c.source(s)/'odom_poses.txt', c.source(s)/'source_frames.json']
    return sorted(set(files))


def freeze(base, selected, script, validator, **extra):
    base.mkdir(exist_ok=False)
    dependency = files_for(selected, script, validator, extra.pop('gt',False), extra.pop('references',False))
    for p in extra.pop('extra_files', []):
        dependency.append(Path(p))
    hashes = {str(p): c.sha(p) for p in sorted(set(dependency))}
    old = c.read(TR/'freeze.json')['files']
    for p in c.frozen_sources():
        if str(p) in old:
            assert hashes[str(p)] == old[str(p)], str(p)
    c.save(base/'freeze.json', dict(utc=c.now(), stage=base.name, files=hashes, rows=selected,
        runtime=runtime(), approved=True, seed_byte_order='big', **extra))
    (base/'INCOMPLETE').write_text('Frozen; execution and independent validation pending.\n')


def check(base):
    return c.check_freeze(base)


def seal(base, manifest='bank.json', folder='bank'):
    c.save(base/'bank_seal.json',dict(utc=c.now(), freeze_sha256=c.sha(base/'freeze.json'),
        manifest=manifest, manifest_sha256=c.sha(base/manifest), folder=folder,
        files={str(p.relative_to(base)):c.sha(p) for p in sorted((base/folder).rglob('*')) if p.is_file()}))


def check_seal(base):
    seal = c.read(base/'bank_seal.json')
    assert c.sha(base/'freeze.json') == seal['freeze_sha256']
    assert c.sha(base/seal['manifest']) == seal['manifest_sha256']
    actual = {str(p.relative_to(base)):c.sha(p) for p in sorted((base/seal['folder']).rglob('*')) if p.is_file()}
    assert actual == seal['files']
    return seal


def validated(base):
    seal = c.read(base/'validation_seal.json')
    assert c.read(base/'validation.json')['passed']
    assert c.sha(base/'validation.json') == seal['validation_sha256']
    assert c.sha(base/'bank_seal.json') == seal['bank_seal_sha256']
    assert c.sha(base/'freeze.json') == seal['freeze_sha256']
    return seal


def pass_validation(base, report):
    check(base); check_seal(base)
    c.save(base/'validation.json',dict(utc=c.now(), passed=True, **report))
    c.save(base/'validation_seal.json',dict(utc=c.now(), validation_sha256=c.sha(base/'validation.json'),
        bank_seal_sha256=c.sha(base/'bank_seal.json'), freeze_sha256=c.sha(base/'freeze.json')))
    (base/'INCOMPLETE').unlink()


def usage():
    import torch
    return dict(wall_s=time.monotonic()-PROCESS_START,
        rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,
        gpu_gib=torch.cuda.max_memory_allocated()/2**30 if torch.cuda.is_initialized() else 0.,
        artifact_bytes=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()))


def cap(stage_limit=3600):
    used=usage()
    previous=sum(x['wall_s'] for x in c.read(B/'RESOURCE_LOG.json')) if (B/'RESOURCE_LOG.json').exists() else 0.
    assert used['wall_s'] <= stage_limit, used
    assert previous+used['wall_s'] <= 3600, (previous, used)
    assert used['rss_gib'] <= 4 and used['gpu_gib'] <= 3 and used['artifact_bytes'] <= 4*2**30, used
    return used


def finish(name, passed=True):
    used=cap()
    old=c.read(B/'RESOURCE_LOG.json') if (B/'RESOURCE_LOG.json').exists() else []
    old.append(dict(stage=name, passed=passed, utc=c.now(), **used))
    (B/'RESOURCE_LOG.json').write_text(json.dumps(old,indent=2)+'\n')
    return used


def fail(name, ex):
    old=c.read(B/'RESOURCE_LOG.json') if (B/'RESOURCE_LOG.json').exists() else []
    old.append(dict(stage=name, passed=False, utc=c.now(), **usage()))
    (B/'RESOURCE_LOG.json').write_text(json.dumps(old,indent=2)+'\n')
    c.save(B/f'FAILURE_{name}.json',dict(utc=c.now(), error=repr(ex), scope='Preserved failure; no automatic rescue', **usage()))
    (B/'STATUS.json').write_text(json.dumps(dict(status='STOPPED',stage=name,error=repr(ex),training=False),indent=2)+'\n')
