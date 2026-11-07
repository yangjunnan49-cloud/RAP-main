"""Actual native API and analytic counterexamples, without real input binding."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
out=Path(sys.argv[1]);gate([],out);lease(out,True)
rng=np.random.default_rng(20261103)
left=rng.integers(0,256,(96,256),dtype=np.uint8)
ok,encoded=cv2.imencode('.png',left); assert ok
decoded=cv2.imdecode(encoded,cv2.IMREAD_GRAYSCALE);assert np.array_equal(left,decoded)
shift_records=[]
for disparity in (8,16,32):
    lease(out)
    right=np.zeros_like(left);right[:,:-disparity]=left[:,disparity:]
    engine=cv2.StereoSGBM_create(minDisparity=0,numDisparities=64,blockSize=5,P1=8*25,P2=32*25,disp12MaxDiff=1,preFilterCap=31,uniquenessRatio=10,speckleWindowSize=0,speckleRange=1,mode=cv2.STEREO_SGBM_MODE_SGBM)
    measured=engine.compute(left,right).astype(np.float64)/16
    sample=measured[8:-8,80:200]
    valid=sample>0
    assert valid.mean()>.95
    median=float(np.median(sample[valid]));assert abs(median-disparity)<.1
    shift_records.append(dict(disparity=disparity,median=median,valid_fraction=float(valid.mean())))
# Independent scalar stereo geometry at non-unit focal length and baseline.
f=200.;baseline=.54;point=np.array([1.2,-.4,9.])
u0=f*point[0]/point[2];v0=f*point[1]/point[2]
u1=f*(point[0]-baseline)/point[2]
depth=f*baseline/(u0-u1)
reconstructed=np.array([u0*depth/f,v0*depth/f,depth])
assert np.max(np.abs(reconstructed-point))<1e-12
invalid=[d for d in (0.,-1.) if d<=0];assert len(invalid)==2
# Exactly repeated appearance has multiple admissible shifts, irrespective of API winner.
repeat=np.tile(np.arange(16,dtype=np.uint8),(24,16))
rival_costs=[int(np.abs(repeat[:,64:192].astype(int)-np.roll(repeat,d,axis=1)[:,64:192].astype(int)).sum()) for d in (0,16,32)]
assert rival_costs==[0,0,0]
# Geometric aliases may be full rank while extra appearance distinguishes or also aliases.
motif=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
wrong=motif+np.array([5.,0.,0.]);assert np.max(abs((motif+[5.,0.,0.])-wrong))==0
centered=wrong-wrong.mean(axis=0);assert np.linalg.matrix_rank(centered)==3
appearance=np.array([11,29,73,151]);different=np.array([151,73,29,11])
assert np.any(appearance!=different) and np.array_equal(appearance,appearance.copy())
rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
translation=np.array([2.,-3.,1.]);q=rotation@point+translation
assert np.max(abs(rotation.T@(q-translation)-point))<1e-12
complete(out,cv2_version=cv2.__version__,numpy_version=np.__version__,threads=cv2.getNumThreads(),opencl=cv2.ocl.useOpenCL(),synthetic_shift_controls=shift_records,nonunit_baseline_depth=depth,repeat_rival_costs=rival_costs,geometry_full_rank_alias=True,distinct_appearance_can_discriminate=True,identical_appearance_remains_ambiguous=True,real_input_bound=False,torch_imported=('torch' in sys.modules))
