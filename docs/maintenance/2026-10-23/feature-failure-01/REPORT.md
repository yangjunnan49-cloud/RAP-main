# FF1 feature-wrapper exception behavior confirmed

Ten controls pass: four NumPy/Tensor and explicit/default keypoint row-routing cases, both model-exception paths, both empty-input paths, and strict rejection of nonfinite/wrong-shaped descriptors. The source wrapper ran eight times with six synthetic descriptor-stub calls. No actual feature model, RAP model, checkpoint, raw point file or private reference was used; CUDA remained uninitialized.

Confirmed source defect at dataset_process/extract_sample_features.py:150: after a model exception, the fallback unconditionally calls keypoints.dim(), which does not exist on a NumPy array. It raises AttributeError while handling the original RuntimeError, masking that error. With Tensor input, the source instead returns zero descriptors. The isolated strict boundary rejects those zeros. Empty inputs produce shape(0,) rather than a valid model descriptor matrix and are not admitted. These are exact source failure-path observations with stubs, not a claim about real descriptor quality.

No production patch is applied. A minimal future candidate could use the ndim property shared by NumPy and Torch in that fallback expression; the zero-descriptor result must still be rejected by a cooperating inference admission boundary. A source fix alone must not relabel failed extraction as success. The RI1 GPU stop remains closed and unretried.

Worker peak RSS485371904bytes; external watcher observed567222272bytes, below1GiB. Host/watcher/worker exits succeeded under fresh12GiB/2s leases and30s stage cap. RUNTIME_CLOSE.json records zero exact matches for the four continuation helper groups and restoration of WSL Stopped. Research remains UNRESOLVED/manuscript PAUSED; no defaults/install/Git/outreach/scheduler/goal-status changes.
