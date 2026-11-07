# ER1: a prospectively distinct robust essential-refit baseline

Authority is the owner's explicit current-window project continuation. VB1's single raw-RANSAC control attempt remains CLOSED_CONTROL_FAIL, with its original source, 0.1/0.5-degree conjunction, seed, fixture and resource receipt unchanged. CD1 completed 13 synthetic interface controls and one analytic certificate; it admits no measured images. Neither result is relabelled here.

The distinct implementation question is whether adding explicit robust geometric refitting to a consensus proposal yields a functional ordinary camera baseline. VB1 has no refitting stage. Its 1-pixel consensus condition admits an analytic 0.2-degree-error candidate on all 96 exact correspondences; a consensus tolerance is not an angular-accuracy certificate. ER1 adds a documented five-parameter geometric optimization, not another RANSAC setting or seed. It has no claimed learning novelty or accuracy guarantee. Preserve the raw proposal and final output for every pair so any measured-data benefit or harm remains visible. No selection between outputs may use references.

## Frozen inputs and unchanged components

Use exactly VB1's source-sealed 273 PNGs, 200 ordered pairs, archive P0 intrinsics, isolated OpenCV5.0.0/NumPy2.3.5 and evaluation-only references. Source copies are byte-bound to VB1. All original SIFT, mutual-ratio, RANSAC threshold/probability/iteration count, per-pair seed, cheirality/support and rotation-validity settings are unchanged. VB1's clean/nondegenerate/scale/direction/no-evidence controls remain; its same fixed outlier fixture and strict rotation <0.1 / direction <0.5 degree control are applied to ER1's final output unchanged. One control attempt only. A failure closes ER1 with no real-image stage or further estimator/setting retry in this continuation.

Full original control/prediction/evaluation/audit semantics and resources are in REFERENCE_PROTOCOL.md, a byte-identical preserved copy for context. This protocol explicitly replaces its method with the following refit and its origin with the ER1 origin; it does not restart VB1 or inherit unused VB1 budget.

## Explicit refit algorithm

Only an already-valid ordinary raw pose may be refined; a raw no-evidence record is not rescued. Use its original essential-inlier correspondences only. With F=K^-T[t]_x R K^-1, minimize signed Sampson pixel residuals e=(x_j^T F x_i)/sqrt(||(F x_i)_xy||^2+||(F^T x_j)_xy||^2). Rotation increments use the exponential map; translation increments use two orthonormal tangent vectors and renormalization. No translation magnitude is estimated.

At each of at most 30 iterations, scale s=max(1e-6 pixels,1.4826*median(abs(e))). Set w=(1-(e/(4.685*s))^2)^2 when abs(e)<4.685*s, otherwise zero. This fixed, data-dependent robust weighting is the new mechanism; no synthetic truth/inlier IDs enter it. Require >=8 positive weights and rank-five weighted central-difference Jacobian (step 1e-6 radians). Solve the weighted least-squares linearization with NumPy lstsq. Limit the joint increment norm to 0.1 radians. Try the eight fixed fractions 1,1/2,...,1/128 of this increment, accepting the first strictly lower fixed-weight squared residual cost. Recompute scale/weights only on the next outer iteration. Stop on no decrease, rank/support failure, increment norm <1e-10 or iteration cap, retaining the current pose. No restarts or adaptive RANSAC/ratio/feature thresholds.

Retain all accepted/rejected line-search costs, scale, positive-weight count, input/output R/t and increments. Reconstruct E=[t]_x R; run the same native cheirality check on the original essential mask, retain its resulting signed pose/mask, and enforce the same support/validity gates. A refit exception or invalid/insufficient final pose yields an explicit no-evidence final record; the initial raw record remains available as a descriptive comparator. The optimizer is ordinary geometric pose fitting, no model/adapter/learned weights or RAP training.

## Measured-data admission, separation, readout and audit

Only after all ER1 controls pass, extract all 273 original images once, seal features, predict all 200 initial/final pairs under the exact Python read allowlist, and seal every output before the evaluation-only worker can read supplied reference/labels. No CF1 support veto. Keep every no-evidence and all 100-pair sequence, 75-positive, 25-confuser and eight 25-pair stratum denominators. Report final rotation/direction errors and frozen 5/10 and 15/30-degree descriptive bins, plus corresponding initial-raw summaries on the identical complete cohort. Do not choose a winning subset or declare an efficacy/safety gate from these bins. Source/reference/frame/physical/generalization/RAP-increment limitations remain unchanged.

The saved-output audit retains VB1's 273-cache/200-pair checks, independent descriptor-distance samples and all 200 Decimal60 reference solves. Additionally verify initial-raw angular readouts independently from the stored poses, and verify the frozen refit trace's fixed-weight cost decreases and finite proper/unit pose states. No new prediction is generated by audit. The reviewer can inspect both estimators' complete records, not only a favorable aggregate.

## Finite resources

Conservative ER1 origin 2026-10-28 07:01:26 UTC; 5400 seconds inclusive, preparation <=1800 seconds, closure reserve 180 seconds. Sole launches: controls <=60s, features <=300s, predict <=300s, evaluate <=120s, audit <=180s. Each child <=1GiB RSS, new dossier <=1GiB. Fresh commit headroom >=12GiB/query <=2s before each child. One CPU thread/OpenCL off, child-only BLAS thread environment, no installation/network/WSL/GPU/Torch/model/default/production/Git writes/outreach/scheduler/goal-status action. Preserve VB1/CD1 costs separately, never spend their old caps again or sum overlapping inclusive wall intervals. Stop and retain actual evidence on any failure. No additional estimator attempt after an ER1 failed control.

Research UNRESOLVED and manuscript PAUSED. Actual account boundary/reset handling remains separate; no automatic reset resume.
