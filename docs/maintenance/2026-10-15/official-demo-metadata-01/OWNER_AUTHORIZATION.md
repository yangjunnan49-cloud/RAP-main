# MDA0 Narrow Owner Metadata Authorization

Owner explicitly answered "允许获取 ≤4 MiB 官方元数据" to the question:
only author-published existing-demo file manifests/reference-pose metadata,
total at most4MiB; no point-cloud/weight download, dependency install or external
message. Permission is limited to this task, not a full dataset or model change.

Official README links the YuePanEdward/regx-benchmark repository. A web tree
observation exposes revisionc8deb301b32bb887acd48371ae93221251a056b5.
Use this exact revision for metadata requests; failed access is not absence.
Canonical14.2MB JSON and7.35MB JSONL are excluded, not fetched in pieces.
