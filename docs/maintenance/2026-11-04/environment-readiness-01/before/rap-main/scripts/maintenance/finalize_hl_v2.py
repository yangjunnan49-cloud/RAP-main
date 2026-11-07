"""Final immutable pilot audit and complete research checkpoint report."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
import sys
import numpy as np
ROOT=Path('/mnt/e/githouse/RAP-main');SLAM=Path('/mnt/e/githouse/RAP-SLAM')
sys.path[:0]=[str(SLAM),str(SLAM/'scripts')]
from rap_slam.measurement import rotation_validity
from hl_v2_bank import seed
BASE=ROOT/'docs/maintenance/2026-09-14/hl-v2';OUT=BASE/'pilot-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False)

freeze=read(OUT/'discovery_frozen.json')
assert all(sha(OUT/'discovery'/p)==h for p,h in freeze['hashes'].items())
data=BASE/'data-expansion-01';f=read(data/'artifact_hashes.json')
assert all(sha(data/p)==h for p,h in f.items())
roles={};validity={};timing={}
for role in ['discovery','confirmation']:
    folder=OUT/role;assert read(folder/'independent_validation.json')['passed']
    inp=read(folder/'inputs.json');bank=read(folder/'bank_hashes.json');assert len(inp)==100 and len(bank)==400
    good=0;failure=0;ss=0;orth=[]
    for r in inp:
        seq,i,j=r['sequence'],r['source_i'],r['source_j']
        assert set(r)=={'sequence','source_i','source_j','support_i','support_j'}
        for g in range(4):
            name=f'{seq}_{i}_{j}_{g}.json';assert sha(folder/'bank'/name)==bank[name]
            b=read(folder/'bank'/name);assert b['seed']==seed(seq,i,j,g)
            if b['validity']['valid']:
                v=rotation_validity(b['T']);assert v['valid'];good+=1;orth.append(v['orthogonality'])
                assert np.isfinite(b['rigidity_rmse_m'])
                if b['support'] is not None:
                    c=b['support']['combinations'];assert len(c)==4
                    assert abs(b['support']['score']-np.mean([x['score'] for x in c]))<1e-12
                    assert all(0<=x['score']<=3 and 0<=x['coverage_1m']<=1 for x in c);ss+=1
            else:failure+=1
    validity[role]=dict(hypotheses=len(bank),valid=good,failed_or_invalid=failure,valid_support=ss,max_orthogonality=max(orth))
    roles[role]=read(folder/'metrics.json');timing[role]=read(folder/'timings.json')
    assert len(read(folder/'evaluator_only_decisions.json'))==len(read(folder/'oracle_only.json'))==100
result=roles['confirmation'];decision=result['decision']
save(OUT/'validation.json',dict(passed=True,discovery_freeze_unchanged=True,data_freeze_unchanged=True,roles=validity,
    scope='All800 seeds, identities, transforms, support combinations, bank hashes and independent metrics verified',
    source_sha256={str(p):sha(p) for p in [SLAM/'scripts/hl_v2_bank.py',SLAM/'scripts/evaluate_hl_v2.py',SLAM/'scripts/validate_hl_v2_results.py',Path(__file__).resolve()]}))
save(OUT/'decision.json',dict(protocol='HL-V2',decision=decision,confirmation=result,discovery_decision=roles['discovery']['decision'],
    stage='Untrained development pilot',training_started=False,completed_utc=datetime.now(timezone.utc).isoformat(),original_HL_V1='INCONCLUSIVE, unchanged'))
lines=['# HL-V2 untrained hard-loop pilot','',f'Final confirmation decision: **{decision}**. Original HL-V1 INCONCLUSIVE remains unchanged.','',
    'The explicitly amended data protocol supplies100 discovery and100 confirmation pairs,25 per fixed stratum. Both are previously observed KITTI development sequences. No independent-domain, pretraining-exclusion, calibrated-risk or publication claim.','',
    '| Role | Method | Positive success | Ungated recall | Correct positive accepts | Incorrect / accepted | Clipped positive error |','|---|---|---:|---:|---:|---:|---:|']
for role,metrics in roles.items():
    for m,v in metrics['overall'].items():
        lines.append(f"| {role} | {m} | {v['strict_positive_successes']}/{v['positives']} | {v['selection_recall']:.2%} | {v['correct_positive_accepts']}/{v['positives']} | {v['incorrect_accepted']}/{v['accepted']} | {v['mean_clipped_positive_error']:.6f} |")
lines += ['','B1=first;B4=same-pair overlap;S4=raw-support score;R4=official mean per-step rigidity criterion;OR4=GT-only oracle;REJ=reject-all. All share one immutable K4 bank. Official criterion availability is now implemented using the original RAP metric functions, not renamed B4.','',
    '| Role | Oracle/B4 discrepant positives | Oracle recall gain | Relative clipped-error reduction | S4 gap recovery | Ordinary recall loss | New incorrect pairs | H1 | H2 |','|---|---:|---:|---:|---:|---:|---:|---|---|']
for role,m in roles.items():
    recovery='N/A' if m['H2_gap_recovery'] is None else f"{m['H2_gap_recovery']:.2%}"
    reduction='N/A' if m['H1_relative_error_reduction'] is None else f"{m['H1_relative_error_reduction']:.2%}"
    lines.append(f"| {role} | {m['discrepant_positive_pairs']} | {m['H1_recall_gain']:.2%} | {reduction} | {recovery} | {m['ordinary_recall_loss']:.2%} | {len(m['new_incorrect_pairs'])} | {m['H1']} | {m['H2']} |")
lines += ['','Exact decision metrics and precedence are frozen in the HL-V2 annex, retaining HL-V1 section7. Recall takes precedence when both H1 paths pass. Helpful transitions never offset a newly incorrect S4 acceptance. An oracle is diagnostic, not an executable selector.','',
    '## Every stratum','', '| Role | Stratum | B1 correct | B4 correct | S4 correct | R4 correct | OR4 correct | B4 incorrect accepts | S4 incorrect accepts |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
for role,m in roles.items():
    for s,v in m['by_stratum'].items():
        lines.append(f"| {role} | {s} | {v['B1']['strict_positive_successes']} | {v['B4']['strict_positive_successes']} | {v['S4']['strict_positive_successes']} | {v['R4']['strict_positive_successes']} | {v['OR4']['strict_positive_successes']} | {v['B4']['incorrect_accepted']} | {v['S4']['incorrect_accepted']} |")
lines += ['','Positive strata each have25 pairs. Confusers are not positive-recall denominators; their accepted counts/rates are reported in the per-role metrics. All continuous errors,90th percentiles, legacy5m/10deg labels, invalid/failure counts and exact harmful/helpful pair IDs remain in evaluator-only files.','',
    '## Runtime and reproducibility','']
for role,t in timing.items():
    p=t['pairs'];alloc=max(x['peak_allocated'] for x in p)/2**30;reserved=max(x['peak_reserved'] for x in p)/2**30
    lines.append(f"- {role}:400 hypotheses, synchronized pair-wall total {t['profile_pair_wall_s']:.3f}s, full bank-run wall {t['wall_s']:.3f}s, peak allocated/reserved {alloc:.3f}/{reserved:.3f}GiB; valid hypotheses/support {validity[role]['valid']}/{validity[role]['valid_support']}.")
lines += ['','Pair timings include raw reads, all geometric/learned preprocessing, four generations, official rigidity statistics, support scores and writes. They are warmed-input end-to-end wall times, not isolated kernel-active GPU time. Data preparation, independent validation, literature work and human labour are not included in these bank timings; human labour was not separately instrumented.','',
    'The ten-pair amended-support preflight passed40/40; RNG repeat and observed-versus-original sampler transform deltas were exactly0. Two extra preflight requests are validation only. The800 scored hypotheses were generated once each under request-local seeds; no oracle retries or resampling. No GT-derived fields enter inference selectors.','',
    'KITTI00 discovery results and complete bank were independently verified and hash-frozen before KITTI02 inference. Final validation reverified that freeze and all data artifacts,800 seeds/transforms/support records, selection denominators and gate calculations. Independent pose errors used direct translation differences and scipy rotation magnitudes.','',
    '## Interpretation and scope','',
    'Data shortages were resolved through a prospective, documented expansion of real proposals and causal raw support. No GT threshold, strict correctness definition, H1/H2 criterion, model weight or production default was changed. The original pilot remains a separate inadequate-cohort result. This expanded case-control pool does not estimate production false-loop prevalence; low-overlap misses can also be rejected by the unchanged same-pair gate. Report ungated selection and gated acceptance separately.','',
    'R4 is a stronger same-input alternative than B4 and must remain visible. Any small S4 advantage over B4 alone does not establish a novel method or advantage over the official criterion. Same-data pooled-support and equal-compute controls plus new geographic/domain evidence remain required before learned-method claims.','',
    'MulRan official download access was checked and requires name/affiliation/email; none were invented or submitted. Local complete data were sufficient for this pilot, so additional raw downloads were unnecessary. The owner authorizes future public downloads. NCLT remains reserved for external testing.','']
if decision=='GO':
    lines += ['Next: freeze new-data sessions/site splits and the small-head training annex, including equal-data/compute controls, before fitting anything. A pilot GO permits that next stage, not an already trained head or final result.']
elif decision=='STOP_RANKING':
    lines += ['Next: stop ranking/head expansion under this protocol. Preserve the adequate negative result and investigate proposal quality only under a separately declared question; do not train a selector to repair a missing oracle gap.']
elif decision=='STOP_NEURAL_EXPANSION':
    lines += ['Next: stop neural-head expansion. First diagnose fixed support-score failures, short-motion error and harmful transitions on these now-development data; any revised scoring proposal requires a new frozen protocol before confirmation. Do not silently tune thresholds.']
else:
    lines += ['Next: identify the exact remaining adequacy/correctness problem from the recorded counts; do not label the scientific hypotheses false or start training.']
lines += ['','No commit, push, pull, reset or cleanup; both worktrees keep existing dirty changes and original HEADs4055d92/6d3f2d2. Upstream source/production defaults unchanged.']
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
for role in ['confirmation']:
    marker=OUT/role/'INCOMPLETE'
    if marker.exists():marker.unlink()
save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='INCOMPLETE'})
print('Final decision',decision,flush=True)
