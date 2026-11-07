# LC0 follow-on source check

Read-only primary-source check,2026-10-07; not an algorithm/result or additional
experiment. LC0 decisions remain those prospectively frozen in PROTOCOL.md.

## Independent inexpensive retrieval cue

[RING (IROS2022, author paper)](https://arxiv.org/abs/2204.07992)
uses a Radon sinogram for place recognition and orientation/translation
estimation without learning. The authors derive a translation-invariant
descriptor and orientation-invariant matching metric. This is a relevant
comparison if structural opportunities are absent from native SC/proximity;
its claimed robustness is not verified on our data.

[RING++ (author paper)](https://arxiv.org/abs/2210.05984)
extends this line to sparse-map global localization and large viewpoint
differences, including conditions on multichannel feature extractors for
preserving roto-translation invariance. This supplies a possible independent
geometry source with no fitting prerequisite. Local code/dependencies/runtime,
compatibility with our scans and actual metric effect have not been inspected
or tested. No source/weights have been acquired. A BEV/spectral cue alone is
prior-art engineering and does not establish RAP originality.

## Measurement availability and graph feedback

[Gupta et al.,2026 author paper](https://arxiv.org/abs/2607.13516)
combines ICP information estimation, hierarchical loop matching and retroactive
loop discovery using an optimized graph. The authors also evaluate local map
consistency separately from trajectory accuracy. Consequently, missed-loop
recovery, geometry-dependent weighting and backend-guided rediscovery already
have close precedent. We verified the abstract and bibliographic record here;
this is not a reproduction or a detailed implementation audit.

## Consequence for thesis design

LC0 tests whether a particular fixed-budget measurement opportunity exists;
it does not invent retrieval or prove missed measurements are recoverable.
If a later cue is warranted, compare it fairly at the original neural attempt
budget, with original geometry/admission and complete online attempts. A RAP
contribution must additionally show useful information from a distinct RAP
interface beyond a matched geometric/direct-feature control. The source-only
512-D joint-token proposal in ../learned-measurement-design-01 remains
conditional; no readout or fitting is licensed by this literature check.
