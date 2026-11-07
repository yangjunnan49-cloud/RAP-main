# Phase record: M0 local preservation and M1 handoff consolidation

Date: 2026-09-09. Owner request: execute maintenance in phases and keep AGENTS.md
as an objective, sufficient handoff between conversations and agents.

## Executed changes

1. Created exclusive snapshot `.maintenance-archive/2026-09-09-m0` in RAP-main.
   Preserved 1,568 files / 4,632,636,436 bytes: all existing RAP-SLAM output products,
   root logs, weights, report materials, tracked code, original audit and selected
   dataset metadata. Every copied file was SHA256 checked; source inventory and
   hashes were checked again before completion. Read an archived POSS edge JSON
   and verified its four measurements. No original output was overwritten.
2. Added `/.maintenance-archive/` to `.gitignore` so large copies cannot accidentally
   enter code history. The archive is a same-volume preservation copy, not independent
   disaster recovery. The snapshot captured the already-updated `.gitignore`; its
   metadata records that worktree state rather than claiming a pristine checkout.
3. Preserved the entire original AGENTS.md byte-for-byte in `../history/` and in the
   snapshot. Replaced the active file with a current maintenance entry point:
   repository boundaries, evidence, unresolved findings, runtime and exact next task.
   Superseded automatic S2 research continuation, stale startup checklists and
   blanket TF32 guidance. No historical experimental record was deleted.
4. Copied the seven original audit files into `../audit-2026-09-09/`, so the handoff
   no longer depends on a previous chat's C: artifact directory. Preserved their
   original content/language; the maintenance index explains temporal scope and
   historical AGENTS.md line references.
5. Built `experiment_registry.json` from archived evidence: seven detailed saved-PGO
   references, 38 recorded configurations, 40 output-directory groups and three
   checkpoint hashes. Unpersisted historical code/weight/environment/frame bindings
   remain unknown. Directory groups are not falsely counted as independent runs.
6. Captured installed environment identities without credentials or environment
   variables: 184 conda-Python distributions, 205 conda package records, 147 system
   Python distributions, ROS Debian versions and GPU/driver. This is an observed
   inventory, not a tested clean-install lockfile.
7. Added three maintenance helpers under `scripts/maintenance/`: preservation,
   environment capture and registry generation. They do not change RAP or SLAM
   inference. The preservation command refuses to reuse a snapshot directory.

## Acceptance evidence

- Snapshot summary and manifest are versioned next to this record. Manifest SHA256:
  `d9f23fdde6871e4b765d0f76c765035091afdc48e6655d11bf6001fffa41d497`.
- `INCOMPLETE` was removed only after copy/hash/source-stability checks and archived
  JSON read-back succeeded. Large data was actually copied, not just enumerated.
- The seven PGO numbers in AGENTS.md are carried from the prior audit, not claimed
  as newly rerun in M0/M1. No GPU/ROS research run was needed for these document and
  preservation changes.
- Final consistency checks are recorded in `phase_validation.json`: historical
  handoff and audit byte identity, manifest identity, registry/evidence consistency,
  active document links, helper syntax and unchanged source boundaries.

## Status and remaining work

**M0 local scope complete; M1 current-entry consolidation complete.** Open M0 items:
independent-device/remote backup, raw data backup policy and historical provenance
recovery. They do not prevent bounded local correctness maintenance, because original
products now have a hash-verified copy outside the verification cleanup paths.

No algorithm fix, protocol recomputation or S1 rebuild has been performed in this
phase. F01–F19 remain open. Existing thesis/report prose is archived, not silently
rewritten; full paper consistency is M5. The new handoff suspends unsupported claims.

RAP-SLAM remains at `6d3f2d2` with a clean worktree. RAP-main maintenance files are
prepared as one local commit; use `git log -3 --oneline` and `git status --short` to
inspect actual current state. No maintenance push has been performed. Do not infer
remote synchronization from the original audit's remote check.

## Exact next action: M2/F02

1. Read F02 in the audit and trace rigid fitting in `rap_slam/rap_backend.py` plus
   RAP `procrustes.py`, `modeling.py` and sampler rigidity forcing. Identify all
   relevant matrix products; do not assume final-fit-only control fixes the entire path.
2. Implement precision control at the RAP-SLAM boundary if feasible, preserving
   upstream source. Restore any global settings after use and consider concurrency.
   If a narrowly scoped upstream fix is necessary, explain and record the boundary.
3. Validate exact known rigid transforms on the GPU with TF32 on/off, rotation
   orthogonality and determinant, and a few real saved frame pairs using new run IDs.
   Keep any legacy-compatibility arm explicit. Do not project and overwrite old edges.
4. Record impact, validation and next step in AGENTS.md and a new phase record before
   moving to F03 official metric/frame correspondence work.

Do not resume S2 research, rerun destructive verify scripts, overwrite golden
directories or treat a pending repair as completed.
