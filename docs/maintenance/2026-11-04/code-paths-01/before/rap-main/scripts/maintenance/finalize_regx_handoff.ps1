$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$today=Join-Path $root 'docs/maintenance/2026-10-16'
$base=Join-Path $today 'continuation-handoff-09'
if(Test-Path $base){throw 'Preserve existing handoff'}
New-Item -ItemType Directory -Path $base|Out-Null
$utf8=[Text.UTF8Encoding]::new($false)
function Save($name,$obj){[IO.File]::WriteAllText((Join-Path $base $name),($obj|ConvertTo-Json -Depth 30),$utf8)}
function Check-Seal($folder){
 $seal=Get-Content -Raw (Join-Path $folder 'DELIVERY_SEAL.json')|ConvertFrom-Json -AsHashtable
 $n=0;foreach($pair in $seal.files.GetEnumerator()){$p=Join-Path $folder $pair.Key;if((Get-Item -LiteralPath $p).Length -ne $pair.Value.bytes -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pair.Value.sha256){throw "Seal mismatch: $p"};$n++}
 if($n -ne $seal.entries){throw 'Seal count mismatch'};return $n
}
$rvc=Check-Seal (Join-Path $today 'ray-consistency-ranking-01')
$old=Check-Seal (Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-08')
$oldIdent=Get-Content -Raw (Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-08/IDENTITY_CHECKS.json')|ConvertFrom-Json -AsHashtable
$markers=@();foreach($path in $oldIdent.files.Keys|Where-Object {$_ -match '/INCOMPLETE$'}){
 $p=$path.Replace('/mnt/e/githouse/RAP-main/',$root+'/');$item=$oldIdent.files[$path]
 if((Get-Item -LiteralPath $p).Length -ne $item.bytes -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw "Historical marker mismatch: $path"}
 $markers+=@{path=$path;bytes=$item.bytes;sha256=$item.sha256}
}
Save 'HISTORICAL_MARKERS.json' $markers
$scopeSeals=@{}
foreach($scope in @('regx-reference-package-01','regx-reference-code-01')){
 $folder=Join-Path $today $scope;$limit=if($scope -eq 'regx-reference-package-01'){32MB}else{2MB}
 $files=[ordered]@{};foreach($f in Get-ChildItem -LiteralPath $folder -File -Recurse|Sort-Object FullName){$relative=[IO.Path]::GetRelativePath($folder,$f.FullName).Replace('\','/');$files[$relative]=@{bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}}
 $seal=@{scope=$scope;entries=$files.Count;files=$files}
 $sealPath=Join-Path $folder 'DELIVERY_SEAL.json';if(Test-Path $sealPath){throw 'No seal overwrite'}
 [IO.File]::WriteAllText($sealPath,($seal|ConvertTo-Json -Depth 15),$utf8)
 $count=Check-Seal $folder;$bytes=(Get-ChildItem $folder -File -Recurse|Measure-Object Length -Sum).Sum
 if($bytes -ge $limit){throw 'Complete dossier cap'}
 $scopeSeals[$scope]=@{entries=$count;complete_dossier_bytes=$bytes;cap_bytes=$limit}
}
$main=@{HEAD=(& git -C $root rev-parse HEAD);branch=(& git -C $root branch --show-current);tracked_dirty=@(& git -C $root diff --name-only)}
if($main.HEAD -ne '4055d929c594b0033aafc6eed339c910369eef55' -or $main.branch -ne 'codex/meeting-20260930' -or (($main.tracked_dirty|Sort-Object)-join ',') -ne '.gitignore,AGENTS.md'){throw 'Main repository state mismatch'}
Save 'MAIN_REPOSITORY.json' $main
$processes=@(Get-CimInstance Win32_Process)
$readable=@($processes|Where-Object CommandLine)
$owned=@($readable|Where-Object {$_.CommandLine -match '(acquire_regx_reference_(package|code)\.ps1|regx_(package_native|reference_code)_control\.ps1|validate_regx_reference_package(_layout02)?\.py|audit_regx_reference_code\.py|ray_consistency_ranking\.py)'}|Select-Object ProcessId,Name)
$nullInterpreters=@($processes|Where-Object {-not $_.CommandLine -and $_.Name -match '^(python|python3|pwsh|powershell|wsl)\.exe$'})
Save 'PROCESS_CHECK_WINDOWS.json' @{processes=$processes.Count;readable_command_lines=$readable.Count;null_command_lines=$processes.Count-$readable.Count;unreadable_relevant_interpreters=$nullInterpreters.Count;scoped_command_matches=$owned;scope='exact worker filename presence in readable command lines; not arbitrary task absence';utc=[DateTime]::UtcNow.ToString('o')}
Save 'CHECKS.json' @{RVC_delivery_entries_match=$rvc;prior_handoff08_seal_entries_match=$old;prior_INCOMPLETE_paths_match=$markers.Count;scope_seals=$scopeSeals;main_repository_matches=$true;scientific_goal_complete=$false;account_exhaustion_observed=$false;original_failed_validator_preserved=$true;retrospective_RVC_scope_clearance=$false;new_model_solver_training_pose_arithmetic=0;scoped_Windows_worker_matches=$owned.Count;all_native_process_tree_cap_claim=$false;observer_full_lifetime_peak='UNKNOWN';bookkeeping_resource_scope='ordinary setup RSS UNKNOWN; outside each original execution cap, no payload replay'}
Save 'CURRENT_DOC_SNAPSHOT.json' @(@{path='AGENTS.md';sha256=(Get-FileHash (Join-Path $root 'AGENTS.md') -Algorithm SHA256).Hash.ToLowerInvariant()},@{path='docs/maintenance/2026-10-16/PHASE_RECORD.md';sha256=(Get-FileHash (Join-Path $today 'PHASE_RECORD.md') -Algorithm SHA256).Hash.ToLowerInvariant()})
Get-Content (Join-Path $base 'CHECKS.json')
