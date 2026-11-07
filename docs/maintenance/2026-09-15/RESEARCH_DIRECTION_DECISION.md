# Direction decision after HL-V2 and SC-V1.1

2026-09-15. Evidence synthesis only; no new experiment, fitted model or manuscript.

## Decision

Stop expansion of the current clipped-distance temporal-support selector route.
Do not train a head or start another score/support/threshold sweep on00/02/08.
The completed experiments do not justify assuming that learning will rescue this
specific representation. This is a scoped resource decision, not proof that all
observation-supported registration methods are impossible.

## Evidence separated by question

1. **Proposal headroom exists but varies.** HL-V2 KITTI02 oracle reduced B4
   clipped error19.8248%, yet S4 did not recover that gap. SC-V1.1 KITTI08 has
   A4/oracle errors1.269984013/1.226284942, an absolute gap0.043699071, with exactly
   10 discrepant positives meeting the declared headroom minimum. Do not present
   the small08 denominator as a large available opportunity.
2. **The fixed extra observations do not improve confirmation ranking.** On08,
   A4/S4 strict successes are33/31 out of75; clipped errors1.269984013/1.400363980.
   S4 worsens error by0.130379967, so its normalized gap recovery is-298.3587%.
   The large negative percentage reflects a small oracle gap; the absolute
   degradation and counts are more interpretable. R4 error1.393695261 is also
   below S4. The full predeclared screen fails.
3. **Simple transport repair does not rescue this score.** Evaluator-only G4,
   using GT local transport, has31/75 strict successes and error1.402462151.
   This does not support local odometry error as the sufficient explanation for
   the observed ranking failure. It is not a certificate of perfect sensor/GT
   accuracy or proof that motion uncertainty never matters.
4. **Preserving the support views has no demonstrated useful confirmation
   advantage here.** P4/P4x2 have32/75 successes and error1.401031220. Their scores
   and decisions are identical; P4x2 matches S4 query count, not exact runtime.
   Neither pooling nor the separate-view S4 meets the useful-support screen.
5. **Ranking and acceptance remain different problems.** On08 A4/S4 both accept
   17 correct positives and10 incorrect transforms. These are deliberately
   stratified case-control counts, not deployment false-loop prevalence. Even
   GT pose-oracle selection followed by the unchanged gate gives16 correct
   accepts and10 incorrect accepts; ranking gains cannot be equated with safe
   accepted-loop gains under that gate. No rejection threshold was fitted.

Confirmation08 S4-minus-A4 mean error changes are+0.386385823 in ambiguous
positives,+0.005934261 in low overlap and-0.001180184 in ordinary revisits.
The adverse contribution is concentrated in ambiguous positives here, whereas
the prior02 S4-versus-B4 diagnosis emphasized low overlap. The comparators differ;
do not claim the same mechanism or that low overlap alone explains both runs.

Discovery00 recovered26.8250% of its A4/oracle gap but introduced an incorrect
acceptance relative to officialR4; it also failed the full screen. Confirmation
was neither tuned nor replaced after that discovery result. Both findings remain.

## What remains worth investigating

The corrected baseline is a defensible engineering foundation. New research
should target a clearly different failure mechanism rather than rename the
current selector. The most concrete candidate for discussion is whether adding
short-submap context **during proposal generation** increases correct-hypothesis
availability relative to frozen anchor-only RAP under officialR4 and matched
data/budget controls. A separate rejection question is also possible, but must
retain correct-accept coverage and reject-all comparisons instead of optimizing
only incorrect acceptance. Neither direction is selected or started here.

The next owner discussion should choose one bounded question from these distinct
mechanisms. Prepare a prospective protocol only after that choice, with exact
fresh confirmation data, sample minima, realistic compute controls and a stop
rule. Do not automatically launch both directions or resume neural training.
All00/02/08 are now development evidence. NCLT remains reserved for external
evaluation; public-download authorization persists and no identity may be invented.
Current thesis drafting stays paused. No claim of CAS publication readiness.

## Evidence and integrity

- [SC-V1.1 final report](../2026-09-14/support-control-02/REPORT.md)
- [SC-V1.1 decision](../2026-09-14/support-control-02/decision.json)
- [SC-V1.1 independent/final validation](../2026-09-14/support-control-02/validation.json)
- [HL-V2 final report](../2026-09-14/hl-v2/pilot-01/REPORT.md)
- [HL-V2 post-hoc diagnosis](../2026-09-14/hl-v2/diagnostic-01/REPORT.md)

SC-V1.1 checked800 immutable bank files,2000 independent selector outcomes and796
rehashed raw scans. Original parent, protocol, source and membership identities
remain unchanged. No production changes or running experiment remains.
