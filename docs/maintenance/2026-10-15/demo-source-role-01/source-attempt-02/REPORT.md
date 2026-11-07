# DSR0 Demo Source And Default Reference Roles

Status: VALIDATED_EXISTING_DEMO_SOURCE_AND_DEFAULT_REFERENCE_ROLE_AUDIT_COMPLETE.

Complete existing namespace:27 directories/156 point-cloud files,151PLY+5PCD,
478400579bytes.214 frozen identities; all bytes and bounded format headers
independently verified without decoding coordinates. No external reference
sidecar exists within this exact root. This is not a global absence or a claim
that PCD VIEWPOINT authenticates cross-scan truth. See headers_and_roles.json.

Default demo source selects direct lowercase .ply only:26 directories contain
PLY; lidar_scan_oxford contains5PCD only and is not admitted by that enumerator.
No automatic conversion or scene selection was performed.

Seven complete static function citations establish the default path:
demo process_point_clouds calls save_processed_sample with3positional arguments,
without its optional source pose-copy directory; demo constructs val.txt and
trainer.test uses the val dataset. The folder loader assigns input sampled pcs
to pointclouds_gt. Its non-training transform uses identity rotations, derives
centering/scaling/translation references from those coordinates, and evaluator
consumes the resulting arrays. --eval_on controls table printing, not admission
of an external reference. No new runtime metric was executed.

If supplied clouds are already aligned, these references describe their supplied
alignment; if not, this path does not independently establish the correct pose.
This audit does not establish either physical state of the demo clouds or a
loader bug. PLY/PCD headers and scene names do not authenticate author/RegX byte
linkage, measurement frames, training exclusion or physical reference quality.
Do not report these default metrics as external-truth registration accuracy.

Original source assertion omitted parentheses emitted by ast.unparse. Its
181-identity freeze/source/INCOMPLETE/audit failure/full receipts remain.
Original30available files bound; separate variant changes1tuple-text assertion
plus routes/evidence binding/aggregate accounting only. Five enclosing CPU
attempts4success/1retained failure; Windows51.0011024s including imports/startup,
Linux-child36.511404056s/RSS23855104bytes/GPU0.
All original/new attempts share300s/128MiB/8MiB caps; setup/closure RSS UNKNOWN.
All9 prior markers plus original DSR0 marker stay. No model/pose/GT/new cohort,
no old family/fit/archive retry, source/default/reference change or acquisition.
Scientific goal unresolved. See NEXT_DESIGN.md for an explicit non-run contract.
