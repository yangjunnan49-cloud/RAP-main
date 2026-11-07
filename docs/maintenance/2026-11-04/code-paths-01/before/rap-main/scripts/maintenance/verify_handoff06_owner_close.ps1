$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06'
$out=Join-Path $base 'owner-close-01'
$identity=Get-Content (Join-Path $base 'IDENTITY_CHECKS.json') -Raw|ConvertFrom-Json -AsHashtable
$checked=0
foreach($entry in $identity.files.GetEnumerator()){
 if(-not $entry.Key.StartsWith('/mnt/e/')){throw 'Unexpected identity path root'}
 $q='E:\'+$entry.Key.Substring(7).Replace('/','\');$r=$entry.Value
 if((Get-Item -LiteralPath $q).Length -ne $r.bytes -or (Get-FileHash -LiteralPath $q -Algorithm SHA256).Hash.ToLowerInvariant() -ne $r.sha256){throw "Frozen identity mismatch: $q"}
 $checked++
}
$seals=@{}
foreach($name in @('DELIVERY_SEAL.json','FINAL_VERIFICATION_SEAL.json','ACCOUNT_STOP_SEAL.json')){
 $seal=Get-Content (Join-Path $base $name) -Raw|ConvertFrom-Json -AsHashtable
 foreach($r in $seal.files){
  $q=Join-Path $base $r.path
  if((Get-Item -LiteralPath $q).Length -ne $r.bytes -or (Get-FileHash -LiteralPath $q -Algorithm SHA256).Hash.ToLowerInvariant() -ne $r.sha256){throw "Closing seal mismatch: $q"}
 }
 $seals[$name]=$seal.files.Count
}
if($checked -ne 552 -or $seals['DELIVERY_SEAL.json'] -ne 12 -or $seals['FINAL_VERIFICATION_SEAL.json'] -ne 10 -or $seals['ACCOUNT_STOP_SEAL.json'] -ne 7){throw 'Closing denominators changed'}
$account=Get-Content (Join-Path $base 'ACCOUNT_STOP.json') -Raw|ConvertFrom-Json -AsHashtable
if($account.primary_used_percent -ne 100 -or $account.ordinaryUsageAllowed -ne $false -or $account.first_writer_executed -ne $false){throw 'Historical quota record mismatch'}
if($account.closing_resume_primary_used_percent -ne 1 -or $account.closing_resume_ordinaryUsageAllowed -ne $true -or $null -ne $account.observation_UTC){throw 'Fresh/old quota window conflation'}
$repos=@{}
foreach($name in @('main','slam')){
 $folder=if($name -eq 'main'){$root}else{Join-Path (Split-Path $root -Parent) 'RAP-SLAM'}
 $head=(& git --no-optional-locks -c "safe.directory=$folder" -C $folder rev-parse HEAD).Trim()
 $branch=(& git --no-optional-locks -c "safe.directory=$folder" -C $folder branch --show-current).Trim()
 $lines=@(& git --no-optional-locks -c "safe.directory=$folder" -C $folder status --short --untracked-files=no)
 $status=($lines -join "`n").Trim().Split("`n");$old=$identity.repositories[$name]
 if($head -ne $old.head -or $branch -ne $old.branch -or ($status|ConvertTo-Json -Compress) -ne ($old.tracked_status|ConvertTo-Json -Compress)){throw "Original repository state changed: $name"}
 $repos[$name]=@{head=$head;branch=$branch;tracked_status=$status}
}
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'census_continuation_handoff06.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Frozen argument-parser source syntax'}
$add=$ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst] -and $n.GetCommandName() -eq 'Add-Type'},$true)
if($add.Count -ne 1){throw 'Frozen argument-parser definition count'}
Add-Type -TypeDefinition $add[0].CommandElements[2].Value
$names=(Get-Content (Join-Path $base 'WINDOWS_PROCESS_CENSUS.json') -Raw|ConvertFrom-Json).scoped_identifiers
$processes=@(Get-CimInstance Win32_Process);$readable=0;$argv=0;$nulls=0;$unknown=@();$matches=@()
foreach($p in $processes){
 if(-not $p.CommandLine){$nulls++;if($p.Name -match '^(python([0-9.]*)?|pwsh|powershell|wsl)\.exe$'){$unknown+=@{pid=$p.ProcessId;name=$p.Name}};continue}
 $readable++;$args=[H06Args]::Read($p.CommandLine);$argv+=$args.Count
 foreach($a in $args){if(($a -replace '\\','/').Split('/')[-1] -in $names){$matches+=@{pid=$p.ProcessId;matched_argument=$a};break}}
}
if($matches.Count){throw 'Scoped payload still running'}
$markers=@();foreach($name in $identity.retained_markers){$q='E:\'+$name.Substring(7).Replace('/','\');if(-not (Test-Path -LiteralPath $q)){throw 'Original marker missing'};$markers+=$name}
$result=@{passed=$true;unique_identity_paths=$checked;prior_seal_entries=$seals;historical_quota_and_fresh_resume_distinguished=$true;
 repositories=$repos;retained_markers=$markers.Count;processes=$processes.Count;readable_command_lines=$readable;argv=$argv;
 null_command_lines=$nulls;unreadable_relevant_interpreters=$unknown;scoped_payload_matches=$matches;scoped_identifiers=$names;
 unrelated_tasks_absence_claim=$false;new_scientific_or_network_payload_calls=0;ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 12)+"`n")
$stream=[IO.FileStream]::new((Join-Path $out 'WINDOWS_CHECKS.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$stream.Write($bytes)}finally{$stream.Dispose()}
Write-Output ($result|Select-Object passed,unique_identity_paths,retained_markers,processes,argv,@{N='scoped_matches';E={$_.scoped_payload_matches.Count}},@{N='unreadable_interpreters';E={$_.unreadable_relevant_interpreters.Count}}|ConvertTo-Json -Compress)
