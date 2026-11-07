# Component decision

The archive inspection completed without point decoding, optimization or numerical GT access. This is a bounded two-sequence source/structure decision, not a causal performance attribution.

| Interface | RAP/E0 | Archived KISS-SLAM | Consequence |
| --- | --- | --- | --- |
| Graph node unit | 670 / 374 keyframes on 00 / 05 | 33 / 20 local-map nodes | IDs cannot be interchanged |
| Local-map graph edges | 12 / 12 admitted RAP loops plus keyframe motion | 39 / 24 total edges, 7 / 5 with nonadjacent map indices | Different observation placements; index classification alone is not a new loop-accuracy evaluation |
| Dense graph | Current keyframe graph propagated to scans | 4541 / 2761 vertices and 4540 / 2760 adjacent edges | Exported dense graph does not expose a simple same-node loop swap |
| Map export | Endpoint-local 4000-point input caches available | 32 / 19 PLYs transformed by optimized keypose at export | Exported points are not already raw sensor-frame inputs |
| Source membership | Explicit E0 source frame manifests | No source/member/frame/timestamp sidecar in these two output folders | No directly authenticated E0 transplant of archived KISS map factors |
| Motion and weighting | Fixed corrected E0 poses; declared motion/loop sigmas | Local odometry reset at each map boundary; unit information for map motion and loops | A whole-system performance gap does not isolate RAP or backend weights |

The installed source shows a local trajectory inside each LocalMap, but that source-frame membership is not exported in the inspected sidecar set. It may be reconstructible with additional execution; no all-source impossibility claim is made. Existing optimized graph text is rounded and is not an original raw-membership manifest.

Decision: do not manufacture a 2x2 causal swap. Proceed with the same-input B/Q/D comparison specified prospectively in PROTOCOL. It holds observation topology/support fixed and tests a different global coupling. The alternative local-map observation route remains a separate later engineering decision, not part of DMF0.
