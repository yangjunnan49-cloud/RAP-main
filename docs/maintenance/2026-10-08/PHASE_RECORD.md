# Phase record: 2026-10-08

## Owner-requested context recovery and RLP1 scope review

Read AGENTS.md, the previous chat 规划RAP下一步提升方向, latest DS0/TR0
reports/protocols/handoffs/status and relevant source/split/seal records.
The last chat completed DS0 and left its explicit fitting question unanswered.
The present request authorizes review, not experimental execution.

Read-only checks: DS0 15 delivery entries and 16 source entries match;
TR0 20 bank files and freeze/bank/validation hashes match. Draft 204 windows
independently reconstruct counts 144/12/48 and 612 distinct frame paths.
Disclose six preflight-shared frame paths in draft 00/t199,06/t201,07/t201.
Saved KISS07/09/10 six source/odom hashes match, with endpoint coverage for
36 evaluation windows. Read odometry lines for counts only, no numeric motion.
M0 archive manifest matches; archived payload not rehashed.

Found a concrete prospective design defect: DS0's annex says little-endian,
but the sealed LMF1/TR0 seed source and all four TR0 integer seeds use big-endian.
Created readout-pilot-review-01/REPORT.md,REVIEWED_SCOPE.md,CHECKS.json,STATUS.json.
Preserved DS0's original annex/seal. Supplement corrects byte order, clarifies
432 required valid primary predictions and proposes G3/KISS per-sequence mean
regression caps 0.005m/0.02deg. Owner review remains pending; no gates executed.
J/I active head capacity matches; D effective capacity differs; I OOD and
weak GT/historical exposure/site/checkpoint unknowns remain disclosed.
Local adjacent-frame readout is not a hard-loop or system-gain result.

Read-only sibling-source/Git access initially denied by sandbox, then received
approval and succeeded. Both original HEADs/branches and dirty work preserved:
main4055d929/codex/meeting-20260930,SLAM6d3f2d22/codex/e0-f1-20260926.
Only review/handoff documents changed. No cloud/GT/checkpoint tensor loading,
labels, model/GPU/inference, fitting, graph/trajectory, defaults/production/
manuscript changes, acquisition/install, commit or Git sync. All older stops,
banks, official GT/metrics,09 discrepancy and breakthrough requirement persist.

Next: obtain the owner's explicit scope choice after presenting the reviewed
goals, prerequisites, fixed budget and expected deliverables. A subsequent
approval permits fresh implementation and prospective freezes within that
scope; this review itself is complete.

## Owner-approved RLP1 execution and mandatory prerequisite stop

Owner replied "批准完整实验！". Implemented new isolated RAP-SLAM
scripts/measured_point_readout.py and RAP-main stage orchestration/independent
validators. Frozen protocol includes reviewed big-endian seeds, fixed204
manifest,432 valid primary predictions and additional G3/KISS sequence safety.
No installed/downloaded dependencies or production/backbone edits.

Original engineering freeze precedes first eligible output; exact pose replay
failed because writer used solve while native TR0 used inverse/multiply.
Amendment01 preserves originals and freezes attempt02. It then fails copying
float scale metadata; reused failure filename produces secondary collision,
without overwriting original failure. Amendment02 preserves sources/partial
00J and separately freezes attempt03 with scalar-safe copies/distinct logging.
All4windows rerun with original scientific settings. No label/error/outcome
changes guided either implementation correction.

Attempt03 engineering16 NPZ bank seals and independently validates four00/05/
06/07t200 rows. Native J exact; I full-flow grouping/repeat/third-noise independence
exact, native1/3unused CUDA vector draws and outer RNG restoration preserved.
Independent12 scans/12000 points/384000 descriptors/noise and Horn pose delta
5.462e-14 pass. No raw/state/tokens/parameters/modes/default change.

Separately frozen weak-label preflight generates11synthetic files and real00/
05/06.00/05 counts pass;06 directions01/02/10/12/20/21 positive counts
23/15/20/23/15/31. All-pair floor20 fails02/20 (199/198 adjacent scans), so
writer stops before07,complete-bank seal,full204 bank/labels,fitting/predictions/
error evaluation. Head synthetic backward checks precede real labels, but their
final JSON is absent; no independent claim from that absent record. Preserve
all14partial NPZs and weak-stage INCOMPLETE. No scientific repair or rescue.

