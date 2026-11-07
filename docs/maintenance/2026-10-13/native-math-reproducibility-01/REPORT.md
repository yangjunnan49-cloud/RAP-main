# NMR0 whole-native scoped math attention prerequisite

Status: VALIDATED_WHOLE_NATIVE_MATH_PREREQUISITE_COMPLETE. Decision: MATH_REPEAT_EXACT_DIRECTION_CORROBORATION_FAIL.

Original synthetic3000-point known-transform/copy-descriptor fixture, fit00 noise,443904 original initialized trainables, exact mode contract, outer fp16/IEEE, original V/P objective/backward scales. All prefix/full/cache attention temporarily uses math SDPA; actual ATen math dispatch recorded for first full trace per arm and original backend flags restored. Eight instrumented backwards/two explicit prefixes;0 optimizer calls/retained updates. Frozen parameters/modes preserved, every trace parameter byteexact. This is a changed numerical condition; it does not replace production or imply default function equivalence.

|Comparison|Output differences|Endpoint upstream differences|Parameter gradient differences|Max parameter gradient delta|
|---|---:|---:|---:|---:|
|V_full1 / V_full2|0|0|0|0|
|V_cache1 / V_cache2|0|0|0|0|
|P_full1 / P_full2|0|0|0|0|
|P_cache1 / P_cache2|0|0|0|0|
|V_full1 / V_cache1|0|0|0|0|
|V_full2 / V_cache2|0|0|0|0|
|P_full1 / P_cache1|0|0|0|0|
|P_full2 / P_cache2|0|0|0|0|

|Math/default archived control|Endpoint max delta|Upstream max delta|Gradient max delta|
|---|---:|---:|---:|
|V_full1|0.00108289719|2.40643828e-07|1.01938494e-05|
|V_cache1|0.00108289719|2.40643828e-07|1.01938494e-05|
|V_full2|0.00108289719|2.40643828e-07|1.01938494e-05|
|V_cache2|0.00108289719|2.40643828e-07|1.01938494e-05|
|P_full1|0.00108289719|0.480957031|149.777344|
|P_cache1|0.00108289719|0.480957031|149.902344|
|P_full2|0.00108289719|0.480957031|149.652344|
|P_cache2|0.00108289719|0.480957031|150.027344|

Independent Horn/direct loss max delta 5.1159077e-12;48 output-direction finite differences and complete pair/backend census rebuilt. Local B products within one fp16 ULP: 32/32, scoped linear diagnostic, not independently implemented whole transformer backward.

|Whole-native direction|Step|CPU central difference|Saved gradient dot|Error|Predeclared bound|Corroborated|
|---|---:|---:|---:|---:|---:|---|
|V/final_mlp|0.001|8.38849701e-06|8.3962703e-06|7.77329339e-09|0.001|True|
|V/final_mlp|0.0003|8.43253171e-06|8.3962703e-06|3.62614084e-08|0.001|True|
|V/final_mlp|0.0001|8.40600478e-06|8.3962703e-06|9.73447962e-09|0.001|True|
|V/LoRA_B|0.001|-4.71095518e-06|-1.25877179e-07|4.585078e-06|0.001|True|
|V/LoRA_B|0.0003|1.54750524e-05|-1.25877179e-07|1.56009295e-05|0.001|True|
|V/LoRA_B|0.0001|-2.54567567e-05|-1.25877179e-07|2.53308795e-05|0.001|True|
|P/final_mlp|0.001|42.3574384|42.8774286|0.519990185|2.14387143|True|
|P/final_mlp|0.0003|43.9728578|42.8774286|1.09542928|2.14387143|True|
|P/final_mlp|0.0001|38.9797332|42.8774286|3.89769532|2.14387143|False|
|P/LoRA_B|0.001|-22.1663934|1.16314713|23.3295405|0.0581573563|False|
|P/LoRA_B|0.0003|122.836012|1.16314713|121.672865|0.0581573563|False|
|P/LoRA_B|0.0001|-75.6726772|1.16314713|76.8358243|0.0581573563|False|

Twenty-four additional full forwards,0 backwards/optimizers, fixed seed/group/step/sign, temporary parameter perturbations fully archived and restored exactly after each call. All vectors, perturbations, directional products and perturbed CPU costs independently reconstructed, max loss delta 6.3380412e-12. Corroboration 8/12; no step selection or tolerance repair. Finite precision can limit central differences; the observations do not identify a unique derivative/rounding cause or establish descent.

542 frozen identities, sealed default controls and old stops retained. 4 successful supervised scientific children, 161.371857s incl imports; peak RSS 3171844096, GPU allocated/reserved 2080926720/2287992832 bytes. New1200s/6GiB RSS/6GiB GPU/512MiB caps pass; full child/Windows exits, 0 logging retries/0 gaps. Higher new memory cap was prospective, not an old-budget amendment. Ordinary setup RSS unknown, final standard-library bookkeeping separate; old resource gaps unchanged.

Repeatability and derivative corroboration are separate prerequisites. No actual optimizer step, fitting, native learning, generalization, physical accuracy, system gain, originality or unique historical full-model cause claimed. Original NOC4 loss-increase/replay mismatch/INCOMPLETE and failed original NBR marker remain. No new noise/real/nearby/trajectory or production/default/backbone/reference/manuscript/install/restart/acquisition/commit/Git sync. Both original HEADs/branches/two-nine tracked dirty sets preserved. Hooks/profiler may affect scheduling; measured instrumented repeats do not certify arbitrary historical execution.
