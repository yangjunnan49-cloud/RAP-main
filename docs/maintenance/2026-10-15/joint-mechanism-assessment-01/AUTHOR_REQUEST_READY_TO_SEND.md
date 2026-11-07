# Exact demo/reference request, ready for review and unsent

Proposed recipient: Yue Pan, yue.pan@igg.uni-bonn.de, listed in the official README.
No email/draft/API message has been sent. No external transmission is authorized.

Subject: Reference construction and member identity of RAP demo_example_data.zip

Dear Dr. Pan,

We are evaluating RAP's intended registration role using the existing demo
point clouds. Could you clarify the reference construction for the original
demo_example_data.zip linked by the official download script?

We queried only the current archive's HTTP metadata and ZIP central directory.
It contains 156 point files in 27 scene directories. Every local file's size and
CRC32 matches that complete directory; local SHA256 identities are retained.
The observed archive ETag is "15fbf5e2-649d68225a385", with Last-Modified
2 February 2026. We recognize that CRC32/ETag are not cryptographic member hashes.

1. Are these supplied point clouds already registered to a shared frame within
   each scene? If so, how was that alignment established and what accuracy or
   limitations should be associated with it?
2. Are there input-to-world reference transforms for these exact members, with
   units, transform direction and coordinate convention, or is the intended
   demo reference simply their supplied coordinate alignment?
3. Is an exact archive version/member SHA256 manifest available? If these examples
   relate to RegX, what preprocessing/reference-version mapping identifies them?
4. Is their training/site/session role documented, or should it remain unknown?

Our goal is to distinguish supplied-reference engineering evaluation from
independently measured registration accuracy. An explicit statement that a
reference or provenance field is unavailable would also be useful. We can provide
the complete 156-member identity list if needed.

Thank you for your time.

## Transmission boundary

This is the complete proposed message for owner review. The 156-member file list
is local at ../continuation-handoff-06/DEMO_MEMBER_REQUEST.json and is not attached
or transmitted. Sending, choosing a sender account, or attaching the list needs
explicit owner instruction. No raw coordinates, model weights or failure arrays
are included in this draft.
