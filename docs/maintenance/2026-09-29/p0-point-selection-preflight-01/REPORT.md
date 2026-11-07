# P0 first engineering preflight: failed reproducibility

The four-pair GT-free bank was sealed after 6.756 s, with 8,000 points per
pair, finite nonzero descriptors, 2.090 GiB peak allocated GPU memory and
4.162 MB of artifacts. The independent validator reproduced the selected
FPS points but failed exact descriptor regeneration. Read-only diagnosis
found maximum absolute descriptor differences 0.918706 on the first scan
and 0.816693 on the last scan. The local miniSpinNet implementation calls
`np.random.choice(N, N, replace=False)` while constructing each patch; the
runner did not fix NumPy state. The descriptor bank is therefore unsuitable
for information efficacy scoring. Its source freeze, bank and artifacts are
preserved; `INCOMPLETE` marks failed validation. The diagnostic output is
named `diagnostic_run_output.json` and is not a passing validation.

The separate P0-02 amendment freezes the saved F2 per-pair seed for all six
descriptor calls and validates exact regeneration. No evaluator GT or labels
were read in this attempt. No RAP generation or full 200-pair run occurred.
