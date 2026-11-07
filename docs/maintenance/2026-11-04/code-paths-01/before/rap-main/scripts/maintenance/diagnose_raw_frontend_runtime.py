"""Synthetic arithmetic diagnosis only; no real scans or registration."""
import time
START=time.monotonic()
import os,sys,resource,subprocess,traceback,hashlib,json,random
from pathlib import Path
import numpy as np
import raw_system_integration03 as d
BASE=d.BASE
def native(label):
    sys.path.insert(0,str(d.r.SLAM));from rap_slam.real_dataset import kitti_vertical_correction
    p=np.load(BASE/'synthetic_runtime_points.npy');out=kitti_vertical_correction(p);np.save(BASE/f'synthetic_corrected_{label}.npy',out)
    c=np.cos(np.deg2rad(.205));s=np.sin(np.deg2rad(.205))
    d.save(BASE/f'correction_runtime_{label}.json',dict(python=sys.version,numpy=np.__version__,input_dtype=str(p.dtype),output_dtype=str(out.dtype),scalar_cos_type=str(type(c)),
        multiply_dtype=str((p[:,0]*c).dtype),sum_dtype=str((p[:,0]*c-p[:,2]*s).dtype),input_sha256=d.sha(BASE/'synthetic_runtime_points.npy'),peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
def run():
    ok=False;err=None;peak=0
    try:
        d.verify();assert not (BASE/'bank_seal03.json').exists();assert d.CAP-d.used()>60
        d.save(BASE/'FRONTEND_DIAGNOSIS_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),BASE/'FRONTEND_FAILURE_DIAGNOSIS_SCOPE.md',d.r.SLAM/'rap_slam/real_dataset.py')},real_raw_scans_read=0))
        rng=random.Random(20261020);points=np.asarray([[rng.uniform(-80,80),rng.uniform(-80,80),rng.uniform(-5,5)] for _ in range(10000)]+[[0,0,1],[1,0,0],[0,1,0]],dtype=np.float32);np.save(BASE/'synthetic_runtime_points.npy',points)
        env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['PYTHONDONTWRITEBYTECODE']='1'
        for label,exe in [('RAP','/root/miniconda3/envs/rap-inference/bin/python'),('KISS',d.r.KISS)]:
            p=subprocess.run([exe,'-u','-B',__file__,'--native',label],env=env,timeout=30);assert p.returncode==0;peak=max(peak,d.read(BASE/f'correction_runtime_{label}.json')['peak_RSS_bytes'])
        a=np.load(BASE/'synthetic_corrected_RAP.npy');b=np.load(BASE/'synthetic_corrected_KISS.npy');different=int(np.sum(a!=b));maximum=float(np.max(abs(a.astype(np.float64)-b.astype(np.float64))))
        stages={p.parent.name:max([d.read(p.parent/n)['wall_seconds'] for n in ('child_exit.json','exit.json') if (p.parent/n).exists()]+[0]) for p in d.SUP.glob('*/child_exit.json')}
        d.save(BASE/'FRONTEND_DIAGNOSIS.json',dict(utc=d.now(),synthetic_only=True,components_compared=a.size,unequal_components=different,maximum_absolute_component_delta=maximum,
            runtime_arithmetic_identical=different==0,real_failure_unique_cause_established=False,original_R0_complete_system_result=False,GT_numeric_reads=0,old_attempt_costs=stages))
        print('Synthetic runtime correction difference',different,'of',a.size,'max',maximum,flush=True);d.cap();ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:d.save(d.SUP/'frontend_diagnosis/child_exit.json',dict(utc=d.now(),success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':
    if '--native' in sys.argv:native(sys.argv[-1])
    else:assert sys.argv[1]=='frontend_diagnosis';run()
