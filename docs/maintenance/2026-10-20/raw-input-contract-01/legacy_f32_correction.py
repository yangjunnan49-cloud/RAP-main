"""Explicit original float32 KITTI correction semantics across NumPy versions."""
import numpy as np
def legacy_f32_correction(points):
    if points.dtype!=np.float32 or points.ndim!=2 or points.shape[1]!=3:raise ValueError('Require Nx3 float32 source points')
    angle=np.deg2rad(.205);c=np.float32(np.cos(angle));s=np.float32(np.sin(angle))
    x,y,z=points[:,0],points[:,1],points[:,2];rho=np.hypot(x,y);safe=rho>np.float32(1e-6);minimum=np.maximum(rho,np.float32(1e-6));zero=np.float32(0)
    sxz=np.where(safe,x*z/minimum,zero);syz=np.where(safe,y*z/minimum,zero);sz=np.where(safe,rho,zero)
    out=points.copy();out[:,0]=np.where(safe,x*c-sxz*s,x);out[:,1]=np.where(safe,y*c-syz*s,y);out[:,2]=np.where(safe,z*c+sz*s,z)
    return out
