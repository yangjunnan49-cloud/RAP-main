"""Isolated differentiable metric relative-pose objective and affine control."""
import math
import numpy as np
import torch
from torch import nn


def geometry(cond,output,centers,scale):
    x=cond.double().reshape(3,1000,3);y=output.double().reshape(3,1000,3)
    a=x.mean(1);b=y.mean(1);H=(x-a[:,None]).transpose(1,2)@(y-b[:,None])
    u,s,vh=torch.linalg.svd(H)
    assert bool(torch.isfinite(s).all()) and float((s[:,-1].min()/s[:,0].max()).detach())>1e-6
    separation=torch.minimum(s[:,0]-s[:,1],s[:,1]-s[:,2])/s[:,0]
    assert float(separation.min().detach())>1e-6,'SVD derivative singular-value separation'
    sign=torch.linalg.det(vh.transpose(1,2)@u.transpose(1,2))
    D=torch.eye(3,device=x.device,dtype=x.dtype).repeat(3,1,1);D[:,2,2]=torch.where(sign<0,-1.,1.)
    R=vh.transpose(1,2)@D@u.transpose(1,2)
    offset=b-(R@a.unsqueeze(2)).squeeze(2)
    t=scale*offset-(R@centers.double().unsqueeze(2)).squeeze(2)
    relR=R[0].T@R[1:];relt=(R[0].T@(t[1:]-t[0]).T).T
    fit=x@R.transpose(1,2)+offset[:,None]
    shape=(scale*(y-fit)).square().mean()
    return relR,relt,shape,R,t,s,separation


def objective(cond,output,centers,scale,truth):
    R,t,shape,*extra=geometry(cond,output,centers,scale)
    te=((t-truth[1:,:3,3].double())/.05).square().sum(1).mean()
    delta=truth[1:,:3,:3].double().transpose(1,2)@R-torch.eye(3,device=R.device,dtype=R.dtype)
    re=delta.square().sum((1,2)).mean()/(2*math.radians(.2)**2)
    sh=.001*shape/.05**2
    return te+re+sh,dict(translation=te,rotation=re,shape=sh)


class Affine(nn.Module):
    def __init__(self,device='cuda'):
        super().__init__()
        self.matrix=nn.Parameter(torch.eye(3,device=device).repeat(3,1,1))
        self.bias=nn.Parameter(torch.zeros(3,3,device=device))
    def forward(self,cond):
        return (cond.reshape(3,1000,3)@self.matrix.transpose(1,2)+self.bias[:,None]).reshape(3000,3)


def gate(bt,br,at,ar):
    bt,br,at,ar=map(np.asarray,(bt,br,at,ar))
    return {k:bool(v) for k,v in dict(mean_t=at.mean()<=.9*bt.mean(),median_t=np.median(bt-at)>=.005,
        mean_R=ar.mean()<=br.mean()+.01,median_R=np.median(br-ar)>=0,
        joint_signs=np.count_nonzero((at<=bt)&(ar<=br))>=12,
        q90_t=np.quantile(at,.9)<=1.05*np.quantile(bt,.9),
        q90_R=np.quantile(ar,.9)<=np.quantile(br,.9)+.02).items()}
