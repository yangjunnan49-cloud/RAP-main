# Matched conventional registration protocol v1

Declared before comparator-01 execution, on the already observed development
cohort core-replay-01. No parameter search or new statistical fitting is planned.

Use Open3D 0.19 point-to-point ICP, maximum correspondence distance 2.5 m,
100 iterations, relative fitness and RMSE stopping tolerances 1e-6. Two separately
reported arms: identity initialization (no external pose prior, like RAP's input
interface), and inv(odom[i]) @ odom[j] initialization (additional frontend prior).
RAP has no explicit initial transform and internally centers/normalizes clouds;
identity ICP is a no-pose-prior comparison, not identical internal initialization.
This is a local registrar baseline, not a claim about all classical/global methods.

Freeze all 40 merged candidates and their order, original source scan identities,
minimum range 1.5 m, RAP preprocessing (0.4 m voxel, statistical outlier removal
20 neighbors/2.5 ratio, cap 4000 with independent seed 42 per scan). Reuse the
production preprocessing implementation with feature extraction disabled; ICP
does not use learned descriptors. Transform direction is j -> i.

Accept only valid rigid transforms with the existing symmetric NN overlap >= 0.7
(distance < 1 m) and symmetric mean NN distance <= 2.5 m. Do not gate on GT or
Open3D fitness. Record all attempts including failures/rejections, initial/final
transforms, same-result GT labels (5 m/10 degrees), point/input/source hashes,
and registration timing. Timing is CPU registration only, not full-system runtime.
Keep relfloor + Huber, NMS 0, frozen frontend and source IDs. Report odometry,
fresh RAP and both ICP arms for each sequence; retain every negative result.

Check transform direction on a known rigid synthetic pair before real scans.
Verify source hashes against replay provenance and recheck them on completion.
Use an exclusive new directory with INCOMPLETE until all evaluations finish.
No legacy output or production algorithm source is modified. This helper belongs
to RAP-main maintenance, importing RAP-SLAM as a read-only dependency.
