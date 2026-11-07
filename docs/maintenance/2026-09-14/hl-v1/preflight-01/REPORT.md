# HL0 preflight-01 report

2026-09-14. **HL0 PASS (bounded engineering prerequisites). HL1 NOT STARTED.**
H1/H2 have not been evaluated; this is not GO for training or evidence of hard-loop
accuracy. The owner requested HL0 only in this execution turn.

## Provenance and geometry

- Complete KITTI 05 source IDs 0-2760 (374 frozen keyframes) and KITTI 06
  source IDs 0-1100 (202 frozen keyframes) verified against the full-run parents.
- All 3,862 scans are present, nonempty, finite float32 XYZI with exact source
  names. All 3,996 parent manifest hashes match, including current RAP source,
  both checkpoints, calibration and GT. All timestamp counts, monotonicity and
  persisted values match the actual times.txt files. Parent reports/validation
  are present and parent INCOMPLETE markers absent.
- M0 snapshot manifest integrity matches its recorded digest and contains 1,568
  entries; INCOMPLETE is absent. Archived payloads were not all rehashed here.
  This remains same-volume preservation, not independent backup.
- Synthetic noncommuting rigid-transform transport checks: maximum point error
  3.55e-15, composition error 8.88e-16. Tested strict 1 m/5 degree labels on
  either side of thresholds, reflection rejection, invalid empty support,
  causal target selection, duplicate collapse and age exclusion.
- Maximum absolute GT rotation orthogonality residuals: 1.71e-7 (05), 1.80e-7
  (06). SVD projection used only for a rounding diagnostic changes an element
  by at most 9.31e-8. Saved hypotheses are never projected to repair validity.
  These checks support numerical labels against the supplied benchmark GT;
  they do not independently establish physical sensor/GT uncertainty.

## Support feasibility and sampling

| Sequence | Keyframes | Two distinct supports | One support | Zero supports |
|---|---:|---:|---:|---:|
| 05 | 374 | 51 | 321 | 2 |
| 06 | 202 | 22 | 179 | 1 |

The frozen keyframes often cross 2 m and 5 m at the same preceding frame, which
must collapse to one support under HL-V1. No frame-spacing or age rule was relaxed.
Local travel accumulates every frozen odometry step, not straight-line displacement.
Support metadata, timestamps and local poses are persisted for both sequences;
no KITTI 06 hypotheses or outcome labels were generated or inspected.

For resource profiling only, enumerated all KITTI 05 keyframe proximity pairs
within 30 m and separation >=200; 35 have two distinct causal supports per side.
The first ten by the declared HL-V1 pair hash were frozen before inference.
This is a feasibility sample, not the HL1 SC/proximity population, not the
four-stratum cohort, and not subject to the HL1 per-query stratified selection.
The complete profile candidate registry includes unsupported pairs. HL1 still
must build the expanded SC population, apply the three-per-query cap and four
stratum minima, and preserve shortages. The sparse support pool is a material
adequacy risk; it cannot justify a quantitative PASS or threshold relaxation.

## GPU and RNG results

Ten pairs, K=4 each: 40/40 outputs valid SE(3), 40/40 complete support scores,
160 valid support combinations, no inference failure and no CUDA OOM.
Four further generations were executed strictly for RNG validation, not added
to the hypothesis bank or used to improve any result.

- Synchronized complete pair wall time: 39.794 s total;
  median 3.671 s, range 3.625-6.482 s.
- Peak allocated GPU memory: 4.457 GiB; peak reserved: 8.998 GiB.
  Reserved memory includes allocator retention between pairs.
- Main preflight script elapsed time: 51.363 s, including
  geometry/support enumeration, model load, profiles and three RNG repeats.
  This excludes provenance hashing, the separate fresh-process validator,
  documentation and literature review. GPU kernel-active time and human labour
  were not separately instrumented; do not equate wall time with GPU-active time.
- Pair timings include raw reads, four support scans' geometric preprocessing,
  four anchor generation calls (including learned features), all support scores
  and result writes. Inputs were warmed by the full provenance read; no cold-I/O
  benchmark or broad difficult-cohort throughput guarantee is claimed.
- Request seeds follow the exact protocol with dataset `kitti`, sequence `05`,
  ordered historical source_i < source_j and zero-based generation 0-3. Each
  request seeds/restores Python, NumPy, CPU/CUDA PyTorch RNG and backend cap seed.
  Geometric support uses the same rules with fixed cap seed 42 and no learned
  support features. Neural anchor features remain enabled.
- Isolated repeat, reversed request order, saved cache reload and a new-process
  first request all recover transforms exactly (maximum element difference 0).
  Caller RNG/backend states restore exactly. Declared tolerance was 1e-6.
  Cache means a hash-bound saved hypothesis lookup; no general cache service exists.
- Maximum hypothesis orthogonality residual 1.65e-6, determinant error 1.55e-6,
  within the existing 1e-5 validity threshold. IEEE rigid-fit protection retained.

Strict/legacy labels are in an evaluator-only file; no GT fields enter the
support score. No B1/B4/S4/OR4 pilot comparison, fitted score or trained head exists.
The 40 hypotheses are an immutable preflight bank, not the forthcoming HL1 bank.

## Literature and limitations

See [bounded primary-source difference matrix](LITERATURE_DIFFERENCE.md).
RAP rigidity selection, trajectory-prior verification, sequential descriptor
evidence and learned hypothesis scoring are established prior work. RegScorer
adds a close overlap to inspect before HL2. Publisher full-text access was limited
for the learned scorers; this limitation is explicit and no novelty certificate
is claimed. The official RAP rigidity selector exists upstream but the current
pair wrapper does not export its trajectory statistic; B4 must be named accurately.

## Validation, files and exact next step

The independent validator checked all bank seeds, geometry and four-way support
availability, cache contents, fresh-process repeat and strict evaluator labels.
Final stability recheck covered 163 hashes including 15 used scans,
both parent metadata sets and non-scan source/checkpoint manifests. Four helper
files parse successfully. The artifact hash manifest binds all final outputs.

New algorithm helpers are only in RAP-SLAM/scripts/hl0_preflight.py and
validate_hl0_preflight.py. RAP-main adds maintenance audit/finalization helpers
and documents; model source and production defaults are unchanged. WSL required
sandbox escalation, which was approved; the initial default attempt was denied.
No unresolved execution exception remains. Existing dirty worktrees are preserved;
HEADs remain 4055d92 / 6d3f2d2 on main. No commit/push/pull/reset/cleanup occurred.

Next authorized research continuation: create a fresh hl-v1/pilot-01, implement
the exact broader candidate registry and evaluator-only strata, check adequacy
before expensive inference, and run HL1 discovery on 05. Freeze its report before
06 confirmation outcomes. Reuse the verified conventions and request seed policy,
not the preflight cohort as hard-loop validation. Inadequacy means INCONCLUSIVE;
no training or manuscript restart follows from this HL0 PASS.
