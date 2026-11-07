"""PRI0 local byte hashes versus author-linked public metadata, no torch."""
import time
START=time.monotonic()
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-15/public-release-identity-01'
SUP=BASE/'supervision'
HANDOFF=ROOT/'docs/maintenance/2026-10-14/continuation-handoff-05'
read,sha=s.read,s.sha
EXPECTED=('mini_spinnet_t.pth','rap_model_10.ckpt','rap_model_12.ckpt')
MARKERS=s.MARKERS+('2026-10-14/physical-comparison-contract-01/INCOMPLETE',
    '2026-10-14/poss-outcome-provenance-01/INCOMPLETE',
    '2026-10-14/windows-pipe-capture-01/INCOMPLETE',
    '2026-10-14/native-memory-query-01/INCOMPLETE')


def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<8*2**20
    with (BASE/name).open('xb') as out:out.write(body)


def local_names():return sorted(p.name for p in (ROOT/'weights').iterdir() if p.is_file())


def freeze():
    assert local_names()==list(EXPECTED)
    paths=[BASE/n for n in ('OWNER_SCOPE.md','PROTOCOL.md','PUBLIC_METADATA_OBSERVATIONS.json')]
    paths += [Path(__file__),Path(__file__).with_name('validate_public_release_identity.py'),
        Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),ROOT/'README.md',
        ROOT/'scripts/download_weights_and_demo_data.sh',
        ROOT/'config/model/flow_model/point_cloud_dit_10.yaml',
        ROOT/'config/model/flow_model/point_cloud_dit_12.yaml']
    paths += [ROOT/'weights'/n for n in EXPECTED]
    paths += [ROOT/'docs/maintenance'/n for n in MARKERS]
    for name in ('DELIVERY_SEAL.json','ACCOUNT_STOP_SEAL.json','FINAL_VERIFICATION_SEAL.json'):
        seal=read(HANDOFF/name)
        for row in seal['files']:
            p=HANDOFF/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
            paths.append(p)
        paths.append(HANDOFF/name)
    files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
    repos=s.repositories();assert repos==read(HANDOFF/'IDENTITY_CHECKS.json')['repositories']
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1','.sh','.yaml'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=repos,local_names=list(EXPECTED),
        caps=dict(Windows_seconds=300,Linux_RSS_bytes=128*2**20,GPU_bytes=0,whole_dossier_bytes=8*2**20),
        public_metadata_previously_visible_not_blind_science=True))
    save('INCOMPLETE',dict(scope='PRI0',pending='byte comparison and independent validation'))
    print('PRI0 frozen',len(files),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    assert local_names()==f['local_names']
    for p,row in f['files'].items():assert sha(p)==row['sha256'] and Path(p).stat().st_size==row['bytes']
    assert s.repositories()==f['repositories']
    return f


def audit():
    verify();metadata=read(BASE/'PUBLIC_METADATA_OBSERVATIONS.json')
    published={row['name']:row for row in metadata['files']}
    assert set(published)==set(EXPECTED) and len(metadata['files'])==3
    rows=[]
    for name in EXPECTED:
        p=ROOT/'weights'/name;digest=sha(p)
        assert digest==published[name]['SHA256']
        rows.append(dict(name=name,path=str(p),local_bytes=p.stat().st_size,SHA256=digest,
            public_blob=published[name]['blob_url'],match=True,remote_exact_size_compared=False))
    assert not (ROOT/'weights/rap_model_10_ns.ckpt').exists()
    result=dict(decision='ALL_THREE_LOCAL_WEIGHTS_MATCH_AUTHOR_LINKED_PUBLIC_SHA256_METADATA',
        files=rows,complete_local_file_denominator=3,total_local_bytes=sum(r['local_bytes'] for r in rows),
        publisher_link_chain_recorded=True,original_download_receipt_authenticated=False,
        strict_tensor_loading_proven_by_this_audit=False,training_membership_authenticated=False,
        native_backward_repair_or_efficacy_established=False,new_model_or_dataset_payload_acquired=False,
        deserialization_model_or_metric_calls=0,all_old_nine_markers_preserved=True)
    save('identity_audit.json',result)
    save('audit_seal.json',dict(path='identity_audit.json',sha256=sha(BASE/'identity_audit.json')))
    verify();print(json.dumps(dict(decision=result['decision'],local_files=3,total_local_bytes=result['total_local_bytes'])),flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    model_deserialization_forward_backward_optimizer_or_metric_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('PRI0 aggregate cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='audit':audit()
        elif stage=='validate':
            import validate_public_release_identity as v
            v.validate()
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<8*2**20
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save('FAILURE_'+stage+'.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save('supervision/'+stage+'/child_exit.json',
            dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
