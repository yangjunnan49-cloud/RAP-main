# KITTI06 visual audit

Inspected strata_examples.png on 2026-09-14 after the KITTI05 discovery freeze.
The ordinary population example (64,891), O_GT=0.849, shows substantial shared
structure in GT-aligned XY. It is unsupported and not selected. No confuser,
ambiguous-positive or low-overlap population example exists under HL-V1.
No disagreement with the numeric ordinary label was identified in this limited
projection; no membership changed. This is not semantic repetition validation.

Independent validation reproduced the candidate union, support construction,
empty selection and GT-free inference-input schema. Batched versus scalar SC
maximum difference 2.35e-8; example GT overlap agrees exactly with independent
chunked brute-force distances. No model hypotheses or scientific outcomes exist.
