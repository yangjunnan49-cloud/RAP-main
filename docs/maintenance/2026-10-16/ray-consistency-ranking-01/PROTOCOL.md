# RVC0 fixed radial-order ranking evidence test

Population: all200F2 pairs,100each00/08, in saved native N order, all4strata
25each. Use only anchor-only A, originalR4=min valid raw rigidity RMSE (stable
generation-order tie), from existing records. No candidate reselection after
new scores, rerun or pose change. Compare G1's200sealed full-scan KISS-Matcher
poses under exactly the same policies. No F/S/P rescue, seed/count/radius search,
reference editing, new graph/trajectory, backward, training or learned selector.

Freeze protocol/scripts, F2 record/label byte identities, G1 bank/seal/freeze,
all used raw identities, source correction and relevant historical stops/repo
states first. Verify original G1 freeze bindings for all raw/record/reference
inputs and its complete bank hash. Construction never numerically opens the
evaluator label/GT files. Select and seal whitelisted pose/source manifests.

Correct full raw scans exactly as G1: XYZ from float32Nx4 bin, range>=1.5m,
unmodified0.205deg kitti_vertical_correction, float32 then promote for geometry.
No voxel/outlier/replacement points. Counts must equal G1 per-pair counts.
These are approximate sensor-origin rays, not authenticated first-return/free
space or per-return timing. No inference of physical emptiness/calibration.

Each unique(seq,frame) supplies2000sorted raw retained row indices without
replacement, default_rng(seed=int(first8SHA256bytes('RVC0|seq|frame'),big)).
All candidate/policy arms share those queries, full XYZ/ray witness support and
exact input identities. Scan reuse/correlated pairs remain explicit.

For each hypothesis i<-j score both j->i and i->j using general matrix inverse.
Transform2000queries into the target sensor frame. For each nonzero transformed
query, find ALL target unit rays within0.15deg(chord radius2sin(.15deg/2)).
For its range r and target cone ranges S: agreement if any |s-r|<=1m; else
front contradiction if min(S)>r+1m; else occluded if max(S)<r-1m; otherwise
mixed-depth unknown. Empty cone/zero range is angular unknown. Agreement takes
priority. Behind/mixed/unknown are neutral, not false positive evidence. Store
all query rows/cone CSR memberships/NN distances/classifications, not merely
aggregate scores. No calibrated ray width or probability is inferred.

Five fixed scores, all high-is-confident, no sign/weight/threshold fit:
 V: min two-direction agreement/(agreement+front_contradiction), eligible only
    when BOTH directions have>=100agreement points;
 R: min agreement/2000, same eligibility as V, removes contradiction term;
 O: min ordinary full-target NN within1m fraction, all valid poses eligible;
 D: minus max two-direction mean of the smallest200(10%) ordinary NN distances;
 F: minus max two-direction mean of ALL ordinary NN distances.
Policies do not optimize/select an alternative pose. Tie order is ascending
SHA256('RVC0|rank|seq|pair'), identical across policies/candidate families.

For each sequence/family/policy select topK eligible pairs, K00=29/K08=32,
exactly old A accepted24/27+5. Never fill from ineligible rows; any primary V
shortfall fails. All ranks/selections and pointwise evidence for all400poses
must seal before numerical reference/label access. This is batch fixed-budget
ranking feasibility, NOT an online gate or a new official SLAM system.

Postseal only: existing F2 calibrated evaluator_gt arrays and strata determine
strict<=1m AND<=5deg, identical to old task. Validate selected A generation/
poses/strict metrics against original A evaluator fields; baseline correct
accepted22/17, incorrect2/10. Count strict correctness on all selected pairs,
and confuser acceptance separately. No exposure relabeling or significance claim.

ALL gates on BOTH00 and08 are needed for evidence admission:
 1) A/V fills K, correct accepts>=old A correct+5, incorrect accepts<=old A
    incorrect and confuser accepts0;
 2) A/V correct accepts>=max(A/R,A/O,A/D,A/F correct accepts)+3, establishing
    an incremental radial-order contribution against the declared strong scores;
 3) A/V correct accepts>=G1/V correct accepts+5. Extra neural candidate history
    and full-scan geometry budgets are disclosed; not equal total work.
Fail any conjunction: retire this exact fixed proxy/ranking construction before
learning, new model inference, threshold calibration or full-system evaluation.
No alpha/count/range-band/K/seed/tie/stratum/score sign rescue. Even a pass only
admits a separate future online-threshold/new-source design. No novelty claim.

Before real data, fixed synthetic range/known transform controls: agreement,
front contradiction, behind neutrality, angular unknown, mixed-depth neutrality,
inclusive1m boundary, common sensor-basis rotation, direction inversion. These
are numerical controls, not efficacy fixtures. Independent validator recomputes
ALL stored CSR cone membership angles/classes/scores/ranks/metric rows/gates
without importing driver. Full brute-force angular-cone and NN completeness
checks on fixed first8query rows in every direction; no all-ray completeness
claim for other queries, no full nonlinear solver to validate.

Caps include all enclosing attempts/imports/failures/independent validation:
1200s cumulative CPU wall,2GiB Linux processRSS,256MiB whole new dossier,GPU0.
No torch/Open3D/model import. Scan cache LRU8. Windows launch commit headroom
>=12GiB. Full child/native exits/logs retained; ordinary setup/closing RSS and
observer lifetime UNKNOWN, no arbitrary process-tree/all-native guarantee.
Exclusive outputs and original pending/failure preservation; no old cap reset,
archive packing/install/network data/model acquisition/outreach/process restart/
production/default/backbone/reference/manuscript/commit/Git sync.
