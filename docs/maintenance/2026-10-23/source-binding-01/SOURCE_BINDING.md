# Actual RAP public interface and transform map

Static source audit only. The 20 source/config identities are in SOURCE_BINDINGS.json and DEPENDENCY_BINDINGS.json; AST_INDEX.json records callable ranges and literal dictionary accesses. All five original pointers still match the October 21 seal. Thirteen static assertions pass. These assertions execute no project function or numerical import.

## Public input, features and ordering

| Path | Actual behavior and source lines | Consequence |
|---|---|---|
| Direct backend | rap_backend.py:127–163 downsample/outlier-filter one public scan, deterministic capped subset if needed, require at least 200 resulting points, extract descriptors on the resulting original-metric points or supply 32 zero channels. | The backend's public array API needs no external GT file. Preprocessing/descriptor correctness is not validated by this static read. |
| Direct features | extract_sample_features.py:118–144 defaults keypoints to an ordered copy of points, passes points/keypoints to miniSpinNet, returns desc in keypoint order; rap_backend.py:238,396 concatenate per-part feature rows in part order. | A later source-interface control can verify routing with row markers, but a stub cannot authenticate miniSpinNet quality. The exception path at extract_sample_features.py:146–157 attempts zero features; its keypoints.dim access also deserves explicit NumPy failure-path treatment rather than assuming every failure silently becomes zeros. |
| Canonical preprocessing | demo.py:240–258 applies voxel downsampling, :266–323 optionally randomly subsamples, :333 invokes SampleProcessor. extract_sample_features.py:367–399 uses FPS indices for points/normals, then computes descriptors with original part points as context and sampled points as keypoints. | This is not the backend's identical computational path. Feature context, sampling, row order and provenance must be stated separately. |
| Serialization/reader | io_utils.py:211–234 writes each part PLY and features_<part>.npy. dataset.py:663–679 sorts PLY filenames; :39–65 reads corresponding feature files and can replace absent/unreadable features with zeros. :682–714 copies vertices/features, marks presampled and supplies zero normals. | No feature-quality authentication follows merely from a matching shape. Stable part identity must follow filenames and point/feature rows, not incidental file order. |
| Dataset val transform | dataset.py:739–911 computes shared scale, centers each part, shuffles point/feature rows together, pads parts and labels the largest part as anchor. | The backend does not perform that shuffle or padding. Algebraic correspondence is conditional on matching rows/dtypes and is not a full loader/canonical equivalence certificate. |

## Normalization and batch fields

Use column vectors x_i in original metric scan coordinates. Let n_i be part counts and a the first argmax of those counts. Backend source rap_backend.py:180–210 computes:

* c_a = mean(x_a); s = 1.5 max_abs(x_a - c_a).
* y_i = (x_i - c_a)/s; g = the point-weighted mean of all y_i; z_i = y_i - g.
* Anchor condition q_a = z_a + g; other condition q_i = z_i - mean(z_i).
* Stored c_i = c_a for the anchor, otherwise c_a + s g + s mean(z_i).

In exact arithmetic, all q_i = (x_i - c_i)/s and c_i is the original part mean. Actual computation uses float64 intermediates and emits float32 cond; operation ordering and this cast matter. CN1 instead uses the maximum extent over all centered views, so its scale convention is different. Dataset val mode (dataset.py:767–799,805–837,844–899) uses the primary-part extent but retains its input dtype and shuffles rows. Source comments claiming identity do not prove identical runtime bytes.

Direct register/register_multi supply the same seven fields (rap_backend.py:249–257 / :403–411):

| Field | Layout / provenance |
|---|---|
| pointclouds | float32 (TP,3), public cond in stacked part order |
| pointclouds_gt | a second tensor made from the same public cond; a compatibility placeholder, not an external reference |
| features | float32 (TP,32), stacked in the same part and row order |
| scales | float32 (1,), one shared scale per sample; recovery still uses the original Python float scale |
| anchor_indices | bool (TP,), exactly the primary part interval |
| points_per_part | int64 (1,P), direct backend has no padded empty part |
| cu_seqlens | int64 [0,TP], later cast to int32 by preparation |

modeling.py:203–231 derives cumulative lengths for nonzero parts and casts lengths to int32. point_cloud_dit.py:173–176 broadcasts the sample scale to points and adds the anchor embedding. split_parts in utils/point_clouds.py:27–49 removes empty splits; fit_transformations still indexes by the declared part index. Canonical trailing zero padding is the relevant supported domain; an interior empty part must not be silently admitted as an equivalent schema. Normalization itself has no explicit finite/positive-scale validation. Any isolated cooperating adapter must reject empty/nonfinite/degenerate inputs before calling it, without claiming the production source already performs those checks.

