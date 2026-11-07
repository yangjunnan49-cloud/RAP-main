param(
    [Parameter(Mandatory=$true)][string]$Script,
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$PublicInputRoot
)
$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskOutput=[System.IO.Path]::GetFullPath($OutputDirectory)
if(-not $taskOutput.StartsWith($taskRoot+[System.IO.Path]::DirectorySeparatorChar)){throw 'Output outside workspace'}
$taskScript=[System.IO.Path]::GetFullPath((Join-Path $taskRoot $Script))
if(-not $taskScript.StartsWith($taskRoot+[System.IO.Path]::DirectorySeparatorChar)){throw 'Script outside workspace'}
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
if($taskHeadroom -lt 12GB){throw 'Launch commit guard'}
$taskStageDir=Join-Path $taskOutput $Stage
if(Test-Path -LiteralPath $taskStageDir){throw 'Existing stage logs must be preserved'}
New-Item -ItemType Directory -Path $taskStageDir|Out-Null
$taskArguments=@('-d','Ubuntu-24.04','-u','root','--','/usr/bin/env','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1',
    '/root/miniconda3/envs/rap-inference/bin/python','-u','-B',$Script,$Stage)
if($PublicInputRoot){if($Stage -ne 'consume' -or $PublicInputRoot -ne '/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-16/regx-interface-contract-01/inputs'){throw 'Unexpected public input argument'};$taskArguments+=@($PublicInputRoot)}
$taskStart=[DateTime]::UtcNow
$taskProcess=Start-Process -FilePath 'wsl.exe' -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskStageDir 'stdout.log') -RedirectStandardError (Join-Path $taskStageDir 'stderr.log') -PassThru
$taskLaunch=[ordered]@{pid=$taskProcess.Id;utc_start=$taskStart.ToString('o');script=$Script;stage=$Stage;headroom_before_bytes=$taskHeadroom}
[System.IO.File]::WriteAllText((Join-Path $taskStageDir 'launch.json'),($taskLaunch|ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
$taskRows=[System.Collections.Generic.List[object]]::new()
while(-not $taskProcess.HasExited){
    $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
    $taskSnapshot=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');committed_bytes=[long]$taskMemory.CommittedBytes;commit_limit_bytes=[long]$taskMemory.CommitLimit;available_physical_bytes=[long]$taskMemory.AvailableBytes;headroom_bytes=([long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes)}
    $taskRows.Add($taskSnapshot)
    [System.IO.File]::AppendAllText((Join-Path $taskStageDir 'host_memory.jsonl'),($taskSnapshot|ConvertTo-Json -Compress)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
    $taskLatest=Join-Path $taskOutput 'host_latest.json'; $taskTemporary=Join-Path $taskOutput 'host_latest.tmp'
    [System.IO.File]::WriteAllText($taskTemporary,($taskSnapshot|ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
    $taskRefreshed=$false
    for($taskRetry=0;$taskRetry -lt 20;$taskRetry++){
        try{
            if(Test-Path -LiteralPath $taskLatest){[System.IO.File]::Move($taskTemporary,$taskLatest,$true)}
            else{[System.IO.File]::Move($taskTemporary,$taskLatest)}
            $taskRefreshed=$true; break
        }catch{
            [System.IO.File]::AppendAllText((Join-Path $taskStageDir 'logging_retry.jsonl'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');retry=$taskRetry;error=$_.Exception.Message}|ConvertTo-Json -Compress)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
            Start-Sleep -Milliseconds 50
        }
    }
    if(-not $taskRefreshed){[System.IO.File]::AppendAllText((Join-Path $taskStageDir 'logging_gap.jsonl'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');kind='latest_pointer_refresh_unavailable';host_snapshot=$taskSnapshot}|ConvertTo-Json -Compress)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))}
    Start-Sleep -Milliseconds 500; $taskProcess.Refresh()
}
$taskProcess.WaitForExit(); $taskEnd=[DateTime]::UtcNow
$taskExit=[ordered]@{exit_code=$taskProcess.ExitCode;utc_end=$taskEnd.ToString('o');wall_seconds=($taskEnd-$taskStart).TotalSeconds;host_memory_observations=$taskRows.Count;minimum_observed_headroom_bytes=($taskRows|ForEach-Object {$_.headroom_bytes}|Measure-Object -Minimum).Minimum}
[System.IO.File]::WriteAllText((Join-Path $taskStageDir 'exit.json'),($taskExit|ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
Get-Content (Join-Path $taskStageDir 'stdout.log') -Tail 16
if($taskProcess.ExitCode -ne 0){Get-Content (Join-Path $taskStageDir 'stderr.log') -Tail 24}
Write-Output ($taskExit|ConvertTo-Json -Compress)
exit $taskProcess.ExitCode
