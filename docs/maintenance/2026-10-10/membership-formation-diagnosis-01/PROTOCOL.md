# MF0: membership-formation diagnostic

Owner 2026-10-10: "启动新实验" after the existing-experiment review and its recommendation. This authorizes this distinct bounded observation-model diagnostic. CV2 and all older decisions remain unchanged. Exposed development and deliberately oracle reference inputs are explicit. This is not an accuracy method or training/full-trajectory authorization.

## Fixed inputs and formation rules

Reuse the sealed CV2 00/05/06 first-accepted cases 2429->3373,538->1302,150->978, all 48 scans and 288000 retained points in their original bank order. No sampling, raw preprocessing, calibration/time, thresholds, scale, hash, cohort or optimizer changes. Rehash CV2 freeze/bank/delivery and exact raw/calibration/reference identities before payload. Reuse the already independently checked raw-to-retained conversion; independent census reconstruction here starts from every sealed retained point.

B/F/T poses are byte-copied from those banks. G is the same full-reference diagnostic as CV2: inv(Tr)*camera*Tr, relative to A endpoint, SVD proper rotations, exact identity anchor. It is an oracle diagnostic input, never a new deployable candidate, inferred physical truth or selector. Freeze reference-file identities and operators before new results.

For each B/G formation source independently, use complete 2m world voxels sorted lexicographically. Per-scan contributions require >=6 points; retained counts then require >=3 scans and >=40 points. Equal mass per contributing scan defines the pooled plane covariance. Eligibility uses lambda0/max(sum(lambda),1e-15)<.025,lambda1>.005,lambda0<=.015 and max active-scan mean normal offset<=.20m. Only eligible patches with both visits contributing enter the final cross-visit sets. Reproduce every B label, key, moment and split from CV2 before interpreting G.

Record ALL candidate voxel keys, raw and effective per-scan counts, eigenvalues/offsets for support-passing candidates, plane-test failure bits, final sequential reason (cross accepted/support/plane/single visit), each point's candidate ID, final label and rejection reason. Low-count scan points inside accepted voxels receive their separate inactive-scan reason. No candidate or rejected point is silently omitted.

Same SHA256 UTF-8 CV1|seq|i|j|2|kx,ky,kz, first four bytes unsigned big-endian modulo4=0 holdout. Report train/holdout support and each scan's coverage. Train >=10 patches,>=3 scans and>=100 points per visit; holdout>=5. Unsupported cases stay visible; nonempty-set costs may be reported diagnostically, but no supported-cohort claim follows. Never replace a case.

Point identity is (sequence, source frame, retained row ordinal), bound to its raw file hash and preprocessing bank. It is not a physical landmark ID or an invented original raw-return index. Persist every row ordinal and source binding.

## Frozen comparisons, not optimization

Seal both membership banks and independently validate their entire accepted/rejected census before evaluating costs. Under each FIXED membership, report B/G/F/T train/holdout/full cost and RMS, analytical plane nuisance refits only. Cost=.5*mean(max(lambda0,0))/.10^2, equal patch mass and scan-balanced covariance. No new pose errors or optimizer calls; no priors, further F/T/J steps, pose selection, learned output or trajectory.

At B, evaluate the training translation gradient in the saved B endpoint body frame and its unit direction towards G endpoint translation, shifting all second-visit scans together. Validate against explicit point finite differences, epsilon1e-5m. A negative local slope does not predict a distant endpoint's cost.

Coverage includes B/G intersection/exclusive/union per scan and visit, point Jaccard, and the full sparse patch overlap matrix with shared-row counts. Split/merge relations mean degree>1 in this row-overlap bipartite graph; voxel-key identity alone is never physical surface identity.

The separately declared intersection diagnostic restricts each source's ORIGINAL labels to rows accepted by both sources. Retain all nonempty original patches, including weak/single-scan ones, renormalize over remaining contributing scans, omit only empty patches, and report kept original IDs and scan counts. Do not reapply eligibility or replace the main train sets. Evaluate B/G costs within each such grouping. Those restrictions alter support and weights; their cross-source means are not controlled model comparisons.

Within each fixed grouping, define preference by Delta=cost(G)-cost(B): >1e-10 prefers B, <-1e-10 prefers G, otherwise numerical tie. This is a numerical reporting rule, not an efficacy gate. Show coverage continuously; there is no post-hoc "large difference" threshold. Summarize supported cases as opposing preferences (B-formed prefers B,G-formed prefers G), persistent B preference, other/mixed, or insufficient support. No cohort accuracy PASS is defined.

## Interpretation and stop

Opposing preferences support formation-dependent objective preference, not the correctness of either grouping or a unique explanation of 05. Persistent conflict requires verified physical-surface/timing/calibration/trajectory evidence before further investment in this objective; without available independent evidence, stop this shared-plane objective. Mixed or unsupported outcomes remain inconclusive. An oracle G grouping cannot be deployed. Existing negative gates are neither relaxed nor reclassified. No residual-based acceptance rule or GT B/F/T selector follows.

## Validation, resources and preservation

Freeze this protocol, owner scope, helper, runner, validator, package versions, old scientific dependencies and source snapshots before synthetic preflight or any new membership/reference evaluation. Synthetic census/rejection/hash/gradient/gauge fixtures run zero optimizers. A separate validator independently reconstructs all candidate groups with a dictionary keyed by explicit world voxel coordinates and centered point covariance, rather than compact moments; check all candidate/row decisions, accepted moments, coverage and split/merge data. Independently evaluate every saved cost and selected direction FD. Shared declared conventions are disclosed; physical association is not independently verified.

Combined measured CPU stages <=1800s, observed peak RSS<=2GiB, new dossier<=512MiB, including freeze, failed/retry processes and independent validation. Timers start after imports; WSL startup, design/docs and final delivery bookkeeping excluded. Use an alarm for remaining stage budget, capture resource/failure in finally, preserve failed source/freeze/output and INCOMPLETE. Any repair requires a separately frozen attempt; no overwritten scientific source. No old budget amendment or production latency claim.

Both original repositories/branches/dirty sets, model/config/checkpoint byte identities, old seals/stops and official GT/metrics remain. Only a new isolated RAP-SLAM membership helper, main maintenance runner/validator, new dossier and mutable handoffs are allowed. No model/checkpoint loading, learning, RAP inference, GPU, acquisition/install, production/default/backbone/manuscript edit, commit or Git sync. All checkpoint/site/09/physical provenance unknowns persist; conventional geometry and owner's originality relaxation remain explicit.
