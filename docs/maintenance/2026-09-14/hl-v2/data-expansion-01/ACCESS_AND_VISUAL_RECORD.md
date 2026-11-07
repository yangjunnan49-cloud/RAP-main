# Data access and fixed-label visual record

The owner authorized autonomous public data acquisition on 2026-09-14.
Local inventory found full scan counts for KITTI00-10 and timestamp files; this
was only an inventory until the subsequent byte-level source audit on00/02.
E: free space was approximately666.6GB before expansion. No MulRan data or local
MulRan adapter was found in the inspected dataset roots and SLAM source paths.

[MulRan official download page](https://sites.google.com/view/mulran-pr/download)
requires a download request with name, affiliation and email, and specifies no
more than three concurrent downloads. The form was read, not submitted. The
missing identity information was requested asynchronously; no identity was
fabricated and no access restriction was bypassed. Official request:
[form](https://docs.google.com/forms/d/e/1FAIpQLSefGq08USiLiUE6FWxCgAeixjj2oPZu2XqTMfTXpNh2QIzODg/viewform).
The official page identifies GT at the rear-wheel base, so a future adapter must
apply the published base/LiDAR extrinsic. Its public calibration/sample links
were located; no unsuitable tiny parking-lot sample was used to fill hard strata.

[NCLT](https://robots.engin.umich.edu/nclt/index.html) has direct downloads but
remains reserved for external evaluation. Metadata states that its dense GT
uses odometry interpolation between SLAM-graph nodes; later strict labels need
that uncertainty check. [ALITA](https://github.com/MetaSLAM/ALITA) was screened
as a fallback; its processed clouds are map-derived submaps and do not directly
provide the disjoint raw-observation experiment. Neither fallback was downloaded.

Because local expanded data now supply100 pairs per role with25 per stratum,
extra raw downloads are not necessary to execute this bounded direction test.
MulRan is still the prospective expanded/site-split source if the pilot supports
further work. No foreign-domain or pretraining-exclusion claim is implied.

Inspected sample_examples.png after freezing data membership and before model
outcomes. Both confuser examples show spatially separated structure after GT
alignment; low-overlap examples show partial common structure; ordinary examples
show substantial shared structure. Ambiguous-positive examples have shared road
geometry, but a single XY projection does not establish semantic repetition or
prove that the competing historical places are indistinguishable. Retain their
numeric proxy labels with semantic status **unverified**, not visually certified.
No label disagreement requiring a correction was found in these views; no pair
was removed or replaced. These projections are illustrative, not a second GT.
