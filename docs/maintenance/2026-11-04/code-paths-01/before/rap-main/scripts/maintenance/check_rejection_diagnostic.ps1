$ErrorActionPreference = 'Stop'
$root = 'E:/githouse/RAP-main'
$out = "$root/docs/maintenance/2026-09-15/rejection-diagnostic-01"
if (Test-Path -LiteralPath "$out/crosscheck.json") { throw 'Completed check already exists' }
$rows = @(Get-Content -Raw "$out/pairs.json" | ConvertFrom-Json)
$summary = Get-Content -Raw "$out/summary.json" | ConvertFrom-Json
$checked = 0
$aucChecks = 0
foreach ($seq in @('00', '08')) {
    $parent = "$root/docs/maintenance/2026-09-15/proposal-context-dev-01/$seq"
    $original = @(Get-Content -Raw "$parent/evaluator_only_decisions.json" | ConvertFrom-Json)
    $gates = Get-Content -Raw "$parent/gates.json" | ConvertFrom-Json
    foreach ($method in @('A-R4', 'P-R4')) {
        $arm = $method.Substring(0, 1)
        $subset = @($rows | Where-Object { $_.sequence -eq $seq -and $_.method -eq $method })
        if ($subset.Count -ne 100) { throw 'Count mismatch' }
        foreach ($r in $subset) {
            $source = @($original | Where-Object { $_.source_i -eq $r.source_i -and $_.source_j -eq $r.source_j })
            if ($source.Count -ne 1) { throw 'Pair mapping is not unique' }
            $v = $source[0].methods.$method
            $g = $gates.($r.key).$arm[$v.generation]
            $strict = $v.RTE_m -le 1 -and $v.RRE_deg -le 5
            $category = if ($strict) { 'correct' } else { 'incorrect' }
            $category += if ($g.accepted) { '_accepted' } else { '_rejected' }
            if ($category -ne $r.category) { throw 'Category mismatch' }
            if (($v.RTE_m -le 5 -and $v.RRE_deg -le 10) -ne $r.legacy_safe) { throw 'Legacy label mismatch' }
            $clauses = @()
            if ($g.overlap_ratio -lt 0.7) { $clauses += 'overlap' }
            if ($g.mean_dist -gt 2.5) { $clauses += 'distance' }
            $expected = if ($clauses.Count) { $clauses -join '+' } else { 'none' }
            if ($expected -ne $r.rejected_clauses) { throw 'Gate clause mismatch' }
            if ($g.accepted -and ($r.selected_neighbors -ne 3 -or -not $r.legacy_safe)) { throw 'Consensus or legacy statement failed' }
            if ($method -eq 'A-R4' -and $r.category -eq 'incorrect_accepted' -and $r.candidate_strict_count -ne 0) { throw 'Candidate statement failed' }
            if ($r.stratum -eq 'confuser' -and $g.accepted) { throw 'Confuser statement failed' }
            $checked++
        }
        $s = $summary."$seq/$method"
        foreach ($group in ($subset | Group-Object category)) {
            if ($s.counts.($group.Name) -ne $group.Count) { throw 'Summary mismatch' }
        }
        $good = @($subset | Where-Object category -eq 'correct_accepted')
        $bad = @($subset | Where-Object category -eq 'incorrect_accepted')
        foreach ($feature in @('overlap','mean_distance','rigidity','translation_spread_m','rotation_spread_deg','selected_neighbors')) {
            $wins = 0.0
            foreach ($a in $good) { foreach ($b in $bad) {
                $delta = $a.$feature - $b.$feature
                if ($feature -notin @('overlap','selected_neighbors')) { $delta = -$delta }
                if ($delta -gt 0) { $wins += 1 } elseif ($delta -eq 0) { $wins += 0.5 }
            } }
            $auc = $wins / ($good.Count * $bad.Count)
            if ([Math]::Abs($auc - $s.accepted_correctness_auc.$feature) -gt 1e-12) { throw 'AUC mismatch' }
            $aucChecks++
        }
    }
}
@{passed=$true; rows=$checked; auc_checks=$aucChecks; method='Separate PowerShell reconstruction from frozen decisions/gates and diagnostic rows'; limitations='Dispersion and all-candidate correctness computed by primary Python diagnostic; no second raw-cloud evaluation'} | ConvertTo-Json | Set-Content -Encoding UTF8 "$out/crosscheck.json"
Write-Output "Passed: $checked rows, $aucChecks ordering summaries."
