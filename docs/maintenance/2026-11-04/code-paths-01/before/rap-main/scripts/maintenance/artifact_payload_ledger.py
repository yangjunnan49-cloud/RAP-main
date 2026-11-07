"""APL0 conservative exclusive-write payload accounting; no archive/neural replay."""
import hashlib,json,resource,signal,sys,time,traceback
from pathlib import Path
import shadow_prefix_storage_codec as s
ROOT=s.ROOT;SOURCE=ROOT/'docs/maintenance/2026-10-13/shadow-evidence-archive-01'
BASE=ROOT/'docs/maintenance/2026-10-14/artifact-payload-ledger-01';SUP=BASE/'supervision';START=None
read,save,sha=s.read,s.save,s.sha
class BudgetRefusal(Exception):pass
class InjectedFailure(Exception):pass
class PayloadLedger:
    def __init__(self,root,cap):
        self.root=Path(root).resolve();self.root.mkdir();self.cap=cap;self.reserved=0;self.events=[]
    def write(self,name,payload,partial=None):
        q=(self.root/name).resolve()
        if self.root not in q.parents:raise ValueError('Outside owned payload root')
        if self.reserved+len(payload)>self.cap:raise BudgetRefusal('Prospective payload cap')
        self.reserved+=len(payload);event=dict(path=str(q.relative_to(self.root)),reservation=len(payload),reserved_after=self.reserved);self.events.append(event)
        q.parent.mkdir(parents=True,exist_ok=True)
        try:
            with q.open('xb') as f:
                if partial is not None:f.write(payload[:partial]);f.flush();raise InjectedFailure('Retained short write')
                f.write(payload)
            event['success']=True
        except BaseException as ex:event.update(success=False,error=type(ex).__name__);raise
def census(root):return sum(q.stat().st_size for q in Path(root).rglob('*') if q.is_file())
def freeze():
    f=read(SOURCE/'freeze.json');files=dict(f['files']);files.update(read(SOURCE/'EXECUTION_BINDING.json')['files']);corpus=[]
    for q in sorted(SOURCE.rglob('*')):
        if q.is_file():h=sha(q);files[str(q)]=h;corpus.append(dict(path=str(q),sha256=h,bytes=q.stat().st_size))
    assert read(SOURCE/'STATUS.json')['LCP0']=='INCOMPLETE_TIME_CAP' and (SOURCE/'INCOMPLETE').exists() and not (SOURCE/'packed/manifest.json').exists()
    paths=[Path(__file__),Path(__file__).with_name('validate_artifact_payload_ledger.py'),Path(__file__).with_name('invoke_mgr_supervised_wsl.ps1'),BASE/'PROTOCOL.md',BASE/'OWNER_SCOPE.md'];snap=BASE/'source_snapshot';snap.mkdir()
    for q in paths:
        files[str(q)]=sha(q)
        if q.suffix in ('.py','.ps1'):(snap/q.name).write_bytes(q.read_bytes())
    for q,h in files.items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'];save(BASE/'freeze.json',dict(files=files,repositories=f['repositories'],source_corpus=corpus,cap_seconds=600,cap_RSS_bytes=2*2**30,cap_GPU_bytes=0,cap_artifact_bytes=16*2**20,filesystem_census_repetitions=3,no_codec_model_GT_or_packing=True));(BASE/'INCOMPLETE').write_text('APL0 exclusive-payload ledger/reconciliation/observer-cost prerequisite pending.\n');print('APL0 frozen',len(files),'identities; corpus',len(corpus),'files',flush=True)
def verify():
    f=read(BASE/'freeze.json')
    for q,h in f['files'].items():assert sha(q)==h,q
    assert s.repositories()==f['repositories'] and (SOURCE/'INCOMPLETE').exists() and not (SOURCE/'packed/manifest.json').exists()
