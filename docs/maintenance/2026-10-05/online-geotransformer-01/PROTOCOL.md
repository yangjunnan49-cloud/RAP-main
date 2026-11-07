# All-online equal-point GeoTransformer comparator

Prospective observed-development comparison, all exact E0 A00/05/06/07/09/10:
71 attempts,58 current accepted RAP edges. All six sequences are exposed.
Official source/weight synthetic preflight passed. This external comparator
is never a RAP novelty or unseen-domain confirmation. One equal-point arm;
no full-density alternative or favorable subset. Official source declares
train00–05,val06–07,test08–10; actual checkpoint membership is not authenticated.

Freeze protocol, runner, independent validators, saved trajectories/logs/config,
all endpoint raw scans, GT/calibration identities (hash only), and validated
GeoTransformer source/checkpoint/extension/package manifests before inputs.
Construction and prediction must not read actual GT labels. Reconstruct exact
online inputs: rawfloat32 XYZ,range>=1.5m,no loading max-range filter,+0.205degree
correction,Open3D0.19 voxel0.4m,outlier20/2.5,float32,fresh PCG64seed42 cap4000
per scan (up to8000/pair). No RAP inference/features. Independently regenerate
all unique scans and native RAP alignment scores (tolerance1e-6), all71 scores
and58 native admissions must match before comparator inference. Failure stops
the study, no substituted input or outcome-driven rescue.

GeoTransformer release1.0.0/commit73e1439,checkpointSHA39cd6a01...,strict
restricted weights-only load, unchanged official architecture/config, CUDA
float32 eval, TF32off,no extra ICP. j source->i reference, ones features.
Official hierarchy0.3m/radius1.275/five stages. GT-free official neighbor
calibration on exact ordered71 pairs,keep_ratio0.8,sample_threshold2000; no
training dataset download or tuning. Seal geometry-only limits with inputs.
Identity dummy transform only. Save poses, matching confidence, point counts,
geometry scores and costs, discard GT bookkeeping. Repeat first pair per seq,
max pose delta<=1e-6. Require71 finite proper poses, no cherry-picked retries.

Common fixed gate on both methods: symmetric NN overlap(distance<1m)>=0.7
and mean symmetric distance<=2.5m, unchanged E0 K1 thresholds. P native full
graph; G replaces only existing58 poses with metadata/base noise unchanged
(diagnostic only); C uses comparator admissions from all71 and its mean_dist
for existing relfloor clip[1,3],Huber1. Same saved unoptimized keyframes/odom,
optimizer and constant propagation. RAP re-gate must reproduce58 edges.

Seal inputs and independent input validation before neural output; seal71
predictions before evaluator GT. Report all pair errors,strict1m/5degree,
supplementary2m/5degree,accepted strict-wrong and GT-far(>15m place) separately.
Accuracy is not graph utility; retrieval recall cannot be measured here.
P/G/C full trajectory KITTI ter/rer and aligned LiDAR ATE, existing protocol.
Arithmetic cohort means dev00/05/06,transfer-exposed07/09/10. Main material
signal for C: either cohort ATE>=5%better with ter<=0.01pp worse OR ter>=0.01pp
better with ATE<=2%worse, plus all six per-seq ATE<=10%worse and ter<=0.03pp
worse than P. G cohort signal is diagnostic only. >=5 additional strict poses
among71 is a descriptive candidate signal, never a RAP gain.

Independent validation: all scan reconstruction/scores/gates and calibration
histogram,freeze/seal/stage order; all71 labels/admissions; explicit GTSAM
P/G/C rebuild; independent Kabsch ATE and every KITTI segment; means/gates/caps.
Resource caps1800s total inputs+prediction+evaluation+validation (acquisition/
compile excluded),peak allocatedGPU<8GiB,processRSS<6GiB,artifacts<2GiB. Stop
on failures. No alternate weights/points/gates/precision rescue. Old stops and
banks persist; no training,production/default edit,manuscript,commit/Git sync.
