# FTI0 Exact Frame And Time Ambiguity Controls

Decision: TRAJECTORY_SHAPE_AND_STORED_TIME_STRUCTURE_DO_NOT_AUTHENTICATE_PHYSICAL_CONVENTIONS. All four predeclared controls pass exactly.

Sensor-frame counterexample: four planar positions are identical under a fixed right-composed90deg sensor orientation, while all three relative translations and rotations differ by exact conjugation. A horizontal position trace alone therefore does not identify local sensor axes. World-gauge counterexample rotates the same xy trace into xz with all three relative sensor poses exactly unchanged. No independent gravity or reference convention was supplied by these synthetic examples.

Clock counterexample uses four0.1s nominal stamps: a7s common offset retains increments/order/IDs; a rate factor2 retains order/IDs. Fixed four-return XYZI and one scan stamp also admit two distinct increasing per-return time lists. These are exact examples of non-identification, not an actual clock error, rate correction, motion estimate or assigned times for real points.

Every actual POSS00 timestamp row was parsed as Decimal:36924 finite, strictly increasing values, first0.000000/last2461.503,132 distinct exact increments, not an arithmetic grid. No hardware origin/rate/trigger, cross-sensor delay or per-return timing is authenticated from that structure. In particular, the synthetic0.1s example is not an assumption about these actual files.

Independent validator rebuilds every matrix inverse/product/conjugation using its own tuple/column implementation and sequential timestamp traversal. Twelve synthetic poses and nine relative-pose records satisfy their exact equations without tolerances or optimization. Current source descriptions/calibration readme/POP0 and RPC0 stops remain bound.

All22 frozen identities match; three successful supervised CPU children: Windows7.966179200s including startup/imports, child3.958054782s after bootstrap, peakRSS28704768bytes/GPU0. 300s/128MiB/8MiB caps pass, full native/Windows exits and host observations, 0 logging retries/0 gaps. Ordinary preparation RSS unknown; stdlib closure separate; historical gaps remain.

This does not prove the current POSS loader or supplied calibration wrong, choose a new convention/reference, identify physical truth or the09 conflict cause. No real reference-pose/point coordinates, new model/learner/registration/pose metric, physical/system/generalization gain or acquisition/install/production/default/backbone/manuscript/restart/commit/Git sync. RPC0/BRF0/old retired families remain stopped.
