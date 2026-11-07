# First bounded optimization experiment

Declared while the remaining core baseline runs execute, before refinement
outcomes. The owner prioritizes transition from auditing to metric improvement.

O1: RAP-initialized point-to-point ICP refinement. Use the four complete fresh
core runs' selected RAP transformations as initialization, identical scan pairs
and production geometric preprocessing (no learned features needed for ICP).
Open3D 0.19, correspondence 2.5 m, 100 iterations, relative fitness/RMSE 1e-6;
these match the earlier comparator without tuning. Every original attempted
pair with a completed RAP measurement is refined, even if RAP rejected it.
Record its own transform, overlap, mean distance, GT label and timing. Apply
the same fixed heuristic anew. No GT-based selection, no fallback to original
RAP, no per-sequence parameter choice. Keep relfloor + Huber and NMS 0.

Compare first-pose and rigid-aligned LiDAR APE and camera-frame KITTI drift
where applicable. This is a development experiment, not an independent test.
Do not change the production default based solely on the best sequence.
Advance the arm as promising only if first-pose APE improves on at least three
of four sequences, no sequence regresses by more than 5%, and no dangerous
edge is accepted. Keep failed/negative outcomes. This practical screen is not
a statistical test; report secondary metric regressions regardless of decision.

If O1 fails, preserve it and proceed next to a fixed candidate-coverage/budget
experiment on all four sequences. Do not reopen general auditing or optional
statistical work unless a new result exposes a specific correctness failure.
