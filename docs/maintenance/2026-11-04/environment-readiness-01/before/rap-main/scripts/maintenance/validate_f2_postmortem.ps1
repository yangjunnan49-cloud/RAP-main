param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$base = Join-Path $root 'docs/maintenance/2026-09-27/f2-structured-dev-01'
$out = Join-Path $root 'docs/maintenance/2026-09-27/f2-postmortem-01'
$analysis = Get-Content -LiteralPath (Join-Path $out 'analysis.json') -Raw | ConvertFrom-Json
$freeze = Get-Content -LiteralPath (Join-Path $out 'freeze.json') -Raw | ConvertFrom-Json
$checks = 0
foreach ($entry in $freeze.sha256.PSObject.Properties) {
    $path = Join-Path $root $entry.Name
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Value) { throw "Frozen input changed: $($entry.Name)" }
    $checks++
}
foreach ($seq in @('00', '08')) {
    $rows = Get-Content -LiteralPath (Join-Path $base "$seq/evaluator_only_decisions.json") -Raw | ConvertFrom-Json
    $metrics = Get-Content -LiteralPath (Join-Path $base "$seq/metrics.json") -Raw | ConvertFrom-Json
    if ($rows.Count -ne 100) { throw "Wrong pair count: $seq" }
    foreach ($arm in @('N', 'S', 'P')) {
        $positive = @($rows | Where-Object { $_.stratum -ne 'confuser' })
        $correct = @($positive | Where-Object { $_.methods.$arm.strict }).Count
        $correctAccepted = @($positive | Where-Object { $_.methods.$arm.strict -and $_.methods.$arm.accepted }).Count
        $oracle = @($positive | Where-Object { $_.methods."$arm-OR4".strict }).Count
        $wrongAccepted = @($rows | Where-Object { $_.methods.$arm.incorrect_accepted }).Count
        $confuserAccepted = @($rows | Where-Object { $_.stratum -eq 'confuser' -and $_.methods.$arm.accepted }).Count
        $part = $analysis.sequences.$seq.arms.$arm.partition
        $saved = $metrics.overall.$arm
        if ($correct -ne $saved.strict_positive_successes -or
            $correctAccepted -ne $saved.correct_positive_accepts -or
            $wrongAccepted -ne $saved.incorrect_accepted -or
            $confuserAccepted -ne $saved.accepted_confusers -or
            $correctAccepted -ne $part.correct_accepted -or
            ($correct - $correctAccepted) -ne $part.correct_rejected -or
            ($oracle - $correct) -ne $part.selection_miss -or
            (75 - $oracle) -ne $part.proposal_unavailable) {
            throw "Independent count mismatch: $seq $arm"
        }
        $checks += 8
    }
}
$result = [ordered]@{
    passed = $true
    scope = 'Independent PowerShell recount from F2 evaluator rows and frozen metrics; no new inference'
    checks = $checks
    analysis_sha256 = (Get-FileHash -LiteralPath (Join-Path $out 'analysis.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    validator_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'validation.json') -Encoding utf8
