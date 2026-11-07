param(
    [Parameter(Mandatory=$true)][int]$UsedPercent,
    [Parameter(Mandatory=$true)][bool]$OrdinaryAllowed
)
$ErrorActionPreference='Stop'
if($UsedPercent -lt 100 -and $OrdinaryAllowed){throw 'Current allowance stop has not been observed'}
$taskRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs\maintenance\2026-10-14\continuation-handoff-04'
function Write-ExclusiveJson([string]$Path,[object]$Value){
    $taskBytes=[System.Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 10)+[Environment]::NewLine)
    $taskStream=[System.IO.File]::Open($Path,[System.IO.FileMode]::CreateNew)
    try{$taskStream.Write($taskBytes,0,$taskBytes.Length)}finally{$taskStream.Dispose()}
}
$taskReceipt=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');source='Codex get_usage_limits';
    primary_usedPercent=$UsedPercent;ordinaryUsageAllowed=$OrdinaryAllowed;windowDurationMins=300;
    account_shared_not_thread_exclusive=$true;current_allowance_stop_observed=$true;
    scientific_goal_complete=$false;no_new_scientific_payload_since_handoff=$true;
    automatic_reset_resume_authorized=$false;previous_93_percent_snapshot_historical=$true}
Write-ExclusiveJson (Join-Path $taskBase 'ACCOUNT_STOP.json') $taskReceipt
$taskFiles=@('ACCOUNT_STOP.json','DELIVERY_SEAL.json')|ForEach-Object{
    $taskPath=Join-Path $taskBase $_
    [ordered]@{path=$_;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $taskPath).Hash.ToLower();bytes=(Get-Item -LiteralPath $taskPath).Length}
}
$taskMutable=@('AGENTS.md','docs/maintenance/2026-10-14/PHASE_RECORD.md')|ForEach-Object{
    $taskPath=Join-Path $taskRoot $_
    [ordered]@{workspace_path=$_;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $taskPath).Hash.ToLower();bytes=(Get-Item -LiteralPath $taskPath).Length}
}
Write-ExclusiveJson (Join-Path $taskBase 'ACCOUNT_STOP_SEAL.json') ([ordered]@{
    status='READ_ONLY_CURRENT_ALLOWANCE_STOP_SUPPLEMENT_COMPLETE';files=@($taskFiles);
    mutable_handoff_values_at_stop=@($taskMutable);original_14_entry_delivery_seal_unchanged=$true;
    no_scientific_replay=$true;source_script_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLower()})
Write-Output ($taskReceipt|ConvertTo-Json -Compress)
