"""All-pair/graph/trajectory independent validator, no comparator runner import."""
import json,time,resource
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import validate_dense_propagation as v
from validate_joint_loop_oracle import graph_rebuild
B=v.MAIN/'docs/maintenance/2026-10-05/online-geotransformer-01'; I=B/'input-bank'; P=B/'prediction-bank'; E=B/'evaluation-01'
read,sha,write=v.read,v.digest,v.write
def score(a,b,T):
    q=b@T[:3,:3].T+T[:3,3]; x=cKDTree(a).query(q)[0]; y=cKDTree(q).query(a)[0]
    return float(.5*((x<1).mean()+(y<1).mean())),float(.5*(x.mean()+y.mean()))
def main():
    t=time.monotonic(); freeze=read(B/'freeze.json'); results=read(B/'results.json'); pairs=read(B/'pair_outcomes.json')
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    f=read(v.MAIN/'docs/maintenance/2026-10-05/geotransformer-feasibility-01/preflight_freeze.json')
    for p,h in f['files'].items(): assert sha(p)==h,p
    for folder,name in [(I,'input_seal.json'),(P,'bank_seal.json')]:
        seal=read(B/name); assert seal['freeze_sha256']==sha(B/'freeze.json')
        assert seal['files']=={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}
    iv=read(B/'input_validation.json'); be=read(P/'execution.json'); se=read(B/'bank_seal.json')
    assert iv['passed'] and be['input_validation_sha256']==sha(B/'input_validation.json')
    assert freeze['utc']<read(I/'execution.json')['started_utc']<read(B/'input_seal.json')['utc']<iv['utc']<be['started_utc']<se['utc']<results['gt_read_started_utc']
    assert results['bank_seal_sha256']==sha(B/'bank_seal.json')
    checks=['freeze/seals/stage order and independently validated inputs']; computed={}; edgecounts={}; strict={'RAP':0,'Geo':0}; totalpairs=segments=0; summary={}; graphdelta={}
    for s in v.SEQS:
        native=read(I/'attempts.json')[s]; pred=read(P/f'{s}.json'); o=v.load(v.src(s)/'odom_poses.txt'); keys=read(v.src(s)/'keyframes.json')
        cam=v.load(v.DATA/'poses'/f'{s}.txt'); tr=v.calibration(s); ti=np.linalg.inv(tr); gt=ti@cam@tr
        saved=read(v.OLD/'attempt-01'/s/'edges.json'); expectedG=[]; expectedC=[]; summary[s]=dict(attempts=len(pred),RAP_strict=0,Geo_strict=0,RAP_accepted_wrong=0,Geo_accepted_wrong=0,RAP_accepted_far=0,Geo_accepted_far=0)
        for r,g,pair in zip(native,pred,pairs[s]):
            assert r['attempt_id']==g['attempt_id']==pair['attempt_id'] and (r['i'],r['j'])==(g['i'],g['j'])==(pair['i'],pair['j']); totalpairs+=1
            pose=np.asarray(g['T_rel']); v.geometry(pose[None]); truth=np.linalg.inv(gt[r['i']])@gt[r['j']]
            a=np.load(I/s/f"{r['i']:06d}.npy"); b=np.load(I/s/f"{r['j']:06d}.npy"); ov,md=score(a,b,pose)
            v.close(ov,g['overlap'],1e-9); v.close(md,g['mean_dist'],1e-9)
            accepted=ov>=.7 and md<=2.5; assert accepted==g['accepted']==pair['geo_accepted']; assert pair['native_accepted']==(r['status']=='accepted')
            far=bool(np.linalg.norm(gt[r['i'],:3,3]-gt[r['j'],:3,3])>15); assert far==pair['GT_far']
            for arm,estimate,admit in [('RAP',np.asarray(r['T_rel']),r['status']=='accepted'),('Geo',pose,accepted)]:
                trans=float(np.sqrt(np.sum((estimate[:3,3]-truth[:3,3])**2))); rot=float(np.arccos(np.clip((np.trace(np.linalg.solve(estimate[:3,:3],truth[:3,:3]))-1)/2,-1,1))*180/np.pi)
                v.close(trans,pair[arm]['translation_m'],1e-8); v.close(rot,pair[arm]['rotation_deg'],.003)
                # Saved float32 rotations can deviate microscopically from SO(3);
                # strict boundaries are still independently checked at this tolerance.
                good=trans<=1 and rot<=5; paper=trans<=2 and rot<=5
                assert good==pair[arm]['strict'] and paper==pair[arm]['paper_threshold']
                strict[arm]+=good; summary[s][arm+'_strict']+=good; summary[s][arm+'_accepted_wrong']+=bool(admit and not good); summary[s][arm+'_accepted_far']+=bool(admit and far)
            if accepted: expectedC.append(dict(i=g['i'],j=g['j'],T_rel=g['T_rel'],overlap=g['overlap'],mean_dist=g['mean_dist'],measurement_id=g['attempt_id']))
        assert len(native)==len(pred)==len(pairs[s])
        for e in saved:
            r=next(r for r in native if r['selected_measurement_id']==e['measurement_id']); g=next(g for g in pred if g['attempt_id']==r['attempt_id']); row=dict(e); row['T_rel']=g['T_rel']; expectedG.append(row)
        assert expectedG==read(E/s/'G_edges.json') and expectedC==read(E/s/'C_edges.json')
        repeat=read(P/'repeatability.json')[s]; assert repeat['attempt_id']==pred[0]['attempt_id']; delta=float(np.max(np.abs(np.array(repeat['repeat'])-pred[0]['T_rel']))); assert delta<=1e-6 and delta==repeat['max_pose_delta']
        computed[s]={}; graphdelta[s]={}; edgecounts[s]=dict(P=len(saved),G=len(expectedG),C=len(expectedC))
        for arm,edges in [('P',saved),('G',expectedG),('C',expectedC)]:
            rebuilt,_=graph_rebuild(o,keys,edges); est=np.load(E/s/f'{arm}.npy'); v.geometry(est)
            delta=float(np.max(np.abs(rebuilt-est))); assert delta<1e-7; graphdelta[s][arm]=delta
            records=v.segments(cam,tr@est@ti,list(range(len(est)))); seg=read(E/s/f'{arm}_segments.json'); assert len(records)==len(seg)>0; segments+=len(records)
            for x,y in zip(records,seg):
                assert set(x)==set(y)
                for key in ['first','last','source_first','source_last','length_m']: assert x[key]==y[key]
                for key in ['translation_fraction','rotation_rad_per_m','speed_mps']: v.close(x[key],y[key],1e-8)
            metric=dict(ate=v.aligned_rmse(gt,est),ter=float(np.mean([x['translation_fraction'] for x in records])*100),rer=float(np.mean([x['rotation_rad_per_m'] for x in records])*180/np.pi*100),segment_count=len(records)); computed[s][arm]=metric
            for key in metric: v.close(metric[key],results['rows'][s][arm][key],2e-6)
        checks.append(s+': all candidates/gates/labels/repeat; explicit graphs and every independent trajectory metric/segment')
    assert totalpairs==71 and sum(x['P'] for x in edgecounts.values())==58 and edgecounts==results['edge_counts']
    means={g:{a:{k:float(np.mean([computed[s][a][k] for s in seqs])) for k in ['ate','ter','rer']} for a in ['P','G','C']} for g,seqs in [('development',v.SEQS[:3]),('transfer_exposed',v.SEQS[3:])]}
    opportunity={}; safety={s:dict(ATE=computed[s]['C']['ate']<=1.1*computed[s]['P']['ate'],ter=computed[s]['C']['ter']<=computed[s]['P']['ter']+.03) for s in v.SEQS}
    for g,m in means.items():
        for a in m:
            for k in m[a]: v.close(m[a][k],results['cohort_means'][g][a][k],2e-6)
        opportunity[g]=dict(ATE_path=m['C']['ate']/m['P']['ate']<=.95 and m['C']['ter']-m['P']['ter']<=.01,ter_path=m['P']['ter']-m['C']['ter']>=.01 and m['C']['ate']/m['P']['ate']<=1.02)
    assert opportunity==results['opportunity'] and safety==results['safety'] and results['candidate_strict']==dict(**strict,signal=strict['Geo']>=strict['RAP']+5)
    decision='MATERIAL_COMMON_GATE_SYSTEM_SIGNAL' if any(any(x.values()) for x in opportunity.values()) and all(all(x.values()) for x in safety.values()) else 'NO_MATERIAL_COMMON_GATE_SYSTEM_SIGNAL'
    assert decision==results['decision']; checks.append('independent means/prospective decisions/resources')
    totalwall=sum(x['wall_s'] for x in [read(I/'execution.json'),iv,be,results])+time.monotonic()-t
    peak=max(x['peak_rss_gib'] for x in [read(I/'execution.json'),iv,be,results]); peak=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    size=sum(p.stat().st_size for p in B.rglob('*') if p.is_file()); assert totalwall<1800 and peak<6 and be['peak_gpu_gib']<8 and size<2*2**30
    for p,h in freeze['files'].items(): assert sha(p)==h,p
    write(B/'validation.json',dict(passed=True,utc=v.now(),decision=decision,check_groups=checks,pairs=totalpairs,segment_records=segments,graph_max_deltas=graphdelta,pair_summary=summary,total_wall_s=totalwall,validator_wall_s=time.monotonic()-t,peak_rss_gib=peak,artifact_bytes_before_report=size))
    (B/'STATUS.json').write_text(json.dumps(dict(stage='VALIDATED',utc=v.now(),decision=decision,report='pending'),indent=2)+'\n')
    print('validated',decision,'all71 candidates and',segments,'segment records',flush=True)
if __name__=='__main__': main()
