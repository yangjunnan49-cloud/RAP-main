"""All synthetic frame/scale/rank/PnP controls, first solver call after I/O gate."""
import codecs
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import baseline_lib as lib
import pnp_lib

OUT=lib.ROOT/'controls'
checks=[]


def check(name,condition,**evidence):
    record={'name':name,'passed':bool(condition),**evidence}
    lib.save(OUT/('check_%02d.json'%(len(checks)+1)),record);checks.append(record)
    assert record['passed'],name


try:
    frozen=lib.verify_freeze('controls');method=lib.load(lib.ROOT/'METHOD.json')
    cv2,np=lib.runtime()
    import numpy.ma
    for name in ('ascii','cp437','utf-8','latin-1'):codecs.lookup(name)
    cache=OUT/'cold_arrays.npz';fixture_path=lib.ROOT/'SYNTHETIC_FIXTURE.json'
    lib.read_gate([fixture_path,cache],OUT)
    fixture=lib.load(fixture_path);xyz=np.asarray(fixture['xyz']);xy=np.asarray(fixture['xy']);k=np.asarray(fixture['K'])
    rotation=np.asarray(fixture['R']);translation=np.asarray(fixture['t'])
    check('installed_API_binding',hasattr(cv2,'solvePnPRansac') and hasattr(cv2,'Rodrigues') and isinstance(cv2.SOLVEPNP_EPNP,int))
    check('rank0_fixture',np.linalg.matrix_rank(np.zeros((8,3)))==0)
    check('rank1_fixture',np.linalg.matrix_rank(np.array([[i,0.,0.] for i in range(8)])-np.array([3.5,0.,0.]))==1)
    plane=np.array([[x,y,10.] for x in (-1.,0.,1.) for y in (-1.,0.,1.)])
    check('rank2_fixture',np.linalg.matrix_rank(plane-plane.mean(axis=0))==2)
    check('rank3_fixture',np.linalg.matrix_rank(xyz-xyz.mean(axis=0))==3)

    def errors(result,expected_r,expected_t):
        q=np.eye(4);q[:3,:3]=expected_r;q[:3,3]=expected_t
        r,_=lib.angles(np,np.asarray(result['R_i_to_j']),np.asarray(result['unit_t_i_to_j']),q,1e-9)
        t=float(np.linalg.norm(np.asarray(result['t_i_to_j_m'])-expected_t))
        return r,t

    pred,arrays=pnp_lib.estimate(cv2,np,xyz,xy,k,method,'synthetic_forward')
    check('cold_clean_nonplanar_pose',pred['status']=='POSE',status=pred['status'])
    er=errors(pred,rotation,translation)
    check('forward_metric_camera_direction',er[0]<.001 and er[1]<.0001,errors=list(er))
    inverse_r=rotation.T;inverse_t=-rotation.T@translation
    target_xyz=xyz@rotation.T+translation
    source=xyz@k.T;source_xy=source[:,:2]/source[:,2:3]
    inverse,_=pnp_lib.estimate(cv2,np,target_xyz,source_xy,k,method,'synthetic_inverse')
    ei=errors(inverse,inverse_r,inverse_t)
    check('inverse_frame_action',inverse['status']=='POSE' and ei[0]<.001 and ei[1]<.0001,errors=list(ei))
    scaled,_=pnp_lib.estimate(cv2,np,xyz*7.3,xy,k,method,'synthetic_scale')
    es=errors(scaled,rotation,translation*7.3)
    check('metric_scale_tracks_supplied3D_units',scaled['status']=='POSE' and es[0]<.001 and es[1]<.001,errors=list(es))
    bad_xy=xy.copy();bad_xy[-16:]=[20.,20.]
    robust,_=pnp_lib.estimate(cv2,np,xyz,bad_xy,k,method,'synthetic_outliers')
    eo=errors(robust,rotation,translation)
    check('fixed_outlier_control',robust['status']=='POSE' and eo[0]<.1 and eo[1]<.02,errors=list(eo))
    again,again_arrays=pnp_lib.estimate(cv2,np,xyz,xy,k,method,'synthetic_forward')
    check('fixed_seed_reproduction',pred==again and all(np.array_equal(arrays[n],again_arrays[n],equal_nan=True) for n in arrays))
    short,_=pnp_lib.estimate(cv2,np,xyz[:7],xy[:7],k,method,'short')
    check('below8_explicit_no_pose',short['status']=='NO_EVIDENCE_INSUFFICIENT_HYPOTHESES' and short['R_i_to_j'] is None)
    planar,_=pnp_lib.estimate(cv2,np,plane,xy[:9],k,method,'plane')
    check('planar_unsupported_explicit',planar['status']=='NO_EVIDENCE_PLANAR_OR_DEGENERATE_3D')
    duplicate,_=pnp_lib.estimate(cv2,np,np.tile(xyz[0],(8,1)),xy[:8],k,method,'duplicate')
    check('rank0_explicit',duplicate['status']=='NO_EVIDENCE_PLANAR_OR_DEGENERATE_3D')
    line=np.asarray([[float(i),0.,10.] for i in range(8)])
    collinear,_=pnp_lib.estimate(cv2,np,line,xy[:8],k,method,'collinear')
    check('rank1_explicit',collinear['status']=='NO_EVIDENCE_PLANAR_OR_DEGENERATE_3D')
    line2d,_=pnp_lib.estimate(cv2,np,xyz,np.column_stack((np.arange(len(xyz)),np.ones(len(xyz)))),k,method,'image_line')
    check('rank1_image_explicit',line2d['status']=='NO_EVIDENCE_DEGENERATE_2D')
    nonfinite=xyz.copy();nonfinite[0,0]=np.nan
    bad,_=pnp_lib.estimate(cv2,np,nonfinite,xy,k,method,'nonfinite')
    check('nonfinite_explicit',bad['status']=='NO_EVIDENCE_INVALID_INPUT')
    invalid_k=k.copy();invalid_k[0,0]=-1
    badk,_=pnp_lib.estimate(cv2,np,xyz,xy,invalid_k,method,'bad_k')
    check('invalid_intrinsic_explicit',badk['status']=='NO_EVIDENCE_INVALID_INTRINSICS')
    check('verified_support_and_depth',pred['verified_inliers']>=8 and np.all(arrays['target_depth'][arrays['verified_mask']!=0]>0) and np.max(arrays['residual_px'][arrays['verified_mask']!=0])<=2)
    check('zero_translation_direction_null',pnp_lib.unit_direction(np,np.zeros(3),1e-9) is None)
    check('unit_direction',abs(np.linalg.norm(pred['unit_t_i_to_j'])-1)<1e-12)
    with cache.open('xb') as f:np.savez(f,xyz=xyz,xy=xy)
    with np.load(cache,allow_pickle=False) as z:check('cold_NPZ_roundtrip',np.array_equal(z['xyz'],xyz) and np.array_equal(z['xy'],xy))
    denied=False
    try:(lib.ROOT/'EVALUATION_INPUTS.json').read_bytes()
    except PermissionError:denied=True
    check('evaluation_binding_denied',denied)
    lib.complete(OUT,{'controls':checks,'control_count':len(checks),'source_freeze_sha256':frozen,
        'measured_data_or_reference_reads':0,'first_solver_call_after_strict_read_gate':True,'EPNP_flag':int(cv2.SOLVEPNP_EPNP)})
    print('PR1 complete synthetic controls PASS')
except BaseException as error:
    lib.failure(OUT,error);raise
