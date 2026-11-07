$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-12/scan-level-graph-feasibility-01'
function Read-TaskJson([string]$taskPath) { Get-Content -LiteralPath $taskPath -Raw | ConvertFrom-Json }
function Write-TaskJson([string]$taskPath, $taskValue) {
    if(Test-Path -LiteralPath $taskPath){throw ('Immutable closing output already exists: '+$taskPath)}
    [System.IO.File]::WriteAllText($taskPath,($taskValue|ConvertTo-Json -Depth 30)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
}
$taskFreeze=Read-TaskJson (Join-Path $taskBase 'freeze.json')
$taskValidation=Read-TaskJson (Join-Path $taskBase 'validation.json')
$taskResults=Read-TaskJson (Join-Path $taskBase 'results.json')
if(-not $taskValidation.passed){throw 'Independent validation missing'}
if($taskResults.gate.passed -or $taskResults.gate.decision -ne 'NO_SAFE_MATERIAL_SCAN_GRAPH_SIGNAL'){throw 'Unexpected scientific outcome'}
$taskIdentityRows=@(); $taskLinuxRows=@()
foreach($taskItem in $taskFreeze.files.PSObject.Properties){
    if($taskItem.Name.StartsWith('/mnt/e/')){
        $taskPath=('E:/'+$taskItem.Name.Substring(7))
        $taskHash=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if($taskHash -ne $taskItem.Value){throw ('Frozen identity changed: '+$taskPath)}
        $taskIdentityRows+= [ordered]@{path=$taskPath;sha256=$taskHash}
    } elseif($taskItem.Name.StartsWith('/root/')){
        $taskLinuxRows+=[ordered]@{path=$taskItem.Name;sha256=$taskItem.Value;receipt='Successful frozen validation verify_freeze; no new Windows mapping'}
    } else {throw ('Unknown frozen path: '+$taskItem.Name)}
}
Write-TaskJson (Join-Path $taskBase 'FINAL_IDENTITY_CHECK.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');passed=$true;windows_entries=$taskIdentityRows.Count;windows_files=$taskIdentityRows;linux_prior_successful_validation=$taskLinuxRows;repositories=$taskFreeze.repositories})
$taskStages=@('freeze','preflight','validate_preflight','bank','evaluate','validate')
$taskDirectories=@(Get-ChildItem (Join-Path $taskBase 'supervision') -Directory)
if($taskDirectories.Count -ne $taskStages.Count){throw 'Unexpected attempt inventory'}
$taskReceipts=@()
foreach($taskStage in $taskStages){
    $taskLog=Join-Path $taskBase ('supervision/'+$taskStage)
    $taskChild=Read-TaskJson (Join-Path $taskLog 'child_exit.json')
    $taskHost=Read-TaskJson (Join-Path $taskLog 'exit.json')
    $taskLaunch=Read-TaskJson (Join-Path $taskLog 'launch.json')
    $taskSamples=@(Get-Content (Join-Path $taskLog 'host_memory.jsonl') | ForEach-Object {$_|ConvertFrom-Json})
    if(-not $taskChild.success -or -not $taskChild.full_resource_capture -or $taskHost.exit_code -ne 0){throw 'Attempt failed or incomplete'}
    if($taskChild.peak_RSS_bytes -gt 4GB -or $taskChild.GPU_calls -ne 0 -or $taskLaunch.headroom_before_bytes -lt 12GB){throw 'Child/launch cap failed'}
    if($taskSamples.Count -ne $taskHost.host_memory_observations -or $taskSamples.Count -lt 1){throw 'Host observations missing'}
    if(($taskSamples.headroom_bytes|Measure-Object -Minimum).Minimum -lt 4GB){throw 'Observed host headroom failed'}
    if([long](Get-Item (Join-Path $taskLog 'stdout.log')).Length -lt 1){throw 'Missing stdout'}
    $taskReceipts+=[ordered]@{stage=$taskStage;child=$taskChild;host=$taskHost;launch=$taskLaunch}
}
$taskWall=($taskReceipts.child.wall_seconds|Measure-Object -Sum).Sum
if($taskWall -ge 900){throw 'Combined payload cap failed'}
$taskPeak=($taskReceipts.child.peak_RSS_bytes|Measure-Object -Maximum).Maximum
$taskBytes=(Get-ChildItem $taskBase -File -Recurse|Measure-Object -Property Length -Sum).Sum
if($taskBytes -ge 512MB){throw 'Whole-dossier artifact cap failed'}
$taskOldMarker=Join-Path $taskRoot 'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE'
if(-not(Test-Path -LiteralPath $taskOldMarker)){throw 'Old NOC4 marker missing'}
$taskPassed=@($taskResults.gate.tests.PSObject.Properties|Where-Object {$_.Value -eq $true}).Count
$taskFailed=@($taskResults.gate.tests.PSObject.Properties|Where-Object {$_.Value -eq $false}).Count
Write-TaskJson (Join-Path $taskBase 'RESOURCE_AUDIT.json') ([ordered]@{passed=$true;all_attempts_full_child_capture=$true;all_windows_exit_records=$true;attempts=6;payload_wall_seconds=$taskWall;supervised_process_wall_seconds=($taskReceipts.host.wall_seconds|Measure-Object -Sum).Sum;max_RSS_bytes=$taskPeak;GPU_calls=0;artifact_bytes_before_closing_metadata=$taskBytes;minimum_observed_host_headroom_bytes=($taskReceipts.host.minimum_observed_headroom_bytes|Measure-Object -Minimum).Minimum;receipts=$taskReceipts;host_sampling_is_not_continuous_peak_capture=$true;old_resource_gaps_not_amended=$true})
Write-TaskJson (Join-Path $taskBase 'CHECKS.json') ([ordered]@{passed=$true;scientific_efficacy_conjunction=$false;prospective_tests=61;passed_tests=$taskPassed;failed_tests=$taskFailed;freeze_identities=1155;bank_entries=55;independent_segments=36990;independent_validation=$taskValidation;resource_caps=$true;historical_NOC4_INCOMPLETE_preserved=$true;new_graph_calls_during_closure=0;production_changes=0;commit_or_sync=$false})
$taskStatus=[ordered]@{status='VALIDATED_EXPLORATORY_COMPLETE';decision=$taskResults.gate.decision;scientific_comparison_complete=$true;scientific_gate_passed=$false;independent_validation_passed=$true;utc=[DateTime]::UtcNow.ToString('o');payload_wall_seconds=$taskWall;peak_RSS_bytes=$taskPeak;neural_calls=0;raw_scan_calls=0;new_loop_observations=0;later_measured_registration_and_residual_head='DESIGN_ONLY';old_NOC4_remains_INCOMPLETE=$true;commit_or_sync=$false}
[System.IO.File]::WriteAllText((Join-Path $taskBase 'STATUS.json'),($taskStatus|ConvertTo-Json -Depth 10)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
$taskMarker=Join-Path $taskBase 'INCOMPLETE'
if(Test-Path -LiteralPath $taskMarker){Remove-Item -LiteralPath $taskMarker}
$taskFiles=@(Get-ChildItem $taskBase -File -Recurse|Sort-Object FullName|ForEach-Object {[ordered]@{path=[System.IO.Path]::GetRelativePath($taskBase,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
$taskClosureSource=Join-Path $taskBase 'closure_source_snapshot.ps1'
Copy-Item -LiteralPath $PSCommandPath -Destination $taskClosureSource
$taskFiles+=[ordered]@{path='closure_source_snapshot.ps1';sha256=(Get-FileHash -LiteralPath $taskClosureSource -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item $taskClosureSource).Length}
Write-TaskJson (Join-Path $taskBase 'DELIVERY_SEAL.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='VALIDATED_EXPLORATORY_COMPLETE';decision=$taskResults.gate.decision;files=$taskFiles;entries=$taskFiles.Count})
Write-Output ([ordered]@{status=$taskStatus.status;decision=$taskStatus.decision;delivery_entries=$taskFiles.Count;payload_seconds=$taskWall;peak_RSS_bytes=$taskPeak}|ConvertTo-Json -Compress)
