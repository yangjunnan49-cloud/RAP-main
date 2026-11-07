param([string]$OutputDirectory = 'E:\githouse\RAP-main\docs\maintenance\2026-10-12\stage-review-01')

# Read-only evidence review. No model imports, inference, optimization or raw preprocessing.
$ErrorActionPreference = 'Stop'
$mainRoot = 'E:\githouse\RAP-main'
$clock = [Diagnostics.Stopwatch]::StartNew()
$hashCache = @{}
$identityRows = [Collections.Generic.List[object]]::new()
$deliveryRows = [Collections.Generic.List[object]]::new()
$wslReceipt = Get-Content -LiteralPath (Join-Path $OutputDirectory 'WSL_SOURCE_HASHES.json') -Raw | ConvertFrom-Json

function LocalPath([string]$path) {
    if ($path.StartsWith('/mnt/e/')) { return [IO.Path]::GetFullPath('E:/' + $path.Substring(7)) }
    return [IO.Path]::GetFullPath($path)
}

function CheckHash([string]$path, [string]$expected, [string]$scope) {
    if ($path.StartsWith('/root/')) {
        $observed = $wslReceipt.files.$path
        if (-not $observed -or $observed -ne $expected.ToLowerInvariant()) { throw "WSL source hash mismatch or missing receipt: $path" }
        $identityRows.Add([ordered]@{ scope=$scope; path=$path; sha256=$observed; method='separate WSL sha256sum receipt'; bytes=$null })
        return
    }
    $local = LocalPath $path
    if (-not $hashCache.ContainsKey($local)) {
        $item = Get-Item -LiteralPath $local
        $hashCache[$local] = @{ sha256 = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant(); bytes = $item.Length }
    }
    $actual = $hashCache[$local]
    if ($actual.sha256 -ne $expected.ToLowerInvariant()) { throw "Identity mismatch: $local" }
    $identityRows.Add([ordered]@{ scope=$scope; path=$local; sha256=$actual.sha256; bytes=$actual.bytes })
}

$folders = @(
    '2026-10-10/native-output-capability-01',
    '2026-10-10/native-noise-robustness-01',
    '2026-10-10/native-pose-objective-fit-01',
    '2026-10-10/native-pose-objective-fit-01/delivery-correction-01',
    '2026-10-10/rigid-control-conditioning-01',
    '2026-10-10/wsl-runtime-recovery-01',
    '2026-10-10/native-conditioned-comparison-01',
    '2026-10-10/native-conditioned-comparison-01/attempt-02',
    '2026-10-09/measured-map-reoptimization-01',
    '2026-10-09/shared-plane-map-pilot-01',
    '2026-10-09/structural-holdout-map-pilot-01',
    '2026-10-09/cross-visit-map-pilot-01',
    '2026-10-09/rotation-protected-map-pilot-01',
    '2026-10-10/membership-formation-diagnosis-01'
)
foreach ($name in $folders) {
    $root = Join-Path $mainRoot ('docs/maintenance/' + $name)
    $seal = Get-Content -LiteralPath (Join-Path $root 'DELIVERY_SEAL.json') -Raw | ConvertFrom-Json
    foreach ($row in $seal.files) { CheckHash (Join-Path $root $row.path) $row.sha256 ('delivery:' + $name) }
    $deliveryRows.Add([ordered]@{ folder=$name; entries=@($seal.files).Count; passed=$true })
}

$benchmark = Join-Path $mainRoot 'docs/meeting_20261011/benchmark'
$freeze = Get-Content -LiteralPath (Join-Path $benchmark 'freeze.json') -Raw | ConvertFrom-Json
foreach ($prop in $freeze.sources.PSObject.Properties) { CheckHash $prop.Name $prop.Value 'benchmark_sources' }
$trajectories = Get-Content -LiteralPath (Join-Path $benchmark 'attempt03/trajectory_seal.json') -Raw | ConvertFrom-Json
foreach ($prop in $trajectories.PSObject.Properties) { CheckHash $prop.Name $prop.Value 'benchmark_trajectories_and_bindings' }
$nativeFreeze = Get-Content -LiteralPath (Join-Path $mainRoot 'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02/freeze.json') -Raw | ConvertFrom-Json
foreach ($prop in $nativeFreeze.files.PSObject.Properties) { CheckHash $prop.Name $prop.Value 'NOC4_attempt02_freeze' }

$results = Get-Content -LiteralPath (Join-Path $benchmark 'attempt03/results.json') -Raw | ConvertFrom-Json
$validation = Get-Content -LiteralPath (Join-Path $benchmark 'attempt03/validation.json') -Raw | ConvertFrom-Json
if (@($results.rows).Count -ne 36 -or -not $validation.passed) { throw 'Benchmark completion record failed' }
$expectedCounts = @{ '00'=4541; '05'=2761; '06'=1101; '07'=1101; '09'=1591; '10'=1201 }
foreach ($row in $results.rows) {
    if ($row.exit -ne 0 -or -not $row.resource.complete -or $row.frames -ne $expectedCounts[$row.sequence]) { throw "Incomplete run: $($row.name)" }
    CheckHash $row.source $row.sha256 'benchmark_metric_source'
}

