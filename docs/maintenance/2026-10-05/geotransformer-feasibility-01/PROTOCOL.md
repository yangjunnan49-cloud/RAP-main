# Official GeoTransformer isolated engineering feasibility

This is executability/provenance validation, not an efficacy experiment. No real
KITTI pair is processed here and no GT trajectory is read. Acquisition and a
CPU extension packaging build preceded this protocol; they are engineering
preparation, not model outputs. Preserve their failed attempts in the report.

Pin official release1.0.0 source commit73e1439a7a61cced595b67712f70e472bcbf76a4
and the official102131979-byte KITTI asset. Verify extracted source against
every archive member. The portable extension differs only by removal of an
unused CUDAContext header include; all numerical sources remain identical.
Dependencies easydict1.13/einops0.8.1/ipdb0.13.13 are workspace-local, no global
environment installation. The extension is CPU C++; model remains CUDA.

Freeze this protocol, runner, complete source/package/extension manifests and
checkpoint SHA before checkpoint loading or neural output. Restricted
`torch.load(weights_only=True)` only; require strict loading with no missing or
unexpected keys. No unsafe pickle fallback. Disable TF32 and use float32 eval
with no augmentation. Official config/architecture/registration numerical code
is unchanged. Empty config output directories are allowed, no source mutation.

Fixed synthetic seed7351; 2000 random points uniform[-25,25]^3. Known rotation
Euler[7,-4,17]degrees and translation[2,-1,.4]. Test official weighted Procrustes
maps source to reference with max matrix error<=1e-4; test extension stack
subsampling isolation and radius neighborhoods against independent NumPy/SciPy
calculations. Do not require a learned matcher accuracy claim on artificial data.

Run the same synthetic pair with identity and distant dummy transforms as the
model's bookkeeping `transform`, then repeat identity. Neighbor limits128 at
five levels are fixed for this synthetic executability test only. Require finite
proper rigid poses, predicted pose and actual matching outputs independent of
dummy transform (max absolute difference<=1e-6), repeatability<=1e-6. Saved
`gt_node_corr_*` bookkeeping may change; never use it as a real label. Report
all actual maxima, strict-load keys, time and memory. Cap synthetic model phase
600seconds, peak allocated GPU<6GiB, total artifacts<1GiB. A failure stops
real-pair work until a separately documented engineering correction passes.

Use an independent validator for manifest, known-transform fit, neighborhood
checks, dummy-label invariance, proper-pose checks and checkpoint load report.
Passing permits prospective real-pair design, not automatic method approval or
RAP novelty. Do not train, alter production/defaults, or sync Git.
