# Validated all-online GeoTransformer comparator

Decision **NO_MATERIAL_COMMON_GATE_SYSTEM_SIGNAL**. The isolated official
matcher on exact online point inputs does not meet either material cohort
branch;07 also fails both per-sequence safety guards. Stop this exact point/
checkpoint/gate arm. No favorable subset, full-density/neighbor/gate sweep,
checkpoint switch, training or production promotion follows from this result.

189 source/input/evaluator identities froze before inputs. Independent input
validation reconstructs all98 scans/392000 points exactly and all71 native
geometry scores at zero difference; the common gate reproduces58 RAP edges.
E0 cap is4000 per scan, not2000. Official geometry-only neighbor calibration
uses the first four ordered input pairs under its fixed2000-node stop, limits
[17,40,63,65,71]; independent SciPy radius census exactly reproduces the limits.
This is equal-point comparison, not official full-density benchmark reproduction
or equal total compute. RAP's existing descriptor/inference budgets differ.

All71 predicted poses sealed before actual evaluator GT; six first-pair repeats
have exact zero matrix delta. Checkpoint safely/strictly loaded. Fixed-current
G swaps only58 poses preserving endpoint/base noise; C re-gates all71 and uses
its own mean-distance metadata. Both retain existing odometry/keyframes/graph/
constant propagation. G is a diagnostic, C is the frozen executable gate path.

| Cohort / arm | Aligned LiDAR ATE(m) | KITTI ter(%) |
|---|---:|---:|
| Dev P native RAP |1.460664|0.388718|
| Dev G/C Geo |1.438929|0.387623|
| Exposed-transfer P |0.721480|0.505615|
| Exposed-transfer G |0.737700|0.526588|
| Exposed-transfer C |0.720340|0.520718|

Dev ATE improves1.488%, ter0.001095pp, below5%/0.01pp gates. Exposed-transfer
C ATE improves0.158%, ter worsens0.015103pp. On07 C ATE0.326400->0.396776m
(21.56%worse),ter0.394673->0.426497% (+0.031824pp), failing10%/0.03pp safety.
09 C ATE1.074523->1.000729m improves, but ter0.593652->0.607138% worsens;
an isolated sequence ATE gain does not override the cohort/safety decision.
10 admits no edge under either method and is unchanged.

| Seq | Attempts | RAP strict | Geo strict | RAP admitted strict-wrong | Geo admitted strict-wrong |
|---|---:|---:|---:|---:|---:|
|00|12|10|9|2|3|
|05|12|12|12|0|0|
|06|12|12|12|0|0|
|07|12|12|11|0|0|
|09|12|0|0|10|9|
|10|11|0|0|0|0|
|Total|71|46|44|12|12|

Geo admits56 versus RAP58. Strict means1m/5degrees against saved official
trajectory GT. 09 has shared approximately3.5–4.2m translation discrepancies;
10's11 attempted endpoints are GT-far under15m. No retrieval recall claim.
Candidate accuracy, gate acceptance and graph utility remain separate.

Independent validation passed eight groups: all71 candidates/labels/gates,
all18 explicitly rebuilt P/G/C graphs (zero trajectory delta),all22194 KITTI
segment records and independent Kabsch ATE/cohort/decision checks. Input+
prediction+evaluation+successful validations64.327s, allocatedGPU1.194GiB,
peakRSS2.347GiB, artifacts before report15.371MB. Failed validator attempts
add less than20s of observed command wall time; including them remains far
below1800s. Acquisition/extension/synthetic feasibility costs are separate.

Two amendments preserve originals and all numerical outputs: input JSON
NumPy-integer serialization fix; independent validator replaces noisy-matrix
inverse by Frobenius rotational trace matching the frozen transpose metric.
No threshold, model output, label, graph or outcome revision. Both amendment
identities are checked by the final validated entry point.

Interpretation: this fixed strong-matcher arm does not recover the joint-GT
oracle opportunity. It does not establish that cross-visit registration is
impossible or prove a RAP feature bottleneck. Shared09 discrepancy warrants
the separately frozen all71 scan/pose geometry diagnostic; it cannot be
attributed to RAP's learned model alone. Novel method remains unproven.
No training, default/production/manuscript changes, commit or Git sync.
