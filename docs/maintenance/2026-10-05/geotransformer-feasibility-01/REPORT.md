# Validated isolated official GeoTransformer feasibility

Decision: **PASS_ISOLATED_SYNTHETIC_FEASIBILITY**. This verifies executable
engineering and label isolation; no real pair efficacy was measured here.

Official release1.0.0, source commit
`73e1439a7a61cced595b67712f70e472bcbf76a4`. API asset63888702,
KITTI checkpoint102131979bytes, SHA256
`39cd6a01de6430c656eb8c9d67997f334f0a38c446dd8884b16a654e2b233237`.
Release/source metadata and source archive are retained locally. Every extracted
source file matches the archive. [Official release](https://github.com/qinzheng93/GeoTransformer/releases/tag/1.0.0)
is the acquisition authority. Dataset split declarations do not authenticate
actual weight training membership.

The first direct asset request timed out; official API asset recovery succeeded.
The first CPU extension attempt failed on an unused CUDA header dependency.
V2 copies the extension and removes only that unused include; all numerical
source remains byte-identical. CPU build31.389s. Original official source and
failed build directory remain. This is a documented packaging adaptation,
not exact reproduction of the legacy tested software stack.

Workspace-local easydict1.13,einops0.8.1,ipdb0.13.13 wheels and extracted
packages avoid installing into RAP's Python environment. Runtime is local
Python3.10/Torch2.7/CUDA12.8/Open3D0.19, model CUDA float32 with TF32 off.
Official numerical architecture and config remain unchanged.

Protocol and257 identities froze before checkpoint loading/neural outputs.
Restricted weights-only checkpoint read and strict state load passed all316
state entries, zero missing/unexpected keys. Synthetic known source->reference
transform maximum matrix error1.49e-7. Independent SVD fit differs by1.42e-7.
Independent radius validation covers4000 rows; voxel-centroid validation covers
3996 points. Identity vs distant dummy label and repeat inference yield exact
zero delta for all seven saved prediction/matching fields. Artificial-cloud
registration accuracy is not used as an efficacy claim.

Synthetic phase13.062s, allocatedGPU4.815GiB, peakRSS2.588GiB, caps passed.
Independent validator passed six groups. `preflight_freeze.json`,
`preflight_results.json`, `validation.json` and synthetic bank preserve evidence.
No GT trajectory was read. No training, production/default edit or Git sync.

Next authorized step is the separately frozen all71 online equal-point
comparator. E0's cap is4000 **per scan**, up to8000 per pair; the old proposed
2000-per-scan wording was corrected before any real matcher prediction.
