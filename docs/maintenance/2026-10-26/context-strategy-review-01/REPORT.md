# Context, training results and next strategy — 2026-10-26

This owner-requested review is complete. The latest adapter experiment establishes reproducible fitting of the specified double-precision shadow function and a complete negative noise comparison. Useful RAP adaptation, an incremental RAP research contribution and independent generalization remain unestablished. Research remains UNRESOLVED and manuscript drafting remains PAUSED.

The recommendation is to close investment in the tested synthetic fitting construction, retain the measured system deliverables with their limitations, and make the next research decision about a useful mechanism on appropriately documented measured observations. Further training needs evidence and a new prospective protocol; this review does not start it.

## Current evidence and authority

The current AGENTS.md header, dated completion records and sealed results take precedence over preserved preparation and ACTIVE paragraphs. The October25 phase record contains PP1/AR1 entries but no SR1 entry; this omission does not negate the later sealed SR1 completion. Its historical bytes are retained.

| Work | Latest supported result | Limit that remains |
|---|---|---|
| SR1, October25 | Strict model load, float64 backward, 40 retained updates and complete 51-case noise bank pass their numerical audits | All four noise gate cells FAIL; original native equivalence is false |
| HFIT0, October13 | Earlier 20 V + 20 P shadow updates reduced the same losses by about 2% | Original 2 GiB prediction-artifact failure and INCOMPLETE remain; SR1 is a separate experiment |
| Native NOC4 attempt02 | Four restored AdamW probes, zero retained training updates | Loss increased in both arms; P gradient/update replay mismatched; no native repair established |
| RLP2 | Nine fixed 1000-update fits and complete comparison/replay | Joint readout beat independent-context readout but failed descriptor-only and stronger geometry/KISS conjunctions; exact construction stopped |
| BRF0 | An optimistic analytic bound excluded the specified small native-base residual family | No fitting; no universal impossibility theorem |
| TT2/BI1/RI2/OC1, October24 | 402 tensors transferred, original constructor integrated, two public GPU cases completed, five output matrices checked | Operability and representation consistency; no qualified physical-accuracy comparison; candidates remain uninstalled |
| S1, completed October21 | All 36 fresh-raw trajectory-core G/K cells and independent metric checks completed | Mixed sequence protections; no new RAP calls or increment; no full CLI side-product timing |
| P0 validation, October21 | All 72 captured cells independently validated later | G and K queue4 candidates CLOSED_EQUIVALENCE_FAIL; original acquisition budget FAIL retained |
| N2, October21 | Fixed-input serial comparison first differs at recorded ICP output; final coarse translation-element delta about 2.71 micrometers | Hidden cause UNKNOWN; does not explain historical 4.31 mm or qualify P0 |
| PP1, October25 | Authorized ParisLuco3D project page captured | Exact RegX derivative/reference construction, independent cohort and checkpoint membership remain unresolved |

Sources: [SR1](../../2026-10-25/shadow-adapter-restart-01/REPORT.md), [HFIT0 stop](../../2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/REPORT.md), [NOC4](../../2026-10-10/native-conditioned-comparison-01/attempt-02/REPORT.md), [RLP2](../../2026-10-08/motion-supervised-readout-01/REPORT.md), [BRF0](../../2026-10-14/bounded-native-residual-feasibility-01/REPORT.md), [public operation](../../2026-10-24/continuation-01/RESULTS_REPORT.md), [current fact index](../../2026-10-21/current-state-audit-01/snapshot/CURRENT_STATE.json), [PP1](../../2026-10-25/upstream-page-01/REPORT.md).

## What the training result means

SR1 uses two strictly initialized models with 344 checkpoint tensors each. The specified 443,904 trainable values are promoted to float64 in the learned tail; the prefix remains frozen float32. Initial sampler traces match SAR0 byte-for-byte, and initial V/P gradients match DTC0. This is the specified changed shadow function, not full original-native/AdamW training. Nominal parameter count is not a claim that every parameter is instantaneously active.

Training uses one existing synthetic fixture, fit00 at tau=1, and 20 retained manual updates per arm. V is the velocity objective and P is the pose objective used by the bound implementation. Both use the frozen normalized update rule; optimizer API calls are zero.

| Arm | Initial training loss | Loss after 20 updates | Relative reduction | Armijo/update checks |
|---|---:|---:|---:|---|
| V | 7.22996671078e-6 | 7.08712625394e-6 | 1.975672% | 20/20 PASS |
| P | 198.329989556 | 194.401887634 | 1.980589% | 20/20 PASS |

The independent audit checks saved parameter-update equations, loss terms and local A/B derivatives. Its `independent_neural_optimizer_replay` is false; the evaluation's `independent_complete_model` is false. These are not independent implementations of the complete transformer or optimizer. Successful model/backward replay and the recorded local audits should retain their actual scope.

