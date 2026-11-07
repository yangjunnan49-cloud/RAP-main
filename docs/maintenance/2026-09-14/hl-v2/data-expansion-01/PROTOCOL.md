# HL-V2 data-expansion bridge annex

Declared 2026-09-14 before new cohort labels or registration outcomes.
The owner authorized autonomous additional public-data downloads and asked to
avoid preventable sample-source blockages. HL-V1 pilot-01 remains INCONCLUSIVE.
This is an explicit amendment, not a revised claim that the original pilot passed.

## Data roles and access

First use complete local KITTI00 (0-4540) for discovery and KITTI02 (0-4660)
for confirmation, subject to full file/GT/calibration/timestamp checks. These
are historically observed development data; 00's previous regression-only role
is prospectively changed to development discovery. No new-to-pretraining claim.
Reuse the corrected full00 frontend; rebuild only 02 odometry from all raw scans
with existing KISS-ICP maxrange60/minrange1.5/voxel0.8/no deskew and keyframes
translation6m/rotation12deg/forced-last. No loop optimization affects sampling.

Before RAP outcomes, if either sequence lacks >=60 total or >=10 per stratum,
extend discovery with 05 then 07, and confirmation with 08 then 09, in that fixed
order. Each added sequence is a development sequence. Stop data-only expansion
when each role reaches >=20 available per stratum, providing headroom over the
minimum. Do not add/substitute sequences after inspecting model results.
Sample a target25 per stratum per role across its frozen sequence set; max3
per physical query (dataset,sequence,source_j). All shortages remain recorded.

MulRan inventory is the next external source: DCC01/02, then Riverside01/03,
then KAIST01/02, in that order, subject to official access, metadata and geometry
verification in a separate dataset adapter annex. Its official request requires
name/affiliation/email; none are fabricated. NCLT remains reserved for a later
external evaluation; it is not silently reassigned to this development bridge.
No unrelated account registration or purchase is authorized or needed.

## Explicit sampling/support amendments

Keep original 20x60/80m SC geometry and temporal source separation>=200. Per query:

1. Expand ring-key shortlist to50; compute SC distance for those50 and retain the
   lowest20 **without** the former SC<=.25 cutoff. Persist the cutoff flag so the
   original easy retrieval subset can still be identified. This studies plausible
   retrieval alternatives, not just previously accepted retrievals.
2. Retain the original closest5 odometry candidates within30m.
3. Add at most one real historical frame from each odometry-distance band
   [30,35), [35,40), ..., [75,80]m, chosen by the smallest physical-pair hash.
   This is an explicitly broadened offset-view sampling arm, not production
   retrieval or a claim of natural-stream prevalence. No synthetic clouds/poses.
4. Deduplicate pairs and retain all source membership, ranks, distances and
   pre-filter population. No GT participates in these three proposal arms.

Support frames now come from **past raw scans**, not only keyframes. Find the
nearest earlier source frame crossing each accumulated-local-odometry target
2m and5m. Require two distinct IDs per side, age<=5s and exclusion of anchors.
All other transport/scoring rules remain unchanged. This corrects the sparse
keyframe/short-support incompatibility while adding no future or GT motion.
Raw IDs do not imply independent noise. Missing support stays an exclusion
before inference. This amended definition needs bounded synthetic checks and
10-pair runtime/RNG validation before a scored bank.

## Unchanged labels, inference and decisions

Keep HL-V1's four priority strata and exact GT-overlap thresholds, ambiguity
gap .02 and historical-candidate separation200, target25 and query cap3. The
ambiguity proxy uses the retained top20 SC proposals. Use fixed seed42 geometric
preprocessing for GT/support; voxel.4/outlier20/2.5/cap4000/minrange1.5.

Seed strings replace only the protocol prefix by HL-V2. Ordered historical
source_i<source_j, dataset `kitti`, two-digit sequence, zero-based generation0-3.
Frozen RAP weights/features, five steps, K4 and request-local RNG are unchanged.
All selectors use one immutable bank. Keep B1/B4/S4/GT-only OR4/REJ and the
original .7/2.5 gate, strict1m/5deg correctness, error clipping and failure
denominators. Add the official rigidity selector if its statistic is accessible;
never label B4 as the official selector. No score weight fitting or neural head.

H1/H2, ordinary-loss limit, no-new-incorrect-pair screen, >=10 oracle/B4-discrepant
positive pairs and adequacy minima remain as in HL-V1 section7. Decisions are
per frozen discovery/confirmation role, with all component sequences reported.
No pooled claim of independent sites. For H1 recall takes precedence if both
recall and continuous-error paths pass. Failure/shortage retains exact original
decision; no synthetic padding or outcome-dependent resampling.

Data-only labels/availability may be inspected for both roles before inference
to prevent foreseeable wasted work; this explicit ordering clarification does
not permit examining confirmation RAP/selector outcomes before the discovery
model-result report is frozen. The full role manifests must be frozen before
any scored inference. Used labels remain evaluator-only; inference inputs have
no GT/stratum or dataset-derived correctness fields.

## Artifacts and scope

Use fresh hl-v2/data-expansion-01 for source/metadata/cohort audit. Use separate
fresh preflight and pilot paths if data adequacy permits. Preserve full source
hashes, failures, environment and report/INCOMPLETE semantics. Production settings
and upstream source remain unchanged; new algorithm helpers stay in RAP-SLAM.
This annex authorizes a bounded development bridge, not training or a claim of
CAS Zone2 novelty. MulRan site splits and head-training controls remain future
conditional work. Additional scans/downloads are tools to obtain evidence;
sample sufficiency will never be asserted until measured.
