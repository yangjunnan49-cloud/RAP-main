"""Identical measured four-image inputs with distinct physical place identities."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import measurement as m
out=Path(sys.argv[1]);gate([],out);lease(out,True)
left=np.random.default_rng(761103).integers(0,256,(96,384),dtype=np.uint8)
right=np.zeros_like(left);right[:,:-16]=left[:,16:]
stereo=m.engine();dl=stereo.compute(left,right)
dr=np.ascontiguousarray(np.fliplr(stereo.compute(np.ascontiguousarray(np.fliplr(right)),np.ascontiguousarray(np.fliplr(left)))))
uv=np.array([[160.,20.],[180.,20.],[200.,40.],[220.,40.],[160.,60.],[180.,70.],[200.,60.],[220.,70.]])
valid,detail,points=m.sample(dl,dr,uv,(200.,200.,100.,40.,.54))
assert valid.all() and len(uv)>=4 and m.min_covariance(uv)>=4
assert np.max(abs(points[:,2]-6.75))<.1
source=points.copy();target=points.copy();residuals=np.linalg.norm(source-target,axis=1)
assert np.max(residuals)==0
centered=source-source.mean(axis=0);radius=float(np.sqrt(np.mean(np.sum(centered*centered,axis=1))))
H=np.zeros((6,6))
for p in centered/radius:
    x,y,z=p;skew=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    jac=np.concatenate([np.eye(3),-skew],axis=1);H+=jac.T@jac/len(source)
spectrum=np.linalg.eigvalsh(H);assert spectrum.min()>1e-4
physical_shift=np.array([30.,0.,0.]);world_source=source.copy();world_target=target+physical_shift
same_correct_T=np.eye(4);alias_correct_T=np.eye(4);alias_correct_T[:3,3]=-physical_shift
# Projection of the duplicated room in its own translated camera is identical.
projection_checks=0
for p_a,p_b,pixel in zip(world_source,world_target,uv):
    local_b=p_b-physical_shift
    assert np.max(abs(p_a-local_b))<1e-12
    for p in (p_a,local_b):
        u=200*p[0]/p[2]+100;v=200*p[1]/p[2]+40
        assert abs(u-pixel[0])<1e-10 and abs(v-pixel[1])<1e-10
        projection_checks+=1
hashes={name:hashlib.sha256(array.tobytes()).hexdigest() for name,array in [('source_left',left),('target_left',left.copy()),('source_right',right),('target_right',right.copy())]}
assert hashes['source_left']==hashes['target_left'] and hashes['source_right']==hashes['target_right']
np.savez_compressed(out/'FIXTURE.npz',left=left,right=right,uv=uv,disparity_left=dl,disparity_right=dr,xyz=points,H=H,physical_same=same_correct_T,physical_alias=alias_correct_T)
save(out/'COUNTEREXAMPLE.json',dict(observation_hashes=hashes,unchanged_cross_visit_pixels=uv.tolist(),valid_joint_matches=int(valid.sum()),min_image_covariance=m.min_covariance(uv),max_identity_fit_residual_m=float(residuals.max()),conditional_H_eigenvalues=spectrum.tolist(),correct_physical_transforms=[same_correct_T.tolist(),alias_correct_T.tolist()],physical_answer_separation_m=30.,alias_wrong_identity_error_m=30.,identity_from_support_not_certified=True,physical_scene='idealized two identical rooms; no claim about real KITTI causes'))
complete(out,synthetic_only=True,actual_stereo_calls=2,joint_supported_matches=8,full_conditional_rank=6,independent_scalar_projection_checks=projection_checks,observations_identical_across_distinct_physical_worlds=True,depth_support_and_rank_insufficient_for_identity=True,real_data_reads=0)
