# PG-V1: short-submap proposal context

Declared 2026-09-15 before new cohort labels or proposal outcomes. The owner
approved proceeding after the direction synthesis. This selects proposal-generation
context as the single next question. The rejected support-selector route and
neural expansion remain stopped. No rejection fitting or manuscript work.

## Question

Does providing the same causal neighbouring scans during generation, rather than
only during later scoring, increase correct-pose availability and improve official
RAP selection under a fixed point/call budget? This is an engineering feasibility
screen, not a novelty claim: pooled submaps and native RAP multiview capabilities
are established context in the existing literature matrix. No new architecture.

## PG0: data eligibility before inference

Discovery: exact frozen HL-V2 KITTI00 100-pair membership, already observed
development data. Confirmation: complete local KITTI09, source IDs0-1590, audited
under unchanged HL-V2 proposals/support/strata. Sampling/band hash prefix PG-V1;
target25 per stratum, max3 per query, minima60 total and10 per stratum. The exact
09 membership must be frozen before any PG-V1 outcome. No00/02/08 confirmation.
No random split of earlier sequences, synthetic negatives or silent resampling.

Run data-only eligibility and independent reconstruction first. If09 fails minima,
finish PG0 as INCONCLUSIVE_DATA and do not start the scored experiment. Preserve
all shortages. A public repeated-route dataset then needs an explicit access/
adapter/split annex; do not repeatedly try unsupported local sequences or change
strata to force sufficiency. NCLT remains external; do not invent MulRan identity.
Data cap: one new sequence1591 scans, one hour,10GiB artifacts. Verify frozen
parents before reuse. The original discovery membership already meets minima.

## Frozen geometry and arms after PG0 passes

For each anchor i, transport the two original past supports into its frame using
the saved local odometry transforms A_s=inv(O_i)O_s. Concatenate raw anchor points
and both transported support clouds. Remove<1.5m points in each original scan
frame before transport, never by GT or a global loop-relative odometry transform.
The pooled coordinates remain in the anchor frame. Use the same .4m voxel,
outlier20/2.5 and cap4000 preprocessing/learned features as anchor RAP. Cap after
pooling; do not allocate4000 per support. Record each raw/processed point count.

Generate K4/five-step frozen RAP for both arms, IEEE protection and official
rigidity observer retained. Anchor A uses only raw generating anchors. Context P
uses the pooled three scans per side. Both get two capped parts and four calls.
Use PG-V1 hypothesis seeds for09 (first8 SHA256 hex digits modulo2^31 of
PG-V1|hypothesis|kitti|09|source_i|source_j|generation). Use the same seed per
generation across arms, a common-random-number control, not an independence claim.
For discovery, reuse exact old anchor hypotheses/seeds and use those same seeds
for its new pooled generations. No regeneration of old00 anchors or oracle retries.

Report A1/A-R4/A-OR4 and P1/P-R4/P-OR4. R4 chooses minimum official average
per-step rigidity within its own bank; do not compare rigidity magnitudes across
arms to create a new selector. Oracles are evaluator-only and minimize the
unclipped max(RTE/1m,RRE/5deg). Also report A-S4: unchanged support score on A's
hypotheses, with the identical six raw observations available to P. This is the
equal-data 'generation versus verification' control; do not train or tune S4.

All arms' acceptance uses the SAME anchor-only seed42 geometric clouds and
existing overlap>=.7/mean-distance<=2.5 gate on the selected anchor-frame transform.
Never gate P on its pooled-cloud overlap, which would confound added context
with acceptance. This prospective common-gate evaluation differs from old
per-generation diagnostic point samples; old results remain unchanged.
Strict<=1m/<=5deg and legacy5m/10deg labels stay separate. Failures stay in their
original denominators with clipped error5; no replacement or fallback generation.

## Controls, cost and preflight

Equal point/call budget is not exact equal wall time. Measure synchronized
end-to-end A-R4, A-S4 and P-R4 costs on fresh09 including preprocessing, reads,
support assembly and score cost. Share the same raw-read cache policy. Report
both generation-only and full costs, not historical00 timings as matched current
measurements. P uses extra observations by design; compare A-S4 on those same
observations before attributing benefit to where context is used.

Before scored execution: synthetic nontrivial frame transport/relative-pose
tests; point-cap checks; no GT fields in model inputs; official observer source
verification; first10 round-robin00 pairs for pooled resource/geometry preflight,
retaining those exact generations in the full bank. Freeze source/validation
identities before full scoring. Independently validate all selections and pose
metrics; freeze discovery report before09 generation. No support-distance sweep.

## Confirmation screen

Primary headroom: P-OR4 strict positive recall must improve A-OR4 by>=5pp.
Primary executable benefit: P-R4 recall must improve A-R4 by>=3pp and be no lower
than A-S4. Require ordinary recall loss<=2pp and no newly incorrectly accepted
pair relative to either A-R4 or A-S4. Helpful transitions never offset harmful ones.
Report clipped error and correct-accept recall regardless of these conditions;
do not substitute an error reduction for failed recall gates after outcomes.

Practical budget screen: P-R4 full09 wall<=1.25 times A-S4 full09 wall at equal
calls/point cap. Exceeding that envelope is NOT a matched-cost success; record
COST_SCREEN_FAIL even if geometry improves. This is an explicit tolerance, not
a claim of exact equal time. All scientific and budget conditions are needed
for CONTEXT_SIGNAL; otherwise NO_CONTEXT_SIGNAL within this fixed protocol.
Data/correctness/resource failures are INCONCLUSIVE, not a scientific negative.

Inference cap:100 pairs per role;1200 new generations maximum (400 pooled00,
400 anchor09,400 pooled09) plus inherited400 anchors; one RTX5070;2 GPU-process
hours;12GiB allocated VRAM;20GiB new artifacts. Preserve partial failures.
Even CONTEXT_SIGNAL does not authorize a learned head or production replacement.
Strong registrar/system baselines and further independent evidence remain future.

Keep exclusive output paths, exact hashes, INCOMPLETE until checks finish, all
strata and paired counts. Update AGENTS.md/phase record with actual results.
