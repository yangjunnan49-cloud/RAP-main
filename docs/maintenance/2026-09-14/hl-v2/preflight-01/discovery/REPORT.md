# HL-V2 amended-support preflight

PASS. Ten frozen KITTI00 discovery pairs across all four strata, K4, yielded
40 valid SE(3) hypotheses and40 complete support scores. No CUDA OOM or
registration failure. Pair wall sum40.890549s; peak allocated4,785,265,152 bytes
and reserved9,661,579,264 bytes. Timings include preprocessing, features,
generation, official rigidity statistics, raw-support scoring and result writes.

The independent data validator reproduced causal raw-scan support with a
separate cumulative-distance search. Transform transport convention is unchanged
from the HL0 synthetic checks. No future frames, GT motion or generating anchors
enter support. Raw scan identity does not imply independent scene/noise.

Request reordering reproduces the first saved transform exactly. Removing the
instance-only official-rigidity observation hook reproduces it exactly as well.
The hook calls the existing RAP fit/rigidity metric for each endpoint-trajectory
step, averages the metric, and returns the original generated trajectory.
It does not modify upstream code, inputs or RNG. IEEE rigid-fit protection and
all learned anchor features remain enabled. Invalid/all-zero features are
treated as explicit failures instead of silently accepting feature fallback.

Two extra requests are reproducibility checks only and are not selected into
the bank. The40 preflight hypotheses are not substitutes for the scored pilot.
No H1/H2 result is claimed here. Sources, seeds, input hashes, memory/timings and
bank hashes are retained beside this report. Initial role order interleaves
fixed strata without changing sample membership or per-request seeds.
