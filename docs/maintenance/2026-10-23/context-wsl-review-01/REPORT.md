# Context review and WSL migration verification — 2026-10-23

The owner requested context recovery, project and experiment status, proposed next actions, and verification of the completed WSL migration. This review is complete. The October 22 closeout still governs research status: original objective UNRESOLVED, manuscript PAUSED, no pending experiment and no automatic quota-reset continuation. No model, registration, training, solver or GT evaluation was run in this review.

## Evidence and project status

Reviewed the current AGENTS entries and standing boundaries, October 22 authoritative closeout, October 21 current-state audit, S1 raw-core report, P0 negative qualification decision, N2 diagnostic report, CN1 report, and the existing static observation/source-binding plan. File identities are recorded in CONTEXT_CHECKS.json. The five source pointers used by that plan all still match their sealed SHA256 and byte sizes. Six selected migration records match the authoritative C-drive records and repository snapshots. The prior 1,005-entry audit and 275-entry documentary closeout checks were not repeated today.

The research direction is reliable loops in low-overlap/repetitive scenes with a demonstrable additional RAP mechanism. A working infrastructure or coordinate contract does not establish that contribution. The earlier HL-V2 confirmation H1 PASS / H2 FAIL and STOP_NEURAL_EXPANSION remain historical constraints; this review does not revive that family.

| Scope | Completed evidence | Remaining limitation / closed result |
|---|---|---|
| S1 fresh raw trajectory core | 36 cells, six sequences, three repeats; 73,776 frame calls. Mean G/K ATE 0.648334140963 / 0.698991712360 m; mean ter 0.446953334008 / 0.478490321918%. | Average objective passes, but 07ter and 10rer protection fails; G ATE is worse on 06/07/10. No new RAP efficacy or stable online 10 Hz claim. Original R0+S1 cost 6762.0941485/7200 s is unchanged. |
| P0 queue4 | All 72 trajectories independently validated and exported; 147,552 frame occurrences and 88,776 independent KITTI segments. G/K observed time reductions 12.64694% / 18.61503%. | CLOSED_EQUIVALENCE_FAIL: G r1_06 and K r1_00/r2_09 fail. G maximum translation-matrix element discrepancy is about 4.31 mm against the original 1 mm gate. Original capture cost 9316.8147729/9000 s remains a budget FAIL. No promotion or rescue. |
| N1 | Frontend complete; partial native prefix recorded. | INCOMPLETE_ARRAY_CAPTURE_CAP at the original 16 MiB single-array limit. No second full native control; no retrospective PASS. |
| N2 | Two complete serial G06 coarse controls, 2,202 frames, 24,830 events. First visible difference at ICP return, frame 564/event 6340 after 6,340 equal recorded events. | Final translation-matrix element difference about 2.71 micrometers. Hidden cause UNKNOWN; does not explain historical 4.31 mm or certify determinism. Coarse diagnostic only; no RAP/fine graph/GT. |
| C0 custom interface | Already complete on October 17, all four stages and 56,557 points; original 22.614594/900 s. | Interface-only evidence, no canonical batch, physical truth or efficacy authentication. Do not repeat completed stages or reuse unused budget as a payload allowance. |
| CN1 | 17 synthetic controls; 9,882 independent Decimal recovery coordinates plus 1,647 normalization roundtrips. | Conditional custom algebra only. It does not authenticate actual RAP output direction, canonical preprocessing, N-way runtime or registration quality. |
| Watcher/recorder | Nine synthetic integration controls and 120 stub assertions passed in the existing scope. | No general OS containment, hidden-state coverage or real-workload nonintervention guarantee. |

The latest closeout also preserves the additive account-boundary correction: October 21 at 22:14:09 Asia/Shanghai observed 100% and ordinary usage disabled. The one-second reset-ID change does not establish a cause or rollover. No account/goal/scheduler state was changed or resumed here.

## Fresh WSL verification

LIVE_CHECKS.json records successful checks from **2026-10-23 09:24:15 to 09:25:02 Asia/Shanghai**. Commands and raw outputs are preserved beside it in separate receipts. The environment probe is the previously reviewed migration metadata script; its SHA256 is captured in LIVE_CHECKS.json. It reads interpreter/package metadata and selected files without importing the numerical packages being inventoried.

