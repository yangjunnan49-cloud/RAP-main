"""Output-routed supervised NOC4 retry; frozen original numerical routines unchanged."""
import json,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
import torch
import native_conditioned_comparison as r
c=r.c
ORIGINAL=r.BASE
BASE=ORIGINAL/'attempt-02'
RECOVERY=c.MAIN/'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
r.BASE=BASE;r.old.BASE=BASE
SUPERVISION=c.MAIN/'docs/maintenance/2026-10-10/native-conditioned-comparison-supervision-02'
STAGE=sys.argv[1];LOG=SUPERVISION/STAGE
START=time.monotonic();r.old.START=START
old_cap=r.cap
old_deliveries=r.old_deliveries


def deliveries():
    counts=old_deliveries();rows=c.read(ORIGINAL/'DELIVERY_SEAL.json')['files'];assert len(rows)==60
    for row in rows: assert c.sha(ORIGINAL/row['path'])==row['sha256'],row['path']
    return counts+[60]


def record(stage):
    u=r.usage()
    with (LOG/'child_progress.jsonl').open('a') as f: f.write(json.dumps(dict(stage=stage,**u))+'\n');f.flush()
    p=LOG.parent/'host_latest.json'
    if p.exists(): assert c.read(p)['headroom_bytes']>=4*2**30,'Windows commit guard'


def cap():
    old_cap();p=LOG.parent/'host_latest.json'
    if p.exists(): assert c.read(p)['headroom_bytes']>=4*2**30,'Windows commit guard'
    assert r.usage()['artifact_bytes']+sum(p.stat().st_size for p in SUPERVISION.rglob('*') if p.is_file())<=512*2**20


r.cap=r.old.cap=cap
r.old_deliveries=r.old.old_deliveries=deliveries


def runtime_verified():
    f=c.read(RECOVERY/'validation.json');assert f['passed'] and f['full_resource_capture']
    for row in f['files']:
        assert c.sha(RECOVERY/row['path'])==row['sha256'],row['path']


def freeze():
    runtime_verified();deliveries();original=c.read(ORIGINAL/'freeze.json')
    files=dict(original['files'])
    for p,h in files.items(): assert c.sha(p)==h,p
    repos=r.n.noc.git_state();assert repos==original['repositories']
    sources=[Path(__file__),Path(__file__).with_name('invoke_supervised_wsl_current.ps1')]
    extra=sources+[BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md',ORIGINAL/'DELIVERY_SEAL.json',ORIGINAL/'freeze.json',
        ORIGINAL/'noise_seal.json',ORIGINAL/'mathematical_preflight.json',ORIGINAL/'bank/synthetic_fixture.npz',RECOVERY/'validation.json']
    extra+=[ORIGINAL/'bank/noise'/f"{x['name']}.npz" for x in r.noise_rows()]
    for p in extra: files[str(p)]=c.sha(p)
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in sources+[Path(__file__).with_name(n) for n in ('native_conditioned_comparison.py',
        'validate_native_conditioned_comparison.py','close_native_conditioned_comparison.py')]:
        (snap/p.name).write_bytes(p.read_bytes())
    f=dict(original,utc=c.now(),files=files,execution_attempt='02',original_freeze_sha256=c.sha(ORIGINAL/'freeze.json'),
        original_delivery_sha256=c.sha(ORIGINAL/'DELIVERY_SEAL.json'),no_scientific_setting_change=True,
        new_attempt_resources=True,legacy_resource_gaps_not_amended=True)
    c.save(BASE/'freeze.json',f);(BASE/'INCOMPLETE').write_text('New output-routed NOC4 attempt; numerical/performance gates pending.\n')
    c.status(BASE,'frozen',status='AUTHORIZED_FROZEN_ATTEMPT02');r.finish('freeze')
    print('NOC4 attempt02 frozen',len(files),flush=True)


