"""Fixed-pair, same-input/noise RAP five versus ten step engineering preflight."""

from __future__ import annotations
import json
import os
import random
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
import global_proposal_baseline as g0
import fullscan_global_baseline as g1

MAIN,F2=g0.MAIN,g0.F2
BASE=MAIN/'docs/maintenance/2026-09-28/s0-stepcount-preflight-01'
RAP=MAIN.parent/'RAP-SLAM'
INDICES=(0,25,50,75)
CAPS=(2000,1000,1000,2000,1000,1000)


def selected():
    return {seq:[g0.order(seq)[i] for i in INDICES] for seq in ('00','08')}


def frozen_files():
    files=[BASE/'PROTOCOL.md',Path(__file__).resolve(),
           MAIN/'scripts/maintenance/validate_s0_stepcount_preflight.py',
           MAIN/'config/RAP_inference.yaml',MAIN/'demo.py',
           MAIN/'rectified_point_flow/modeling.py',MAIN/'rectified_point_flow/sampler.py',
           MAIN/'rectified_point_flow/procrustes.py',
           RAP/'rap_slam/rap_backend.py',RAP/'rap_slam/structured_motion.py',
           RAP/'rap_slam/real_dataset.py',RAP/'rap_slam/rap_precision.py',
           RAP/'scripts/hl0_preflight.py',F2/'validation.json',F2/'freeze.json',
           MAIN/'weights/rap_model_12.ckpt',MAIN/'weights/mini_spinnet_t.pth']
    files += list((MAIN/'rectified_point_flow').rglob('*.py'))
    files += list((MAIN/'dataset_process').rglob('*.py'))
    files += list((MAIN/'config').rglob('*.yaml'))
    for seq,pairs in selected().items():
        files += [F2/f'inputs_{seq}.json']
        rows={r['key']:r for r in g0.read(F2/f'inputs_{seq}.json')}
        for pair in pairs:
            folder=F2/seq/pair
            files += [folder/'inputs.npz',folder/'N0.npz']
            files.extend(Path(e['path']) for e in rows[pair]['scans'])
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE/'freeze.json').exists()
    assert g0.read(F2/'validation.json')['passed']
    files=frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE/'freeze.json',{'utc':datetime.now(timezone.utc).isoformat(),
        'pairs':selected(),'files':{str(p):g0.sha(p) for p in files}})
    print('S0 frozen',len(files),'files',flush=True)


def verify():
    frozen=g0.read(BASE/'freeze.json')
    assert frozen['pairs']==selected()
    for name,digest in frozen['files'].items():
        assert g0.sha(Path(name))==digest,name


