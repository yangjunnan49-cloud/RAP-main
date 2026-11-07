# P0 budget guard incident — preserve original receipts

The frozen rule charges each stage once by max(Windows enclosing, Linux controller, Linux wrapper). Seven completed stages total 9316.8147729 seconds before documentary closure, exceeding the ORIGINAL 9000 seconds by 316.8147729 seconds. P0 budget compliance is FAIL. There is no new cap or borrowed S1 balance.

Raw run02 Windows enclosing: 9082.9120766 seconds. Linux wrapper: 8763.28642155499 seconds; controller: 8762.00714634999 seconds. The Windows-minus-wrapper difference is 319.625655045007 seconds. Cause UNKNOWN; neither suspension nor a clock correction is established. These observations are distinct from the earlier rejected PowerShell timestamp parsing projection.

Static source inspection identifies an enforcement gap: launch_overlap02.py and overlap_core02.py use Linux monotonic time and Linux alarm/subprocess timeouts. invoke_raw_guard06.ps1 records its UTC-derived outer duration after exit and has no concurrent max-clock deadline. The original Linux timer completed within its local remaining allowance; that does not satisfy the frozen maximum-receipt accounting rule. No executable is repaired, no numerical run replayed, and no past cap reinterpreted here.

All72 cells were already complete and sealed when final outer receipts were collected. Stop new scientific stages: no independent packet/source/graph audit, paired equivalence, GT metrics, qualification, performance comparison or numeric export. Prepared audit/metric/report helpers remain unexecuted. Preserve predictions/failures/receipts and archive their exact bytes. Documentary closure execution is additional recorded cost; 9316.8147729 is a lower bound before that closure, not a claim of full final cost or compliance.

Any future decision must first address the clock/deadline enforcement and explicitly define a bounded validation scope. Do not automatically resume this stopped account, reset the old cap, change equivalence thresholds, rerun successful cells, or claim measured parallel speedup from this capture.
