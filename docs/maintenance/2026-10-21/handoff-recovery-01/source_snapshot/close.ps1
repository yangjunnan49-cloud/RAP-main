$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/handoff_recovery_20261021'
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\handoff-recovery-01'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
if(Test-Path -LiteralPath $target){throw 'Preserve existing handoffs'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md')
Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 evening explicit owner again requests continuation until current5h quota exhausted. New actual1%/ordinarytrue/reset1792606845 at13:20:45UTC; this is explicit authorization, NOT automatic reset resume. Previous actual100%/ordinaryfalse/reset1792582782 at07:29:57UTC retained. Prior final elevated close was not executed because automatic approval review hit the usage limit; retry now authorized/available and COMPLETE. Old240s documentary closure honestly FAILS at21286.351482s including stopped interval; do not reset/exclude gap or alter the four previously closed scientific/engineering scope costs. Read continuation-final-01/snapshot/REVIEW_FAILURE and COSTS_AND_STATUS_FINAL, prior281sealed hashes PASS/0scoped processmatches. New finite handoff recovery does not repair oldcap. Current next: separately frozen synthetic integration of immutable host-loss guard and boundary recorder with strong stub nonintervention/exception controls, then decide whether a complete native stability scope is justified. No real native/raw/GT payload admitted yet, P0queue4 remainsCLOSED_EQUIVALENCE_FAIL and oldP0budgetFAIL; native causeUNKNOWN, original research goal unresolved. Preserve all oldfails/seals/stops plus production/default/Git/install/model/outreach/scheduler/goal-status limits. Full new-window outputs C:/Users/AAA/Documents/Codex/2026-10-21/y/outputs/handoff_recovery_20261021.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents)
$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 evening explicit continuation and prior close recovery`r`n`r`n"+$entry,$utf8)
Copy-Item -LiteralPath (Join-Path $root 'outputs/continuation_20261021/ACCOUNT_STATE.json') -Destination (Join-Path $out 'PRIOR_ACCOUNT_BOUNDARY.json')
Copy-Item -LiteralPath (Join-Path $root 'outputs/continuation_20261021/REVIEW_FAILURE.json') -Destination $out
Copy-Item -LiteralPath (Join-Path $root 'outputs/continuation_20261021/COSTS_AND_STATUS_FINAL.json') -Destination (Join-Path $out 'PRIOR_CLOSE_COSTS.json')
[IO.File]::WriteAllText((Join-Path $out 'OWNER_SCOPE.md'),$entry,$utf8)
$elapsed=([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds
$result=@{closed=$true;elapsed_seconds=$elapsed;cap_seconds=240;budget_compliant=($elapsed -lt 240);prior_documentary_cap_failed=$true;old_caps_unchanged=$true;current_quota_reset=1792606845;current_continuation='ACTIVE';new_predictions=0;raw_reads=0;GT_reads=0}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_AND_STATUS.json'),($result | ConvertTo-Json),$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$result | ConvertTo-Json
