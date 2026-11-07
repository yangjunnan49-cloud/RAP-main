import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
for n,h in freeze['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h.lower()
paths=['/root/miniconda3/bin/python','/root/venvs/kiss-slam-hc1/bin/python','/usr/bin/python3']
code="import importlib.util,json,sys; print(json.dumps({'executable':sys.executable,'modules':{n:({'available':True,'origin':s.origin} if (s:=importlib.util.find_spec(n)) else {'available':False}) for n in ['cv2','numpy','scipy','skimage']}}))"
rows=[]
for p in paths:
    q=Path(p);assert q.is_file();r=subprocess.run([p,'-I','-B','-c',code],capture_output=True,text=True,timeout=15,env=os.environ.copy());rows.append({'path':p,'resolved':str(q.resolve()),'interpreter_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'exit_code':r.returncode,'result':json.loads(r.stdout) if r.returncode==0 else None,'stderr':r.stderr[:2000]})
obj={'environments':rows,'module_imports':0,'package_installs':0,'images_or_models_read':0,'elapsed_seconds':time.monotonic()-START};(ROOT/'RESULTS.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');print(json.dumps(obj))
