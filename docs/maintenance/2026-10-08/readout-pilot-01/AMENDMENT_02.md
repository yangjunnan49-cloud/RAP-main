# Amendment 02: scalar metadata copy and unique failure record

Attempt-02 stopped at the first00 I repeat-reference snapshot. The metadata
dictionary contains scale as a Python float, so `{k:v.copy() ...}` raised
AttributeError. Its00 J NPZ was already written and remains a partial bank;
no complete-bank seal or validation exists. The attempted error writer then
hit FileExistsError because it reused the original failure filename. The
original failure was not overwritten; the second failed resource entry was
written before the filename collision. FAILURE_engineering_bank_attempt02.json
records both observed exceptions and the partial file identity.

Preserve both prior freezes, runners/validators/common files, INCOMPLETE markers,
partial J output and failures. No GT labels or fitting have started.

New attempt-03 uses `np.asarray(v).copy()` for every array/scalar snapshot,
preserving values and saved dtypes. Its wrapper prefixes failure/resource names
to keep attempt records distinct. Native inverse/multiply serialization from
Amendment01 stays. All four windows are rerun prospectively under a fresh
attempt-03 freeze. No model, grouping, data, seed, timestep, tolerance, gate or
scientific setting changes. Existing failed work remains invalid as a complete
experiment. All failed and retry compute stays within the original total cap.
