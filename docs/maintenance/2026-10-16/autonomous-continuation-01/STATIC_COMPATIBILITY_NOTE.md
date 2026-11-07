# Focused static follow-up: no nonzero softcap path identified

This is a read-only substantiation of RBA0, not a new experiment or a second
compatibility query. The concrete question was whether the local SDPA helper's
unused softcap argument can be traced to a nonzero value in the historical
native-model construction that failed numerical gates.

The examined source path is native_conditioned_comparison.model aliasing
native_pose_fit.model, which calls native_output_capability.load_model. That
loader composes RAP_inference with model=rap_12 and fixed sampling overrides,
then instantiates the model before loading the strict state dict. The reviewed
RAP_inference, rap_12 and point_cloud_dit_12 YAMLs contain no softcap override.
PointCloudDiT declares softcap=0.0 and passes it to DiTLayer. Its dropout source
configuration is 0.0. No model construction was executed for this note.

All eight selected current source/config identities match their exact NBR02
freeze entries; STATIC_CONFIGURATION_CHECKS.json records them. RBA0 already
recorded zero softcap configuration lines. This follow-up strengthens the source
chain reading; it is not a newly discovered cause or a reopened direction.
There is no demonstrated nonzero softcap application in this examined route.
Do not infer an actual nonzero-cap mismatch from the unused argument alone.

This does not authenticate external FlashAttention implementation/version,
library dispatch, numerical equality or full runtime equivalence. It does not
prove a unique cause of finite-precision direction gaps, nor repair NOC4/NMR/FPC.
It does not authorize a new backend/softcap/precision/optimizer experiment.
Stop this static explanation branch without changing the frozen model source.

The initial active wait was intentionally ended after its retained observations
to perform this independent source check. Its observed 27%/29% usage and roughly
9.0 GB headroom are preserved; neither observation is exhaustion or a guard pass.
C0 stages remain unstarted. Resource eligibility is still the dependency.
