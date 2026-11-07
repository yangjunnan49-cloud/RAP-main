# Local SDPA Port Derivative Controls: Review Brief, Not Sent

## Identity And Scope

Local RAP-main HEAD4055d929c594b0033aafc6eed339c910369eef55, branch
codex/meeting-20260930, original two tracked dirty files preserved. Exact tested
layer SHA256e8e7caabe1da47b8c8aefea0db58ec5ffb910be8fc01b7a541ca6fec345618e8.
The12-layer weight SHA2560c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200
matches [author-linked hosted metadata](https://huggingface.co/YuePanEdward/RAP/blob/main/rap_model_12.ckpt)
and every selected historical freeze. PRI0 independently hashes all local bytes.

Local layer is a PyTorch SDPA replacement. The observed
[author layer source](https://github.com/PRBonn/RAP/blob/main/rectified_point_flow/flow_model/layer.py)
uses external FlashAttention varlen calls. Web source has a4months-old crawl
label and mutable main; no immutable remote commit/runtime was authenticated.
We have not tested that external runtime. Identical checkpoint tensors do not
make these numeric functions or backward behavior equivalent. No upstream
FlashAttention bug, current official release failure or defective weight claim.

Historical captured packages:torch2.7.0+cu128,numpy1.26.4,scipy1.15.2. No claim that
CUDA toolkit/driver/GPU identity or current installed runtime is fully specified
by those package labels. Full precise environment/backend provenance is a
requirement for a future differently scoped reproduction, not guessed here.

## Existing Bounded Observations

All controls use the old exposed copied-descriptor synthetic scene/fit00 noise,
443904 initialized local adaptation trainables, no physical reference validation.

|Archived condition|Repeat behavior|Direction-gate outcome|
|---|---|---|
|NBR02 local default fp16|V exact; P full repeat6219gradient values differ, cached6143|No admitted native fit|
|NMR0 local scoped math/fp16|All instrumented full/cache repeats exact|8/12 saved directions corroborated; conjunction fails|
|FPC0 local FP32, S objective|Full/cache repeats exact|8/12; conjunction fails|
|FPC0 local FP32, D objective|Full/cache repeats exact|8/12; conjunction fails|
|DTC0 fixed-prefix double tail|Repeated shadow records exact|12/12 for changed shadow function only|

Forward and endpoint upstream arrays in all8NBR02 comparisons match exactly.
The8pair scalar counts and48distinct saved direction records are independently
reconciled in attribution.json/validation.json. This new audit does not decode
old NPZs or replay models/FDs; it verifies selected old sealed records, not the
entire old binary bank. Old original NOC4/NBR/HFIT/LCP incomplete stops persist.

Passing repeatability is not derivative corroboration. Failing fixed FD bounds
in finite precision is not proof that autograd is mathematically wrong; numerical
quantization/step effects remain possible. No unique cache/kernel/precision
cause is identified. The coarse V absolute tolerance must not be advertised as
relative derivative accuracy. DTC0/SFC0/shadow fitting change the function and
cannot repair or stand in for original local native conditions.

## Review Questions And Next Gate

1. Which implementation, library versions, attention dtype/dispatch and precision
   contract are intended for adapting the released inference checkpoint?
2. Is there an author-supported differentiable training/adaptation entry point,
   with exact checkpoint/config/source identity and a small gradient reference?
3. Can authors provide exact existing-demo byte manifests and input-to-world
   reference construction, separately from training-membership disclosure?

This is a local review artifact, not a submitted issue or email. No package,
checkpoint substitution, new backend run or production change follows. Any
future external-runtime comparison needs explicit source/environment/acquisition
authorization, isolated prospective resource limits, complete input commonality,
independent output/objective checks and fixed whole-direction conjunctions.
No old failed directory replay, step/tolerance selection, radius/head rescue or
claim of physical/system/novelty gain. Original research goal unresolved.
