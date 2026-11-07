# SC-V1: observation-versus-score control

Declared 2026-09-14 before this protocol's data labels or registration outcomes.
This is a bounded untrained mechanism study. HL-V2 STOP_NEURAL_EXPANSION remains
authoritative. No result here automatically authorizes a learned head.

## Question and evidence

Does the existing causal support improve hypothesis ranking over the *same*
clipped-distance score on generating anchors, and does preserving individual
support views help over pooling the identical support observations?

HL-V2 confirmation S4 minus B4 summed clipped error was +1.262892 in low overlap;
S4 lost one ambiguous-positive strict success. B4 sorts overlap then distance,
whereas S4 sorts bidirectional mean distances clipped at 3 m. Thus B4/S4 changes
both observations and ranking objective. Small local-motion residuals do not
prove that transport error is irrelevant. View redundancy and non-overlap penalty
are hypotheses, not established causes. This study does not test every possible
support representation or establish information-theoretic absence of evidence.

The nearest-work matrix remains RESEARCH_REPOSITIONING_PLAN.md. Official RAP
rigidity, temporal verification and learned selection are prior art; this control
is not a novelty claim. Corrected core baseline and O1-O3 remain unchanged.

## SC0: data-only feasibility and membership

Use unchanged HL-V2 proposals, labels, preprocessing, raw support (2/5 m, <=5 s),
query cap 3 and priority strata. New hash prefix is `SC-V1`; use
`SC-V1|kitti|sequence|source_i|source_j` for proposal-band and sampling hashes.
Discovery sequence order: 07 then 10. Confirmation order: 08 then 09. Start each
role with its first sequence; add the second only if the pooled selected cohort
has fewer than 20 in any stratum. Never inspect method outcomes during expansion.
These are fresh memberships for this study, with no pretraining-exclusion or
geographic-independence claim. 00/02 and all earlier scored pairs are excluded.
Keep NCLT external. No MulRan identity submission is needed.

Pool eligible populations within a role, sort each stratum by the new physical
pair hash, select up to 25 each, and enforce cap 3 on (sequence, source_j).
Target 100 per role; minimum 60 total and 10 in every stratum in each role.
Store complete populations and exclusions, including individual sequence counts.
No alternate sequences, threshold relaxation or synthetic padding in SC-V1.
If the fixed four-sequence pool fails minima, finish SC0 as INCONCLUSIVE_DATA
and do not generate a bank. This is not a negative mechanism result.

Audit source IDs, finite raw scans, timestamps, calibration, GT and causal
transport; independently reconstruct proposals, support, labels and selection.
Verify old pilot manifest (829 artifacts) before any reuse. Reuse old helper
functions through a maintenance orchestration entry point, with exclusive new
output paths. This changes no algorithm in RAP-main. Record exact source hashes.
Freeze both exact role manifests before new scores or inference, even if a
sequence's data-only audit is insufficient. Insufficient membership is not a
valid confirmation set. Hash-freeze this protocol before SC0 labels.

## SC1: fixed controls, only after adequate SC0

Generate one new immutable K=4 anchor-only bank per role, with unchanged RAP,
five steps, IEEE protection, point caps and official trajectory observer. Seeds:
first 8 SHA256 hex digits of
`SC-V1|hypothesis|kitti|sequence|source_i|source_j|generation` modulo 2^31.
No retries for registration failures. All controls share these exact transforms.

| Arm | Fixed selection rule | Purpose |
|---|---|---|
| B1/B4/R4 | Existing first/overlap/official mean per-step rigidity rules | Baselines |
| A4 | Existing clipped bidirectional support score, with each side's preprocessed anchor duplicated twice and identity local motion | Same objective, no additional observations; execute all four comparisons, no cached duplicate shortcuts |
| S4 | Unchanged HL-V2 four support combinations | Additional observations |
| P4 | Pool both transported support clouds per side, concatenate without deduplication or further subsampling, then compute the identical clipped bidirectional mean | Identical support data and point multiplicities, changed view aggregation |
| G4 | S4 with evaluator-only GT short-motion transport | Transport sensitivity diagnostic, never deployable or eligible to win |
| OR4/REJ | Existing GT pose oracle / reject all | Headroom and rejection context |

