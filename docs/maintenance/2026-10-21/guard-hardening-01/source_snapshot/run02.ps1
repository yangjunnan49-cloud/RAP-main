$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot;$taskOut=Join-Path (Split-Path (Split-Path $taskRoot -Parent) -Parent) 'outputs\guard_hardening_20261021\run02'
$taskSources=[ordered]@{};foreach($taskFile in Get-ChildItem -LiteralPath $taskRoot -File|Where-Object {$_.Extension -in '.py','.ps1'}){$taskSources[$taskFile.Name]=(Get-FileHash -LiteralPath $taskFile.FullName).Hash}
[IO.File]::WriteAllText((Join-Path $taskOut 'SOURCE_FREEZE.json'),(@{files=$taskSources;scope='Synthetic-only guards; no numerical data';original_caps_unchanged=$true}|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$taskSummaries=@()
foreach($taskCase in @('normal','host_deadline','linux_deadline','observer_loss','bad_nonce','identity_rejection')){
    & (Join-Path $taskRoot 'host02.ps1') -Case $taskCase
    $taskCode=$LASTEXITCODE
    if($taskCase -eq 'observer_loss'){if($taskCode -ne 17){throw 'Observer fault injection did not exit as intended'}}elseif($taskCode -ne 0){throw ('Host case failed: '+$taskCase)}
    $taskDir=Join-Path $taskOut $taskCase;$taskWait=[Diagnostics.Stopwatch]::StartNew()
    while(-not(Test-Path -LiteralPath (Join-Path $taskDir 'child_exit.json')) -and $taskWait.Elapsed.TotalSeconds -lt 5){Start-Sleep -Milliseconds 50}
    if(-not(Test-Path -LiteralPath (Join-Path $taskDir 'child_exit.json'))){throw ('Child did not stop after observer exit: '+$taskCase)}
    $taskChild=Get-Content -Raw -LiteralPath (Join-Path $taskDir 'child_exit.json')|ConvertFrom-Json
    if($taskCase -eq 'normal'){if(-not $taskChild.success){throw 'Normal case failed'}}
    elseif($taskCase -eq 'observer_loss'){if($taskChild.error -ne 'host_lease_expired' -or $taskChild.stop_after_last_accepted_reply -gt 2.3){throw 'Observer-loss stop failed'}}
    elseif($taskCase -eq 'bad_nonce'){if($taskChild.error -ne 'nonce_or_sequence_mismatch'){throw 'Bad nonce admitted'}}
    elseif($taskChild.success){throw 'Expected controlled stop missing'}
    if($taskChild.peak_RSS_bytes -gt 512MB){throw 'Synthetic memory cap'}
    $taskSummaries+=@{case=$taskCase;passed=$true;child=$taskChild}
    Write-Output ($taskCase+' PASS '+$taskChild.error)
}
$taskOrigin=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'origin.json')|ConvertFrom-Json
$taskElapsed=[Math]::Max((([Diagnostics.Stopwatch]::GetTimestamp()-$taskOrigin.initialization_ticks)/$taskOrigin.frequency+$taskOrigin.conservative_prelude),([DateTimeOffset]::UtcNow-[DateTimeOffset]$taskOrigin.start_utc).TotalSeconds)
if($taskElapsed -gt 360){throw 'Hardening budget failed'}
[IO.File]::WriteAllText((Join-Path $taskOut 'RESULTS.json'),(@{passed=$true;cases=$taskSummaries;scope_seconds=$taskElapsed;cap_seconds=360;original_P0_equivalence='FAIL_RETAINED';scientific_payloads=0;OS_isolation_certified=$false}|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))

