"""RLP1 separately frozen four-window GT-free context engineering."""
import sys
from pathlib import Path
import numpy as np
import rlp1_attempt03_common as r
import local_motion_common as c


def freeze():
    old=c.check_freeze(r.TR); c.check_seal(r.TR)
    vs=c.read(r.TR/'validation_seal.json')
    assert c.sha(r.TR/'validation.json') == vs['validation_sha256']
    assert c.sha(r.TR/'bank_seal.json') == vs['bank_seal_sha256']
    allrows=r.rows()
    selected=old['rows']
    assert [(x['seq'],x['t']) for x in selected] == [('00',200),('05',200),('06',200),('07',200)]
    extra=[r.TR/n for n in ('freeze.json','bank.json','bank_seal.json','validation.json','validation_seal.json')]
    extra += [r.TR/'bank'/f"{r.stem(x)}_{m}.npz" for x in selected for m in ('N','E','H')]
    r.freeze(r.ENG,selected,__file__,Path(__file__).with_name('validate_rlp1_engineering_v3.py'),
             extra_files=extra+[Path(__file__).with_name('rlp1_attempt03_common.py'),r.B/'AMENDMENT_01.md',r.B/'FAILURE_engineering_bank.json',r.B/'AMENDMENT_02.md',r.B/'FAILURE_engineering_bank_attempt02.json',r.B/'engineering-preflight/attempt-02/freeze.json',r.B/'engineering-preflight/attempt-02/bank/00_000200_J.npz'], full_manifest=allrows, modes=['J','I','R','P'],
             tolerances=dict(exact=0.,horn=1e-8),input_labels_read=False)
    (r.B/'INCOMPLETE').write_text('RLP1 authorized; prerequisite and complete pilot validation pending.\n')
    (r.B/'STATUS.json').write_text(__import__('json').dumps(dict(status='AUTHORIZED_PREFLIGHT_FROZEN',training_authorized=True,training=False),indent=2)+'\n')
    r.finish('engineering_freeze')
    print('RLP1 engineering frozen; full204 manifest also fixed',flush=True)


def bank():
    import torch
    from measured_point_readout import contextual
    from joint_token_extraction import snapshot,same_rng
    f=r.check(r.ENG); assert r.runtime()==f['runtime']
    (r.ENG/'bank').mkdir()
    b,audit=c.make_backend(); torch.cuda.reset_peak_memory_stats()
    records=[]
    for row in f['rows']:
        points,features=c.get_points(b,row)
        bb,scale,centers,counts=c.batch(b,points,features)
        cond=bb['pointclouds'].cpu().numpy()
        with c.rng(row['seed']): noise=torch.randn((3000,3),device='cuda')
        inputs=dict(points=np.concatenate(points),features=np.concatenate(features),
            cond=cond,scale=scale,centers=centers,counts=counts,noise=noise.cpu().numpy(),
            scan_ids=np.array(row['ids']),seed=np.array(row['seed']))
        modes=[]
        for mode in ('J','I','R','P'):
            perturbed=noise.clone()
            if mode=='P': perturbed[2000:]+=1.
            outer=snapshot()
            with c.rng(row['seed']):
                arrays,meta=contextual(b.model,bb,perturbed,independent=mode!='J',hook=True)
            assert same_rng(outer,snapshot())
            assert np.array_equal(arrays['tokens'],arrays['hook_tokens'])
            parts=c.decode(cond,arrays['end_point_trajectory'][-1],centers,counts,scale)
            arrays.update(inputs,parts=parts,pose=np.linalg.inv(parts[0]) @ parts[1],actual_noise=perturbed.cpu().numpy())
            if mode=='J':
                with np.load(r.TR/'bank'/f"{r.stem(row)}_N.npz",allow_pickle=False) as old, \
                     np.load(r.TR/'bank'/f"{r.stem(row)}_E.npz",allow_pickle=False) as old_tokens:
                    for key in ('points','features','cond','scale','centers','counts','noise','parts','pose','trajectory','end_point_trajectory'):
                        assert np.array_equal(arrays[key],old[key]),key
                    assert np.array_equal(arrays['tokens'],old_tokens['tokens'])
            if mode=='I': reference={k:np.asarray(v).copy() for k,v in arrays.items()}
            if mode=='R':
                for key in arrays:
                    assert np.array_equal(arrays[key],reference[key]),key
            if mode=='P':
                for key in ('trajectory','end_point_trajectory','flow_inputs'):
                    assert np.array_equal(arrays[key][:,:2000],reference[key][:,:2000]),key
                assert np.array_equal(arrays['tokens'][:2],reference['tokens'][:2])
            assert all(np.isfinite(v).all() for v in arrays.values())
            np.savez_compressed(r.ENG/'bank'/f"{r.stem(row)}_{mode}.npz",**arrays)
            modes.append(dict(mode=mode,outer_rng_restored=True,**meta))
            r.cap(1200)
        records.append(dict(**row,modes=modes))
        print('RLP1 engineering bank',row['seq'],'J/I/repeat/perturb exact controls',flush=True)
    r.check(r.ENG)
    used=r.cap(1200)
    c.save(r.ENG/'bank.json',dict(utc=c.now(),rows=records,checkpoint=audit,npzs=16,gt_read=False,training=False,**used))
    r.seal(r.ENG); r.finish('engineering_bank')
    print('RLP1 GT-free engineering bank sealed',flush=True)


if __name__=='__main__':
    try: {'freeze':freeze,'bank':bank}[sys.argv[1]]()
    except Exception as ex:
        r.fail('engineering_'+sys.argv[1],ex)
        raise


