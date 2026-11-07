$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/native_stability_control_20261021'
$preflight=Get-Content -Raw (Join-Path $out 'PREFLIGHT.json') | ConvertFrom-Json
$worker=Get-Content -Raw (Join-Path $out 'supervision/preflight/worker_exit.json') | ConvertFrom-Json
$runner=Get-Content -Raw (Join-Path $out 'supervision/preflight/runner_exit.json') | ConvertFrom-Json
$hostReceipt=Get-Content -Raw (Join-Path $out 'supervision/preflight/host_exit.json') | ConvertFrom-Json
if(-not $preflight.passed -or -not $worker.success -or -not $runner.success -or $hostReceipt.exit_code -ne 0){throw 'Preflight must pass completely before real admission'}
$freeze=Get-Content -Raw (Join-Path $out 'supervision/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw ('Frozen source changed: '+$file.Name)}}
$newBytes=0L
foreach($top in @('work','outputs')){$newBytes += [long](Get-ChildItem -LiteralPath (Join-Path $root $top) -File -Recurse | Measure-Object -Property Length -Sum).Sum}
$copies=@('p0-validation-01','guard-hardening-01','native-stability-review-01','boundary-contract-01','continuation-final-01','handoff-recovery-01','guard-recorder-integration-01')
foreach($name in $copies){$newBytes += [long](Get-ChildItem -LiteralPath ('E:\githouse\RAP-main\docs\maintenance\2026-10-21\'+$name) -File -Recurse | Measure-Object -Property Length -Sum).Sum}
if($newBytes+8MB -gt 64MB -or $newBytes+140458966L+8MB -gt 256MB){throw 'Insufficient full-stage dossier reserve'}
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
if($elapsed -ge 900){throw 'Insufficient prospective whole-scope reserve before real stages'}
$newFiles=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$newFiles[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
$result=@{admitted=$true;utc=[DateTimeOffset]::UtcNow.ToString('o');whole_scope_elapsed=$elapsed;whole_scope_cap=1800;close_reserve=180;new_bytes_at_admission=$newBytes;remaining_growth_reserve=8MB;combined_old_bytes=140458966L;all_source_files=$newFiles;preflight_checks=@($preflight.checks).Count;preflight_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'PREFLIGHT.json')).Hash;runtime_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'RUNTIME_BINDING.json')).Hash;source_freeze_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'supervision/SOURCE_FREEZE.json')).Hash;fixed_stages=@('front','native1','native2','analysis');GT_reads=0;successful_real_stages_replayed=0;scope='Fresh frontend once; exact-map-and-pose native serial diagnostic only'}
[IO.File]::WriteAllText((Join-Path $out 'ADMISSION.json'),($result | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$result | Select-Object admitted,whole_scope_elapsed,preflight_checks,new_bytes_at_admission | ConvertTo-Json
