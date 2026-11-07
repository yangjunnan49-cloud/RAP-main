# Complete visual/historical-proposal categorical join

All200 existing pair IDs and19 complete groups are retained. Of64 historical native-N proposal-unavailable positives (00:23;08:41), camera5DoF emits only two outputs, both00. One of00's23 enters the pre-frozen5/15-degree bin; none of08's41 does. This is one ID intersection, not recovery of a missing metric6DoF/RAP pose. The frames, quantities and criteria remain distinct.

| Historical positive category |00 pairs / visual poses /5-15 bin|08 pairs / visual poses /5-15 bin|
|---|---|---|
| Correct accepted |23 /19 /15|17 /0 /0|
| Correct rejected |26 /8 /6|13 /0 /0|
| Selection miss |3 /1 /1|4 /0 /0|
| Correct proposal unavailable |23 /2 /1|41 /0 /0|

All25 confusers per sequence remain and yield no visual pose. All11 historical incorrect-accepted overlay IDs also have no visual pose, but21 of40 historically correct-accepted IDs likewise have no visual pose. Therefore lack of this visual evidence cannot be adopted as a safe old-registration veto or as an incorrectness label. These exposed categorical counts do not calibrate a classifier.

CF1 both-zero finite-frustum source-LiDAR upper support is84/200 (00:28;08:56, including confusers); original75 positives remain15/42. All30 visual outputs fall in the remaining116 IDs, but42 of00's72 and all44 of08's44 not-both-zero IDs still lack a visual pose. Projected source-LiDAR support is not measured visibility/correspondence or a sufficient visual-pose condition. Do not select that support subset or infer image-only impossibility.

The present result provides limited camera5DoF information on00, with only one strict-bin intersection among64 old missing-proposal IDs and no evidence on08. It does not justify training, RAP increment, a general rejector or an automatic system integration. A distinct source-depth-association feasibility question can determine whether a full-cohort ordinary PnP comparison is implementable; it must not claim true correspondences or metric pose recovery merely from nearest projected-point associations. Any such next numerical diagnostic needs a separate complete source/resource freeze and controls. No new pose solver is executed by this review.

Worker uses saved JSON only; no new angles/pose/feature/model/point/image computation. SOURCE_FREEZE binds all inputs/code. The prospective absolute-path host adaptation is separately bound in HOST_RUNNER_FREEZE; no worker/scientific changes or failed stage launch were needed. The copied launcher's 'VB1 controls PASS' string refers only to this folder's JSON join. Original VB1 remains failed. Research UNRESOLVED/manuscript PAUSED; old failures/caps/source limitations unchanged.
