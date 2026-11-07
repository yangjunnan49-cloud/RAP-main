# Native Memory Observation Boundary

Primary documentation checked 2026-10-14:

- https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process
- https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.refresh?view=net-10.0
- https://learn.microsoft.com/en-us/windows/win32/psapi/process-memory-usage-information

Microsoft documents grouped Process property caching and Refresh invalidation.
GetProcessMemoryInfo reports current/peak categories through a native handle.
These general descriptions do not establish which final queries succeeded in
the original WPC0 controller: two empty catch blocks omit those observations.
The resource-stop conclusion is an evidence sufficiency inference, not a claim
that all queries failed or that the measured native working set exceeded cap.
No Microsoft sample or general API description authenticates old missing logs.
