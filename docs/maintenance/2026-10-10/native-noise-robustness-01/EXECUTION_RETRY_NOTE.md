# NOC1 execution-order retry

The evaluation command returned an active process handle. The orchestrator started independent validation before that process completed and sealed results_seal.json. Validation stopped with FileNotFoundError before numerical reconstruction or replay. This was an execution-order error, not an implementation or scientific failure.

Preserve FAILURE_validation.json and its failed RESOURCE_LOG entry. Evaluation subsequently completed normally and retained the failed entry in the combined ledger. The same frozen validator is rerun only after the complete results seal exists; no source, adapter, noise, prediction, teacher output, gate or resource ceiling changes. The failed attempt and retry both count toward the original NOC1 resource caps. No additional full prediction bank is generated.
