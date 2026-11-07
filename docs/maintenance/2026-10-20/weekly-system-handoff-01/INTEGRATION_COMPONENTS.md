# Fixed-E0 integration components

Use `fixed_E0_integration_components_20261020.zip` for the two reusable interfaces. This is a local experimental component bundle, not a complete new raw-frontend SLAM release.

- `fixed_odometry.py`: exact extracted external-odometry adapter, native14-frame import/state/reset check passed.
- `anchor_component/anchor_fine.py`: explicit-config coarse-anchor-preserving fine graph, complete six CLI outputs exactly equal the frozen G matrices.
- `anchor_component/cases/`: all six complete source odometry/initial/coarse-anchor/G arrays.
- `anchor_component/pose_graph_config.json`: unchanged ten-iteration native configuration.
- Per-member checksum manifests, original source snapshot, and interface/equivalence proofs are included. Dependencies remain the existing documented Linux environment.

Typical isolated API use after explicit execution scope and resource/budget checks:

```python
from fixed_odometry import FixedOdometry
from kiss_slam.slam import KissSLAM
from anchor_component.anchor_fine import fine

slam = KissSLAM(config)
slam.odometry = FixedOdometry(config.kiss_icp_config(), odometry_poses)
# Feed every preprocessed source frame once, preserve map/reset membership,
# finalize maps, and recover each actual source-anchor coarse pose.
# Use fine(odometry, initial, anchor_ids, coarse_poses,
#          config.pose_graph_optimizer) for the same fixed G correction.
```

The full working source-recording application remains the frozen `e0_local_map_six.py`, which was used for the real experiment; the bundle's short example does not replace its preprocessing, source identity, membership, finalization and budget safeguards. Do not infer anchors from rounded poses or graph-node IDs. Keep the known0.205degree/range/source-frame conventions and the original source-role limits.

G's measured six-sequence average target passes, but individual07 ter/10 rer protection fails; original strict tests remain failed. G remains experimental, B remains the default. No new whole raw-system timing, independent scene, physical reference authentication or RAP increment is supplied. These modules permit concrete review/integration work, not automatic production/default mutation or candidate retry.
