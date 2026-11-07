"""Independent RLP2 equations: no readout/runner algorithm imports."""
import hashlib
import numpy as np
from rlp1_validation_math import quaternion_rotation,gt_selected,calibration,errors

def horn(source,target,raw):
    x,y,w=map(lambda a:np.asarray(a,np.float64),(source,target,raw))
    mass=w.sum();assert np.isfinite(mass) and mass>0
    w=w/mass
    ax=np.sum(x*w.sum(0)[:,None],axis=0);ay=np.sum(y*w.sum(1)[:,None],axis=0)
    H=np.einsum('ij,ik,jl->kl',w,(y-ay),(x-ax),optimize=True).T
    R,gap=quaternion_rotation(H);assert gap>1e-6
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=ay-R@ax
    return T,gap

def torch_embedding(state,feature,common):
    import torch
    f=feature/torch.linalg.vector_norm(feature,dim=-1,keepdim=True).clamp_min(1e-8)
    if f.shape[-1]==32:f=torch.cat((f,torch.zeros((*f.shape[:-1],480),device=f.device,dtype=f.dtype)),-1)
    x=torch.cat((f,common),-1)
    h=torch.nn.functional.linear(x,state['hidden.weight'],state['hidden.bias'])
    h=h*torch.sigmoid(h)
    e=torch.nn.functional.linear(h,state['project.weight'],state['project.bias'])
    return e/torch.linalg.vector_norm(e,dim=-1,keepdim=True).clamp_min(1e-8)

def raw_weights(embedding):
    import torch
    s=torch.matmul(embedding[0],embedding[1].transpose(0,1))/.10
    return torch.nn.functional.softmax(s,dim=1)*torch.nn.functional.softmax(s.transpose(0,1),dim=1).transpose(0,1)

def common(z):
    parts=[]
    for p in range(3):
        start=p*1000;end=start+1000
        parts.append(np.column_stack((z['cond'][start:end],z['noise'][start:end],
            np.full(1000,1. if p==0 else 0.,np.float32),
            np.full(1000,np.log(float(z['scale'])),np.float32),np.full(1000,.2,np.float32))))
    return np.stack(parts).astype(np.float32)

def targets(root,row):
    poses=gt_selected(root,row)
    raw=np.array([np.linalg.inv(poses[a])@poses[b] for a,b in ((0,1),(0,2),(1,2))])
    angular=raw.copy()
    for p in angular:p[:3,:3]=quaternion_rotation(p[:3,:3].T)[0]
    return raw,angular

def reconstruct_encoded(z,points):
    import torch
    E=torch.tensor(z['embedding'],device='cuda')
    w=raw_weights(E).cpu().numpy()
    assert hashlib.sha256(w.tobytes()).hexdigest()==str(z['weight_sha256'])
    pose,gap=horn(points[1],points[0],w)
    assert abs(pose-z['pose']).max()<1e-8
    assert abs(gap-float(z['gap']))<1e-10
    wd=w.astype(np.float64);mass=wd.sum();wd/=mass
    assert abs(mass-float(z['mass']))<1e-10
    assert abs(wd.sum(1)-z['marginal_target']).max()<1e-10
    assert abs(wd.sum(0)-z['marginal_source']).max()<1e-10
    return pose,w
