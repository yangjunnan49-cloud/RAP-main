"""Post-run validation and engineering report; does not generate trajectories.

E0-AMENDMENT-01 (2026-09-27): identical to the frozen validate_e0_frontend.py
except both independent NumPy Umeyama crosschecks anchor trajectories to the
first pose first (float64 gauge-conditioning fix; tolerance unchanged 1e-8).
See docs/maintenance/2026-09-26/e0-frontend-01/AMENDMENT_01.md.
"""
import hashlib,json,sys
from pathlib import Path
from collections import Counter
import numpy as np
MAIN=Path('/mnt/e/githouse/RAP-main');ROOT=MAIN.parent/'RAP-SLAM'
BASE=MAIN/'docs/maintenance/2026-09-26/e0-frontend-01'
OLD=MAIN/'docs/maintenance/2026-09-11'
DATA=MAIN.parent/'Datasets/data_odometry_velodyne/dataset'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import eval_paper_metrics as epm
from rap_slam.real_dataset import load_gt_poses,_read_calib_transform
from rap_slam.measurement import transform_label,rotation_validity
from rap_slam.evaluate import align_to_first_pose

def read(p):return json.loads(Path(p).read_text())
def save(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def odom_path(seq,arm):
    old=BASE/f'odom-{seq}-{arm}'
    return old if (old/'metrics.json').exists() else BASE/'resume-01'/f'odom-{seq}-{arm}'
def numpy_ate(gt,est):
    x=est[:,:3,3];y=gt[:,:3,3];a=x-x.mean(0);b=y-y.mean(0)
    u,_,v=np.linalg.svd(a.T@b);D=np.eye(3);D[2,2]=np.linalg.det(v.T@u.T)
    r=v.T@D@u.T
    return float(np.sqrt(np.mean(np.sum((a@r.T-b)**2,axis=1))))
def anchored_numpy_ate(gt,est):
    a=np.asarray(align_to_first_pose(list(gt)));b=np.asarray(align_to_first_pose(list(est)))
    return numpy_ate(a,b)
def main():
    execution=read(BASE/'execution.json');selection=read(BASE/'selection.json')
    frozen=read(BASE/'freeze.json')
    for p,h in frozen['sources'].items():assert sha(p)==h,p
    seqs={'00':4541,'05':2761,'06':1101};metrics={};full={};checks=[]
    for seq,n in seqs.items():
        calib=DATA/'sequences'/seq/'calib.txt';tr=_read_calib_transform(str(calib))
        gt=load_gt_poses(str(DATA/'poses'/f'{seq}.txt'),str(calib),apply_calib=True)
        metrics[seq]={}
        for arm in 'OABC':
            out=odom_path(seq,arm);poses=np.load(out/'poses.npy');saved=read(out/'metrics.json')
            assert len(poses)==n and read(out/'source_ids.json')==list(range(n))
            assert np.isfinite(poses).all()
            r=poses[:,:3,:3];assert np.max(np.abs(r.transpose(0,2,1)@r-np.eye(3)))<1e-4
            assert np.max(np.abs(np.linalg.det(r)-1))<1e-4
            lidar=epm.evaluate_pair(list(gt),list(poses),list(range(n)))
            camera=epm.evaluate_pair(list(tr@gt@np.linalg.inv(tr)),list(tr@poses@np.linalg.inv(tr)),list(range(n)))
            assert abs(anchored_numpy_ate(gt,poses)-saved['lidar']['ape_aligned_rmse'])<1e-8
            for frame,fresh in [('lidar',lidar),('camera',camera)]:
                for k,v in saved[frame].items():assert abs(fresh[k]-v)<1e-9,(seq,arm,k)
            metrics[seq][arm]=dict(ter=camera['kitti_ter_pct'],rer=camera['kitti_rer_deg100m'],ate=lidar['ape_aligned_rmse'])
            if arm=='O':
                old=np.asarray(epm.load_kitti_format(str(OLD/f'full-kitti{seq}-01/pipeline/odom_poses.txt')))
                assert np.max(np.abs(poses-old))<=1e-5
            checks.append(f'{seq}-{arm}: geometry, exact IDs, independent ATE and metric recomputation')
    means={a:{k:float(np.mean([metrics[s][a][k] for s in seqs])) for k in ['ter','ate']} for a in 'OABC'}
    eligible=[a for a in 'ABC' if means[a]['ter']<=means['O']['ter']-.02 and means[a]['ate']<=means['O']['ate']*1.1 and all(metrics[s][a]['ter']<=metrics[s]['O']['ter']+.05 for s in seqs)]
    selected=min(eligible,key=lambda a:(means[a]['ter'],means[a]['ate'],a)) if eligible else None
    assert selected==selection['selected'] and eligible==selection['eligible']
    for a in means:
        for k in means[a]:assert abs(means[a][k]-selection['means'][a][k])<1e-12
    labels=[];strict=[];baseline=read(OLD/'core-baseline-v1/registry.json')
    if selected:
        for seq,n in seqs.items():
            dest=BASE/f'full-{seq}-{selected}';assert not (dest/'INCOMPLETE').exists()
            summary=read(dest/'summary.json');cfg=summary['config'];frames=read(dest/'source_frames.json')
            assert summary['n_scans']==n and summary['odometry_backend']=='kiss-icp'
            assert frames['source_frame_ids']==list(range(n)) and len(frames['scan_files'])==n
            assert frames['scan_files']==[str(DATA/'sequences'/seq/'velodyne'/f'{i:06d}.bin') for i in range(n)]
            assert not cfg['deskew'] and not cfg['allow_odom_fallback'] and cfg['multigen_k']==1 and cfg['loop_nms_width']==0
            assert cfg['max_candidates']==12 and cfg['rap_steps']==5
            ods=np.asarray(epm.load_kitti_format(str(dest/'odom_poses.txt')))
            assert np.max(np.abs(ods-np.load(odom_path(seq,selected)/'poses.npy')))<=1e-5
            fresh=epm.eval_offline(str(dest));assert fresh['frame_binding']=='persisted_source_frame_ids'
            events=[json.loads(x) for x in (dest/'verification_measurements.jsonl').read_text().splitlines()]
            starts={e['attempt_id']:e for e in events if e['event']=='candidate_started'}
            ends={e['attempt_id']:e for e in events if e['event']=='candidate_finished'}
            generations={e['measurement']['measurement_id']:e['measurement'] for e in events if e['event']=='generation'}
            assert starts.keys()==ends.keys() and len(starts)==summary['n_loop_candidates']
            assert all(e['status'] in ['accepted','rejected'] for e in ends.values())
            edges=read(dest/'accepted_loops.json')
            assert {e['measurement_id'] for e in edges}=={e['selected_measurement_id'] for e in ends.values() if e['status']=='accepted'}
            gt=np.asarray(epm.gt_from_summary(str(dest)))
            for edge in edges:
                m=generations[edge['measurement_id']];np.testing.assert_array_equal(m['T_rel'],edge['T_rel'])
                assert m['source_frame_ids']==[edge['i'],edge['j']]
                label=transform_label(m['T_rel'],np.linalg.inv(gt[edge['i']])@gt[edge['j']])
                assert label['validity']['valid'] and label['label']==m['labels']['label']
                labels.append(label['label']);strict.append(label['gt_translation_error_m']<=1 and label['gt_rotation_error_deg']<=5)
            for name in ['odometry','pgo']:
                poses=np.asarray(epm.load_kitti_format(str(dest/('odom_poses.txt' if name=='odometry' else 'optimized_poses.txt'))))
                assert abs(anchored_numpy_ate(gt,poses)-fresh[name]['ape_aligned_rmse'])<1e-8
                for T in poses:assert rotation_validity(T,1e-4)['valid']
            full[seq]=dict(ter=fresh['pgo']['camera_kitti']['kitti_ter_pct'],rer=fresh['pgo']['camera_kitti']['kitti_rer_deg100m'],ate=fresh['pgo']['ape_aligned_rmse'],
                first_ape=fresh['pgo']['ape_unaligned_rmse'],accepted=len(edges),attempts=len(starts))
            save(BASE/f'full-{seq}-metrics.json',fresh)
            checks.append(f'{seq}-full: matching frontend, frame/source binding, measurement edges and metrics')
    oldrows={r['sequence'].replace('kitti',''):r for r in baseline['sequences'] if r['sequence']!='poss'}
    oldmean=dict(ter=float(np.mean([oldrows[s]['camera_pgo']['kitti_ter_pct'] for s in seqs])),ate=float(np.mean([oldrows[s]['pgo']['ape_aligned_rmse'] for s in seqs])))
    newmean={k:float(np.mean([full[s][k] for s in seqs])) for k in ['ter','ate']} if selected else None
    successor=bool(selected and all(newmean[k]<oldmean[k] for k in oldmean))
    decision='FREEZE_DEVELOPMENT_SUCCESSOR' if successor else 'NO_SUCCESSOR'
    save(BASE/'validation.json',dict(passed=True,checks=checks,selected=selected,decision=decision,old_mean=oldmean,new_mean=newmean,
        accepted_historical_labels=dict(Counter(labels)),accepted_strict_correct=sum(strict),accepted_strict_incorrect=len(strict)-sum(strict),
        execution=execution,validator_sha256=sha(__file__),
        amendment='E0-AMENDMENT-01: anchored independent NumPy ATE crosscheck; see AMENDMENT_01.md'))
    if successor:
        save(BASE/'development_baseline_v2.json',dict(name='e0-development-v2',selection=selected,scope='Observed KITTI00/05/06 development, no independent confirmation',
            config=read(BASE/f'full-00-{selected}/run_manifest.json')['config'],sequences=full,execution_freeze_sha256=sha(BASE/'freeze.json'),
            original_baseline='core-baseline-v1 retained as historical canonical comparator',POSS='unchanged, separate original convention'))
    lines=['# E0 frontend alignment: validated development comparison','',f'Decision: **{decision}**. Selected arm: **{selected}**.','',
      'These sequences and the prior meeting combined arm were already observed. No independent confirmation or first-tier claim.','',
      '## Fresh odometry results','', '| Sequence | Arm | Camera ter % | Aligned LiDAR ATE m |','|---|---|---:|---:|']
    for s in seqs:
        for a in 'OABC':lines.append(f"| {s} | {a} | {metrics[s][a]['ter']:.6f} | {metrics[s][a]['ate']:.6f} |")
    lines+=['','O: original; A: correction only; B: KISS ranges/voxel only; C: combined.','',
            '## Selected frontend and full system','', '| Sequence | Odom ter % | Full ter % | Odom ATE m | Full ATE m | Accepted |','|---|---:|---:|---:|---:|---:|']
    for s,v in full.items():lines.append(f"| {s} | {metrics[s][selected]['ter']:.6f} | {v['ter']:.6f} | {metrics[s][selected]['ate']:.6f} | {v['ate']:.6f} | {v['accepted']} |")
    lines+=['',f'Historical full mean: {oldmean}. New full mean: {newmean}.',
        '',f'Accepted historical labels: {dict(Counter(labels))}; strict correct/incorrect: {sum(strict)}/{len(strict)-sum(strict)}. Historical safe is not strict correctness or guaranteed graph benefit.',
        '', 'Frontend engineering gains must not be attributed to a new RAP method. Per-sequence and odometry-to-full regressions remain visible above. Original O trajectories reproduced within the frozen tolerance.',
        '', 'Source/input freeze, exact frame identities, geometry, NumPy alignment crosscheck, selection arithmetic and full measurement-edge consistency passed. New source snapshot identifies uncommitted execution code. No production edits or Git synchronization.',
        '', 'The full-system settings are K1, five steps, candidate budget12 and NMS0. Prior HC table K4/NMS10 introductory prose was incorrect; archived artifacts were not rewritten.',
        '', 'E0-AMENDMENT-01: the frozen validator\'s unanchored NumPy ATE crosscheck exceeded its 1e-8 tolerance due to float64 gauge conditioning (5.83e-7); anchored crosscheck agrees to 4.4e-12 and frozen-code recomputation matched exactly. See AMENDMENT_01.md.',
        '', 'Next research task: F1 engineering preflight; no backend tuning or extra frontend sweep is authorized by these results.']
    (BASE/'REPORT.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    x=np.arange(3)
    for ax,key,label in zip(axs,['ter','ate'],['Camera translational drift (%)','Aligned LiDAR ATE (m)']):
        ax.bar(x-.23,[oldrows[s]['camera_pgo']['kitti_ter_pct'] if key=='ter' else oldrows[s]['pgo']['ape_aligned_rmse'] for s in seqs],.23,label='Original full')
        ax.bar(x,[metrics[s][selected][key] for s in seqs],.23,label='Selected odometry')
        ax.bar(x+.23,[full[s][key] for s in seqs],.23,label='Selected full')
        ax.set_xticks(x,list(seqs));ax.set_ylabel(label);ax.set_xlabel('KITTI sequence');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axs[0].legend(fontsize=8);fig.suptitle('E0: engineering alignment on observed development sequences')
    fig.savefig(BASE/'results.png',dpi=170);plt.close(fig)
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())<20*2**30
    (BASE/'INCOMPLETE').unlink()
    save(BASE/'artifact_hashes.json',{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()})
    print(decision,selected,newmean,flush=True)
if __name__=='__main__':main()
