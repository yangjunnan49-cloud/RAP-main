"""Read-only input routing and a distinct bounded validation account."""
import hashlib, importlib, json, os, resource, sys, time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parents[1]/'outputs/overlap_validation_20261021'
OLD=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-21/runtime-overlap-01')
SOURCE=Path('/mnt/e/githouse/RAP-main/scripts/maintenance')
sys.path.insert(0,str(SOURCE))
oldcore=importlib.import_module('overlap_core02')
d=oldcore.d;r=oldcore.r;old=oldcore.old
CAP=1200
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
class Route:
    def __init__(self,kind):self.kind=kind
    def __truediv__(self,name):
        name=str(name)
        if self.kind=='base' and name in {'bank02','bank_seal02.json','schedule.json','PROTOCOL.md','AUDIT_EVALUATION02_FREEZE.json'}:return OLD/name
        if self.kind=='sup' and name=='run02':return OLD/'supervision'/name
        return OUT/('supervision' if self.kind=='sup' else '')/name
BASE=Route('base');SUP=Route('sup')
def used():
    h=read(ROOT/'live_host.json')
    age=time.monotonic()-float(read(ROOT/'local_clock.json')['start_monotonic'])
    elapsed=float(read(ROOT/'local_clock.json')['initial_global_elapsed'])+age
    return max(elapsed,float(h['elapsed']))+60
def process_usage():
    u=resource.getrusage(resource.RUSAGE_SELF)
    return dict(peak_RSS_bytes=u.ru_maxrss*1024,user_CPU_seconds=u.ru_utime,system_CPU_seconds=u.ru_stime)
def cap():
    assert process_usage()['peak_RSS_bytes']<=4*2**30
    amount=sum(p.stat().st_size for root in (ROOT,OUT) for p in root.rglob('*') if p.is_file())
    baseline=read(ROOT/'SOURCE_FREEZE.json')['original_dossier_bytes']
    assert amount<=64*2**20 and baseline+amount+2**20<=256*2**20
    assert used()<CAP
def save(p,x):
    p=Path(p);assert p.is_relative_to(OUT),p
    b=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
    amount=sum(q.stat().st_size for root in (ROOT,OUT) for q in root.rglob('*') if q.is_file())
    assert amount+len(b)<=64*2**20
    assert read(ROOT/'SOURCE_FREEZE.json')['original_dossier_bytes']+amount+len(b)+2**20<=256*2**20
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def verify():
    oldcore.verify()
    manifest=read(ROOT/'SOURCE_FREEZE.json')
    for file,h in manifest['files'].items():assert sha(file)==h,file
    for rel,h in read(OLD/'CLOSE_CHECK_SEAL.json')['files'].items():assert sha(OLD/rel)==h,rel
    cap()
