# D0-AMENDMENT-01 — retain the exact saved final reference

The first frozen D0 runner stopped at KITTI00 pair 51, before a bank or
any evaluator labels existed. Its final-pose consistency check compared
the CPU float64 refit to F2's saved GPU float32 fit with a 1e-5 gate
mean-distance tolerance. A read-only diagnosis of all 200 pairs found
maximum pose matrix differences 4.2444e-5 (00) and 5.1211e-5 (08),
maximum mean-distance differences 2.4086e-5 and 1.4497e-5, and **zero
overlap differences**. Recomputing the gate on the original saved F2
poses matched F2 exactly. The worst00 pair was `00_1423_3594` (index50),
with reconstructed/saved mean distances 18.593694743806672 /
18.59371882946786. The worst08 pair was `08_827_2326` (index9), with
10.361855608516167 / 10.361870105172137. This is a numerical decode
convention mismatch, not a label- or outcome-derived adjustment.

The original protocol, runner and validator remain unchanged and hashed.
Version 2 retains the predeclared <=1e-4 pose-reconstruction check,
uses the exact original F2 saved selected final pose for the baseline
and gate, and uses CPU-refitted poses for all intermediate candidates.
The final saved gate still must match F2 within the original 1e-5 margin.
Version 2's independent validator permits the declared <=1e-4 difference
between decoded and saved final poses and checks the exact saved final
reference. The cohort, candidate set, fixed penultimate checkpoint, GT
separation, success criteria and resource caps are unchanged. No GT was
loaded and no score/pose bank was produced before this amendment.

Hash the original freeze, this amendment, the diagnostic helper and both
version-2 scripts in `amendment_freeze.json` before version-2 decoding.
Keep the original unsuccessful attempt's `INCOMPLETE` marker until the
amended bank and evaluation finish; do not call it an efficacy result.
