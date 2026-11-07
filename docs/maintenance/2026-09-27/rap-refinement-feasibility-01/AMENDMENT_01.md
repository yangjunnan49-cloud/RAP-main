# R0-AMENDMENT-01: integrity-hash wording clarification

Recorded after the completed R0 execution; the original frozen protocol,
runner, bank, metrics and validator are unchanged. The protocol's phrase
“Runner reads only F2 records and each pair's inputs.npz; never evaluator
rows, strata, GT” was too broad. The frozen `verify_freeze()` called at
runner start streams the bytes of **every** frozen file for SHA256,
including evaluator rows and evaluator GT arrays. The runner did not parse,
load as arrays/JSON, branch on, or use the contents of those evaluator
files in pose selection or ICP. Its actual pose computation reads only
`records.json` and `inputs.npz`. The separate evaluator loaded GT and
strata only after `bank.json` was sealed by SHA256.

This is an integrity-read exception to the protocol's literal wording, not
an outcome-dependent input or a change in the measured result. The original
protocol and frozen source hashes remain available so the distinction is
auditable. Future protocols should say “evaluator files may be byte-hashed
for integrity, but not parsed or used by the runner” when that is intended.
