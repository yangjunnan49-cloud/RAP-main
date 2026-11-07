"""RVC0 cumulative resource enclosure, imports and failures included."""
import time
START=time.monotonic()
import ast,json,resource,runpy,signal,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'docs/maintenance/2026-10-16/ray-consistency-ranking-01';stage=sys.argv[1];sup=base/'supervision'/stage
previous=sum(json.loads(p.read_text())['wall_seconds'] for p in (base/'supervision').glob('*/child_exit.json'))
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RVC0 cumulative1200s')));signal.alarm(max(1,int(1200-previous)))
ok=False;err=None
try:
    target=Path(__file__).with_name('validate_ray_consistency_ranking.py' if stage=='validate' else 'ray_consistency_ranking.py')
    ast.parse(target.read_text());runpy.run_path(str(target),run_name='__main__')
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=2*2**30
    assert previous+time.monotonic()-START<=1200 and sum(p.stat().st_size for p in base.rglob('*') if p.is_file())<=256*2**20
    assert 'torch' not in sys.modules and 'open3d' not in sys.modules;ok=True
except BaseException as ex:err=repr(ex);raise
finally:
    with (sup/'child_exit.json').open('x') as f:json.dump(dict(success=ok,error=err,wall_seconds=time.monotonic()-START,peak_Linux_process_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0,model_solver_training_calls=0,artifact_bytes=sum(p.stat().st_size for p in base.rglob('*') if p.is_file()),ordinary_setup_RSS='UNKNOWN',observer_lifetime_peak='UNKNOWN'),f,indent=2)