function Mean($values) { return ($values | Measure-Object -Average).Average }
function PopulationStd($values, [double]$average) {
    $sum = 0.0
    foreach ($value in $values) { $sum += ([double]$value - $average) * ([double]$value - $average) }
    return [Math]::Sqrt($sum / @($values).Count)
}
$cohortRows = [Collections.Generic.List[object]]::new()
foreach ($model in 'RAP-SLAM','KISS-SLAM') {
    foreach ($cohort in '00/05/06','07/09/10','all6') {
        $sequences = if ($cohort -eq 'all6') { @('00','05','06','07','09','10') } else { $cohort.Split('/') }
        $repetitions = @(foreach ($rep in 1,2,3) {
            $subset = @($results.rows | Where-Object { $_.model -eq $model -and $_.rep -eq $rep -and $_.sequence -in $sequences })
            if ($subset.Count -ne $sequences.Count) { throw "Run grid mismatch: $model/$cohort/$rep" }
            [ordered]@{ rep=$rep; ter=(Mean $subset.ter); ate=(Mean $subset.ate) }
        })
        $values = [ordered]@{}
        foreach ($metric in 'ter','ate') {
            $average = Mean $repetitions.$metric
            $std = PopulationStd $repetitions.$metric $average
            $stored = $results.cohorts.$model.$cohort.summary.$metric
            if ([Math]::Abs($average-$stored.mean) -gt 1e-12 -or [Math]::Abs($std-$stored.std) -gt 1e-12) { throw "Aggregate mismatch: $model/$cohort/$metric" }
            $values[$metric] = [ordered]@{mean=$average;population_std=$std}
        }
        $best = @($repetitions | Sort-Object { $_.ter }, { $_.ate }, { $_.rep })[0]
        if ($best.rep -ne $results.cohorts.$model.$cohort.best_single_rep.rep) { throw 'Best repetition mismatch' }
        $cohortRows.Add([ordered]@{model=$model;cohort=$cohort;metrics=$values;best_single_rep=$best.rep})
    }
}

$sequenceRows = @(foreach ($seq in '00','05','06','07','09','10') {
    $rap = @($results.rows | Where-Object { $_.model -eq 'RAP-SLAM' -and $_.sequence -eq $seq })
    $kiss = @($results.rows | Where-Object { $_.model -eq 'KISS-SLAM' -and $_.sequence -eq $seq })
    [ordered]@{sequence=$seq;RAP_ter=(Mean $rap.ter);KISS_ter=(Mean $kiss.ter);RAP_ATE=(Mean $rap.ate);KISS_ATE=(Mean $kiss.ate)}
})
$noc4root = Join-Path $mainRoot 'docs/maintenance/2026-10-10/native-conditioned-comparison-01/attempt-02'
$noc4status = Get-Content -LiteralPath (Join-Path $noc4root 'STATUS.json') -Raw | ConvertFrom-Json
if ($noc4status.scientific_comparison_complete -or $noc4status.fit_updates -ne 0 -or $noc4status.optimizer_probe_calls -ne 4 -or -not (Test-Path -LiteralPath (Join-Path $noc4root 'INCOMPLETE'))) { throw 'NOC4 stop boundary differs' }

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$clock.Stop()
$check = [ordered]@{
    status='BOUNDED_READ_ONLY_EVIDENCE_REVIEW_PASSED'
    review_date='2026-10-12 Asia/Shanghai'
    delivery_checks=@($deliveryRows)
    unique_hashed_files=($hashCache.Count + @($wslReceipt.files.PSObject.Properties).Count)
    unique_local_hashed_files=$hashCache.Count
    separate_WSL_source_files=@($wslReceipt.files.PSObject.Properties).Count
    identity_references=$identityRows.Count
    unique_hashed_bytes=($hashCache.Values.bytes | Measure-Object -Sum).Sum
    benchmark_source_entries=@($freeze.sources.PSObject.Properties).Count
    benchmark_trajectory_binding_entries=@($trajectories.PSObject.Properties).Count
    NOC4_attempt02_freeze_entries=@($nativeFreeze.files.PSObject.Properties).Count
    benchmark_complete_runs=36
    benchmark_original_independent_validation=$validation
    arithmetic_recount=$cohortRows.ToArray()
    per_sequence_recount=$sequenceRows
    NOC4_current_status=$noc4status
    review_wall_seconds=$clock.Elapsed.TotalSeconds
    review_attempt_note='Initial review stopped at Windows mapping of a Linux-only source path before emitting review results. Helper now uses a separately observed WSL source-hash receipt. No historical source, scientific array, gate or seal was repaired.'
    scope='SHA256/file identity checks and arithmetic from stored scalar results only; no fresh trajectory metric, raw preprocessing, descriptor, neural, backward, optimizer or physical reference replay. No all-history audit or new resource-cap certification.'
}
$check | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'CHECKS.json') -Encoding utf8
$identityRows.ToArray() | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'IDENTITY_CHECKS.json') -Encoding utf8
[ordered]@{status=$check.status;unique_hashed_files=$check.unique_hashed_files;delivery_dossiers=$deliveryRows.Count;benchmark_runs=36;wall_seconds=$check.review_wall_seconds} | ConvertTo-Json
