"""NOC3 float64 fixed-anchor proper poses, physical units and loss routes."""
import math
import numpy as np
import torch
import native_pose_objective as old

CASES=('RAW_DIRECT','RAW_DECODE','SCALED_DIRECT','SCALED_DECODE')
SETTINGS=dict(lr=1.,max_iter=20,max_eval=40,history_size=10,tolerance_grad=1e-9,tolerance_change=1e-14,line_search_fn='strong_wolfe')


def units(name):
    d=[.05,.05,.05,math.radians(.2),math.radians(.2),math.radians(.2)] if name.startswith('SCALED') else [1.]*6
    return torch.tensor(d,dtype=torch.float64).repeat(2,1)
def rotation(w):
    a,b,c=w.unbind(-1);zero=a*0
    H=torch.stack([zero,-c,b,c,zero,-a,-b,a,zero],-1).reshape(-1,3,3)
    return torch.matrix_exp(H)
def poses(physical):
    p=physical.reshape(2,6);I=torch.eye(3,dtype=torch.float64)
    return torch.cat((I[None],rotation(p[:,3:])),0),torch.cat((torch.zeros(1,3,dtype=torch.float64),p[:,:3]),0)
def endpoints(z,physical):
    R,t=poses(physical);cond=torch.tensor(z['cond'],dtype=torch.float64).reshape(3,1000,3)
    centers=torch.tensor(z['centers'],dtype=torch.float64);scale=float(z['scale'])
    bias=((R@centers.unsqueeze(2)).squeeze(2)+t-centers[0])/scale
    return (cond@R.transpose(1,2)+bias[:,None]).reshape(3000,3)
def cost(z,physical,route):
    if route=='DECODE':
        return old.objective(torch.tensor(z['cond']),endpoints(z,physical),torch.tensor(z['centers']),
            torch.tensor(z['scale']),torch.tensor(z['truth']))[0]
    R,t=poses(physical);truth=torch.tensor(z['truth'],dtype=torch.float64)
    te=((t[1:]-truth[1:,:3,3])/.05).square().sum(1).mean()
    delta=truth[1:,:3,:3].transpose(1,2)@R[1:]-torch.eye(3,dtype=torch.float64)
    re=delta.square().sum((1,2)).mean()/(2*math.radians(.2)**2)
    return te+re
def physical_reference(z):
    from scipy.spatial.transform import Rotation
    return np.concatenate((z['truth'][1:,:3,3],Rotation.from_matrix(z['truth'][1:,:3,:3]).as_rotvec()),1)
def optimizer_state(opt,u):
    def convert(x):
        if torch.is_tensor(x): return x.detach().numpy().tolist()
        if isinstance(x,(list,tuple)): return [convert(v) for v in x]
        if isinstance(x,dict): return {k:convert(v) for k,v in x.items()}
        if isinstance(x,np.generic): return x.item()
        return x
    return convert(opt.state[u])
def solve(z,name,monitor=lambda:None):
    u=torch.nn.Parameter(torch.zeros(2,6,dtype=torch.float64));d=units(name);route=name.split('_')[1]
    opt=torch.optim.LBFGS([u],**SETTINGS);trace=[]
    def closure():
        assert len(trace)<40,'NOC3 declared closure-evaluation ceiling'
        opt.zero_grad(set_to_none=True);loss=cost(z,u*d,route);loss.backward()
        assert bool(torch.isfinite(loss)) and bool(torch.isfinite(u.grad).all())
        trace.append(dict(solver=u.detach().numpy().copy(),physical=(u*d).detach().numpy().copy(),
            cost=float(loss.detach()),gradient=u.grad.detach().numpy().copy()))
        monitor();return loss
    opt.step(closure)
    loss=cost(z,u*d,route);grad=torch.autograd.grad(loss,u)[0];physical=(u*d).detach()
    R,t=poses(physical);q=endpoints(z,physical)
    arrays=dict(trace_solver=np.stack([x['solver'] for x in trace]),trace_physical=np.stack([x['physical'] for x in trace]),
        trace_cost=np.array([x['cost'] for x in trace]),trace_gradient=np.stack([x['gradient'] for x in trace]),
        final_solver=u.detach().numpy(),final_physical=physical.numpy(),final_cost=np.array(float(loss.detach())),
        final_gradient=grad.detach().numpy(),final_rotations=R.detach().numpy(),final_translations=t.detach().numpy(),
        final_output=q.detach().numpy(),units=d.numpy())
    return arrays,optimizer_state(opt,u)
