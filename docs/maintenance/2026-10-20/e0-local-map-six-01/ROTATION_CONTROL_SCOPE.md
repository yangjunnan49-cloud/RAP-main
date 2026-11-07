# Noncommuting rotation contract supplement

The original analytic anchor fixture is translational; a common world rotation alone does not test relative noncommuting rotations. Add one fixed12-frame synthetic trajectory with Rx/Ry/Rz products and nonlinear translations. With anchors at existing source indices0/4/8 and their unchanged poses, fine correction must be a no-op and all adjacent relative motions agree. Apply a common rigid world change and require equivalent output. This tests implementation convention, not physical efficacy or SO(3) guarantees of RAP. No real trajectory rerun, parameter choice or primary gate change.

Use the exact source-bound corrected-anchor helper and native optimizer/config; record input matrices and maximum errors. Charge original cumulative LMB1800s/4GiB per process/128MiB combined/GPU0, original12GiB host launch guard. The current full bank/result is unaffected by a pass; failure invalidates implementation confidence and is preserved.