def measure():
    verify();folder=BASE/'fixtures';folder.mkdir();rows=[]
    def record(name,L,expected):
        actual=census(L.root);upper=L.reserved>=actual
        assert upper==expected;rows.append(dict(name=name,cap=L.cap,reserved=L.reserved,actual_bytes=actual,payload_upper_bound=upper,expected_upper_bound=expected,events=L.events))
    L=PayloadLedger(folder/'exact_success',10);L.write('a.bin',b'abcd');L.write('sub/b.bin',b'efg');record('exact_success',L,True)
    L=PayloadLedger(folder/'short_write',10)
    try:L.write('a.bin',b'abcdefgh',partial=3)
    except InjectedFailure:pass
    else:raise AssertionError('short-write fixture did not fail')
    record('short_write',L,True)
    L=PayloadLedger(folder/'duplicate_refusal',10);L.write('a.bin',b'abcd')
    try:L.write('a.bin',b'WXYZ')
    except FileExistsError:pass
    else:raise AssertionError('exclusive-create collision not refused')
    assert (L.root/'a.bin').read_bytes()==b'abcd';record('duplicate_refusal',L,True)
    L=PayloadLedger(folder/'budget_refusal',5);L.write('a.bin',b'abcd')
    try:L.write('b.bin',b'ef')
    except BudgetRefusal:pass
    else:raise AssertionError('budget refusal missing')
    assert not (L.root/'b.bin').exists();record('budget_refusal',L,True)
    L=PayloadLedger(folder/'path_refusal',10)
    try:L.write('../escaped.bin',b'abc')
    except ValueError:pass
    else:raise AssertionError('out-of-root path not refused')
    assert not (folder/'escaped.bin').exists();record('path_refusal',L,True)
    L=PayloadLedger(folder/'two_retained_failures',20)
    for name,n in [('a.bin',2),('sub/b.bin',5)]:
        try:L.write(name,b'abcdefgh',partial=n)
        except InjectedFailure:pass
    L.write('c.bin',b'xy');record('two_retained_failures',L,True)
    L=PayloadLedger(folder/'untracked_external_negative',20);L.write('a.bin',b'abcd');(L.root/'external.bin').write_bytes(b'123456789012');record('untracked_external_negative',L,False)
    # Whole-source census remains the exact reference. Metadata sums are only a frozen replay.
    f=read(BASE/'freeze.json');source_paths={q for q in SOURCE.rglob('*') if q.is_file()};assert source_paths=={Path(x['path']) for x in f['source_corpus']};expected=sum(x['bytes'] for x in f['source_corpus']);runs=[]
    for rep in range(3):
        begin=time.perf_counter();actual=census(SOURCE);census_seconds=time.perf_counter()-begin;assert actual==expected
        begin=time.perf_counter();total=0
        for row in f['source_corpus']:total+=row['bytes']
        ledger_seconds=time.perf_counter()-begin;assert total==actual
        runs.append(dict(rep=rep+1,complete_filesystem_census_bytes=actual,complete_filesystem_census_seconds=census_seconds,known_length_sum_bytes=total,known_length_sum_seconds=ledger_seconds));cap()
    save(BASE/'measurements.json',dict(fixtures=rows,source_corpus_files=len(f['source_corpus']),source_corpus_bytes=expected,repetitions=runs,payload_only_not_whole_dossier_cap_proof=True,external_untracked_counterexample_detected=True,no_total_archive_speedup_claim=True,no_packing_codec_model_or_GT_execution=True));verify();print('APL0 seven accounting fixtures and three complete observer checks pass',flush=True)
def usage():return dict(wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,artifact_bytes=sum(q.stat().st_size for q in BASE.rglob('*') if q.is_file()),imports_included=True,optimizer_calls=0)
def cap():
    u=usage();assert u['peak_RSS_bytes']<=2*2**30 and u['artifact_bytes']<=16*2**20,u
    if (SUP/'host_latest.json').exists():assert read(SUP/'host_latest.json')['headroom_bytes']>=4*2**30
def run(stage):
    global START
    START=time.monotonic();used=sum(read(q)['wall_seconds'] for q in SUP.glob('*/child_exit.json'));assert used<600
    signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('APL0 aggregate child time cap')));signal.alarm(max(1,int(600-used)));ok=False;error=None
    try:
        if stage=='freeze':freeze()
        elif stage=='measure':measure()
        elif stage=='validate':
            import validate_artifact_payload_ledger as v;v.validate()
        else:raise ValueError(stage)
        cap();ok=True
    except BaseException as ex:error=repr(ex);traceback.print_exc();save(BASE/f'FAILURE_{stage}.json',dict(error=error,**usage()))
    finally:signal.alarm(0);save(SUP/stage/'child_exit.json',dict(success=ok,error=error,full_resource_capture=True,**usage()))
    if not ok:sys.exit(1)
if __name__=='__main__':sys.modules['artifact_payload_ledger']=sys.modules[__name__];run(sys.argv[1])
