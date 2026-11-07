$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-12/reference-physical-consistency-01'
function Read-RpcJson([string]$taskPath){Get-Content -LiteralPath $taskPath -Raw|ConvertFrom-Json}
function Write-RpcJson([string]$taskPath,$taskValue){
    if(Test-Path -LiteralPath $taskPath){throw ('Immutable closing output exists: '+$taskPath)}
    [System.IO.File]::WriteAllText($taskPath,($taskValue|ConvertTo-Json -Depth 50)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
}
function Check-RpcHash([string]$taskPath,[string]$taskExpected){
    $taskActual=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if($taskActual -ne $taskExpected){throw ('Identity changed: '+$taskPath)}
    return $taskActual
}
function Map-RpcPath([string]$taskPath){
    if($taskPath.StartsWith('/mnt/e/')){return 'E:/'+$taskPath.Substring(7)}
    throw ('Not a Windows mapped path: '+$taskPath)
}
$taskFreeze=Read-RpcJson (Join-Path $taskBase 'freeze.json')
$taskAmend=Read-RpcJson (Join-Path $taskBase 'VALIDATION_AMENDMENT_FREEZE02.json')
$taskResult=Read-RpcJson (Join-Path $taskBase 'results.json')
$taskValidation=Read-RpcJson (Join-Path $taskBase 'validation.json')
$taskPrerequisite=Read-RpcJson (Join-Path $taskBase 'preflight_validation_attempt02.json')
if(-not $taskValidation.passed -or -not $taskPrerequisite.passed -or $taskPrerequisite.unchanged_tolerance -ne 1e-8){throw 'Complete validated result required'}
if($taskValidation.scans -ne 11 -or $taskValidation.cross_pairs -ne 15 -or $taskValidation.local_pairs -ne 7 -or $taskValidation.logical_directed_NN_records -ne 1949696 -or $taskValidation.unique_brute_NN_records -ne 1703936 -or $taskValidation.explicit_aliases -ne 30){throw 'Complete population/aliases mismatch'}
if($taskResult.optimizer_calls -ne 0 -or $taskValidation.optimizer_neural_graph_calls -ne 0 -or $taskValidation.reference_truth_certified){throw 'Unexpected scientific expansion'}
if($taskResult.summary.decision -ne $taskValidation.summary.decision){throw 'Decision mismatch'}
if(@($taskFreeze.files.PSObject.Properties).Count -ne 1910 -or @($taskAmend.files.PSObject.Properties).Count -ne 13){throw 'Freeze counts mismatch'}
$taskIdentities=@(); $taskLinux=@(); $taskOriginalValidator=$null
foreach($taskEntry in $taskFreeze.files.PSObject.Properties){
    if($taskEntry.Name -eq $taskAmend.original_validator_path){
        $taskPath=Map-RpcPath $taskAmend.original_validator_snapshot
        $taskHash=Check-RpcHash $taskPath $taskEntry.Value
        if($taskHash -ne $taskAmend.original_validator_sha256){throw 'Original validator mismatch'}
        $taskOriginalValidator=[ordered]@{original_path=$taskEntry.Name;frozen_snapshot=$taskPath;original_sha256=$taskHash;repair_disclosed='AMENDMENT_01.md'}
    }elseif($taskEntry.Name.StartsWith('/mnt/e/')){
        $taskPath=Map-RpcPath $taskEntry.Name; $taskHash=Check-RpcHash $taskPath $taskEntry.Value
        $taskIdentities+=[ordered]@{path=$taskPath;sha256=$taskHash}
    }elseif($taskEntry.Name.StartsWith('/root/')){
        $taskLinux+=[ordered]@{path=$taskEntry.Name;sha256=$taskEntry.Value;receipt='Successful independent Linux verify at end of validate02; no new Windows Linux hash'}
    }else{throw 'Unknown frozen path'}
}
foreach($taskEntry in $taskAmend.files.PSObject.Properties){$null=Check-RpcHash (Map-RpcPath $taskEntry.Name) $taskEntry.Value}
$null=Check-RpcHash (Map-RpcPath $taskAmend.original_validator_path) $taskAmend.repaired_validator_sha256
foreach($taskPair in @(@('bank','bank_seal.json'),@('evaluation','evaluation_seal.json'))){
    $taskFolder=Join-Path $taskBase $taskPair[0]; $taskSeal=Read-RpcJson (Join-Path $taskBase $taskPair[1])
    if($taskSeal.freeze_sha256 -ne (Get-FileHash (Join-Path $taskBase 'freeze.json')).Hash.ToLowerInvariant()){throw 'Seal/freeze mismatch'}
    if(@(Get-ChildItem $taskFolder -File -Recurse).Count -ne @($taskSeal.files.PSObject.Properties).Count){throw 'Seal file count mismatch'}
    foreach($taskEntry in $taskSeal.files.PSObject.Properties){$null=Check-RpcHash (Join-Path $taskFolder $taskEntry.Name) $taskEntry.Value}
}
Write-RpcJson (Join-Path $taskBase 'FINAL_IDENTITY_CHECK.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');passed=$true;total_original_frozen_identities=1910;Windows_current_identities=$taskIdentities;Linux_successful_validation_receipts=$taskLinux;original_validator_preserved=$taskOriginalValidator;validator_amendment_entries=13;corpus_and_evaluation_seals_pass=$true;repositories=$taskFreeze.repositories})
$taskStages=@('freeze','preflight','validate_preflight','bank','evaluate','validate','freeze02','validate_preflight02','validate02')
if(@(Get-ChildItem (Join-Path $taskBase 'supervision') -Directory).Count -ne 9){throw 'Unexpected child inventory'}
$taskReceipts=@(); $taskRetries=0; $taskGaps=0
foreach($taskStage in $taskStages){
    $taskDir=Join-Path $taskBase ('supervision/'+$taskStage)
    $taskChild=Read-RpcJson (Join-Path $taskDir 'child_exit.json'); $taskLaunch=Read-RpcJson (Join-Path $taskDir 'launch.json'); $taskHost=Read-RpcJson (Join-Path $taskDir 'exit.json')
    if(-not $taskChild.full_resource_capture -or $taskChild.peak_RSS_bytes -gt 2GB -or $taskChild.optimizer_neural_graph_calls -ne 0 -or $taskLaunch.headroom_before_bytes -lt 12GB){throw 'Child/launch caps or records incomplete'}
    $taskExpected=if($taskStage -eq 'validate'){1}else{0}
    if($taskHost.exit_code -ne $taskExpected -or $taskChild.success -ne ($taskExpected -eq 0)){throw 'Expected success/failure not preserved'}
    $taskSamples=@(Get-Content -LiteralPath (Join-Path $taskDir 'host_memory.jsonl')|ForEach-Object{$_|ConvertFrom-Json})
    $taskMinimum=($taskSamples.headroom_bytes|Measure-Object -Minimum).Minimum
    if(-not $taskSamples.Count -or $taskMinimum -lt 4GB -or $taskHost.host_memory_observations -ne $taskSamples.Count){throw 'Host guard/observation mismatch'}
    foreach($taskKind in @('logging_retry','logging_gap')){
        $taskLog=Join-Path $taskDir ($taskKind+'.jsonl')
        if(Test-Path -LiteralPath $taskLog){$taskCount=@(Get-Content -LiteralPath $taskLog).Count;if($taskKind -eq 'logging_retry'){$taskRetries+=$taskCount}else{$taskGaps+=$taskCount}}
    }
    $taskReceipts+=[ordered]@{stage=$taskStage;child=$taskChild;host=$taskHost;launch=$taskLaunch;host_observations=$taskSamples.Count;minimum_observed_headroom_bytes=$taskMinimum}
}
$taskWall=($taskReceipts.child.wall_seconds|Measure-Object -Sum).Sum; $taskPeak=[long]($taskReceipts.child.peak_RSS_bytes|Measure-Object -Maximum).Maximum
$taskBytes=[long](Get-ChildItem $taskBase -File -Recurse|Measure-Object Length -Sum).Sum
if($taskWall -ge 900 -or $taskBytes -ge 256MB){throw 'Combined payload/artifact cap'}
foreach($taskMarker in @('docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE','docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE')){if(-not(Test-Path -LiteralPath (Join-Path $taskRoot $taskMarker))){throw 'Old NOC4 marker missing'}}
Write-RpcJson (Join-Path $taskBase 'RESOURCE_AUDIT.json') ([ordered]@{passed=$true;children=9;successful=8;retained_validation_failures=1;full_child_RSS_and_time_records=$true;windows_exit_records=9;all_windows_exits_captured=$true;payload_wall_seconds=$taskWall;peak_RSS_bytes=$taskPeak;artifact_bytes_before_closing_metadata=$taskBytes;windows_process_wall_seconds=($taskReceipts.host.wall_seconds|Measure-Object -Sum).Sum;logging_retry_records=$taskRetries;latest_pointer_gap_records=$taskGaps;minimum_observed_headroom_bytes=($taskReceipts.minimum_observed_headroom_bytes|Measure-Object -Minimum).Minimum;CPU_only=$true;GPU_calls=0;setup_full_RSS_unknown=$true;payload_time_excludes_imports_WSL_startup_design_final_bookkeeping=$true;RSS_includes_imports=$true;old_gaps_and_caps_not_amended=$true;approval_service_nonexecution=1;receipts=$taskReceipts})
Write-RpcJson (Join-Path $taskBase 'CHECKS.json') ([ordered]@{passed=$true;bounded_diagnostic_complete=$true;all_original_1910_identities_accounted=$true;validator_repair_preserved_and_separately_frozen=$true;amendment_entries=13;raw_records=1380000;retained_points=45056;scans=11;revisit_pairs=15;immediate_pairs=7;independent_validation=$taskValidation;resource_caps_scientific_children=$true;all_setup_capture_claim=$false;optimizer_neural_graph_calls=0;physical_reference_truth_certified=$false;new_system_metric_gain=$false;old_NOC4_INCOMPLETE_preserved=$true;commit_or_sync=$false})
$taskStatus=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='VALIDATED_BOUNDED_REFERENCE_PHYSICAL_DIAGNOSIS_COMPLETE_WITH_VALIDATOR_REPAIR';decision=$taskResult.summary.decision;diagnostic_complete=$true;physical_cause_resolved=$false;independent_validation_passed=$true;scans=11;revisit_pairs=15;local_pairs=7;optimizer_neural_graph_calls=0;reference_replacement=$false;new_system_metrics=$false;payload_wall_seconds=$taskWall;peak_RSS_bytes=$taskPeak;next_boundary='DESIGN_ONLY changed causal observation context/submap feasibility; no exact local/refinement/reference rescue';old_gaps_retained=$true;commit_or_sync=$false}
[System.IO.File]::WriteAllText((Join-Path $taskBase 'STATUS.json'),($taskStatus|ConvertTo-Json -Depth 20)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $taskBase 'closure_source_snapshot.ps1')
$taskMarker=Join-Path $taskBase 'INCOMPLETE'; if(Test-Path -LiteralPath $taskMarker){Remove-Item -LiteralPath $taskMarker}
$taskRows=@(Get-ChildItem $taskBase -File -Recurse|Sort-Object FullName|ForEach-Object{[ordered]@{path=[System.IO.Path]::GetRelativePath($taskBase,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
if(($taskRows.bytes|Measure-Object -Sum).Sum -ge 256MB){throw 'Final pre-seal artifact cap'}
Write-RpcJson (Join-Path $taskBase 'DELIVERY_SEAL.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');status=$taskStatus.status;decision=$taskStatus.decision;entries=$taskRows.Count;files=$taskRows;physical_cause_unresolved=$true;validator_failure_and_repair_preserved=$true;old_gaps_not_amended=$true})
Write-Output ([ordered]@{status=$taskStatus.status;decision=$taskStatus.decision;entries=$taskRows.Count;payload_seconds=$taskWall;peak_RSS_bytes=$taskPeak;windows_exit_records=9;logging_retry_records=$taskRetries;logging_gap_records=$taskGaps}|ConvertTo-Json -Compress)
