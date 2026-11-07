"""Ordinary fixed camera_i3D -> camera_j2D PnP, no reference/file API."""
import hashlib
import math


def seed(key):
    return int(hashlib.sha256(('PR1:'+key).encode('ascii')).hexdigest()[:8],16)%2147483647


def unit_direction(np,translation,epsilon):
    norm=float(np.linalg.norm(translation))
    return (translation/norm).tolist() if norm>epsilon else None


def estimate(cv2,np,xyz,xy,k,method,key):
    n=len(xyz)
    out={'status':'NO_EVIDENCE_INSUFFICIENT_HYPOTHESES','input_hypotheses':n,'seed':seed(key),
        'native_inliers':0,'verified_inliers':0,'R_i_to_j':None,'t_i_to_j_m':None,'unit_t_i_to_j':None}
    arrays={'native_mask':np.zeros(n,dtype=np.uint8),'verified_mask':np.zeros(n,dtype=np.uint8),
        'projected_xy':np.full((n,2),np.nan),'target_depth':np.full(n,np.nan),'residual_px':np.full(n,np.inf),
        'rvec':np.empty(0),'tvec':np.empty(0)}
    if n<method['minimum_hypotheses']:return out,arrays
    if xyz.shape!=(n,3) or xy.shape!=(n,2) or not np.isfinite(xyz).all() or not np.isfinite(xy).all():
        out['status']='NO_EVIDENCE_INVALID_INPUT';return out,arrays
    if k.shape!=(3,3) or not np.isfinite(k).all() or k[0,0]<=0 or k[1,1]<=0 or not np.array_equal(k[2],[0.,0.,1.]) or np.linalg.det(k)<=0:
        out['status']='NO_EVIDENCE_INVALID_INTRINSICS';return out,arrays
    rank=int(np.linalg.matrix_rank(xyz-xyz.mean(axis=0)));out['centered_3D_rank']=rank
    if rank<3:
        out['status']='NO_EVIDENCE_PLANAR_OR_DEGENERATE_3D';return out,arrays
    if np.linalg.matrix_rank(xy-xy.mean(axis=0))<2:
        out['status']='NO_EVIDENCE_DEGENERATE_2D';return out,arrays
    cv2.setRNGSeed(out['seed'])
    try:
        ok,rvec,tvec,inliers=cv2.solvePnPRansac(np.ascontiguousarray(xyz,dtype=np.float64),np.ascontiguousarray(xy,dtype=np.float64),
            cameraMatrix=k,distCoeffs=None,useExtrinsicGuess=False,iterationsCount=method['iterations'],
            reprojectionError=method['reprojection_px'],confidence=method['confidence'],flags=cv2.SOLVEPNP_EPNP)
        if not ok or rvec is None or tvec is None or inliers is None:
            out['status']='NO_EVIDENCE_NATIVE_FAILURE';return out,arrays
        rvec=np.asarray(rvec,dtype=np.float64).reshape(3);tvec=np.asarray(tvec,dtype=np.float64).reshape(3)
        ids=np.asarray(inliers).reshape(-1)
        if not np.isfinite(rvec).all() or not np.isfinite(tvec).all() or len(set(map(int,ids)))!=len(ids) or np.any(ids<0) or np.any(ids>=n):
            out['status']='NO_EVIDENCE_INVALID_NATIVE_POSE';return out,arrays
        rotation,_=cv2.Rodrigues(rvec)
        arrays.update(rvec=rvec,tvec=tvec)
        tolerance=method['rotation_tolerance']
        if not np.isfinite(rotation).all() or np.max(np.abs(rotation.T@rotation-np.eye(3)))>tolerance or abs(np.linalg.det(rotation)-1)>tolerance:
            out['status']='NO_EVIDENCE_INVALID_ROTATION';return out,arrays
        native=np.zeros(n,dtype=np.uint8);native[ids.astype(np.int64)]=1
        camera=xyz@rotation.T+tvec;positive=np.isfinite(camera).all(axis=1)&(camera[:,2]>0)
        projected=np.full((n,2),np.nan);homogeneous=camera[positive]@k.T
        projected[positive]=homogeneous[:,:2]/homogeneous[:,2:3]
        residual=np.full(n,np.inf);residual[positive]=np.linalg.norm(projected[positive]-xy[positive],axis=1)
        verified=((native!=0)&positive&(residual<=method['reprojection_px'])).astype(np.uint8)
        arrays.update(native_mask=native,verified_mask=verified,projected_xy=projected,target_depth=camera[:,2],residual_px=residual)
        out.update(native_inliers=int(native.sum()),verified_inliers=int(verified.sum()))
        if out['verified_inliers']<method['minimum_hypotheses']:
            out['status']='NO_EVIDENCE_VERIFIED_SUPPORT';return out,arrays
        norm=float(np.linalg.norm(tvec))
        out.update(status='POSE',R_i_to_j=rotation.tolist(),t_i_to_j_m=tvec.tolist(),
            unit_t_i_to_j=unit_direction(np,tvec,method['translation_epsilon_m']),
            max_verified_residual_px=float(np.max(residual[verified!=0])))
        return out,arrays
    except cv2.error as error:
        out.update(status='NO_EVIDENCE_SOLVER_ERROR',solver_error=str(error)[:800]);return out,arrays
