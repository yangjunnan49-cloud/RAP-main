"""Finite existing-runtime identity/config preflight; no raw numerical payload."""
import time
START=time.monotonic()
import os,sys,json,hashlib,subprocess,resource,signal,traceback
from pathlib import Path
MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-10-20/raw-system-integration-01'
SUP=BASE/'supervision'
RAP='/root/miniconda3/envs/rap-inference/bin/python';KISS='/root/venvs/kiss-slam-hc1/bin/python'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def used():
    return sum(max([read(d/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (d/n).exists()]+[0]) for d in SUP.glob('*') if d.is_dir())
def inspect(label):
    import importlib.metadata as md
    import kiss_icp
    from kiss_icp.config import KISSConfig
    sys.path.insert(0,str(MAIN.parent/'RAP-SLAM'))
    from rap_slam.odometry import KissOdometry
    engine=KissOdometry(max_range=80.,min_range=1.5,voxel_size=.8,deskew=False)
    root=Path(kiss_icp.__file__).parent
    files={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and p.suffix in ('.py','.so')}
    save(BASE/'environment'/f'{label}.json',dict(python=sys.version,executable=sys.executable,kiss_icp_version=md.version('kiss-icp'),root=str(root),files=files,frontend_config=engine._odom.config.model_dump() if hasattr(engine._odom,'config') else KISSConfig(data=dict(max_range=80.,min_range=1.5,deskew=False),mapping=dict(voxel_size=.8)).model_dump(),raw_scans_read=0,odometry_registration_calls=0,
        self_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
def run():
    left=7200-used();assert left>1;signal.signal(signal.SIGALRM,lambda a,b:(_ for _ in ()).throw(TimeoutError('raw integration cumulative cap')));signal.alarm(max(1,int(left)))
    ok=False;err=None;peak=0
    try:
        (BASE/'environment').mkdir();save(BASE/'PREFLIGHT_SOURCE.json',dict(files={str(p):sha(p) for p in (Path(__file__),BASE/'OWNER_SCOPE.md',MAIN.parent/'RAP-SLAM/rap_slam/odometry.py')}))
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['PYTHONDONTWRITEBYTECODE']='1'
        for label,exe in [('RAP',RAP),('KISS',KISS)]:
            p=subprocess.run([exe,'-u','-B',__file__,'--inspect',label],env=env,timeout=60);assert p.returncode==0
            peak=max(peak,read(BASE/'environment'/f'{label}.json')['self_peak_RSS_bytes'])
        a=read(BASE/'environment/RAP.json');b=read(BASE/'environment/KISS.json');keys={p for p in a['files'] if p.endswith('.py')}|{p for p in b['files'] if p.endswith('.py')}
        differences=[p for p in sorted(keys) if a['files'].get(p)!=b['files'].get(p)]
        save(BASE/'RUNTIME_PREFLIGHT.json',dict(same_package_version=a['kiss_icp_version']==b['kiss_icp_version'],Python_source_differences=differences,
            same_frontend_config=a['frontend_config']==b['frontend_config'],different_ABI_native_builds_may_remain=True,raw_scans_read=0,remaining_scope_seconds_before_this_attempt=left))
        assert a['frontend_config']==b['frontend_config'];assert max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)<=4*2**30;ok=True
        print('Runtime compatibility: package',a['kiss_icp_version'],b['kiss_icp_version'],'Python differences',differences,'config equal',a['frontend_config']==b['frontend_config'],flush=True)
    except BaseException as e:err=repr(e);traceback.print_exc();save(BASE/'FAILURE_preflight.json',dict(error=err))
    finally:
        signal.alarm(0);save(SUP/'preflight/child_exit.json',dict(success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--inspect' in sys.argv:inspect(sys.argv[-1])
    else:assert sys.argv[1]=='preflight';run()
