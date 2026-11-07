"""Independent fixed-fit replay equations; no algorithm readout imports."""
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from rlp1_validation_math import quaternion_rotation

class IndependentHead(nn.Module):
    def __init__(self):
        super().__init__();self.hidden=nn.Linear(521,128);self.project=nn.Linear(128,64)
    def forward(self,feature,common):
        f=F.normalize(feature,dim=-1,eps=1e-8)
        if f.shape[-1]==32:f=F.pad(f,(0,480))
        h=F.silu(F.linear(torch.cat((f,common),-1),self.hidden.weight,self.hidden.bias))
        e=F.linear(h,self.project.weight,self.project.bias)
        return F.normalize(e,dim=-1,eps=1e-8)

def loss(head,feature,channels,points,truth):
    E=head(feature,channels);terms=[];gaps=[]
    for k,(a,b) in enumerate(((0,1),(0,2),(1,2))):
        s=E[a]@E[b].T/.10
        w=(F.softmax(s,dim=1)*F.softmax(s.T,dim=1).T).double()
        mass=w.sum();assert torch.isfinite(mass) and float(mass.detach())>0;w=w/mass
        x,y=points[b].double(),points[a].double()
        cx=w.sum(0)@x;cy=w.sum(1)@y
        H=(x-cx).T@w.T@(y-cy)
        _,gap=quaternion_rotation(H.detach().cpu().numpy());assert gap>1e-6
        u,_,vh=torch.linalg.svd(H);sgn=torch.linalg.det(vh.T@u.T)
        R=vh.T@torch.diag(torch.stack((sgn*0+1,sgn*0+1,sgn)))@u.T;t=cy-R@cx
        td=torch.linalg.vector_norm(t-truth[k,:3,3])/.20
        rd=torch.linalg.matrix_norm(R-truth[k,:3,:3])/(np.sqrt(2.)*np.deg2rad(.2))
        terms.append(F.huber_loss(td,torch.zeros_like(td),delta=1.)+F.huber_loss(rd,torch.zeros_like(rd),delta=1.))
        gaps.append(gap)
    return torch.stack(terms).mean(),dict(pair_losses=[float(v.detach()) for v in terms],gaps=gaps)
