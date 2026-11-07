"""Independent explicit graph reconstruction for the joint GT diagnostic."""
import importlib.metadata
import json
import resource
import sys
import time
from pathlib import Path

import gtsam
import numpy as np
import validate_dense_propagation as independent

MAIN=independent.MAIN
BASE=MAIN/'docs/maintenance/2026-10-05/joint-loop-oracle-01'
BANK=BASE/'attempt-01'; EVAL=BASE/'evaluation-01'; SEQS=independent.SEQS
read,digest,write,now=independent.read,independent.digest,independent.write,independent.now


def graph_rebuild(o,keys,edges):
    graph=gtsam.NonlinearFactorGraph(); initial=gtsam.Values()
    for k in keys: initial.insert(k,gtsam.Pose3(o[k]))
    prior=gtsam.noiseModel.Diagonal.Sigmas(np.full(6,.01))
    graph.add(gtsam.PriorFactorPose3(keys[0],gtsam.Pose3(o[keys[0]]),prior))
    odom_noise=gtsam.noiseModel.Diagonal.Sigmas(np.array([.05,.05,.05,.30,.30,.30]))
    for a,b in zip(keys[:-1],keys[1:]):
        graph.add(gtsam.BetweenFactorPose3(a,b,gtsam.Pose3(np.linalg.inv(o[a])@o[b]),odom_noise))
    sigmas=[]
    for e in edges:
        sigma=np.array([.03,.03,.03,.20,.20,.20])*np.clip(e['mean_dist'],1.,3.)
        sigmas.append(sigma.tolist())
        noise=gtsam.noiseModel.Robust.Create(gtsam.noiseModel.mEstimator.Huber(1.),gtsam.noiseModel.Diagonal.Sigmas(sigma))
        graph.add(gtsam.BetweenFactorPose3(e['i'],e['j'],gtsam.Pose3(np.asarray(e['T_rel'])),noise))
    params=gtsam.LevenbergMarquardtParams(); params.setMaxIterations(100)
    solved=gtsam.LevenbergMarquardtOptimizer(graph,initial,params).optimize()
    corrections={k:solved.atPose3(k).matrix()@np.linalg.inv(o[k]) for k in keys}
    full=np.empty_like(o); active=0
    for s in range(len(o)):
        while active+1<len(keys) and keys[active+1]<=s: active+=1
        full[s]=corrections[keys[active]]@o[s]
    return full,sigmas