## Actual sampling and reference dependency

modeling.py:211 unconditionally retrieves pointclouds_gt in _prepare_data. However, sample_rectified_flow:659 assigns that first returned value to `_`; the effective sampler receives x_0=cond and condition=cond at :710–721. Noise is generated from cond at :664. Effective Euler is selected by config/model/rap_12.yaml:13 and sampler.py:154–167. A public placeholder can therefore satisfy the dictionary API without providing private reference coordinates. This is a source inference about this exact branch and not a general statement that the key is never read.

The default evaluation route is different: demo.py:892–896 and sample.py:204–208 call trainer.test; modeling.py:339 invokes self.forward, whose :235–245 prepares x_0, constructs noise and flow targets using it, and calls the flow model. test_step also sends internal GT/transform fields to evaluator.run at :380–400. Evaluator._compute_metrics:38–66 compares against pointclouds_gt/rotations/translations. demo.py:901 only gates printed tables, after trainer.test has already run. Thus `eval_on=false` does not remove the reference-dependent computations.

For folder inputs, dataset.py:673 names the loaded public part vertices pointclouds_gt before normalization. That name does not establish a common physical world or independently authenticated truth for unposed scans. Use a direct public route plus a separate evaluator for any future physical claim; do not relabel those internal arrays as independent GT. A cooperating in-process separation is not OS containment.

sampler.py:58–65 additionally distinguishes a rigidified integration state from the raw endpoint estimate: rigidity_forcing uses a fitted x_0_hat_rigidified to update x_t, while end_point_trajectory stores the original x_0_hat. Backend :265/:419 selects this endpoint and then fits transforms. Do not assume the endpoint tensor is already rigid merely because rigidity_forcing is true.

## Fit direction and original-coordinate recovery

Backend register:267–268 and register_multi:421–422 pass **cond as source, endpoint prediction as target** to fit_transformations. procrustes.py:20–37 computes the source-to-target Kabsch fit, with row form `q @ R.T + t`, equivalently column form `R q + t`. Determinant correction is part of that existing fitting algorithm. It is not permission to repair an invalid matrix supplied to an independent recovery contract.

Let the resulting normalized fit A_i have rotation R_i and translation t_i. Backend :275–283 / :428–445 builds:

`T_i = [R_i, s*t_i - R_i*c_i; 0, 1]`.

T_i maps original scan i into the metric registered common frame. The returned pair transform is `inverse(T_0) @ T_1`, mapping scan 1 coordinates into scan 0 coordinates. N-way returns all T_i; any reference r gives `inverse(T_r) @ T_i`. A common rigid left gauge cancels. This recovery already exists for both paths.

In dataset val mode let m be the original point-weighted global mean. The internal target is `(x_i-m)/s`, R_gt=I, and t_gt=(c_i-m)/s. evaluator.py:457–485 forms metric A_i, metric GT_i, and G=[I,m], then writes `A_i @ inverse(GT_i) @ inverse(G)`. Substitution gives the same original-coordinate T_i in exact arithmetic. demo.py:1044–1054 reads those matrices and uses the first part as reference. The exporter uses float32 matrices and eight decimal text digits; its recovery and formatting need a representation-aware source test, not an assumed exact-byte equivalence. This derivation does not extend to training augmentation or authenticate external references.

## Decision

There is no missing generic recovery implementation to build. A distinct actual-source synthetic scope is justified to test the currently untested linkage: actual backend normalization/N-way recovery with row-marked public arrays and known rigid endpoints; actual val transform/export bookkeeping including permutations and padding; the sampler's placeholder-content dependency and endpoint/state distinction. It can use AST-extracted unchanged function bodies with explicitly stubbed preprocessing, neural endpoints and flow model, plus actual small synthetic NumPy/Torch geometry. It must report those substitutions and cannot certify real preprocessing/features/model efficacy or canonical file loading.

Before such work: freeze exact source/functions and controls, choose independent scalar oracles and prospective representation budgets, retain invalid-schema and wrong-direction/scale/order controls, and use a fresh bounded guarded CPU-only scope. No numeric/model payload was executed in S2. No old family, threshold, budget or failed result is reopened.
