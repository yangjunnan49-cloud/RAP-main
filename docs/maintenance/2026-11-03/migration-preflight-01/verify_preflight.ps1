# Read-only integrity checks. Does not run historical experimental programs.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$phase = [IO.Path]::GetFullPath($PSScriptRoot)
$repository = [IO.Path]::GetFullPath((Join-Path $phase '../../../..'))
$historicalRoot = Join-Path $repository 'docs/maintenance/2026-11-03'

function Read-Json([string]$Path) {
    return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json)
}
function Assert-Condition([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Test-Asset([string]$Path, [object]$Entry) {
    $item = Get-Item -LiteralPath $Path -Force
    Assert-Condition ($item.Length -eq [long]$Entry.bytes) ('Length mismatch: ' + $Path)
    $digest = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-Condition ($digest -eq $Entry.sha256) ('SHA256 mismatch: ' + $Path)
}

$baseline = Read-Json (Join-Path $phase 'BASELINE.json')
foreach ($entry in $baseline.authority_backups) { Test-Asset (Join-Path $phase $entry.path) $entry }
$proof = Read-Json (Join-Path $phase 'AUTHORITY_PROOF.json')
foreach ($entry in $proof.files) { Test-Asset (Join-Path $repository $entry.path) $entry }
$oldProof = Read-Json (Join-Path $historicalRoot 'round-close-01/AUTHORITY_PROOF.json')
Assert-Condition ($proof.previous_authority_sha256 -eq $oldProof.current_sha256) 'Old current authority does not match preserved original.'
Assert-Condition ($proof.previous_authority_bytes -eq (Get-Item -LiteralPath (Join-Path $phase $proof.previous_authority_backup)).Length) 'Original authority length mismatch.'
Assert-Condition ((Get-FileHash -LiteralPath $oldProof.parent_path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $oldProof.parent_sha256) 'Parent authority changed.'
Assert-Condition ((Get-FileHash -LiteralPath (Join-Path $repository 'AGENTS.md') -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath (Join-Path $phase 'AGENTS_CURRENT.md') -Algorithm SHA256).Hash) 'Current authority differs from staged source.'

$oldCount = 0
$oldBytes = [long]0
foreach ($scope in @('identity-evidence-01','stereo-source-01','stereo-support-01','stereo-alias-01','windows-lease-01')) {
    $folder = Join-Path $historicalRoot $scope
    foreach ($entry in (Read-Json (Join-Path $folder 'DELIVERY_SEAL.json')).files) {
        Test-Asset (Join-Path $folder $entry.path) $entry
        $oldCount++
        $oldBytes += [long]$entry.bytes
    }
}
Assert-Condition ($oldCount -eq 2047 -and $oldBytes -eq 297738079) 'Historical science seal count or size mismatch.'
$sourceCount = 0
foreach ($scope in @('stereo-source-01','stereo-support-01','stereo-support-01/integration02','stereo-alias-01','windows-lease-01')) {
    foreach ($entry in (Read-Json (Join-Path $historicalRoot ($scope + '/SOURCE_FREEZE.json'))).files) {
        Test-Asset $entry.path $entry
        $sourceCount++
    }
}
$oldCloseoutCount = 0
foreach ($relative in @('round-close-01/DELIVERY_SEAL.json','DELIVERY_SEAL.json')) {
    $sealPath = Join-Path $historicalRoot $relative
    foreach ($entry in (Read-Json $sealPath).files) {
        Test-Asset (Join-Path (Split-Path -Parent $sealPath) $entry.path) $entry
        $oldCloseoutCount++
    }
}

$summary = Read-Json (Join-Path $phase 'inventory02/SUMMARY.json')
$discovery = Read-Json (Join-Path $phase 'DISCOVERY_SUMMARY.json')
Assert-Condition (@($summary.roots).Count -eq 6) 'Unexpected metadata roots.'
Assert-Condition (@($summary.roots | Where-Object {-not $_.enumeration_complete -or $_.errors -ne 0}).Count -eq 0) 'Metadata enumeration incomplete.'
Assert-Condition ((Get-Item -LiteralPath (Join-Path $phase 'inventory02/errors.jsonl')).Length -eq 0) 'Unexpected metadata enumeration error.'
$actualCounts = @{}
foreach ($root in $summary.roots) { $actualCounts[$root.id] = @{files=[long]0; directories=[long]0; bytes=[long]0; links=0} }
foreach ($line in [IO.File]::ReadLines((Join-Path $phase 'inventory02/entries.jsonl'))) {
    $record = $line | ConvertFrom-Json
    Assert-Condition ($actualCounts.ContainsKey($record.root)) 'Unknown metadata root.'
    $tally = $actualCounts[$record.root]
    if ($record.kind -eq 'file') { $tally.files++; $tally.bytes += [long]$record.bytes }
    elseif ($record.kind -eq 'directory') { $tally.directories++ }
    else { throw 'Unknown metadata entry kind.' }
    if ($record.reparse_point) { $tally.links++ }
}
foreach ($root in $summary.roots) {
    $tally = $actualCounts[$root.id]
    Assert-Condition ($root.files -eq $tally.files -and $root.directories -eq $tally.directories -and $root.logical_bytes -eq $tally.bytes -and $root.skipped_reparse_points -eq $tally.links) ('Metadata tally mismatch: ' + $root.id)
}
Assert-Condition ($discovery.files -eq 106754 -and $discovery.logical_bytes -eq 130779517380) 'Discovery totals mismatch.'
Assert-Condition (($summary.roots | Measure-Object files -Sum).Sum -eq $discovery.files -and ($summary.roots | Measure-Object logical_bytes -Sum).Sum -eq $discovery.logical_bytes) 'Discovery totals do not match inventory.'
$links = @(Read-Json (Join-Path $phase 'LINK_AUDIT.json'))
Assert-Condition ($links.Count -eq 27 -and @($links | Where-Object {$_.target}).Count -eq 2) 'Link audit tally mismatch.'

$linkChecks = 0
foreach ($relative in @('AGENTS.md','docs/migration/README.md','docs/migration/PLAN.md')) {
    $document = Join-Path $repository $relative
    $content = Get-Content -LiteralPath $document -Raw
    foreach ($match in [regex]::Matches($content, '\[[^\]]+\]\(([^)]+)\)')) {
        $target = $match.Groups[1].Value.Split('#')[0]
        if ($target -match '^[a-z]+://' -or $target.Length -eq 0) { continue }
        Assert-Condition (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $document) $target)) ('Missing document link: ' + $target)
        $linkChecks++
    }
}

$phaseSealCount = 0
$phaseSeal = Join-Path $phase 'DELIVERY_SEAL.json'
if (Test-Path -LiteralPath $phaseSeal) {
    foreach ($entry in (Read-Json $phaseSeal).files) {
        Test-Asset (Join-Path $phase $entry.path) $entry
        $phaseSealCount++
    }
}
[ordered]@{
    passed=$true; stage='A0_BASELINE_AND_PLAN_COMPLETE';
    authority_original_backups_exact=$true; new_authority_proof_matches=$true;
    historical_scientific_seal_files_verified=$oldCount;
    historical_scientific_seal_bytes_verified=$oldBytes;
    historical_source_freeze_entries_verified=$sourceCount;
    historical_closeout_seal_entries_verified=$oldCloseoutCount;
    historical_live_AGENTS_hash_assertion_superseded=$true;
    old_verifier_executed_after_authority_change=$false;
    inventory_roots=6; metadata_files=$discovery.files;
    metadata_logical_bytes=$discovery.logical_bytes; metadata_arithmetic_verified=$true;
    full_file_content_inventory_hashes=$false; unresolved_link_targets=25;
    current_markdown_links_verified=$linkChecks; phase_seal_entries_verified=$phaseSealCount;
    experiments_or_training_run=$false; model_loaded=$false; wsl_started=$false;
    existing_scientific_records_modified=$false; overall_migration_audit_complete=$false;
    next_stage='A1_ASSET_CLASSIFICATION_AND_PRESERVATION'
} | ConvertTo-Json -Depth 4
