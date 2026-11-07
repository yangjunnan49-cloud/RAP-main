# NBR0 mode-inventory repair and bounded backward reproducibility diagnosis

Status: VALIDATED_BOUNDED_BACKWARD_DIAGNOSIS_COMPLETE. Decision: INSTRUMENTED_BACKWARD_MISMATCH_LOCALIZED.

Same exposed NOC4 known-transform/copy-descriptor synthetic fixture, fit00 noise and443904 original initialized native trainables. Eight supervised instrumented backwards: two full and two cached paths per V/P. Original fp16/IEEE/eval/loss/multipliers unchanged. Zero optimizer calls and all parameters unchanged byte-exactly. A strict weights_only checkpoint load passes; frozen parameters/modes preserved.

|Comparison|Forward output differing values|Upstream endpoint differing values|Parameter gradient differing values|Max parameter gradient difference|
|---|---:|---:|---:|
|V_full1 / V_full2|0|0|0|0|
|V_cache1 / V_cache2|0|0|0|0|
|P_full1 / P_full2|0|0|6219|0.125|
|P_cache1 / P_cache2|0|0|6143|0.25|
|V_full1 / V_cache1|0|0|0|0|
|V_full2 / V_cache2|0|0|0|0|
|P_full1 / P_cache1|0|0|5717|0.125|
|P_full2 / P_cache2|0|0|6870|0.375|

Independent Horn/direct loss max delta 5.1159077e-12; V upstream max delta 2.27373675e-13;48 P output directional FD checks pass, max absolute delta 2.31501035e-05. All difference censuses and unchanged parameters independently reproduce. Local B linear product checks have 0/32 outside the reported one-fp16-ULP bound; this is a disclosed local GEMM/reduction diagnostic, not independently implemented complete native backward.

Per-module input/output/scaled-gradient/rank activations and every trainable gradient are sealed. Hooks synchronize/capture identically but can affect scheduling; instrumented repeatability cannot certify historical uninstrumented determinism. Enabled SDPA flags do not identify actual dispatch. Compare existing old probe arrays descriptively in results.json. No unique cache/kernel/precision cause, derivative accuracy of all transformer operators, functional-step descent, native learning, robustness, physical accuracy or system gain is established.

382 identities frozen, original204 NOC4 bindings/86 deliveries and40 runtime recovery deliveries preserved. Eight combined supervised scientific children (six new plus two retained original, two failures), 116.719167s incl imports; RSS 3063087104 bytes, GPU allocated/reserved 616103936/656408576 bytes.1200s/4GiB/3GiB/512MiB caps pass; full child/Windows exits, 0 logging retries/0 pointer gaps. Final standard-library bookkeeping separate; old supervision/budget gaps unchanged.

Exact independent four-wrapper/source-AST/initialized-parameter mode contract passes with0 mode mutations. Initial Windows path-separator freeze failure and all original sources/receipts remain. Original NOC4 loss-increase and replay-mismatch gates/INCOMPLETE markers remain. This closes only the new NBR0 mode-repair diagnosis; original NBR0 failed dossier/marker stays immutable. No optimizer/update/fit/new noise/real/nearby/trajectory, no production/default/backbone/manuscript/reference/install/restart/commit/Git synchronization. Both original HEADs/branches/two-nine tracked dirty sets preserved.
