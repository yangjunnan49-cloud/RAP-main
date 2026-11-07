# AOD0 isolated last-block attention result

Status: VALIDATED_ISOLATED_ATTENTION_DIAGNOSIS_COMPLETE. Decision: BOUNDED_DEFAULT_FLASH_VJP_VARIATION_MATH_REPEAT_EXACT.

Fixed original layer11 global-attention boundary, sealed V_full1/P_full1 QKV and incoming cotangents. The exact archived raw/projection/cotangent and normalized-QKV bindings pass independently. Original strict model/initialization/mode source contract retained; no parameters or persistent backend changed.8 local attention VJPs plus4 input-projection VJPs,0 whole-native/explicit-prefix calls and0 optimizer/updates.

|Cotangent/backend|Forward differing values|Raw-QKV gradient differing values|Normalized QKV gradient differing values|
|---|---:|---:|---:|
|V/default|0|0|0|
|V/math|0|0|0|
|P/default|0|2|13|
|P/math|0|0|0|

Actual CPU-profiler ATen dispatch records show scaled_dot_product_flash_attention and its backward for the default first repetitions. Default forward exactly matches the archived attention output. P default repeated raw-QKV gradients differ at2 values, normalized gradients at13 values, both max5.960464477539063e-8 (one fp16 minimum step, in the inherited scaled-cotangent units). V default and both math repeats are exact. Same normalized inputs and cotangents exclude an input change in this bounded local reproduction; the normalized-gradient differences occur within the observed SDPA VJP before QK-normalization backward. This does not prove the unique source of every historical whole-model mismatch.

The scoped math backend changes hidden forward activations by max.00390625 relative to the archive, despite repeatability. These are hidden activation units, not metres or pose scores. Math is therefore a distinct numerical path, not an established drop-in complete model repair. Both backend flags and original/frozen parameter values restore exactly. No production default switch occurred.

Independent explicit float64 softmax-Q equations check64 query rows/head for every case (4096 head-query rows). FP16 rounding differences/one-ULP counts are reported descriptively in validation.json. This is not full independent K/V/QK-normalization/projection or whole-transformer backward. No extra repetitions, targeted seeds or backend sweeps after outcomes.

482 identities plus2 separately frozen input-audit sources preserved.4 successful supervised children, 71.216919s incl imports; RSS 2293174272 bytes, GPU allocated/reserved 1563338752/1698693120.600s/4GiB/3GiB/256MiB new caps pass; all child/Windows exits, 0 logging retries/0 gaps. Standard-library closure separate; ordinary setup full RSS unknown and old gaps/budgets unchanged. A normal first-backward cuBLAS primary-context warning was retained; no process restart or configuration repair occurred.

Original NOC4 loss-increase/P mismatch/INCOMPLETE, original NBR0 prerequisite failure and CCR0 negative remain. No learnability, physical truth, robustness, official metric/system or novelty gain; no production/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync.
