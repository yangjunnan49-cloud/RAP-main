$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
if(Test-Path -LiteralPath (Join-Path $taskRoot 'OWNED_PROCESS.json')){throw 'Preserve existing CU1 attempt; no retry'}
$taskStart=[Diagnostics.Stopwatch]::StartNew()
$taskOrigin=[DateTimeOffset]::Parse('2026-10-26T06:35:00Z')
if(([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds -gt 1620){throw 'CU1 closure reserve reached'}
$taskUtf8=[Text.UTF8Encoding]::new($false)
function TaskWrite($Name,$Value){[IO.File]::WriteAllText((Join-Path $taskRoot $Name),($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
$taskBinding=Get-Content -LiteralPath (Join-Path $taskRoot 'LAUNCH_BINDING.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskBinding.host_sha256){throw 'Host binding mismatch'}
if((Get-FileHash -LiteralPath (Join-Path $taskRoot 'FREEZE.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskBinding.freeze_sha256){throw 'Freeze changed'}
$taskQ=[Diagnostics.Stopwatch]::StartNew()
$taskM=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHead=[long]$taskM.CommitLimit-[long]$taskM.CommittedBytes
$taskQ.Stop()
TaskWrite 'ADMISSION.json' @{utc=[DateTimeOffset]::UtcNow.ToString('o');headroom_bytes=$taskHead;query_seconds=$taskQ.Elapsed.TotalSeconds;required_bytes=12884901888}
if($taskHead -lt 12GB -or $taskQ.Elapsed.TotalSeconds -gt 2){throw 'Original fresh12GiB/2s gate failed'}
$taskExe='C:\Users\AAA\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskProc=$null;$taskPeak=0L;$taskForced=$false;$taskError=$null;$taskExit=$null
try{
 $taskProc=Start-Process -FilePath $taskExe -ArgumentList @('-I','-B',(Join-Path $taskRoot 'worker.py')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'stdout.log') -RedirectStandardError (Join-Path $taskRoot 'stderr.log') -PassThru
 TaskWrite 'OWNED_PROCESS.json' @{PID=$taskProc.Id;start_utc=$taskProc.StartTime.ToUniversalTime().ToString('o');script=(Join-Path $taskRoot 'worker.py');host_pid=$PID}
 while(-not $taskProc.HasExited){
  $taskProc.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProc.PeakWorkingSet64)
  if($taskStart.Elapsed.TotalSeconds -ge 300 -or $taskPeak -gt 256MB -or ([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds -ge 1620){throw 'CU1 worker resource/closure limit'}
  $taskBytes=(Get-ChildItem -LiteralPath $taskRoot -File -Recurse | Measure-Object Length -Sum).Sum
  if($taskBytes -gt 16MB){throw 'CU1 dossier cap'}
  Start-Sleep -Milliseconds 50
 }
}catch{
 $taskError=$_.Exception.Message
 if($null -ne $taskProc -and -not $taskProc.HasExited){$taskProc.Kill();$taskForced=$true}
}finally{
 if($null -ne $taskProc){$taskProc.WaitForExit();$taskProc.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProc.PeakWorkingSet64);$taskExit=$taskProc.ExitCode}
 TaskWrite 'HOST_EXIT.json' @{exit_code=$taskExit;error=$taskError;forced_stop=$taskForced;elapsed_seconds=$taskStart.Elapsed.TotalSeconds;peak_working_set_bytes=$taskPeak;no_live_owned_process=($null -eq $taskProc -or $taskProc.HasExited);scope_seconds_to_worker_exit=([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds}
}
if($taskExit -ne 0 -or $taskError -or $taskForced){throw 'CU1 failed; preserve and stop without retry'}
