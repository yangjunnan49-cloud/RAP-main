import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;START=time.monotonic();target=ROOT/'site-packages'
assert json.loads((ROOT/'LOCAL_WHEEL_RESULT.json').read_text())['passed'];sys.path.insert(0,str(target))
import cv2,numpy as np
assert Path(cv2.__file__).resolve().is_relative_to(target.resolve()) and np.__version__=='2.3.5';cv2.setNumThreads(1);cv2.ocl.setUseOpenCL(False)
names=['SIFT_create','ORB_create','BFMatcher','solvePnPRansac','findEssentialMat','recoverPose','findFundamentalMat'];APIs={n:hasattr(cv2,n) for n in names};assert all(APIs.values())
cv2.SIFT_create();cv2.ORB_create();cv2.BFMatcher()
obj={'passed':True,'cv2_version':cv2.__version__,'cv2_origin':cv2.__file__,'numpy_version':np.__version__,'numpy_origin':np.__file__,'APIs':APIs,'factory_smoke_pass':True,'OpenCL':cv2.ocl.useOpenCL(),'threads':cv2.getNumThreads(),'Torch_imported':'torch' in sys.modules,'image_feature_solver_calls':0,'elapsed_seconds':time.monotonic()-START}
(ROOT/'API_RESULT.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');(ROOT/'INSTALLED_API_DOCS.json').write_text(json.dumps({n:(getattr(cv2,n).__doc__ or '')[:24000] for n in names},indent=2)+'\n',encoding='utf-8');print(json.dumps(obj))
