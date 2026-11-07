"""Independent RLP1 brute geometry and quaternion numerics; no algorithm import."""
import numpy as np


def quaternion_rotation(H):
    sxx,sxy,sxz,syx,syy,syz,szx,szy,szz=np.asarray(H,np.float64).ravel()
    A=np.array([[sxx+syy+szz,syz-szy,szx-sxz,sxy-syx],
        [syz-szy,sxx-syy-szz,sxy+syx,szx+sxz],
        [szx-sxz,sxy+syx,-sxx+syy-szz,syz+szy],
        [sxy-syx,szx+sxz,syz+szy,-sxx-syy+szz]])
    e,v=np.linalg.eigh(A);w,x,y,z=v[:,-1]
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    return R,float((e[-1]-e[-2])/max(abs(e).max(),1e-12))


def weighted_horn(x,y,w):
    x,y,w=np.asarray(x,np.float64),np.asarray(y,np.float64),np.asarray(w,np.float64)
    assert w.sum()>0 and len(w)>=3
    cx=np.average(x,axis=0,weights=w);cy=np.average(y,axis=0,weights=w)
    H=np.einsum('ni,nj,n->ij',x-cx,y-cy,w)
    R,gap=quaternion_rotation(H);assert gap>1e-6
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=cy-R@cx
    return T,gap


def distances(a,b):
    result=np.empty((len(a),len(b)),np.float64)
    for k in range(0,len(a),128):
        difference=a[k:k+128,None,:]-b[None,:,:]
        result[k:k+128]=np.sqrt(np.einsum('ijk,ijk->ij',difference,difference))
    return np.where(np.isfinite(result),result,np.inf)


def labels(points,poses):
    parts=np.split(np.asarray(points,np.float64),3);out={}
    for a in range(3):
        homogeneous=np.linalg.inv(poses[a])
        for b in range(3):
            if a==b:continue
            third=next(k for k in range(3) if k not in (a,b))
            Tb=homogeneous@poses[b];Tc=homogeneous@poses[third]
            q=(Tb@np.c_[parts[b],np.ones(len(parts[b]))].T).T[:,:3]
            u=(Tc@np.c_[parts[third],np.ones(len(parts[third]))].T).T[:,:3]
            dd=distances(parts[a],q);sd=distances(parts[a],u)
            near=dd.min(1);support=sd.min(1)<=.60
            codes=np.where(support & (near<=.30),1,np.where(support & (near>=.60),2,0)).astype(np.int8)
            out[f'positive_{a}{b}']=np.packbits(dd<=.30,axis=1,bitorder='little')
            out[f'class_{a}{b}']=codes;out[f'support_{a}{b}']=support;out[f'minimum_{a}{b}']=near
    raw=np.array([np.linalg.inv(poses[a])@poses[b] for a,b in ((0,1),(0,2),(1,2))])
    angular=raw.copy()
    for T in angular:T[:3,:3]=quaternion_rotation(T[:3,:3].T)[0]
    out.update(raw_truth=raw,angular_truth=angular,lidar_poses=poses)
    return out


def calibration(path):
    for line in path.read_text().splitlines():
        if line.split(':')[0]=='Tr':
            T=np.eye(4);T[:3]=np.fromstring(line.split(':',1)[1],sep=' ').reshape(3,4);return T
    raise ValueError('Missing Tr')


def gt_selected(root,row):
    camera=np.loadtxt(root/'poses'/f"{row['seq']}.txt").reshape(-1,3,4)
    C=calibration(root/'sequences'/row['seq']/'calib.txt')
    poses=[]
    for i in row['ids']:
        P=np.eye(4);P[:3]=camera[i]
        poses.append(np.linalg.inv(C)@P@C)
    return np.array(poses)


def errors(truth,prediction):
    translation=float(np.linalg.norm(prediction[:3,3]-truth[:3,3]))
    R=truth[:3,:3].T@prediction[:3,:3]
    sine=.5*np.linalg.norm([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])
    cosine=.5*(np.trace(R)-1)
    return dict(translation_m=translation,rotation_deg=float(np.degrees(np.arctan2(sine,cosine))))
