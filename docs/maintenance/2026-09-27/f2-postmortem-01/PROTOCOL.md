# F2 saved-result diagnostic protocol

Declared before the new diagnostic aggregates are computed. This is a
post-hoc, observed-development description of the completed F2 banks, not a
prospective method screen, confirmation set, new model result, or route rescue.

## Inputs and cohorts

Read only `f2-structured-dev-01/{00,08}/evaluator_only_decisions.json`,
`gates.json`, `metrics.json`, `decision.json`, and `validation.json`. Require
the F2 validator to have passed and the frozen decision to be
NO_DEVELOPMENT_MECHANISM_SIGNAL. Preserve each sequence's 100 saved pairs and
25 per stratum, order and pair identity. Report sequences separately. No raw
scan, GT file, generation array, inference process or graph optimization is
needed. Record SHA256 of all inputs and this protocol before analysis.

## Fixed descriptive arithmetic

For N, S and P, inspect each positive pair's selected R4 row and its OR4
diagnostic. Let `selected_correct` mean R4 `strict=true`; let
`candidate_available` mean OR4 `strict=true`. Partition all 75 positives into:

1. selected correct and accepted;
2. selected correct and rejected;
3. selected incorrect but an OR4 correct candidate exists (selection miss);
4. no OR4 correct candidate (proposal unavailable).

The first two categories sum to selected strict success. The last two sum
to selected strict failure. OR4 is GT-selected and is only an upper-bound
diagnostic; never call it an executable selector. For all 100 pairs count
incorrect accepts and confuser accepts. Within incorrect accepts, count
whether any correct candidate existed (on positives). For selected-correct
rejections, read the selected generation's saved common-gate values and
partition failures into overlap-only, distance-only and both, using the
frozen overlap>=0.7 and mean_dist<=2.5 rules. This describes the gate's
observed restriction, not a license to relax it.

Report paired N->S and N->P changes on the same positive identities: strict
gains/losses, correct-accept gains/losses, new/resolved incorrect accepts.
Also report by stratum, without treating reused scans as independent trials.
List the identities of changes and incorrect accepts for audit, but do not
highlight a few convenient examples as a population effect. Do not calculate
new optimized thresholds, weights, learned scores, or significance tests.

## Verification and decision use

Crosscheck all selected strict successes, correct accepts, incorrect accepts
and confuser accepts against F2 metrics exactly. Check the four-category
partition sums, OR4 dominance of R4 per pair, gate classification, 25-per-
stratum counts and stable pair ordering. Independently aggregate the primary
counts from the input rows a second time. A failure stops reporting and is
recorded without modifying F2 outputs. This diagnostic may justify a new
separately frozen question, but cannot select or validate a method by itself.
