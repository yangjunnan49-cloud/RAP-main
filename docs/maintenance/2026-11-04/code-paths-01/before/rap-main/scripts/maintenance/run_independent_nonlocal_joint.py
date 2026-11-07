"""NJE0 enclosing resource receipt, including imports and failed attempts."""
import time
START=time.monotonic()
import ast,json,resource,runpy,signal,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01'
stage=sys.argv[1];sup=base/'supervision'/stage
previous=sum(json.loads(p.read_text())['wall_seconds'] for p in (base/'supervision').glob('*/child_exit.json'))
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NJE0 cumulative2400s')))
signal.alarm(max(1,int(2400-previous)))
target=Path(__file__).with_name('independent_nonlocal_joint.py')
ok=False;error=None;gpu_a=gpu_r=0
try:
    ast.parse(target.read_text());runpy.run_path(str(target),run_name='__main__')
    if 'torch' in sys.modules:
        torch=sys.modules['torch']
        if torch.cuda.is_initialized():gpu_a=torch.cuda.max_memory_allocated();gpu_r=torch.cuda.max_memory_reserved()
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=6*2**30
    assert gpu_a<=8*2**30 and gpu_r<=8*2**30
    assert previous+time.monotonic()-START<=2400
    assert sum(p.stat().st_size for p in base.rglob('*') if p.is_file())<256*2**20
    ok=True
except BaseException as ex:error=repr(ex);raise
finally:
    if 'torch' in sys.modules and sys.modules['torch'].cuda.is_initialized():
        gpu_a=sys.modules['torch'].cuda.max_memory_allocated();gpu_r=sys.modules['torch'].cuda.max_memory_reserved()
    result=dict(success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
      peak_GPU_allocated_bytes=gpu_a,peak_GPU_reserved_bytes=gpu_r,artifact_bytes=sum(p.stat().st_size for p in base.rglob('*') if p.is_file()),
      observer_full_lifetime_peak='UNKNOWN',ordinary_preparation_RSS='UNKNOWN',full_child_exit_retained=True)
    with (sup/'child_exit.json').open('x') as f:json.dump(result,f,indent=2)
