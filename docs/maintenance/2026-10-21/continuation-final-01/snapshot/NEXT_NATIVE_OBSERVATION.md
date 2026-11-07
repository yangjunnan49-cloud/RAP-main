# Prospective admission: native boundary observability

Status: DOCUMENTARY PLAN ONLY. This document does not launch or admit native payloads, reopen the closed queue4 candidate, or authorize a library/configuration change. The next question is where same-scheduler variation first becomes visible with sufficient input and state evidence. It is not a new RAP efficacy claim.

## Order of work

1. Integrate the immutable-nonce host-loss prototype with a synthetic owned workload and the boundary-signature prototype. Preserve source/config hashes, monotonic/UTC bounds, PID/PGID/start ticks and command hash, idempotent exit, and the original 12 GiB fresh-memory rule. Freeze one complete finite scope before running it, including preparation, faults, verification, artifacts and closure. A passing isolated prototype is not evidence that integration works.
2. Add an isolated, uninstalled recorder around the frozen Python/native call interfaces. Verify with controlled stubs that arguments are not rewritten, calls are neither duplicated nor dropped, returned object identity and exceptions are preserved, and no sorting/rounding silently changes data. Measure recording overhead separately. This demonstrates only stub behavior; native timing and state effects remain unproven.
3. Only after a separately frozen resource/cost/source protocol and its synthetic controls pass may a real same-scheduler native control be considered. Do not import packages or reconstruct a real trajectory merely to prepare that protocol. Use a complete stateful call sequence, never an isolated detector query presented as equivalent to its historical state.

## Recording contract

Record the actual typed contiguous bytes presented at each native boundary, in original row and call order: mapping points after float32 conversion; frame/timestamp identity; derived pose; split/reset event IDs; inherited map points; detector query cloud/history; finalized source/target positions and normals; candidate source/query IDs, inliers and initial guess including rejection paths; ICP transformation and acceptance counts; coarse variables, factors, fixed nodes and estimates. Bind installed source and native binary hashes, effective runtime/configuration and component lineage.

Separate prepared input from derived pose, recorded state, and output. Raw/prepared source identity must be established independently of summaries that include the new pose. Do not infer missing historical arrays from final trajectories. Existing P0 records do not supply all these bytes, so they cannot be described as an exact native replay bank.

Descriptor signatures must include dtype, shape, explicit endian, byte length and order. Event seals detect accidental changes but are not an independent proof of authenticity or provenance. If a native boundary has hidden state, keep state completeness UNKNOWN even if every recorded descriptor matches. Equal outputs in two runs establish only those observations; they do not prove determinism.

## Strong controls and interpretation

Use two independent fresh processes under the same serial scheduler, same frozen prepared input, runtime and effective settings, without seed, thread, point-order, loop-gate or optimizer changes. Predeclare the complete comparison and stop rules. A diagnostic focused on exposed sequence06 cannot support all-six benefit or generalization. Do not choose a favorable historical repeat as a new baseline.

Compare source/runtime bindings first, then event order, prepared bytes, derived inputs, recorded state and outputs. Report the earliest observed difference, not a causal root cause. If an input or preceding state differs, downstream output divergence cannot identify the native operator as the cause. If only output differs while complete internal state is unavailable, report output divergence with cause UNKNOWN.

Retain original equivalence thresholds and all unsuccessful controls. A diagnosed source of variability would require a new independently justified engineering decision; it does not retroactively qualify P0, permit queue/threshold/repeat rescue, or supply RAP novelty. No training, model acquisition, production/default installation, GT-driven tuning, outreach, Git mutation, scheduler or automatic reset continuation follows from this plan.
