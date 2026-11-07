# SC-V1 data feasibility and control declaration

**SC0 complete: INCONCLUSIVE_DATA. SC1 not started. Neural expansion remains stopped.**

This result concerns the newly declared cohort, not the adequate HL-V2 H2 failure.

## Concrete research advance

The fixed comparison previously changed both observations and scoring objective: B4 ranks overlap, S4 ranks clipped distances. The new protocol isolates additional observations with A4 (same distance score on anchors), S4, identical-support pooled P4 and a query-budget P4x2 control. Official R4 and evaluator-only GT transport remain explicit. This identifies a testable confound, not a demonstrated cause.

[Prospective protocol](PROTOCOL.md) was hash-frozen before data labels. No new selector was implemented or scored; no weights, score constants or acceptance thresholds changed.

## Data screen

| Role | Sequences | Candidates | Confuser | Ambiguous | Low overlap | Ordinary | Selected | Adequate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| discovery | 07,10 | 4399 | 25 | 3 | 17 | 0 | 45 | False |
| confirmation | 08 | 11545 | 25 | 25 | 25 | 25 | 100 | True |

Minimum is 60 total and 10 in each stratum in both roles; target 25 each. The physical query cap and stratum priority are unchanged. Sequence expansion followed the predeclared order, before any RAP outcomes.

| Sequence | Raw scans | Candidates | Supported ambiguous / ordinary | Selected |
|---|---:|---:|---|---:|
| 07 | 1101 | 2039 | 3 / 9 | 44 |
| 08 | 4071 | 11545 | 62 / 60 | 100 |
| 10 | 1201 | 2360 | 0 / 0 | 25 |

Per-sequence selection is diagnostic; final role membership is resampled once over its pooled population under the declared hash and sequence-qualified query cap. Therefore role counts need not equal the sum of sequence selections.

Discovery 07+10 has only 3 supported ambiguous positives and 9 supported ordinary positives even before the query cap. Its failure is not repaired merely by changing sample order. These two sequences cannot supply the fixed minimum under this protocol. No padding, label relaxation or outcome-based replacement was used.

[Exact membership freeze](data/cohort_freeze.json) and [decision](data/decision.json) preserve all selected inputs and evaluator labels. Frozen membership with inadequate counts is not a valid confirmation experiment.

## Validation and scope

- Read and hashed 6,373 finite raw scans; checked source IDs, timestamps, GT/calibration, and constructed fresh KISS-ICP odometry without loop optimization.
- Independent checks passed proposal union, causal raw support and local poses, strata, per-sequence sampling, GT-free selector input schema and bounded brute-force GT-overlap examples. Pooled role selection was separately reconstructed.
- Reverified all new data artifact hashes, unchanged source/protocol hashes and metadata hashes. Original 829 pilot and 3 diagnosis artifact hashes still match.
- The M0 snapshot exists without INCOMPLETE and its manifest hash matches. Archived payload was not rehashed; the same-volume backup limitation remains.
- Data orchestration wall time: 365.566 s. This includes reads, odometry, labels and validation; no RAP GPU inference or training occurred. Human labour and active-kernel time were not measured.
- KITTI07-10 names had no match in the two recorded historical inventory documents. This limited search does not prove exhaustive historical non-use, site independence or RAP pretraining exclusion.

## Next decision

SC-V1 ends at its predeclared data stop. Do not rerun these completed folders or implement SC1 against an inadequate discovery cohort. The control question remains untested. KITTI08 already has an adequate frozen 100-pair membership with no registration outcomes. The exact next task is a prospective SC-V1.1 data-role annex: use the frozen HL-V2 KITTI00 bank as explicitly observed development discovery and retain this exact KITTI08 confirmation membership. Declare inherited discovery seed/bank identities versus fresh confirmation seeds, preserve all fixed controls and score/gate definitions, and hash-freeze the annex before new scores. Then implement/validate the controls in RAP-SLAM, freeze discovery before confirmation outcomes and keep neural training stopped. Do not use 00/02 as unseen confirmation or resample08. This avoids insisting that discovery itself be unseen. No more raw data are needed for that proposed amendment; it is not yet declared or executed. Preserve SC-V1 INCONCLUSIVE_DATA as a separate result, without threshold/support-rule relaxation.

Public-download authorization remains; no download or identity submission was needed for this audit. MulRan access still needs owner-provided identity; NCLT remains external and manuscript drafting remains paused.

Only RAP-main maintenance orchestration/documents/artifacts changed. RAP-SLAM algorithms were reused read-only; production defaults and upstream source remain unchanged. HEADs remain 4055d92 / 6d3f2d2 on main with earlier dirty changes; no commit, push, pull, reset or cleanup. The initial sandbox WSL denial was resolved by scoped approved execution. No unresolved execution error remains.
