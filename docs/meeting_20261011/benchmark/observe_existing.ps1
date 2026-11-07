$ErrorActionPreference='Stop'
$taskBase=Join-Path $PSScriptRoot 'attempt03/supervision'
$taskLaunch=Get-Content -LiteralPath (Join-Path $taskBase 'run/launch.json') -Raw | ConvertFrom-Json
$taskProcess=Get-Process -Id $taskLaunch.pid
if($taskProcess.ProcessName -ne 'wsl'){throw 'Unexpected process identity'}
$taskObservation=Join-Path $taskBase 'recovery-observation'
New-Item -ItemType Directory -Path $taskObservation | Out-Null
$taskBegin=[DateTime]::UtcNow
while(-not $taskProcess.HasExited){
 $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
 $taskSnapshot=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');committed_bytes=[long]$taskMemory.CommittedBytes;commit_limit_bytes=[long]$taskMemory.CommitLimit;available_physical_bytes=[long]$taskMemory.AvailableBytes;headroom_bytes=([long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes)}
 [System.IO.File]::AppendAllText((Join-Path $taskObservation 'host_memory.jsonl'),($taskSnapshot|ConvertTo-Json -Compress)+[Environment]::NewLine)
 $taskTemp=Join-Path $taskBase 'observer_latest.tmp'
 [System.IO.File]::WriteAllText($taskTemp,($taskSnapshot|ConvertTo-Json))
 $taskWritten=$false
 for($taskTry=0;$taskTry -lt 20;$taskTry++){
  try{[System.IO.File]::Move($taskTemp,(Join-Path $taskBase 'host_latest.json'),$true);$taskWritten=$true;break}catch [System.IO.IOException]{Start-Sleep -Milliseconds 50}
 }
 if(-not $taskWritten){throw 'Host snapshot replacement retries exhausted'}
 Start-Sleep -Milliseconds 500
 $taskProcess.Refresh()
}
$taskProcess.WaitForExit()
[System.IO.File]::WriteAllText((Join-Path $taskObservation 'exit.json'),([ordered]@{observed_pid=$taskLaunch.pid;utc_observer_start=$taskBegin.ToString('o');utc_end=[DateTime]::UtcNow.ToString('o');windows_exit_code=$taskProcess.ExitCode;scope='attached observation; original pre-attachment host gap retained'}|ConvertTo-Json))
Get-Content -LiteralPath (Join-Path $taskBase 'run/stdout.log') -Tail 8
