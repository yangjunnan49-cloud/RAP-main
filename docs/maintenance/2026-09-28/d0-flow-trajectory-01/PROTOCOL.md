# D0: native RAP intermediate-trajectory candidate audit

Owner requested continued exploration after V0's negative result. This is a
separate, CPU-only saved-result diagnosis of *when* the native RAP flow has
a correct candidate. It does not rerun F2, change a model, make a method
claim, or revive the stopped V0 visibility search. Use the exact F2 observed
development cohorts KITTI00/08, 100 pairs per sequence in F2 saved N order,
all four native N generations and all five saved raw clean endpoints. No
pair/seed/outcome filtering. Freeze this protocol, runner, independent
validator, model/source identities, all 800 N trajectory files, 200 input
files, F2 records/gates/evaluator and GT hashes before decoding real pairs.

## Fixed reconstruction and comparisons

`inputs.npz` supplies the saved six-part normalized `cond`, six counts,
centers and uniform scale. Each `Nk.npz` supplies the five raw
`end_point_trajectory` arrays. At each step, fit independent proper rigid
SE(3) transforms from normalized input to raw endpoint on part 0 and part
3 using float64 Kabsch, with the same center/scale physical decoding as
F2. Form the source-j to target-i candidate `inv(T_part0) @ T_part3`.
Require the reconstructed final step to match F2's saved N pose within
1e-4 matrix maximum, or stop as an engineering inconclusive result. Use
F2's original R4 generation chosen by mean five-step rigidity RMSE; do
not change generation selection. The *fixed executable checkpoint* is
its penultimate raw endpoint, step index 3. Recompute the unchanged F2
geometry gate for that pose and verify the final gate against F2 within
1e-5. Save all 20 poses per pair, the fixed selected step3/final poses
and gates. Synthetic rigid/Kabsch and coordinate decoding checks must
pass before freeze.

The runner is GT-free. It may hash evaluator/GT files but must not parse
them. Seal all decoded candidate poses and gates by SHA256 before the
evaluator loads labels. Use original F2 `inv(gt[i]) @ gt[j]`, strict
RTE<=1m and RRE<=5deg, and clipped error min(5,max(RTE,RRE/5)).

Report per sequence and stratum: final and each earlier step's K4 oracle
strict availability; positives with no strict final K4 candidate but any
strict earlier candidate, including first/last step where one exists;
step3 fixed-native-R4 paired strict gains/losses; correct/incorrect accepts
under the same gate; ordinary losses; confuser accepts and costs. The
earlier-step K4 oracle is evaluator-only and cannot select a live pose.
Do not claim a positive method result from it.

## Prospective interpretation gates

- `NO_TRANSIENT_CANDIDATE_EVIDENCE` if fewer than five of KITTI08's 41
  final-K4-unavailable positives have a strict candidate at steps 0-3.
  Stop the saved-step/checkpoint route under this evidence.
- Otherwise `TRANSIENT_ONLY` unless the **fixed** penultimate pose (same
  native R4 generation) gains >=5 net strict positives and >=2 net correct
  accepts on08, introduces no newly incorrect accept on either sequence,
  loses at most two net strict positives on00, and loses at most one
  ordinary strict positive on each sequence. If these all pass, label
  `CHECKPOINT_EXECUTABLE_SIGNAL`, still only observed development evidence
  requiring a separate frozen efficacy and independent confirmation study.
- CPU decoding/evaluation wall<=20min, peak RSS<=4GiB and new artifacts
  <=50MB. A resource or reconstruction failure is
  `INCONCLUSIVE_ENGINEERING`, not a scientific negative.

Do not rescue a failed fixed checkpoint by choosing the best step or
generation using GT, retuning rigidity/gate thresholds, or rerunning the
completed F2 experiment. An oracle-only transient finding may motivate a
separately defined GT-free selector question, not automatic GPU work.
No training, network, raw-data download, production/default edit or Git sync.
