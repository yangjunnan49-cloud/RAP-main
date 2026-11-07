"""Freeze evaluation-only output-route adapter before any GT read."""
import time
START=time.monotonic()
import sys,ast,inspect,resource,traceback
from pathlib import Path
import raw_input_system05 as d
def run():
    ok=False;error=None
    try:
        d.verify();assert d.used()<7200
        original=inspect.getsource(d.evaluate);corrected=original.replace("BASE/'bank04'","BASE/'bank05'")
        assert original.count("BASE/'bank04'")==5
        assert ast.dump(ast.parse(original.replace('bank04','bank05')),include_attributes=False)==ast.dump(ast.parse(corrected),include_attributes=False)
        output=Path(__file__).with_name('evaluate_raw_bank05.py')
        source='import sys,inspect\nimport raw_input_system05 as d\n'
        source+="d.verify()\nfor p,h in d.read(d.BASE/'EVAL05_ROUTE_FREEZE.json')['files'].items():assert d.sha(p)==h,p\n"
        source+="original=inspect.getsource(d.evaluate)\nsource=original.replace(\"BASE/'bank04'\",\"BASE/'bank05'\")\nassert original.count(\"BASE/'bank04'\")==5\nexec(compile(source,__file__,'exec'),d.__dict__)\nassert sys.argv[1]=='evaluate05'\nd.run('evaluate05',False)\n"
        compile(source,str(output),'exec')
        with output.open('x') as f:f.write(source)
        d.save(d.BASE/'EVAL05_ROUTE_FREEZE.json',dict(utc=d.now(),files={str(p):d.sha(p) for p in (Path(__file__),output,Path(d.__file__),d.BASE/'GUARD05_FREEZE.json')},change='Only five evaluator bank04 path literals become bank05; no numeric/gate change; before all GT',GT_numeric_read=False))
        print('Evaluation route05 frozen; no GT read or numeric change',flush=True);ok=True
    except BaseException as e:error=repr(e);traceback.print_exc()
    finally:d.save(d.SUP/'prepare_eval05/child_exit.json',dict(utc=d.now(),success=ok,error=error,wall_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,GPU_calls=0))
    if not ok:sys.exit(1)
if __name__=='__main__':assert sys.argv[1]=='prepare_eval05';run()
