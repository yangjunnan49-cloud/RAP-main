"""Audit available NOC4 artifacts on CPU; no new neural or CUDA calls."""
import json
import resource
import time
import numpy as np
import torch
import native_conditioned_comparison as r
import validate_native_pose_fit as v
c=r.c
start=time.monotonic()
assert not torch.cuda.is_initialized()
f=r.check();counts=r.old_deliveries();r.noise_check()
z=r.load(r.BASE/'bank/synthetic_fixture.npz')
assert c.sha(r.BASE/'bank/synthetic_fixture.npz')==c.sha(r.n.RETRY/'bank/synthetic_fixture.npz')
math_again=r.old.mathematical(z)
assert v.difference(math_again,c.read(r.BASE/'mathematical_preflight.json'))<1e-10
target_cost,target_terms=v.objective(z,z['target']);assert target_cost<1e-8
initial_cost,initial_terms=v.objective(z,z['cond'])
with torch.no_grad(): raw,terms=r.o.objective(torch.tensor(z['cond']),torch.tensor(z['cond']),
    torch.tensor(z['centers']),torch.tensor(z['scale']),torch.tensor(z['truth']))
delta=max(abs(float(raw)-initial_cost),v.difference(initial_terms,{k:float(x) for k,x in terms.items()}))
assert delta<1e-7
for row in r.noise_rows():
    noise=r.load(r.BASE/'bank/noise'/f"{row['name']}.npz")['noise']
    assert noise.shape==(3000,3) and noise.dtype==np.float32 and np.isfinite(noise).all()
assert not (r.BASE/'preflight/V').exists() and not (r.BASE/'preflight/P').exists()
assert not (r.BASE/'bank/synthetic_V').exists() and not (r.BASE/'bank/synthetic_P').exists()
assert not (r.BASE/'bank/synthetic_predictions').exists()
repos=r.n.noc.git_state();assert repos==f['repositories']
for name in ('preflight','preflight-external-exit'):
    p=r.BASE/name
    if p.exists(): assert not any(p.rglob('*'))
assert not torch.cuda.is_initialized()
usage=dict(wall_seconds=time.monotonic()-start,RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
assert usage['wall_seconds']<120 and usage['RSS_peak_bytes']<2*2**30
result=dict(passed=True,audit_scope='available artifact integrity, independent CPU mathematics and stopped execution boundary',
    freeze_entries=len(f['files']),old_delivery_counts=counts,noise_arrays_integrity_checked=24,
    noise_generator_replay=False,fixture_byteexact=True,mathematics_reproduced=True,
    independent_Horn_exact_target_cost=target_cost,independent_Horn_identity_cost_delta=delta,
    no_neural_backward_or_optimizer_evidence=True,no_probe_or_fitted_parameters_written=True,
    retained_updates=0,native_fitting_gate_not_reached=True,neural_learnability_not_evaluated=True,
    repository_state_preserved=True,repositories=repos,GPU_used=False,**usage)
c.save(r.BASE/'validation_execution_stop.json',result)
c.save(r.BASE/'validation_execution_stop_seal.json',dict(validation_sha256=c.sha(r.BASE/'validation_execution_stop.json'),
    freeze_sha256=c.sha(r.BASE/'freeze.json'),noise_seal_sha256=c.sha(r.BASE/'noise_seal.json')))
print('NOC4 available artifact and stop audit VALIDATED',result,flush=True)
