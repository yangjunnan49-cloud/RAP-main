$ErrorActionPreference='Stop'
$previous=Join-Path (Split-Path $PSScriptRoot -Parent) 'guard_recorder_integration_01'
$utf8=[Text.UTF8Encoding]::new($false)
foreach($name in @('identity.py','stop_identity.py')){Copy-Item -LiteralPath (Join-Path $previous $name) -Destination (Join-Path $PSScriptRoot $name)}
$runner=Get-Content -Raw (Join-Path $previous 'lease_runner.py')
$runner=$runner.Replace('scope_cap = 780.0','scope_cap = 480.0')
$runner=$runner.Replace("[sys.executable, '-B', str(ROOT / 'worker.py'), str(folder), case]","['/root/venvs/kiss-slam-hc1/bin/python', '-B', str(ROOT / 'worker.py'), str(folder), case]")
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'lease_runner.py'),$runner,$utf8)
$hostText=(Get-Content -Raw (Join-Path $previous 'host.ps1')).Replace('guard_recorder_integration_20261021','chunk_hash_feasibility_20261021').Replace('guard_recorder_integration_01','chunk_hash_feasibility_01')
$hostText=$hostText.Replace(' -ge 780',' -ge 480').Replace('$hostCap=15.;$linuxCap=15.','$hostCap=90.;$linuxCap=90.')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'host.ps1'),$hostText,$utf8)
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/chunk_hash_feasibility_20261021/run01'
New-Item -ItemType Directory -Path $out | Out-Null
$files=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$files[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
[IO.File]::WriteAllText((Join-Path $out 'SOURCE_FREEZE.json'),(@{files=$files;scope='synthetic NumPy layout hashing only';protocol_sha256=(Get-FileHash -LiteralPath (Join-Path (Split-Path $out -Parent) 'PROTOCOL.md')).Hash;old_N1_remains_incomplete=$true} | ConvertTo-Json -Depth 4),$utf8)