The complete evaluation compares U/V20/P20 on fit00 and every existing eval00..15 noise. All 51 cases are present, with 357 prediction-file hashes and 765 independently reconstructed Horn part fits in the original audit. Fit00 is diagnostic only. All four cells fail the unchanged conjunction:

| Arm / part | Mean translation gain | Gain relative to baseline mean | Joint translation/rotation nonworse | Cell |
|---|---:|---:|---:|---|
| V / 1 | 26.2727 micrometers | 0.02156% | 3/16 | FAIL |
| V / 2 | 17.7285 micrometers | 0.01439% | 5/16 | FAIL |
| P / 1 | 9.2970 micrometers | 0.00763% | 5/16 | FAIL |
| P / 2 | 15.4962 micrometers | 0.01258% | 3/16 | FAIL |

The gate requires a mean translation ratio at most 0.9, a paired median translation gain at least 5 mm and at least 12/16 joint nonworse cases, together with rotation/tail conditions. The table's percentage gains are descriptive arithmetic on saved summaries, not newly computed pose metrics. The decision is `BOUNDED_SHADOW_FIT_COMPLETE_NO_SAFE_MATERIAL_NOISE_CONJUNCTION`.

SR1 reproduces the earlier HFIT0 fitting outcome and supplies a separately authorized complete comparison. It does not complete or repair HFIT0's partial bank. Local objective descent did not transfer into a useful five-step evaluation benefit in this test. The observations do not uniquely attribute that failure to update count, objective, capacity or precision, and do not justify tuning any of those on this evidence.

The fixture also has a deeper scientific limitation: GSG0 recovered both transforms of its exactly congruent point sets with ordinary geometry, at approximately 1e-14 m translation error. It was already retired as a RAP-context efficacy/innovation test. Its numerical derivative role remains valid. Sixteen reused noises on one exposed synthetic fixture are neither sixteen independent scenes nor fresh-noise confirmation. See [GSG0](../../2026-10-13/geometry-signature-control-01/REPORT.md).

Original SR1 accounting passes: successful scientific children total 594.287837 s; including three 300 s outer interruptions gives a conservative 1494.287837/1800 s. Peak process RSS is 2.638 GiB, GPU allocated/reserved 4.088/4.621 GiB and the new dossier 2.407/4 GiB. Available arithmetic capacity was sufficient for this task. These are October25 measurements, not fresh October26 resource checks or production speed.

## System progress to retain

The latest fresh-raw trajectory-core evidence is S1, completed October21 in the October20 directory. It must not be confused with the earlier cached-E0 G result or the October11 complete native CLI benchmark.

| Saved S1 aggregate | Fixed G | KISS control |
|---|---:|---:|
| Mean aligned LiDAR ATE | 0.648334141 m | 0.698991712 m |
| Mean ter | 0.446953334% | 0.478490322% |
| Batch throughput | 11.391 FPS | 27.092 FPS |
| p99 frame time | 137.363 ms | 69.420 ms |

Mean ATE/ter improve 7.2472%/6.5909%, but 07 ter and 10 rer protections fail; G ATE is worse on 06/07/10. No stable online 10 Hz result follows. All six sequences are development-exposed, and three process repeats do not create independent generalization. No RAP forward runs in this G/K study, so it cannot establish adapter or RAP-specific gain.

The October21 runtime-overlap report's original unvalidated P0 state was superseded by the separate completed validation. Its G candidate fails r1_06 equivalence and K fails r1_00/r2_09. Their measured timing reductions do not qualify promotion. Preserve the original capture budget failure and later validation result separately; do not restart queue4 or relax equivalence thresholds.

Sources: [S1 current delivery](../../2026-10-20/raw-input-contract-01/CURRENT_HANDOFF.md), [S1 report](../../2026-10-20/raw-input-contract-01/REPORT.md), [P0 current validation status](../../2026-10-21/p0-validation-01/STATUS.json), [current fact index](../../2026-10-21/current-state-audit-01/snapshot/CURRENT_STATE.json), [N2](../../2026-10-21/native-stability-stream-02/REPORT_CN.md).

## Recommended next decisions

### 1. Retain completed engineering evidence and retire the tested training route

Keep serial G as the already delivered experimental system result with complete per-sequence tradeoffs, and preserve the current default. Existing S1/public-operation stages need no replay. No new full-system benchmark, parallel rescue or repeated synthetic fitting is recommended merely to regenerate these conclusions. If production integration becomes a separate requested deliverable, review its exact ownership and output/cost contract first; it is not automatically justified by this review.

Keep NOC4, HFIT0, RLP2, BRF0, P0 and N1 statuses intact. Do not treat free disk, recovered GPU headroom or unused old time balances as scientific permission or a reason to revisit a stopped family. Native backward diagnosis remains a distinct optional engineering problem, without an established direct route to research benefit; it is not the present priority.

### 2. Resolve one useful research task and its evidence role before a new runner

