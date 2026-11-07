# MC1 measurement-source audit

Status: **VALIDATED**, decision **NO_SUPPORTED_PROPAGATED_COVARIANCE_MODEL**.
Owner requested an explicit next plan and further progress on 2026-10-07.
This is a read-only source/census result, not a metric intervention.

The 53-identity freeze preceded output. All 12,296 saved scan poses, 1,800
keyframes and 1,794 intervals on E0 A 00/05/06/07/09/10 were audited without
reading evaluator poses or generation-label JSON. Independent scalar code
reproduces the original keyframe selection and every interval, source-frame
binding, motion summaries, 71 attempts and 58 accepted edges. Maximum motion
delta is 1.776357e-15; census/validator take 0.178/0.105 s, peak RSS 37.95 MiB.
No failure or repair occurred. Seals precede this report.

| Sequence | Keyframes | Scan span min/median/p95/max | Rotation triggers before 6 m | Loop endpoint fraction |
|---|---:|---|---:|---:|
| 00 | 670 | 3 / 6 / 10 / 45 | 152 | 2.54% |
| 05 | 374 | 4 / 7 / 11 / 94 | 62 | 6.15% |
| 06 | 202 | 1 / 5 / 8 / 10 | 25 | 11.88% |
| 07 | 134 | 4 / 7 / 13 / 90 | 39 | 7.46% |
| 09 | 266 | 4 / 6 / 8 / 16 | 22 | 2.63% |
| 10 | 154 | 4 / 7 / 11 / 66 | 17 | 0% |

Source inspection, rather than these span statistics, establishes the missing
interfaces. `pose_graph.py` reuses one diagonal odometry noise model for all
keyframe intervals. `odometry.py` and installed KISS-ICP 1.3.0 return poses;
registration/map interfaces do not export per-scan covariance or observation
source/cross-correlation records. The selected saved artifacts contain none.
Adaptive KISS matching thresholds are not covariance estimates. The census's
absence flags summarize this bounded source audit; the scalar validator checks
motion/identity/event records, not statistical calibration.

Under right perturbations, independent composition would transport one noise
through Ad(B^-1), but reused scan-to-map observations require cross-covariance
terms. These inputs are unavailable. Variable scan span therefore does not
justify sqrt(span) weighting or show the constant noise causes metric harm.
Point-to-point inverse Hessians also neglect rematching. See the primary
[GTSAM derivation](https://gtsam.org/2021/02/23/uncertainties-part3.html),
[joint-pose uncertainty](https://arxiv.org/abs/1906.07795) and
[ICP covariance analysis](https://arxiv.org/abs/1410.7632).

The logging source persists attempts, not the complete ring-key shortlist or
pre-cap SC/proximity exposure. Absence of that record is not low recall.
No retrieval-budget/quota rescue is admitted. Loop endpoint fractions measure
accepted endpoint coverage only, not place-retrieval recall or useful coverage.

The defensible next question concerns measured geometric curvature at fixed
RAP loop centers, rather than inventing per-scan statistical information.
Measured surface-direction information is strong prior art:
[X-ICP](https://arxiv.org/abs/2211.16335) and
[information-aware PGO](https://arxiv.org/html/2607.13516v1).
It is a conditional model shape, not calibrated uncertainty or proof that
aliases are correct. Its metric effect and RAP-specific originality remain
unestablished. NEXT_ROUND_PLAN defines a separately frozen analytic preflight
and a conditional direct system screen.

All prior negative stops, banks, RAD1 original failure/repair, unknown checkpoint
membership, official labels/metrics, 09 physical discrepancy and original
breakthrough requirement remain. No scan, inference, GT, optimization,
training, production/default/model/manuscript edit, acquisition or Git sync.
