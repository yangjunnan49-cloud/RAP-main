$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$day=Join-Path $root 'docs/maintenance/2026-10-15'
$base=Join-Path $day 'official-demo-metadata-01'
$out=Join-Path $day 'continuation-handoff-06'
$catalog=Get-Content (Join-Path $base 'catalog_windows.json') -Raw|ConvertFrom-Json -AsHashtable
$local=(Get-Content (Join-Path $day 'demo-source-role-01/source-attempt-02/headers_and_roles.json') -Raw|ConvertFrom-Json -AsHashtable).files
$sizes=[Collections.Generic.HashSet[long]]::new();$hashes=[Collections.Generic.HashSet[string]]::new()
foreach($row in $local){$null=$sizes.Add([long]$row.bytes);$null=$hashes.Add($row.sha256+':'+$row.bytes)}
$paths=[Collections.Generic.HashSet[string]]::new();$clouds=0;$lfs=0;$plain=0;$matches=0;$plainSizeMatches=0
foreach($e in $catalog.entries){
 if(-not $paths.Add($e.path)){throw 'Duplicate catalog path'}
 if($e.type -ne 'file' -or [IO.Path]::GetExtension($e.path) -notin @('.ply','.pcd')){continue}
 $clouds++
 if($e.lfs){$lfs++;if($hashes.Contains($e.lfs.oid+':'+$e.size)){$matches++}}
 else{$plain++;if($sizes.Contains([long]$e.size)){$plainSizeMatches++}}
}
if(-not $catalog.complete -or $paths.Count -ne 4577 -or $clouds -ne 3243 -or $lfs -ne 3215 -or $plain -ne 28 -or $matches -ne 0 -or $plainSizeMatches -ne 0){throw 'Catalog coverage mismatch'}
$transfers=@(Get-ChildItem (Join-Path $base 'transfers') -Filter '*.json'|Sort-Object Name|ForEach-Object {Get-Content $_.FullName -Raw|ConvertFrom-Json -AsHashtable})
$total=0;$admitted=0
foreach($r in $transfers){
 $q=Join-Path $base $r.body_path
 if((Get-Item -LiteralPath $q).Length -ne $r.acquired_body_bytes -or (Get-FileHash -LiteralPath $q -Algorithm SHA256).Hash.ToLowerInvariant() -ne $r.SHA256){throw 'Metadata body mismatch'}
 $total+=$r.acquired_body_bytes;if($r.admitted){$admitted++}
 if($r.acquired_body_bytes -gt 524288 -or $total -gt 4194304){throw 'Owner acquisition cap'}
}
if($total -ne 1273695 -or $transfers.Count -ne 10 -or $admitted -ne 9){throw 'Transport ledger mismatch'}
$result=@{passed=$true;independent_Windows_reconstruction=$true;revision=$catalog.revision;local_file_denominator=$local.Count;
 catalog_unique_entries=$paths.Count;catalog_point_files=$clouds;LFS_SHA256_point_files=$lfs;nonLFS_point_files=$plain;
 LFS_exact_matches=$matches;nonLFS_size_matches=$plainSizeMatches;acquired_body_bytes=$total;requests=$transfers.Count;
 admitted_requests=$admitted;new_network_point_model_pose_or_metric_calls=0;physical_scene_or_all_history_absence_claim=$false;
 ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
function Save([string]$Name,$Value){
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 15)+"`n")
 $stream=[IO.FileStream]::new((Join-Path $out $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$stream.Write($bytes)}finally{$stream.Dispose()}
}
Save 'WINDOWS_METADATA_VERIFICATION.json' $result
$members=@($local|ForEach-Object {@{path=$_.path;bytes=$_.bytes;SHA256=$_.sha256}})
Save 'DEMO_MEMBER_REQUEST.json' @{purpose='Local unsent request manifest for exact original demo source/reference authentication';
 member_count=$members.Count;total_bytes=($members|Measure-Object bytes -Sum).Sum;members=$members;
 requested_fields=@('original author archive version and member byte identities','input coordinate units and frame for every member',
 'whether supplied clouds are already registered','exact reference input-to-world transform convention and construction',
 'any resampling or reencoding map to RegX','training membership or explicit unknown');sent_externally=$false}
Write-Output ($result|Select-Object passed,catalog_point_files,LFS_exact_matches,nonLFS_size_matches,acquired_body_bytes|ConvertTo-Json -Compress)
