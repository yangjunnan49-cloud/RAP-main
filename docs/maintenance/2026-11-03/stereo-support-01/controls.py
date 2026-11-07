"""New actual128-disparity interface, mutual sampling and cold NPZ controls."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import measurement as m
out=Path(sys.argv[1]);gate([],out);lease(out,True)
texture=np.random.default_rng(11032026).integers(0,256,(96,384),dtype=np.uint8)
right=np.zeros_like(texture);right[:,:-16]=texture[:,16:]
algo=m.engine();dl=algo.compute(texture,right)
lease(out)
dr=np.fliplr(algo.compute(np.ascontiguousarray(np.fliplr(right)),np.ascontiguousarray(np.fliplr(texture))))
coords=np.array([[160.,30.],[180.,50.],[210.,70.],[220.,40.]])
valid,detail,xyz=m.sample(dl,dr,coords,(200.,200.,100.,40.,.54))
assert valid.all() and np.max(abs(detail[:,0]-16))<.1 and np.max(abs(xyz[:,2]-6.75))<.1
synthetic=np.full((8,16),16*4,dtype=np.int16);back=synthetic.copy()
uv=np.array([[8.,3.],[-2.,3.],[8.,20.],[2.,3.],[8.49,3.],[8.5,3.]])
v,d,x=m.sample(synthetic,back,uv,(100.,100.,0.,0.,.5))
assert v.tolist()==[True,False,False,False,True,True]
assert abs(x[0,2]-12.5)<1e-12
for bad in (0,-16):
    badmap=synthetic.copy();badmap[3,8]=bad
    assert not m.sample(badmap,back,np.array([[8.,3.]]),(100.,100.,0.,0.,.5))[0][0]
back_bad=back.copy();back_bad[3,4]=16*7
assert not m.sample(synthetic,back_bad,np.array([[8.,3.]]),(100.,100.,0.,0.,.5))[0][0]
file=out/'COLD_FIXTURE.npz'
np.savez_compressed(file,left=dl,right=dr,uv=coords)
with np.load(file,allow_pickle=False) as z:assert np.array_equal(z['left'],dl) and np.array_equal(z['right'],dr)
square=np.array([[0.,0.],[4.,0.],[0.,4.],[4.,4.]])
assert abs(m.min_covariance(square)-4)<1e-12
assert m.min_covariance(np.array([[0.,0.],[1.,0.],[2.,0.],[3.,0.]]))==0
complete(out,actual_128_disparity_bidirectional=True,valid_known_depths=xyz[:,2].tolist(),invalid_zero_negative_outside_and_LR_rejection=True,cold_restricted_NPZ_roundtrip=True,minimum_covariance_boundary_checked=True,real_inputs_bound=False,identity_proof=False)
