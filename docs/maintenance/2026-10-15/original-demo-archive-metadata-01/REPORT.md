# ODA0 original author demo archive metadata

Decision: COMPLETE_ORIGINAL_ARCHIVE_MEMBER_CRC_LENGTH_CONSISTENCY_WITHOUT_CRYPTOGRAPHIC_OR_REFERENCE_AUTHENTICATION.

The official download-script URL was queried by HEAD, followed by exactly the
22-byte standard ZIP end record and its declared 23,077-byte central directory.
No point-cloud member, weight, local-file header, speculative tail, full archive,
or full RegX manifest was requested. All three requests completed with exact
HTTP status/range/length and stable ETag predicates independently reconstructed.

The observed archive is 368,834,018 bytes; ETag "15fbf5e2-649d68225a385";
Last-Modified Mon, 02 Feb 2026 12:31:55 GMT. These are current server metadata,
not a cryptographic archive identity or proof of original acquisition history.
The central directory contains 184 entries: 28 directories including its root,
and exactly 156 point files. Its complete relative filename/length population
matches the existing 156-member local request. All 478,400,579 local bytes
still match their preexisting SHA256 identities.

All 156 current local CRC32/length pairs match the author archive directory.
Primary streaming C# CRC/SHA256 and independent Python zlib/hashlib comparisons
agree. This materially strengthens current bundle consistency beyond a filename
match or a RegX mismatch. CRC32 is not collision resistant: it does not establish
remote member SHA256 equality or exact cryptographic byte authentication.
The earlier MDA0 result remains valid for its different pinned RegX revision.

Every archive file is PLY or PCD; there is no pose/reference sidecar or other
regular file in this complete directory. All member comments are empty. The
only extra-field tags are 0x5455 timestamps and 0x7875 Unix UID/GID; no member
SHA256 or reference construction is supplied by these fields. This is an
archive-namespace statement, not all-history or global metadata absence.
Whether clouds were prealigned, which input-to-world references were used,
their measurement quality, and training/session membership remain unknown.
DSR0's default supplied-coordinate reference interpretation is unchanged.

New acquired response bodies total 23,099 bytes. Together with the previous
1,273,695 bytes, the shared official-metadata total is 1,296,794 <= 4,194,304.
No range partitions an oversized manifest; the two ranges are the ZIP's natural
end record and its explicitly declared metadata directory. Both requested
intervals are after all member payloads under the independently parsed standard
layout. Socket/header bytes are outside the response-body measure.

The first local inventory stopped at its standard CRC assertion, before parsing
the directory or scanning local files: PowerShell interpreted unsuffixed
0xcbf43926 as signed Int32. The retained C# CRC implementation returns the correct
UInt32 value. A separately bound variant changes that expected literal to
3421780262L plus source/output routes. It changes no CRC algorithm, byte identity,
comparison predicate, HTTP request or resource cap. Original worker/controller,
local binding, INCOMPLETE marker and complete failed execution remain preserved.
The independent validator variant changes only binding/inventory routes.

The source/reference evidence decision remains limited: current original-bundle
membership is supported by full CRC/length consistency, while cryptographic
member identity and reference construction are unauthenticated. No default-demo
external-truth accuracy test is admitted. Reuse the existing unsent author request
with this additional evidence; no external message was sent. Further geometry
correlation or a full ZIP download would not provide the missing reference
construction, so this scope stops here and independent mechanism assessment follows.

See CHECKS.json for actual enclosing durations and native final-peak observations.
Five enclosing attempts include four successes and the retained CRC assertion
failure. Independent Linux validation reads byte streams only, no coordinates,
and uses no new network request. All original 600s/512MiB native/128MiB Linux/
8MiB dossier caps retain their exact scopes. Observer complete lifetime peak and
ordinary setup RSS remain unknown; no all-native/process-tree claim or old-gap
repair is made. No new model, fit, pose metric, production/reference/manuscript,
installation, restart, commit or Git synchronization. Original research goal
remains unresolved. The newly retained original inventory marker supplements
the ten inherited markers; it does not change their states.
