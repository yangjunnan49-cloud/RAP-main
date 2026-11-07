# WPC0 Windows Binary Pipe And Exit Counterpart

Freeze all source and exact existing PowerShell executable identity first.
No runtime install or current supervisor edit. The enclosing Linux driver
launches this fixed native PowerShell controller through WSL interop; records
its returned exit separately. The controller records its native PID, elapsed,
CPU seconds and peak working set. Each of8 fixed children records the same
plus its actual native exit code. Full parent/child records required.

Reimplement the frozen BEJ0 format using .NET exclusive FileStream/BinaryWriter,
incremental SHA256 and fixed little-endian framing. The single controller
serializes completed binary64-byte ReadAsync chunks from both pipes; it does
not use text-line decoding. Same2048-byte journal+1024-byte exit record envelope
and per-channel256/128/128/256 payload caps as BPC0. Native exit/terminal metadata
must fit before exclusive writing. Case namespace contains exactly two files.

Same8 modes: normal, stdout overflow, stderr overflow, both flood, exit7,
timeout, empty, invalidUTF8+NUL. Normal deadline5s; timeout deadline0.5s. On
failure terminate only owned fixed PID if still running; drain both streams,
wait for native exit and record observed discarded bytes. These fixed scripts
spawn no descendants. Exit0 alone never overrides a logging failure. Capturing
observed bytes after termination does not mean full intended flood output.

Independent stdlib validator reuses only the frozen independent BEJ0 decoder,
reconstructs channel bytes/namespace/envelope, exact clean bytes, all native
exit/working-set records and returned controller exit. Allow actual nonzero
Windows termination code rather than pretending Linux signal semantics. No
cross-platform performance equivalence or matching stream interleave claim.

This bounds only cooperating prototype files and observed process lifecycles;
no hostile external writer/OS quota/arbitrary child-tree/concurrent writer/
crash durability/whole-production-dossier guarantee. It is not an archive
codec/reconstruction/old failure repair or a new scientific experiment.
