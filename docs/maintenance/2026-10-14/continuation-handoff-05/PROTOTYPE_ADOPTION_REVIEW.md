# Prototype Adoption Review

Late read-only supplement after the22-entry handoff seal. No new execution or
frozen source edit. The prototypes are not ready for general pipeline adoption.
These risks do not invalidate the fixed tiny-case outcomes within their stated
assumptions, and do not authorize another automatic control campaign.

## Adoption Blockers

1. Native WPC0 telemetry is not complete. The empty catches at
   scripts/maintenance/windows_pipe_capture_control.ps1:76 and:95 omit query
   failure/freshness records. Its original resource gate remains INCOMPLETE.
   NMQ0 records new direct OS final peaks, but its observer self-query is only
   to-snapshot. Do not reuse either as proof of whole-process-tree/whole-system
   memory completeness or backfill any original resource gap.

2. Linux descendant-held pipes are unsupported. In
   scripts/maintenance/bounded_pipe_capture.py:27 the loop continues until
   native exit AND pipe EOF, but at:31 termination is conditional on native
   still being unknown. An untested descendant retaining a pipe after the
   immediate child is reaped could therefore keep that loop waiting. Current
   frozen fixtures spawn no descendants; arbitrary process-tree supervision
   must not be inferred from the8 passes. A future adapter needs an explicit
   drain/tree deadline and owned-tree cleanup contract, not an implicit claim.

3. A valid journal is not sufficient evidence admission. Journal.close at
   scripts/maintenance/bounded_evidence_journal.py:75 records container state,
   not native launch/exit, required scientific payload, expected namespace or
   intended producer output. An unexpected launch/metadata failure can leave
   no terminal exit record even when a container footer exists. BPC0/WPC0
   tests correctly require separate native/namespace checks; empty success
   is a valid empty fixture, not a complete scientific bank.

4. Exclusive file creation is not exclusive directory ownership. BEJ0's
   external-file negative demonstrates this. Its digest detects changed bytes
   against the bound evidence; it does not authenticate an arbitrary author's
   forged journal or enforce external-writer quotas. A future integration
   needs a declared cooperating namespace/all-output routes and reconciliation;
   malicious/noncooperating writers need a different OS-level boundary.

5. Footer reservation is not crash durability. Body/footer I/O exceptions,
   loss before terminal metadata, power failure and restart recovery have not
   been implemented as production lifecycle cases. Do not equate SHA, close,
   a retained partial prefix or one exclusive writer with durable completion.
   An incomplete record/bad footer stays unsealed; never delete old evidence
   or relax an old cap to make it appear successful.

## Required Use Discipline

Keep all frozen source/failures/markers and use the controls only for their
exact functions. No source/threshold edits are made by this review. Any future
implementation must be separately scoped against a justified task and include
its exact failure/ownership/process-tree/resource/complete-output contract.
Do not spend more effort expanding prototypes just because the account resets.

The current research priority remains a distinct observable and source/strong-
control design. These infrastructure issues do not establish a scientific
failure cause, physical truth or a RAP contribution. No LCP0/HFIT0 retry,
real-model integration, production/default/reference/manuscript/Git change.
