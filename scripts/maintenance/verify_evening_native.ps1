$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-15/continuation-handoff-08'
$taskIdentity=Get-Content (Join-Path $taskBase 'IDENTITY_CHECKS.json') -Raw|ConvertFrom-Json
$taskChecked=0;$taskExcluded=0;$taskBytes=0L
foreach($taskProperty in $taskIdentity.files.PSObject.Properties){
    $taskName=$taskProperty.Name
    if(-not $taskName.StartsWith('/mnt/e/githouse/RAP-main/')){$taskExcluded++;continue}
    $taskPath=Join-Path $taskRoot $taskName.Substring('/mnt/e/githouse/RAP-main/'.Length).Replace('/','\')
    $taskInfo=Get-Item -LiteralPath $taskPath
    if($taskInfo.Length -ne $taskProperty.Value.bytes){throw "Length mismatch $taskPath"}
    if((Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLower() -ne $taskProperty.Value.sha256){throw "SHA mismatch $taskPath"}
    $taskChecked++;$taskBytes+=$taskInfo.Length
}
$taskLate=[ordered]@{}
foreach($taskSuffix in @('dependency-audit-02','dependency-audit-03')){
    $taskOldBase=Join-Path $taskRoot "docs/maintenance/2026-10-15/continuation-handoff-07/$taskSuffix"
    $taskSeal=Get-Content (Join-Path $taskOldBase 'DELIVERY_SEAL.json') -Raw|ConvertFrom-Json
    foreach($taskEntry in $taskSeal.files){
        $taskFile=Join-Path $taskOldBase $taskEntry.path
        $taskInfo=Get-Item -LiteralPath $taskFile
        if($taskInfo.Length -ne $taskEntry.bytes -or (Get-FileHash -LiteralPath $taskFile).Hash.ToLower() -ne $taskEntry.sha256){throw 'Historical late seal mismatch'}
        $taskLate["$taskSuffix/$($taskEntry.path)"]=[ordered]@{bytes=$taskInfo.Length;sha256=$taskEntry.sha256}
    }
}
$taskProcesses=@(Get-CimInstance Win32_Process)
$taskReadable=@($taskProcesses|Where-Object{$_.CommandLine})
$taskRelevantNull=@($taskProcesses|Where-Object{-not $_.CommandLine -and $_.Name -match '^(python(?:w)?(?:3(?:\.\d+)?)?|wsl)\.exe$'})
$taskPattern='(?i)(?:^|[\/\s])(?:nonlocal_joint_connectivity|run_nonlocal_joint_connectivity|validate_nonlocal_joint_connectivity|nonlocal_joint_comparison(?:_cpu02)?|run_nonlocal_joint_comparison(?:_cpu02)?|validate_nonlocal_joint_comparison|independent_nonlocal_joint|run_independent_nonlocal_joint)\.py(?:\s|$)'
$taskOwned=@($taskReadable|Where-Object{$_.Name -match '^(python(?:w)?(?:3(?:\.\d+)?)?|wsl)\.exe$' -and $_.CommandLine -match $taskPattern})
if($taskOwned.Count){throw 'Scoped payload remains visible'}
$taskCensus=[ordered]@{processes=$taskProcesses.Count;readable_command_lines=$taskReadable.Count;null_command_lines=($taskProcesses.Count-$taskReadable.Count);unreadable_relevant_interpreter_count=$taskRelevantNull.Count;scoped_owned_payload_matches=$taskOwned.Count;scope='Only NJC/NJE interpreter arguments; no unrelated task absence claim';utc=[DateTime]::UtcNow.ToString('o')}
$taskCensus|ConvertTo-Json|Set-Content (Join-Path $taskBase 'PROCESS_CENSUS_WINDOWS.json') -Encoding utf8
$taskResult=[ordered]@{passed=$true;independently_checked_RAP_main_paths=$taskChecked;checked_bytes=$taskBytes;outside_RAP_main_paths_verified_by_Linux_only=$taskExcluded;total_Linux_verified_paths=$taskIdentity.unique_verified_paths;prior_late_supplements=$taskLate;original_handoff07_14entry_and737identity_proofs_unchanged=$true;complete_all_native_memory_claim=$false;setup_RSS='UNKNOWN'}
$taskResult|ConvertTo-Json -Depth 8|Set-Content (Join-Path $taskBase 'WINDOWS_CHECKS.json') -Encoding utf8
[ordered]@{checked=$taskChecked;excluded=$taskExcluded;late_sealed_references=$taskLate.Count;process_census=$taskCensus}|ConvertTo-Json -Depth 5
