# C2 amendment 01 — fixed-index stratum count correction

The original protocol fixed 14 saved-order indices per sequence before
generation and asserted that these represent two confusers and four of
each positive stratum per sequence. The fixed F2 saved order does not
have perfectly contiguous strata at those indices. The full 28-pair
bank completed and was SHA-sealed before evaluator-only GT. The original
evaluator wrote all28 per-pair outcomes, then stopped at its own
`len(ordinary)==8` assertion before writing a summary or decision.
`INCOMPLETE` remains pending this amendment.

Measured cohort composition from the evaluator labels is 00:
confuser4, ambiguous4, low-overlap3, ordinary3; 08: confuser2,
ambiguous4, low-overlap4, ordinary4. Thus there are seven ordinary pairs.
The cohort IDs, interventions, saved output, GT separation and all effect
definitions remain fixed. Preserve the original PROTOCOL.md, runner and
validator verbatim. The amended evaluator and independent validator
correct only the impossible ordinary-count assertion from8 to7, keep
the original **absolute >=6 ordinary-pair** response threshold unchanged,
and report the actual composition. This makes the response requirement
stricter in fraction (6/7 rather than6/8). No extra pair, generation,
effect threshold, favorable subset or gate adjustment is allowed.

The amendment freeze records original bank/outcomes hashes and amended
source hashes before the summary is finalized. The per-pair outcomes
from the stopped original evaluator are retained and independently
recomputed against the sealed bank and frozen GT by the amended validator.
