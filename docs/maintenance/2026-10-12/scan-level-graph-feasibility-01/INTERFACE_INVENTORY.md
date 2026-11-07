# Available measurement interfaces

This is a read-only inventory and design note, not a new registration execution.

- All12296 saved scan poses have exact dense source IDs and matched timestamps. All1800 keyframes cover both endpoints. All58 admitted loop endpoints are keyframes. Stored E0 poses, source_frames, keyframes, accepted_loops and summaries are sufficient for this graph replay.
- Existing graph API accepts Pose3 loop measurements and mean_dist/overlap diagnostics; relfloor/Huber uses fixed scalar information. It does not consume physically measured point residuals or a registered local information matrix in the tested path.
- There is no measured per-scan KISS covariance/Jacobian/correlated-increment model in the inspected saved bindings. SGC0 allocation cannot fill that missing measurement evidence by naming an engineered covariance empirical.
- Raw scan paths exist in source manifests, but no raw scan was loaded this round. Future measurement work must rebind the exact physical support and preprocessing before registration, retain attempt failures and distinguish reference-only fields from deployable input.
- Existing `scripts/geometric_loop_information.py` estimates measured surface-information shapes for earlier PFG work. Earlier fixed-centre information/shared-plane stops remain; it is not a fresh successful GICP measurement implementation.
- Repository search found no `registration_generalized_icp`, `GeneralizedICP`, `small_gicp`, `pygicp` or `fast_gicp` call sites in the inspected RAP-SLAM source/scripts or main maintenance Python helpers. This says nothing about installed packages. No installed GICP API was verified or acquired here. A later scope must verify a supported CPU API before a payload; missing dependencies do not authorize installation.

Existing full-system benchmark uses different computational work from this stored-graph study. This round's input binding is historical E0 A, which reproduces the latest benchmark's RAP numbers to the shown precision; it is not a fourth fresh full-pipeline repetition.
