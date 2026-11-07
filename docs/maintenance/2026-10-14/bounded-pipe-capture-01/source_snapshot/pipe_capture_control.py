"""BPC0 fixed synthetic pipe controller prerequisite, no science integration."""
import time
START=time.monotonic()
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s
from bounded_pipe_capture import capture

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/bounded-pipe-capture-01'
SUP=BASE/'supervision'
BEJ=ROOT/'docs/maintenance/2026-10-14/bounded-evidence-journal-01'
CASES=('normal','stdout_overflow','stderr_overflow','both_flood','nonzero','timeout','empty','binary')
read,sha=s.read,s.sha


def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<8*2**20
    with (BASE/name).open('xb') as stream:stream.write(body)


def freeze():
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__)]
    paths += [Path(__file__).with_name(n) for n in ('bounded_pipe_capture.py','pipe_capture_fixture.py',
        'validate_pipe_capture.py','bounded_evidence_journal.py','validate_evidence_journal.py',
        'physical_source_role_feasibility.py','invoke_mgr_supervised_wsl.ps1')]
    paths += [BEJ/n for n in ('REPORT.md','STATUS.json','CHECKS.json','DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in s.MARKERS]
    files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=s.repositories(),cases=CASES,
        caps=dict(Windows_seconds=300,parent_RSS_bytes=128*2**20,inner_RSS_bytes=64*2**20,
                  GPU_bytes=0,whole_dossier_bytes=8*2**20)))
    save('INCOMPLETE',dict(scope='BPC0',pending='exercise and independent validation'))
    print('BPC0 frozen',len(files),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for p,r in f['files'].items():assert sha(p)==r['sha256'] and Path(p).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories']
    return f


def exercise():
    verify();fixtures=BASE/'fixtures';fixtures.mkdir();rows=[]
    for name in CASES:
        folder=fixtures/name;folder.mkdir()
        receipt=capture(folder,Path(__file__).with_name('pipe_capture_fixture.py'),name)
        expected=name in ('normal','empty','binary')
        assert receipt['admitted'] is expected
        entries=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(folder.iterdir())]
        assert {r['path'] for r in entries}=={'evidence.rdj','exit.json'}
        assert sum(r['bytes'] for r in entries)<=3072
        rows.append(dict(case=name,receipt=receipt,files=entries))
    save('exercise.json',dict(cases=rows,inner_children=8,all_native_exits_and_RSS=True,
        nested_wall_seconds_not_added_to_parent=True,old_model_archive_or_fit_calls=0))
    save('exercise_seal.json',dict(path='exercise.json',sha256=sha(BASE/'exercise.json')))
    verify();print('BPC0 all8 native children reaped',flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),
    old_archive_or_model_or_fit_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('BPC0 cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='exercise':exercise()
        elif stage=='validate':
            import validate_pipe_capture as v
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
