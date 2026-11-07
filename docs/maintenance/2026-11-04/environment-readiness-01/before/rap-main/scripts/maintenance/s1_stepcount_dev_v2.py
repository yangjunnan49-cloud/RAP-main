"""Frozen full-cohort native RAP ten-step development screen."""

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
import v0_ray_visibility as v0
import s0_stepcount_preflight as s0

MAIN,F2,GT=g0.MAIN,g0.F2,g0.GT
BASE=MAIN/'docs/maintenance/2026-09-28/s1-stepcount-dev-01'
RAP=MAIN.parent/'RAP-SLAM'
CAPS=(2000,1000,1000,2000,1000,1000)


def verify_amendment():
    for name,digest in g0.read(BASE/'amendment_freeze.json')['files'].items():
        assert g0.sha(Path(name))==digest,name


def frozen_files():
    files=[BASE/'PROTOCOL.md',Path(__file__).resolve(),
           MAIN/'scripts/maintenance/validate_s1_stepcount_dev.py',
           MAIN/'scripts/maintenance/s0_stepcount_preflight.py',
           MAIN/'docs/maintenance/2026-09-28/s0-stepcount-preflight-01/validation.json',
           MAIN/'docs/maintenance/2026-09-28/s0-stepcount-preflight-01/bank_seal.json',
           F2/'validation.json',F2/'freeze.json',
           MAIN/'weights/rap_model_12.ckpt',MAIN/'weights/mini_spinnet_t.pth',
           RAP/'rap_slam/rap_backend.py',RAP/'rap_slam/structured_motion.py',
           RAP/'rap_slam/real_dataset.py',RAP/'rap_slam/rap_precision.py',
           RAP/'scripts/hl0_preflight.py']
    files += list((MAIN/'rectified_point_flow').rglob('*.py'))
    files += list((MAIN/'dataset_process').rglob('*.py'))
    files += list((MAIN/'config').rglob('*.yaml'))
    for seq in ('00','08'):
        files += [F2/f'inputs_{seq}.json',F2/seq/'records.json',F2/seq/'gates.json',
                  F2/seq/'evaluator_only_decisions.json',GT[seq]]
        inputs={r['key']:r for r in g0.read(F2/f'inputs_{seq}.json')}
        for pair in g0.order(seq):
            files.append(F2/seq/pair/'inputs.npz')
            files.extend(Path(e['path']) for e in inputs[pair]['scans'])
    return list(dict.fromkeys(files))


def freeze():
    assert not (BASE/'freeze.json').exists()
    assert g0.read(F2/'validation.json')['passed']
    assert g0.read(MAIN/'docs/maintenance/2026-09-28/s0-stepcount-preflight-01/validation.json')['passed']
    files=frozen_files()
    assert all(p.is_file() for p in files)
    g0.save_new(BASE/'freeze.json',{'utc':datetime.now(timezone.utc).isoformat(),
        'pairs':{seq:g0.order(seq) for seq in ('00','08')},
        'files':{str(p):g0.sha(p) for p in files}})
    print('S1 frozen',len(files),'files',flush=True)


def verify():
    f=g0.read(BASE/'freeze.json')
    assert f['pairs']=={seq:g0.order(seq) for seq in ('00','08')}
    for name,digest in f['files'].items():
        assert g0.sha(Path(name))==digest,name


