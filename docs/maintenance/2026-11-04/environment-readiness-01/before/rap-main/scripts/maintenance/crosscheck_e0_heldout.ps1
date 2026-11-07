param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$base = Join-Path $root 'docs/maintenance/2026-09-27/e0-heldout-01'
$r = Get-Content -LiteralPath (Join-Path $base 'results.json') -Raw | ConvertFrom-Json
$v = Get-Content -LiteralPath (Join-Path $base 'validation.json') -Raw | ConvertFrom-Json
$seqs = @('07', '09', '10')
$frames = @{ '07' = 1101; '09' = 1591; '10' = 1201 }
$checks = 0
foreach ($seq in $seqs) {
    foreach ($arm in @('O', 'A')) {
        $summary = Get-Content -LiteralPath (Join-Path $base "full-$seq-$arm/summary.json") -Raw | ConvertFrom-Json
        $ids = Get-Content -LiteralPath (Join-Path $base "full-$seq-$arm/source_frames.json") -Raw | ConvertFrom-Json
        if ($summary.n_scans -ne $frames[$seq] -or $ids.source_frame_ids.Count -ne $frames[$seq]) { throw "Frame count mismatch: $seq $arm" }
        if ($summary.config.apply_kitti_205 -ne ($arm -eq 'A')) { throw "Configuration mismatch: $seq $arm" }
        if (($r.sequences.$seq.$arm.strict_correct + $r.sequences.$seq.$arm.strict_incorrect) -ne $r.sequences.$seq.$arm.accepted_loops) { throw "Loop label mismatch: $seq $arm" }
        $checks += 3
    }
}
foreach ($arm in @('O', 'A', 'KISS')) {
    foreach ($metric in @('ter', 'rer', 'ate')) {
        $sum = 0.0
        foreach ($seq in $seqs) { $sum += [double]$r.sequences.$seq.$arm.$metric }
        if ([math]::Abs($sum / 3 - [double]$r.means.$arm.$metric) -gt 1e-12) { throw "Mean mismatch: $arm $metric" }
        $checks++
    }
}
$transfer = ($r.means.A.ter -le $r.means.O.ter - 0.02) -and ($r.means.A.ate -lt $r.means.O.ate)
foreach ($seq in $seqs) { $transfer = $transfer -and ($r.sequences.$seq.A.ter -le $r.sequences.$seq.O.ter + 0.05) }
$decision = if ($transfer) { 'HELDOUT_TRANSFER' } else { 'NO_HELDOUT_TRANSFER' }
if ($decision -ne $r.decision -or $decision -ne $v.decision) { throw 'Decision mismatch' }
$checks++
$out = [ordered]@{
    passed = $true
    checks = $checks
    decision = $decision
    scope = 'Independent PowerShell recount of means, decision, frame counts, correction flags and accepted labels'
    results_sha256 = (Get-FileHash -LiteralPath (Join-Path $base 'results.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
$out | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $base 'decision_crosscheck.json') -Encoding utf8
