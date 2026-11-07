# C4 temporal-support feature intervention — complete

2026-09-29. Frozen decision: **NO_MATERIAL_SUPPORT_FEATURE_RELIANCE**
under the specific *ordinary-pair pose* and positive-control gates in the
[protocol](PROTOCOL.md). This label must **not** be read as “RAP ignores
support features”: the support-only intervention changed raw flow on all28
pairs and materially changed poses on15/28, concentrated in confuser and
hard-positive strata. It did not meet the predeclared ordinary-pair gate
and did not demonstrate a useful candidate-creation improvement.

## Execution and validation

The protocol, runner, separate validator and201 input/source identities
were SHA256-frozen before inference. The fixed28 C2 pairs reused exact F2
points/noise and C1 six-part miniSpinNet features. Arm T kept all features;
arm A shuffled only the two anchors (parts0,3); arm S shuffled only four
temporal support parts (1,2,4,5). Both used C2's fixed per-part permutation
indices. All28 T five-step raw and state trajectories reproduced saved F2
N0 **exactly** (max delta0.0). Points, normalization, seed, model and
noise were identical among arms. The GT-free bank was sealed before
evaluator labels at SHA256
`e3a76e7d4596fb3e7db0af1af3afeae7fef6c6bc45c475b2d0ed0cf35948d0db`.
Bank wall65.164s, peak allocated GPU0.687GiB, artifacts75.37MB;
all caps passed.

The independent [validation](validation.json) passed1,329 checks:
frozen hashes, all28 exact reproductions, A/S within-part permutations
and unchanged other parts, all trajectories, independent CPU pose fits,
paired raw/pose deltas, GT strict labels and frozen decision arithmetic.
`INCOMPLETE` is absent. No C1/C2/C3/F2 artifact, production source,
default or Git state was overwritten or synchronized.

## Observed response

The positive-control A arm materially changed pose on **5/7 ordinary**
pairs and met its predeclared adequacy gate. S changed raw-final flow
above0.005 on **28/28**, but materially changed pose on **0/7 ordinary**
pairs. Its ordinary relative pose deltas were small: translation
0.040–0.201m and rotation0.059–0.206deg, below both 0.25 thresholds.
The large raw changes therefore mostly cancel in anchor rigid decoding
on these ordinary pairs. Across all28, median raw-final RMS was0.450
for A and0.348 for S in normalized model coordinates; these are
out-of-distribution intervention effects, not registration errors.

| Fixed group | Pairs | A material pose responses | S material pose responses | T strict | S strict |
|---|---:|---:|---:|---:|---:|
| 00 confuser | 4 | 4 | 4 | 0 | 0 |
| 00 ambiguous positive | 4 | 4 | 4 | 4 | 2 |
| 00 low overlap | 3 | 3 | 2 | 0 | 1 |
| 00 ordinary | 3 | 2 | 0 | 3 | 2 |
| 08 confuser | 2 | 2 | 2 | 0 | 0 |
| 08 ambiguous positive | 4 | 3 | 0 | 4 | 4 |
| 08 low overlap | 4 | 4 | 3 | 0 | 0 |
| 08 ordinary | 4 | 3 | 0 | 2 | 2 |

Of22 fixed positives, S changed the strict correctness label on4:
one gain and three losses, all on00. There was no strict-label change
on08. These flips alone were insufficient for the frozen decision because
the required >=6/7 ordinary material pose responses were absent. The
heterogeneous hard-pair response is descriptive and should not be turned
into a revised post-hoc success criterion. In particular, support
features may affect generated flow and hard poses, but C4 does not show
that their normal information is beneficial, or that removing/replacing
them would improve candidate creation.

## Next boundary

Retire feature shuffling as a candidate method. C2/C4 localize a strong
anchor-feature effect and a support-feature flow effect with substantial
hard-pair heterogeneity. The next useful question is **constructive**:
can a defined, GT-blind use of cross-scan context create correct
hard08 candidates without sacrificing ordinary pairs or safety? Before
any efficacy run, audit existing RAP attention/support handling and
primary low-overlap registration methods for overlap-aware selection and
geometric context, then freeze one mechanism with matched controls,
cost and stop margins. PREDATOR and GeoTransformer already use related
ideas; a generic overlap head or geometric attention transplant is not
an originality claim. No such C5 protocol or method has started.

E0 held-out engineering transfer remains the positive metric result.
All prior negative route stops, manuscript pause and no-Git-sync
boundary persist.
