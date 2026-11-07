# FTI0 Coordinate And Time Identifiability

Freeze source/data identities before numerical work. This is a measurement
identifiability control, not a repeated geometry/reference rescue experiment.
No real pose matrices, point clouds or new physical errors are evaluated.

Timestamp inspection: parse every nonempty POSS00 times.txt row as Decimal,
record count, strict increase, number of distinct increments, first/last value
and whether it is exactly an arithmetic grid. Do not infer hardware timestamps,
clock calibration or per-return acquisition timing from any result.

Four prospective exact Fraction/integer controls:

1. Sensor-frame ambiguity: four poses with planar world positions and changing
   yaw; right-compose a fixed zero-lever-arm90deg x-rotation. Both worlds retain
   exactly the same planar position trace and first translation, but their
   sensor-frame relative translation/rotation differ. Construct transformed
   relative poses independently and check the conjugation equation.
2. World gauge: left-compose a90deg x-rotation. The trace changes from xy-plane
   to xz-plane while every relative sensor pose is exactly unchanged. Without
   independent gravity/world convention, trajectory horizontality is not an
   authenticated sensor-frame label.
3. Clock ambiguity: a four-row nominal 0.1-second grid and a common offset of
   7 seconds have identical increments/order/row IDs but different physical
   epoch; scale2 changes rate while preserving monotonicity and row counts.
   This illustrates insufficiency of structure, not a measured local clock fault.
4. Within-scan ambiguity: fixed four-return XYZI values and identical scan stamp
   admit two different increasing per-return time assignments. A file with no
   point-time field cannot select between them. Do not synthesize/attach times
   to real points or make a deskew diagnosis.

Seal all controls and the timestamp census. A separate validator uses its own
exact matrix multiplication/inverse/conjugation, sequential Decimal traversal
and candidate reconstruction. Gate: all exact equalities hold, both changed
local poses differ in case1, changed plane case2, distinct clock/time choices
in cases3/4. No tunable tolerance or optimization is involved.

Consequence is limited: the cited argument/data schema do not uniquely identify
physical conventions. It neither establishes the local loader wrong nor chooses
a corrected convention/reference, and it does not reopen RPC0/09 diagnosis.