def prepare():
    r.check();runtime_verified();bank=BASE/'bank';(bank/'noise').mkdir(parents=True)
    for rel in ('bank/synthetic_fixture.npz','mathematical_preflight.json','noise_seal.json'):
        (BASE/rel).write_bytes((ORIGINAL/rel).read_bytes())
    for row in r.noise_rows():
        rel=f"bank/noise/{row['name']}.npz";(BASE/rel).write_bytes((ORIGINAL/rel).read_bytes())
        assert c.sha(BASE/rel)==c.sha(ORIGINAL/rel)
    r.noise_check();r.finish('reused_sealed_inputs');print('Original24 noises and fixture reused byte-exactly',flush=True)


def close():
    r.check();runtime_verified();deliveries()
    receipt_stages=['freeze','prepare','preflight','validate_preflight']
    if c.read(BASE/'preflight/probes.json')['passed']:
        receipt_stages+=['fit_synthetic','predict_synthetic','evaluate_synthetic','validate_synthetic']
    receipts=[]
    for stage in receipt_stages:
        child=c.read(SUPERVISION/stage/'child_exit.json');host=c.read(SUPERVISION/stage/'exit.json')
        assert child['success'] and child['full_resource_capture'] and host['exit_code']==0
        assert child['peak_RSS_bytes']<=4*2**30
        assert max(child['peak_GPU_allocated_bytes'],child['peak_GPU_reserved_bytes'])<=3*2**30
        receipts.append(dict(stage=stage,child=child,host=host))
    assert sum(x['child']['wall_seconds'] for x in receipts)<1800
    c.save(BASE/'SUPERVISED_RESOURCE_AUDIT.json',dict(passed=True,all_attempts_full_resource_capture=True,
        receipts=receipts,payload_wall_seconds=sum(x['child']['wall_seconds'] for x in receipts),
        external_process_wall_seconds=sum(x['host']['wall_seconds'] for x in receipts),
        max_RSS_bytes=max(x['child']['peak_RSS_bytes'] for x in receipts),
        max_GPU_allocated_bytes=max(x['child']['peak_GPU_allocated_bytes'] for x in receipts),
        max_GPU_reserved_bytes=max(x['child']['peak_GPU_reserved_bytes'] for x in receipts),
        legacy_resource_gaps_not_amended=True))
    (BASE/'ATTEMPT_NOTE.md').write_text('# Resumed supervised execution\n\nOwner explicitly requested runtime repair and project continuation. Original NOC4 stopped60-entry dossier and its INCOMPLETE/resource gaps remain unchanged. Windows Event2004/host commit exhaustion evidence and supervised recovery verification are retained separately. This new attempt reuses exact original scientific sources/settings/24 noises/fixture and fresh output routing. See SUPERVISED_RESOURCE_AUDIT for full child peaks and Windows exit/wall/headroom observations. No recorded attempt02 failure or numerical repair; no real/nearby/trajectory or scientific gate changes.\n')
    import close_native_conditioned_comparison as closer
    closer.close()


def run():
    record('stage_enter')
    assert torch.get_num_threads()==1
    if STAGE=='freeze': freeze()
    elif STAGE=='prepare': prepare()
    elif STAGE=='preflight': r.preflight()
    elif STAGE=='fit_synthetic': r.fit('synthetic')
    elif STAGE=='predict_synthetic': r.old.predict('synthetic')
    elif STAGE=='evaluate_synthetic': r.old.evaluate('synthetic')
    elif STAGE.startswith('validate_'):
        import validate_native_conditioned_comparison as v
        {'validate_preflight':v.preflight,'validate_synthetic':v.evaluate}[STAGE]()
    elif STAGE=='close': close()
    else: raise ValueError(STAGE)
    cap();record('stage_complete')


signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('attempt02 remaining payload cap')))
signal.alarm(max(1,int(1800-sum(x['wall_seconds'] for x in r.ledger()))))
try:
    run();success=True;error=None
except BaseException as ex:
    traceback.print_exc();success=False;error=repr(ex)
    r.finish(STAGE,False,error=error)
    c.save(BASE/f'FAILURE_{STAGE}.json',dict(error=error,**r.usage()))
    c.status(BASE,'failure',status='INCOMPLETE',error=error)
finally:
    signal.alarm(0)
    c.save(LOG/'child_exit.json',dict(success=success,error=error,full_resource_capture=True,**r.usage()))
if not success: sys.exit(1)
