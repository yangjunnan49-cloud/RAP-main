# SC-V1.1 data-role amendment

Declared 2026-09-14 before new control scores or KITTI08 registration outcomes.
Inherits all fixed controls, metrics, gates and resource caps from
[SC-V1](../support-control-01/PROTOCOL.md), except the explicit data/bank changes
below. SC-V1 SC0 INCONCLUSIVE_DATA and HL-V2 STOP_NEURAL_EXPANSION are preserved.

Discovery is the exact 100 KITTI00 rows and 400 existing hypotheses in
HL-V2 pilot-01/discovery, with original HL-V2 seeds, transforms, diagnostics and
official rigidity. This is already observed development material, not unseen
evidence. Do not regenerate it. Confirmation is the exact 100 KITTI08 rows in
support-control-01/data/confirmation_inputs.json and its evaluator companion,
25 per stratum. No resampling, role expansion or additional sequences.
Generate exactly four hypotheses per KITTI08 pair with the SC-V1 seed formula
already declared (not a new SC-V1.1 prefix). One immutable bank per role serves
every control. Discovery/confirmation banks need not share random seeds.

Verify all parent manifests and bind these membership files before new scores.
Freeze scorer, evaluator and independent validator source hashes after synthetic
checks and before real control scoring. Preflight uses the first ten existing
round-robin KITTI00 rows; retain their scores in the full discovery result and
verify all40 original S4 scores within1e-10. Reuse the frozen original official
observer/RNG invariance evidence if its implementation/dependency hashes remain
unchanged. No new discovery RAP calls are needed for this data-role amendment.
Independently validate all discovery selections/metrics, then freeze discovery
report and artifacts before any confirmation hypothesis or control outcome.

Execute A4/S4/P4/P4x2 as SC-V1 specifies, no fitted parameters. P4x2 performs two
fresh pooled-score passes, records their combined cost and uses the first score.
G4 is evaluator-only, computed separately after executable scores are persisted;
it substitutes only GT short-motion transforms of the same support IDs. Keep
its outputs separate from executable selectors. Preserve B1/B4/R4/OR4/REJ.

Timing: common generation and preprocessing wall costs are distinct from control
score costs; synchronize CUDA at the bank boundaries. CPU scoring wall time is
measured by a monotonic timer. Count actual NN query points; P4x2 and S4 match
query count, not necessarily runtime or tree construction cost. Legacy discovery
generation timing stays historical, not charged as new inference work.

Decision clarification before outcomes: the >=0.10 A4/OR4 discrepancy in SC-V1
uses clipped positive error, consistent with the main gap denominator. Apply
all original failure denominators and strict<=1m/<=5deg labels, unchanged gate,
and show every individual condition. Missing/invalid output is a failed selection
with clipped error5, never an omitted pair. Incorrect accepts are checked per
physical pair separately against A4 and R4; helpful transitions cannot offset
harmful ones. GT oracle minimizes un-clipped normalized pose error as in HL-V2.

New execution cap: 400 KITTI08 generations, inherited400 KITTI00 hypotheses,
200 total pairs, one RTX5070, <=2h inference-process wall, <=12GiB allocated VRAM,
<=20GiB new artifacts. Persist partial outputs on engineering/cap failure and
mark INCONCLUSIVE; do not retry scientific failures or tune. Method-specific
scoring failures remain in denominators; coding/provenance failures halt the run.

Even a mechanism signal does not authorize neural expansion, reverse HL-V2,
establish novel-method superiority, or justify production changes. Pooled RAP,
strong registration/system baselines and external evidence remain outside this
bounded mechanism study. No new manuscript work, training or downloads.

Use this fresh support-control-02 directory exclusively. SC-V1.1 outcome is
governed by confirmation. Keep the frozen00/02 development status explicit.
