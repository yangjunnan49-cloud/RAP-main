"""Small serial functional audit; no real data or optional numerical imports."""
import datetime,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.monotonic();results=[]
cases=('normal','without_lease','nonzero','no_result','blocking','future_serial','source_mismatch','preflight_refusal')
for case in cases:
    assert time.monotonic()-start<110
    folder=ROOT/case;folder.mkdir(exist_ok=False)
    for name in ('host.py','winapi.py'):shutil.copyfile(ROOT/name,folder/name)
    shutil.copyfile(ROOT/'worker.py',folder/'controls.py')
    save(folder/'CASE.json',dict(case=case))
    method=dict(origin_utc='2026-11-03T04:52:00+00:00',scope_seconds=900,reserve_seconds=120,headroom_bytes=(2**63 if case=='preflight_refusal' else 12*1024**3),rss_bytes=512*1024**2,dossier_bytes=2*1024**2,stage_seconds=dict(controls=5))
    save(folder/'METHOD.json',method)
    files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file()]
    if case=='source_mismatch':files[0]['sha256']='0'*64
    save(folder/'SOURCE_FREEZE.json',dict(files=files))
    with (folder/'HARNESS_STDOUT.log').open('xb') as stdout,(folder/'HARNESS_STDERR.log').open('xb') as stderr:
        owned=subprocess.Popen([sys.executable,'-I','-B',str(folder/'host.py'),'controls'],stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        save(folder/'OWNED_HOST.json',dict(pid=owned.pid,exact_Popen_handle=True))
        try:code=owned.wait(timeout=9)
        except subprocess.TimeoutExpired:
            owned.kill();owned.wait();raise RuntimeError('synthetic host exceeded bounded cap; inspect any child identity before further work')
    receipt=read(folder/'controls/HOST_EXIT.json') if (folder/'controls/HOST_EXIT.json').exists() else None
    if case=='normal':assert code==0 and receipt['passed'] and receipt['nonce_responses']==1
    elif case in ('source_mismatch','preflight_refusal'):
        assert code!=0 and not (folder/'controls/OWNED_PROCESS.json').exists()
    else:
        assert code!=0 and not receipt['passed'] and receipt['owned_child_reaped']
        if case=='without_lease':assert receipt['exit_code']==0 and receipt['nonce_responses']==0
        if case=='nonzero':assert receipt['exit_code']==7 and not receipt['forced_stop']
        if case=='no_result':assert receipt['exit_code']==0 and receipt['nonce_responses']==1
        if case in ('blocking','future_serial'):assert receipt['forced_stop'] and receipt['elapsed_seconds']<5
    results.append(dict(case=case,expected_outcome_passed=True,host_exit_code=code,child_launched=receipt is not None,child_reaped=receipt['owned_child_reaped'] if receipt else None,child_receipt=receipt))
save(ROOT/'RESULT.json',dict(passed=True,cases=results,elapsed_seconds=time.monotonic()-start,all_owned_hosts_reaped=True,expected_refusals_not_scientific_failures=True))
print('WLC1 all8 functional controls PASS; owned hosts/children reaped')
