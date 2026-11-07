$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/current_state_audit_20261021'
$c0='E:\githouse\RAP-main\docs\maintenance\2026-10-16\regx-interface-contract-01'
$checks=@();$sources=@()
foreach($name in @('SOURCE_FREEZE.json','SUPPLEMENTAL_SOURCE_FREEZE.json')){
    $rows=Get-Content -Raw (Join-Path $c0 $name) | ConvertFrom-Json
    foreach($row in $rows){
        $actual=(Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash
        $sources+=@{path=$row.path;expected=$row.SHA256;actual=$actual;matched=($actual -eq $row.SHA256)}
    }
}
if($sources.Count -ne 19 -or @($sources | Where-Object {-not $_.matched}).Count -ne 0){throw 'C0 source identity mismatch; do not rerun'}
function CheckSeal($Directory,$SealName,$Label){
    $seal=Get-Content -Raw (Join-Path $Directory $SealName) | ConvertFrom-Json
    $entries=@()
    if($seal -is [array]){$entries=$seal}
    else{$entries=@($seal.files.PSObject.Properties | ForEach-Object {@{path=$_.Name;sha256=$(if($_.Value -is [string]){$_.Value}else{$_.Value.sha256})}})}
    $mismatches=@()
    foreach($entry in $entries){
        $path=Join-Path $Directory $entry.path
        if(-not(Test-Path -LiteralPath $path -PathType Leaf)){$mismatches+=('MISSING:'+ $entry.path);continue}
        if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.sha256){$mismatches+=('HASH:'+ $entry.path)}
    }
    return @{scope=$Label;seal=$SealName;entries=$entries.Count;mismatches=$mismatches;passed=($mismatches.Count -eq 0)}
}
$checks+=CheckSeal $c0 'DELIVERY_SEAL.json' 'C0 original preparation'
$checks+=CheckSeal $c0 'NUMERIC_DELIVERY_SEAL.json' 'C0 completed numeric delivery'
$checks+=CheckSeal (Join-Path $root 'outputs/continuation_20261021') 'FINAL_SEAL.json' 'Prior quota boundary recovery'
foreach($name in @('overlap_validation_20261021','guard_hardening_20261021','native_stability_review_20261021','boundary_contract_20261021','guard_recorder_integration_20261021','native_stability_control_20261021','chunk_hash_feasibility_20261021','native_stability_stream_20261021')){$checks+=CheckSeal (Join-Path $root ('outputs/'+$name)) 'DELIVERY_SEAL.json' $name}
$numeric=Get-Content -Raw (Join-Path $c0 'NUMERIC_CHECKS.json') | ConvertFrom-Json
$cost=Get-Content -Raw (Join-Path $c0 'NUMERIC_COSTS.json') | ConvertFrom-Json
$four=@($numeric.records | Where-Object {$_.child.success -and $_.supervisor.exit_code -eq 0})
if($four.Count -ne 4 -or [Math]::Abs($cost.original_prestart_charged_seconds+$cost.new_enclosing_tool_command_seconds-$cost.combined_charged_seconds) -gt 1e-12){throw 'C0 completion or budget evidence inconsistent'}
$oldPending=Join-Path $c0 'RUNBOOK_CN.md';$latest=Join-Path $c0 'NUMERIC_REPORT.md'
$reports=@{}
foreach($name in @('RUNBOOK_CN.md','NUMERIC_REPORT.md','NUMERIC_CHECKS.json','NUMERIC_COSTS.json','NUMERIC_STATUS','ADOPTION_DECISION_CN.md')){$reports[$name]=@{path=(Join-Path $c0 $name);sha256=(Get-FileHash -LiteralPath (Join-Path $c0 $name)).Hash}}
$result=@{utc=[DateTimeOffset]::UtcNow.ToString('o');C0_current_status='COMPLETE_CUSTOM_INTERFACE_ONLY';C0_completed_utc='2026-10-17T12:24:32.6455237Z';C0_source_bindings=$sources;C0_completed_stages=$four.Count;C0_points_previously_validated=$numeric.validation.all_points;C0_charged_original_seconds=$cost.combined_charged_seconds;C0_original_cap_seconds=$cost.original_cap_seconds;C0_remaining_is_not_new_payload_authorization=$true;historical_pending_runbook=$oldPending;authoritative_completed_report=$latest;C0_reports=$reports;checks=$checks;sealed_entries_total=[long]($checks | Measure-Object entries -Sum).Sum;all_seals_match=(@($checks | Where-Object {-not $_.passed}).Count -eq 0);new_scientific_launches=0;point_numeric_decodes=0;model_fit_solver_calls=0;no_historical_file_modified=$true}
[IO.File]::WriteAllText((Join-Path $out 'CHECKS.json'),($result | ConvertTo-Json -Depth 9),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{C0_current=$result.C0_current_status;C0_bindings=$sources.Count;C0_stages=$four.Count;C0_charged=$cost.combined_charged_seconds;seal_entries=$result.sealed_entries_total;all_match=$result.all_seals_match} | ConvertTo-Json
if(-not $result.all_seals_match){throw 'Seal discrepancy must be preserved and investigated'}
