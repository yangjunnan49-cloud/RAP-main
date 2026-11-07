# G0: fixed global proposal comparator on observed F2 pairs

The owner authorized continued work after F2 and asked for positive-signal
status. This component test asks whether an established, independent global
registration method can create strict poses missing from RAP's saved K4 bank.
It is a feasibility comparator, not a new RAP mechanism, novelty claim,
independent confirmation, accepted-loop result, or production change.

## Sources, inputs and fixed method

Use the official KISS-Matcher v1.0.2 PyPI Linux cp310 wheel, SHA256
`1a07d57bd23cb0ef4d9803194a74acccfa11f0015c080ab5ecc7302f258fc1f1`,
from https://pypi.org/project/kiss-matcher/. Its official Python quickstart
uses `KISSMatcherConfig(0.3)` then `estimate(src,tgt)`. The method is described
at https://arxiv.org/abs/2409.15615. Install the wheel into an isolated
directory under this experiment; do not modify the RAP environment.

Use every one of the 100 saved F2 pairs on KITTI 00 and 08, saved N record
order, including all 25 confusers and all 75 positives per sequence. Use
`inputs.npz` target i `points[0:2000]` and source j
`points[4000:6000]`, exactly the same corrected, retained physical anchor
points as the F2 anchor arm, with no supports, GT, odometry initialization,
or outcome-based pair filtering. Call a fresh matcher for each pair with
resolution 0.3 and `estimate(source,target)` once. Construct the source-to-
target 4x4 pose from its rotation and translation. Record any exception,
nonfinite or non-SE(3) result as failure, not as a dropped pair. Set
`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` for reproducible CPU execution.
This matched-point input is a deliberately bounded component comparison;
it is not a full-scan benchmark or tuned KISS-Matcher result.

Before running a real pair, freeze this protocol, source, independent
validator, package wheel, 200 pair input files, saved N records/evaluator
files and GT identities. The runner may hash but must not parse GT or
evaluator rows. It saves and SHA-seals its 200-pair pose bank before any
evaluator parses labels. Do not alter the frozen recipe after outcomes.

## Metrics and prospective decision

For each sequence separately, report strict pose success (translation <=1m,
rotation <=5deg), clipped positive error (min(5,max(RTE,RRE/5))), paired
gains/losses versus saved native N/R4, and strict recovery among positives
with no correct native N K4 candidate. Retain confuser pose and label rows.
Use exact F2 GT semantics and evaluator labels; use no common acceptance
gate because this comparator is only about candidate creation. Do not
infer accepted loops, graph effect or system ATE.

Call `GLOBAL_CANDIDATE_FEASIBILITY_SIGNAL` only if KITTI08 has >=5 strict
recoveries among the 41 native K4-unavailable positives, >=5 net strict
successes versus native N/R4, and mean clipped positive error <=0.95 of
native N/R4; KITTI00 must have no more than 3 net strict losses. These are
development planning thresholds, not significance tests. If unmet, stop
this fixed 2000-point comparator. If met, the next step is a separately
frozen RAP integration hypothesis with KISS-Matcher alone as a strong
baseline, common executable gate, cost, and eventually system results;
this outcome alone selects no method.

Separate validation recomputes hashes, bank seal, complete pair identity,
pose validity, labels, paired and aggregate arithmetic and decision.
CPU wall <=45 min, peak RSS <=4 GiB, outputs <=2 GiB, wheel transfer <=20 MB.
No GPU, training, raw scan acquisition, default edits or Git sync.
If package/runtime setup fails, record `INCONCLUSIVE_ENGINEERING` and stop
without changing the frozen method or silently substituting an algorithm.
