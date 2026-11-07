# PRI0 Snapshot Layout Amendment

Original prefreeze failed on a repeated audit_continuation_handoff05.py basename,
before freeze.json or comparison. All original source, partial snapshot and full
failure/exit receipts remain in place and are bound by ORIGINAL_AVAILABLE_SEAL.
This separate attempt deduplicates exact input paths and preserves repository-
relative paths in source_snapshot. Hash/comparison/claim predicates do not change.
Only output routing, original-evidence binding, snapshot layout and aggregate
attempt accounting change. Original and new attempts share300s/128MiB/8MiB caps;
the8MiB cap covers both directories. No model/dataset download or deserialization.
