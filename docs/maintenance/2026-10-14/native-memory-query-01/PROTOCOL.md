# NMQ0 Direct Native Query Sufficiency

Bind current runtime executable, source, WPC0 available evidence/stop and primary
API notes before execution. Compile only in-memory P/Invoke declarations using
existing PowerShell Add-Type; no package install or external binary acquisition.
Read the newly launched process handle before exit and keep it until every
query is recorded and the process is reaped. Fixed children create no files.

Baseline waits0.1s and exits0. Observe running direct OS counters every5ms,
logging success/error relevance/returned fields. After WaitForExit, query the
same retained handle twice, with a Process.Refresh()+PeakWorkingSet64 attempt
between them. Record that .NET result or exception, never empty catches.
Win32 error is meaningful for failed API calls only; preserve its raw value
on success without interpreting it as failure.

Only if both post-exit queries succeed with positive identical peak working
set values at least every successful running peak may early/late burst run.
Each burst allocates64MiB byte array and touches every4KiB page. Early frees
and requests GC then waits0.1s; late exits immediately after touching. These
are behavioral controls, not guaranteed whole-lifetime allocator benchmarks.
All native child exits must be0; a10s deadline kills only that owned PID and
fails the stage. No arbitrary process-tree claim. Retain all observed failures.

Independent validator reconstructs ABI field size72 on64bit, query counts,
conditional1-or3 child denominator, returned exit/counter relations and both
post-exit .NET outcomes. Success of post-exit API observation does not retro-
authenticate WPC0 or old RSS gaps. If unavailable, do not run more burst cases
or call the full native resource gate passed. Observer self-query remains
observed-to-snapshot only, not complete full-lifetime telemetry.
