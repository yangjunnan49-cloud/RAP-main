"""Separate E1 evaluator and independent correctness/decision crosschecks."""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
MAIN=Path('/mnt/e/githouse/RAP-main');ROOT=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-09-27/e1-backend-01';OUT=BASE/'attempt-01'
E0=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import eval_paper_metrics as epm
from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def crosscheck(gt,p):
    g=np.linalg.inv(gt[0])@gt;e=np.linalg.inv(p[0])@p
    x=e[:,:3,3];y=g[:,:3,3];a=x-x.mean(0);b=y-y.mean(0)
    u,_,v=np.linalg.svd(a.T@b);d=np.eye(3);d[2,2]=np.linalg.det(v.T@u.T)
    r=v.T@d@u.T
    return float(np.sqrt(np.mean(np.sum((a@r.T-b)**2,axis=1)))),float(np.sqrt(np.mean(np.sum((x-y)**2,axis=1))))
def main():
    start=time.monotonic();freeze=read(BASE/'freeze.json');checks=[];rows={};audit={}
    for p,h in freeze['files'].items():assert sha(p)==h,p
    checks.append('All frozen source, parent, input and evaluator hashes match')
    for seq,n in {'00':4541,'05':2761,'06':1101}.items():
        src=E0/f'full-{seq}-A';calib=DATA/'sequences'/seq/'calib.txt'
        gt=np.asarray(load_gt_poses(str(DATA/'poses'/f'{seq}.txt'),str(calib),apply_calib=True))
        tr=_read_calib_transform(str(calib));gc=tr@gt@np.linalg.inv(tr)
        edges=read(src/'accepted_loops.json');kf=read(src/'keyframes.json');rows[seq]={};audit[seq]={}
        events=[json.loads(x) for x in (src/'verification_measurements.jsonl').read_text().splitlines()]
        measurements={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
        for edge in edges:
            m=measurements[edge['measurement_id']];assert m['source_frame_ids']==[edge['i'],edge['j']]
            assert m['T_rel']==edge['T_rel']
        assert read(src/'source_frames.json')['source_frame_ids']==list(range(n))
        np.testing.assert_array_equal(np.load(OUT/f'{seq}-O/poses.npy'),np.load(OUT/f'{seq}-O-repeat/poses.npy'))
        ref=np.asarray(epm.load_kitti_format(str(src/'optimized_poses.txt')))
        assert np.max(np.abs(ref-np.load(OUT/f'{seq}-O/poses.npy')))<=1e-5
        for arm in ['O','W1','W2','E1']:
            dest=OUT/f'{seq}-{arm}';p=np.load(dest/'poses.npy');assert p.shape==(n,4,4) and np.isfinite(p).all()
            assert read(dest/'source_ids.json')==list(range(n))
            r=p[:,:3,:3];orth=float(np.max(np.abs(r.transpose(0,2,1)@r-np.eye(3))))
            assert orth<1e-4 and np.max(np.abs(np.linalg.det(r)-1))<1e-4
            assert np.max(np.abs(p[:,3]-[0,0,0,1]))<1e-12
            expected=edges
            if arm=='E1':
                expected=[]
                for e in sorted(edges,key=lambda e:-e['overlap']):
                    if not any(max(abs(e['i']-k['i']),abs(e['j']-k['j']))<=10 for k in expected):expected.append(e)
            kept=read(dest/'edges.json')
            assert kept==[{k:e[k] for k in ['i','j','T_rel','overlap','mean_dist','measurement_id']} for e in expected]
            assert all(e['i'] in kf and e['j'] in kf for e in kept)
            diag=read(dest/'diagnostics.json')
            if arm=='W2':
                w=np.asarray(diag['weights']);lw=np.asarray(diag['loop_weights'])
                assert len(w)==len(kf)+len(edges) and np.array_equal(w[:len(kf)],np.ones(len(kf)))
                assert np.array_equal(w[len(kf):],lw) and np.isfinite(w).all() and np.all((w>=0)&(w<=1))
                assert diag['n_rejected']==int(sum(lw<.5)) and diag['n_loop']==len(edges)
            else:assert diag=={}
            lidar=epm.evaluate_pair(list(gt),list(p),list(range(n)))
            camera=epm.evaluate_pair(list(gc),list(tr@p@np.linalg.inv(tr)),list(range(n)))
            save(dest/'metrics.json',dict(lidar=lidar,camera=camera))
            # Re-read saved trajectory and independently recompute the frozen metrics.
            for frame,g,e in [('lidar',gt,np.load(dest/'poses.npy')),('camera',gc,tr@np.load(dest/'poses.npy')@np.linalg.inv(tr))]:
                again=epm.evaluate_pair(list(g),list(e),list(range(n)))
                saved=read(dest/'metrics.json')[frame]
                assert again==saved
                ate,first=crosscheck(g,e)
                assert abs(ate-saved['ape_aligned_rmse'])<1e-8
                assert abs(first-saved['ape_unaligned_rmse'])<1e-8
            rows[seq][arm]=dict(ate=lidar['ape_aligned_rmse'],ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],first_ape=lidar['ape_unaligned_rmse'],edges=len(kept))
            audit[seq][arm]=dict(max_orthogonality=orth,gnc=diag)
            checks.append(f'{seq}-{arm}: IDs, SE3, edge identity/NMS, metrics, independent APE crosscheck')
        checks.append(f'{seq}: O reproduction, exact double-run, parent measurement identity')
    means={a:{k:float(np.mean([rows[s][a][k] for s in rows])) for k in ['ate','ter']} for a in ['O','W1','W2','E1']}
    gates={}
    for a in ['W1','W2','E1']:
        gates[a]=dict(mean_ate=means[a]['ate']<=.95*means['O']['ate'],mean_ter=means[a]['ter']<=means['O']['ter']+.02,
            sequence_ter=all(rows[s][a]['ter']<=rows[s]['O']['ter']+.05 for s in rows),
            sequence_ate=all(rows[s][a]['ate']<=1.1*rows[s]['O']['ate'] for s in rows))
    eligible=[a for a in gates if all(gates[a].values())]
    selected=min(eligible,key=lambda a:(means[a]['ate'],means[a]['ter'],a)) if eligible else None
    old=read(E0/'development_baseline_v2.json');oldmean=float(np.mean([v['ate'] for v in old['sequences'].values()]))
    decision='FREEZE_DEVELOPMENT_SUCCESSOR_V3' if selected and means[selected]['ate']<oldmean else 'NO_SUCCESSOR'
    # Alternative arithmetic, including ranking, independent of the boolean gate table.
    candidates=[]
    for a in ['E1','W2','W1']:
        da=[rows[s][a]['ate']/rows[s]['O']['ate'] for s in rows]
        dt=[rows[s][a]['ter']-rows[s]['O']['ter'] for s in rows]
        if means[a]['ate']/means['O']['ate']<=.95 and means[a]['ter']-means['O']['ter']<=.02 and max(da)<=1.1 and max(dt)<=.05:candidates.append(a)
    candidates.sort(key=lambda a:(means[a]['ate'],means[a]['ter'],a))
    assert selected==(candidates[0] if candidates else None)
    execution=read(OUT/'execution.json');wall=execution['wall_s']+time.monotonic()-start
    assert wall<1800 and sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<2**30
    for p,h in freeze['files'].items():assert sha(p)==h,p
    checks+=['Decision gates and selection independently recomputed','30 minute / 1 GiB caps and post-run hash stability']
    save(BASE/'results.json',dict(rows=rows,means=means,audit=audit))
    save(BASE/'decision.json',dict(decision=decision,gates=gates,eligible=eligible,selected=selected,means=means))
    save(BASE/'validation.json',dict(passed=True,checks=checks,wall_s=wall))
    if decision=='FREEZE_DEVELOPMENT_SUCCESSOR_V3':save(BASE/'development_baseline_v3.json',dict(name='e1-development-v3',arm=selected,means=means[selected],sequences={s:rows[s][selected] for s in rows},freeze_sha256=sha(BASE/'freeze.json'),scope='Observed development only; production defaults unchanged'))
    lines=['# E1 bounded backend review','','Decision: **'+decision+'**.','','Observed KITTI00/05/06 development evidence; no independent confirmation or novelty claim.','','| Seq | Arm | Camera ter % | Aligned ATE m | First-pose APE m | Edges |','|---|---|---:|---:|---:|---:|']
    for s in rows:
        for a,r in rows[s].items():lines.append(f"| {s} | {a} | {r['ter']:.6f} | {r['ate']:.6f} | {r['first_ape']:.6f} | {r['edges']} |")
    lines+=['','## Means and eligibility','','| Arm | Mean ter % | Mean ATE m | Eligible |','|---|---:|---:|---|']
    for a,m in means.items():lines.append(f"| {a} | {m['ter']:.6f} | {m['ate']:.6f} | {a in eligible} |")
    lines+=['','Gate details: `decision.json`. No post-hoc arm, parameter search or combined arm.',
        'W1 uses unit loop information with unchanged anisotropic odometry information; it is not a KISS-SLAM backend reproduction or a test of equal trust across all factors.',
        'W2 uses the historical GNC-TLS defaults. E1 uses fixed NMS width 10. Accepted transforms are unchanged; evaluator fields were stripped before optimization.',
        f'O reproduced saved E0 trajectories within 1e-5; repeated O outputs are exactly identical. {len(checks)} validation checks passed; replay plus evaluation wall {wall:.3f}s.',
        'Separate validator recomputed frozen metrics and independently crosschecked anchored APE and decision arithmetic. No new scans, inference, production change, Git commit or synchronization.',
        'E0 development_baseline_v2 and historical core-baseline-v1 remain preserved. F2 requires a separate owner decision. Manuscript pause and all prior research stops persist.']
    (BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (BASE/'INCOMPLETE').unlink()
    save(BASE/'artifact_hashes.json',{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()})
    print(decision,means,gates,flush=True)
if __name__=='__main__':main()
