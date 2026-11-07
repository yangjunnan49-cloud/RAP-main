$ErrorActionPreference='Stop'
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-12/measured-gicp-registration-01'
function Read-MgrJson([string]$taskPath){Get-Content -LiteralPath $taskPath -Raw|ConvertFrom-Json}
function Write-MgrJson([string]$taskPath,$taskValue){
    if(Test-Path -LiteralPath $taskPath){throw ('Immutable closing output already exists: '+$taskPath)}
    [System.IO.File]::WriteAllText($taskPath,($taskValue|ConvertTo-Json -Depth 40)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
}
$taskFreeze=Read-MgrJson (Join-Path $taskBase 'freeze.json')
$taskResult=Read-MgrJson (Join-Path $taskBase 'results.json')
$taskValidation=Read-MgrJson (Join-Path $taskBase 'result_validation.json')
if(-not $taskValidation.passed -or -not $taskResult.full58 -or $taskResult.records.Count -ne 58){throw 'Full58 validated result required'}
if($taskResult.gate.engineering_passed -or $taskResult.gate.increment_passed -or $taskResult.gate.decision -ne 'NO_SAFE_MEASURED_REGISTRATION_HEADROOM'){throw 'Unexpected gate outcome'}
if(Test-Path (Join-Path $taskBase 'graphs')){throw 'Dependent graph must remain unexecuted after failed gate'}
$taskIdentities=@(); $taskLinux=@()
foreach($taskEntry in $taskFreeze.files.PSObject.Properties){
    if($taskEntry.Name.StartsWith('/mnt/e/')){
        $taskPath='E:/'+$taskEntry.Name.Substring(7); $taskHash=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if($taskHash -ne $taskEntry.Value){throw ('Frozen identity changed: '+$taskPath)}
        $taskIdentities+=[ordered]@{path=$taskPath;sha256=$taskHash}
    }elseif($taskEntry.Name.StartsWith('/root/')){
        $taskLinux+=[ordered]@{path=$taskEntry.Name;sha256=$taskEntry.Value;receipt='Fresh successful frozen verify in validate_results; no new Windows Linux hash'}
    }else{throw 'Unknown frozen path'}
}
$taskAmend=Read-MgrJson (Join-Path $taskBase 'SUPERVISION_AMENDMENT_FREEZE02.json')
if($taskAmend.files.Count -ne 7){throw 'Complete supervision amendment required'}
foreach($taskEntry in $taskAmend.files){if((Get-FileHash -LiteralPath $taskEntry.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw 'Supervision amendment identity changed'}}
$taskSupplement=Read-MgrJson (Join-Path $taskBase 'SOURCE_SNAPSHOT_SUPPLEMENT.json')
foreach($taskEntry in $taskSupplement.files){if((Get-FileHash -LiteralPath (Join-Path $taskBase $taskEntry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw 'Frozen source supplement changed'}}
Write-MgrJson (Join-Path $taskBase 'FINAL_IDENTITY_CHECK.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');passed=$true;total_frozen_identities=$taskFreeze.files.PSObject.Properties.Count;windows_files=$taskIdentities;Linux_successful_validation_receipts=$taskLinux;supervision_amendment_entries=7;source_supplement_pass=$true;repositories=$taskFreeze.repositories})
$taskStages=@('freeze','freeze02','preflight','validate_preflight','inputs','validate_inputs','pilot','validate_pilot','bank','validate_bank','evaluate','validate_results')
if(@(Get-ChildItem (Join-Path $taskBase 'supervision') -Directory).Count -ne $taskStages.Count){throw 'Unexpected child attempt inventory'}
$taskReceipts=@(); $taskMissing=@(); $taskHostCount=0
foreach($taskStage in $taskStages){
    $taskDir=Join-Path $taskBase ('supervision/'+$taskStage); $taskChild=Read-MgrJson (Join-Path $taskDir 'child_exit.json'); $taskLaunch=Read-MgrJson (Join-Path $taskDir 'launch.json')
    if(-not $taskChild.full_resource_capture -or $taskChild.peak_RSS_bytes -gt 4GB -or $taskChild.CPU_binding -ne 'cpu' -or $taskChild.neural_calls -ne 0){throw 'Incomplete/capped child'}
    if($taskStage -eq 'freeze'){if($taskChild.success){throw 'Original prefreeze failure must be retained'}}else{if(-not $taskChild.success){throw 'Later child unexpectedly failed'}}
    if($taskLaunch.headroom_before_bytes -lt 12GB){throw 'Launch guard failed'}
    $taskHost=$null; $taskHostPath=Join-Path $taskDir 'exit.json'
    if(Test-Path -LiteralPath $taskHostPath){
        $taskHost=Read-MgrJson $taskHostPath; $taskHostCount++
        $taskExpected=if($taskStage -eq 'freeze'){1}else{0}; if($taskHost.exit_code -ne $taskExpected){throw 'Unexpected Windows exit'}
    }else{if($taskStage -ne 'validate_bank'){throw 'Unexpected missing Windows exit'}; $taskMissing+=$taskStage}
    $taskSamples=@(Get-Content (Join-Path $taskDir 'host_memory.jsonl')|ForEach-Object{$_|ConvertFrom-Json})
    if(-not $taskSamples.Count -or ($taskSamples.headroom_bytes|Measure-Object -Minimum).Minimum -lt 4GB){throw 'Host observations/guard failed'}
    if($taskHost -and $taskHost.host_memory_observations -ne $taskSamples.Count){throw 'Host count mismatch'}
    $taskReceipts+=[ordered]@{stage=$taskStage;child=$taskChild;host=$taskHost;launch=$taskLaunch;host_observations=$taskSamples.Count;minimum_observed_headroom_bytes=($taskSamples.headroom_bytes|Measure-Object -Minimum).Minimum}
}
$taskWall=($taskReceipts.child.wall_seconds|Measure-Object -Sum).Sum; $taskPeak=($taskReceipts.child.peak_RSS_bytes|Measure-Object -Maximum).Maximum
if($taskWall -ge 1800 -or $taskMissing.Count -ne 1 -or $taskHostCount -ne 11){throw 'Combined cap or expected supervision gap mismatch'}
$taskPred=@(Get-ChildItem (Join-Path $taskBase 'bank') -Filter '*_*.json' -File|ForEach-Object{Read-MgrJson $_.FullName})
$taskCount=0; $taskSupport=0
foreach($taskItem in $taskPred){foreach($taskName in @('RI','GI','GK','GF')){if($taskItem.candidates.$taskName.status -ne 'completed'){throw 'Reported232 completions mismatch'};$taskCount++};if($taskItem.candidates.RI.diagnostics.supported){$taskSupport++};if($taskItem.selector_W.fallback -or $taskItem.selector_J.fallback){throw 'Reported zero fallback mismatch'}}
if($taskCount -ne 232 -or $taskSupport -ne 58){throw 'Prediction count mismatch'}
$taskBytes=(Get-ChildItem $taskBase -File -Recurse|Measure-Object -Property Length -Sum).Sum; if($taskBytes -ge 512MB){throw 'Artifact cap'}
foreach($taskMarker in @('docs/maintenance/2026-10-10/native-conditioned-comparison-01/INCOMPLETE','docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/INCOMPLETE')){if(-not(Test-Path -LiteralPath (Join-Path $taskRoot $taskMarker))){throw 'Historical NOC4 marker missing'}}
Write-MgrJson (Join-Path $taskBase 'RESOURCE_AUDIT.json') ([ordered]@{passed=$true;scientific_children=12;successful=11;failed_prefreeze=1;all_child_wall_RSS_captured=$true;payload_wall_seconds=$taskWall;peak_RSS_bytes=$taskPeak;artifact_bytes_before_closing_metadata=$taskBytes;windows_exit_records=11;all_windows_exits_captured=$false;missing_windows_exit_stages=$taskMissing;validate_bank_late_host_gap_retained=$true;setup_full_RSS_unknown=$true;available_windows_process_wall_seconds=($taskReceipts.host.wall_seconds|Measure-Object -Sum).Sum;available_windows_wall_excludes_gap_stage=$true;minimum_observed_headroom_bytes=($taskReceipts.minimum_observed_headroom_bytes|Measure-Object -Minimum).Minimum;no_legacy_budget_amendment=$true;receipts=$taskReceipts})
$taskFalse=@($taskResult.gate.engineering_tests.PSObject.Properties|Where-Object {$_.Value -eq $false}).Count
Write-MgrJson (Join-Path $taskBase 'CHECKS.json') ([ordered]@{passed=$true;all58_measurements_validated=$true;scientific_engineering_gate=$false;engineering_tests=46;engineering_failed=$taskFalse;increment_tests=14;increment_failed=2;all_RI_supported=58;completed_refinement_outputs=232;FGR_failures=0;bundle_fallbacks=0;independent_validation=$taskValidation;source_identities=1567;resource_caps_scientific_children=$true;all_setup_and_Windows_capture_claim=$false;conditional_graph_calls=0;neural_calls=0;old_NOC4_markers_preserved=$true;commit_or_sync=$false})
$taskStatus=[ordered]@{status='VALIDATED_MEASUREMENT_COMPARISON_COMPLETE_WITH_PREFREEZE_AND_SUPERVISION_REPAIR';decision=$taskResult.gate.decision;scientific_comparison_complete=$true;engineering_gate_passed=$false;RAP_initializer_increment_passed=$false;relative_pose_pairs=58;independent_validation_passed=$true;conditional_graph_executed=$false;neural_calls=0;payload_wall_seconds=$taskWall;peak_RSS_bytes=$taskPeak;known_Windows_supervision_gap='validate_bank';setup_resource_gaps_retained=$true;next_boundary='DESIGN_ONLY reference/physical-consistency diagnosis; no exact GICP rescue';utc=[DateTime]::UtcNow.ToString('o');commit_or_sync=$false}
[System.IO.File]::WriteAllText((Join-Path $taskBase 'STATUS.json'),($taskStatus|ConvertTo-Json -Depth 10)+[Environment]::NewLine,[System.Text.UTF8Encoding]::new($false))
$taskMarker=Join-Path $taskBase 'INCOMPLETE'; if(Test-Path -LiteralPath $taskMarker){Remove-Item -LiteralPath $taskMarker}
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $taskBase 'closure_source_snapshot.ps1')
Copy-Item -LiteralPath (Join-Path $taskRoot 'scripts/maintenance/invoke_mgr_supervised_wsl.ps1') -Destination (Join-Path $taskBase 'supervision_source_snapshot.ps1')
$taskRows=@(Get-ChildItem $taskBase -File -Recurse|Sort-Object FullName|ForEach-Object{[ordered]@{path=[System.IO.Path]::GetRelativePath($taskBase,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
Write-MgrJson (Join-Path $taskBase 'DELIVERY_SEAL.json') ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');status=$taskStatus.status;decision=$taskStatus.decision;files=$taskRows;entries=$taskRows.Count;Windows_gap_retained=$true;conditional_graph_not_admitted=$true})
Write-Output ([ordered]@{status=$taskStatus.status;decision=$taskStatus.decision;entries=$taskRows.Count;payload_seconds=$taskWall;peak_RSS_bytes=$taskPeak;Windows_exit_records=$taskHostCount;known_gap=$taskMissing}|ConvertTo-Json -Compress)
