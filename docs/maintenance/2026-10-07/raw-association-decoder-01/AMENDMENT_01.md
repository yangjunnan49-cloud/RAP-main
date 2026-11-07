# RAD1 implementation repair before evaluator access

Original independent bank validation stopped at08_384_634, descriptor armD,
generation0 after120 completed pairs. Kabsch/Horn pose delta24.78940957.
No evaluator GT or strata were parsed. Original1497-identity freeze, three
sources, all200 prediction NPZs, bank/seal and failure remain unchanged.
Original attempt is INCOMPLETE and is not scientific negative evidence.

Diagnosis: both fits used exactly the same winning seed1, clique, all three
refit masks, nine final inliers and21 valid proposals. The last support's
source/target centered second singular values are0.26829/0.43277, but its
cross-covariance singular values are[0.1977435,2.94e-17,4.97e-18]. Repeated
rows in consensus make the rotation objective nonunique. Two different
proper rotations have identical SSE1.11378097721057. Checking the two point
sets' separate ranks is insufficient. Native decoder replay is exact, so
relaxing the independent pose tolerance would conceal an actual ambiguity.

Attempt-02 adds the missing proper-rotation identifiability check to every
Kabsch fit and independently to Horn: reject top eigenvalue gap<=1e-6 times
the leading cross-covariance singular value, or leading value<=1e-12.
Kabsch uses the analytically equivalent2*(s1+sign*s2). The same relative
degeneracy tolerance1e-6 was already frozen for point-set rank checks.
No fit is returned for a nonunique rotation; existing rejection/fallback
semantics apply. Add one synthetic crossed noncollinear correspondence case.

No scientific gate, data, cap, association rule, consensus threshold, seed,
selector or admission rule changes. This is a disclosed correctness repair,
not outcome-based algorithm tuning. Freeze new sources/protocol plus this
amendment and original freeze/seal/failure before new output. Rerun the
complete200-pair bank and independent validation. Use separate v2 algorithm,
driver and validator names; do not overwrite original sources or outputs.

No training, new inference, graph, trajectory, model/default/production/
manuscript change, download/install, commit or Git sync.
