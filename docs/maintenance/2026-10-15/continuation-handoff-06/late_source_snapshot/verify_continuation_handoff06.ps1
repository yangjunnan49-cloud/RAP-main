$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06'
$identity=Get-Content (Join-Path $base 'IDENTITY_CHECKS.json') -Raw|ConvertFrom-Json -AsHashtable
$seal=Get-Content (Join-Path $base 'DELIVERY_SEAL.json') -Raw|ConvertFrom-Json -AsHashtable
$checked=0
foreach($entry in $identity.files.GetEnumerator()){
 if(-not $entry.Key.StartsWith('/mnt/e/')){throw 'Unmapped frozen path'}
 $path='E:\'+$entry.Key.Substring(7).Replace('/','\');$row=$entry.Value
 if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256){throw "Identity mismatch: $path"}
 $checked++
}
foreach($row in $seal.files){
 $path=Join-Path $base $row.path
 if((Get-Item -LiteralPath $path).Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256){throw "Handoff mismatch: $path"}
}
$supRoots=@('public-release-identity-01/supervision','public-release-identity-01/identity-attempt-02/supervision',
 'demo-source-role-01/supervision','demo-source-role-01/source-attempt-02/supervision',
 'release-backend-attribution-01/supervision','official-demo-metadata-01/supervision')
$count=0;$success=0;$wall=0.0;$linux=0.0
foreach($sup in $supRoots){foreach($dir in Get-ChildItem (Join-Path $root "docs/maintenance/2026-10-15/$sup") -Directory){
 $e=Get-Content (Join-Path $dir.FullName 'exit.json') -Raw|ConvertFrom-Json
 $c=Get-Content (Join-Path $dir.FullName 'child_exit.json') -Raw|ConvertFrom-Json
 if($c.success -ne ($e.exit_code -eq 0)){throw 'Exit receipt mismatch'}
 $count++;if($e.exit_code -eq 0){$success++};$wall+=$e.wall_seconds;$linux+=$c.wall_seconds
}}
if($count -ne 17 -or $success -ne 14 -or [Math]::Abs($wall-159.6039669) -gt 0.000001){throw 'Resource receipt reconciliation'}
$repos=@{}
foreach($name in @('main','slam')){
 $folder=if($name -eq 'main'){$root}else{Join-Path (Split-Path $root -Parent) 'RAP-SLAM'}
 $head=(& git --no-optional-locks -c "safe.directory=$folder" -C $folder rev-parse HEAD).Trim()
 $branch=(& git --no-optional-locks -c "safe.directory=$folder" -C $folder branch --show-current).Trim()
 $lines=@(& git --no-optional-locks -c "safe.directory=$folder" -C $folder status --short --untracked-files=no)
 $status=($lines -join "`n").Trim().Split("`n")
 $old=$identity.repositories[$name]
 if($head -ne $old.head -or $branch -ne $old.branch -or ($status|ConvertTo-Json -Compress) -ne ($old.tracked_status|ConvertTo-Json -Compress)){throw "Repository changed: $name"}
 $repos[$name]=@{head=$head;branch=$branch;tracked_status=$status}
}
foreach($name in $identity.retained_markers){$path='E:\'+$name.Substring(7).Replace('/','\');if(-not (Test-Path -LiteralPath $path)){throw 'Retained marker missing'}}
$result=@{passed=$true;independent_Windows_SHA256_and_sizes=$true;frozen_available_delivery_paths=$checked;
 handoff_entries=$seal.files.Count;enclosing_exit_receipts=$count;successes=$success;retained_failures=3;
 total_Windows_seconds=$wall;total_Linux_child_seconds=$linux;retained_markers=$identity.retained_markers.Count;
 repositories=$repos;new_scientific_or_network_payload_calls=0;ordinary_preparation_RSS='UNKNOWN';utc=[DateTime]::UtcNow.ToString('o')}
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 10)+"`n")
$stream=[IO.FileStream]::new((Join-Path $base 'WINDOWS_FINAL_VERIFICATION.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$stream.Write($bytes)}finally{$stream.Dispose()}
Write-Output ($result|Select-Object passed,frozen_available_delivery_paths,handoff_entries,enclosing_exit_receipts,retained_markers,total_Windows_seconds|ConvertTo-Json -Compress)
