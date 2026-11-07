# Exact original extraction record needed next

This is a local evidence specification, not a sent message or authorization to obtain a dataset. Existing author outreach remains unsent. A local file path to an already authorized original record is sufficient to begin a bounded source-role review; a newly written explanation cannot retroactively supply missing provenance.

Target revision: c8deb301b32bb887acd48371ae93221251a056b5 of YuePanEdward/regx-benchmark; scene OutdoorScan/paris_02. Published payload identities already bound by B1:

| Member | Bytes | SHA256 |
|---|---:|---|
|000.ply|270148|3b9baa3c723165975b01fe878a154a5fd126ab548e3b6a4a9dc2730c3c8ecfaf|
|001.ply|271660|0d24b46c7b71354a614a5b36759285eeff2fcb117ec4bdf2a6cabc42782f560c|
|002.ply|273076|16bc406305aa0b58a8f5f3f075e4cbe52d925a23fff09be6f14fc4ed95a35cf0|

Needed fields, with original publisher/creator identity and release/version:

1. Exact upstream scan/return members and timestamps contributing to each PLY, including whether a view is one scan or an accumulated/cropped map.
2. Raw versus motion-corrected input, CT-ICP/pose-release version, accumulation order, interpolation and any dynamic-object treatment.
3. Sensor/vehicle/world frame, units and exact transform action, plus the physical calibration/time convention used during conversion.
4. Filtering, cropping, voxelization/subsampling, coordinate changes and export recipe sufficient to bind the source membership to these exact payloads.
5. Reference construction and any independent validation or uncertainty. The creation paper's upstream pose-generation description alone is not an exact-file or independent-accuracy certificate.
6. Known acquisition/session/site relationships and prior exposure. Any checkpoint-exclusion claim additionally requires a record for the exact local checkpoint; otherwise retain UNKNOWN.

Explicitly unavailable fields should remain unavailable. Do not infer time/ring information from the derivative XYZ schema, reconstruct source membership from favorable geometry, substitute another Paris scene, alter official references, or call multiple augmentations independent scenes. Receipt of a record permits its review only; a numerical experiment still needs its own useful task/control/resource decision.

Original identity source: docs/maintenance/2026-10-16/regx-reference-package-01/PACKAGE_PLAN.json, read with its later authorized acquisition/report rather than its historical prepared-status string. No point or reference payload was decoded for this specification.
