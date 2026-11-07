"""Package MDC0 accounting and append current handoff facts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np
MAIN=Path(__file__).resolve().parents[2];BASE=MAIN/'docs/maintenance/2026-10-07/metric-conflict-decomposition-01';LC=MAIN/'docs/maintenance/2026-10-07/retrieval-placement-audit-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(x,encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()
def main():
    r=read(BASE/'results.json');v=read(BASE/'validation.json');f=read(BASE/'freeze.json');assert v['passed'] and not (BASE/'INCOMPLETE').exists()
    assert read(BASE/'validation_seal.json')['results_sha256']==sha(BASE/'results.json')
    stages=[f,r,v];wall=sum(x['wall_s'] for x in stages);rss=max(x.get('peak_rss_bytes',0) for x in stages)
    lines=['# MDC0: why aligned positions and segment ter can disagree','',
      'Status **VALIDATED_ACCOUNTING**, evaluator-only and post-hoc to the observed LC0 pattern. It is not a new method, metric replacement or calibrated uncertainty result.','',
      '## Concrete finding','',
      'The development H oracle lowers both component energies under BOTH compulsory gauges, while total mean squared segment translation error increases. Its negative orientation/chord cross term becomes substantially less negative. Under aligned gauge A, P shows the same pattern. Thus lower aligned position error does not imply lower segment ter, and blaming only worse orientation is unsupported.','',
      'The exact identity is z=u+v and ||z||^2=||u||^2+||v||^2+2u dot v. z is the unchanged official segment translation error divided by nominal length. u is orientation-associated, v is endpoint-chord-associated. Rotation and translation errors can cancel. These are signed descriptive terms, not independent physical causes, covariance or nonnegative error shares.','',
      '## Complete cohort accounting','',
      'Units below are mean squared segment fractions times10000 (%^2), averaged equally across sequences within each cohort. Total is not the square of mean ter. F uses original first-pose gauge; A additionally rigidly aligns estimated camera positions, without scale or subsequent re-anchoring. A does not replace LiDAR ATE.','',
      '| Cohort | Gauge | Arm | Orientation | Chord | Signed cross | Total |','| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for g,m in r['cohort_means'].items():
        for gauge in ['F','A']:
            for a in ['N','C','P','H']:
                d=m[a][gauge];lines.append(f"| {g} | {gauge} | {a} | {d['orientation_squared_pct']:.6f} | {d['chord_squared_pct']:.6f} | {d['cross_squared_pct']:+.6f} | {d['total_squared_pct']:.6f} |")
    lines += ['', 'Aligned development N->H: orientation.409658->.376807, chord.285319->.090316, cross-.394903->-.052215, total.300074->.414908. Reductions in the first two terms are outweighed by the loss of cancellation. In F the components have different numerical values, while the same total/ter is preserved. Components must not be interpreted as unique causal shares.','',
      'P transfer mean ter improves slightly while mean squared segment error increases (.337161->.339000), showing why squared accounting cannot silently replace the official mean-norm criterion. All official LC0 metrics/gates remain exactly as validated.','',
      '## Source and independent validation','',
      f"72 identities froze before52 NPZs:48 sequence/arm/gauge arrays and4 fixed analytic fixtures. All59184 segment-gauge vectors reconstruct independently from full4x4 relative errors; all29592 original segment identities and ter values remain. Native Kabsch alignment independently reproduces by Horn quaternion eigenanalysis (maxdelta{v['max_alignment_delta']:.3e}); maxvector{v['max_vector_delta']:.3e}, maxsummary{v['max_summary_delta']:.3e}. Total gauge invariance and signed accounting closure pass. No failure/repair.",'',
      'Fixtures include perfect, chord-only, orientation-only and constant-global-rotation cancellation. The last has nonzero component terms but zero total error, preventing an orientation component from being mistaken for an independently harmful measurement.','',
      f"Successful stages{wall:.3f}s,peak{rss/2**30:.3f}GiB;1h/4GiB/100MiB caps pass. Only sealed LC0 trajectories and unchanged evaluator GT/calibration are read; no graph/inference/new feature/head/fit or new trajectory.",'',
      '## Next decision','',
      'Prioritize a distinct source of accurate coupled local relative motion. TR0 is a four-window GT-free extraction/invariance preflight for the already inspected512-D joint-token interface, PLANNED_NOT_IMPLEMENTED. It can establish a source hook, not learnability. A later physically grounded small readout needs explicit fitting scope, matched trained descriptor/independent-token controls, both rotation and translation plus actual ter/ATE, and honest data exposure. See NEXT_ROUND_PLAN.md.','',
      'The accounting does not prescribe a new weight/uncertainty matrix, prove a backend defect, identify individual-edge causal effects, license old interpolation/shape/R3/feedback rescues or establish RAP originality.09 physical discrepancy and unknown checkpoint membership remain. No training, production/default/model/manuscript edit, acquisition/install, commit/Git.','']
    write(BASE/'REPORT.md','\n'.join(lines))
    status=dict(stage='MDC0',status='VALIDATED_ACCOUNTING',post_hoc_evaluator_only=True,frozen_identities=72,segment_gauge_vectors=59184,fixtures=4,gauge_invariance=True,physical_causality_established=False,new_metric_gain=False,next='TR0 four-window GT-free token extraction/invariance preflight PLANNED_NOT_IMPLEMENTED',training=False,inference=False,production_edit=False,git_sync=False)
    write(BASE/'STATUS.json',json.dumps(status,indent=2)+'\n')
    write(BASE/'HANDOFF.md',f'''# MDC0 final handoff

Status VALIDATED_ACCOUNTING, post-hoc evaluator-only, no failure or INCOMPLETE.
Read REPORT.md,PROTOCOL.md,NEXT_ROUND_PLAN.md,STATUS.json and freeze/results/
output_seal/validation/validation_seal.72 identities,52 NPZs,59184 vectors.
Independent full-pose error and Horn alignment validate every vector/summary;
max vector{v['max_vector_delta']:.3e}, alignment{v['max_alignment_delta']:.3e}.
All official LC0 segment ter values and both-gauge total errors unchanged.

Development H improves orientation/chord squared terms in both gauges but loses
their negative cancellation, increasing total segment error. Under aligned A,
P has the same effect. Gauge dependence prevents unique physical attribution;
do not infer worse orientation alone, covariance calibration or a backend bug.
No graph, model or new trajectory. Successful stages{wall:.3f}s,peak{rss/2**30:.3f}GiB.

LC0 remains VALIDATED_NEGATIVE; complete native exposure and original71
attempts independently reconstruct. Current native pre-cap near-query coverage
281/285 is conditional on15m/200/source keyframes, not physical recall;10 has
zero eligible near pair. All earlier stopped arms/banks/official labels remain.

Next TR0 is only a separately frozen four-window local joint-token extraction/
native-invariance preflight plan. No selection/freeze/runner/token outputs yet.
No fitting authorized. A readout must generate measured-point correspondences,
use matched learned controls and validate coupled local motion and system
ter/ATE. Checkpoint membership/09 physical discrepancy/originality unresolved.
Preserve both original HEADs/branches/dirty work and all frozen outputs. No
training, production/default/model/manuscript edit, acquisition/install/Git.
''')
    payload=sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file());assert payload<=100*2**20
    write(BASE/'EXECUTION_SUMMARY.json',json.dumps(dict(total_wall_s=wall,peak_rss_bytes=rss,artifact_bytes=payload,stages={k:dict(wall_s=x['wall_s'],peak_rss_bytes=x.get('peak_rss_bytes')) for k,x in zip(['freeze','analysis','validation'],stages)}),indent=2)+'\n')
    # Review a sentinel convention on existing sealed scores, not a new method.
    bs=read(LC/'bank_seal.json')['files'];mins=[];count=0
    for s in ['00','05','06','07','09','10']:
        p=LC/f'bank/{s}/exposure.npz';assert sha(p)==bs[f'{s}/exposure.npz']
        with np.load(p,allow_pickle=False) as z:
            scored=z['ring_rank']<=10;sd=z['sc_distance'];mins.append(float(np.min(sd[scored])));count+=int(np.sum(scored))
            assert np.array_equal(scored&(sd<.25),(sd>=0)&(sd<.25))
    assert count==15914
    write(LC/'SEALED_SCORE_REVIEW.json',json.dumps(dict(utc=utc(),scope='POST_HOC_REVIEW_OF_SEALED_VALUES_ONLY',scored_pairs=count,min_scored_distance=min(mins),native_pass_mask_equals_sentinel_mask_in_actual_bank=True,bank_seal_sha256=sha(LC/'bank_seal.json'),gt_read=False),indent=2)+'\n')
    phase=MAIN/'docs/maintenance/2026-10-07/PHASE_RECORD.md'
    text=f'''

## LC0 and MDC0 continuation (2026-10-07)

Owner requested next-stage progress and then said continue. LC0 freezes1873
identities/1800 raw scans, seals44-file GT-free bank before independent source
validation and GT. All319728 eligible pairs/15914 SC scores/71 original attempt
IDs and order reconstruct;2160000 descriptor pixels and36000 ring keys exact.
All58 native accepted edges/graphs reproduce;29592 metrics and148 oracle edges
independently validate (graph5.963e-10,aggregate5.896e-13). No failure/repair.
Native pre-cap near queries281/285;4 omissions00,10 near pairs0/8048 at frozen
15m/200-frame/source-keyframe definition. This is a position proxy, not recall.
LC0 VALIDATED_NEGATIVE, NO_FIXED_BUDGET_PLACEMENT_SIGNAL. P/H development ATE
gain55.241/56.005% but ter regression+.065168/.075811pp; transfer ter gain
.007136pp below.01;00/05 ter and06 ATE safety fail. Stop exact fixed-budget
distribution/noise/radius rule without rescue. Stages594.513s,peak0.116GiB.

Owner-authorized separate MDC0 freezes72 identities before52 evaluator-only
NPZs. All59184 segment-gauge vectors/four fixtures validate via full-pose
solves and independent Horn alignment. Max vector{v['max_vector_delta']:.3e},
alignment{v['max_alignment_delta']:.3e}, summary{v['max_summary_delta']:.3e}.
Orientation/chord terms AND signed cross exactly reconstruct unchanged ter;
development H improves both component energies under both gauges, while lost
negative cancellation raises total. Gauge-dependent accounting is not causal
shares/calibrated covariance/backend fault. Stages{wall:.3f}s,peak{rss/2**30:.3f}GiB.

Next TR0 four local-window joint-token extraction/native-invariance preflight
PLANNED_NOT_IMPLEMENTED; no source selection/protocol/runner/freeze/tokens or
fitting. New source targets accurate coupled local relative motion, distinct
from stopped native R3/RAD1/support/FDI/D1. Read both new NEXT_ROUND_PLANs.
No training/production/default/model/manuscript edit, acquisition/install,
commit/Git. Both original HEADs/branches and dirty work preserved. All prior
sealed banks/stops/official labels,09 discrepancy,unknown checkpoint split and
original-breakthrough requirement remain.
'''
    with phase.open('a',encoding='utf-8') as fp:fp.write(text)
    print('MDC0 packaged',wall,'s',payload,'bytes; LC0 score sentinel review passed')
if __name__=='__main__':main()
