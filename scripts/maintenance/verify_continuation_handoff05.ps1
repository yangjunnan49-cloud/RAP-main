$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-14/continuation-handoff-05'
$utf8=[System.Text.UTF8Encoding]::new($false)
function Read-Json([string]$Path){Get-Content -Raw -LiteralPath $Path|ConvertFrom-Json -AsHashtable}
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Win-Path([string]$Path){
    if($Path -match '^/mnt/([a-z])/(.*)$'){return $Matches[1].ToUpperInvariant()+':\'+$Matches[2].Replace('/','\')}
    throw 'Unexpected identity path root'
}
function Save-New([string]$Name,$Value){
    $p=Join-Path $base $Name
    $b=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 20)+"`n")
    $f=[System.IO.FileStream]::new($p,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write)
    try{$f.Write($b)}finally{$f.Dispose()}
}
$seal=Read-Json (Join-Path $base 'DELIVERY_SEAL.json')
foreach($entry in $seal.files){
    $p=Join-Path $base $entry.path
    if((Get-Item -LiteralPath $p).Length -ne $entry.bytes -or (Hash $p) -ne $entry.sha256){throw "Handoff identity mismatch $p"}
}
if($seal.entries -ne 22 -or $seal.files.Count -ne 22){throw 'Unexpected handoff denominator'}
$id=Read-Json (Join-Path $base 'IDENTITY_CHECKS.json')
foreach($pair in $id.files.GetEnumerator()){
    $path=Win-Path $pair.Key
    if((Hash $path) -ne $pair.Value){throw "Scope identity mismatch $path"}
}
if($id.files.Count -ne 409){throw 'Unexpected scope identity denominator'}
$checks=Read-Json (Join-Path $base 'CHECKS.json')
$receipts=@($checks.receipts)
if($receipts.Count -ne 22){throw 'Unexpected attempt denominator'}
$seconds=0.0;$childSeconds=0.0;$success=0;$peak=0L
foreach($row in $receipts){
    $seconds+=$row.Windows.wall_seconds;$childSeconds+=$row.child.wall_seconds
    $peak=[Math]::Max($peak,[long]$row.child.peak_RSS_bytes)
    if($row.child.success){$success++}
    if($row.Windows.exit_code -ne $(if($row.child.success){0}else{1})){throw 'Exit mismatch'}
}
if($success -ne 20 -or [Math]::Abs($seconds-86.2359991) -gt 1e-8 -or [Math]::Abs($childSeconds-50.823979292064905) -gt 1e-8){throw 'Resource aggregate mismatch'}
if($checks.WPC0_complete_native_resource_gate_passed -or $checks.NMQ0_observer_complete_lifetime_peak_known){throw 'Unknown resource boundary lost'}
if($id.retained_INCOMPLETE_paths.Count -ne 9){throw 'Marker denominator'}
foreach($path in $id.retained_INCOMPLETE_paths){if(-not (Test-Path -LiteralPath (Win-Path $path))){throw 'Marker lost'}}
$windows=Read-Json (Join-Path $base 'PROCESS_CENSUS_WINDOWS.json')
$linux=Read-Json (Join-Path $base 'PROCESS_CENSUS_LINUX.json')
if($windows.owned_payload_matches.Count -or $windows.unreadable_relevant_interpreters.Count -or $linux.owned_payload_matches.Count -or $linux.unreadable_processes.Count){throw 'Process boundary'}
$record=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');independent_Windows_hash_and_size_pass=$true;
    handoff_entries=22;scope_identity_hashes=409;scoped_references=271;original_available_references=62;
    outer_attempts=22;outer_exit_successes=20;retained_failures=2;Windows_seconds=$seconds;
    Linux_child_seconds=$childSeconds;peak_outer_Linux_RSS_bytes=$peak;retained_markers=9;
    WPC0_full_native_resource_gate_passed=$false;NMQ0_observer_full_lifetime_peak_known=$false;
    existing_process_snapshots_reused_no_payload_after_census=$true;new_scientific_replay=$false;
    live_AGENTS_SHA256=(Hash (Join-Path $root 'AGENTS.md'));
    live_PHASE_SHA256=(Hash (Join-Path $root 'docs/maintenance/2026-10-14/PHASE_RECORD.md'))}
Save-New 'FINAL_VERIFICATION.json' $record
$files=@('FINAL_VERIFICATION.json','DELIVERY_SEAL.json')|ForEach-Object{
    $p=Join-Path $base $_;[ordered]@{path=$_;sha256=(Hash $p);bytes=(Get-Item -LiteralPath $p).Length}
}
Save-New 'FINAL_VERIFICATION_SEAL.json' ([ordered]@{entries=2;files=@($files);verification_source_sha256=(Hash $PSCommandPath);late_supplement_not_in_original22_entries=$true})
Write-Output ($record|ConvertTo-Json -Compress)
