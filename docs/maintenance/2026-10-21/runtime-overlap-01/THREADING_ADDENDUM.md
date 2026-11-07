# Native threading correction before executable freeze

The planning design's phrase 'S one numerical core and P up to two' is unsupported. Existing G/K registration config max_num_threads=0 retains the native automatic policy. OMP/MKL/OpenBLAS environment variables remain1, but they do not certify all native/TBB thread counts or CPU use. Preserve all original configuration values; do not introduce an affinity/seed/thread-count workaround.

P runs two numerical processes and may incur native contention/oversubscription. S/P do not have certified equal CPU resources; no one/two-core speedup or efficiency claim. Record per-process CPU times and observed native thread count, with whole-tree/native peak limitations explicit. This addendum supersedes that single core-count sentence before any raw pilot; prior DESIGN/admission freeze remains immutable. It does not change numerical/performance gates, partitions or algorithm parameters.
