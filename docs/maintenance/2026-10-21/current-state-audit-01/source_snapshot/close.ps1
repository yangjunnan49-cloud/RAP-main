$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/current_state_audit_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$checks=Get-Content -Raw (Join-Path $out 'CHECKS.json') | ConvertFrom-Json
if(-not $checks.all_seals_match -or $checks.C0_completed_stages -ne 4){throw 'State audit incomplete'}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\current-state-audit-01'
if(Test-Path -LiteralPath $target){throw 'Preserve old state audit'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 currentfact audit COMPLETE: C0custominterface ALREADY completedOct17~12:24UTC (all4stages/56557points), original22.614594/900s,19bindings match. PreservedRUNBOOK/STATUS/REPORT/INCOMPLETE and earlierresourcechecks are historical; NUMERIC_REPORT/CHECKS/COSTS+NUMERIC_DELIVERY_SEAL govern completion. DoNOTrestartC0fornewheadroom orspendits877.385406balance asautomaticmodelpayload.1005entries acrossC0preparation+numeric andcurrentclosedseals allmatch, no stage/pointnumericdecode/model/fit/solver ran. Read docs/maintenance/2026-10-21/current-state-audit-01/snapshot/CURRENT_STATE.json+REPORT_CN+CHECKS (datedscopeIDs/evidenceSHA/currentstatus), nothistoricalACTIVEalone. S1completebut07ter/10rerFAIL/noRAP; P0validatedbutG/Kqueue4CLOSED_EQFAIL+oldbudgetFAIL; N1incomplete16MiBcap; N2complete diagnosticfirstICP564/2.71um/causeUNKNOWN, no4.31mm explanation. Originalresearchgoalunresolved/manuscriptpaused. Next bounded possible interfacework only: public-input normalization/sharedscale/rigidprediction-recovery syntheticcontract, no canonical/model/physicaltruth/efficacyclaim oractualRAPinference. Defaultfolderloader internalreference hazard remains; no automaticC0efficacy/oldfamilyrescue. Actual71%/ordinarytrue/reset1792606845 lastobserved NOTexhaustion; ownercontinuationACTIVE. Originalcaps/stops/production/default/Git/install/outreach/scheduler/goalstatuslimits retained.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 current-state audit; C0 completion supersedes pending runbook`r`n`r`n"+$entry,$utf8)
$elapsed=([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds
$cost=@{status='CLOSED_READ_ONLY_PASS';elapsed_seconds=$elapsed;cap_seconds=900;budget_compliant=($elapsed -lt 900);conservative_origin_includes_earlier_C0_reading=$true;sealed_entries=1005;C0_source_bindings=19;old_C0_not_replayed=$true;point_numeric_decodes=0;new_scientific_launches=0;original_research_goal='UNRESOLVED';owner_continuation='ACTIVE'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($cost | ConvertTo-Json),$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse;Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File | ForEach-Object {@{path=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$cost | ConvertTo-Json
