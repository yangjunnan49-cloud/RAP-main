# ER1 complete ordinary camera baseline: limited coverage, no refit gain claim

All 273 original images and all 200 existing ordered pairs are complete. The final result is 30 pose outputs and 170 explicit no-evidence records. All 30 outputs are from sequence00's original75 positives; sequence08 has zero outputs on all100 pairs, and all50 confusers have no output. These are output-availability observations for this fixed estimator, not calibrated rejection/correctness labels or proof of image-only impossibility.

| Complete-cohort quantity | Initial raw RANSAC | Robust refit |
|---|---:|---:|
| Pose outputs /200 | 30 | 30 |
| Rotation mean, degrees (30 outputs) | 5.994019784 | 6.457726072 |
| Rotation median, degrees (30 outputs) | 0.724137465 | 0.722346730 |
| Direction mean, degrees (30 outputs) | 16.049755271 | 16.099105788 |
| Direction median, degrees (30 outputs) | 3.991091657 | 3.759320437 |
| Rotation<=5 and direction<=15, all200 denominator | 23/200 | 23/200 |
| Rotation<=10 and direction<=30, all200 denominator | 24/200 | 24/200 |

Refit improved the two medians slightly but worsened both means and increased neither complete-cohort joint bin. This does not establish an overall or material improvement. Keep all170 missing outputs and the full00/08, positive/confuser and eight25-pair strata. Full rows and15 summary groups per estimator are under runtime03/evaluate. Reference direction is defined on all200; reported mean/median errors have denominator30, not200. Frozen bins are descriptive, not safety/efficacy gates.

## Implementation and controls

Original VB1 raw-RANSAC outlier control remains FAILED (0.113146318316918-degree rotation versus strict0.1 gate; direction0.499837669953744 versus0.5). CD1's fixed analytic0.2-degree candidate still meets both1-pixel line-distance bounds on96 exact correspondences; this refutes an angular certificate from the consensus tolerance alone, not native solver correctness. ER1 is a distinct five-parameter robust Sampson-refit implementation with all parameters and code frozen before real images. The identical outlier fixture/seed/gates now gives5.944964418571343e-14-degree rotation and zero printed direction error; all23 controls pass. Initial raw values/failure remain visible in its controls and measured-data comparator.

The first actual prediction launch failed before the pair loop on a standard ASCII codec lazy import. The first narrow cold P0/NPZ probe passed; the next prediction reached seven complete no-evidence files then failed on NumPy.ma lazy loading. Both original children/sources/receipts are preserved. The final correction preloads standard modules before the same exact read allowlist, passes a complete cold synthetic computation path, preserves seven exact NPZ files, reconstructs two insufficient-match and five insufficient-essential-support JSON records from their frozen early-return semantics, and computes only193 missing pairs. A metadata-preparation assumption that all seven were insufficient-match records failed before freeze; the earlier source/plan are retained and the actual ZIP/header/mask branches were checked explicitly. No image/algorithm/threshold/seed changes or partial accuracy readout occurred. A prospective audit-only read-set correction accounts for five feature caches no longer needed by the skipped completed pairs; all273 caches remain sealed and audited.

## Separation and independent evidence

All200 initial/final predictions were sealed at2026-10-28 07:14:04.8454464 UTC. The independent reference-read begin record is07:16:11.579718 UTC. Prediction's strict Python audit hook permits only needed feature caches, two archive P0 files and seven previously completed evidence files; reference/label values are excluded. This is reviewed Python-level enforcement, not an OS security claim. Inputs retain their exposed cohort and supplied-reference roles.

The audit passed all273 cache identities/shapes,200 ordered predictions/masks/pose semantics, 6308 independent clear descriptor nearest/ratio checks. 6 sampled decisions are numerically ambiguous and explicitly retained, not counted as independently clear. All200 relative transforms were independently recomputed with Decimal60 Gaussian elimination: maximum element difference 8.5265128291212022e-14; rotation/direction metric differences 5.440092820663267e-15/2.3590018827235326e-12 degrees. All15 final and15 raw summaries retain complete denominators. The saved refit audit covers 564 manifold trace steps and 720 independently recomputed line-search costs; maximum scaled cost difference 8.2613578022730907e-11. No prediction/feature replay was used for audit.

## Resources and limits

Prediction failures+cold controls+final continuation total 24.126833500/300 seconds. All scientific-stage host walls including failures sum 72.986481300 seconds; these are child accounts, not summed overlapping inclusive scopes. Maximum successful-child OS lifetime peak is 326406144 bytes. Failed children lack final self-peak; their host-polled peaks remain. ER1 inclusive time at this closure is 1243.388731/5400 seconds, new dossier 303289946/1073741824 bytes before small closure records. Every owned child exited/reaped; fresh12GiB/2s guards and original stage caps passed. RESOURCE_AUDIT.json contains exact receipts. No old cap is replenished.

This is measured-image camera rotation and signed unit translation direction only. No metric translation scale/full metric6DoF, corrected-LiDAR equivalence, physical truth, independent source/cohort authentication, RAP increment, new RAP training or manuscript readiness is established. Old SR1 four-noise-cell failure, HFIT0 INCOMPLETE/2GiB stop, old native/joint/equivalence/source failures and all caps remain. Research UNRESOLVED; manuscript PAUSED. No installations, network, WSL start, existing-environment/default/production/Git writes, outreach, scheduler or goal-status action. Next useful review is a complete saved-output categorical join to historical missing-proposal categories, not parameter/seed/subset rescue.
