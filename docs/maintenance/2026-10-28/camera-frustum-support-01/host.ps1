$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
if(Test-Path -LiteralPath (Join-Path $taskRoot 'HOST_EXIT.json')){throw 'No retry: prior host receipt exists'}
$taskTick=[Diagnostics.Stopwatch]::StartNew()
$queryTick=[Diagnostics.Stopwatch]::StartNew();$memory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory;$queryTick.Stop()
$headroom=[long]$memory.CommitLimit-[long]$memory.CommittedBytes
@{utc=[DateTimeOffset]::UtcNow.ToString('o');headroom_bytes=$headroom;query_seconds=$queryTick.Elapsed.TotalSeconds} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'PREFLIGHT.json') -Encoding UTF8
if($headroom -lt 12GB -or $queryTick.Elapsed.TotalSeconds -gt 2){throw 'Fresh host gate failed; preserve and stop'}
$exe='C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$child=Start-Process -FilePath $exe -ArgumentList @('-I','-B',(Join-Path $taskRoot 'worker.py')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'stdout.log') -RedirectStandardError (Join-Path $taskRoot 'stderr.log') -PassThru
@{PID=$child.Id;start_utc=$child.StartTime.ToUniversalTime().ToString('o');script=(Join-Path $taskRoot 'worker.py')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'OWNED_PROCESS.json') -Encoding UTF8
$peak=0L;$errorText=$null;$forced=$false
try{while(-not $child.HasExited){$child.Refresh();$peak=[Math]::Max($peak,$child.PeakWorkingSet64);if($taskTick.Elapsed.TotalSeconds -ge 300 -or $peak -gt 512MB){throw 'Worker wall/RSS cap'};Start-Sleep -Milliseconds 25}}
catch{$errorText=$_.Exception.Message;if(-not $child.HasExited){$child.Kill();$forced=$true}}
$child.WaitForExit();$child.Refresh();$peak=[Math]::Max($peak,$child.PeakWorkingSet64)
@{exit_code=$child.ExitCode;elapsed_seconds=$taskTick.Elapsed.TotalSeconds;peak_working_set_bytes=$peak;error=$errorText;forced_stop=$forced;no_live_owned_process=$child.HasExited} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'HOST_EXIT.json') -Encoding UTF8
if($child.ExitCode -ne 0 -or $errorText){throw 'Metadata worker failed; preserve and stop'}
