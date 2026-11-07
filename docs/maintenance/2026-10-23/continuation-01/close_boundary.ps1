param([Parameter(Mandatory=$true)][string]$Observation)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskRecord=Get-Content -LiteralPath $Observation -Raw|ConvertFrom-Json
$taskText=@($taskRecord.usage_tool_result.content|Where-Object {$_.type -eq 'text'})[0].text
$taskUsage=$taskText|ConvertFrom-Json
$taskPrimary=$taskUsage.rateLimitsByLimitId.codex.primary
if($null -eq $taskPrimary){$taskPrimary=$taskUsage.rateLimits.primary}
$taskLimit=($taskUsage.ordinaryUsageAllowed -eq $false)
$taskWindowChanged=($null -ne $taskPrimary.resetsAt -and $taskPrimary.resetsAt -ne 1792736321)
$taskRecord|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $taskRoot 'ACCOUNT_STATE.json') -Encoding utf8NoBOM
if(-not $taskLimit -and -not $taskWindowChanged){
    $taskCurrent=Get-Content -LiteralPath (Join-Path $taskRoot 'CURRENT_STATE.json') -Raw|ConvertFrom-Json
    $taskCurrent.last_observed_used_percent=$taskPrimary.usedPercent
    $taskCurrent.ordinary_usage_allowed=$taskUsage.ordinaryUsageAllowed
    $taskCurrent.reset_id=$taskPrimary.resetsAt
    $taskCurrent|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $taskRoot 'CURRENT_STATE.json') -Encoding utf8NoBOM
    Write-Output ('Ordinary continuation still available at '+$taskPrimary.usedPercent+' percent.');exit 0
}
if(Test-Path -LiteralPath (Join-Path $taskRoot 'ACCOUNT_STOP.json')){throw 'Preserve the existing stop; do not duplicate or resume.'}
$taskClass=if($taskLimit){'ACTUAL_ACCOUNT_LIMIT_OBSERVED'}else{'WINDOW_ID_CHANGED_WITHOUT_OBSERVED_EXHAUSTION'}
$taskStop=[ordered]@{classification=$taskClass;primary_used_percent=$taskPrimary.usedPercent;ordinary_usage_allowed=$taskUsage.ordinaryUsageAllowed;reset_id=$taskPrimary.resetsAt;initial_reset_id=1792736321;following_clock=$taskRecord.following_clock;observation=$Observation;automatic_reset_resume=$false;pending_experiment=$false;all_numeric_scopes_closed=$true;research_goal='UNRESOLVED';manuscript='PAUSED';model_calls_completed_this_continuation=0;RI1='CLOSED_PRESTART_GPU_HEADROOM_FAIL';cause_or_rollover_inferred=$false}
$taskStop|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $taskRoot 'ACCOUNT_STOP.json') -Encoding utf8NoBOM
[ordered]@{owner_continuation='CLOSED_AT_OBSERVED_BOUNDARY';stop_classification=$taskClass;automatic_reset_resume=$false;pending_experiment=$false;research_goal='UNRESOLVED';manuscript='PAUSED';original_failures_and_caps_preserved=$true}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskRoot 'CURRENT_STATE.json') -Encoding utf8NoBOM
$taskAgents='E:\githouse\RAP-main\AGENTS.md'
$taskBefore=[IO.File]::ReadAllBytes($taskAgents)
[IO.File]::WriteAllBytes((Join-Path $taskRoot 'AGENTS.before_boundary.md'),$taskBefore)
$taskPrefix="# October 23 owner continuation closed at observed account boundary`n`nClassification: $taskClass. Observed primary $($taskPrimary.usedPercent) percent, ordinary usage $($taskUsage.ordinaryUsageAllowed), reset $($taskPrimary.resetsAt); see docs/maintenance/2026-10-23/continuation-01/ACCOUNT_STOP.json and ACCOUNT_STATE.json for exact following UTC clock. No reset-cause or rollover inference. No automatic resume or pending experiment.`n`nS2 static20 files/13 controls complete; SI1 57 source assertions/233577 Decimal checks with original negative-label limitation retained; EV1 separately verifies54 exports/26 controls/98982 Decimal coordinates including actual missing-center rejection; RA1 physical efficacy NOT ADMITTED. RI1 closed at original GPU>=9216MiB-free preflight failure, no point decode/model load/RAP or ICP call, no retry. FF1 ten CPU controls confirm NumPy fallback .dim() defect and zero-descriptor rejection. Proposed fix is uninstalled text only. All numerical scopes closed; exact helper matches0 and WSL Stopped restored. Existing E VHD/backup/compatibility Junction remain.`n`nOriginal research UNRESOLVED, manuscript PAUSED. All old failures, budgets, stops, source/reference boundaries and default/production/install/Git/outreach/scheduler/goal-status limits remain. Read continuation-01/REPORT.md and the six dated scope dossiers; old AGENTS bytes remain below and in before files.`n`n---`n`n"
$taskPrefixBytes=[Text.UTF8Encoding]::new($false).GetBytes($taskPrefix)
$taskCombined=[byte[]]::new($taskPrefixBytes.Length+$taskBefore.Length)
[Array]::Copy($taskPrefixBytes,0,$taskCombined,0,$taskPrefixBytes.Length)
[Array]::Copy($taskBefore,0,$taskCombined,$taskPrefixBytes.Length,$taskBefore.Length)
[IO.File]::WriteAllBytes($taskAgents,$taskCombined)
$taskNote="`n`n## Actual owner-window boundary`n`n$taskClass; primary $($taskPrimary.usedPercent) percent, ordinary usage $($taskUsage.ordinaryUsageAllowed), reset $($taskPrimary.resetsAt). Exact observation/following UTC clock in continuation-01/ACCOUNT_STOP.json. All finite scopes closed, RI1 resource failure unretried, no pending experiment or automatic reset resume. Original research/manuscript/stops remain.`n"
[IO.File]::AppendAllText('E:\githouse\RAP-main\docs\maintenance\2026-10-23\PHASE_RECORD.md',$taskNote,[Text.UTF8Encoding]::new($false))
[IO.File]::AppendAllText((Join-Path $taskRoot 'REPORT.md'),$taskNote,[Text.UTF8Encoding]::new($false))
$taskStop|ConvertTo-Json -Depth 8
