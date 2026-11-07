# Post-outcome objective diagnosis

This diagnostic is explicitly selected after all four MMR0 window outcomes are
known and validated. It cannot serve as a prospective confirmation, new winning
arm or a repair of the zero-of-four pose/probe signals. No optimizer is run.

Use the existing sealed point/normal/pose banks. Evaluate the same point-plane
objective at saved O/F/R poses and the reference poses, with both fixed initial
matches and fixed final R matches. Examine a fixed five-point interpolation from
R toward the nearest-proper reference pose, and its directional derivative split
into rotation and translation. Supplementary rematching costs disclose all
association counts: different selected supports are not a common objective.

The purpose is to distinguish an optimizer failure hypothesis from a mismatch
between this geometric residual and the existing short-window pose reference.
Neither outcome proves that official GT is wrong or identifies scan distortion,
normal bias, dynamic returns, association identity or calibration as the cause.
Evaluate reference poses only; never use them to optimize a candidate trajectory.

Bind this scope, code, helper and sealed banks/results before diagnostic output.
Resource time including this analysis counts toward the same new 1800 s CPU
exploration ceiling. No source, point, solver, window or historical gate changes.
