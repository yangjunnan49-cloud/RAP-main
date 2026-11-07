"""RLP2 sealed continuous-pose predictions and independent reconstruction."""
import sys
import hashlib
from pathlib import Path
import numpy as np
import local_motion_common as c
import rlp2_common as r

def base(mode):return r.PRED if mode=='primary' else r.DIAG

def load(row,arm,independent=False,permuted=False):
    import torch
    with np.load(r.FULL/'bank'/f'{r.stem(row)}.npz',allow_pickle=False) as z:
        small={k:z[k] for k in ('points','cond','noise','scale')}
        feature=z['features'].reshape(3,1000,32) if arm=='D' else z[arm+'_tokens']
    if permuted:feature=np.roll(feature,137,axis=1)
    if independent:
        from rlp2_independent import common
    else:
        from motion_supervised_readout import common
    return tuple(torch.tensor(a,device='cuda') for a in (feature,common(small),small['points'].reshape(3,1000,3)))

def freeze(mode):
    selected=[x for x in r.rows() if x['role']=='exposed_evaluation']
    extra=[r.FULL/name for name in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [r.FULL/'bank'/f'{r.stem(x)}.npz' for x in selected]
    for seed in r.SEEDS:
        for arm in ('D','I','J'):
            fit=r.FIT/f'{seed}_{arm}';r.check(fit);r.check_seal(fit);r.validated(fit)
            extra += [fit/name for name in ('freeze.json','bank_seal.json','validation.json','validation_seal.json','bank/final.npz')]
    if mode=='permuted':
        r.check(r.PRED);r.check_seal(r.PRED);r.validated(r.PRED)
        extra += [r.PRED/name for name in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    r.freeze(base(mode),selected,__file__,__file__,extra_files=extra,mode=mode,
        predictions=432 if mode=='primary' else 144,GT_read=False)
    r.finish(mode+'_predictions_freeze')

def run(mode):
    import torch
    from rap_slam.rap_precision import ieee_matmul
    from motion_supervised_readout import Readout,encode_prediction,weights
    folder=base(mode);f=r.check(folder);assert r.runtime()==f['runtime'];(folder/'bank').mkdir()
    records=[];torch.cuda.reset_peak_memory_stats()
    with ieee_matmul():
        for seed in r.SEEDS:
            for arm in (('D','I','J') if mode=='primary' else ('J',)):
                head=Readout().cuda()
                with np.load(r.FIT/f'{seed}_{arm}/bank/final.npz',allow_pickle=False) as z:
                    head.load_state_dict({k:torch.tensor(z[k],device='cuda') for k in z.files},strict=True)
                for row in f['rows']:
                    feature,channels,points=load(row,arm,permuted=mode!='primary')
                    try:
                        z=encode_prediction(head,feature,channels,points);z.update(valid=np.array(True),reason=np.array(''))
                    except ValueError as ex:
                        with torch.no_grad():e=head(feature,channels);w=weights(e[0],e[1]).cpu().numpy()
                        z=dict(embedding=e[:2].cpu().numpy(),weight_sha256=np.array(hashlib.sha256(w.tobytes()).hexdigest()),
                            valid=np.array(False),reason=np.array(str(ex)))
                    np.savez(folder/'bank'/f'{seed}_{arm}_{r.stem(row)}.npz',**z)
                    records.append(dict(seed=seed,arm=arm,seq=row['seq'],t=row['t'],valid=bool(z['valid']),reason=str(z['reason'])))
                    r.cap()
                print('RLP2 predictions sealed rows prepared',mode,seed,arm,flush=True)
    r.check(folder);c.save(folder/'bank.json',dict(utc=c.now(),mode=mode,records=records,GT_read=False,
        valid=sum(x['valid'] for x in records),total=len(records),**r.usage()))
    r.seal(folder);r.finish(mode+'_predictions');print('RLP2 prediction bank sealed',mode,flush=True)

def validate(mode):
    import torch
    from rap_slam.rap_precision import ieee_matmul
    import rlp2_independent as v
    folder=base(mode);f=r.check(folder);r.check_seal(folder);assert r.runtime()==f['runtime']
    bank=c.read(folder/'bank.json');ed=0.;wd=0.;pd=0.;valid=0
    with ieee_matmul():
        for seed in r.SEEDS:
            for arm in (('D','I','J') if mode=='primary' else ('J',)):
                with np.load(r.FIT/f'{seed}_{arm}/bank/final.npz',allow_pickle=False) as z:
                    state={k:torch.tensor(z[k],device='cuda') for k in z.files}
                for row in f['rows']:
                    feature,channels,points=load(row,arm,independent=True,permuted=mode!='primary')
                    with torch.no_grad():E=v.torch_embedding(state,feature,channels)
                    with np.load(folder/'bank'/f'{seed}_{arm}_{r.stem(row)}.npz',allow_pickle=False) as zz:z={k:zz[k] for k in zz.files}
                    d=float(abs(E[:2].cpu().numpy()-z['embedding']).max());ed=max(ed,d);assert d<5e-5
                    expected=v.raw_weights(E[:2]).cpu().numpy()
                    if bool(z['valid']):
                        pose,w=v.reconstruct_encoded(z,points.cpu().numpy())
                        d=float(abs(w-expected).max());wd=max(wd,d);assert d<5e-5
                        pd=max(pd,float(abs(pose-z['pose']).max()));valid+=1
                    else:
                        w=v.raw_weights(torch.tensor(z['embedding'],device='cuda')).cpu().numpy()
                        assert hashlib.sha256(w.tobytes()).hexdigest()==str(z['weight_sha256'])
                        try:v.horn(points[1].cpu().numpy(),points[0].cpu().numpy(),w)
                        except AssertionError:pass
                        else:raise AssertionError('Saved invalid pose independently valid')
                    r.cap()
                print('RLP2 independent predictions',mode,seed,arm,flush=True)
    expected_count=432 if mode=='primary' else 144
    assert len(bank['records'])==expected_count and bank['valid']==valid
    r.pass_validation(folder,dict(decision='PASS_SEALED_CONTINUOUS_PREDICTIONS',total=expected_count,valid=valid,
        exact_all_weight_hashes=True,max_embedding_delta=ed,max_weight_delta=wd,max_pose_delta=pd,GT_read=False,**r.usage()))
    r.finish(mode+'_predictions_validation');print('RLP2 predictions independently VALIDATED',mode,valid,flush=True)

if __name__=='__main__':
    action,mode=sys.argv[1:3]
    try:{'freeze':freeze,'run':run,'validate':validate}[action](mode)
    except Exception as ex:r.fail(mode+'_predictions_'+action,ex);raise
