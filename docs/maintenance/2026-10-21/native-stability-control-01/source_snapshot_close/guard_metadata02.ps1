$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
$runner=Get-Content -Raw (Join-Path $PSScriptRoot 'lease_runner.py')
$runner=$runner.Replace('from identity import','from identity02 import').Replace("'SOURCE_FREEZE.json'","'SOURCE_FREEZE02.json'")
$old='synthetic=True, raw_reads=0, GT_reads=0, new_predictions=0)'
if(-not $runner.Contains($old)){throw 'Expected metadata template absent'}
$runner=$runner.Replace($old,"synthetic=(case == 'preflight'), workload_stage=case, payload_counts='SEE_WORKER_AND_BANK_RECEIPTS')")
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'lease_runner02.py'),$runner,$utf8)
$identity=(Get-Content -Raw (Join-Path $PSScriptRoot 'identity.py')).Replace("'runner': 'lease_runner.py'","'runner': 'lease_runner02.py'")
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'identity02.py'),$identity,$utf8)
$stopText=(Get-Content -Raw (Join-Path $PSScriptRoot 'stop_identity.py')).Replace('from identity import','from identity02 import')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'stop_identity02.py'),$stopText,$utf8)
$hostText=(Get-Content -Raw (Join-Path $PSScriptRoot 'host.ps1')).Replace('lease_runner.py','lease_runner02.py').Replace('stop_identity.py','stop_identity02.py')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'host02.ps1'),$hostText,$utf8)
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_control_20261021'
$oldFreeze=Get-Content -Raw (Join-Path $out 'supervision/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $oldFreeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'Original frozen source changed'}}
$files=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$files[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
[IO.File]::WriteAllText((Join-Path $out 'supervision/SOURCE_FREEZE02.json'),(@{files=$files;prior_freeze_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'supervision/SOURCE_FREEZE.json')).Hash;binding02_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'BINDING02.md')).Hash;frontend_seal_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'frontend/SEAL.json')).Hash;numerical_sources_changed=$false;successful_stages_replayed=0;scope_cap_unchanged=1800} | ConvertTo-Json -Depth 5),$utf8)
[IO.File]::WriteAllText((Join-Path $out 'RECEIPT_CLASSIFICATION_CORRECTION.json'),(@{original_receipt_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'supervision/front/runner_exit.json')).Hash;stage='front';original_fields_invalid=@('synthetic','raw_reads','new_predictions');correct_synthetic=$false;actual_raw_frames=1101;new_frontend_poses=1101;GT_reads=0;authoritative_bank_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'frontend/SEAL.json')).Hash;original_receipt_retained=$true;old_clocks_memory_identity_and_exits_unchanged=$true} | ConvertTo-Json -Depth 4),$utf8)
