# BEJ0 Bounded Evidence Journal Prototype

Freeze source before testing. Exclusive fixed evidence.rdj in a new per-case
directory; no arbitrary output paths. Header16bytes and footer64bytes are
reserved before any payload. Each body record has channel1byte/length4bytes
plus exact bytes. Four channels: payload1/stdout2/stderr3/metadata4. Charge the
whole encoded record before writing, with no refund on partial failures.
Global and per-channel limits must both pass before writing. Footer includes
terminal status, charged body bytes, complete record count, actual body length
and SHA256 of actual body bytes. Terminal footer is excluded from channel budget
but included in file cap. No silent log truncation: any rejected record marks
the journal failed and prevents further body writes. A failed journal is not
successful scientific evidence, even if its retained prefix is decodable.

Short I/O may leave a torn record. Preserve it with a failed footer when footer
I/O succeeds; decoder exposes torn status. Footer I/O failure/power loss cannot
be made complete by a reservation; a missing/bad footer is unsealed. Do not
claim durability or atomicity from close(), SHA or bounded length alone.

Prospective15 cases: normal four-channel completion; stdout overflow; stderr
overflow; metadata overflow; global cap rejection; preexisting collision;
injected short-write failure; copied payload corruption; copied truncated
footer; an out-of-band external file; invalid input type; append after close;
exact cap fill; second concurrent constructor collision; invalid channel.
All cases retained. Expected negative evidence is not a failed test invocation.

Independent parser rebuilds header/frames/footer/digest and filesystem census
without importing writer/runner helpers. Verify all15 outcomes, exact-cap file,
overflows never admitted, prefix accounting conservative, invalid copies not
admitted and the external file detected. The external case proves a boundary:
single-file bounds do not bound a namespace writable by others. No global OS
quota or hostile-writer prevention is implemented.

This prototype bounds its cooperating single-file output only. All future
process/log redirection, lifecycle/concurrency, emergency metadata and complete
directory ownership need their own implementation/validation before a future
whole-dossier guarantee. No LCP0/HFIT0 retry or integrated packing follows.
