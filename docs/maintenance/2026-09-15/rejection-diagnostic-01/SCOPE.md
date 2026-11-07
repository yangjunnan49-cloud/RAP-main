# Bounded rejection diagnostic

2026-09-15. Owner authorized the proposed bounded diagnosis after PG-DEV-V1.
This is post-hoc hypothesis generation on already observed KITTI00/08, not a
prospective efficacy experiment. Preserve all HL/SC/PG stop decisions.

## Fixed scope before diagnostic execution

- Reuse all 200 fixed pairs and the saved common-anchor gates. A-R4 is the
  primary baseline; P-R4 is a contextual comparison, not a rescue of PG.
- Partition into strict correct accepted, strict incorrect accepted, strict
  correct rejected, and strict incorrect rejected. Strict means <=1m/5deg;
  report legacy <=5m/10deg separately. Report positive/confuser strata explicitly.
- Identify which original gate clauses reject correct selected transforms.
- Describe saved overlap, mean distance, rigidity and four-candidate dispersion.
  Dispersion uses maximum pairwise translation-vector distance and relative
  rotation angle, plus selected-candidate neighbor count at the existing 1m/5deg
  tolerances. This tolerance is descriptive and is not a calibrated uncertainty
  bound or a proposed operating threshold. No sweep, threshold fitting or model.
- Report all errors and class summaries, never select only favorable cases.
  Pairwise feature ordering (descriptive AUC) may summarize separation among
  currently accepted transforms; no significance or independent validation claim.
- Quantify shared scan IDs and sequence/frame concentration; pair counts are not
  independent trials or deployment error prevalence.
- Verify saved artifact hashes and reconstruct gate decisions, baseline counts,
  R4 choices and available candidate labels. Do not regenerate raw geometry.

## Exit

Recommend a new experiment only if the saved evidence supports a concrete
mechanism distinct from the failed distance-support score. Any recommendation
must identify counterexamples, coverage cost and the need for fresh confirmation.
Otherwise stop this diagnostic route and recommend scope convergence. Missing
features imply untested mechanisms, not universal impossibility. No new data,
inference, training, production edits or manuscript drafting in this diagnostic.

Outputs use this new exclusive directory. Preserve source and input hashes,
machine-readable per-pair results, summary, validation and a readable decision.
