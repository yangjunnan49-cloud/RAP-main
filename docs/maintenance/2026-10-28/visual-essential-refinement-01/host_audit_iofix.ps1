param([Parameter(Mandatory=$true)][ValidateSet('audit')][string]$Stage)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskRunRoot=Join-Path $taskRoot 'runtime03'
$taskOut=Join-Path $taskRunRoot $Stage
$taskPreflight=Join-Path $taskRunRoot ($Stage+'.PREFLIGHT.json')
if((Test-Path -LiteralPath $taskOut) -or (Test-Path -LiteralPath $taskPreflight)){throw 'One correction launch only; preserve all receipts'}
$taskPython='C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskMethod=Get-Content -LiteralPath (Join-Path $taskRoot 'METHOD.json') -Raw | ConvertFrom-Json
$taskOrigin=[DateTimeOffset]::Parse($taskMethod.scope_origin_utc)
if(([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds -ge ($taskMethod.whole_scope_seconds-$taskMethod.closure_reserve_seconds)){throw 'Original scope closure reserve'}
foreach($taskFreezeName in @('SOURCE_FREEZE.json','RUNTIME03_FREEZE.json','AUDIT_IOFIX_FREEZE.json')){
    $taskFreeze=Get-Content -LiteralPath (Join-Path $taskRoot $taskFreezeName) -Raw | ConvertFrom-Json
    foreach($taskEntry in $taskFreeze.files){$taskP=Join-Path $taskRoot $taskEntry.path;if((Get-FileHash -LiteralPath $taskP -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw ('Source freeze changed: '+$taskP)}}
}
$taskPrior=@{probe='controls';predict='runtime03/probe';evaluate='runtime03/predict';audit='runtime03/evaluate'}[$Stage]
$taskPriorDir=Join-Path $taskRoot $taskPrior
$taskPriorSeal=Get-Content -LiteralPath (Join-Path $taskPriorDir 'SEAL.json') -Raw | ConvertFrom-Json
foreach($taskEntry in $taskPriorSeal.files){if((Get-FileHash -LiteralPath (Join-Path $taskPriorDir $taskEntry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw 'Preceding seal changed'}}
$taskPriorExit=Get-Content -LiteralPath (Join-Path $taskPriorDir 'HOST_EXIT.json') -Raw | ConvertFrom-Json
if(-not $taskPriorExit.passed){throw 'Preceding stage not passed'}
$taskOldFailure=Get-Content -LiteralPath (Join-Path $taskRoot 'predict/HOST_EXIT.json') -Raw | ConvertFrom-Json
if($taskOldFailure.passed -or -not $taskOldFailure.no_live_owned_process){throw 'Old integration failure receipt mismatch'}
$taskCharged=[double]$taskOldFailure.elapsed_seconds
foreach($taskOldRel in @('runtime02/probe/HOST_EXIT.json','runtime02/predict/HOST_EXIT.json')){$taskOldAttempt=Get-Content -LiteralPath (Join-Path $taskRoot $taskOldRel) -Raw|ConvertFrom-Json;if(-not $taskOldAttempt.no_live_owned_process){throw 'Unreaped earlier child'};$taskCharged+=[double]$taskOldAttempt.elapsed_seconds}
if(Test-Path -LiteralPath (Join-Path $taskRunRoot 'probe/HOST_EXIT.json')){$taskProbe=Get-Content -LiteralPath (Join-Path $taskRunRoot 'probe/HOST_EXIT.json') -Raw|ConvertFrom-Json;$taskCharged+=[double]$taskProbe.elapsed_seconds}
$taskLimit=if($Stage -eq 'probe'){[Math]::Min(30,300-$taskCharged)}elseif($Stage -eq 'predict'){300-$taskCharged}else{[double]$taskMethod.stage_seconds.$Stage}
if($taskLimit -le 0){throw 'Original stage budget depleted'}
$taskQuery=[Diagnostics.Stopwatch]::StartNew()
try{
    $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory;$taskQuery.Stop()
    $taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
    $taskGate=$taskHeadroom -ge $taskMethod.headroom_bytes -and $taskQuery.Elapsed.TotalSeconds -le $taskMethod.query_seconds
    @{utc=[DateTimeOffset]::UtcNow.ToString('o');passed=$taskGate;headroom_bytes=$taskHeadroom;query_seconds=$taskQuery.Elapsed.TotalSeconds;original_prediction_seconds_charged=$taskCharged;this_stage_seconds_limit=$taskLimit}|ConvertTo-Json|Set-Content -LiteralPath $taskPreflight -Encoding UTF8
    if(-not $taskGate){throw 'Original fresh 12GiB/2s gate failed'}
}catch{if(-not(Test-Path -LiteralPath $taskPreflight)){@{passed=$false;error=$_.Exception.Message;utc=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath $taskPreflight -Encoding UTF8};throw}
New-Item -ItemType Directory -Path $taskOut | Out-Null
$taskScript=@{probe='cold_probe_runtime03.py';predict='predict_runtime03.py';evaluate='evaluate_runtime03.py';audit='audit_runtime03_iofix.py'}[$Stage]
$taskEnvNames=@('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS');$taskOldEnv=@{}
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
try{
    foreach($taskEnvName in $taskEnvNames){$taskOldEnv[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process');[Environment]::SetEnvironmentVariable($taskEnvName,'1','Process')}
    $taskProcess=Start-Process -FilePath $taskPython -ArgumentList @('-I','-B',(Join-Path $taskRoot $taskScript)) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskOut 'stdout.log') -RedirectStandardError (Join-Path $taskOut 'stderr.log')
}finally{foreach($taskEnvName in $taskEnvNames){[Environment]::SetEnvironmentVariable($taskEnvName,$taskOldEnv[$taskEnvName],'Process')}}
@{pid=$taskProcess.Id;launched_utc=[DateTimeOffset]::UtcNow.ToString('o');script=$taskScript;stage=$Stage}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskOut 'OWNED_PROCESS.json') -Encoding UTF8
$taskPeak=0L;$taskForced=$false;$taskError=$null
try{
    while(-not $taskProcess.HasExited){
        $taskProcess.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProcess.PeakWorkingSet64)
        $taskSize=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File|Measure-Object Length -Sum).Sum
        if($taskTimer.Elapsed.TotalSeconds -ge $taskLimit -or $taskPeak -gt $taskMethod.child_peak_bytes -or $taskSize -gt $taskMethod.dossier_bytes -or ([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds -ge ($taskMethod.whole_scope_seconds-$taskMethod.closure_reserve_seconds)){throw 'Original wall/RSS/dossier/scope cap'}
        Start-Sleep -Milliseconds 100
    }
}catch{$taskError=$_.Exception.Message;if(-not $taskProcess.HasExited){$taskProcess.Kill();$taskForced=$true}}
$taskProcess.WaitForExit();$taskProcess.Refresh()
$taskChildPeak=$null;$taskChildPass=$false
if(Test-Path -LiteralPath (Join-Path $taskOut 'RESULT.json')){$taskResult=Get-Content -LiteralPath (Join-Path $taskOut 'RESULT.json') -Raw|ConvertFrom-Json;$taskChildPass=$taskResult.passed;$taskChildPeak=$taskResult.child_lifetime_peak_bytes}
$taskSize=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File|Measure-Object Length -Sum).Sum
$taskPassed=$taskProcess.ExitCode -eq 0 -and -not $taskError -and $taskChildPass -and $taskChildPeak -le $taskMethod.child_peak_bytes -and $taskTimer.Elapsed.TotalSeconds -lt $taskLimit -and $taskSize -le $taskMethod.dossier_bytes
@{passed=$taskPassed;exit_code=$taskProcess.ExitCode;elapsed_seconds=$taskTimer.Elapsed.TotalSeconds;host_poll_peak_bytes=$taskPeak;child_lifetime_peak_bytes=$taskChildPeak;forced_stop=$taskForced;error=$taskError;no_live_owned_process=$taskProcess.HasExited;exit_utc=[DateTimeOffset]::UtcNow.ToString('o');original_prediction_seconds_precharged=$taskCharged;stage_limit_seconds=$taskLimit}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskOut 'HOST_EXIT.json') -Encoding UTF8
if(-not $taskPassed){throw ('Correction stage failed: '+$Stage)}
$taskEntries=@(Get-ChildItem -LiteralPath $taskOut -Recurse -File|Sort-Object FullName|ForEach-Object{@{path=[IO.Path]::GetRelativePath($taskOut,$_.FullName).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}})
@{sealed_utc=[DateTimeOffset]::UtcNow.ToString('o');files=$taskEntries;runtime_correction_freeze_sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'RUNTIME03_FREEZE.json') -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $taskOut 'SEAL.json') -Encoding UTF8
Write-Output ('ER1 codec correction '+$Stage+' PASS; sealed; reaped')
