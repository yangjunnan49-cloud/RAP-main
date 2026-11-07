# RLP1 review: suitable for a bounded pilot after one correction

**READ_ONLY_REVIEW_COMPLETE; OWNER_AUTHORIZATION_PENDING.** This review follows
the owner's request to recover context and audit the previous conversation's
task. It authorizes no inference, labels, fitting or trajectory execution.
The recommendation is to approve the scope in REVIEWED_SCOPE.md, including
mandatory prerequisites and the corrected seed convention.

## Recovered task and authorization

The previous chat is **规划RAP下一步提升方向**, thread
01a113b8-b101-73c1-ac2e-799472f5900a. Its latest owner instruction was
"启动下一步". That turn completed DS0 data/supervision design and ended with an
unanswered request to authorize small-head fitting after prerequisites.
DS0 STATUS explicitly records training_authorized=false, head_implemented=false
and experiment_frozen=false. The present owner request is a review instruction.
Historical allowance for conditional small adaptation in the HL direction does
not settle this new RLP1 scope.

TR0 validates extraction and native invariance of joint 512-D tokens. DS0 supplies
an actionable design, not learnability, accuracy, system gain or originality.
RAD1, R3/LMF1, D1, PFG1 and LC0 negative stops remain in force. The proposed
readout uses intermediate representations to create new original-point
correspondences; it is distinct from ranking failed poses or reopening the
stopped final-coordinate decoder.

## Evidence rechecked

- All 15 DS0 delivery entries matched before this review updated AGENTS.md.
  All 16 DS0 source-snapshot entries also matched, including sibling sources.
- All 20 TR0 bank files matched their seal. Freeze, bank-seal and validation
  hashes matched the separate validation seal. No model or validator was rerun.
- The 204-window manifest reconstructs its count-only rule, roles 144/12/48 and
  612 unique sequence/frame paths, with no repeated paths within the manifest.
- Four-window preflight exposure overlaps six frame paths in three draft
  windows: 00/t199 fit shares 198,199; 06/t201 development shares 199,200;
  07/t201 exposed evaluation shares 199,200. Keep these windows and disclose
  this exposure; do not select replacements after outcomes.
- Saved KISS odometry and source manifests for 07/09/10 match their earlier
  six frozen hashes. Their 1101/1591/1201 rows cover all 36 proposed endpoints.
  This checks availability and identity, not pose error or physical truth.
- Original HEADs and branches remain main 4055d929 on codex/meeting-20260930
  and SLAM 6d3f2d22 on codex/e0-f1-20260926. Existing dirty work was preserved.
  M0 archive manifest matches its preservation summary; archive payload was
  not rehashed.

## Required correction: seed byte order

TRAINING_ANNEX_DRAFT.md lines 35-36 calls its rule the original LMF1 rule but
says **little-endian**. The sealed source local_motion_common.py line 43 uses
**big-endian**. Its hash matches both LMF1 and TR0 freezes. TR0's four saved
seed values independently match big-endian SHA256-prefix interpretation:

| Sequence, t=200 | Correct big-endian seed | Draft little-endian seed |
|---|---:|---:|
| 00 | 721294808 | 3625319978 |
| 05 | 1717843090 | 2452907110 |
| 06 | 1644359845 | 2783969890 |
| 07 | 2246292046 | 1320346501 |

This discrepancy would change native preprocessing/noise and contradict exact
TR0 replay. Use the sealed big-endian rule for RLP1 and store each integer seed
prospectively. This is a design correction before outputs, not an experimental
repair. The original DS0 annex and its seal remain unchanged as historical
evidence; REVIEWED_SCOPE.md records the prospective correction.

## What the proposed controls can establish

J versus I is the main comparison: both expose 512 feature channels to the same
active readout capacity, with joint versus separated full-flow grouping. D is
a necessary trained direct-feature reference, but zero padding leaves only
13762 effective parameters versus 75202 in I/J. J>D alone cannot attribute a
gain to joint information. I may be outside the pretrained one-part distribution;
a J>I result therefore supports this particular context-removal comparison,
not universal generative superiority. Runtime grouping/independence remains
an essential preflight, including the original five-step states and RNG draws.

The next pilot measures adjacent-frame local motion. It does not directly test
hard low-overlap revisits or solve the old 08 hard-loop candidate deficit.
Local gain must beat G3 and saved KISS before proposing a separate system stage.
A system stage still needs a concrete insertion point and both ter and aligned
ATE; improving a learned local feature does not establish a trajectory benefit.

Generic contextual correspondence learning already has direct precedent in
[GeoTransformer](https://arxiv.org/abs/2202.06688). A small MLP is not an
originality result. The defensible conditional goal is to demonstrate useful
measured motion from the frozen generative representation with fair controls,
then reproducible system gains. The owner's breakthrough requirement persists.

## Practical limitations and scope supplement

The old annex specifies per-sequence safety relative to I/D, but its G3/KISS
usefulness paragraph only specifies pooled gains. A strong pooled gain could
hide harm on one sequence. REVIEWED_SCOPE proposes extending the existing
0.005 m / 0.02 degree mean-regression limits to G3 on 07-10 and KISS on 07/09/10.
This is a stricter prospective admission gate, pending owner approval.

Coverage is clarified as every seed/window primary prediction: 3 arms x 3 seeds
x 48 windows = 432 valid poses. Never take a median of only successful seeds.
Missing output prevents a primary pass; complete valid coverage still requires
independent source, labels, fit separation, solver and metric validation.

KITTI itself warns that short-segment GT error can bias evaluation, motivating
weak labels and limiting interpretation of millimetre-scale local margins.
Those margins are engineering screens, not verified physical accuracy or
significance tests. [Official KITTI specification](https://www.cvlibs.net/datasets/kitti/eval_odometry.php).
The published RAP split excludes KITTI08-10 and includes Oxford training;
our local checkpoint binding remains unknown. Historic exposure and absent
confirmed external payload prevent an independent-confirmation claim.
[RAP training data](https://arxiv.org/html/2512.01850v1).

No new generic dataset/literature inventory is needed. Runtime feasibility,
weak-label counts, gradient stability, full coverage and resource caps are
unresolved prerequisites, not reasons to promise success. A failure stops
this fixed construction and must not be generalized to all joint-token readouts.

## This review's delivery boundary

Only new review documents and the current handoff entry were written. No raw
clouds, numeric GT poses or checkpoint tensors were loaded; no relative GT,
correspondence labels, feature bank, gradient updates or errors were computed.
Saved odometry text was read for row counts only. Read-only sibling access
required and received sandbox approval after default access was denied.
No experiment failed and no repair or INCOMPLETE was created.

Old scientific evidence, DS0 delivery files and official metrics remain intact.
DS0's historical AGENTS.md entry will naturally differ after this handoff update;
do not overwrite its delivery seal. User approval remains the next action.
