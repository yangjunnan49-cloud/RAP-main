# O1: RAP-initialized ICP refinement

Predeclared practical screen passed: False. Production default unchanged.

| Sequence | RAP first APE m | Refined first APE m | RAP aligned APE m | Refined aligned APE m | Accepted |
|---|---:|---:|---:|---:|---:|
| poss | 1.822264 | 1.912266 | 0.666054 | 0.676565 | 4/4 |
| kitti06 | 2.446184 | 2.516788 | 0.868971 | 0.867795 | 12/12 |
| kitti05 | 3.417117 | 2.913561 | 1.129313 | 1.047307 | 12/12 |
| kitti00 | 11.432935 | 11.533925 | 2.891543 | 2.930891 | 12/12 |

| Sequence | Drift frame | RAP translation % | Refined translation % | Additional ICP seconds |
|---|---|---:|---:|---:|
| poss | LiDAR (POSS) | 1.961403 | 1.988821 | 0.021 |
| kitti06 | camera | 0.667058 | 0.667760 | 0.072 |
| kitti05 | camera | 0.703737 | 0.701841 | 0.063 |
| kitti00 | camera | 0.914171 | 0.908802 | 0.061 |

Same pairs, fixed local refinement, freshly measured gate diagnostics, same backend. No GT-based selection. See JSON for individual measurements. This development screen is not independent validation. Refinement runtime excludes loading/preprocessing and is additional to baseline registration.
