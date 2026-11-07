# RI1 closed at the original GPU admission gate

The stdlib-only preflight failed `GPU free memory admission` before importing numerical packages or constructing a model. The frozen threshold was 9,216 MiB free. The failing worker did not persist the measured free value before its assertion, so that original value is UNKNOWN; GPU_DIAGNOSTIC_AFTER_STOP.json is explicitly a later read-only observation, not a replacement measurement. No lower threshold, alternate allocator/config, case retry or unrelated application termination is allowed or performed.

Worker counters are all zero: point occurrences decoded, model constructor attempts/completions, RAP calls and ICP calls. The independent watcher saw the nonzero worker exit, cleaned correctly, and the Windows host exit is2. No ADMISSION.json or numeric stage was created. A subsequent documentary command attempted to read the absent success RESULTS.json and failed; this did not launch work and is retained as a bookkeeping assumption error, not a second model attempt.

All 78 project source/config identities, eight public inputs and two existing weight identities were checked before the GPU assertion. Current weights were not deserialized. The public/reference separation and physical-efficacy NOT ADMITTED decision remain. This is a resource-stopped functional attempt, not a RAP efficacy or model failure result. Scope time/caps and original preflight receipts remain; no automatic retry follows quota reset or changing capacity.

Continue independent CPU-only source failure-path characterization if budget/account allow. Original P0/N1/N2/C0/CN1 states, all old caps/stops, manuscript PAUSED and research UNRESOLVED remain.
