# HL0 bounded nearest-paper difference check

Checked 2026-09-14. This is a prerequisite audit, not a novelty certificate.
No manuscript claims or learned method are established by this preflight.

| Primary source and reading depth | Reused/established mechanism | Proposed difference and required evidence |
|---|---|---|
| [RAP](https://arxiv.org/html/2512.01850v1), HTML sections 3.3/3.4 and local source | Frozen generative registration and rigidity-based selection across samples | Extra causal raw scans excluded from anchor generation provide hypothesis-specific metric support. Best-of-K itself is reused. |
| [ROVER](https://arxiv.org/html/2508.13488v1), HTML method section III | Candidate-conditioned trajectory optimization and trajectory-prior verification | HL-V1 uses local within-visit motion only to transport support scans; it does not score deformation of the global trajectory. Temporal verification itself is established. |
| [Sequential Testing](https://arxiv.org/html/2512.09447v1), HTML section III | Accumulation of descriptor-distance evidence with a truncated sequential probability ratio test | HL-V1 scores cross-visit raw metric geometry under each proposed transform. Disjoint frame IDs do not imply independent noise or statistical coverage. |
| [A hybrid algorithm with inlier-guided Hough voting for point cloud registration](https://www.sciencedirect.com/science/article/pii/S0925231224020484), publisher indexed abstract; direct DOI/page fetch failed | Geometric consensus hypothesis generation and a learned Hough voting network with inlier-count prior for model selection | Corrects the earlier matrix's generic label to the actual paper title. A learned pose ranker is established; extra support observations and matched-input controls must justify any later distinction. Full-text audit remains limited by access. |
| [RegScorer: Learning to select the best transformation of point cloud registration](https://www.sciencedirect.com/science/article/pii/S0924271626000420), publisher indexed method excerpts; direct page returned 403 | Learned scoring of supplied transforms using geometric/feature conflicts | Newly identified close overlap with the proposed evidence head. Do not claim novelty for learned geometric scoring. Before HL2, inspect the complete method and compare same-pair scoring against disjoint-support evidence. |

The local RAP source implements rigidity selection in
`rectified_point_flow/modeling.py` (generation selection around lines 456-522).
The existing RAP-SLAM pair wrapper returns overlap and mean distance but does
not export the pre-projection trajectory rigidity statistics. Therefore B4 is
our same-pair overlap selector, not the official RAP rigidity selector. A later
HL1 adapter should expose that diagnostic if accessible without changing the
frozen generation; this preflight did not implement that baseline.

HL0 decision: the bounded comparison is complete with the stated reading-depth
limits. The specific evidence question remains testable, but generic learned
selection, multiple proposals and temporal verification are not new. No change
to HL-V1 gates, thresholds, K or point caps is justified by this literature check.
The same-input pooled-support and equal-compute comparisons remain required
before a method-advantage or novelty claim.
