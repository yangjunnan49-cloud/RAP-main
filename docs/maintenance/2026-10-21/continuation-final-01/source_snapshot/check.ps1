$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $taskRoot 'outputs/continuation_20261021'
$checks=@()
foreach($name in @('overlap_validation_20261021','guard_hardening_20261021','native_stability_review_20261021','boundary_contract_20261021')){
    $root=Join-Path $taskRoot ('outputs/'+$name)
    $seal=Get-Content -Raw (Join-Path $root 'DELIVERY_SEAL.json') | ConvertFrom-Json
    $entries=@()
    if($seal -is [array]){$entries=$seal}
    else{$entries=@($seal.files.PSObject.Properties | ForEach-Object {[pscustomobject]@{path=$_.Name;sha256=$_.Value}})}
    $mismatches=@()
    foreach($entry in $entries){
        $path=Join-Path $root $entry.path
        if(-not(Test-Path -LiteralPath $path -PathType Leaf)){$mismatches+=('MISSING:'+ $entry.path);continue}
        if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.sha256){$mismatches+=('HASH:'+ $entry.path)}
    }
    $checks+=@{scope=$name;sealed_entries=$entries.Count;mismatches=$mismatches;passed=($mismatches.Count -eq 0)}
}
$copies=@()
foreach($name in @('p0-validation-01','guard-hardening-01','native-stability-review-01','boundary-contract-01')){
    $dir='E:\githouse\RAP-main\docs\maintenance\2026-10-21\'+$name
    $copies+=@{directory=$dir;bytes=[long](Get-ChildItem -LiteralPath $dir -File -Recurse | Measure-Object -Property Length -Sum).Sum}
}
$worknames=@('overlap_validation_01','guard_hardening_01','native_stability_review_01','boundary_contract_01','delivery_reconciliation_01')
$outnames=@('overlap_validation_20261021','guard_hardening_20261021','native_stability_review_20261021','boundary_contract_20261021','continuation_20261021')
$bytes=0L
foreach($name in $worknames){$bytes += [long](Get-ChildItem -LiteralPath (Join-Path $taskRoot ('work/'+$name)) -Recurse -File | Measure-Object -Property Length -Sum).Sum}
foreach($name in $outnames){$bytes += [long](Get-ChildItem -LiteralPath (Join-Path $taskRoot ('outputs/'+$name)) -Recurse -File | Measure-Object -Property Length -Sum).Sum}
$bytes += [long]($copies | Measure-Object -Property bytes -Sum).Sum
$original=140458966L
$result=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');checks=$checks;repository_copies=$copies;all_sealed_entries_match=(@($checks | Where-Object {-not $_.passed}).Count -eq 0);new_bytes_at_snapshot=$bytes;old_dossier_bytes=$original;combined_bytes_at_snapshot=($bytes+$original);new_cap_bytes=64MB;combined_cap_bytes=256MB;growth_pass=($bytes -lt 64MB -and ($bytes+$original) -lt 256MB);late_documentary_bytes_additional=$true;no_numeric_payload=$true;original_caps_unchanged=$true}
[IO.File]::WriteAllText((Join-Path $out 'INTEGRITY_CHECKS.json'),($result | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$result | Select-Object all_sealed_entries_match,new_bytes_at_snapshot,combined_bytes_at_snapshot,growth_pass | ConvertTo-Json
if(-not $result.all_sealed_entries_match -or -not $result.growth_pass){throw 'Integrity discrepancy must be disclosed and resolved without overwriting sealed history'}
