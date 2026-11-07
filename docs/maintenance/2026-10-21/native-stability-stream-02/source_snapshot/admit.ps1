$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_stream_20261021'
$inputRoot=Join-Path $root 'outputs/native_stability_control_20261021'
$p=Get-Content -Raw (Join-Path $out 'PREFLIGHT.json') | ConvertFrom-Json
foreach($name in @('worker_exit.json','runner_exit.json')){if(-not (Get-Content -Raw (Join-Path $out ('supervision/preflight/'+$name)) | ConvertFrom-Json).success){throw 'N2 preflight incomplete'}}
if(-not $p.passed -or @($p.checks).Count -ne 17){throw 'N2 controls incomplete'}
$freeze=Get-Content -Raw (Join-Path $out 'supervision/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'N2 frozen source changed'}}
foreach($file in $freeze.readonly_N1_inputs.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $inputRoot $file.Name)).Hash -ne $file.Value){throw 'Read-only N1 bank/status changed'}}
$oldStatus=Get-Content -Raw (Join-Path $inputRoot 'COSTS_FINAL.json') | ConvertFrom-Json
if($oldStatus.status -ne 'CLOSED_INCOMPLETE_ARRAY_CAPTURE_CAP' -or $oldStatus.native2_launched){throw 'N1 stop was not retained'}
$oldRuntime=Get-Content -Raw (Join-Path $inputRoot 'RUNTIME_BINDING.json') | ConvertFrom-Json
$newRuntime=Get-Content -Raw (Join-Path $out 'RUNTIME_BINDING.json') | ConvertFrom-Json
foreach($library in $oldRuntime.libraries.PSObject.Properties){if($newRuntime.libraries.($library.Name) -ne $library.Value){throw ('Runtime binding differs: '+$library.Name)}}
$newBytes=0L
foreach($top in @('work','outputs')){$newBytes += [long](Get-ChildItem -LiteralPath (Join-Path $root $top) -File -Recurse | Measure-Object Length -Sum).Sum}
foreach($name in @('p0-validation-01','guard-hardening-01','native-stability-review-01','boundary-contract-01','continuation-final-01','handoff-recovery-01','guard-recorder-integration-01','native-stability-control-01','chunk-hash-feasibility-01')){$newBytes += [long](Get-ChildItem -LiteralPath ('E:\githouse\RAP-main\docs\maintenance\2026-10-21\'+$name) -File -Recurse | Measure-Object Length -Sum).Sum}
if($newBytes+14MB+1MB -gt 64MB -or $newBytes+140458966L+14MB+1MB -gt 256MB){throw 'Full N2 data+closure reserve does not fit original dossier bounds'}
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
if($elapsed -ge 1000){throw 'Insufficient complete-stage time reserve'}
$result=@{admitted=$true;utc=[DateTimeOffset]::UtcNow.ToString('o');scope_elapsed=$elapsed;scope_cap=1800;close_reserve=180;controls=17;new_bytes_at_admission=$newBytes;data_reserve_bytes=14MB;documentary_reserve_bytes=1MB;N1_unchanged_incomplete=$true;frontend_generation_repeated=$false;N1_runtime_bindings_match=$true;fixed_stages=@('native1','native2','analysis');real_retry_after_failure=$false;source_freeze_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'supervision/SOURCE_FREEZE.json')).Hash;admission_source_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}
[IO.File]::WriteAllText((Join-Path $out 'ADMISSION.json'),($result | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
