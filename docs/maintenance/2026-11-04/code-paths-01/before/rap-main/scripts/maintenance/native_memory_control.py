"""NMQ0 scoped API behavior observation, not an old resource-gap repair."""
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
BASE=ROOT/'docs/maintenance/2026-10-14/native-memory-query-01'
SUP=BASE/'supervision'
EXE=Path('/mnt/c/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
NATIVE=Path(__file__).with_name('native_memory_probe.ps1')
read,sha=s.read,s.sha


def size():return sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())


def save(name,value):
    body=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert size()+len(body)<8*2**20
    with (BASE/name).open('xb') as out:out.write(body)


def freeze():
    old=BASE.parent/'windows-pipe-capture-01'
    paths=[BASE/n for n in ('OWNER_SCOPE.md','PROTOCOL.md','SOURCE_NOTES.md')]
    paths += [Path(__file__),EXE,NATIVE,Path(__file__).with_name('native_memory_fixture.ps1'),
        Path(__file__).with_name('validate_native_memory.py'),Path(__file__).with_name('physical_source_role_feasibility.py'),
        Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1')]
    paths += [old/n for n in ('REPORT.md','RESOURCE_SOURCE_NOTES.md','STATUS.json','RESOURCE_AUDIT.json',
                             'INCOMPLETE','AVAILABLE_DELIVERY_SEAL.json')]
    paths += [ROOT/'docs/maintenance'/n for n in s.MARKERS]
    files={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
    snap=BASE/'source_snapshot';snap.mkdir()
    for p in paths:
        if p.suffix in ('.py','.ps1'):
            with (snap/p.name).open('xb') as out:out.write(p.read_bytes())
    save('freeze.json',dict(files=files,repositories=s.repositories(),
        potential_cases=['baseline','early_burst','late_burst'],conditional_baseline_gate=True,
        caps=dict(Windows_seconds=300,Linux_driver_RSS_bytes=128*2**20,
                  Windows_observer_observed_working_set_bytes=256*2**20,
                  native_child_final_peak_bytes_when_available=256*2**20,GPU_bytes=0,
                  whole_dossier_bytes=8*2**20),full_native_observer_peak_proof_claimed=False))
    save('INCOMPLETE',dict(scope='NMQ0',pending='direct OS observation and independent validation'))
    print('NMQ0 frozen',len(files),'identities',flush=True)


def verify():
    f=read(BASE/'freeze.json')
    for p,r in f['files'].items():assert sha(p)==r['sha256'] and Path(p).stat().st_size==r['bytes']
    assert s.repositories()==f['repositories']
    return f


def exercise():
    verify();script=subprocess.check_output(['wslpath','-w',str(NATIVE)],text=True).strip()
    start=time.monotonic()
    p=subprocess.run([str(EXE),'-NoLogo','-NoProfile','-NonInteractive','-File',script],
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    save('interop_exit.json',dict(exit_code=p.returncode,wall_seconds=time.monotonic()-start,
        stdout=p.stdout.decode('utf-8',errors='backslashreplace'),stderr=p.stderr.decode('utf-8',errors='backslashreplace')))
    assert p.returncode==0
    native=read(BASE/'native_queries.json');assert native['observation_execution_complete']
    assert native['observer_to_snapshot']['success']
    assert native['observer_to_snapshot']['peak_working_set']<=256*2**20
    save('observation_seal.json',dict(path='native_queries.json',sha256=sha(BASE/'native_queries.json'),
        interop_exit_sha256=sha(BASE/'interop_exit.json')))
    verify();print('NMQ0 observation complete/native children',native['native_children'],flush=True)


def usage():return dict(wall_seconds=time.monotonic()-START,
    peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
    peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=size(),old_model_archive_or_fit_calls=0)


def run(stage):
    spent=sum(read(p)['wall_seconds'] for p in SUP.glob('*/exit.json'));assert spent<300
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NMQ0 cap')))
    signal.alarm(max(1,int(300-spent)));ok,error=False,None
    try:
        if stage=='freeze':freeze()
        elif stage=='exercise':exercise()
        elif stage=='validate':
            import validate_native_memory as v
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
