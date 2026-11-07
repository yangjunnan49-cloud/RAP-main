# Input-validator record serialization correction

Before any neural prediction or evaluator GT, the original independent input
validator completed scan/score/calibration assertions but failed dumping its
NumPy int64 accepted count into JSON. Its partial file is preserved verbatim
as `input_validation.failed-original.json`; original frozen validator, protocol,
runner and sealed input bank are unchanged. V2 changes only `accepted +=
admitted` to `accepted += int(admitted)`. No numerical calculation, threshold,
input, calibration limit, or efficacy output changes. V2 repeats every check.

Freeze this amendment, V2 script, failed partial record and amended validation
entry point before rerun. The original final validator is called unchanged by
an entry point which additionally verifies this amendment manifest. No pair
prediction exists at this amendment boundary; no GT label has been read.
