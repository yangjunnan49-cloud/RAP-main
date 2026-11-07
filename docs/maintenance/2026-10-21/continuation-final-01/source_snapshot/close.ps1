$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $taskRoot 'outputs/continuation_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$account=Get-Content -Raw (Join-Path $out 'ACCOUNT_STATE.json') | ConvertFrom-Json
if($account.reset_id -ne $origin.reset_id){$stop='WINDOW_CHANGED_NOT_EXHAUSTION'}
elseif($account.used_percent -ge 100 -or -not $account.ordinary_usage_allowed){$stop='ACTUAL_ACCOUNT_BOUNDARY'}
else{throw 'No actual boundary: continuation remains active'}
$utf8=[Text.UTF8Encoding]::new($false)
$pattern='(overlap_validation_01/(validation_stage|validation_core|audit_adapted|assess_adapted|metrics_adapted)|guard_hardening_01/guard_child|boundary_contract_01/check_contract)'
$processes=@(& wsl -d Ubuntu-24.04 -u root -- /bin/ps -eo pid,pgid,args)
if($LASTEXITCODE -ne 0){throw 'Scoped process snapshot failed'}
$matches=@($processes | Where-Object {$_ -match $pattern})
[IO.File]::WriteAllText((Join-Path $out 'SCOPED_PROCESS_CHECK.json'),(@{utc=[DateTimeOffset]::UtcNow.ToString('o');matching_owned_commands=$matches;count=$matches.Count;scope='Exact continuation helper path patterns only; no global absence claim';processes_terminated=0} | ConvertTo-Json -Depth 4),$utf8)
if($matches.Count -ne 0){throw 'Owned helper still present; stop only after identity verification'}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\continuation-final-01'
if(Test-Path -LiteralPath $target){throw 'Do not replace prior handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md'
$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md')
Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 owner until-current5h-boundary continuation CLOSED: $stop; actual$($account.used_percent)%/ordinary$($account.ordinary_usage_allowed)/reset$($account.reset_id), following$($account.following_utc). No automatic reset resume. P0 independent validation COMPLETE all72/147552frames/88776segments, but queue4 CLOSED_EQUIVALENCE_FAIL: G time reduction12.64694% failsr1_06(~4.31mm>1mm); K18.61503% failsr1_00/r2_09. OriginalP0budgetFAIL9316.8147729/9000 andS1close6762.0941485/7200 unchanged. SerialG06 also varies; native causeUNKNOWN. Host-loss guard6synthetic controls and boundaryrecording21synthetic controls PASS, neither installed/integrated; 8source wrappers matchS1freeze. Four delivery seals281entries PASS; all72exact-roundtrip posesZIP delivered. Read docs/maintenance/2026-10-21/continuation-final-01/REPORT_CN,ACCOUNT_STATE,INTEGRITY_CHECKS,NEXT_NATIVE_OBSERVATION and full outputs C:/Users/AAA/Documents/Codex/2026-10-21/y/outputs/continuation_20261021. Plan only: integrate guards/recorder with controlled stubs before separately scoped real native stability work; no raw replay launch or queue4rescue. 0scoped helper matches on finalsnapshot; not global process certification. Original research objective unresolved, no newRAPincrement/default promotion. Oldfails/seals/stops plus production/default/Git/install/outreach/scheduler/goal-status limits retained.`r`n`r`n"
$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
if($split -le 1){throw 'Header delimiter missing'}
$added=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$added.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($added,0,$new,$split,$added.Length);[Array]::Copy($old,$split,$new,$split+$added.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new)
$recovered=New-Object byte[] $old.Length
[Array]::Copy($new,0,$recovered,0,$split)
[Array]::Copy($new,$split+$added.Length,$recovered,$split,$old.Length-$split)
$sha=[Security.Cryptography.SHA256]::Create()
$beforeHash=[BitConverter]::ToString($sha.ComputeHash($old))
$recoveredHash=[BitConverter]::ToString($sha.ComputeHash($recovered))
if($beforeHash -ne $recoveredHash){throw 'Original AGENTS bytes were not preserved'}
[IO.File]::WriteAllText((Join-Path $out 'HANDOFF_PRESERVATION.json'),(@{prior_AGENTS_preserved=$true;prior_sha256=$beforeHash;reconstructed_prior_sha256=$recoveredHash;inserted_bytes=$added.Length;prior_copy=(Join-Path $target 'AGENTS.before.md')} | ConvertTo-Json),$utf8)
[IO.File]::AppendAllText($phase,"`r`n### Oct21 current quota boundary and consolidated handoff`r`n`r`n"+$entry,$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$newBytes=0L
foreach($name in @('overlap_validation_01','guard_hardening_01','native_stability_review_01','boundary_contract_01','delivery_reconciliation_01')){$newBytes += [long](Get-ChildItem -LiteralPath (Join-Path $taskRoot ('work/'+$name)) -Recurse -File | Measure-Object -Property Length -Sum).Sum}
foreach($name in @('overlap_validation_20261021','guard_hardening_20261021','native_stability_review_20261021','boundary_contract_20261021','continuation_20261021')){$newBytes += [long](Get-ChildItem -LiteralPath (Join-Path $taskRoot ('outputs/'+$name)) -Recurse -File | Measure-Object -Property Length -Sum).Sum}
foreach($name in @('p0-validation-01','guard-hardening-01','native-stability-review-01','boundary-contract-01','continuation-final-01')){$newBytes += [long](Get-ChildItem -LiteralPath ('E:\githouse\RAP-main\docs\maintenance\2026-10-21\'+$name) -Recurse -File | Measure-Object -Property Length -Sum).Sum}
$reservedBytes=1MB
$growthPass=($newBytes+$reservedBytes -lt 64MB -and $newBytes+140458966L+$reservedBytes -lt 256MB)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$result=[ordered]@{stop=$stop;elapsed_seconds=$elapsed;cap_seconds=240;budget_compliant=($elapsed -lt 240);all_preparation_verification_documentation_included=$true;owner_continuation='CLOSED_AT_OBSERVED_BOUNDARY';automatic_reset_resume=$false;original_research_goal='UNRESOLVED';defaults_changed=$false;new_RAP_efficacy=$false;raw_reads=0;GT_reads=0;new_predictions=0}
$result.new_bytes_at_final_snapshot=$newBytes
$result.combined_bytes_at_final_snapshot=$newBytes+140458966L
$result.remaining_write_reserve_bytes=$reservedBytes
$result.growth_pass_including_reserve=$growthPass
if(-not $growthPass){throw 'Dossier growth guard failed'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_AND_STATUS_FINAL.json'),($result | ConvertTo-Json -Depth 4),$utf8)
Copy-Item -LiteralPath (Join-Path $out 'COSTS_AND_STATUS_FINAL.json') -Destination $target
Copy-Item -LiteralPath (Join-Path $out 'ACCOUNT_STATE.json') -Destination $target
Copy-Item -LiteralPath (Join-Path $out 'REPORT_CN.md') -Destination $target
Copy-Item -LiteralPath (Join-Path $out 'NEXT_NATIVE_OBSERVATION.md') -Destination $target
$entries=Get-ChildItem -LiteralPath $out -File | ForEach-Object {@{path=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'FINAL_SEAL.json'),($entries | ConvertTo-Json -Depth 4),$utf8)
$result | ConvertTo-Json -Depth 4
