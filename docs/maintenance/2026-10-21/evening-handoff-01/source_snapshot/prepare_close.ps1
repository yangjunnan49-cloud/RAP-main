$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/evening_handoff_20261021'
$costPaths=@('outputs/handoff_recovery_20261021/COSTS_AND_STATUS.json','outputs/guard_recorder_integration_20261021/COSTS_FINAL.json','outputs/native_stability_control_20261021/COSTS_FINAL.json','outputs/chunk_hash_feasibility_20261021/COSTS_FINAL.json','outputs/native_stability_stream_20261021/COSTS_FINAL.json','outputs/current_state_audit_20261021/COSTS_FINAL.json','outputs/custom_normalization_contract_20261021/COSTS_FINAL.json')
$costs=@($costPaths | ForEach-Object {$path=Join-Path $root $_;@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash;closed_receipt=(Get-Content -Raw $path | ConvertFrom-Json)}})
$utf8=[Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $out 'CLOSED_SCOPES.json'),(@{current_window_scopes=$costs;do_not_sum_overlapping_origins=$true;prior_recovered_documentary_failure='outputs/continuation_20261021/COSTS_AND_STATUS_FINAL.json';no_cap_reset=$true} | ConvertTo-Json -Depth 8),$utf8)
$sealChecks=@()
foreach($name in @('current_state_audit_20261021','custom_normalization_contract_20261021')){
    $dir=Join-Path $root ('outputs/'+$name);$seal=Get-Content -Raw (Join-Path $dir 'DELIVERY_SEAL.json') | ConvertFrom-Json;$bad=@()
    foreach($entry in $seal){if((Get-FileHash -LiteralPath (Join-Path $dir $entry.path)).Hash -ne $entry.sha256){$bad+=$entry.path}}
    if($bad.Count -ne 0){throw 'New delivery seal mismatch'}
    $sealChecks+=@{scope=$name;entries=@($seal).Count;passed=$true}
}
$all=@(& wsl -d Ubuntu-24.04 -u root -- /bin/ps -eo pid,pgid,args)
if($LASTEXITCODE -ne 0){throw 'Final scoped process snapshot failed'}
$matches=@($all | Where-Object {$_ -match '(guard_recorder_integration_01|native_stability_control_01|native_stability_stream_02|chunk_hash_feasibility_01|custom_normalization_contract_01)/(lease_runner02?|worker|native_stage|grandchild)\.py'})
if($matches.Count -ne 0){throw 'Owned numerical helper remains'}
$newBytes=0L
foreach($top in @('work','outputs')){$newBytes += [long](Get-ChildItem -LiteralPath (Join-Path $root $top) -File -Recurse | Measure-Object Length -Sum).Sum}
foreach($name in @('p0-validation-01','guard-hardening-01','native-stability-review-01','boundary-contract-01','continuation-final-01','handoff-recovery-01','guard-recorder-integration-01','native-stability-control-01','chunk-hash-feasibility-01','native-stability-stream-02','current-state-audit-01','custom-normalization-contract-01')){$newBytes += [long](Get-ChildItem -LiteralPath ('E:\githouse\RAP-main\docs\maintenance\2026-10-21\'+$name) -File -Recurse | Measure-Object Length -Sum).Sum}
$reserve=1MB
if($newBytes+$reserve -gt 64MB -or $newBytes+140458966L+$reserve -gt 256MB){throw 'Final dossier including closure reserve exceeds original caps'}
[IO.File]::WriteAllText((Join-Path $out 'FINAL_CHECKS.json'),(@{utc=[DateTimeOffset]::UtcNow.ToString('o');prior_verified_sealed_entries=1005;new_seal_checks=$sealChecks;scoped_live_helper_matches=0;not_global_process_certification=$true;new_bytes_at_snapshot=$newBytes;combined_bytes_at_snapshot=$newBytes+140458966L;closure_reserve_bytes=$reserve;new_cap_bytes=64MB;combined_cap_bytes=256MB;growth_pass_including_reserve=$true;all_current_finite_scopes_closed=$true;no_new_payload=$true} | ConvertTo-Json -Depth 5),$utf8)
$account=Get-Content -Raw (Join-Path $out 'ACCOUNT_STATE.json') | ConvertFrom-Json
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\evening-handoff-01'
if(Test-Path -LiteralPath $target){throw 'Preserve previous evening handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 evening finite work CLOSED and delivery pre-boundary check COMPLETE. Latestactual$($account.used_percent)%/ordinary$($account.ordinary_usage_allowed)/reset$($account.reset_id) at$($account.following_utc); notexhaustion unless actualboundary. AUTHORITATIVE OWNER WINDOW STOP when present: C:/Users/AAA/Documents/Codex/2026-10-21/y/outputs/evening_handoff_20261021/ACCOUNT_STOP.json plusACCOUNT_STATE; it supersedes this pre-boundaryACTIVE percentage without rewriting closed evidence. No new payload pending orautomaticresetresume. Sevennew finite scopes closed: handoffrecovery77.596s/240;watcher-recorder272.359s/900;N1incomplete925.789s/1800;chunkhash150.220s/600;N2complete697.440s/1800;stateaudit625.327s/900;CN1synthetic595.968s/1200, exactreceiptsCLOSED_SCOPES. Prior240sclosefailure21286.351482s explicitly retained. N2sameinputs2202frames/24830events firstICP564 after6340equal events, finalcoarse2.71um/causeUNKNOWN/no4.31mm explanation;2coarsetrajectoriesZIPPASS. C0ALREADYcompleteOct17 interfaceonly22.614594s,no replay;1005oldsealedentries+newsealsPASS,0scopedlivehelper matches. CN1customconditional17controls/9882+1647coordsPASS, noactualRAP/canonicalauth. Source-pointer staticreading shows existing2partbackend already recovers originalframe transforms consistently in algebra; doNOTrebuildmissinggenericrecovery. Remainingmeaningfulsourcequestion is custom/N-waybatch/anchor/features/outputsemantics/externalreference, no modeladmission. Read evening-handoff-01/snapshot/REPORT_CN,STATIC_OBSERVATION,NEXT_SOURCE_BINDING_PLAN,FINAL_CHECKS and CURRENT_STATE in priorstateaudit. Originalresearchunresolved/manuscriptpaused/P0closedFAIL/alloldcaps/stops/default/production/Git/install/outreach/scheduler/goalstatus limits retained.`r`n`r`n"
$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1;$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 evening finite scopes closed; authoritative workspace boundary marker`r`n`r`n"+$entry,$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse;Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$elapsed=([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds
[IO.File]::WriteAllText((Join-Path $out 'PRE_BOUNDARY_CLOSE.json'),(@{elapsed_seconds=$elapsed;cap_seconds=900;budget_compliant=($elapsed -lt 900);finite_delivery_complete=$true;actual_account_boundary_observed=($account.used_percent -ge 100 -or -not $account.ordinary_usage_allowed);workspace_boundary_marker_authoritative=$true;automatic_reset_resume=$false;new_payloads=0;original_research_goal='UNRESOLVED'} | ConvertTo-Json),$utf8)
$immutable=@(Get-ChildItem -LiteralPath $out -File | Where-Object {$_.Name -notin @('ACCOUNT_STATE.json','ACCOUNT_STOP.json','BOUNDARY_CLOSE.json','IMMUTABLE_DELIVERY_SEAL.json')} | ForEach-Object {@{path=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}})
[IO.File]::WriteAllText((Join-Path $out 'IMMUTABLE_DELIVERY_SEAL.json'),(@{files=$immutable;mutable_boundary_files_explicitly_excluded=@('ACCOUNT_STATE.json','ACCOUNT_STOP.json','BOUNDARY_CLOSE.json');reason='Record actual quota after immutable science/metadata closure without invalidating sealed evidence'} | ConvertTo-Json -Depth 5),$utf8)
[pscustomobject]@{finite_delivery_complete=$true;scoped_live_helpers=0;new_bytes=$newBytes;combined_bytes=$newBytes+140458966L;elapsed_seconds=$elapsed;boundary_marker_pending=($account.used_percent -lt 100 -and $account.ordinary_usage_allowed)} | ConvertTo-Json
