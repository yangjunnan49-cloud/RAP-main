$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskOrigin=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'origin.json') | ConvertFrom-Json
function TaskElapsed { [Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$taskOrigin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$taskOrigin.start_ticks)/[double]$taskOrigin.frequency) }
if((TaskElapsed) -ge 1020){throw 'DA2 whole-scope reserve reached'}
$taskTick=[Diagnostics.Stopwatch]::GetTimestamp()
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
if($taskHeadroom -lt 12GB -or ([Diagnostics.Stopwatch]::GetTimestamp()-$taskTick)/[Diagnostics.Stopwatch]::Frequency -gt 2){throw 'Fresh12GiB admission failed'}
$taskProcess=Start-Process -FilePath 'C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -ArgumentList @('-I','-B',(Join-Path $taskRoot 'audit.py')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'stdout.log') -RedirectStandardError (Join-Path $taskRoot 'stderr.log') -PassThru
$taskPeak=0L;$taskStart=[Diagnostics.Stopwatch]::GetTimestamp()
while(-not $taskProcess.HasExited){
    $taskProcess.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProcess.PeakWorkingSet64)
    if($taskPeak -gt 256MB -or ([Diagnostics.Stopwatch]::GetTimestamp()-$taskStart)/[Diagnostics.Stopwatch]::Frequency -gt 120 -or (TaskElapsed) -ge 1020){$taskProcess.Kill();throw 'Owned DA2 process cap'}
    Start-Sleep -Milliseconds 20
}
$taskProcess.WaitForExit()
[IO.File]::WriteAllText((Join-Path $taskRoot 'HOST_RECEIPT.json'),(@{exit_code=$taskProcess.ExitCode;observed_peak_working_set_bytes=$taskPeak;headroom_before_bytes=$taskHeadroom;stage_seconds=([Diagnostics.Stopwatch]::GetTimestamp()-$taskStart)/[Diagnostics.Stopwatch]::Frequency;exact_owned_pid=$taskProcess.Id;no_live_owned_process=$taskProcess.HasExited;scope_elapsed=(TaskElapsed)} | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
if($taskProcess.ExitCode -ne 0){throw 'DA2 worker failed; preserve and stop'}
