"""BEJ0 tiny-byte controls; no old corpus or scientific replay."""
import time
START=time.monotonic()
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s
import bounded_evidence_journal as j

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-evidence-journal-01'
SUP=BASE/'supervision'
read,sha=s.read,s.sha
CASES=('normal','stdout_overflow','stderr_overflow','metadata_overflow','global_cap',
       'collision','short_write','corruption','truncated_footer','external_file',
       'invalid_type','after_close','exact_fill','concurrent_open','invalid_channel')


def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<8*2**20
    with (BASE/name).open('xb') as stream:stream.write(body)


def freeze():
    old=ROOT/'docs/maintenance/2026-10-14/artifact-payload-ledger-01'
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),
        Path(__file__).with_name('bounded_evidence_journal.py'),
        Path(__file__).with_name('validate_evidence_journal.py'),
        Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [old/n for n in ('REPORT.md','STATUS.json','CHECKS.json','DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in s.MARKERS]
    files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=s.repositories(),cases=CASES,
        caps=dict(Windows_seconds=300,RSS_bytes=128*2**20,GPU_bytes=0,whole_dossier_bytes=8*2**20)))
    save('INCOMPLETE',dict(scope='BEJ0',pending='exercise and independent validation'))
    print('BEJ0 frozen',len(files),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for p,r in f['files'].items():assert sha(p)==r['sha256'] and Path(p).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories']
    return f


def exercise():
    verify();fixtures=BASE/'fixtures';fixtures.mkdir();rows=[]
    for name in CASES:
        folder=fixtures/name;folder.mkdir()
        limits={1:256,2:16,3:16,4:16}
        cap=256 if name=='exact_fill' else 512
        if name=='global_cap':cap=100
        if name=='collision':
            with (folder/'evidence.rdj').open('xb') as out:out.write(b'PREEXISTING')
            try:j.Journal(folder,cap,limits)
            except FileExistsError:error='FileExistsError'
            else:raise AssertionError('collision overwritten')
            observation=None
        else:
            writer=j.Journal(folder,cap,limits,inject_short=name=='short_write')
            error=None
            try:
                if name=='normal':
                    for channel in range(1,5):writer.append(channel,b'channel'+str(channel).encode())
                elif name in ('stdout_overflow','stderr_overflow','metadata_overflow'):
                    channel={'stdout_overflow':2,'stderr_overflow':3,'metadata_overflow':4}[name]
                    writer.append(channel,b'x'*17)
                elif name=='global_cap':writer.append(1,b'x'*16)
                elif name=='short_write':writer.append(1,b'preserve-full-reservation')
                elif name=='invalid_type':writer.append(1,'not-bytes')
                elif name=='invalid_channel':writer.append(5,b'x')
                elif name=='exact_fill':writer.append(1,b'x'*171)
                elif name=='concurrent_open':
                    writer.append(1,b'first-owner')
                    try:j.Journal(folder,cap,limits)
                    except FileExistsError:error='FileExistsError'
                    else:raise AssertionError('second writer opened')
                else:writer.append(1,b'fixed payload')
            except (BufferError,OSError,ValueError) as ex:error=type(ex).__name__
            writer.close()
            if name=='after_close':
                before=sha(writer.path)
                try:writer.append(1,b'forbidden')
                except RuntimeError:error='RuntimeError'
                else:raise AssertionError('append after close succeeded')
                assert sha(writer.path)==before
            observation=writer.observation()
            if name in ('corruption','truncated_footer'):
                body=bytearray(writer.path.read_bytes())
                if name=='corruption':body[21]^=1
                else:body=body[:-1]
                with (folder/'invalid_copy.rdj').open('xb') as out:out.write(body)
            if name=='external_file':
                with (folder/'out_of_band.bin').open('xb') as out:out.write(b'UNTRACKED'*64)
        entries=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(folder.iterdir())]
        rows.append(dict(case=name,expected_exception=error,observation=observation,files=entries))
    save('exercise.json',dict(cases=rows,all15_cases_retained=True,old_payloads_or_models_used=False))
    save('exercise_seal.json',dict(path='exercise.json',sha256=sha(BASE/'exercise.json')))
    verify();print('BEJ0 all15 cases written',flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    old_archive_or_model_or_fit_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('BEJ0 cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='exercise':exercise()
        elif stage=='validate':
            import validate_evidence_journal as v
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
