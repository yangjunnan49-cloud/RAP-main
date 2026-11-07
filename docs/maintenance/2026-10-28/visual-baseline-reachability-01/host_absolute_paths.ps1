param([Parameter(Mandatory=$true)][ValidateSet('controls','features','predict','evaluate','audit')][string]$Stage)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskPython='C:/Users/AAA/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskMethod=Get-Content -LiteralPath (Join-Path $taskRoot 'METHOD.json') -Raw | ConvertFrom-Json
$taskFreeze=Get-Content -LiteralPath (Join-Path $taskRoot 'SOURCE_FREEZE.json') -Raw | ConvertFrom-Json
$taskOut=Join-Path $taskRoot $Stage
$taskPreflight=Join-Path $taskRoot ($Stage+'.PREFLIGHT.json')
if((Test-Path -LiteralPath $taskOut) -or (Test-Path -LiteralPath $taskPreflight)){throw 'One launch only; retain prior stage/receipt'}
$taskOrigin=[DateTimeOffset]::Parse($taskMethod.scope_origin_utc)
$taskElapsed=([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds
if($taskElapsed -ge ($taskMethod.whole_scope_seconds-$taskMethod.closure_reserve_seconds)){throw 'Whole-scope closure reserve'}
$taskOwnHash=(Get-Content -LiteralPath (Join-Path $taskRoot 'HOST_RUNNER_FREEZE.json') -Raw | ConvertFrom-Json).sha256
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskOwnHash){throw 'Frozen host changed'}
foreach($taskEntry in $taskFreeze.files){
    $taskFile=$taskEntry.path
    if((Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw ('Frozen source changed: '+$taskEntry.path)}
}
$taskPrior=@{controls=$null;features='controls';predict='features';evaluate='predict';audit='evaluate'}[$Stage]
if($taskPrior){
    $taskPriorDir=Join-Path $taskRoot $taskPrior
    $taskPriorSeal=Get-Content -LiteralPath (Join-Path $taskPriorDir 'SEAL.json') -Raw | ConvertFrom-Json
    foreach($taskEntry in $taskPriorSeal.files){if((Get-FileHash -LiteralPath (Join-Path $taskPriorDir $taskEntry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256){throw 'Preceding seal mismatch'}}
    $taskPriorReceipt=Get-Content -LiteralPath (Join-Path $taskPriorDir 'HOST_EXIT.json') -Raw | ConvertFrom-Json
    if(-not $taskPriorReceipt.passed){throw 'Preceding stage not passed'}
}
$taskSize=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File | Measure-Object Length -Sum).Sum
if($taskSize -ge $taskMethod.dossier_bytes){throw 'Dossier cap before launch'}
$taskQuery=[Diagnostics.Stopwatch]::StartNew()
try{
    $taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
    $taskQuery.Stop()
    $taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
    $taskGate=($taskHeadroom -ge $taskMethod.headroom_bytes -and $taskQuery.Elapsed.TotalSeconds -le $taskMethod.query_seconds)
    @{utc=[DateTimeOffset]::UtcNow.ToString('o');headroom_bytes=$taskHeadroom;query_seconds=$taskQuery.Elapsed.TotalSeconds;passed=$taskGate} | ConvertTo-Json | Set-Content -LiteralPath $taskPreflight -Encoding UTF8
    if(-not $taskGate){throw 'Fresh 12GiB / 2s launch gate failed'}
}catch{if(-not(Test-Path -LiteralPath $taskPreflight)){@{utc=[DateTimeOffset]::UtcNow.ToString('o');passed=$false;error=$_.Exception.Message}|ConvertTo-Json|Set-Content -LiteralPath $taskPreflight -Encoding UTF8};throw}
New-Item -ItemType Directory -Path $taskOut | Out-Null
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
$taskEnvNames=@('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')
$taskOldEnv=@{}
try{
    foreach($taskEnvName in $taskEnvNames){$taskOldEnv[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process');[Environment]::SetEnvironmentVariable($taskEnvName,'1','Process')}
    $taskProcess=Start-Process -FilePath $taskPython -ArgumentList @('-I','-B',(Join-Path $taskRoot ($Stage+'.py'))) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskOut 'stdout.log') -RedirectStandardError (Join-Path $taskOut 'stderr.log')
}finally{foreach($taskEnvName in $taskEnvNames){[Environment]::SetEnvironmentVariable($taskEnvName,$taskOldEnv[$taskEnvName],'Process')}}
@{pid=$taskProcess.Id;launched_utc=[DateTimeOffset]::UtcNow.ToString('o');stage=$Stage;python=$taskPython}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskOut 'OWNED_PROCESS.json') -Encoding UTF8
$taskPeak=0L;$taskForced=$false;$taskError=$null
try{
    while(-not $taskProcess.HasExited){
        $taskProcess.Refresh();$taskPeak=[Math]::Max($taskPeak,$taskProcess.PeakWorkingSet64)
        $taskSize=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File | Measure-Object Length -Sum).Sum
        if($taskTimer.Elapsed.TotalSeconds -ge $taskMethod.stage_seconds.$Stage -or $taskPeak -gt $taskMethod.child_peak_bytes -or $taskSize -gt $taskMethod.dossier_bytes -or ([DateTimeOffset]::UtcNow-$taskOrigin).TotalSeconds -ge ($taskMethod.whole_scope_seconds-$taskMethod.closure_reserve_seconds)){throw 'Stage wall/RSS/dossier/scope limit'}
        Start-Sleep -Milliseconds 100
    }
}catch{$taskError=$_.Exception.Message;if(-not $taskProcess.HasExited){$taskProcess.Kill();$taskForced=$true}}
$taskProcess.WaitForExit();$taskProcess.Refresh()
$taskResultPath=Join-Path $taskOut 'RESULT.json'
$taskChildPeak=$null;$taskChildPass=$false
if(Test-Path -LiteralPath $taskResultPath){$taskResult=Get-Content -LiteralPath $taskResultPath -Raw | ConvertFrom-Json;$taskChildPeak=$taskResult.child_lifetime_peak_bytes;$taskChildPass=$taskResult.passed}
$taskSize=(Get-ChildItem -LiteralPath $taskRoot -Recurse -File | Measure-Object Length -Sum).Sum
$taskPassed=($taskProcess.ExitCode -eq 0 -and -not $taskError -and $taskChildPass -and $taskChildPeak -le $taskMethod.child_peak_bytes -and $taskTimer.Elapsed.TotalSeconds -lt $taskMethod.stage_seconds.$Stage -and $taskSize -le $taskMethod.dossier_bytes)
@{passed=$taskPassed;exit_code=$taskProcess.ExitCode;elapsed_seconds=$taskTimer.Elapsed.TotalSeconds;host_poll_peak_bytes=$taskPeak;child_lifetime_peak_bytes=$taskChildPeak;forced_stop=$taskForced;error=$taskError;no_live_owned_process=$taskProcess.HasExited;exit_utc=[DateTimeOffset]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskOut 'HOST_EXIT.json') -Encoding UTF8
if(-not $taskPassed){throw ('Stage failed: '+$Stage)}
$taskEntries=@(Get-ChildItem -LiteralPath $taskOut -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=[IO.Path]::GetRelativePath($taskOut,$_.FullName).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}})
@{sealed_utc=[DateTimeOffset]::UtcNow.ToString('o');files=$taskEntries}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $taskOut 'SEAL.json') -Encoding UTF8
Write-Output ('VB1 '+$Stage+' PASS, sealed, child reaped')
