# P0-02 corrected point-selection engineering preflight

Decision: **PASS_POINT_SELECTION_PREFLIGHT**. The fixed first two F2 pairs
per sequence (00/08), six scans each, were processed without evaluator GT
or labels. All four inputs have the exact six-part
`[2000,1000,1000,2000,1000,1000]` budget and finite nonzero 32-D features
from 5 m miniSpinNet patches supported by the complete 0.25 m voxel cloud.
The unchanged F2/C1 control inputs were checked but not rewritten.

The protocol, runner, independent validator and 49 source/input identities
were frozen before output. The complete four-pair bank was SHA-sealed at
`9f0c1c2f5f29b656f3e7c40f6cf0698b102bc92364fcff90dcfecb907c642228`.
Bank wall was 6.452 s, peak allocated GPU memory 2.090 GiB, and artifacts
4.162 MB, all within the frozen caps. Independent validation passed 261
checks, including all 24 source scans, point budgets, FPS membership and
exact regeneration of all 24 point/descriptor parts under the scoped
per-pair NumPy seed. No `INCOMPLETE` marker remains.

P0-01's unseeded descriptor attempt remains marked failed. P0-02 corrects
only that engineering defect; its small cohort cannot establish an
information advantage or registration improvement. Next freeze the exact
200-pair C1-style information metric, primary hard08 common-eligible set,
margin, ordinary safety guards, resources and independent validator before
full output. No RAP generation or default change follows this preflight.