| Check | Fresh observation |
|---|---|
| Registration | Ubuntu-24.04, WSL2, BasePath `E:\WSL\Ubuntu-24.04`, DefaultUid 1000, VhdFileName `ext4.vhdx`. |
| Active image | `E:\WSL\Ubuntu-24.04\ext4.vhdx`, 44,881,149,952 bytes (41.798828125 GiB). |
| Legacy path | C AppData distro directory is an NTFS Junction targeting `E:\WSL\Ubuntu-24.04`. Active and legacy VHD paths both resolve to file ID `0x0000000000000000000400000002b546`. The C path does not identify a second physical VHD. |
| Boot/default identity | Fresh minimal startup succeeds. Default user `aaa`, UID 1000, home `/home/aaa`; root filesystem `/dev/sdd`, ext4. The device name is only this boot's observation. |
| Four Python environments | Interpreter paths, resolved executable hashes, Python versions and selected package metadata exactly match the October 22 post-migration snapshot. |
| Selected files | All six selected Linux configuration/project file records, including hashes/size/mode/ownership, match the migration snapshot. Home-directory listing matches. |
| GPU visibility | WSL nvidia-smi reports NVIDIA GeForce RTX 5070, driver 610.62, 12,227 MiB. No CUDA computation or model allocation was requested. |
| Windows configuration | `.wslconfig` SHA256 unchanged from the migration snapshot. |
| Retained backup | `E:\WSL-Backup\Ubuntu-24.04-before-move-20261022.vhdx`, 44,881,149,952 bytes. Full SHA256 recomputed in about 36.11 s and matches `D911FD7AF4B748FF4B3E52422494BA4EF0DD99BADCE36028A2328FB0BF1878C5`. |
| Final runtime state | Initially Stopped; restored to Stopped after only this review's finite probes. No global WSL shutdown/service/registry/Junction modification. |
| Free space | C about 51.21 GiB; E about 501.45 GiB at the recorded observation. Free space varies with unrelated activity. |

**Conclusion: storage migration is complete and startup works with the retained compatibility Junction.** The check did not remove the link, reboot Windows, or certify direct startup without the legacy path. The precise stale-reference cause remains unresolved. Keep the backup through normal-use validation and retain the Junction until a separately controlled direct-path check succeeds; never delete contents through the old path.

The active VHD was not compared against the pre-first-boot digest: ordinary boot writes can change it. Migration-time preboot byte identity is established by the retained October 22 MOVED_IMAGE_CHECKS.json. Today's full digest comparison is for the offline backup. Native Python extension imports and PyTorch CUDA visibility passed in the original migration acceptance; today repeated metadata checks and nvidia-smi visibility, without repeating those imports.

## Proposed next action, not started

1. **Produce one source-bound interface map before any inference.** Follow the five still-matching files listed in the existing SOURCE_POINTERS.json: `rap_backend.py`, `demo.py`, `dataset.py`, `procrustes.py`, and `sample.py`. Bind actual public reader paths, custom/N-way batch construction, part IDs, primary/anchor selection, features, shared scale and offsets, precision, fit source/target direction, row/column convention, translation units and returned transform/reference gauge to source lines and hashes. Explicitly distinguish internally constructed `pointclouds_gt` from an independently authenticated external reference. Deliver a data-flow/equation table and a list of genuinely unresolved interfaces.
2. **Only if that map identifies an unmet interface requirement, define a separate finite synthetic source-interface control.** It should exercise actual called coordinate-bookkeeping routines with known synthetic transforms, at least three views, multiple gauges/references, and invalid-input controls. Compare to an independent scalar oracle and prohibit fitting/projecting invalid predictions merely to pass. Existing two-part recovery is algebraically consistent under its assumptions; do not rebuild an allegedly missing generic layer. CN1's different custom normalization cannot certify canonical RAP behavior.
3. **Only after a complete interface decision, consider a separately scoped real-model protocol.** It would need explicit source/resource/stop bounds, externally separated references, matched non-RAP controls and exposed-scene limitations. This review admits no new inference, feature extraction, real fit, training, data acquisition or numerical payload. Preserve P0 closure, N1 incompleteness, retired-family stops and all historical budgets. The next work should answer an unresolved source question, not repeat completed C0 or seek a favorable N2 sample.

The existing plan remains authoritative for the proposed next scope: `docs/maintenance/2026-10-21/evening-handoff-01/snapshot/NEXT_SOURCE_BINDING_PLAN.md`.

## Repository state and execution notes

Local HEADs remain RAP-main `4055d929c594b0033aafc6eed339c910369eef55` and RAP-SLAM `6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6`. Both contain pre-existing uncommitted maintenance changes (see GIT_STATE.json); no fetch/pull/push/commit/reset/clean or global configuration change was performed. Remote synchronization was not checked.

The first sandboxed registry/WSL and RAP-SLAM Git reads were denied by sandbox access restrictions. The necessary read checks succeeded outside that sandbox; this was not a WSL migration failure. One ad hoc PowerShell hash-loop command failed to parse before execution because a foreach statement was directly piped; collecting its results into an array fixed the read command, and all five comparisons passed. No existing evidence or settings were altered by these failures.

Only today's documentary records, a finite verification helper, the dated phase record and an additive AGENTS entry were added. Original AGENTS bytes are preserved in before_update with a SHA256 receipt. Older experiment reports, failures, seals and budgets remain unchanged. This review creates no automation, account-quota continuation, experiment admission or goal-status change.