def run():
    import torch
    sys.path[:0]=[str(RAP),str(RAP/'scripts')]
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.rap_precision import ieee_matmul
    from rap_slam.structured_motion import build_batch,decode_parts
    from rap_slam.measurement import rotation_validity
    from hl0_preflight import request_rng
    verify()
    assert os.environ.get('OMP_NUM_THREADS')=='1' and os.environ.get('OPENBLAS_NUM_THREADS')=='1'
    assert torch.cuda.is_available()
    (BASE/'INCOMPLETE').write_text('S0 native sampler preflight started\n',encoding='utf-8')
    start=time.monotonic()
    b=RAPBackend()
    assert b.device.type=='cuda' and b.model.inference_sampling_steps==5
    assert b.model.inference_sampler=='euler' and b.model.rigidity_forcing
    torch.cuda.reset_peak_memory_stats()
    rows=[]

    def state():
        return (torch.get_rng_state().clone(),torch.cuda.get_rng_state().clone(),
                random.getstate(),np.random.get_state(),b.seed,
                torch.get_float32_matmul_precision())

    def same(a,c):
        assert torch.equal(a[0],c[0]) and torch.equal(a[1],c[1]) and a[2]==c[2]
        assert a[3][0]==c[3][0] and np.array_equal(a[3][1],c[3][1]) and a[3][2:]==c[3][2:]
        assert a[4:]==c[4:]

    for seq,pairs in selected().items():
        inputs={r['key']:r for r in g0.read(F2/f'inputs_{seq}.json')}
        for pair in pairs:
            t0=time.monotonic()
            r=inputs[pair]
            assert len(r['scans'])==6 and len(r['seeds'])==4
            scans=[]
            for e in r['scans']:
                path=Path(e['path'])
                assert g0.sha(path)==e['sha256']
                scans.append(g1.load_scan(path))
            before=state()
            with request_rng(r['seeds'][0],b),ieee_matmul(),torch.inference_mode():
                b.seed=42
                points,features=[],[]
                for scan,cap in zip(scans,CAPS):
                    p,f=b.preprocess(scan,max_points=cap)
                    assert len(p)==cap and np.isfinite(f).all() and np.any(f)
                    points.append(p);features.append(f)
            same(before,state())
            batch,scale,centers,counts=build_batch(b,points,features)
            with np.load(F2/seq/pair/'inputs.npz',allow_pickle=False) as z:
                assert np.array_equal(np.concatenate(points),z['points'])
                assert np.array_equal(counts,z['counts'])
                assert np.array_equal(batch['pointclouds'].cpu().numpy(),z['cond'])
                assert np.array_equal(centers,z['centers']) and scale==float(z['scale'])
                noise=torch.from_numpy(z['noise'][0]).to(b.device)
            with np.load(F2/seq/pair/'N0.npz',allow_pickle=False) as z:
                saved_raw=z['end_point_trajectory']
                saved_state=z['trajectory']
            before=state()
            with request_rng(r['seeds'][0],b),ieee_matmul(),torch.inference_mode(),\
                 torch.autocast(device_type='cuda',dtype=torch.float16):
                five=b.model.sample_rectified_flow(batch,None,x_1=noise,return_tarjectory=True)
            torch.cuda.synchronize()
            same(before,state())
            five_raw=five['end_point_trajectory'].detach().float().cpu().numpy()
            five_state=five['trajectory'].detach().float().cpu().numpy()
            assert five_raw.shape==saved_raw.shape==(5,8000,3)
            delta_raw=float(np.max(np.abs(five_raw-saved_raw)))
            delta_state=float(np.max(np.abs(five_state-saved_state)))
            assert max(delta_raw,delta_state)<=1e-5,(pair,delta_raw,delta_state)
            before=state()
            try:
                b.model.inference_sampling_steps=10
                with request_rng(r['seeds'][0],b),ieee_matmul(),torch.inference_mode(),\
                     torch.autocast(device_type='cuda',dtype=torch.float16):
                    ten=b.model.sample_rectified_flow(batch,None,x_1=noise,return_tarjectory=True)
            finally:
                b.model.inference_sampling_steps=5
            torch.cuda.synchronize()
            same(before,state())
            raw=ten['end_point_trajectory'].detach().float().cpu().numpy()
            state10=ten['trajectory'].detach().float().cpu().numpy()
            assert raw.shape==state10.shape==(10,8000,3)
            assert np.isfinite(raw).all() and np.isfinite(state10).all()
            with ieee_matmul(),torch.inference_mode():
                parts=decode_parts(batch,ten['end_point_trajectory'][-1],centers,scale)
            pose=np.linalg.inv(parts[0])@parts[3]
            assert rotation_validity(pose)['valid']
            dest=BASE/f'{pair}.npz'
            assert not dest.exists()
            np.savez_compressed(dest,end_point_trajectory=raw,trajectory=state10,
                                T=pose,counts=counts,centers=centers,scale=scale)
            rows.append({'sequence':seq,'pair':pair,'seed':r['seeds'][0],
                         'five_raw_max_delta':delta_raw,'five_state_max_delta':delta_state,
                         'ten_valid':True,'T':pose.tolist(),'artifact_sha256':g0.sha(dest),
                         'wall_s':time.monotonic()-t0})
            print('S0',pair,'five delta',max(delta_raw,delta_state),
                  'elapsed',round(time.monotonic()-start,1),flush=True)
            assert time.monotonic()-start<=600
            assert torch.cuda.max_memory_allocated()<=12*2**30
            assert sum(p.stat().st_size for p in BASE.glob('*.npz'))<=2**30
    g0.save_new(BASE/'bank.json',rows)
    g0.save_new(BASE/'bank_seal.json',{'sha256':g0.sha(BASE/'bank.json'),
        'utc':datetime.now(timezone.utc).isoformat(),'wall_s':time.monotonic()-start,
        'peak_allocated_gib':torch.cuda.max_memory_allocated()/2**30,
        'artifact_bytes':sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())})
    print('S0 bank sealed',flush=True)


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
