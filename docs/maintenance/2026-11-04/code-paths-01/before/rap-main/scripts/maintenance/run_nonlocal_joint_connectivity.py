"""NJC0 resource enclosure; no model/scientific library imports."""
import time
START=time.monotonic()
import ast,json,resource,runpy,signal,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
base=root/'docs/maintenance/2026-10-15/nonlocal-joint-connectivity-01'
stage=sys.argv[1];sup=base/'supervision'/stage
old=sum(json.loads(p.read_text())['wall_seconds'] for p in (base/'supervision').glob('*/child_exit.json'))
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NJC0 combined300s')))
signal.alarm(max(1,int(300-old)))
target=Path(__file__).with_name('validate_nonlocal_joint_connectivity.py' if stage=='validate' else 'nonlocal_joint_connectivity.py')
ok=False;error=None
try:
    ast.parse(target.read_text())
    runpy.run_path(str(target),run_name='__main__')
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<=128*2**20
    assert old+time.monotonic()-START<=300
    assert sum(p.stat().st_size for p in base.rglob('*') if p.is_file())<8*2**20
    ok=True
except BaseException as ex:error=repr(ex);raise
finally:
    result=dict(success=ok,error=error,full_resource_capture=True,wall_seconds=time.monotonic()-START,
      peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,peak_GPU_allocated_bytes=0,peak_GPU_reserved_bytes=0,
      artifact_bytes=sum(p.stat().st_size for p in base.rglob('*') if p.is_file()),model_coordinate_pose_calls=0)
    with (sup/'child_exit.json').open('x') as f:json.dump(result,f,indent=2)
