param([Parameter(Mandatory=$true)][string]$ObservationLog)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskRun=Join-Path $taskRoot 'docs/maintenance/2026-10-16/autonomous-continuation-01'
$taskHandoff=Join-Path $taskRoot 'docs/maintenance/2026-10-16/continuation-handoff-11'
$taskLog=[IO.Path]::GetFullPath($ObservationLog)
if(-not $taskLog.StartsWith($taskRun+[IO.Path]::DirectorySeparatorChar)){throw 'Observation outside current continuation'}
$taskLines=@(Get-Content -LiteralPath $taskLog|Where-Object {$_})
if(-not $taskLines.Count){throw 'No actual account observation'}
$taskActual=$taskLines[-1]|ConvertFrom-Json
if($taskActual.primary.resetsAt -ne 1792176615){throw 'Different allowance window; do not claim this window exhausted'}
if($taskActual.primary.usedPercent -lt 100 -and $taskActual.ordinaryUsageAllowed -ne $false){throw 'No actual exhaustion boundary'}
foreach($name in @('synthetic','build','consume','validation','inputs')){if(Test-Path -LiteralPath (Join-Path $taskRoot ('docs/maintenance/2026-10-16/regx-interface-contract-01/'+$name))){throw 'C0 state changed; this resource-wait close text is no longer applicable'}}
$taskExpected=Join-Path $taskRun 'LATE_CLOSE_SOURCE_BINDING.json'
$taskBinding=Get-Content -LiteralPath $taskExpected -Raw|ConvertFrom-Json
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash -ne $taskBinding.sha256){throw 'Late close source identity differs'}
$taskEnc=[Text.UTF8Encoding]::new($false)
function NewText([string]$Path,[string]$Value){$bytes=$taskEnc.GetBytes($Value);$f=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$f.Write($bytes)}finally{$f.Dispose()}}
$taskStop=[ordered]@{status='ACTUAL_CURRENT_WINDOW_ACCOUNT_BOUNDARY_OBSERVED';observed_primary=$taskActual.primary;ordinaryUsageAllowed_as_returned=$taskActual.ordinaryUsageAllowed;following_account_clock_UTC=$taskActual.following_account_clock_UTC;exact_tool_observation_timestamp='Not independently supplied; following clock recorded';record_write_UTC=[DateTime]::UtcNow.ToString('o');source_log=$taskLog;source_log_SHA256=(Get-FileHash -LiteralPath $taskLog -Algorithm SHA256).Hash.ToLowerInvariant();no_automatic_reset_resume=$true;original_research_objective_complete=$false;no_goal_status_changed=$true}
NewText (Join-Path $taskHandoff 'ACCOUNT_STOP.json') (($taskStop|ConvertTo-Json -Depth 12)+[Environment]::NewLine)
$taskSummary='Current-window account boundary: actual primary '+$taskActual.primary.usedPercent+'% / ordinaryUsageAllowed '+$taskActual.ordinaryUsageAllowed+'. OIC0 exact public reply complete; no new local checkpoint remedy or efficacy admission. C0 remains resource-gated: no numeric stage was launched by the active observer. Prior C0 source/budget/guard, all old seals/stops and owner outreach decline remain. No automatic reset resume; original research objective unresolved. Read continuation-handoff-11 ACCOUNT_STOP and autonomous-continuation-01 observations.'
$taskAgents=Join-Path $taskRoot 'AGENTS.md';$taskOriginal=[IO.File]::ReadAllText($taskAgents)
$taskTitle='# AGENTS.md — RAP / RAP-SLAM current handoff'
if(-not $taskOriginal.StartsWith($taskTitle)){throw 'Unexpected AGENTS header'}
[IO.File]::WriteAllText($taskAgents,$taskTitle+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine+[Environment]::NewLine+$taskOriginal.Substring($taskTitle.Length).TrimStart([char[]]"`r`n"),$taskEnc)
[IO.File]::AppendAllText((Join-Path $taskRoot 'docs/maintenance/2026-10-16/PHASE_RECORD.md'),[Environment]::NewLine+'## Actual Current-window Account Boundary'+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine,$taskEnc)
NewText (Join-Path $taskHandoff 'CLOSE_REPORT.md') ('# Actual current-window close'+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine+[Environment]::NewLine+'The resource observations are distinct from quota observations. The last actual headroom is in the retained logs; no later value is inferred. Source and resource prechecks are documented in PREPARATION_CHECKS.json. This late close is not a new scientific validation, numerical success or complete-system benchmark. Ordinary preparation/observer lifetime RSS remains UNKNOWN.'+[Environment]::NewLine)
$taskSnapshot=Join-Path $taskHandoff 'account_boundary_snapshot';New-Item -ItemType Directory -Path $taskSnapshot|Out-Null
foreach($p in @($taskAgents,(Join-Path $taskRoot 'docs/maintenance/2026-10-16/PHASE_RECORD.md'))){$target=Join-Path $taskSnapshot ([IO.Path]::GetFileName($p));$bytes=[IO.File]::ReadAllBytes($p);$f=[IO.FileStream]::new($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$f.Write($bytes)}finally{$f.Dispose()}}
$taskEntries=[ordered]@{}
foreach($f in Get-ChildItem -LiteralPath $taskHandoff -Recurse -File|Sort-Object FullName){if($f.Name -notin @('ACCOUNT_STOP_SEAL.json','DELIVERY_SEAL.json')){$taskEntries[$f.FullName.Substring($taskHandoff.Length+1).Replace('\','/')]=[ordered]@{bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}}}
NewText (Join-Path $taskHandoff 'ACCOUNT_STOP_SEAL.json') (([ordered]@{utc=[DateTime]::UtcNow.ToString('o');scope='Late actual account boundary, no science replay';files=$taskEntries}|ConvertTo-Json -Depth 12)+[Environment]::NewLine)
Write-Output ($taskStop|ConvertTo-Json -Depth 12 -Compress)
