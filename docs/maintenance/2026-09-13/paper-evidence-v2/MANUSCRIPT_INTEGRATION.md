# Integration notes for the experimental chapter

The English draft in EXPERIMENTAL_RESULTS_DRAFT.md is a new, evidence-bound
chapter. It has not been inserted into the earlier Chinese outline at
E:/githouse/RAP-SLAM-report/paper/main.tex or typeset. Local E1-E7 references
support numerical audit; method/dataset bibliography entries still require a
separate citation review before submission. Do not treat the chapter as a
compiled or submission-ready thesis.

## Existing outline changes required

| Existing area | Required treatment |
|---|---|
| Abstract and introduction | Replace broad online/generalization/zero-error claims with the measured offline scope. Do not transfer RAP-paper claims into claims about this thesis system. |
| System framework | Describe the implemented default pairwise offline chain. Separate unused multiway, online and statistical variants from the evaluated system. |
| Proposed contributions | Emphasize integration, correct geometric interfaces and traceable evidence. Do not present negligible robust-weighting effects as a proven accuracy contribution. |
| Datasets and current results | Use the explicit four source ranges and Table 2. Replace mixed historical metrics; keep first-pose APE, aligned APE and camera drift distinct. |
| Online ROS and multiway results | Retain only as labeled historical/deferred material if needed. They are not newly validated by the offline reruns. |
| Comparison and ablation plans | Replace completed portions with Tables 3-4 and measured secondary tradeoffs. O3 is experimental, not the default or a per-sequence winner selection. |
| Runtime and expected targets | Separate recorded warm-run timings from targets. Remove claims of measured real-time performance or achieved extrapolated targets. |
| Conclusion | Limit claims to observed development sequences, report KITTI 05 counterexamples and KITTI 06/00 drift regressions, and preserve unresolved training membership. |

## Editorial decisions already resolved in the draft

The main system remains proximity-priority budget 12. O3 is a separate
source-allocation study; its matched ICP comparison cannot silently replace the
main-system table. The post-hoc common-edge-fixed diagnostic is explicitly
identified. No p-values, confidence intervals, coverage guarantees or unseen
domain claims are invented. Per-sequence method selection is not reported as a
single system.

## Next concrete deliverable

Draft the methods section to match the implemented offline default, including
transform direction, candidate ordering, acceptance diagnostics, graph factors
and frame-aware evaluation. Verify each technical description against current
source. Then integrate methods and results into a coherent manuscript and review
the bibliography. This is writing and source verification, not a new optimization
sweep. Keep the old outline intact until a replacement manuscript is prepared.
