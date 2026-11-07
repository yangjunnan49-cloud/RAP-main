# Primary Native API Boundary

Checked2026-10-14:
https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo
https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters
https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.refresh?view=net-10.0

The native function takes a process handle, output structure and size; nonzero
return indicates success, zero permits GetLastError interpretation. The counter
structure contains peak working set and peak commit. The .NET Process group
cache is refreshed explicitly. None of these general sources specifies which
queries succeeded in old missing logs or guarantees this exact post-exit runtime
behavior. That bounded behavior is measured here, with every result retained.
