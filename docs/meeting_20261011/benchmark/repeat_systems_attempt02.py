from pathlib import Path
import inspect,json,sys
import repeat_systems as e
ORIGINAL=e.BASE
BASE=ORIGINAL/'attempt02'
SOURCE=inspect.getsource(e.run)
old="payload=cmd[1:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]"
assert SOURCE.count(old)==1
SOURCE=SOURCE.replace(old,"payload=cmd[2:] if model=='RAP-SLAM' else [KISS,*cmd[1:]]")
def freeze():
 e.verify();BASE.mkdir(exist_ok=False)
 (BASE/'child_capture.py').write_bytes((ORIGINAL/'child_capture.py').read_bytes())
 (BASE/'PROTOCOL.md').write_bytes((ORIGINAL/'PROTOCOL.md').read_bytes())
 (BASE/'effective_run.py').write_text(SOURCE,encoding='utf-8')
 inherited=e.read(ORIGINAL/'freeze.json')
 inherited['sources'].update({str(p):e.sha(p) for p in [Path(__file__),BASE/'child_capture.py',BASE/'PROTOCOL.md',BASE/'effective_run.py',ORIGINAL/'freeze.json',ORIGINAL/'AMENDMENT_01.md',ORIGINAL/'evaluate_repeats.py',ORIGINAL/'evaluation_freeze.json']})
 inherited['scope']='administrative payload correction and separate routing; original raw hash freeze inherited'
 e.save(BASE/'freeze.json',inherited)
 e.save(BASE/'evaluation_freeze.json',e.read(ORIGINAL/'evaluation_freeze.json'))
 print('Attempt02 frozen; no model payload yet',flush=True)
def run():
 assert (BASE/'effective_run.py').read_text()==SOURCE
 ns=dict(vars(e));ns['BASE']=BASE
 # Rebind original verify to the new frozen routing through a distinct globals map.
 src=inspect.getsource(e.verify)+'\n'+SOURCE
 exec(compile(src,str(BASE/'effective_run.py'),'exec'),ns);ns['run']()
if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
