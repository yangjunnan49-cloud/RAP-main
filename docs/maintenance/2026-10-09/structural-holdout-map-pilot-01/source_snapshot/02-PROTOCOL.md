# SMP2: support-preserving structural holdout

Prospective protocol, fixed before any SMP2 optimization or numeric pose-reference
outcome. Owner request: "不错，继续推进下一轮方案" after SMP1's concrete next plan.
This authorizes this isolated CPU development pilot and a next-stage design if
useful. The earlier relaxation of originality/rigor admits established geometry;
it does not relabel exposed development data or amend old experiments.

## Inputs and split

Use the four unchanged MMR0 attempt-02 eight-scan point banks and O initial poses:
00-200,00-800,05-200,06-200. All190332 already-retained points participate in the
same2m eligible-plane construction from shared_plane_map.py. Every patch retains
all its eligible per-scan rows. Same support/flatness rules; membership fixed at O.
No additional raw density, neural tokens, GT selection or even/odd division.

For each eligible integer voxel key(kx,ky,kz), encode the UTF-8 string
`SMP2|{window}|2|{kx},{ky},{kz}` with decimal integers, no spaces or newline.
Take SHA256 first4bytes as an unsigned BIG-ENDIAN integer; remainder0 modulo4 is
geometry holdout; other remainders are optimization. Approximate75/25 split,
not forced counts. Freeze this one split rule; no replacement, hash search or
feature ranking. Patch eligibility was selected using O and all observations;
holdout is excluded from pose optimization but is not an independent data/site
split. Correlated neighboring surfaces and O selection bias remain.

Optimization support:>=10training patches and>=100training points in every scan.
Holdout support:>=5patches and>0points in every scan. Otherwise retain an invalid
record with no candidate, no threshold/window/split rescue. Report full and split
counts, per-scan point coverage, and normal scatter eigenvalues at O.

## One candidate

O versus P only. P uses training-patch scan-balanced plane moments with analytic
plane refitting and Schur elimination, plus the unchanged adjacent O motion
regularizer(.10m/.15deg). This is a correlated engineering regularizer, not a
calibrated independent sensor covariance. Reuse the byte-frozen SMP1 algorithm:
24updates,1e-3diagonal damping,1deg/.2m step limits and fixed backtracking.
Anchor pose0; correction validity<=1m and<=5deg. No G arm, warm start, tuning,
extra updates or full trajectory. BALM established prior art is credited.

Geometry-check RMS is sqrt(mean(max(minimum pooled covariance eigenvalue,0)))
over entire held-out patches. Each patch and contributing scan has equal mass.
Refit the holdout plane nuisance parameters at O/P for this report only; never
use them for pose updates, stopping, selection or backtracking. Also report
training geometry and unchanged regularizer cost. It is surface consistency,
not physical accuracy or statistically independent validation.

## Ordering, checks and decision

Freeze sources, protocol, old banks and GT/calibration file identities first.
Run a bounded split/subset numerical preflight. Generate and seal all four
records/predictions without parsing new numeric GT. Independently check every
moment against explicit points, patch membership/hash/mass coverage, holdout
costs, proper poses/correction bounds, traces and selected training gradients.
No full optimizer replay required for this discovery stage. Only then parse
unchanged official reference/calibration and compute the unchanged MMR0 local
translation RMSE, mean rotation error and rigid-aligned position ATE. Independently
reconstruct metrics and the complete conjunction.

Eligibility requires all four supported/valid;>=3/4positive aligned-ATE gains;
mean fractional aligned-ATE gain>=5%; each window ATE and translation RMSE
regression<=5%; each mean rotation regression<=.02deg; ratio of mean holdout RMS
P/O<=1.01. Preserve all records and outcomes. No best subset or revised gates.
An eligible result admits a concrete GT-blind accepted-loop revisit design,
not production promotion or a whole-system gain claim. A failed result stops
this exact one-split local candidate; a distinct cross-visit hypothesis can
still be reviewed honestly without calling this pilot successful.

## Resources and scope

New combined measured-stage CPU wall ceiling1800s, peak RSS2GiB, dossier512MiB.
Imports/WSL startup, design/docs and source bookkeeping outside stage timers
are disclosed; not production latency. No GPU/model load/training/RAP inference,
acquisition/install, production/default/backbone/manuscript edits, commit/sync.
Both repository HEADs/branches and existing dirty work preserved. Old SMP1/MMR0
sources, banks, seals and decisions remain immutable. Official GT/metrics,
09 discrepancy and checkpoint/site/exposure unknowns remain.

Prior art: [BALM](https://arxiv.org/abs/2209.08854). No original mechanism claim.