Lower scores win, ties by generation ID. No score weights, visibility masks,
thresholds or support baselines are searched. G4 uses exactly the same support
IDs/clouds; only local transforms change. GT and strata remain outside executable
selector inputs. P4 uses four support scans only, like S4; it is not pooled RAP.
Pooled anchor+support RAP and strong registrar/system comparisons remain required
before claiming a method advantage, and are outside this mechanism screen.

For each hypothesis, S4 has four bidirectional comparisons; P4 has two directions
on twice-as-large point sets. Neither is claimed equal wall time from operation
counts. A4 executes four comparisons but point counts differ. Report points,
distance queries, preprocessing and actual synchronized scoring wall time per
arm, plus common bank cost separately. Also run P4 twice from the same cached
clouds, use its first result and count both passes as the compute-budget control
P4x2 (must select identically). This matches S4's total query-point count exactly;
tree sizes/build costs can differ. Equal-data and equal-query-budget comparisons
are explicit; do not claim exact equal-runtime performance when times differ.

Bounded preflight: synthetic transport/duplicate-anchor/pooling/tie/empty checks,
then first 10 round-robin discovery pairs. Validate scorer reproduction and
official observer invariance; retain these same 10 bank entries in the pilot.
Do not duplicate generations for scoring variants. Algorithm additions belong
in RAP-SLAM; freeze implementation and validation hashes before scored execution.

## Metrics and decision

Report all original strict 1 m/5 degree and 0.7/2.5 gate metrics, failures in
denominators, all strata and each component sequence. Main mechanism contrast is
paired clipped positive error A4 minus S4, divided by A4 minus OR4. Require
positive denominator and at least 10 positives whose A4/OR4 error differs >=0.10;
otherwise INCONCLUSIVE_HEADROOM. Do not switch to recall after outcomes.

EVIDENCE_FOR_SUPPORT requires all of: >=25% recovery of that gap; S4 no worse
than R4 in mean clipped positive error; <=2 pp ordinary ungated recall loss
relative to A4; no newly incorrect accepted pair relative to either A4 or R4.
Report strict recall and gated metrics even if the continuous screen passes.
This is a predeclared practical screen, not a statistical guarantee.

If S4 meets these conditions but does not beat P4 in positive mean clipped error,
record SUPPORT_BUT_NO_VIEW_AGGREGATION_ADVANTAGE. If S4 also beats P4 and P4x2,
record SUPPORT_AND_VIEW_AGGREGATION_SIGNAL. If S4 fails, record
NO_SUPPORT_SIGNAL_UNDER_FIXED_SCORE. G4 improvement is transport sensitivity;
even G4 failure does not prove no other scoring method can use the observations.
No confidence intervals treating correlated frames as independent samples.

Freeze discovery report before confirmation inference/scoring. Confirmation
governs the SC-V1 conclusion; preserve both roles without pooling a GO. Every
SC-V1 outcome leaves neural expansion STOPPED pending an explicitly justified
future protocol; it cannot retrospectively reverse HL-V2 H2.

## Resources and closure

SC0 cap: four sequences, 7,964 scans, 2 elapsed compute hours, 20 GiB new artifacts.
SC1 cap: 200 pairs / 800 unique hypotheses, one RTX 5070, 2 GPU-process hours,
12 GiB peak allocated VRAM and 20 GiB artifacts. No sweep or repeated seed search.
Record synchronized wall/peak memory, failures and timer scope; do not invent
active-kernel time or human labour. OOM/correctness/cap failure is INCONCLUSIVE.
Cap exhaustion must stop execution, preserve partial products and record reason.

Exclusive directories, INCOMPLETE until validation, protocol/source/input hashes,
GT-separated files, full denominators and a final report are mandatory. SC0 may
end the study without inference if data are insufficient. Update AGENTS.md and
PHASE_RECORD.md with actual completion, limitations, Git state and next step.
