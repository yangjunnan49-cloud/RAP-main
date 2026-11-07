# Post-hoc support decomposition; zero pose optimization

The existing representation census changed both the uniform 6000-point upper
cap and the even/odd training split. It therefore cannot assign the observed
support gain uniquely to either step. Add an intermediate count-only scenario:
all retained MMR0 points (including its old odd probe rows), with the same frozen
O poses and 2m/4m feature rules. Reuse the existing thin/full census values.

Verify every one of the 190332 retained points is unchanged in the full voxel
superset. No new pose candidate, reference error, optimizer, gate change or
dense accuracy claim. Previously held-out rows are used only for this clearly
post-outcome support census; they remain held out in SMP1 optimization/evaluation.
Record source/output bindings and include computation in the same pilot budget.
