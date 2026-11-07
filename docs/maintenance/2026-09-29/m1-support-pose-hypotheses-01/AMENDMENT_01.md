# M1 protocol arithmetic clarification

The frozen protocol correctly specifies four generations with nine
`T_ab` transforms each. One sentence incorrectly calls the non-anchor
set “other 35 support-derived candidates.” There are eight non-anchor
transforms per generation, hence **32** support-derived transforms and
four original `T_00` transforms per pair. The frozen runner, evaluator
and independent validator all use `strict[:, 1:]`, which selects those
same 32 support-derived transforms. The candidate bank, thresholds,
outcomes and decision are unchanged. This amendment records the typo
without editing any frozen file or rerunning an experiment.
