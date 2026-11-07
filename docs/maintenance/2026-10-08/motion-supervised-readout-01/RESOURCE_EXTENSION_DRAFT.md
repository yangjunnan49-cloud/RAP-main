# Prospective resource-only extension, approval pending

All nine fixed1000-update fits and full independent replays have passed. The
complete primary prediction bank is still being generated before any new GT
error readout. Observed per-file resource auditing costs make the original
combined3600s cap insufficient for the complete remaining independent stage.
No accuracy outcome has been inspected to justify this proposed extension.

Request at most2700 additional process seconds, combined6300s (105min). This
changes only the combined time ceiling. Keep GPU3GiB,RSS4GiB,artifacts4GiB,
extraction1200s,each fit300s and all scientific settings/gates unchanged.
No optimizer or RAP/backbone inference is added. Remaining scope: complete
432 primary predictions and their full independent validation;144 fixed J
token-row permutation predictions and validation;708 evaluator records and
independent GT/error/gate reconstruction; final source/seal/closure/delivery audit.

Original cap enforcement remains active until owner approval and a separate
resource-amendment freeze. If the running original stage reaches its cap,
preserve its failure, source/freeze/bank, resource log and historical marker
snapshot. No count, partial compute or failure is excluded from the new ceiling.
An approved extension must use a new isolated, hash-bound budget-only launcher,
keep original scientific sources unchanged, and retain the original cap failure
in the final report. Original60min will not be reported as passed. Failed/partial
validation may be replayed in full; no selected row subset is promoted.

Until approval, no6300s ceiling is active. If the owner keeps the original cap
or does not answer, stop at3600s and deliver the completed fits/source evidence
without an accuracy or trajectory claim. System work remains separately scoped.
