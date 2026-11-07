"""WPC0 enclosing supervisor stages for fixed Windows-native fixtures."""
import time
START=time.monotonic()
import json
import resource
import signal
import subprocess
import sys
import traceback
from pathlib import Path
import physical_source_role_feasibility as s

ROOT=s.ROOT
BASE=ROOT/'docs/maintenance/2026-10-14/windows-pipe-capture-01'
SUP=BASE/'supervision'
EXE=Path('/mnt/c/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
NATIVE=ROOT/'scripts/maintenance/windows_pipe_capture_control.ps1'
CASES=('normal','stdout_overflow','stderr_overflow','both_flood','nonzero','timeout','empty','binary')
read,sha=s.read,s.sha


def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<16*2**20
    with (BASE/name).open('xb') as out:out.write(body)


def freeze():
    paths=[BASE/'OWNER_SCOPE.md',BASE/'PROTOCOL.md',Path(__file__),EXE,NATIVE]
    paths += [Path(__file__).with_name(n) for n in ('windows_pipe_fixture.ps1',
        'validate_windows_pipe.py','validate_evidence_journal.py',
        'physical_source_role_feasibility.py','invoke_mgr_supervised_wsl.ps1')]
    for scope in ('bounded-evidence-journal-01','bounded-pipe-capture-01'):
        paths += [BASE.parent/scope/n for n in ('REPORT.md','STATUS.json','CHECKS.json','DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in s.MARKERS]
    files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=s.repositories(),cases=CASES,
        caps=dict(Windows_seconds=600,Linux_driver_RSS_bytes=128*2**20,
            Windows_parent_and_child_peak_working_set_bytes=256*2**20,GPU_bytes=0,
            whole_dossier_bytes=16*2**20)))
    save('INCOMPLETE',dict(scope='WPC0',pending='exercise and validation'))
    print('WPC0 frozen',len(files),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for p,r in f['files'].items():assert sha(p)==r['sha256'] and Path(p).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories']
    return f


def exercise():
    verify()
    windows_script=subprocess.check_output(['wslpath','-w',str(NATIVE)],text=True).strip()
    start=time.monotonic()
    result=subprocess.run([str(EXE),'-NoLogo','-NoProfile','-NonInteractive','-File',windows_script],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    save('interop_exit.json',dict(exit_code=result.returncode,wall_seconds=time.monotonic()-start,
        stdout=result.stdout.decode('utf-8',errors='backslashreplace'),
        stderr=result.stderr.decode('utf-8',errors='backslashreplace')))
    assert result.returncode==0
    native=read(BASE/'native_controller.json')
    assert native['success'] and native['inner_children']==8
    assert 0<native['peak_working_set_bytes']<=256*2**20
    entries=[dict(path=str(p.relative_to(BASE)),sha256=sha(p),bytes=p.stat().st_size)
             for p in sorted((BASE/'fixtures').rglob('*')) if p.is_file()]
    assert len(entries)==16
    save('exercise.json',dict(inner_children=8,files=entries,old_model_archive_or_fit_calls=0))
    save('exercise_seal.json',dict(path='exercise.json',sha256=sha(BASE/'exercise.json'),
        native_controller_sha256=sha(BASE/'native_controller.json'),interop_exit_sha256=sha(BASE/'interop_exit.json')))
    verify();print('WPC0 native parent/8children recorded',flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),old_model_archive_or_fit_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<600
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('WPC0 cap')))
    signal.alarm(max(1,int(600-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='exercise':exercise()
        elif stage=='validate':
            import validate_windows_pipe as v
            v.validate()
        else:raise ValueError(stage)
        u=usage();assert u['peak_RSS_bytes']<=128*2**20 and u['artifact_bytes']<16*2**20
        if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
        ok=True
    except BaseException as ex:
        error=repr(ex);traceback.print_exc();save('FAILURE_'+stage+'.json',dict(error=error,**usage()))
    finally:
        signal.alarm(0);save('supervision/'+stage+'/child_exit.json',
            dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)


if __name__=='__main__':run(sys.argv[1])
