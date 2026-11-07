"""RLP2 complete fixed GT-free feature/native-binding/reference bank."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def freeze():
    r.check(r.NUM);r.check_seal(r.NUM);r.validated(r.NUM)
    selected=r.rows();assert selected==c.read(r.NUM/'freeze.json')['full_manifest']
    extra=[r.NUM/x for x in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [c.SLAM/'scripts/measured_point_readout.py',
        Path(__file__).with_name('validate_local_motion_source_binding.py'),
        Path(__file__).with_name('validate_local_motion_feasibility_v2.py')]
    r.freeze(r.FULL,selected,__file__,Path(__file__).with_name('validate_rlp2_full_bank.py'),
        extra_files=extra,references=True,gt_read=False,flow_calls=204*2*5)
    r.finish('full_bank_freeze');print('RLP2 complete204 bank frozen',flush=True)

def run():
    import torch
    from measured_point_readout import contextual
    from joint_token_extraction import snapshot,same_rng
    f=r.check(r.FULL);assert r.runtime()==f['runtime'];(r.FULL/'bank').mkdir()
    backend,audit=c.make_backend();torch.cuda.reset_peak_memory_stats();records=[]
    od={s:np.loadtxt(c.source(s)/'odom_poses.txt').reshape(-1,3,4) for s in ('07','09','10')}
    for ix,row in enumerate(f['rows']):
        points,features=c.get_points(backend,row);batch,scale,centers,counts=c.batch(backend,points,features)
        cond=batch['pointclouds'].cpu().numpy()
        with c.rng(row['seed']):noise=torch.randn((3000,3),device='cuda')
        z=dict(points=np.concatenate(points),features=np.concatenate(features),cond=cond,scale=scale,
            centers=centers,counts=counts,noise=noise.cpu().numpy(),scan_ids=np.array(row['ids']),seed=np.array(row['seed']))
        modes=[]
        for arm in ('J','I'):
            outer=snapshot()
            with c.rng(row['seed']):arrays,meta=contextual(backend.model,batch,noise,independent=arm=='I',hook=True)
            assert same_rng(outer,snapshot()) and np.array_equal(arrays['tokens'],arrays['hook_tokens'])
            parts=c.decode(cond,arrays['end_point_trajectory'][-1],centers,counts,scale)
            z.update({arm+'_'+key:value for key,value in arrays.items() if key!='hook_tokens'})
            z[arm+'_parts']=parts;z[arm+'_pose']=np.linalg.inv(parts[0])@parts[1]
            modes.append(dict(arm=arm,passive_token_equal=True,outer_rng_restored=True,**meta))
        trace=None
        if row['role']=='exposed_evaluation':
            poses,trace=c.geometric(points)
            z.update({name+'_pose':pose for name,pose in poses.items()})
            if row['seq'] in od:
                a,b=np.eye(4),np.eye(4);a[:3]=od[row['seq']][row['t']-1];b[:3]=od[row['seq']][row['t']]
                z['KISS_pose']=np.linalg.inv(a)@b
        assert all(np.isfinite(value).all() for value in z.values())
        np.savez(r.FULL/'bank'/f'{r.stem(row)}.npz',**z)
        records.append(dict(**row,modes=modes,icp_trace=trace))
        r.cap(1200)
        if ix%12==0 or ix==203:print('RLP2 full bank',ix+1,'/204',row['seq'],flush=True)
    r.check(r.FULL)
    c.save(r.FULL/'bank.json',dict(utc=c.now(),rows=records,checkpoint=audit,npzs=204,gt_read=False,training=False,**r.usage()))
    r.seal(r.FULL);r.finish('full_bank');print('RLP2 complete GT-free bank sealed',flush=True)

if __name__=='__main__':
    try:{'freeze':freeze,'run':run}[sys.argv[1]]()
    except Exception as ex:r.fail('full_bank_'+sys.argv[1],ex);raise
