"""Independent numpy/scipy proper-pose and Horn checks for NOC3."""
import math
import numpy as np
from scipy.spatial.transform import Rotation


def poses(physical):
    p=np.asarray(physical).reshape(2,6);T=np.repeat(np.eye(4)[None],3,axis=0)
    T[1:,:3,:3]=Rotation.from_rotvec(p[:,3:]).as_matrix();T[1:,:3,3]=p[:,:3]
    return T
def output(z,physical):
    T=poses(physical);x=z['cond'].astype(np.float64).reshape(3,1000,3)
    b=np.array([(t[:3,:3]@c+t[:3,3]-z['centers'][0])/float(z['scale']) for t,c in zip(T,z['centers'])])
    return (x@T[:,:3,:3].transpose(0,2,1)+b[:,None]).reshape(3000,3)
def horn(x,y):
    x=x.astype(np.float64);y=y.astype(np.float64);a=x.mean(0);b=y.mean(0)
    xx,xy,xz,yx,yy,yz,zx,zy,zz=((x-a).T@(y-b)).ravel()
    K=np.array([[xx+yy+zz,yz-zy,zx-xz,xy-yx],[yz-zy,xx-yy-zz,xy+yx,zx+xz],
        [zx-xz,xy+yx,-xx+yy-zz,yz+zy],[xy-yx,zx+xz,yz+zy,-xx-yy+zz]])
    e,Q=np.linalg.eigh(K);w,i,j,k=Q[:,-1]
    R=np.array([[1-2*(j*j+k*k),2*(i*j-k*w),2*(i*k+j*w)],
        [2*(i*j+k*w),1-2*(i*i+k*k),2*(j*k-i*w)],
        [2*(i*k-j*w),2*(j*k+i*w),1-2*(i*i+j*j)]])
    assert (e[-1]-e[-2])/max(abs(e).max(),1e-12)>1e-6
    return R,b-R@a
def decode(z,q):
    T=np.repeat(np.eye(4)[None],3,axis=0);res=[]
    for k in range(3):
        sl=slice(k*1000,(k+1)*1000);R,b=horn(z['cond'][sl],q[sl]);T[k,:3,:3]=R
        T[k,:3,3]=float(z['scale'])*b-R@z['centers'][k]
        res.append(float(np.mean((float(z['scale'])*(q[sl]-z['cond'][sl]@R.T-b))**2)))
    relative=np.array([np.eye(4)]+[np.linalg.solve(T[0],T[k]) for k in (1,2)])
    return relative,float(np.mean(res))
def cost_from_poses(z,T,shape=0.):
    t=np.mean([np.sum((T[k,:3,3]-z['truth'][k,:3,3])**2)/.05**2 for k in (1,2)])
    R=np.mean([np.sum((z['truth'][k,:3,:3].T@T[k,:3,:3]-np.eye(3))**2)/(2*math.radians(.2)**2) for k in (1,2)])
    return float(t+R+.001*shape/.05**2)
def direct_cost(z,p): return cost_from_poses(z,poses(p))
def gradient(z,p,h=1e-6):
    p=np.asarray(p,np.float64).reshape(2,6);g=np.empty_like(p)
    for k in range(12):
        d=np.zeros_like(p);d.flat[k]=h;g.flat[k]=(direct_cost(z,p+d)-direct_cost(z,p-d))/(2*h)
    return g
def metrics(z,T):
    return [dict(part=k,t_m=float(np.linalg.norm(T[k,:3,3]-z['truth'][k,:3,3])),
        R_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(z['truth'][k,:3,:3].T@T[k,:3,:3]).as_rotvec())))) for k in (1,2)]
def hessian_zero(z,h=1e-4):
    p=np.zeros((2,6));H=np.empty((12,12));f=direct_cost(z,p)
    for i in range(12):
        a=np.zeros_like(p);a.flat[i]=h;H[i,i]=(direct_cost(z,a)-2*f+direct_cost(z,-a))/h**2
        for j in range(i):
            b=np.zeros_like(p);b.flat[j]=h
            H[i,j]=H[j,i]=(direct_cost(z,a+b)-direct_cost(z,a-b)-direct_cost(z,-a+b)+direct_cost(z,-a-b))/(4*h**2)
    return H
