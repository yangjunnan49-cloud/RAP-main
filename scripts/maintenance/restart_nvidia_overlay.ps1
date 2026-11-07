param([Parameter(Mandatory=$true)][int]$RootProcessId)
$ErrorActionPreference='Stop'
$taskOutput=Join-Path (Join-Path $PSScriptRoot '..\..') 'docs/maintenance/2026-10-10/wsl-runtime-recovery-01'
$taskRoot=Get-CimInstance Win32_Process -Filter ('ProcessId='+$RootProcessId)
if(-not $taskRoot -or $taskRoot.Name -ne 'NVIDIA Overlay.exe'){throw 'Expected overlay root absent'}
$taskExecutable='C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA Overlay.exe'
if($taskRoot.ExecutablePath -ne $taskExecutable){throw 'Overlay path mismatch'}
if($taskRoot.CommandLine.Trim() -ne ('"'+$taskExecutable+'"')){throw 'Unexpected root launch arguments'}
$taskBeforeMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskBefore=Get-CimInstance Win32_Process -Filter "Name='NVIDIA Overlay.exe'" | Where-Object {$_.ProcessId -eq $RootProcessId -or $_.ParentProcessId -eq $RootProcessId}
foreach($taskItem in $taskBefore){if($taskItem.ExecutablePath -ne $taskExecutable){throw 'Unexpected child executable'}}
$taskCAD=Get-Process -Id 193076 -ErrorAction Stop
if($taskCAD.ProcessName -ne 'SLDWORKS'){throw 'Preserved CAD identity changed'}
$taskCADStart=$taskCAD.StartTime
$taskStart=[DateTime]::UtcNow
Stop-Process -Id $RootProcessId -ErrorAction Stop
foreach($taskItem in $taskBefore){
    $taskRemaining=Get-CimInstance Win32_Process -Filter ('ProcessId='+$taskItem.ProcessId)
    if($taskRemaining -and $taskRemaining.ExecutablePath -eq $taskExecutable -and $taskRemaining.ParentProcessId -eq $RootProcessId){
        Stop-Process -Id $taskItem.ProcessId -ErrorAction Stop
    }
}
$taskRestarted=Start-Process -FilePath $taskExecutable -WorkingDirectory (Split-Path $taskExecutable) -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 3
$taskAfterMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskAfter=Get-Process -Name 'NVIDIA Overlay' -ErrorAction SilentlyContinue | Select-Object Id,PrivateMemorySize64,WorkingSet64
$taskCAD=Get-Process -Id 193076 -ErrorAction Stop
if($taskCAD.StartTime -ne $taskCADStart){throw 'CAD process identity changed'}
$taskResult=[ordered]@{utc_start=$taskStart.ToString('o');utc_end=[DateTime]::UtcNow.ToString('o');
    action='Human-approved targeted NVIDIA Overlay restart';original_root_pid=$RootProcessId;new_root_pid=$taskRestarted.Id;
    affected_pids=@($taskBefore|ForEach-Object {$_.ProcessId});CAD_pid=193076;CAD_process_preserved=$true;
    before_memory=$taskBeforeMemory|Select-Object CommittedBytes,CommitLimit,AvailableBytes;
    after_memory=$taskAfterMemory|Select-Object CommittedBytes,CommitLimit,AvailableBytes;new_overlay_processes=$taskAfter;
    commit_released_bytes=([long]$taskBeforeMemory.CommittedBytes-[long]$taskAfterMemory.CommittedBytes)}
[System.IO.File]::WriteAllText((Join-Path $taskOutput 'HOST_REMEDIATION.json'),($taskResult|ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
Write-Output ($taskResult|ConvertTo-Json -Depth 4)
