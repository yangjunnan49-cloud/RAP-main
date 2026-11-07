# Implementation-only variable-length representation amendment

The original frozen bank stage stopped before optimization or any prediction at
the first window. Its `np.stack` call assumed that all eight scans retained the
same number of representatives after the unchanged 0.5 m voxel sampling and
6000-point upper cap. That assumption is false: the cap is an upper limit, not
a density replacement rule. No numerical GT payload has been parsed.

Preserve the original source files, freeze, passing synthetic preflight, empty
bank directory, failure traceback, resource log and INCOMPLETE marker. The new
attempt-02 uses variable-length lists during optimization and separate numeric
NPZ arrays per scan for storage. No padded, repeated, removed or newly selected
points are introduced. The canonical algorithm helper stays byte-identical.

All four frame selections, point filtering/correction/voxel ordering and cap,
even/odd split, normal estimation, edges, solver, steps, losses, correction bounds,
evaluation rules and total 1800 s/2 GiB/512 MiB caps remain unchanged. Failed
original compute counts in the combined process ceiling. Attempt-02 freezes both
original evidence and its new orchestration/validation sources before execution.

This is an implementation repair within the owner's selected exploration, not a
scientific gate amendment, favorable window replacement or automatic full-system
experiment authorization. No original stage is relabeled complete.
