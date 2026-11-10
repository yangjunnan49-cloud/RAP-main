"""Bounded CPU child execution with checked termination and output receipts."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
R=Path(__file__).resolve().parent
MEM=2*2**30-64*2**20
CAP=4*2**20

def limits(file_cap):
    os.setsid();resource.setrlimit(resource.RLIMIT_AS,(MEM,MEM));resource.setrlimit(resource.RLIMIT_CPU,(25,25))
    resource.setrlimit(resource.RLIMIT_FSIZE,(file_cap,file_cap));resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def size(out):return sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) if out and out.exists() else 0

def run(cmd,label,seconds,out=None,file_cap=CAP,total_cap=CAP):
    start=time.monotonic();reason=None;peak=0;reserve_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    assert not (R/f'{label}.json').exists()
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    with (R/f'{label}.log').open('x') as log:
        child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=lambda:limits(file_cap))
        while child.poll() is None:
            try:
                data=Path(f'/proc/{child.pid}/status').read_text().splitlines()
                peak=max(peak,next(int(x.split()[1])*1024 for x in data if x.startswith('VmRSS:')))
            except (FileNotFoundError,StopIteration):pass
            if time.monotonic()-start>=seconds:reason='wallclock_limit'
            if size(out)>total_cap:reason='total_output_limit'
            if peak>MEM:reason='memory_limit'
            if reason:
                os.killpg(child.pid,signal.SIGKILL);break
            time.sleep(.01)
        code=child.wait()
    final_size=size(out)
    if final_size>total_cap:reason='total_output_limit'
    if time.monotonic()-start>=seconds and reason is None:reason='wallclock_limit'
    receipt=dict(exit_code=code,reason=reason,passed=code==0 and reason is None,wall_s=time.monotonic()-start,
        observed_peak_RSS_bytes=peak,supervisor_peak_RSS_bytes=reserve_peak,child_AS_limit_bytes=MEM,CPU_limit_s=25,
        wall_limit_s=seconds,file_limit_bytes=file_cap,total_limit_bytes=total_cap,final_output_bytes=final_size,CUDA_VISIBLE_DEVICES='')
    with (R/f'{label}.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    return receipt

def preflight():
    geom=run([sys.executable,str(R/'support_algebra.py'),'synthetic'],'synthetic-supervision',30)
    wall=run([sys.executable,'-c','import time;time.sleep(3)'],'timeout-fixture',.15)
    mem=run([sys.executable,'-c','x=bytearray(3*2**30)'],'memory-fixture',5)
    file=run([sys.executable,'-c',"from pathlib import Path;Path('file-fixture.bin').write_bytes(b'x'*(256*1024))"],'file-fixture',5,file_cap=128*1024)
    aggdir=R/'aggregate-fixture';aggdir.mkdir()
    agg=run([sys.executable,'-c',"from pathlib import Path;import time;p=Path('aggregate-fixture');(p/'a').write_bytes(b'x'*98304);(p/'b').write_bytes(b'x'*98304);time.sleep(3)"],
        'aggregate-fixture-supervision',5,out=aggdir,file_cap=128*1024,total_cap=128*1024)
    passed=geom['passed'] and wall['reason']=='wallclock_limit' and wall['wall_s']<1 and mem['exit_code']==1 and 'MemoryError' in (R/'memory-fixture.log').read_text() and file['exit_code']==1 and 'Errno 27' in (R/'file-fixture.log').read_text() and agg['reason']=='total_output_limit'
    with (R/'preflight.json').open('x') as f:json.dump(dict(passed=passed,geometry=geom,wallclock=wall,memory=mem,file_output=file,aggregate_output=agg),f,indent=2);f.write('\n')
    print('Preflight',passed);assert passed

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','run']);a=p.parse_args();os.chdir(R)
    if a.mode=='preflight':preflight()
    else:
        assert json.loads((R/'preflight.json').read_text())['passed']
        result=run([sys.executable,str(R/'support_algebra.py'),'run'],'real-supervision',30,out=R/'results')
        print(json.dumps(result));assert result['passed']
