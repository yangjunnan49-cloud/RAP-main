# OIC0 fixed public compatibility reply

Question: does the existing reply to PRBonn/RAP issue 3 identify an actionable
online-versus-downloadable input/configuration/model distinction, or supply no
such explanation? A participant observation is not automatically author evidence.

Fetch exactly once:
https://api.github.com/repos/PRBonn/RAP/issues/3/comments?per_page=30

No query changes, redirects, retries, subsequent pages or linked assets. Request
identity encoding; require HTTP 200 and a complete body before admitting JSON.
Read and retain at most 65,536 delivered body bytes, including partial failed
reads; headers are recorded separately. Non-200 or encoded responses are not
body-read. A declared body larger than the reservation is rejected before read.
At the cap, unknown EOF is incomplete, not permission for another read/retry.
Link headers and array length determine whether a complete page is supported;
an incomplete page cannot support an all-comments claim. The historical cached
count of one is context, not an assumption about the current response.

The prior metadata body ledger 1,357,466 bytes is immutable. Record the new body
separately and its arithmetic addition to that old metadata scope, retaining
the 4,194,304-byte combined ceiling. B1 and B2 have separate authorized byte
accounts; do not combine or reset those scopes.

Freeze this protocol, owner scope, transport/controller, native query definition
and exact parent cached response identities before the GET. Parse only complete
admitted UTF-8 JSON. Record author association, identity, dates, original body,
comment URL, completeness limits and any concrete stated distinction. Do not
infer present model equivalence, a local defect, a unique historical cause,
training membership, independent physical truth or efficacy from the comment.

Resources: at most 300 s total enclosing execution across source acquisition and
validation attempts, 512 MiB native child OS peak, 8 MiB new dossier, zero GPU.
Controller uses a retained process handle, records every running query and two
post-exit OS peak queries, and preserves stdout/stderr, failure and exit. The
observer's full lifetime peak and ordinary preparation RSS remain UNKNOWN.
No whole-machine/process-tree or arbitrary-writer guarantee is claimed.

On failure, preserve the exact attempt and stop acquisition. On success, verify
the response hash/length, exact endpoint, receipt and comment structure in a
separate read-only validation. Then write the compatibility decision. No second
network request or payload is admitted by this protocol.
