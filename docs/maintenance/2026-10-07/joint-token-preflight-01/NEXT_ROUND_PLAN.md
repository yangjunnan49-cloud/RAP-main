# After TR0: define a measurable readout experiment

Status PLANNED_ONLY. TR0 validates extraction/native invariance, not useful
matching information. No next-stage protocol, label bank, independent-context
bank, readout implementation or fitting exists. No training is authorized.

## Next executable planning unit: bounded data and supervision audit

Inspect existing dataset metadata/archives and payload availability in the known
local roots (KITTI,oxford_spires,part2), using read-only inventory and relevant
loader/source documentation. No downloads/install, GT-error computation, new
RAP inference or label generation. Record actual scan/pose/calibration/time
availability, physical sequence/site provenance and known checkpoint/data
exposure. Presence of a file or an uninspected archive is not a validated label
or independent site. Do not scan unrelated private directories.

The deliverable is one concrete dataset-role table and training annex draft:
which data can support a bounded development pilot; which data, if any, can
support confirmation; exact sequence/site grouping, chronological leakage
guards, source identity and label construction.00/05/06/07/09/10 E0 and08 pair
studies remain exposed. KITTI01-04 are present according to old metadata, but
neither physical independence nor checkpoint exclusion is established. No
neighboring-window random split; overlap and repeated physical site must be
disclosed. Local motion label plausibility needs an appropriately bounded
geometry/time/calibration check;09 cross-revisit discrepancy is not solved by
TR0. Avoid turning optional external-data completeness into endless thesis
maintenance: if confirmed independent data are unavailable, disclose that and
offer a bounded exposed engineering pilot for explicit owner authorization.
It cannot be called an independent originality/accuracy confirmation.

## Concrete mechanism and controls to finalize before fitting

Target: frozen RAP joint-flow representation -> new correspondences between
original measured point rows -> a new coupled SE3 local-motion measurement.
Do not select old failed poses or use GT to choose scan/windows/features/noise.
Use one small shared correspondence readout and one identical original-point
solver. Input adapters, dimensions, parameter counts, total work and common
geometric inputs must be declared; equal point counts are not equal cost.

The controlled comparison has three trained arms on identical labels/splits/
optimizer/solver/budget: direct native descriptors plus the declared common
measured-point inputs; independently conditioned frozen RAP tokens; jointly
conditioned frozen RAP tokens. Native R3, saved KISS and matched geometric
multi-scan motion remain reference controls, not revived/rescued native arms.
The independent-context construction must preserve original measured rows,
normalization, descriptor/noise/time/anchor roles while separating cross-scan
conditioning; source/interface feasibility must be checked before its freeze.
Do not compare an equally trained joint readout to an untrained descriptor
matcher, or call row-destroyed tokens the main competitive baseline.

Propose the smallest measured-point correspondence head, explicit overlap/
unmatched supervision and fixed proper-rotation pose fit. Freeze architecture,
losses on correspondence and coupled relative rotation/translation, label
ambiguity handling, optimizer/steps/seeds, total compute and failure stopping
before fitting. Reject GT-nearest labels that force dynamic/nonoverlap points
into arbitrary matches. Confidence output, if any, is not calibrated by TR0.
Do not reopen timestep/point-density/noise/window sweeps as old-route rescue.

## Admission and thesis claim

The first fitting pilot needs new explicit owner scope after a concrete annex
is reviewable. Its primary question is whether joint context contributes beyond
the equally trained independent-context control, with direct-feature comparison
and ordinary/dynamic/ambiguous safety. A small MLP improvement shared by all
three arms is evidence for the readout, not RAP-specific originality.

Only a coupled translation AND rotation local improvement can justify a separately
frozen system stage. Full native trajectories must show meaningful ter and
aligned ATE together with safety/compute; descriptor recall or pair success
cannot replace system metrics. Use the existing MDC0 lesson: lowering isolated
error components can still increase total segment error through cancellation.
Do not tune the later system rule on sealed pilot errors or report exposed
development as held-out confirmation. Originality remains conditional on the
specific construction and primary-source comparison, not token dimension.

Preserve every old negative stop, scientific seal/bank, official GT/metrics,
unknown checkpoint membership,09 discrepancy and original HEAD/dirty work.
No production/default/model/manuscript edit, training or Git sync in this next
planning unit. This is a bounded transition toward a useful experiment, not
permission for an open-ended audit or automatic head fitting.