def run():
    import torch
    sys.path[:0]=[str(MAIN),str(RAP),str(RAP/'scripts')]
    from rap_slam.rap_backend import RAPBackend
    from rap_slam.rap_precision import ieee_matmul
    from rap_slam.structured_motion import build_batch,decode_parts
    from rap_slam.measurement import rotation_validity
    from hl0_preflight import request_rng
    from rectified_point_flow.procrustes import fit_transformations
    from rectified_point_flow.eval.metrics import compute_rigidity_rmse
    verify()
    verify_amendment()
    assert os.environ.get('OMP_NUM_THREADS')=='1' and os.environ.get('OPENBLAS_NUM_THREADS')=='1'
    assert torch.cuda.is_available()
    (BASE/'INCOMPLETE').write_text('S1 ten-step bank started\n',encoding='utf-8')
    start=time.monotonic()
    b=RAPBackend()
    assert b.device.type=='cuda' and b.model.inference_sampling_steps==5
    assert b.model.inference_sampler=='euler' and b.model.rigidity_forcing
    g=v0.gate_backend()
    torch.cuda.reset_peak_memory_stats()
    bank=[]

    def state():
        return (torch.get_rng_state().clone(),torch.cuda.get_rng_state().clone(),
                random.getstate(),np.random.get_state(),b.seed,torch.get_float32_matmul_precision())

    def same(a,c):
        assert torch.equal(a[0],c[0]) and torch.equal(a[1],c[1]) and a[2]==c[2]
        assert a[3][0]==c[3][0] and np.array_equal(a[3][1],c[3][1]) and a[3][2:]==c[3][2:]
        assert a[4:]==c[4:]

    for seq in ('00','08'):
        inputs={r['key']:r for r in g0.read(F2/f'inputs_{seq}.json')}
        old_records=g0.read(F2/seq/'records.json')
        old_gates=g0.read(F2/seq/'gates.json')
        for ix,pair in enumerate(g0.order(seq)):
            row=inputs[pair]
            dest=BASE/seq/pair
            dest.mkdir(parents=True,exist_ok=False)
            scans=[]
            for e in row['scans']:
                path=Path(e['path'])
                assert g0.sha(path)==e['sha256']
                scans.append(g1.load_scan(path))
            before=state()
            with request_rng(row['seeds'][0],b),ieee_matmul(),torch.inference_mode():
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
                noises=torch.from_numpy(z['noise']).to(b.device)
            anchor_t=g.preprocess(scans[0])[0]
            anchor_s=g.preprocess(scans[3])[0]
            old=[r for r in old_records if r['pair']==pair and r['arm']=='N']
            assert len(old)==4 and all(r['valid'] for r in old)
            old_selected=min(old,key=lambda r:(r['rigidity_rmse_m'],r['generation']))
            ref=g._alignment_metrics(anchor_t,anchor_s,np.asarray(old_selected['T']),thresh=1.)
            saved=old_gates[pair]['N'][str(old_selected['generation'])]
            assert abs(ref[0]-saved['overlap_ratio'])<=1e-5 and abs(ref[1]-saved['mean_dist'])<=1e-5
            generations=[]
            for k in range(4):
                t0=time.monotonic()
                before=state()
                try:
                    b.model.inference_sampling_steps=10
                    with request_rng(row['seeds'][k],b),ieee_matmul(),torch.inference_mode(),\
                         torch.autocast(device_type='cuda',dtype=torch.float16):
                        result=b.model.sample_rectified_flow(batch,None,x_1=noises[k],return_tarjectory=True)
                finally:
                    b.model.inference_sampling_steps=5
                torch.cuda.synchronize()
                same(before,state())
                raw=result['end_point_trajectory']
                assert raw.shape==(10,8000,3) and torch.isfinite(raw).all()
                rigidity=[]
                with ieee_matmul(),torch.inference_mode(),torch.autocast(device_type='cuda',enabled=False):
                    cu=batch['cu_seqlens'].to(torch.int32)
                    for pred in raw.float():
                        rot,trans=fit_transformations(batch['pointclouds'],pred,batch['points_per_part'],cu)
                        val=compute_rigidity_rmse(batch['pointclouds'],pred,rot,trans,
                            batch['points_per_part'],cu,batch['scales'])
                        rigidity.append(float(val.item()))
                    parts=decode_parts(batch,raw[-1],centers,scale)
                pose=np.linalg.inv(parts[0])@parts[3]
                assert rotation_validity(pose)['valid'] and np.isfinite(rigidity).all()
                overlap,mean_dist=g._alignment_metrics(anchor_t,anchor_s,pose,thresh=1.)
                file=dest/f'N10_{k}.npz'
                np.savez_compressed(file,end_point_trajectory=raw.detach().float().cpu().numpy(),
                                    rigidity_steps=np.asarray(rigidity),T=pose)
                generations.append({'generation':k,'seed':row['seeds'][k],
                    'rigidity_steps_m':rigidity,'rigidity_rmse_m':float(np.mean(rigidity)),
                    'T':pose.tolist(),'overlap':float(overlap),'mean_dist':float(mean_dist),
                    'accepted':bool(overlap>=.7 and mean_dist<=2.5),
                    'file':str(file),'sha256':g0.sha(file),'generation_wall_s':time.monotonic()-t0})
            selected=min(generations,key=lambda r:(r['rigidity_rmse_m'],r['generation']))['generation']
            bank.append({'sequence':seq,'pair':pair,'selected_generation':selected,
                         'generations':generations})
            if (ix+1)%10==0:
                print('S1 bank',seq,ix+1,'elapsed',round(time.monotonic()-start,1),flush=True)
            assert time.monotonic()-start<=2700
            assert torch.cuda.max_memory_allocated()<=12*2**30
            assert sum(p.stat().st_size for p in BASE.rglob('N10_*.npz'))<=2*2**30
    g0.save_new(BASE/'bank.json',bank)
    g0.save_new(BASE/'bank_seal.json',{'sha256':g0.sha(BASE/'bank.json'),
        'utc':datetime.now(timezone.utc).isoformat(),'wall_s':time.monotonic()-start,
        'peak_allocated_gib':torch.cuda.max_memory_allocated()/2**30,
        'artifact_bytes':sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())})
    print('S1 bank sealed',flush=True)