def main():
    t=time.monotonic(); started=now()
    freeze,seal,result=(read(BASE/name) for name in ('freeze.json','bank_seal.json','results.json'))
    for p,h in freeze['files'].items(): assert digest(p)==h,p
    assert freeze['packages']=={p:importlib.metadata.version(p) for p in ('numpy','scipy','gtsam','evo')}
    assert seal['freeze_sha256']==digest(BASE/'freeze.json')
    assert result['bank_seal_sha256']==digest(BASE/'bank_seal.json')
    assert set(seal['files'])=={str(p.relative_to(BANK)) for p in BANK.rglob('*') if p.is_file()}
    for p,h in seal['files'].items(): assert digest(BANK/p)==h,p
    assert freeze['utc']<read(BANK/'execution.json')['started_utc']<seal['utc']<result['gt_read_started_utc']<started
    assert not list(BANK.rglob('oracle*')) and not list(BANK.rglob('J.npy'))
    checks=['identity, packages, GT-free bank inventory/seal and stage order']
    old=read(MAIN/'docs/maintenance/2026-09-29/system-opportunity-audit-01/results.json')
    actual={}; deltas={}; segment_total=0; edges_total=0
    for s in SEQS:
        o=independent.load(independent.src(s)/'odom_poses.txt')
        frames=read(BANK/s/'frames.json'); keys=frames['keyframes']; ids=frames['source_frame_ids']
        assert ids==list(range(len(o))) and keys==read(independent.src(s)/'keyframes.json')
        assert frames['source_frame_ids']==read(independent.src(s)/'source_frames.json')['source_frame_ids']
        edges=read(BANK/s/'edges.json'); oracle=read(EVAL/s/'oracle_edges.json')
        assert len(edges)==len(oracle) and all(set(e)=={'i','j','T_rel','overlap','mean_dist','measurement_id'} for e in edges)
        edges_total+=len(edges)
        tr=independent.calibration(s); ti=np.linalg.inv(tr)
        cam=independent.load(independent.DATA/'poses'/f'{s}.txt'); gt=ti@cam@tr
        assert gt.shape==o.shape
        local_oracle=[]
        for e,replaced in zip(edges,oracle):
            for key in set(e)-{'T_rel'}: assert e[key]==replaced[key]
            truth=np.linalg.inv(gt[e['i']])@gt[e['j']]
            np.testing.assert_allclose(truth,replaced['T_rel'],rtol=0,atol=1e-10)
            row=dict(e); row['T_rel']=truth.tolist(); local_oracle.append(row)
        rp,psigma=graph_rebuild(o,keys,edges); rj,jsigma=graph_rebuild(o,keys,local_oracle)
        assert psigma==jsigma
        p,j=np.load(BANK/s/'P.npy'),np.load(EVAL/s/'J.npy')
        np.testing.assert_allclose(rp,p,rtol=0,atol=1e-7)
        np.testing.assert_allclose(rj,j,rtol=0,atol=1e-7)
        deltas[s]=dict(P_graph_max_delta=float(np.max(np.abs(rp-p))),J_graph_max_delta=float(np.max(np.abs(rj-j))))
        for trajectory in (o,p,j): independent.geometry(trajectory)
        if s=='10': assert len(edges)==0 and np.max(np.abs(j-p))<=1e-5 and np.max(np.abs(j-o))<=1e-5
        actual[s]={}
        for arm,est in [('odom',o),('P',p),('J',j)]:
            records=independent.segments(tr@gt@ti,tr@est@ti,ids); saved=read(EVAL/s/f'{arm}_segments.json')
            assert len(records)==len(saved)>0
            segment_total+=len(records)
            for a,b in zip(records,saved):
                assert set(a)==set(b)
                for k in ('first','last','source_first','source_last','length_m'): assert a[k]==b[k]
                independent.close(a['translation_fraction'],b['translation_fraction'],1e-9)
                independent.close(a['rotation_rad_per_m'],b['rotation_rad_per_m'],1e-8)
                independent.close(a['speed_mps'],b['speed_mps'])
            metrics=dict(ate=independent.aligned_rmse(gt,est),ter=float(np.mean([x['translation_fraction'] for x in records])*100),
                         rer=float(np.mean([x['rotation_rad_per_m'] for x in records])*180/np.pi*100),segment_count=len(records))
            actual[s][arm]=metrics
            for k in metrics: independent.close(metrics[k],result['rows'][s][arm][k],2e-6)
            if arm in ('odom','P'):
                for k in metrics: independent.close(metrics[k],old['rows'][s]['odom' if arm=='odom' else 'full'][k],1e-5)
        checks.append(s+': full explicit native/oracle graph, every replacement and preserved sigma, independent metrics/segments')
        assert time.monotonic()-t<1200
    assert edges_total==58
    means={g:{a:{k:float(np.mean([actual[s][a][k] for s in seqs])) for k in ('ate','ter','rer')} for a in ('odom','P','J')} for g,seqs in [('development',SEQS[:3]),('transfer_exposed',SEQS[3:])]}
    opportunity={}
    for g,m in means.items():
        for a in m:
            for k in m[a]: independent.close(m[a][k],result['cohort_means'][g][a][k],2e-6)
        opportunity[g]=dict(ter_path=m['J']['ter']<=m['P']['ter']-.01 and m['J']['ate']/m['P']['ate']<=1.02,
                            ATE_path=m['J']['ate']/m['P']['ate']<=.95 and m['J']['ter']<=m['P']['ter']+.01)
    decision='MATERIAL_CURRENT_EDGE_JOINT_HEADROOM' if any(any(v.values()) for v in opportunity.values()) else 'NO_MATERIAL_COHORT_JOINT_SIGNAL'
    assert opportunity==result['opportunity'] and decision==result['decision']
    checks.append('independent cohort means and prospective opportunity criteria')
    total=read(BANK/'execution.json')['wall_s']+result['wall_s']+time.monotonic()-t
    peak=max(read(BANK/'execution.json')['peak_rss_gib'],result['peak_rss_gib'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    size=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
    assert total<1200 and peak<2 and size<500000000
    for p,h in freeze['files'].items(): assert digest(p)==h,p
    for p,h in seal['files'].items(): assert digest(BANK/p)==h,p
    write(BASE/'validation.json',dict(passed=True,utc=now(),decision=decision,check_groups=checks,
          edges=edges_total,independent_segment_records=segment_total,graph_crosscheck=deltas,
          total_wall_s=total,validator_wall_s=time.monotonic()-t,peak_rss_gib=peak,artifact_bytes_before_report=size))
    (BASE/'STATUS.json').write_text(json.dumps(dict(stage='VALIDATED',utc=now(),decision=decision,report='pending'),indent=2)+'\n')
    print('validated',decision,'edges',edges_total,'segments',segment_total,flush=True)


if __name__=='__main__': main()
