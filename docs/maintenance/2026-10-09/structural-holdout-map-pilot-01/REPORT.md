# SMP2: complete clusters recover support, not a material local gain

Status **VALIDATED_EXPLORATORY_COMPLETE**; decision **NO_MATERIAL_SUPPORT_PRESERVING_LOCAL_GAIN**.
Owner said "不错，继续推进下一轮方案" after the support-preserving next plan.
The one2m complete-patch experiment is executed and closed. It meets all support,
pose validity and safety conditions but misses the prospective5%mean aligned-ATE
gain. No full trajectory, useful system gain or original method is established.

## Results

The same190332retained points in the four MMR0windows participate in unchanged
eligible-plane construction. Full106/132/52/51patches now retain their complete
cross-scan support. One fixed BIG-ENDIAN SHA256 whole-patch split produces the
training/holdout sets below. No alternate hashes, scales, windows or thresholds.
P uses only training patches plus the frozen.10m/.15deg motion regularizer;
24updates. O is the unchanged properly projected E0 input. All4records support
optimization and all4candidate poses are valid.

| Window | Train/test patches | Min train/test points per scan | Local aligned ATE O->P(m) | ATE gain | tRMSE gain | Mean R change(deg) | Holdout RMS P/O |
|---|---:|---:|---:|---:|---:|---:|---:|
| 00-200 | 86/20 | 319/62 | 0.080207->0.079507 | +0.872% | +1.021% | -0.007515 | 0.979256 |
| 00-800 | 100/32 | 457/140 | 0.056836->0.055358 | +2.601% | +2.487% | +0.004797 | 0.996182 |
| 05-200 | 40/12 | 171/62 | 0.059114->0.058060 | +1.784% | +0.049% | +0.001837 | 0.990564 |
| 06-200 | 37/14 | 131/29 | 0.041382->0.041674 | -0.706% | -1.402% | +0.000838 | 0.998650 |

Positive gains are improvements. Three of four ATEs improve; mean fractional
gain **1.137760%**, below the fixed5%line.
ATE/tRMSE5%regression guards and rotation.02deg guards all pass. Ratio of mean
holdout patch RMS **0.992992337**, a0.700766%decrease,
passes1.01. The conjunction still fails. The06localATE regresses0.706%; do not
omit it or present the other three as a selected cohort. P maximum corrections
are.015509/.009617/.012464/.005185m and.014030/.007857/.007426/.006252deg.

## What we learned

Whole-patch retention directly removes the support failure found in SMP1.
This is an engineering result, not proof of useful poses. Support repair alone
does not produce material improvement under this local geometry/regularizer.
These data do not identify whether the remaining limit is strong prior, biased
geometry/membership, or redundant single-visit information. No prior-strength,
point-count or membership sweep was performed; no universal BA/geometry stop.

Held-out patch planes are refitted at the reporting pose to measure consistency.
Those complete patches do not enter pose optimization, backtracking or stopping.
Eligibility was nevertheless selected at O with all observed geometry; neighboring
surfaces are correlated and normal spectra differ between splits. This is
structural geometric checking, not independent statistical/physical validation.
The official reference convention and known short-segment caveat are retained.
Full rank/residual reduction cannot resolve physical correspondence, dynamics,
calibration, missing point times, checkpoint/site exposure or09discrepancy.

## Verification and resources

34source/input entries froze before synthetic preflight. Subset compact versus
explicit H/g checks are5.3291e-15/8.8818e-16; unchanged SMP1 solver preflight is
hash-bound. All4prediction records seal before any new numeric reference parsing.
Every retained eligible moment and whole-patch hash/membership/coverage is checked;
moment delta0, explicit geometry2.8953e-13, geometry+prior cost3.2258e-13,
selected training FD2.8005e-10. Independent pose-error reconstruction delta
5.6843e-14 and fractional-gain delta7.1276e-14; complete conjunction reproduced.
Bounded discovery verification, not full optimizer replay or an independent
census of every rejected feature. No scientific implementation failure/repair.

Six core stages **4.432199s**; observed successful-process peak RSS
**77492224bytes**. Separate next-design audit plus its failure/retry brings recorded
accounting to **7.657054s**. Combined wall1800s/artifact512MiB pass. Successful
observed RSS is below2GiB; failed metadata process did not capture peak RSS, so
combined attempted-process RSS compliance is not fully verified. Original failed
metadata tool wall2.6586884s includes startup/imports; other timings exclude
imports/WSL startup/design/docs/bookkeeping. These are not production latency.

The separate next-design audit originally misread source_frames.json's outer
record as a list (KeyError2378). Original8entryfreeze/source/failure/INCOMPLETE
are retained; attempt-02 repairs only source_frame_ids lookup and validates all
16bindings. No scientific bank, gates, selection or optimizer was changed.

## Next concrete question

The proposed next pilot uses original00accepted record0,2429->3373, two eight-frame
visits with bound raw identities. Compare saved RAP relative alignment, rigid
shared-map refinement and joint internal-pose refinement on identical cross-visit
structures. This introduces actual revisit observations; the completed local
windows did not. It is a design recommendation following a failed material-gain
test, not a conditionally admitted successful method. See NEXT_ROUND_PLAN.md.
No new two-visit coordinates, planes, optimization or reference errors exist yet.

The accepted-loop source contains historical GT fields and was displayed this
turn; prescribed first-record selection does not rank on them. Previously exposed
development remains explicit. Established [BALM](https://arxiv.org/abs/2209.08854)
is eligible under the owner's originality relaxation; no new mechanism claim.

Both original HEADs/branches and2/9tracked dirty sets are preserved. SMP1's
42delivery identities and MMR0's35remain unchanged;8model/config hashes
and opaque checkpoint digest match. No checkpoint deserialization, training,
RAP inference, GPU, full trajectory, official metric/GT replacement, acquisition,
production/default/backbone/manuscript edit, commit or Git sync.
