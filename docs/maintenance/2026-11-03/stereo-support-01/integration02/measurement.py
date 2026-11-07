"""Fixed stereo sampling; availability is not a physical identity certificate."""
import math
import numpy as np
import cv2
def engine():
    return cv2.StereoSGBM_create(minDisparity=0,numDisparities=128,blockSize=5,P1=200,P2=800,disp12MaxDiff=1,preFilterCap=31,uniquenessRatio=10,speckleWindowSize=0,speckleRange=1,mode=cv2.STEREO_SGBM_MODE_SGBM)
def sample(dl, dr, uv, camera):
    h,w=dl.shape
    valid=np.zeros(len(uv),dtype=bool)
    details=np.full((len(uv),3),np.nan,dtype=np.float64)
    xyz=np.full((len(uv),3),np.nan,dtype=np.float64)
    fx,fy,cx,cy,baseline=camera
    for k,(u,v) in enumerate(uv):
        if not math.isfinite(float(u)) or not math.isfinite(float(v)):continue
        x,y=math.floor(float(u)+.5),math.floor(float(v)+.5)
        if not (0<=x<w and 0<=y<h):continue
        d=float(dl[y,x])/16
        details[k,0]=d
        xr=math.floor(x-d+.5)
        if not (.5<=d<127 and 0<=xr<w):continue
        rd=float(dr[y,xr])/16;details[k,1]=rd;details[k,2]=abs(d-rd)
        if not (.5<=rd<127 and abs(d-rd)<=1):continue
        z=fx*baseline/d
        xyz[k]=[(float(u)-cx)*z/fx,(float(v)-cy)*z/fy,z]
        valid[k]=True
    return valid,details,xyz
def min_covariance(uv):
    if len(uv)<2:return 0.
    centered=uv-uv.mean(axis=0)
    return float(np.linalg.eigvalsh(centered.T@centered/len(uv))[0])
