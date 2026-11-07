"""Bind .NET seven-digit UTC serialization repair before first real worker."""
import time
START=time.monotonic()
import ast,json,sys,resource,traceback,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
MAIN=Path(__file__).resolve().parents[2];BASE=MAIN/'docs/maintenance/2026-10-20/raw-system-integration-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def run():
    ok=False;err=None
    try:
        old=Path(__file__).with_name('raw_system_integration02.py');new=old.with_name('raw_system_integration03.py');text=old.read_text();assert sha(old)==read(BASE/'VARIANT02_FREEZE.json')['files'][str(old)]
        assert not any((BASE/'bank').iterdir()) and not any((BASE/'supervision/run').glob('r*_*_*'))
        source=text.replace('import os,sys,json,hashlib,resource,signal,subprocess,traceback,importlib.util','import os,sys,json,hashlib,resource,signal,subprocess,traceback,importlib.util,re')
        expression="datetime.fromisoformat(data['utc'].replace('Z','+00:00'))"
        repaired="datetime.fromisoformat(re.sub(r'(\\.\\d{6})\\d+(?=[+-]|Z|$)',r'\\1',data['utc']).replace('Z','+00:00'))"
        assert source.count(expression)==1;source=source.replace(expression,repaired)
        for a,b in [("BASE/'bank'","BASE/'bank03'"),("BASE/'bank_seal.json'","BASE/'bank_seal03.json'"),("BASE/'evaluation'","BASE/'evaluation03'"),("BASE/'results.json'","BASE/'results03.json'"),("SUP/'run'","SUP/'run03'")]:source=source.replace(a,b)
        source=source.replace("'run':run_bank,'evaluate':evaluate","'run03':run_bank,'evaluate03':evaluate")
        marker="    for p,h in read(BASE/'VARIANT02_FREEZE.json')['files'].items():assert sha(p)==h,p"
        assert source.count(marker)==1;source=source.replace(marker,marker+"\n    for p,h in read(BASE/'VARIANT03_FREEZE.json')['files'].items():assert sha(p)==h,p")
        compile(source,str(new),'exec')
        def numeric(code):
            worker=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='worker');names={'front.register','slam.process_scan','slam.generate_new_node','slam.local_map_graph.erase_last_local_map','fine_module.fine','slam.fine_grained_optimization','np.linalg.solve','kitti_vertical_correction','binding._correct_kitti_scan','proper_one'}
            return [ast.dump(n,include_attributes=False) for n in ast.walk(worker) if isinstance(n,ast.Call) and ast.unparse(n.func) in names]
        assert numeric(text)==numeric(source)
        cases=['2026-10-20T14:27:36.8780068Z','2026-10-20T14:27:36.8780068+00:00','2026-10-20T14:27:36.878006Z']
        for value in cases:
            stamp=datetime.fromisoformat(re.sub(r'(\.\d{6})\d+(?=[+-]|Z|$)',r'\1',value).replace('Z','+00:00'));assert stamp==datetime(2026,10,20,14,27,36,878006,tzinfo=timezone.utc)
        wrapper=Path(__file__).with_name('launch_raw_integration_run.py');outwrapper=wrapper.with_name('launch_raw_integration_run03.py');ws=wrapper.read_text().replace('import raw_system_integration02 as d','import raw_system_integration03 as d').replace("'LAUNCH_BINDING.json'","'LAUNCH_BINDING03.json'").replace("SUP/'run/","SUP/'run03/").replace("d.run('run',False)","d.run('run03',False)").replace("sys.argv[1]=='run'","sys.argv[1]=='run03'")
        compile(ws,str(outwrapper),'exec')
        with new.open('x',encoding='utf-8') as f:f.write(source)
        with outwrapper.open('x',encoding='utf-8') as f:f.write(ws)
        save(BASE/'VARIANT03_FREEZE.json',dict(files={str(p):sha(p) for p in (old,new,wrapper,outwrapper,Path(__file__),BASE/'CLOCK_SERIALIZATION03.md')},clock_serialization_cases=cases,numerical_call_AST_equal=True,guard_age_seconds=2,guard_headroom_bytes=12*2**30,old_attempts_preserved=True,real_workers_before_repair=0,cap_reset=False))
        print('Clock03 bound; three UTC forms pass; numerical AST unchanged;0 real workers replayed',flush=True);ok=True
    except BaseException as e:err=repr(e);traceback.print_exc()
    finally:save(BASE/'supervision/prepare03/child_exit.json',dict(success=ok,error=err,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare03';run()
