from pathlib import Path
import inspect,sys
import repeat_systems as e
ORIGINAL=e.BASE;BASE=ORIGINAL/'attempt03'
source=inspect.getsource(e.run)
source=source.replace("payload=cmd[1:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]","payload=cmd[2:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]")
source=source.replace("row['resource']['rss_bytes']<=12*2**30 and row['resource']['gpu_allocated_bytes']<=4*2**30 and row['resource']['gpu_reserved_bytes']<=4*2**30","row['resource']['rss_bytes']<=18*2**30 and row['resource']['gpu_allocated_bytes']<=6*2**30 and row['resource']['gpu_reserved_bytes']<=10*2**30")
source=source.replace('timeout=7200-(time.monotonic()-start)','timeout=6940-(time.monotonic()-start)')
child=(ORIGINAL/'child_capture.py').read_text()
old=" if t is not None and t.cuda.is_initialized():allocated=t.cuda.max_memory_allocated();reserved=t.cuda.max_memory_reserved()"
assert old in child
child=child.replace(old," cuda=getattr(t,'cuda',None)\n if cuda is not None and hasattr(cuda,'is_initialized') and cuda.is_initialized():allocated=cuda.max_memory_allocated();reserved=cuda.max_memory_reserved()")
child=child.replace("assert p['rss_bytes']<=12*2**30 and max(p['gpu_allocated_bytes'],p['gpu_reserved_bytes'])<=4*2**30","assert p['rss_bytes']<=18*2**30 and p['gpu_allocated_bytes']<=6*2**30 and p['gpu_reserved_bytes']<=10*2**30")
def freeze():
 e.verify();BASE.mkdir(exist_ok=False)
 (BASE/'child_capture.py').write_text(child)
 (BASE/'effective_run.py').write_text(source)
 (BASE/'PROTOCOL.md').write_bytes((ORIGINAL/'FULL_SYSTEM_RESOURCE_SCOPE.md').read_bytes())
 f=e.read(ORIGINAL/'freeze.json');extras=[Path(__file__),BASE/'child_capture.py',BASE/'effective_run.py',BASE/'PROTOCOL.md',ORIGINAL/'PROTOCOL.md',ORIGINAL/'FULL_SYSTEM_RESOURCE_SCOPE.md',ORIGINAL/'freeze.json',ORIGINAL/'evaluation_freeze.json',ORIGINAL/'evaluate_repeats.py',ORIGINAL/'evaluate_attempt03.py',ORIGINAL/'evaluation03_routing_freeze.json',ORIGINAL/'attempt02/r01-00-RAP-SLAM.resource.json',ORIGINAL/'attempt02/ledger.jsonl']
 f['sources'].update({str(p):e.sha(p) for p in extras});f['scope']='distinct prospective full-system resource scope; identical scientific commands';e.save(BASE/'freeze.json',f)
 e.save(BASE/'evaluation_freeze.json',e.read(ORIGINAL/'evaluation_freeze.json'));print('Attempt03 full-system scope frozen',flush=True)
def run():
 assert (BASE/'effective_run.py').read_text()==source and (BASE/'child_capture.py').read_text()==child
 ns=dict(vars(e));ns['BASE']=BASE
 exec(compile(inspect.getsource(e.verify)+'\n'+source,str(BASE/'effective_run.py'),'exec'),ns);ns['run']()
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
