$ErrorActionPreference='Stop'
$previous=Join-Path (Split-Path $PSScriptRoot -Parent) 'guard_recorder_integration_01'
$utf8=[Text.UTF8Encoding]::new($false)
$identity=(Get-Content -Raw (Join-Path $previous 'identity.py')).Replace("'worker': 'worker.py'","'worker': 'native_stage.py'")
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'identity.py'),$identity,$utf8)
Copy-Item -LiteralPath (Join-Path $previous 'stop_identity.py') -Destination (Join-Path $PSScriptRoot 'stop_identity.py')
$runner=Get-Content -Raw (Join-Path $previous 'lease_runner.py')
$runner=$runner.Replace('scope_cap = 780.0','scope_cap = 1620.0')
$runner=$runner.Replace("if group_rss > (32 if case == 'rss_fault' else 512) * 2**20:",'if group_rss > 4 * 2**30:')
$runner=$runner.Replace("[sys.executable, '-B', str(ROOT / 'worker.py'), str(folder), case]","['/root/venvs/kiss-slam-hc1/bin/python', '-B', str(ROOT / 'native_stage.py'), str(folder), case]")
$runner=$runner.Replace("record(worker.pid, ROOT / 'worker.py')","record(worker.pid, ROOT / 'native_stage.py')")
$runner=$runner.Replace("env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))","env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', OPEN3D_CPU_RENDERING='true'))")
$needle="    group_rss = 0"
$insert="    if sum(p.stat().st_size for root in (ROOT, folder.parent.parent) for p in root.rglob('*') if p.is_file()) > 8*2**20:`n        raise RuntimeError('N1_work_output_growth_cap')`n    group_rss = 0"
$runner=$runner.Replace($needle,$insert)
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'lease_runner.py'),$runner,$utf8)
$host=Get-Content -Raw (Join-Path $previous 'host.ps1')
$host=$host.Replace('guard_recorder_integration_20261021','native_stability_control_20261021').Replace('guard_recorder_integration_01','native_stability_control_01')
$host=$host.Replace("[string]`$Run='run01'","[string]`$Run='supervision'")
$host=$host.Replace(' -ge 780',' -ge 1620').Replace('$hostCap=15.;$linuxCap=15.','$hostCap=1500.;$linuxCap=1500.')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'host.ps1'),$host,$utf8)
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/native_stability_control_20261021'
New-Item -ItemType Directory -Path (Join-Path $out 'supervision') | Out-Null
$hashes=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$hashes[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
$binding=@{files=$hashes;protocol_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'PROTOCOL.md')).Hash;original_guard_sources=@{identity=(Get-FileHash -LiteralPath (Join-Path $previous 'identity.py')).Hash;runner=(Get-FileHash -LiteralPath (Join-Path $previous 'lease_runner.py')).Hash;host=(Get-FileHash -LiteralPath (Join-Path $previous 'host.ps1')).Hash};adaptation='New root/stage worker, original native interpreter/environment,4GiB RSS,1800s scope/180s reserve,8MiB growth; nonce/identity mechanism unchanged';successful_stages_not_replayed=$true}
[IO.File]::WriteAllText((Join-Path $out 'supervision/SOURCE_FREEZE.json'),($binding | ConvertTo-Json -Depth 5),$utf8)
