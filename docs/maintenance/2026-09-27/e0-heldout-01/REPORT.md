# E0-H1 held-out-system confirmation — completed 2026-09-27

Frozen [PROTOCOL.md](PROTOCOL.md) and source/input identities preceded all
new trajectories. E0's original algorithmic source hashes matched the E0
freeze. Six complete RAP-SLAM runs (O/A on 07/09/10) and three same-data
KISS-SLAM default runs completed. Separate trajectory/metric validator passed
nine per-run groups of checks (`validation.json`); an independent PowerShell
recount passed 28 frame/config/mean/decision checks
(`decision_crosscheck.json`). Decision under the predeclared E0-A versus O
rule: **HELDOUT_TRANSFER**. This is an engineering result, not a new RAP
method or fully unseen-data claim.

## Full-system results

Camera KITTI ter (%) and SE(3)-aligned LiDAR ATE (m), identical frame sets
and metric implementation for the three methods:

| Seq | O ter | A ter | KISS ter | O ATE | A ATE | KISS ATE | O/A accepted loops |
|---|---:|---:|---:|---:|---:|---:|---:|
| 07 | 0.5400 | 0.3947 | 0.3866 | 0.3598 | 0.3264 | 0.3154 | 12 / 12 |
| 09 | 0.9811 | 0.5937 | 0.5421 | 1.4703 | 1.0745 | 1.2591 | 10 / 10 |
| 10 | 1.3574 | 0.5285 | 0.5250 | 1.8228 | 0.7635 | 0.7178 | 0 / 0 |
| Arithmetic mean | **0.9595** | **0.5056** | **0.4846** | **1.2177** | **0.7215** | **0.7641** | — |

The 0.205 degree correction A improves mean ter by 0.4539 percentage points
and mean ATE by 0.4962 m versus O, with no per-sequence ter regression;
it passes the predeclared transfer rule. A's mean ATE is 0.0426 m lower
than KISS-SLAM's here, driven by 09. KISS-SLAM has lower ter on all three
sequences and lower ATE on 07 and 10. Do not summarize this mixed comparison
as general pipeline superiority. The KISS comparison is same-data, but the
pipelines differ beyond the correction and were not component controlled.

## Odometry and loop observations

| Seq | A odometry ter | A full ter | A odometry ATE | A full ATE | A strict correct / incorrect accepted |
|---|---:|---:|---:|---:|---:|
| 07 | 0.3838 | 0.3947 | 0.3666 | 0.3264 | 12 / 0 |
| 09 | 0.5194 | 0.5937 | 1.2041 | 1.0745 | 0 / 10 |
| 10 | 0.5285 | 0.5285 | 0.7635 | 0.7635 | 0 / 0 |

On 09, all ten accepted A loop transforms miss the strict <=1 m / <=5 deg
pair threshold, yet full-trajectory aligned ATE improves relative to A
odometry. A strict pair label therefore does not establish a loop's graph
effect. The full ter worsens relative to odometry on 07 and 09 even while
ATE improves; both metrics must remain visible. On 10, no loop is accepted,
so the A improvement over O is front-end only. These observations do not
identify an optimal backend or acceptance threshold.

## Provenance, resources and scope

- Exact complete frame counts 1101/1591/1201; 71 source identities and
  3902 input identities froze before execution and rehashed after it.
- E0-H1 wall 548.6 s (<2 h cap), artifacts 408.8 MB (<20 GiB cap).
  No network, training, new model inference method, production change or
  Git synchronization. All result directories were newly created.
- 07/10 had prior SC-V1 data and old-odometry feasibility exposure; 09 had
  prior PG-V1 data exposure. None selected E0's arm or had a recorded
  RAP-SLAM full-system outcome before this protocol. All remain KITTI;
  pretrained RAP checkpoint membership is unresolved.
- The comparison supports transfer of the **frontend correction** to this
  fixed held-out system set. It does not establish cross-domain generality,
  a first-tier thesis claim by itself, or efficacy of F2's mechanism.

The next algorithmic question remains separate: F2's saved 08 bank has
41/75 positives with no strictly correct N candidate and ten incorrect
accepts with no correct candidate. Before implementing a visibility-aware
refiner, test whether a fixed local pose-refinement baseline can recover any
of those proposals without increasing wrong accepts. This is a new scoped
question, not a rescue of F2's S/P arms.