Separate prospective stop-audit freezes those14files/source/GT and independently
reconstructs masks,third-view support,counts,calibration and transforms. Maximum
delta2.274e-13; Horn rigid/planar4.163e-16,rank1 rejected,proper-rotation fixtures
and selected finite-difference soft gradients4.603e-11 pass. Decision VALIDATED
PREREQUISITE_STOP_INSUFFICIENT_WEAK_LABEL_COVERAGE. Its valid seal supports the
stop only, not complete weak-stage validation or any learnability/accuracy gain.

11recorded process stages115.329s include failed attempts/freezes/validators;
peakGPU1.387GiB,RSS2.689GiB,about198MiB before final documents. RESOURCE_AUDIT
records enclosing interval and sampling/startup boundary caveats; all caps pass.
Original204count-only manifest and source seeds unchanged. DS016 source entries
and TR020bankfiles rehash unchanged; both original HEADs/branches/dirty work
preserved. No fitting/full bank/trajectory/default/production/backbone/manuscript
edit,acquisition/install,commit/Git synchronization. New REPORT/HANDOFF/STATUS/
NEXT_ROUND_PLAN and AGENTS boundary preserve all older negative stops/official
GT/metrics,09 discrepancy,checkpoint/site unknowns and breakthrough requirement.

The authorized fixed pilot is closed at its mandatory prerequisite. Do not
relax the floor,replace06/change geometry/density/noise or fit successful-only
windows. Any distinct next supervision/task design remains unselected; obtain
an explicit request/scope before new experimental outputs.

## Owner-requested interpretation and distinct motion-supervision plan

Owner asked for thoughts on the result and next planning. Read RLP1's protocol,
stop audit/engineering validation, source helper and DS0/earlier measurement
design. Read primary DCP/RPM-Net/GeoTransformer documentation and authors' code;
DCP's official implementation explicitly trains rotation/translation losses.
KITTI's official short-segment GT caveat persists. Some publisher PDF fetches
failed; official paper landing pages and authors' code supplied the evidence.
No external source/checkpoint acquisition or installation.

Created readout-task-redesign-01 REPORT/PLAN/HANDOFF/STATUS/SOURCE_AUDIT/seal.
The15/20 row count is a failed prospective supervision prerequisite, not proof
of pose degeneracy or lack of useful token information. Sparse partner plus
third-view support can reduce labels, but no cause decomposition was run.
Selected a recommendation for a distinct pose-supervised soft readout: no row
classes/overlap/dustbin, common projector75072nominal/D13632effective, same
continuous original-point proper weighted solve for train/inference, R/t loss
from update1. Preserve original204manifest/roles/inputseeds,three fixed seeds,
nine1000-stepfits,432primary predictions and useful local conjunctions. Add
fixed token-row permutation and no-motion diagnostics; no selectable rescue.
New numerical checks precede actual bank/fitting/evaluation in one future scope;
useful local pass alone permits only a separately reviewed system intervention.

This is READ_ONLY_DESIGN_COMPLETE. New numerical preflight, labels, feature banks,
inference, optimizer and trajectories remain unimplemented/unexecuted. Former
full approval ended with RLP1; current user request is planning, no new experiment
scope. No old scientific bank/source/seal/gate/default/backbone/manuscript change,
Git commit/synchronization or data installation. All old stops, official GT/
metrics,09 discrepancy,unknown training/site roles and original breakthrough
requirement remain. Generic soft matching/SVD/pose supervision is established
prior art; success would first show representation value, not automatic novelty.

## Authorized RLP2 execution: prerequisites passed, fitting stage next

Owner said "执行你的建议" then "请继续". New isolated motion-supervised readout,
orchestration and independent validators implemented. Before any eligible output,
execution protocol fixes float32embedding/operator/raw-W-hash encoding because
retaining full W matrices alongside feature banks would exceed4GiB. Independent
validators must regenerate complete W byte-exactly; no precision/density change.
Original204manifest/noise,three seeds/nine1000steps and scientific conjunctions
remain fixed. Small readout fitting authorized; original backbones/defaults frozen.