The most concrete inherited candidate is JMD0's question: can a frozen joint conditional prior recover useful alignment of genuinely distinct, initially unposed measured views beyond equally informed ordinary geometry and independent-pair RAP, without harmful acceptances or tails? This is a task hypothesis, not a new algorithmic contribution. Before implementation, specify the intended contribution or explicitly choose a limited engineering comparison. Generic joint registration is already in the original method.

Prepare one short task/source decision sheet, using original already authorized local records where available. It must identify exact scan/session/release membership, actual preprocessing, the reference's construction/units/frame/direction/time/quality, the observation unit, known exposure and the claim being tested. For RegX, bind the derivative-to-upstream mapping; the captured project HTML does not supply it. Any linked external object would require its own concrete acquisition scope under the existing source boundary; this review fetches none and sends no outreach.

Do not require reconstruction of all historical records for an honestly limited engineering task. Existing exposed KITTI supplied-reference studies remain possible for a distinct justified question, while retaining that role and all old stops. Checkpoint membership can remain UNKNOWN for a frozen-pretrained engineering claim; it cannot become an exclusion claim. A physical or independent-generalization claim needs the corresponding source and prospectively reserved scene/session evidence. Renaming files, changing augmentation noise or using configured-only POSS ranges does not establish it.

If no useful mechanism/task or usable source/reference role can be stated, stop this branch at the decision sheet. Further interface roundtrips, supervisor prototypes or repeated literature-free local audits cannot supply the missing evidence. See [JMD0](../../2026-10-15/joint-mechanism-assessment-01/REPORT.md), [RC2 evidence requirements](../../2026-10-24/reference-cohort-decision-01/EVIDENCE_REQUEST.md) and [conditional comparison](../../2026-10-24/reference-cohort-decision-01/CONDITIONAL_COMPARISON.md).

### 3. If the task is justified, test the source of incremental information first

Before outcomes, freeze common measured raw IDs, point/preprocessing choices, descriptor exposure, initialization, complete connected observation graph, verifier/solver, all attempted population members and actual end-to-end work. Compare strong task-appropriate geometry G, independent-pair frozen RAP P, joint frozen RAP J and a declared alternative use of equal work W. Identity-initialized local ICP alone is not a sufficient global-registration control. All relevant arms receive the same measured support.

Define the primary useful effect, adverse tails/false acceptance, sequence protections, cluster-aware analysis and stop/resource rules from the task and reference precision before any predictions. Do not inherit favorable thresholds from the two exposed public cases. Seal complete predictions before reference evaluation; report every failure and fallback. Common-pose cycle closure is an identity, not an independent correctness or confidence measurement.

This proposed pilot is conditional and unexecuted. Its exact source, sample count, algorithm settings, numerical thresholds and resource account remain to be frozen; no missing values are silently chosen here. Its purpose is to discriminate information and compute effects before another fit, not to recast old stopped mechanisms.

### 4. Reconsider adaptation only after a credible learning-specific case exists

A positive frozen-model increment would be one reason to study adaptation. Alternatively, a distinct learning-specific hypothesis would need concrete source-bound evidence of attainable useful improvement over strong controls; frozen success is not asserted to be universally necessary. Either way, the new training proposal must explain why its supervision, observations and deployed prediction path can address the demonstrated limitation, and why the experiment is distinct from the stopped constructions.

Any future fit must separate development and confirmation by physical scene/session, retain known pretraining/exposure uncertainty, match trainable/effective capacity and total work controls, and evaluate the deployed complete sampler and useful registration/system outcome. Loss descent is a prerequisite rather than the success criterion. Freeze limits and failure rules prospectively; first verify the selected function's loading/backward/update behavior, without relabeling SR1 as native equivalence. No such new experiment is admitted or pending from this document.

## What this review changed and checked

The review reads documentary records and bound training source text, with descriptive arithmetic on saved scalars. Thirteen selected SR1 documents/source files match their length/SHA256 entries in the 711-entry delivery seal. This is a selected-entry identity check, not a fresh rehash of all 2.407 GiB, a replay of 357 predictions or an independent new gradient/pose evaluation. REVIEW_CHECKS.json records the evidence identities and selected checks.

Both current repository HEADs and tracked dirty sets match the recorded main/slam identities: 4055d929c594b0033aafc6eed339c910369eef55 on codex/meeting-20260930 with two tracked dirty paths; 6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6 on codex/e0-f1-20260926 with nine. The sibling Git metadata read required an allowed read-only sandbox escalation. No fetch/remote check or Git state mutation occurs.

Only this dated review, its checks, a phase record and an additive AGENTS.md header are written. Exact prior AGENTS bytes are backed up and retained as the suffix. No model/array payload, new pose metric, training, optimizer, solver, WSL startup, environment/storage/default/production change, network acquisition, outreach, scheduler, account or goal-status action occurs. Historical WSL E-image/Junction/backup checks remain historical; direct boot without the Junction is still untested and no storage is modified. The review is finished; proposed future scientific work is not started.
