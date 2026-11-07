"""Create compact, traceable thesis tables from completed saved evidence."""
import hashlib
import json
from pathlib import Path

HOME=Path('/mnt/e/githouse/RAP-main')
BASE=HOME/'docs/maintenance/2026-09-13'


def main():
    out=BASE/'paper-evidence-v2'
    out.mkdir(exist_ok=False)
    sources={}
    def read(p):
        raw=p.read_bytes();sources[str(p)]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    baseline=read(BASE.parent/'2026-09-11/core-baseline-v1/registry.json')['sequences']
    comparison=read(BASE/'o3-comparator-01/summary.json')
    validation=read(BASE/'o3-comparator-01/association_validation.json')
    assert validation['attempts']==80 and validation['failed']==0
    assert not (BASE/'o3-comparator-01/INCOMPLETE').exists()
    lines=['# Thesis results and evidence v2','',
        'Compiled after the experiments on 2026-09-13. This is a reporting consolidation, not a new preregistration. Keep the default offline system and the O3 source-balanced comparison separate. All four sequences are observed development data.','',
        '## Main default system: complete raw-scan reruns','',
        '| Sequence | Frames | Accepted loops | Odom first APE m | RAP first APE m | RAP aligned APE m | Odom translation drift % | RAP translation drift % |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in baseline:
        a=r['camera_odometry'] or r['odometry'];b=r['camera_pgo'] or r['pgo']
        lines.append(f"| {r['sequence']} | {r['frames']} | {r['accepted']} | {r['odometry']['ape_unaligned_rmse']:.6f} | {r['pgo']['ape_unaligned_rmse']:.6f} | {r['pgo']['ape_aligned_rmse']:.6f} | {a['kitti_ter_pct']:.6f} | {b['kitti_ter_pct']:.6f} |")
    lines+=['','The same fixed budget-12 RAP loop system improves first-pose APE over odometry on all four sequences. Camera translation drift worsens on KITTI 06 and 00. Thus global APE gains do not imply universal local drift gains. These full runs persist source-frame identities; legacy frontend assumptions are not used for this table.','',
        '## O3 fixed-budget source allocation: matched registrars','',
        'O3 allocates up to six proximity and six distinct SC candidates with deterministic backfill. Its 40 RAP attempts are all accepted. O3 failed the predeclared adoption screen and remains an experimental arm.','',
        '| Sequence | Method | Accepted / attempted | First APE m | Aligned APE m | Translation drift % | Rotation drift deg/100m |',
        '|---|---|---:|---:|---:|---:|---:|']
    compact=[]
    for r in comparison:
        count=r['arms']['identity']['candidates']
        for method,m,n in [('RAP',r['rap'],count),('ICP identity',r['arms']['identity']['metrics'],r['arms']['identity']['accepted']),('ICP odometry',r['arms']['odometry']['metrics'],r['arms']['odometry']['accepted'])]:
            d=m.get('camera_kitti',m)
            lines.append(f"| {r['sequence']} | {method} | {n}/{count} | {m['ape_unaligned_rmse']:.6f} | {m['ape_aligned_rmse']:.6f} | {d['kitti_ter_pct']:.6f} | {d['kitti_rer_deg100m']:.6f} |")
            compact.append(dict(sequence=r['sequence'],method=method,accepted=n,attempted=count,first_ape_m=m['ape_unaligned_rmse'],aligned_ape_m=m['ape_aligned_rmse'],translation_drift_pct=d['kitti_ter_pct'],rotation_drift_deg100m=d['kitti_rer_deg100m']))
    lines+=['','Drift uses the KITTI camera frame; POSS uses a custom LiDAR-frame segment measure. Do not pool them or call POSS an official KITTI benchmark. First APE uses first-pose LiDAR alignment; rigidly aligned APE is distinct.','',
        'RAP has lower first-pose APE than either ICP arm on POSS, KITTI 06 and 00. Both ICP arms have lower first-pose APE on KITTI 05. Secondary metrics do not follow this ordering: for example, identity ICP has slightly lower aligned APE on POSS and KITTI 00, and both ICP arms have lower aligned APE and camera translation drift on KITTI 06.','',
        'Identity ICP accepts 36/40; its four dangerous measurements (three on KITTI 05, one on KITTI 00) are rejected. Odometry ICP accepts 40/40, all safe. All 80 attempts complete and all 76 accepted edges exactly reference their logged measurements. A safe label means pose error <= 5 m and <= 10 degrees, not negligible bias or guaranteed trajectory improvement.','',
        'These are fixed-gate system comparisons with potentially different accepted sets. Odometry ICP receives a pose prior; RAP and identity ICP receive no external relative-pose prior. Do not claim superiority over all classical/global registration, unseen domains or independent statistical risk guarantees. ICP registration-only times are not comparable to full RAP-stage wall times as a speed ratio.','',
        '## Interpretation for the thesis','',
        'The evidence supports a traceable offline integration of frozen pretrained RAP with KISS-ICP, candidate retrieval, geometric gating and graph optimization. No task-level fine-tuning is performed. The system improves global trajectory error on the four development sequences, while registration choice, candidate allocation and evaluation metric affect the result.','',
        'O1 ICP refinement, O2 increased budget and O3 source balancing each yield mixed outcomes and do not replace the default. The clean-cohort backend ablation was negligible, so robust weighting is an engineering choice rather than a demonstrated performance contribution. Do not choose the best method separately for each sequence and present that combination as one system.','',
        '## Evidence map','',
        '- Main full baseline: [report](../../2026-09-11/core-baseline-v1/REPORT.md) and its registry/source manifests.',
        '- O1-O3: [synthesis](../OPTIMIZATION_SYNTHESIS.md), preserving secondary regressions.',
        '- O3 matched comparison: [report](../o3-comparator-01/REPORT.md), per-attempt logs, source_manifest.json and association_validation.json.',
        '- Candidate/measurement confounding: [common-edge-fixed diagnostic](../o3-common-fixed-01/REPORT.md); explicitly post-hoc.',
        '- Earlier proximity-priority ICP comparison: [report](../../2026-09-11/comparator-01/REPORT.md); frozen legacy frontend scope, separate from O3.',
        '- Runtime: full-run timing includes warmed reads/map export and clock-accounting limitations; no real-time claim.',
        '- Deferred: independent backup, checkpoint training membership, optional statistical validation and unused ROS/Spires features.','',
        'Next deliverable: draft the thesis experimental-results section using these fixed tables and measured limitations. Do not launch further parameter sweeps merely to remove negative results. Any additional experiment needs a specific unresolved question.']
    for p,h in sources.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    (out/'registry.json').write_text(json.dumps(dict(scope='retrospective reporting consolidation',o3_rows=compact,source_hashes=sources),indent=2))
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(str(out/'RESULTS.md'))


if __name__=='__main__':main()
