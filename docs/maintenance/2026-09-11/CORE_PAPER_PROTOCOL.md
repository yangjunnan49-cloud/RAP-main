# Core thesis comparison protocol v1

Declared after core-replay-01 and before backend-ablation-01. This is a prospective
ablation plan on already observed sequences, not an unseen benchmark registration.

## Scope and fixed choices

The core claim is that frozen pretrained RAP constraints can improve a KISS-ICP
trajectory through a traceable offline retrieval and graph-optimization system.
No task-level fine-tuning is performed. Training-domain novelty is not claimed.
Use POSS, KITTI 00, 05 and 06 with the exact source ranges and frozen frontends
identified in core-replay-01. Preserve its budget 12, preprocessing, single
generation, seed order, gate thresholds and NMS 0. Do not tune per sequence.

Primary metric: first-pose-aligned LiDAR translation APE RMSE, per sequence.
Secondary: rigidly aligned APE RMSE. Retain all sequences and negative results.
Do not pool frames across datasets or present these as official camera-frame
KITTI drift scores. Camera-frame drift and full frontend reruns remain separate
deliverables before claiming complete end-to-end benchmark performance.

## First controlled comparison

Reuse exactly the newly measured accepted edges from core-replay-01:

1. Frozen odometry, no graph loop correction.
2. Fixed loop noise, no robust kernel.
3. Fixed loop noise with Huber.
4. Relative-floor loop noise, no robust kernel.
5. Relative-floor loop noise with Huber (current system).

Keep all other optimizer parameters at the recorded source defaults. Save source
and input hashes, all optimized trajectories and metrics in an exclusive new run
directory. Verify arm 5 reproduces the saved fresh trajectory within numerical
tolerance before interpreting the ablation. Do not select a new default merely
because it wins these four already observed sequences.

All 40 edges are GT-labeled safe. This experiment tests backend behavior on the
current clean cohort; it cannot establish robustness against false loops. Gate
removal would accept the same edges and is therefore not an informative ablation.
Registration and retrieval baselines require fresh, matched candidate experiments;
do not substitute historical runs with different budgets or protocols.

## Remaining evidence, ordered by value

First complete the controlled backend table. Then run a matched conventional
registration comparator on the same candidate pairs and initial conditions, with
its own documented acceptance policy. Before evaluating it, fix its settings and
record any tuning data. Finally rerun core frontends where feasible to replace
historical frame-binding assumptions. Runtime measurements must separate stages
and cannot mix warm-cache replay time with full-system time.

Statistical gating is optional. Any future cohort must be allocated by whole
sequence/site before fitting, retain rejected and failed candidates, and report
class counts and nearby-site dependence. Do not choose split seeds to obtain a
desired score. The existing curated pilot and all-safe replay are development
evidence, not independent calibration or final statistical validation.