def label(pose,truth):
    e=np.linalg.inv(truth)@pose
    r=e[:3,:3]
    skew=np.array([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])
    rte=float(np.linalg.norm(e[:3,3]))
    rre=float(np.degrees(np.arctan2(np.linalg.norm(skew)/2,np.clip((np.trace(r)-1)/2,-1,1))))
    return {'RTE_m':rte,'RRE_deg':rre,'strict':bool(rte<=1 and rre<=5),
            'clipped_error':float(min(5,max(rte,rre/5)))}


def evaluate():
    verify()
    verify_amendment()
    seal=g0.read(BASE/'bank_seal.json')
    assert g0.sha(BASE/'bank.json')==seal['sha256']
    bank=g0.read(BASE/'bank.json')
    outcomes=[]
    for seq in ('00','08'):
        parents=g0.read(F2/seq/'evaluator_only_decisions.json')
        old_records=g0.read(F2/seq/'records.json')
        old_gates=g0.read(F2/seq/'gates.json')
        gt=np.load(GT[seq],allow_pickle=False)
        rows=[r for r in bank if r['sequence']==seq]
        assert len(rows)==len(parents)==100
        for row,parent in zip(rows,parents):
            assert row['pair']==f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            truth=np.linalg.inv(gt[parent['source_i']])@gt[parent['source_j']]
            old=sorted((r for r in old_records if r['pair']==row['pair'] and r['arm']=='N'),
                       key=lambda r:r['generation'])
            assert len(old)==4
            five=[label(np.asarray(r['T']),truth) for r in old]
            ten=[label(np.asarray(r['T']),truth) for r in row['generations']]
            for k in range(4):
                five[k]['accepted']=old_gates[row['pair']]['N'][str(k)]['accepted']
                ten[k]['accepted']=row['generations'][k]['accepted']
            old_k=min(old,key=lambda r:(r['rigidity_rmse_m'],r['generation']))['generation']
            assert five[old_k]['strict']==parent['methods']['N']['strict']
            assert any(x['strict'] for x in five)==parent['methods']['N-OR4']['strict']
            five_selected=five[old_k]
            ten_selected=ten[row['selected_generation']]
            for x in (five_selected,ten_selected):
                x['correct_accepted']=bool(x['strict'] and x['accepted'])
                x['incorrect_accepted']=bool(not x['strict'] and x['accepted'])
            outcomes.append({'sequence':seq,'pair':row['pair'],'stratum':parent['stratum'],
                'five_generation':old_k,'ten_generation':row['selected_generation'],
                'five':five,'ten':ten,'five_selected':five_selected,'ten_selected':ten_selected})
    g0.save_new(BASE/'outcomes.json',outcomes)
    summary={'scope':'observed-development fixed native five versus ten Euler steps','sequences':{}}
    for seq in ('00','08'):
        rows=[r for r in outcomes if r['sequence']==seq]
        pos=[r for r in rows if r['stratum']!='confuser']
        methods={}
        for name in ('five','ten'):
            methods[name]={'strict':sum(r[f'{name}_selected']['strict'] for r in pos),
                'oracle_strict':sum(any(x['strict'] for x in r[name]) for r in pos),
                'correct_accepts':sum(r[f'{name}_selected']['correct_accepted'] for r in pos),
                'incorrect_accepts':sum(r[f'{name}_selected']['incorrect_accepted'] for r in rows),
                'confuser_accepts':sum(r[f'{name}_selected']['accepted'] for r in rows if r['stratum']=='confuser'),
                'ordinary_strict':sum(r[f'{name}_selected']['strict'] for r in pos if r['stratum']=='ordinary'),
                'clipped_error':float(np.mean([r[f'{name}_selected']['clipped_error'] for r in pos]))}
        summary['sequences'][seq]={'methods':methods,
            'new_strict_candidates':[r['pair'] for r in pos if not any(x['strict'] for x in r['five']) and any(x['strict'] for x in r['ten'])],
            'strict_gains':[r['pair'] for r in pos if r['ten_selected']['strict'] and not r['five_selected']['strict']],
            'strict_losses':[r['pair'] for r in pos if r['five_selected']['strict'] and not r['ten_selected']['strict']],
            'new_correct_accepts':[r['pair'] for r in pos if r['ten_selected']['correct_accepted'] and not r['five_selected']['correct_accepted']],
            'lost_correct_accepts':[r['pair'] for r in pos if r['five_selected']['correct_accepted'] and not r['ten_selected']['correct_accepted']],
            'newly_incorrect_accepts':[r['pair'] for r in rows if r['ten_selected']['incorrect_accepted'] and not r['five_selected']['incorrect_accepted']],
            'ordinary_strict_losses':[r['pair'] for r in pos if r['stratum']=='ordinary' and r['five_selected']['strict'] and not r['ten_selected']['strict']],
            'matched_generation_gains':sum(r['ten'][k]['strict'] and not r['five'][k]['strict'] for r in pos for k in range(4)),
            'matched_generation_losses':sum(r['five'][k]['strict'] and not r['ten'][k]['strict'] for r in pos for k in range(4)),
            'by_stratum':{st:{'five_strict':sum(r['five_selected']['strict'] for r in rows if r['stratum']==st),
                              'ten_strict':sum(r['ten_selected']['strict'] for r in rows if r['stratum']==st),
                              'five_oracle':sum(any(x['strict'] for x in r['five']) for r in rows if r['stratum']==st),
                              'ten_oracle':sum(any(x['strict'] for x in r['ten']) for r in rows if r['stratum']==st)}
                          for st in ('confuser','ambiguous_positive','low_overlap','ordinary')}}
    a,b=summary['sequences']['08'],summary['sequences']['00']
    af,at=a['methods']['five'],a['methods']['ten']
    bf,bt=b['methods']['five'],b['methods']['ten']
    conditions={
        '08_candidate_and_strict':len(a['new_strict_candidates'])>=5 and at['strict']-af['strict']>=5,
        '08_accept_safety':at['correct_accepts']-af['correct_accepts']>=2 and not a['newly_incorrect_accepts'],
        '00_guard':bt['strict']-bf['strict']>=-2 and len(b['lost_correct_accepts'])<=1 and not b['newly_incorrect_accepts'],
        'ordinary_guard':len(a['ordinary_strict_losses'])<=1 and len(b['ordinary_strict_losses'])<=1,
        'clipped_error':at['clipped_error']-af['clipped_error']<=.05 and bt['clipped_error']-bf['clipped_error']<=.05,
        'cost':seal['wall_s']<=2700 and seal['peak_allocated_gib']<=12 and
               sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=2*2**30}
    summary['conditions']=conditions
    summary['decision']='TEN_STEP_DEVELOPMENT_SIGNAL' if all(conditions.values()) else 'NO_TEN_STEP_DEVELOPMENT_SIGNAL'
    g0.save_new(BASE/'summary.json',summary)
    print('S1',summary['decision'],conditions,flush=True)


if __name__=='__main__':
    {'freeze':freeze,'run':run,'evaluate':evaluate}[sys.argv[1]]()
