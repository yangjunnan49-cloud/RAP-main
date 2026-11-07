# ADR0 fixed-prefix double trainable-tail derivative control

Status: VALIDATED_ACTIVATED_ADAPTER_DERIVATIVE_CONTROL_COMPLETE. Decision: ACTIVATED_ADAPTER_ALL_GROUP_DERIVATIVE_CORROBORATION_PASS.

Frozen archived FPC0 D_V/D_P float32 first10-layer prefixes match exactly and are promoted to double. Original checkpoint/modes/nominal443904 trainables retained; only four B matrices temporarily activated with target-independent seed2026101307/global Frobenius norm1e-3; original values restored afterwards, last2 complete layers/final_mlp promoted to double, math/IEEE/no autocast. Original tail layer-loop AST independently matches, with sole final input float-to-double change. Four original parameter-free Timesteps modules still compute float32 constants, explicitly promoted via temporary hooks; no derivative wrt timestep or fully double upstream claimed. All parameter values/dtypes, hooks, attention dtypes/backend flags/frozen digest/modes restored after scoped control.

Four shadow-tail backwards,0 whole-native/prefix forwards or optimizers/retained updates. V/P repeated outputs/upstreams/all gradients/post parameters byteexact: True. Independent CPU Horn/direct loss max delta 2.75690581e-12; V upstream 4.23516474e-22;24 P output-direction FD checks pass. No whole/full-cache function-equivalence claim.

|Direction|Step|CPU central difference|Saved gradient dot|Error|Stricter bound|Corroborated|Prior FPC D error|
|---|---:|---:|---:|---:|---:|---|---:|
|V/final_mlp|0.001|8.03050352791e-06|8.03049031193e-06|1.32159829e-11|4.01524516e-07|True|1.26038877e-08|
|V/final_mlp|0.0003|8.03049150148e-06|8.03049031193e-06|1.18954945e-12|4.01524516e-07|True|4.72274796e-08|
|V/final_mlp|0.0001|8.03049044393e-06|8.03049031193e-06|1.32003405e-13|4.01524516e-07|True|1.62985566e-08|
|V/LoRA_B|0.001|-1.37646820334e-07|-1.37646820473e-07|1.39097739e-16|6.88234102e-09|True|1.71260926e-08|
|V/LoRA_B|0.0003|-1.37646820226e-07|-1.37646820473e-07|2.47376766e-16|6.88234102e-09|True|9.53394923e-08|
|V/LoRA_B|0.0001|-1.37646821033e-07|-1.37646820473e-07|5.60127959e-16|6.88234102e-09|True|1.25325799e-07|
|V/LoRA_A|0.001|-1.74105280262e-11|-1.74105911599e-11|6.31337407e-17|1e-12|True|NA|
|V/LoRA_A|0.0003|-1.74105561195e-11|-1.74105911599e-11|3.50404813e-17|1e-12|True|NA|
|V/LoRA_A|0.0001|-1.74125198242e-11|-1.74105911599e-11|1.92866423e-15|1e-12|True|NA|
|P/final_mlp|0.001|42.3326869508|42.3326867514|1.99468992e-07|2.11663434|True|0.145913515|
|P/final_mlp|0.0003|42.3326867727|42.3326867514|2.13217248e-08|2.11663434|True|0.66793391|
|P/final_mlp|0.0001|42.332686771|42.3326867514|1.96164152e-08|2.11663434|True|4.66515089|
|P/LoRA_B|0.001|1.33202973348|1.33202973289|5.86203974e-10|0.0666014866|True|1.01186241|
|P/LoRA_B|0.0003|1.332029756|1.33202973289|2.31056718e-08|0.0666014866|True|5.70938793|
|P/LoRA_B|0.0001|1.3320296965|1.33202973289|3.639044e-08|0.0666014866|True|2.1291029|
|P/LoRA_A|0.001|0.000400232607944|0.000400230314503|2.29344101e-09|2.00115157e-05|True|NA|
|P/LoRA_A|0.0003|0.000400241191301|0.000400230314503|1.08767973e-08|2.00115157e-05|True|NA|
|P/LoRA_A|0.0001|0.000400127930789|0.000400230314503|1.02383715e-07|2.00115157e-05|True|NA|

Original stored A gradients are zero; all16 activated A matrix records have nonzero finite gradients: True. Full independent local A/B products 32/32 pass; max delta 3.41060513e-13. This checks complete local linear derivatives, not complete transformer backward or Jacobian rank.
18/18 predeclared double-control direction checks corroborated.36 temporary symmetric shadow forwards, same finalMLP/B vectors plus predeclared A vector seed2026101308/three steps/signs; all perturbations/output costs/dots independently rebuilt, loss max delta 5.1159077e-12. Every temporary parameter value restored per call and original float32 dtype restored on context exit. A positive result is bounded derivative feasibility of this changed fixed-prefix function. It does not repair former native conditions, isolate one unique precision cause, implement independent complete transformer backward, certify functional-step descent, fit/generalization or system/physical gain.

1060 frozen identities, 5 successful supervised scientific children, 172.407348s incl imports; RSS 2625298432, GPU allocated/reserved 4052324864/4240441344 bytes.900s/6GiB RSS/8GiB GPU/1GiB prospective caps pass, full child/Windows exits, 1 retries/0 logging gaps. Setup RSS unknown; standard-library closure separate, all old caps/gaps remain.

Original NOC4 loss-increase/P replay/INCOMPLETE, original failed NBR marker, NMR/FPC failed directions and CCR0 stop remain. No optimizer/retained updates/functional step/fit/new noise/real/nearby/trajectory, no production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.
