# Execution startup retry

The first prepare and prematurely submitted dependent preflight calls failed at `check()` because the launcher had not applied the prospectively fixed single CPU thread. Both original failures and resource rows are retained. Neither call reached fixture/noise preparation, model load, mathematical numerics or optimizer work. The missing noise stage was not bypassed.

Retry uses the same frozen sources and inputs with OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 and OPENBLAS_NUM_THREADS=1, matching freeze.runtime.threads=1. No objective/backward scale/optimizer/seed/gate/resource setting changes. Source freeze is unchanged. Both failed calls count toward the combined wall/RSS limits. Delivery wording must disclose the startup failures; the original closure's assumption of all-successful stages requires a separately frozen delivery-only correction before closing.
