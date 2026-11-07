# BPC0 Synthetic Pipe Lifecycle Control

Each new per-case directory permits exactly evidence.rdj (cap2048bytes) and
exit.json (maximum1024bytes reserved before launch): cooperating-file envelope
3072bytes. Four BEJ0 channel payload limits are256/128/128/256 bytes. Original
BEJ0 includes all framing/footer overhead in its own cap. Terminal native exit
metadata is serialized/length-checked before exclusive writing. No other case
output is permitted. A directory writable by external actors is not OS-quota
safe; this envelope applies only to the controller's fixed cooperating paths.

Launch a fixed frozen synthetic child in its own session with stdout/stderr
pipes, no file redirection. One parent selector serializes64-byte pipe reads
into the journal, keeping channels separate and binary-safe. On overflow, mark
failure, terminate only the owned child session, drain/discard remaining pipe
bytes, reap via wait4 exactly once and record observed discarded byte counts.
No silent truncated-success claim. Nonzero exit and timeout also deny admission.
The normal deadline is3s, timeout-case deadline0.25s, SIGTERM then conditional
SIGKILL after0.25s. Native child peak RSS must be <=64MiB. The current outer
Windows supervisor is not replaced or claimed bounded by this prototype.

Eight prospective modes: normal stdout+stderr; stdout overflow; stderr overflow;
both-stream flood; exit7; sleep timeout; empty success; invalid UTF8/NUL bytes.
All children use only the frozen script and spawn no descendants. Complete
native exit/resources/pipe EOF/terminal metadata required for every case.
Failure cases are expected controls, not supervised-stage failure. Exact bytes
required for the three nonempty/empty success modes; byte order across separate
streams is not asserted. Flood termination may prevent some intended writes:
record observed bytes only, never claim full intended-output completeness.

Independent validation uses the previously frozen independent BEJ0 decoder,
separately reconstructs per-channel bytes, expected child exits, all1024-byte
terminal limits and full per-case namespace. It imports no writer/controller
construction. All8 cases/children must be present, clean cases admitted, failed
cases unadmitted, no complete journal treated as enough without native exit.
No arbitrary process tree, concurrent writers, crash durability or whole-dossier
guarantee. No old LCP0/HFIT0 archive/fit follows automatically.
