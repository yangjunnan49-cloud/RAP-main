"""RLP2 full pose-only targets and independent direction/projection validation."""
import sys
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def freeze():
    r.check(r.FULL);r.check_seal(r.FULL);r.validated(r.FULL)
    r.freeze(r.LAB,r.rows(),__file__,__file__,gt=True,
        extra_files=[r.FULL/x for x in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]+[c.SLAM/'scripts/measured_point_readout.py'],
        supervision='pose_only',positive_row_gates=False)
    r.finish('targets_freeze')

def run():
    from measured_point_readout import poses_from_camera,relative_truth
    f=r.check(r.LAB);(r.LAB/'bank').mkdir();rows=[]
    for row in f['rows']:
        camera=np.loadtxt(c.DATA/'poses'/f"{row['seq']}.txt").reshape(-1,3,4)
        C=np.eye(4)
        for line in (c.DATA/'sequences'/row['seq']/'calib.txt').read_text().splitlines():
            if line.startswith('Tr:'):C[:3]=np.fromstring(line.split(':',1)[1],sep=' ').reshape(3,4)
        selected=np.repeat(np.eye(4)[None],3,0);selected[:,:3]=camera[row['ids']]
        raw,angular=relative_truth(poses_from_camera(selected,C))
        assert np.isfinite(raw).all() and np.isfinite(angular).all()
        np.savez(r.LAB/'bank'/f'{r.stem(row)}.npz',raw_truth=raw,angular_truth=angular)
        rows.append(row);r.cap()
    r.check(r.LAB);c.save(r.LAB/'bank.json',dict(utc=c.now(),rows=rows,pose_only=True,optimizer_updates=0,**r.usage()))
    r.seal(r.LAB);r.finish('targets_bank');print('RLP2 all204 pose targets sealed',flush=True)

def validate():
    import rlp2_independent as v
    f=r.check(r.LAB);r.check_seal(r.LAB);maximum=0.
    for row in f['rows']:
        raw,angular=v.targets(c.DATA,row)
        with np.load(r.LAB/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:
            d=max(float(abs(raw-z['raw_truth']).max()),float(abs(angular-z['angular_truth']).max()))
        maximum=max(maximum,d);assert d<1e-8
    r.pass_validation(r.LAB,dict(decision='PASS_POSE_ONLY_TARGET_BANK',windows=204,maximum_target_delta=maximum,
        physical_GT_verified=False,positive_row_gates=False,**r.usage()))
    r.finish('targets_validation');print('RLP2 targets independently VALIDATED',maximum,flush=True)

if __name__=='__main__':
    try:{'freeze':freeze,'run':run,'validate':validate}[sys.argv[1]]()
    except Exception as ex:r.fail('targets_'+sys.argv[1],ex);raise
