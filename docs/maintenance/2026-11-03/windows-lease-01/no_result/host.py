"""Own and observe one bounded child without changing any existing environment."""
import datetime, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import winapi
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p, v):
    with Path(p).open('x', encoding='utf-8') as f: json.dump(v, f, indent=2)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
method = read(ROOT/'METHOD.json')
stage = sys.argv[1]
assert stage in method['stage_seconds']
def scope_elapsed():
    return (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(method['origin_utc'])).total_seconds()
assert scope_elapsed() < method['scope_seconds']-method['reserve_seconds']
freeze = read(ROOT/'SOURCE_FREEZE.json')
for entry in freeze['files']:
    assert Path(entry['path']).stat().st_size == entry['bytes'] and sha(entry['path']) == entry['sha256'], entry['path']
prior = {'controls': None, 'packet': 'controls', 'audit': 'packet'}[stage]
if prior:
    assert read(ROOT/prior/'HOST_EXIT.json')['passed']
    for e in read(ROOT/prior/'SEAL.json')['files']:
        p=ROOT/prior/e['path']; assert p.stat().st_size == e['bytes'] and sha(p) == e['sha256']
out = ROOT/stage
out.mkdir(exist_ok=False)
pre = winapi.memory()
save(out/'PREFLIGHT.json', dict(utc=stamp(), **pre))
assert pre['headroom_bytes'] >= method['headroom_bytes'] and pre['query_seconds'] <= 2
env = os.environ.copy()
for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): env[n]='1'
env['CUDA_VISIBLE_DEVICES']=''
start=time.monotonic(); last_request=start; serial=0; peak=0; error=None; forced=False
stdout=(out/'stdout.log').open('xb'); stderr=(out/'stderr.log').open('xb')
observations=(out/'MEMORY_OBSERVATIONS.jsonl').open('x', encoding='utf-8')
p=subprocess.Popen([sys.executable,'-I','-B',str(ROOT/(stage+'.py')),str(out)],stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
handle=winapi.kernel.OpenProcess(0x0410,False,p.pid)
save(out/'OWNED_PROCESS.json',dict(pid=p.pid,parent_pid=os.getpid(),launched_utc=stamp(),python=sys.executable,program=str(ROOT/(stage+'.py')),program_sha256=sha(ROOT/(stage+'.py')),retained_process_handle=True))
try:
    assert handle
    while p.poll() is None:
        now=time.monotonic(); memory=winapi.memory(); memory['utc']=stamp()
        observations.write(json.dumps(memory)+'\n'); observations.flush()
        peak=max(peak,winapi.peak(handle))
        assert memory['headroom_bytes'] >= method['headroom_bytes'] and memory['query_seconds'] <= 2, 'fresh memory gate'
        assert now-start < method['stage_seconds'][stage] and scope_elapsed() < method['scope_seconds']-method['reserve_seconds'], 'wall cap'
        assert peak <= method['rss_bytes'], 'RSS cap'
        requests=list(out.glob(f'{serial+1:06d}_*_request.json'))
        assert len(requests)<=1, 'duplicate next request'
        if requests:
            request=read(requests[0])
            if request['serial']>serial:
                assert request['serial']==serial+1
                serial=request['serial'];last_request=now
                response=out/f'{serial:06d}_{request["nonce"]}_response.json'
                temp=response.with_suffix('.tmp')
                save(temp,dict(**memory,serial=serial,nonce=request['nonce'],passed=True)); os.replace(temp,response)
        assert now-last_request <= 2, 'heartbeat missing'
        assert sum(f.stat().st_size for f in ROOT.rglob('*') if f.is_file()) <= method['dossier_bytes'], 'dossier cap'
        time.sleep(.05)
except BaseException as exc:
    error=type(exc).__name__+': '+str(exc)
    if p.poll() is None: p.kill();forced=True
finally:
    p.wait(timeout=10)
    if handle: winapi.kernel.CloseHandle(handle)
    stdout.close();stderr.close();observations.close()
result=read(out/'RESULT.json') if (out/'RESULT.json').exists() else {}
peak=max(peak,result.get('child_lifetime_peak_bytes',0))
passed=p.returncode==0 and error is None and result.get('passed',False) and serial>=1 and peak<=method['rss_bytes'] and time.monotonic()-start<method['stage_seconds'][stage]
save(out/'HOST_EXIT.json',dict(passed=bool(passed),exit_code=p.returncode,error=error,forced_stop=forced,elapsed_seconds=time.monotonic()-start,scope_elapsed_seconds=scope_elapsed(),peak_RSS_bytes=peak,nonce_responses=serial,owned_child_reaped=True,exit_utc=stamp(),not_OS_containment=True))
if not passed: raise SystemExit('SRA1 '+stage+' FAILED; preserve original outputs')
save(out/'SEAL.json',dict(utc=stamp(),files=[dict(path=f.relative_to(out).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(out.rglob('*')) if f.is_file()]))
print('SRA1 '+stage+' PASS; child reaped',flush=True)
