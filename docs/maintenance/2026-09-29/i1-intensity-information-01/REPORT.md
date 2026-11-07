# I1 cross-visit intensity information audit — complete

Decision: **NO_INTENSITY_INFORMATION_SIGNAL** under the fixed
[PROTOCOL.md](PROTOCOL.md). All 200 F2 observed-development pairs (00/08,
100 each) used unchanged saved 2000-point anchors. Protocol, runner,
validator and 485 source/input identities were SHA-frozen. Every assigned
target/source intensity and raw-nearest distance was saved in the complete
GT-free bank; the bank manifest was SHA-sealed before evaluator GT or labels
were parsed. Independent validator passed 6,563 checks, including all 200
raw assignments, C1 geometric eligibility, pair metrics, 16 controls for
each supported pair, and the primary decision. No GPU or RAP inference.

Binding remained adequate across all 400 anchor scans: 100% of saved points
were within0.5m of a corrected raw point, with at least63 distinct assigned
intensities per scan. Bank wall19.717s, peak RSS0.073GiB, bank artifacts
5.793MB; all frozen caps passed.

| Group | Adequate pairs | Median control-minus-true intensity difference | Positive pairs |
| --- | ---: | ---: | ---: |
| 08 native K4 unavailable (primary) | 33/41 | 0.014868 | 27/33 |
| 08 native K4 available | 33/34 | 0.015403 | 29/33 |
| 00 native K4 unavailable | 16/23 | 0.005433 | 12/16 |
| 00 native K4 available | 52/52 | 0.025329 | 47/52 |

The primary group had median true/control mean absolute intensity
differences 0.152079/0.159873 on the raw approximately [0,1] scale.
Its median paired advantage 0.014868 failed the predeclared >=0.03 margin,
although 27/33 positive signs passed the separate two-thirds condition.
This is a small association at GT-defined corresponding points; it is not
an executable matching, candidate creation or registration gain. The range-
matched shuffle controls range-dependent intensity distributions but cannot
remove every incidence-angle, material or scan calibration confounder.

Stop this exact nearest-raw intensity and range-bin proxy. Do not reduce the
margin, choose favorable bins or combine it with miniSpinNet post hoc.
[Intensity Scan Context](https://arxiv.org/abs/2003.05656) and
[intensity-image segment descriptors](https://arxiv.org/abs/2108.01383)
also make a generic intensity-fusion novelty claim untenable. A future
constructive candidate mechanism needs a different justified signal, a
matched comparator, fixed safety stops and independent confirmation.
Owner's original-breakthrough requirement, manuscript pause, E0 engineering
reference, all C1–C6 stops, no-default-edit and no-Git-sync boundaries persist.