Numerical stage froze before6synthetic rigid/planar/partial-unequal/duplicate/
rank1/uniform cases,one selected-gradient fixture and18 initial00/05D/I/J checks.
Independent Horn max1.510e-14,FD selected gradient3.823e-10,all weight hashes exact;
stage VALIDATED,no optimizer updates/native new inference. Existing RLP1 context
invariance/source/seals reused unchanged after rechecks.

Complete204 GT-free bank separately froze and generated J/I/native hook/state/
row/noise bindings,48same-pointG3 and36KISS references. Independent full source
validator reconstructs612scans/612000points/19584000descriptor values/noise exactly,
native group/time/RNG and Horn/geometry controls(max1.099e-13). VALIDATED before
new full pose targets or any optimizer updates. Full bank about2.81GiB; caps pass.
All compute,freezes,failed outputs/validation are recorded,not deployment timings.

Next authorized stages: separately freeze/validate all204 pose targets,then all
nine fixed fits with independent complete replay,complete sealed predictions,
fixed diagnostics and independent error/gate validation. No trajectory is included
without a useful local conjunction and separate system protocol. All earlier
failed banks/stops/officialGT/metrics,09 discrepancy and checkpoint/site unknowns
persist; no acquisition/install/commit/Git synchronization.

## RLP2 owner-approved time amendment before GT model-error scoring

All nine fixed fits and9000 independent replay updates VALIDATED;432 primary
predictions sealed and432valid. Per-file resource audit costs made original
combined3600s budget insufficient for all remaining validation/diagnostics.
Before any GT model-error outcome was read, owner explicitly approved at most
45additional process minutes (combined6300s). Scope is existing heads only;
no optimizer/backbone inference/scientific setting/gate change. GPU3GiB,RSS4GiB,
artifacts4GiB unchanged. A separate hash-bound resource-amendment launcher is
prepared. Old immutable controller runs to completion/its existing cap stop;
all partial/failure compute/snapshots will count. Original60min will not be
claimed passed if exceeded. Full prediction/diagnostic/error validation and
final closure remain pending; no trajectory is authorized.

## Complete RLP2 fixed motion-supervised readout: VALIDATED_NEGATIVE

Decision NO_COUPLED_JOINT_READOUT_SIGNAL.204feature/target windows,144fit00-05,
12unuseddevelopment06,48exposed07-10. Nine1000-update fits+9000independent replay
updates pass;initial/final/optimizer exact. All432primary+144fixed permutation
poses valid,all full weight hashes exact;708GT/error/gate records independently
reproduce(max2.195e-13).15scientific stages seal and final1994unique-file identity
audit passes;oldRLP1 62/redesign5/DS013sealed study files and originalTR0 unchanged.

48window t(m)/R(deg) medians:D.951464/.606511,I1.392460/.698359,J.888431/.552965.
JvsI conjunction passes;JvsD rotation paired gain.007573<.01,signs26/48<60%,
cohort90%ratios and07/09rotation safety fail. G3.097115/.238968;KISS36.022371/
.049555 (J36.888431/.593314);both usefulness/safety conjunctions fail. Identity
.854124/.250591;permutedJ1.709437/11.652314 shows input binding matters,without
proving useful motion/physical identity/confidence. Stop this fixed construction;
no tuning/seed/loss/density/cohort/decoder rescue or trajectory stage.

Original3600s controller resource stop during primary validation preserved with
complete432bank/source/freeze/failure/log/status/marker snapshots. Owner explicitly
approved at most45additional process minutes BEFORE any new GT model-error readout;
combined6300s budget-only launcher separately froze,all partial compute counts,
full validation replays. Original60min NOT passed;amended caps pass,exact totals
in final RESOURCE_AUDIT (6107.588s before final delivery preparation/hashing).
No numerical implementation repair/new optimizer/backbone inference after approval.
These audited process costs include file/resource checks,not deployment latency.

Both originalHEADs/branches and2/9tracked dirty counts preserved;RAP/miniSpin/defaults
and officialGT/old metrics untouched. No acquisition/install,production/manuscript
edit,commit/Git sync. All prior stops/seals,09discrepancy,unknown checkpoint/site/
exposure and original breakthrough remain. No independent generalization/originality
claim. The immediate authorized pilot is complete;no new arm/system protocol selected.
