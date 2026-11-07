param([Parameter(Mandatory=$true)][string]$ObservationLog)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskRun=Join-Path $taskRoot 'docs/maintenance/2026-10-17/autonomous-continuation-02'
$taskHandoff=Join-Path $taskRoot 'docs/maintenance/2026-10-17/continuation-handoff-12'
$taskLog=[IO.Path]::GetFullPath($ObservationLog)
if(-not $taskLog.StartsWith($taskRun+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Observation outside this continuation'}
$taskLines=@(Get-Content -LiteralPath $taskLog|Where-Object {$_})
if(-not $taskLines.Count){throw 'No actual account observation'}
$taskActual=$taskLines[-1]|ConvertFrom-Json
if($taskActual.primary.resetsAt -ne 1792217489){throw 'Different allowance window; do not claim this window exhausted'}
if($null -eq $taskActual.primary.usedPercent -or $null -eq $taskActual.ordinaryUsageAllowed){throw 'Incomplete account receipt'}
if($taskActual.primary.usedPercent -lt 100 -and $taskActual.ordinaryUsageAllowed -ne $false){throw 'No actual allowance boundary'}
foreach($name in @('synthetic','build','consume','validation','inputs')){
 if(Test-Path -LiteralPath (Join-Path $taskRoot ('docs/maintenance/2026-10-16/regx-interface-contract-01/'+$name))){throw 'C0 state changed; this preparation-only close no longer applies'}
}
$taskBinding=Get-Content -LiteralPath (Join-Path $taskRun 'LATE_CLOSE_SOURCE_BINDING.json') -Raw|ConvertFrom-Json
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash -ne $taskBinding.sha256){throw 'Late-close source identity differs'}
$taskEnc=[Text.UTF8Encoding]::new($false)
function NewTaskText([string]$Path,[string]$Value){
 $bytes=$taskEnc.GetBytes($Value)
 $f=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$f.Write($bytes)}finally{$f.Dispose()}
}
$taskResources=@()
$taskInitial=Join-Path $taskRun 'RESOURCE_INITIAL.json'
if(Test-Path -LiteralPath $taskInitial){$taskResources+=Get-Content -LiteralPath $taskInitial -Raw|ConvertFrom-Json}
foreach($file in Get-ChildItem -LiteralPath $taskRun -Filter 'ACTIVE_WAIT_OBSERVATIONS_*.jsonl' -File){
 foreach($line in Get-Content -LiteralPath $file.FullName|Where-Object {$_}){
  $row=$line|ConvertFrom-Json
  if($null -ne $row.resource -and $null -ne $row.resource.headroom_bytes){$taskResources+=$row.resource}
 }
}
$taskStop=[ordered]@{
 status='ACTUAL_CURRENT_WINDOW_ACCOUNT_BOUNDARY_OBSERVED'
 observed_primary=$taskActual.primary
 observed_secondary=$taskActual.secondary
 ordinaryUsageAllowed_as_returned=$taskActual.ordinaryUsageAllowed
 following_account_clock_UTC=$taskActual.following_account_clock_UTC
 exact_tool_observation_timestamp='Not independently supplied; following clock recorded'
 record_write_UTC=[DateTime]::UtcNow.ToString('o')
 source_log=$taskLog
 source_log_SHA256=(Get-FileHash -LiteralPath $taskLog -Algorithm SHA256).Hash.ToLowerInvariant()
 no_automatic_reset_resume=$true
 original_research_objective_complete=$false
 no_goal_status_changed=$true
}
NewTaskText (Join-Path $taskHandoff 'ACCOUNT_STOP.json') (($taskStop|ConvertTo-Json -Depth 12)+[Environment]::NewLine)
$taskSummary='Explicit Oct17 continuation ended at actual primary '+$taskActual.primary.usedPercent+'% / ordinaryUsageAllowed '+$taskActual.ordinaryUsageAllowed+', reset identity1792217489, following clock '+$taskActual.following_account_clock_UTC+'. C0 remained preparation-only; no numeric stage launched. Original19bindings/12GiBguard/2.1993678s charged and897.8006322s remaining unchanged. OIC0 exact reply remains closed with no new local checkpoint remedy or efficacy admission. Prior seals/stops and owner outreach decline persist. No automatic reset resume; original research goal unresolved, no goal status changed. Read docs/maintenance/2026-10-17/continuation-handoff-12 ACCOUNT_STOP and autonomous-continuation-02 observations.'
$taskAgents=Join-Path $taskRoot 'AGENTS.md'
$taskOriginal=[IO.File]::ReadAllText($taskAgents)
$taskTitle='# AGENTS.md — RAP / RAP-SLAM current handoff'
if(-not $taskOriginal.StartsWith($taskTitle)){throw 'Unexpected AGENTS header'}
[IO.File]::WriteAllText($taskAgents,$taskTitle+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine+[Environment]::NewLine+$taskOriginal.Substring($taskTitle.Length).TrimStart([char[]]"`r`n"),$taskEnc)
[IO.File]::AppendAllText((Join-Path $taskRoot 'docs/maintenance/2026-10-17/PHASE_RECORD.md'),[Environment]::NewLine+'## Actual account boundary'+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine,$taskEnc)
$taskMax=if($taskResources.Count){($taskResources|Measure-Object -Property headroom_bytes -Maximum).Maximum}else{$null}
$taskResourceRecord=[ordered]@{valid_resource_observations=$taskResources.Count;maximum_headroom_bytes=$taskMax;original_required_bytes=12884901888;source_note='Initial single read plus retained active-observer rows; no value inferred at the final account boundary';C0_numeric_stages_launched=0;C0_python_syntax_runtime='UNTESTED';original_C0_charged_seconds=2.1993678;original_C0_remaining_seconds=897.8006322;full_observer_native_process_tree_RSS='UNKNOWN'}
NewTaskText (Join-Path $taskHandoff 'RESOURCE_CLOSE.json') (($taskResourceRecord|ConvertTo-Json -Depth 8)+[Environment]::NewLine)
NewTaskText (Join-Path $taskHandoff 'CLOSE_REPORT.md') ('# Actual allowance boundary'+[Environment]::NewLine+[Environment]::NewLine+$taskSummary+[Environment]::NewLine+[Environment]::NewLine+'Current-window identity checks independently matched10previous late account-seal entries,26OIC0 delivery entries and19C0source bindings. Both original repository HEADs/branches/two-nine tracked dirty path sets matched at the initial observation; this is not all-file-content or process-absence certification. No new scientific efficacy test or complete-system benchmark was run. Resource and account observations are separate; see RESOURCE_CLOSE.json. The original research objective remains unresolved.'+[Environment]::NewLine)
$taskSnapshot=Join-Path $taskHandoff 'account_boundary_snapshot'
New-Item -ItemType Directory -Path $taskSnapshot|Out-Null
foreach($path in @($taskAgents,(Join-Path $taskRoot 'docs/maintenance/2026-10-17/PHASE_RECORD.md'))){
 $target=Join-Path $taskSnapshot ([IO.Path]::GetFileName($path))
 $f=[IO.FileStream]::new($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$bytes=[IO.File]::ReadAllBytes($path);$f.Write($bytes)}finally{$f.Dispose()}
}
$taskEntries=[ordered]@{}
foreach($file in Get-ChildItem -LiteralPath $taskHandoff -Recurse -File|Sort-Object FullName){
 if($file.Name -ne 'ACCOUNT_STOP_SEAL.json'){$taskEntries[$file.FullName.Substring($taskHandoff.Length+1).Replace('\','/')]=[ordered]@{bytes=$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}}
}
foreach($file in Get-ChildItem -LiteralPath $taskRun -Recurse -File|Sort-Object FullName){
 $taskEntries['../autonomous-continuation-02/'+$file.FullName.Substring($taskRun.Length+1).Replace('\','/')]=[ordered]@{bytes=$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
NewTaskText (Join-Path $taskHandoff 'ACCOUNT_STOP_SEAL.json') (([ordered]@{utc=[DateTime]::UtcNow.ToString('o');scope='This explicit current allowance boundary only, no science replay';files=$taskEntries}|ConvertTo-Json -Depth 12)+[Environment]::NewLine)
Write-Output ($taskStop|ConvertTo-Json -Depth 12 -Compress)
