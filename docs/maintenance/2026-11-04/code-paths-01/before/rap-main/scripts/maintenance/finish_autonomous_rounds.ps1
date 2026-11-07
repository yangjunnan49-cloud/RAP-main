# Owner-authorized bounded CCR0 completion followed by independent NBR0 diagnosis.
param()
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskDate=Join-Path $taskRoot 'docs/maintenance/2026-10-12'
$taskJournal=Join-Path $taskDate 'autonomous-continuation-01'
if(Test-Path -LiteralPath $taskJournal){throw 'Existing controller attempt must remain'}
New-Item -ItemType Directory -Path $taskJournal|Out-Null
$taskSources=@($PSCommandPath,(Join-Path $PSScriptRoot 'close_causal_context.py'),(Join-Path $PSScriptRoot 'close_native_backward.py'))
$taskHashes=@(); foreach($taskSource in $taskSources){$taskHashes+=[ordered]@{path=$taskSource;sha256=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant()}}
[IO.File]::WriteAllText((Join-Path $taskJournal 'CONTROLLER_FREEZE.json'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');files=$taskHashes;scope='Sequential orchestration and standard-library metadata closure only; no scientific setting/gate changes'}|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$taskStage='wait_CCR0_bank';$taskStart=[DateTime]::UtcNow
function Record-TaskStage([string]$name){
    $script:taskStage=$name
    [IO.File]::AppendAllText((Join-Path $taskJournal 'progress.jsonl'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$name}|ConvertTo-Json -Compress)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
}
function Run-TaskStage([string]$scriptName,[string]$stageName,[string]$folderName){
    Record-TaskStage ($folderName+'/'+$stageName)
    & (Join-Path $PSScriptRoot 'invoke_mgr_supervised_wsl.ps1') -Script ('scripts/maintenance/'+$scriptName) -Stage $stageName -OutputDirectory (Join-Path $taskDate ($folderName+'/supervision'))
    if($LASTEXITCODE -ne 0){throw ('Retained child failed: '+$folderName+'/'+$stageName)}
}
function Close-TaskMetadata([string]$scriptName){
    Record-TaskStage $scriptName
    & wsl -d Ubuntu-24.04 -u root -- /root/miniconda3/envs/rap-inference/bin/python -u -B ('scripts/maintenance/'+$scriptName)
    if($LASTEXITCODE -ne 0){throw ('Metadata closure stopped: '+$scriptName)}
}
try{
    Record-TaskStage 'wait_CCR0_bank'
    $taskBankExit=Join-Path $taskDate 'causal-context-registration-01/supervision/bank/exit.json'
    while(-not (Test-Path -LiteralPath $taskBankExit)){
        if(([DateTime]::UtcNow-$taskStart).TotalSeconds -gt 5400){throw 'Existing bank supervision did not complete within bounded wait'}
        Start-Sleep -Seconds 2
    }
    $taskExit=Get-Content -LiteralPath $taskBankExit -Raw|ConvertFrom-Json
    if($taskExit.exit_code -ne 0){throw 'Existing CCR0 bank child failed; no dependent work'}
    foreach($taskNext in @('validate_bank','evaluate','validate_results')){Run-TaskStage 'causal_context_registration.py' $taskNext 'causal-context-registration-01'}
    Close-TaskMetadata 'close_causal_context.py'
    foreach($taskNext in @('freeze','diagnose','validate')){Run-TaskStage 'native_backward_reproducibility.py' $taskNext 'native-backward-reproducibility-01'}
    Close-TaskMetadata 'close_native_backward.py'
    Record-TaskStage 'two_rounds_validated_and_closed'
    [IO.File]::WriteAllText((Join-Path $taskJournal 'STATUS.json'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='TWO_ROUNDS_CLOSED';scientific_settings_changed=$false;old_NOC4_INCOMPLETE=$true;commit_or_sync=$false}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
}catch{
    [IO.File]::WriteAllText((Join-Path $taskJournal 'FAILURE.json'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$taskStage;error=$_.Exception.Message;automatic_retry=$false;dependent_work_stopped=$true}|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
    throw
}finally{
    [IO.File]::WriteAllText((Join-Path $taskJournal 'controller_exit.json'),([ordered]@{utc=[DateTime]::UtcNow.ToString('o');last_stage=$taskStage;external_wall_seconds=([DateTime]::UtcNow-$taskStart).TotalSeconds;scope='Orchestration/metadata time, separate from fully recorded scientific children'}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
}
