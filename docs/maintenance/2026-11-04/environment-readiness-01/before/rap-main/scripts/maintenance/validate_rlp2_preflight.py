"""Independent quaternion, finite difference, binding and head checks."""
import sys
import numpy as np
import local_motion_common as c
import rlp2_common as r
import rlp2_independent as v

def validate():
    import torch
    from rap_slam.rap_precision import ieee_matmul
    f=r.check(r.NUM);r.check_seal(r.NUM);assert r.runtime()==f['runtime']
    bank=c.read(r.NUM/'bank.json');maximum=0.;fd=0.;ed=0.
    for case in bank['cases']:
        with np.load(r.NUM/'bank'/f"synthetic_{case['name']}.npz",allow_pickle=False) as z:
            if case['rejected']:
                try:v.horn(z['source'],z['target'],z['W'])
                except AssertionError:pass
                else:raise AssertionError('Independent expected rejection absent')
            else:
                pose,gap=v.horn(z['source'],z['target'],z['W'])
                d=float(abs(pose-z['pose']).max());maximum=max(maximum,d);assert d<1e-8
                assert abs(pose-z['expected']).max()<1e-8
    with np.load(r.NUM/'bank/synthetic_gradient.npz',allow_pickle=False) as z:
        for i,j in ((0,0),(1,3),(5,9)):
            losses=[]
            for sign in (-1,1):
                w=z['W'].copy();w[i,j]+=sign*1e-6
                pose,_=v.horn(z['source'],z['target'],w)
                losses.append(np.square(pose[:3,:3]).sum()+np.square(pose[:3,3]).sum())
            actual=(losses[1]-losses[0])/2e-6
            delta=abs(actual-z['gradient'][i,j]);fd=max(fd,float(delta));assert delta<1e-6
    with ieee_matmul():
        for record in bank['real_checks']:
            seed,arm,s,t=(record[k] for k in ('seed','arm','seq','t'))
            with np.load(r.NUM/'bank'/f'initial_{seed}.npz',allow_pickle=False) as zz:
                state={k:torch.tensor(zz[k],device='cuda') for k in zz.files}
            with c.rng(seed):
                h=torch.nn.Linear(521,128);p=torch.nn.Linear(128,64)
            for k,array in {'hidden.weight':h.weight,'hidden.bias':h.bias,'project.weight':p.weight,'project.bias':p.bias}.items():
                assert np.array_equal(state[k].cpu().numpy(),array.detach().numpy())
            with np.load(r.ENG/'bank'/f'{s}_{t:06d}_J.npz',allow_pickle=False) as zz:z={k:zz[k] for k in ('points','features','cond','noise','scale','tokens')}
            if arm=='D':features=z['features'].reshape(3,1000,32)
            elif arm=='J':features=z['tokens']
            else:
                with np.load(r.ENG/'bank'/f'{s}_{t:06d}_I.npz',allow_pickle=False) as zz:features=zz['tokens']
            channels=v.common(z)
            embedding=v.torch_embedding(state,torch.tensor(features,device='cuda'),torch.tensor(channels,device='cuda')).cpu().numpy()
            with np.load(r.NUM/'bank'/f'real_{seed}_{arm}_{s}_{t:06d}.npz',allow_pickle=False) as zz:
                predicted={k:zz[k] for k in zz.files}
            delta=float(abs(embedding[:2]-predicted['embedding']).max());ed=max(ed,delta);assert delta<5e-5
            pose,_=v.reconstruct_encoded(predicted,z['points'].reshape(3,1000,3))
            maximum=max(maximum,float(abs(pose-predicted['pose']).max()))
            assert record['gradient_norm']>0 and np.isfinite(record['gradient_norm']) and len(record['gaps'])==3
    assert len(bank['real_checks'])==18 and bank['optimizer_updates']==0
    r.pass_validation(r.NUM,dict(decision='PASS_MOTION_SUPERVISED_NUMERICAL_PREFLIGHT',synthetic_cases=len(bank['cases']),
        initialized_head_checks=18,maximum_horn_delta=maximum,maximum_embedding_delta=ed,maximum_fd_gradient_delta=fd,
        exact_weight_hash_reconstruction=True,optimizer_updates=0,**r.usage()))
    r.finish('numerical_validation');print('RLP2 numerical preflight independently VALIDATED',maximum,fd,flush=True)

if __name__=='__main__':
    try:validate()
    except Exception as ex:r.fail('numerical_validation',ex);raise
