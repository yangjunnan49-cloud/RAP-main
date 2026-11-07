"""Independent S0 hash, replay-record, ten-state and pose audit (CPU)."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

MAIN=Path(__file__).resolve().parents[2]
BASE=MAIN/'docs/maintenance/2026-09-28/s0-stepcount-preflight-01'
F2=MAIN/'docs/maintenance/2026-09-27/f2-structured-dev-01'
INDICES=(0,25,50,75)

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def decode(cond,raw,counts,centers,scale):
    cuts=np.r_[0,np.cumsum(counts)]
    poses=[]
    for k in (0,3):
        x=torch.from_numpy(cond[cuts[k]:cuts[k+1]].astype(np.float64))
        y=torch.from_numpy(raw[cuts[k]:cuts[k+1]].astype(np.float64))
        xm,ym=x.mean(0),y.mean(0)
        u,_,vt=torch.linalg.svd((x-xm).T@(y-ym))
        d=torch.sign(torch.det(vt.T@u.T))
        r=vt.T@torch.diag(torch.stack([torch.ones_like(d),torch.ones_like(d),d]))@u.T
        t=ym-xm@r.T
        p=np.eye(4);p[:3,:3]=r.numpy();p[:3,3]=scale*t.numpy()-p[:3,:3]@centers[k]
        poses.append(p)
    return np.linalg.inv(poses[0])@poses[1]

def main():
    assert not (BASE/'validation.json').exists() and not (BASE/'INCOMPLETE').exists()
    frozen=read(BASE/'freeze.json')
    checks=0
    for name,digest in frozen['files'].items():
        assert sha(Path(name))==digest,name
        checks+=1
    bank=read(BASE/'bank.json')
    seal=read(BASE/'bank_seal.json')
    assert sha(BASE/'bank.json')==seal['sha256'] and len(bank)==8
    assert seal['wall_s']<=600 and seal['peak_allocated_gib']<=12
    assert seal['artifact_bytes']<=2**30
    expected=[]
    for seq in ('00','08'):
        records=read(F2/seq/'records.json')
        pairs=list(dict.fromkeys(r['pair'] for r in records if r['arm']=='N'))
        assert len(pairs)==100
        expected += [pairs[i] for i in INDICES]
    assert frozen['pairs']=={'00':expected[:4],'08':expected[4:]}
    assert [r['pair'] for r in bank]==expected
    checks+=5
    for r in bank:
        seq,pair=r['sequence'],r['pair']
        assert pair.startswith(seq+'_')
        source={x['key']:x for x in read(F2/f'inputs_{seq}.json')}[pair]
        assert r['seed']==source['seeds'][0]
        assert r['five_raw_max_delta']<=1e-5 and r['five_state_max_delta']<=1e-5
        assert r['ten_valid'] and r['wall_s']>=0
        path=BASE/f'{pair}.npz'
        assert sha(path)==r['artifact_sha256']
        with np.load(path,allow_pickle=False) as z:
            raw=z['end_point_trajectory'];state=z['trajectory'];pose=z['T']
            counts=z['counts'];centers=z['centers'];scale=float(z['scale'])
        assert raw.shape==state.shape==(10,8000,3)
        assert np.isfinite(raw).all() and np.isfinite(state).all()
        assert counts.tolist()==[2000,1000,1000,2000,1000,1000]
        assert centers.shape==(6,3) and np.isfinite(centers).all() and scale>0
        with np.load(F2/seq/pair/'inputs.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(counts,z['counts'])
            np.testing.assert_array_equal(centers,z['centers'])
            assert scale==float(z['scale'])
            cond=z['cond']
            assert cond.shape==(8000,3) and z['noise'][0].shape==(8000,3)
        expected_pose=decode(cond,raw[-1],counts,centers,scale)
        np.testing.assert_allclose(pose,expected_pose,atol=1e-4,rtol=0)
        np.testing.assert_allclose(r['T'],pose,atol=1e-10,rtol=0)
        assert np.max(np.abs(pose[:3,:3].T@pose[:3,:3]-np.eye(3)))<1e-4
        assert abs(np.linalg.det(pose[:3,:3])-1)<1e-4
        checks+=11
    result={'passed':True,'decision':'PASS_STEPCOUNT_PREFLIGHT','checks':checks,
            'pairs':expected,'bank_sha256':seal['sha256']}
    with (BASE/'validation.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print('S0 validation passed',checks,'checks',flush=True)

if __name__=='__main__': main()
