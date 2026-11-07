# PPR1 original creation-paper read

Decision: UPSTREAM_ACQUISITION_AND_POSE_CONSTRUCTION_STATEMENTS_OBTAINED; EXACT_REGX_CROSSWALK_AND_PHYSICAL_EFFICACY_NOT_ADMITTED.

The owner explicitly authorized the two exact sources and their envelope. Both complete objects were obtained, then read offline. The abstract identifies arXiv2310.16542; the PDF and its response filename identify revision v3, dated June3 2024. This is a current capture of that document, not proof of a historical local dataset or checkpoint identity.

## Newly supported upstream statements

The following paraphrases are limited to the original paper, Section III-A, PDF pages2-3. Both complete pages were visually inspected after text extraction.

| Field | Paper-supported statement |
|---|---|
| Acquisition | November2015, a 2.1km route around Luxembourg Garden, Paris; Velodyne HDL32 |
| Scan unit | 7501 scans, each one 360-degree revolution at10Hz |
| Raw attributes | XYZ, per-point timestamp, intensity and laser index; timestamps synchronized with GPS |
| Motion treatment | Raw scans retain motion distortion; CT-ICP estimates motion-corrected scans |
| Pose construction | CT-ICP supplies scan poses, then overlap ICP and graph SLAM close the loop |
| World/time convention | World based on the first scan; KITTI-format vehicle poses at scan midpoint |
| Pose accuracy | The inspected acquisition section does not quantify independent pose accuracy or give a calibrated uncertainty bound |

Source: [the original paper](https://arxiv.org/pdf/2310.16542), locally retained as ParisLuco3D_2310.16542v3.pdf. The content digest, rather than the response ETag, binds the bytes read. The received ETag's digest-like value differs from our body SHA256; no equality or remote checksum authentication is claimed.

## Consequence for the project

This resolves an upstream method question that the main project HTML left open. GPS synchronization does not establish independently measured GPS pose ground truth. Our inference is that comparisons against the described poses must state their CT-ICP/ICP/graph construction and potential methodological dependence, rather than treating them as independently surveyed truth. This does not show the poses are wrong, and no original reference is changed.

The exact RegX metadata still supplies only a named source and overlapping street sections. Its three XYZ-only PLY schemas and author augmentation convention do not identify upstream raw scan/return memberships, source timestamps, accumulation/deskew revisions or the source-to-derivative transform chain. The paper's upstream six-field schema must not be attributed to the derivative files. In particular, no measured per-return timing or ring information is recovered from XYZ by this source read.

The precise LiDAR-to-vehicle extrinsic/direction for the three local derivative files, exact matrix action and extraction membership remain unknown. No independently reserved cohort or exclusion from the exact local RAP checkpoint is established. Physical efficacy and independent generalization remain NOT_ADMITTED. Original references,09 outcomes and all stopped families stay intact.

The next useful record would be the original derivative extraction/accumulation manifest or creator's record binding000/001/002 to raw members and reference construction. A published readme may clarify upstream release conventions, but even that would not by itself supply the RegX crosswalk. No model, array, pose metric, training or solver follows from this paper.

## Transport and resource evidence

Three requests: abstract200, one necessary PDF301 redirect from the authorized .pdf path to its authorized canonical path, and PDF200. Application-delivered body total4,777,213bytes, comprising41,722 abstract,217 redirect and4,735,274 PDF bytes. All objects reached EOF with identity encoding. No retry, other hyperlink, data-share access, credentials, cookie reuse, script execution or outreach.

Complete transport3.7625246/180s; worker2.734/90s. Native and watcher worker peak39,821,312bytes<256MiB. Initial and all three fresh12GiB/2s host leases pass. Exact owned process exited normally. Body SHA256: abstract0a92284ecf8229ca1e8d847a4496df93b4c0c99307b1ae353cd7326815b0b7ed; PDFbe0fa636b79f3a3524b3e8bcc2a08299f52a7ea9167f0f86bbdd0b720b3225be.

Offline extraction reads14pages/55,546characters without following links. Its observed process peak51,666,944bytes and enclosing0.9263408s pass the declared90s/256MiB offline limits. Page3 rendering has an enclosing1.0516772s/22,155,264-byte peak receipt. Page2 rendering succeeded in the tool's0.9635589s command interval, but no retained native process-peak receipt was captured for that render; its peak remains UNKNOWN. This gap does not affect the complete transport worker receipt and is not presented as an all-process resource guarantee. The complete source account and dossier bytes are in CLOSE_CHECKS.json, with all preparation included from02:27:05UTC and no old-cap amendment.

No WSL startup or environment/storage/default/production/install/Git/outreach/scheduler/goal-status change. Original research UNRESOLVED/manuscript PAUSED. The separate current-window continuation remains governed by actual account observations.
