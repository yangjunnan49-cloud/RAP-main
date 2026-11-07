# FPC0 whole-native precision controls

Status: VALIDATED_BOUNDED_PRECISION_CONTROLS_COMPLETE. Decision: PRECISION_CONTROLS_RETAIN_DIRECTION_GAPS.

Same original checkpoint/443904 initialized parameters/synthetic fixture/fit00 noise/modes/tau1/backward factors. Full model uses original float32 weights/inputs without autocast and temporary12-layer float32 attention dtype under scoped math/IEEE. All four adapter linear boundaries and prefixes verified float32; actual math dispatch recorded. Every attention dtype/backend flag restored, parameters/frozen digest/modes preserved. S retains original float32 endpoint/residual arithmetic; D computes endpoint/residual in float64. These are distinct numerical controls; original default/NMR0 conditions and failed gates stay sealed.

Sixteen full-or-tail forwards/backwards/four explicit prefixes; every16 repeat/full-cache pair byteexact: True. All outputs/upstreams/trainable gradients/post parameters independently recounted. CPU Horn/direct loss max delta 4.86011231e-12; V upstream 2.27373675e-13;96 pose-output directional FD checks pass. Equations are independent; complete transformer backward is not independently implemented.

|Condition/direction|Step|CPU central difference|Saved gradient dot|Error|Bound|Corroborated|Original NMR error|
|---|---:|---:|---:|---:|---:|---|---:|
|S/V/final_mlp|0.001|8.04425326e-06|8.03159634e-06|1.26569199e-08|0.001|True|7.77329339e-09|
|D/V/final_mlp|0.001|8.04418512e-06|8.03158124e-06|1.26038877e-08|0.001|True|7.77329339e-09|
|S/V/final_mlp|0.0003|7.98460557e-06|8.03159634e-06|4.69907743e-08|0.001|True|3.62614084e-08|
|D/V/final_mlp|0.0003|7.98435376e-06|8.03158124e-06|4.72274796e-08|0.001|True|3.62614084e-08|
|S/V/final_mlp|0.0001|8.01264832e-06|8.03159634e-06|1.8948021e-08|0.001|True|9.73447962e-09|
|D/V/final_mlp|0.0001|8.01528268e-06|8.03158124e-06|1.62985566e-08|0.001|True|9.73447962e-09|
|S/V/LoRA_B|0.001|-1.54386726e-07|-1.37567912e-07|1.68188141e-08|0.001|True|4.585078e-06|
|D/V/LoRA_B|0.001|-1.54693985e-07|-1.37567892e-07|1.71260926e-08|0.001|True|4.585078e-06|
|S/V/LoRA_B|0.0003|-2.33436973e-07|-1.37567912e-07|9.58690619e-08|0.001|True|1.56009295e-05|
|D/V/LoRA_B|0.0003|-2.32907385e-07|-1.37567892e-07|9.53394923e-08|0.001|True|1.56009295e-05|
|S/V/LoRA_B|0.0001|-2.61479727e-07|-1.37567912e-07|1.23911815e-07|0.001|True|2.53308795e-05|
|D/V/LoRA_B|0.0001|-2.62893691e-07|-1.37567892e-07|1.25325799e-07|0.001|True|2.53308795e-05|
|S/P/final_mlp|0.001|42.4815976|42.3295568|0.152040799|2.11647784|True|0.519990185|
|D/P/final_mlp|0.001|42.4754675|42.3295539|0.145913515|2.1164777|True|0.519990185|
|S/P/final_mlp|0.0003|41.6654055|42.3295568|0.664151339|2.11647784|True|1.09542928|
|D/P/final_mlp|0.0003|41.66162|42.3295539|0.66793391|2.1164777|True|1.09542928|
|S/P/final_mlp|0.0001|46.8881033|42.3295568|4.55854646|2.11647784|False|3.89769532|
|D/P/final_mlp|0.0001|46.9947048|42.3295539|4.66515089|2.1164777|False|3.89769532|
|S/P/LoRA_B|0.001|0.317977151|1.33210495|1.0141278|0.0666052475|False|23.3295405|
|D/P/LoRA_B|0.001|0.320241053|1.33210346|1.01186241|0.0666051732|False|23.3295405|
|S/P/LoRA_B|0.0003|-4.37865691|1.33210495|5.71076186|0.0666052475|False|121.672865|
|D/P/LoRA_B|0.0003|-4.37728447|1.33210346|5.70938793|0.0666051732|False|121.672865|
|S/P/LoRA_B|0.0001|-0.773180915|1.33210495|2.10528586|0.0666052475|False|76.8358243|
|D/P/LoRA_B|0.0001|-0.796999432|1.33210346|2.1291029|0.0666051732|False|76.8358243|

ConditionS: 8/12 fixed whole-direction records corroborated; conjunction False.

ConditionD: 8/12 fixed whole-direction records corroborated; conjunction False.

Twenty-four additional full forwards shared by S/D objectives; fixed original vectors/three step sizes/signs, every temporary parameter perturbation and output archived, all parameters restored after each call, zero direction backwards/optimizer. V absolute1e-3 criterion is coarse relative to tiny derivatives; passing it does not demonstrate relative accuracy. No step/precision condition selected posthoc for a fit and no tolerance adjusted. FP32 model jointly changes many operators; the S/D contrast isolates endpoint/objective arithmetic within that model, not every source of historical mismatch. Independent direction losses/perturbations/dots reproduced.

686 frozen identities, 5 supervised scientific children, 122.086378s incl imports, RSS 2701664256, GPU allocated/reserved 2173726720/2323644416 bytes.900s/6GiB RSS/6GiB GPU/256MiB new caps pass; full child/Windows exits, 0 logging retries/0 gaps. Setup RSS unknown; standard-library final closure separate; old caps/gaps unchanged.

No optimizer calls/retained updates/fits/new noise/real/nearby/trajectory, no functional-step descent/native learning/physical/generalization/system gain/novelty or unique historical cause. Original NOC4 loss-increase/P mismatch/INCOMPLETE, failed original NBR marker, CCR0 stop and all old seals remain. No production/default/backbone/reference/manuscript/install/acquisition/restart/commit/Git sync. Both original HEADs/branches/two-nine dirty sets preserved.
