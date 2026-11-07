$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-14/continuation-handoff-05'
$inputPath=Join-Path $base 'ACCOUNT_STOP_INPUT.json'
$observation=Get-Content -Raw -LiteralPath $inputPath|ConvertFrom-Json -AsHashtable
$primary=$observation.rateLimits.primary
if($null -eq $primary -or ($primary.usedPercent -lt 100 -and $observation.ordinaryUsageAllowed -ne $false)){throw 'Not an observed quota-stop boundary'}
$utf8=[System.Text.UTF8Encoding]::new($false)
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save-New([string]$name,$value){
    $bytes=$utf8.GetBytes(($value|ConvertTo-Json -Depth 20)+"`n")
    $stream=[System.IO.FileStream]::new((Join-Path $base $name),[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write)
    try{$stream.Write($bytes)}finally{$stream.Dispose()}
}
$record=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');boundary='OBSERVED_CURRENT_ACCOUNT_ALLOWANCE_STOP_NOT_SCIENCE_COMPLETION';
    observed_primary_used_percent=$primary.usedPercent;ordinaryUsageAllowed=$observation.ordinaryUsageAllowed;
    observed_resets_at=$primary.resetsAt;original_snapshot81_percent_historical=$true;
    no_new_scientific_payload_after_six_scope_closures=$true;scientific_goal_complete=$false;
    no_automatic_quota_reset_resume=$true;WPC0_native_resource_gate_still_INCOMPLETE=$true;
    NMQ0_observer_complete_lifetime_peak_known=$false;
    AGENTS_sha256=(Hash (Join-Path $root 'AGENTS.md'));
    PHASE_sha256=(Hash (Join-Path $root 'docs/maintenance/2026-10-14/PHASE_RECORD.md'));
    account_input_sha256=(Hash $inputPath);handoff_seal_sha256=(Hash (Join-Path $base 'DELIVERY_SEAL.json'))}
Save-New 'ACCOUNT_STOP.json' $record
$entries=@('ACCOUNT_STOP_INPUT.json','ACCOUNT_STOP.json','DELIVERY_SEAL.json','FINAL_VERIFICATION_SEAL.json','PROTOTYPE_ADOPTION_REVIEW.md','AUTHENTICATION_DEPENDENCIES.md','RESOURCE_ADOPTION_REQUIREMENTS.md','FINAL_PREPARATION_NOTES.md')|ForEach-Object{
    $p=Join-Path $base $_;[ordered]@{path=$_;sha256=(Hash $p);bytes=(Get-Item -LiteralPath $p).Length}
}
Save-New 'ACCOUNT_STOP_SEAL.json' ([ordered]@{entries=8;files=@($entries);finalizer_source_sha256=(Hash $PSCommandPath);late_supplement_not_in_original22_entries=$true})
Write-Output ($record|ConvertTo-Json -Compress)
