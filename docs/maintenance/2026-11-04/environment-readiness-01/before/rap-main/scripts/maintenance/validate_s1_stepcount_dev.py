"""Independent S1 source, raw-flow, geometry, evaluator and decision audit."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

MAIN=Path(__file__).resolve().parents[2]
F2=MAIN/'docs/maintenance/2026-09-27/f2-structured-dev-01'
BASE=MAIN/'docs/maintenance/2026-09-28/s1-stepcount-dev-01'
GT={'00':MAIN/'docs/maintenance/2026-09-14/hl-v2/data-expansion-01/00/evaluator_gt.npy',
    '08':MAIN/'docs/maintenance/2026-09-14/support-control-01/data/08/evaluator_gt.npy'}
sys.path.insert(0,str(MAIN/'scripts/maintenance'))
import fullscan_global_baseline as g1
import v0_ray_visibility as v0

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()
def close(a,b,tol=1e-6):assert abs(float(a)-float(b))<=tol,(a,b)

def fit(x,y):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    xm,ym=x.mean(0),y.mean(0)
    u,_,vt=np.linalg.svd((x-xm).T@(y-ym))
    d=np.linalg.det(vt.T@u.T)
    r=vt.T@np.diag([1.,1.,1. if d>=0 else -1.])@u.T
    t=ym-xm@r.T
    return r,t

def raw_metrics(cond,pred,counts,centers,scale):
    cuts=np.r_[0,np.cumsum(counts)]
    poses=[];sq=0.0
    for k in range(6):
        sl=slice(cuts[k],cuts[k+1])
        x,y=cond[sl],pred[sl]
        r,t=fit(x,y)
        sq+=float(np.sum((x@r.T+t-y)**2))
        if k in (0,3):
            p=np.eye(4);p[:3,:3]=r;p[:3,3]=scale*t-r@centers[k]
            poses.append(p)
    return float(np.sqrt(sq/len(cond))*scale),np.linalg.inv(poses[0])@poses[1]

def label(pose,truth):
    e=np.linalg.inv(truth)@pose;r=e[:3,:3]
    skew=[r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]]
    rte=float(np.linalg.norm(e[:3,3]))
    rre=float(np.degrees(np.arctan2(np.linalg.norm(skew)/2,
        np.clip((np.trace(r)-1)/2,-1,1))))
    return rte,rre

def geometry(target,source,pose):
    mapped=source@pose[:3,:3].T+pose[:3,3]
    da=cKDTree(target).query(mapped,k=1,workers=1)[0]
    db=cKDTree(mapped).query(target,k=1,workers=1)[0]
    return (float((np.mean(da<1)+np.mean(db<1))/2),float((np.mean(da)+np.mean(db))/2))

def main():
    assert not (BASE/'validation.json').exists() and not (BASE/'INCOMPLETE').exists()
    freeze=read(BASE/'freeze.json')
    checks=0
    for name,digest in freeze['files'].items():
        assert sha(Path(name))==digest,name
        checks+=1
    bank=read(BASE/'bank.json');seal=read(BASE/'bank_seal.json')
    outcomes=read(BASE/'outcomes.json');summary=read(BASE/'summary.json')
    assert sha(BASE/'bank.json')==seal['sha256']
    assert len(bank)==len(outcomes)==200
    assert seal['wall_s']<=2700 and seal['peak_allocated_gib']<=12
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=2*2**30
    checks+=4
    max_rig=max_pose=0.0
    for seq in ('00','08'):
        records=read(F2/seq/'records.json')
        gates=read(F2/seq/'gates.json')
        input_rows={r['key']:r for r in read(F2/f'inputs_{seq}.json')}
        parents=read(F2/seq/'evaluator_only_decisions.json')
        gt=np.load(GT[seq],allow_pickle=False)
        pairs=list(dict.fromkeys(r['pair'] for r in records if r['arm']=='N'))
        assert freeze['pairs'][seq]==pairs and len(pairs)==100
        rows=[r for r in bank if r['sequence']==seq]
        labels=[r for r in outcomes if r['sequence']==seq]
        assert len(rows)==len(labels)==len(parents)==100
        for ix,(row,out,parent) in enumerate(zip(rows,labels,parents)):
            pair=f'{seq}_{parent["source_i"]}_{parent["source_j"]}'
            assert row['pair']==out['pair']==pairs[ix]==pair
            assert out['stratum']==parent['stratum']
            old=sorted((r for r in records if r['pair']==pair and r['arm']=='N'),key=lambda r:r['generation'])
            assert len(old)==4 and [r['generation'] for r in old]==list(range(4))
            with np.load(F2/seq/pair/'inputs.npz',allow_pickle=False) as z:
                cond=z['cond'].astype(np.float64);counts=z['counts'];centers=z['centers'];scale=float(z['scale'])
                assert counts.tolist()==[2000,1000,1000,2000,1000,1000]
            truth=np.linalg.inv(gt[parent['source_i']])@gt[parent['source_j']]
            assert len(row['generations'])==len(out['ten'])==len(out['five'])==4
            for k,gen in enumerate(row['generations']):
                assert gen['generation']==k and gen['seed']==input_rows[pair]['seeds'][k]
                path=Path(gen['file'])
                assert path==BASE/seq/pair/f'N10_{k}.npz'
                assert sha(path)==gen['sha256']
                with np.load(path,allow_pickle=False) as z:
                    raw=z['end_point_trajectory'];rig=z['rigidity_steps'];pose=z['T']
                assert raw.shape==(10,8000,3) and rig.shape==(10,)
                assert np.isfinite(raw).all() and np.isfinite(rig).all()
                deltas=[]
                for step in range(10):
                    metric,reconstructed=raw_metrics(cond,raw[step],counts,centers,scale)
                    deltas.append(abs(metric-rig[step]))
                max_rig=max(max_rig,max(deltas))
                assert max(deltas)<=1e-3,(pair,k,max(deltas))
                pose_delta=float(np.max(np.abs(reconstructed-pose)))
                max_pose=max(max_pose,pose_delta)
                assert pose_delta<=1e-4,(pair,k,pose_delta)
                np.testing.assert_allclose(pose,gen['T'],atol=1e-10,rtol=0)
                np.testing.assert_allclose(rig,gen['rigidity_steps_m'],atol=1e-10,rtol=0)
                close(np.mean(rig),gen['rigidity_rmse_m'])
                assert gen['accepted']==(gen['overlap']>=.7 and gen['mean_dist']<=2.5)
                assert gen['generation_wall_s']>=0
                rte,rre=label(pose,truth)
                lab=out['ten'][k]
                close(lab['RTE_m'],rte);close(lab['RRE_deg'],rre)
                assert lab['strict']==(rte<=1 and rre<=5)
                close(lab['clipped_error'],min(5,max(rte,rre/5)))
                assert lab['accepted']==gen['accepted']
                old_pose=np.asarray(old[k]['T'])
                frte,frre=label(old_pose,truth)
                flab=out['five'][k]
                close(flab['RTE_m'],frte);close(flab['RRE_deg'],frre)
                assert flab['strict']==(frte<=1 and frre<=5)
                assert flab['accepted']==gates[pair]['N'][str(k)]['accepted']
                checks+=12
            selected=min(row['generations'],key=lambda r:(r['rigidity_rmse_m'],r['generation']))['generation']
            assert row['selected_generation']==selected==out['ten_generation']
            old_k=min(old,key=lambda r:(r['rigidity_rmse_m'],r['generation']))['generation']
            assert out['five_generation']==old_k
            assert out['five_selected']=={**out['five'][old_k],
                'correct_accepted':out['five_selected']['correct_accepted'],
                'incorrect_accepted':out['five_selected']['incorrect_accepted']}
            assert out['ten_selected']=={**out['ten'][selected],
                'correct_accepted':out['ten_selected']['correct_accepted'],
                'incorrect_accepted':out['ten_selected']['incorrect_accepted']}
            for name in ('five','ten'):
                chosen=out[f'{name}_selected']
                assert chosen['correct_accepted']==(chosen['strict'] and chosen['accepted'])
                assert chosen['incorrect_accepted']==(not chosen['strict'] and chosen['accepted'])
            assert out['five_selected']['strict']==parent['methods']['N']['strict']
            assert any(x['strict'] for x in out['five'])==parent['methods']['N-OR4']['strict']
            if ix in (0,25,50,75):
                tp,sp=g1.pair_scans(seq,pair)
                g=v0.gate_backend()
                target=g.preprocess(g1.load_scan(tp))[0]
                source=g.preprocess(g1.load_scan(sp))[0]
                for gen in row['generations']:
                    overlap,dist=geometry(target,source,np.asarray(gen['T']))
                    close(overlap,gen['overlap'],1e-10);close(dist,gen['mean_dist'],1e-8)
                checks+=4
        pos=[r for r in labels if r['stratum']!='confuser']
        s=summary['sequences'][seq]
        assert len(pos)==75
        for name in ('five','ten'):
            m=s['methods'][name]
            assert m['strict']==sum(r[f'{name}_selected']['strict'] for r in pos)
            assert m['oracle_strict']==sum(any(x['strict'] for x in r[name]) for r in pos)
            assert m['correct_accepts']==sum(r[f'{name}_selected']['correct_accepted'] for r in pos)
            assert m['incorrect_accepts']==sum(r[f'{name}_selected']['incorrect_accepted'] for r in labels)
            assert m['confuser_accepts']==sum(r[f'{name}_selected']['accepted'] for r in labels if r['stratum']=='confuser')
            assert m['ordinary_strict']==sum(r[f'{name}_selected']['strict'] for r in pos if r['stratum']=='ordinary')
            close(m['clipped_error'],np.mean([r[f'{name}_selected']['clipped_error'] for r in pos]))
        assert s['new_strict_candidates']==[r['pair'] for r in pos if not any(x['strict'] for x in r['five']) and any(x['strict'] for x in r['ten'])]
        assert s['strict_gains']==[r['pair'] for r in pos if r['ten_selected']['strict'] and not r['five_selected']['strict']]
        assert s['strict_losses']==[r['pair'] for r in pos if r['five_selected']['strict'] and not r['ten_selected']['strict']]
        assert s['new_correct_accepts']==[r['pair'] for r in pos if r['ten_selected']['correct_accepted'] and not r['five_selected']['correct_accepted']]
        assert s['lost_correct_accepts']==[r['pair'] for r in pos if r['five_selected']['correct_accepted'] and not r['ten_selected']['correct_accepted']]
        assert s['newly_incorrect_accepts']==[r['pair'] for r in labels if r['ten_selected']['incorrect_accepted'] and not r['five_selected']['incorrect_accepted']]
        assert s['ordinary_strict_losses']==[r['pair'] for r in pos if r['stratum']=='ordinary' and r['five_selected']['strict'] and not r['ten_selected']['strict']]
        assert s['matched_generation_gains']==sum(r['ten'][k]['strict'] and not r['five'][k]['strict'] for r in pos for k in range(4))
        assert s['matched_generation_losses']==sum(r['five'][k]['strict'] and not r['ten'][k]['strict'] for r in pos for k in range(4))
        for st,b in s['by_stratum'].items():
            ss=[r for r in labels if r['stratum']==st]
            assert len(ss)==25
            assert b['five_strict']==sum(r['five_selected']['strict'] for r in ss)
            assert b['ten_strict']==sum(r['ten_selected']['strict'] for r in ss)
            assert b['five_oracle']==sum(any(x['strict'] for x in r['five']) for r in ss)
            assert b['ten_oracle']==sum(any(x['strict'] for x in r['ten']) for r in ss)
        checks+=1
    a,b=summary['sequences']['08'],summary['sequences']['00']
    af,at=a['methods']['five'],a['methods']['ten']
    bf,bt=b['methods']['five'],b['methods']['ten']
    conditions={'08_candidate_and_strict':len(a['new_strict_candidates'])>=5 and at['strict']-af['strict']>=5,
      '08_accept_safety':at['correct_accepts']-af['correct_accepts']>=2 and not a['newly_incorrect_accepts'],
      '00_guard':bt['strict']-bf['strict']>=-2 and len(b['lost_correct_accepts'])<=1 and not b['newly_incorrect_accepts'],
      'ordinary_guard':len(a['ordinary_strict_losses'])<=1 and len(b['ordinary_strict_losses'])<=1,
      'clipped_error':at['clipped_error']-af['clipped_error']<=.05 and bt['clipped_error']-bf['clipped_error']<=.05,
      'cost':seal['wall_s']<=2700 and seal['peak_allocated_gib']<=12 and sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<=2*2**30}
    assert summary['conditions']==conditions
    decision='TEN_STEP_DEVELOPMENT_SIGNAL' if all(conditions.values()) else 'NO_TEN_STEP_DEVELOPMENT_SIGNAL'
    assert summary['decision']==decision
    checks+=2
    with (BASE/'validation.json').open('x',encoding='utf-8') as f:
        json.dump({'passed':True,'decision':decision,'checks':checks,'max_rigidity_delta':max_rig,
            'max_pose_delta':max_pose,'bank_sha256':seal['sha256']},f,indent=2)
        f.write('\n')
    print('S1 validation passed',checks,'checks',flush=True)

if __name__=='__main__':main()
