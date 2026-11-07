# SAR0 target-free source sampler/extraction precision bindings

Status: VALIDATED_SHADOW_SOURCE_SAMPLER_BINDINGS_COMPLETE. Decision: SHADOW_SOURCE_SAMPLER_EXTRACTION_AND_PRECISION_BINDINGS_VALID.

Original checkpoint/443904 initial parameters/B=0/modes. Two already generated original noise00 arrays fit/eval, two prefix paths (unchanged helper versus original full-FP32 layer9 hook), two repeats each. Eight complete five-step source Euler+rigidity-forcing rollouts; no truth/target arrays/losses/pose metrics/backwards/optimizer/retained updates. Prefix state/model float32, carried state/double-tail/rigidification float64, original source output buffers float32. Four float32 time constants explicitly promoted within double tail. Model values/dtypes/modes/hook/backend and original rigidifier callback binding restored.

20 prefix helper calls/20 complete-FP32 flow forwards/40 double tails/40 rigidifications/160 time-constant promotions. Independent Horn eigensystem reconstructs120 part rigidifications, max delta 1.11022302e-15; state recurrence max 7.21644966e-16. Source Euler AST exact; input/timestep casts and every raw endpoint/forced-state/source-buffer precision independently reconstructed. All80 float32 buffer comparisons within one ULP, 80 byteequal. Fit00 tau1 prefixes exactly bind prior FPC0 D. This is source/extraction/arithmetic validation, not independent complete neural implementation.

|Noise|Left|Right|Complete arrays byteexact|Max delta|
|---|---|---|---|---:|
|fit_00|helper1|helper2|True|0|
|fit_00|hook1|hook2|True|0|
|fit_00|helper1|hook1|True|0|
|fit_00|helper2|hook2|True|0|
|eval_00|helper1|helper2|True|0|
|eval_00|hook1|hook2|True|0|
|eval_00|helper1|hook1|True|0|
|eval_00|helper2|hook2|True|0|

All noise/path/repeat bindings reported, no output selection or gate relaxation. Full-hook path evaluates additional frozen model work; this is a control, not an equal-work or latency comparison. Original configured5-step Euler/rigidity=True retained, no anchor or rigidification deletion. The explicit mixed-precision function differs from original native fp16/FP32, and source float32 return buffers still limit stored precision. Passing at initial state does not prove post-fit equivalence, rank/active capacity, learning, fresh-noise robustness, physical/generalization/system gains or novelty.

1211 frozen identities,3 supervised scientific children,132.253653s incl imports; RSS 2417074176, GPU allocated/reserved 1761263104/2319450112 bytes.900s/6GiB RSS/8GiB GPU/512MiB prospective caps pass/full child-Windows exits/0 logging retries/0 gaps. Setup RSS unknown, standard-library final closure separate, old caps/gaps unchanged.

All original NOC4 loss-increase/P replay/INCOMPLETE, failed original NBR marker, NMR/FPC direction gaps and CCR0 retired family/09 physical unknown remain. No fit/new noise/real/nearby/trajectory benchmark/production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.
