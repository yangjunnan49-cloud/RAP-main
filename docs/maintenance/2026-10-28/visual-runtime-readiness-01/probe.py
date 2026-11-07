import hashlib,importlib.util,json,os,resource,signal,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;START=time.monotonic()
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('probe alarm')));signal.alarm(45)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((ROOT/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
for n,h in freeze['files'].items():assert sha(ROOT/n)==h.lower(),n
available={n:bool(importlib.util.find_spec(n)) for n in ['cv2','numpy','scipy','skimage']}
result={'available':available,'python_executable':sys.executable,'python_version':sys.version,'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),'image_point_pose_model_reads':0}
try:
    if not available['cv2']:raise ImportError('Existing environment has no cv2; no install')
    import cv2,numpy as np
    names=['SIFT_create','ORB_create','BFMatcher','solvePnPRansac','findEssentialMat','recoverPose']
    result.update(cv2_version=cv2.__version__,cv2_origin=cv2.__file__,numpy_version=np.__version__,APIs={n:hasattr(cv2,n) for n in names})
    docs={n:(getattr(cv2,n).__doc__ or '')[:24000] for n in names if hasattr(cv2,n)}
    (ROOT/'INSTALLED_API_DOCS.json').write_text(json.dumps(docs,indent=2)+'\n',encoding='utf-8')
    result['passed']=all(result['APIs'].values())
except BaseException as e:
    result.update(passed=False,error=repr(e))
finally:
    result.update(elapsed_seconds=time.monotonic()-START,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    (ROOT/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
    signal.alarm(0)
if not result['passed']:sys.exit(2)
