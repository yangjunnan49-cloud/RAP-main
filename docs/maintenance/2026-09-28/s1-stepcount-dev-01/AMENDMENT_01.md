# S1-AMENDMENT-01 — runner import-path startup repair

The original frozen S1 runner stopped before constructing `RAPBackend`,
creating `INCOMPLETE`, generating any pair or loading evaluator GT. It
imported `rectified_point_flow` before adding RAP-main to Python's import
path. The module was present in the original 1,081-file freeze but not
yet importable. The original runner and protocol remain unchanged.

The separately frozen `s1_stepcount_dev_v2.py` adds RAP-main to the
module search path before that import. It also checks the amendment
file hashes at run and evaluator entry. No cohort, input, point, noise,
sampler, score, gate, outcome decision or resource rule changes. The
separately frozen v2 validator adds the amendment-hash check; all
geometric and evaluator checks are otherwise unchanged. Freeze this
amendment and v2 scripts before any real pair generation.
