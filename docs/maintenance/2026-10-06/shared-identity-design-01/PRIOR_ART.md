# Primary-source comparison

Accessed2026-10-06. Bounded mechanism search, not exhaustive novelty clearance.
The positions below refer to verified sections/equations. No paper benchmark
score transfers to this project's cohort. Summaries are paraphrases.

| Primary source | Existing operation | Boundary for the candidate |
| --- | --- | --- |
| [RAP v2,2026-03-16, sections3.3/3.4, equations4/5](https://arxiv.org/html/2512.01850v2) | Clean point extrapolation, per-scan rigid projection every Euler step, original-noise reconstruction, global multi-view attention. | These are native RAP, including offline batch pose estimation; only cross-window interaction could be additional. |
| [RPF v1,2025-06-05, section3/appendixA](https://arxiv.org/html/2506.05282v1) | Joint point flow, point-index Procrustes pose recovery, fixed first anchored part. | Point identity to pose and common anchors are established; RAP's actual sampler remains anchor-free. |
| [FUSER v3,2026-06-16, section3.3](https://arxiv.org/html/2512.09373v3) | Joint global poses and trained SE(3)^N diffusion refinement from the model's prior poses. | Generative global correction already exists; frozen point-flow plus explicit identity is a distinction, not novelty proof. |
| [Wednesday v1,2024-03-30 UTC, section3.5](https://arxiv.org/html/2404.00429v1) | Pairwise diffusion matching, global pose optimization and learned joint diffusion pose refinement. | Do not claim first multiway generative synchronization. |
| [VGGT-SLAM2.0 v2, sectionIV-A, equations3/4](https://arxiv.org/html/2601.19887v2) | Same image reused in submaps; known point identity; equal frame position/rotation/calibration, remaining scale relations and graph optimization. | Shared-observation identity is a direct geometry precedent; camera calibration/scale ambiguity is not metric LiDAR SE(3). |
| [TALO v3,2026-03-18, sections3.2-3.5](https://arxiv.org/html/2512.02341v3) | Overlapping camera-pose alignment, same-pixel control-point propagation and spatial deformation fields. | Identity propagation has precedent; camera-map deformation does not justify nonrigid metric LiDAR warping. |
| [MultiDiffusion,ICML2023, section3.1/equations4/5](https://proceedings.mlr.press/v202/bar-tal23a/bar-tal23a.pdf) | Frozen diffusion on overlap windows; each update reconciled by shared-variable least squares and returned to windows. | Per-step overlap synchronization is a direct operator precedent. |
| [SyncDiffusion v1,2023-06-08, algorithm1/equation15](https://arxiv.org/html/2306.05178v1) | Cross-window agreement on predicted clean outputs, gradients back to states, overlap aggregation. | Clean-output consistency guidance or gradients are already established. |
| [SyncTweedies v4,2024-11-04, section3.2/Case2](https://arxiv.org/html/2403.14370v4) | Instance clean predictions mapped to canonical space, averaged, returned to instances before further denoising. | Closest clean-feedback framework; unknown SE(3) mappings and rigid-input orbits require derivation, not automatic novelty. |
| [Compositional Visual Planning v1,2026-03-03, sections4.1-4.3/equations7-9](https://arxiv.org/html/2603.02646v1) | Overlapping video factors share boundary variables; message passing constrains clean estimates during inference without retraining. | Shared identity plus clean-estimate feedback already exists outside registration; its noisy-factor theorem does not automatically apply to RAP. |

The broad proposal combines RAP rigidity, shared-frame constraints, generalized
Procrustes and synchronized generation. Estimating unknown gauges prevents
simple canonical averaging, but gauge estimation is itself classical geometry.
Adding an SE(3) fit or moving a terminal operator earlier is insufficient to
establish a new contribution.

The remaining narrow question is whether exact rigid-input cross-context
feedback changes frozen RAP trajectories usefully beyond identical terminal
synchronization and native complete context. No exact matched RAP performance
result or uniqueness proof was found in this limited search.

Queries combined RAP/RPF, point-cloud registration, shared scans/overlapping
windows, flow/diffusion, multiway synchronization, VGGT submaps and clean
endpoint consensus. Secondary search summaries located primary sources only.
No method was reproduced, repository/checkpoint acquired, training split
authenticated or new external comparator selected.
