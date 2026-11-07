# DTC0 fixed-prefix double trainable-tail derivative control

Status: VALIDATED_FIXED_PREFIX_DOUBLE_TAIL_CONTROL_COMPLETE. Decision: FIXED_PREFIX_DOUBLE_TAIL_DIRECTION_CORROBORATION_PASS.

Frozen archived FPC0 D_V/D_P float32 first10-layer prefixes match exactly and are promoted to double. Original initialized443904 trainable values/checkpoint/modes retained, last2 complete layers/final_mlp promoted to double, math/IEEE/no autocast. Original tail layer-loop AST independently matches, with sole final input float-to-double change. Four original parameter-free Timesteps modules still compute float32 constants, explicitly promoted via temporary hooks; no derivative wrt timestep or fully double upstream claimed. All parameter values/dtypes, hooks, attention dtypes/backend flags/frozen digest/modes restored after scoped control.

Four shadow-tail backwards,0 whole-native/prefix forwards or optimizers/retained updates. V/P repeated outputs/upstreams/all gradients/post parameters byteexact: True. Independent CPU Horn/direct loss max delta 3.97903932e-13; V upstream 4.23516474e-22;24 P output-direction FD checks pass. No whole/full-cache function-equivalence claim.

|Direction|Step|CPU central difference|Saved gradient dot|Error|Stricter bound|Corroborated|Prior FPC D error|
|---|---:|---:|---:|---:|---:|---|---:|
|V/final_mlp|0.001|8.03144268425e-06|8.0314294683e-06|1.32159504e-11|4.01571473e-07|True|1.26038877e-08|
|V/final_mlp|0.0003|8.03143065771e-06|8.0314294683e-06|1.18941178e-12|4.01571473e-07|True|4.72274796e-08|
|V/final_mlp|0.0001|8.03142960025e-06|8.0314294683e-06|1.31947611e-13|4.01571473e-07|True|1.62985566e-08|
|V/LoRA_B|0.001|-1.37566992855e-07|-1.37566993031e-07|1.76278382e-16|6.87834965e-09|True|1.71260926e-08|
|V/LoRA_B|0.0003|-1.37566992892e-07|-1.37566993031e-07|1.39855966e-16|6.87834965e-09|True|9.53394923e-08|
|V/LoRA_B|0.0001|-1.3756699251e-07|-1.37566993031e-07|5.21020792e-16|6.87834965e-09|True|1.25325799e-07|
|P/final_mlp|0.001|42.3302306552|42.3302304543|2.00968628e-07|2.11651152|True|0.145913515|
|P/final_mlp|0.0003|42.3302304728|42.3302304543|1.85486257e-08|2.11651152|True|0.66793391|
|P/final_mlp|0.0001|42.3302304465|42.3302304543|7.78882736e-09|2.11651152|True|4.66515089|
|P/LoRA_B|0.001|1.33213872736|1.33213872591|1.44934642e-09|0.0666069363|True|1.01186241|
|P/LoRA_B|0.0003|1.33213872289|1.33213872591|3.02707259e-09|0.0666069363|True|5.70938793|
|P/LoRA_B|0.0001|1.33213875515|1.33213872591|2.92315674e-08|0.0666069363|True|2.1291029|

12/12 predeclared double-control direction checks corroborated.24 temporary symmetric shadow forwards, same original vectors/three steps/signs; all perturbations/output costs/dots independently rebuilt, loss max delta 9.86233317e-12. Every temporary parameter value restored per call and original float32 dtype restored on context exit. A positive result is bounded derivative feasibility of this changed fixed-prefix function. It does not repair former native conditions, isolate one unique precision cause, implement independent complete transformer backward, certify functional-step descent, fit/generalization or system/physical gain.

859 frozen identities, 5 successful supervised scientific children, 98.515955s incl imports; RSS 2435121152, GPU allocated/reserved 4052324864/4240441344 bytes.900s/6GiB RSS/8GiB GPU/256MiB prospective caps pass, full child/Windows exits, 0 retries/0 logging gaps. Setup RSS unknown; standard-library closure separate, all old caps/gaps remain.

Original NOC4 loss-increase/P replay/INCOMPLETE, original failed NBR marker, NMR/FPC failed directions and CCR0 stop remain. No optimizer/retained updates/functional step/fit/new noise/real/nearby/trajectory, no production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.
