# SSC1 complete: direct stereo support improves coverage but fails the target screen

All273 stereo pairs and all200 unchanged cross-visit SIFT hypothesis sets completed. The new right-camera channel supplies4381 jointly supported cross-visit rows across196 pairs;141 pairs meet the frozen >=4 matches / both-image covariance>=4px² eligibility definition. These are support hypotheses, not authenticated associations or accepted poses.

| Exposed diagnostic group | Pairs | Any joint depth | Eligible |
|---|---:|---:|---:|
| All |200|196|141|
| Positive |150|148|109|
| Nonloop |50|48|32|
| RAP-unique00 |21|21|18|
| RAP-unique08 |6|6|3|
| Historical missing |64|63|41|
| Old wrong accepted |9|8|6|
| Current wrong accepted |8|7|5|

The predeclared target admission screen required at least5 eligible oldunique pairs in EACH sequence. Actual00/08=18/3, therefore FAIL: STOP_THIS_STEREO_SUPPORT_ROUTE before candidate scoring or training. No disparity, LR, SIFT, support-count or covariance sweep follows. This does not prove all camera methods impossible or that the newly measured support has no use. It preserves a concrete source-level improvement while respecting this finite gate.

Depths come from both endpoint stereo image pairs, unlike CPV1's assigned source-LiDAR proximity depth. Original left-left SIFT hypotheses were unchanged; no feature extraction, candidate fitting, RAP, PnP, geometric gate, reference-pose evaluation or PGO ran. The spatial covariance uses the explicitly implemented population second moment;4px² is a support margin, not calibrated pose/identity confidence. Hypotheses, acquisitions and pairs have different denominators and are not independent samples. Support in32/50 nonloops reinforces why eligibility cannot be acceptance.

Independent scalar reconstruction verified10682 endpoint disparity samples and400 covariance quantities, all eligibility decisions and all jointly supported xyz; xyz delta0, largest covariance eigenvalue delta1.0914e-11px². It consumed saved disparity arrays, not a second SGBM implementation. Disparity uncertainty and calibration/timing errors remain uncalibrated. Exposed group membership was joined only after complete support and audit seals; data were already exposed historically and are not blind or unseen confirmation.

Original packet interruption is retained in SUPERVISION_FAILURE.md and original HOST_EXIT:46.406s,131 nonce responses,135 unsealed complete map files. A separate immutable-mailbox integration passed160 rapid serial/nonce exchanges. Its135 maps were validated and byte-copied; only138 missing maps were newly computed. Measurement source is byte-identical. Original control and failed-packet costs were deducted from90/300s caps; original04:43UTC/2400s clock retained, parent256MiB dossier retained. The fresh native engine for remaining scans has the same configuration; complete hidden-state equivalence to an uninterrupted engine is not claimed. No partial coverage outcomes were used to choose the integration or parameters.

Five unique Windows children (original controls, interrupted packet, integration controls, remaining packet, audit) exited and were reaped. Successful stages carry self-peaks and external counters; the interrupted child's lifetime self-peak is unknown and its54,493,184-byte value is host-observed. No WSL/GPU/install/training/default/production/Git-history change. Ordinary and RAP candidates were not scored by this study, so there is no new correct/wrong acceptance count. Historical GCG1 remains37/8; all old stops and E0 engineering positives remain. Research UNRESOLVED; manuscript PAUSED.
