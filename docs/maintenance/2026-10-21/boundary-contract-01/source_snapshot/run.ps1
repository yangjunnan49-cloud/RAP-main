$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $taskRoot 'outputs/boundary_contract_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
function Elapsed { [Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency) }
if((Elapsed) -gt 240){throw 'Synthetic scope close reserve reached'}
$freeze=Get-ChildItem -LiteralPath $PSScriptRoot -File | ForEach-Object {[ordered]@{name=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}}
[IO.File]::WriteAllText((Join-Path $out 'SOURCE_FREEZE.json'),($freeze | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$pre=[Diagnostics.Stopwatch]::GetTimestamp()
$mem=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$headroom=[long]$mem.CommitLimit-[long]$mem.CommittedBytes
$age=([Diagnostics.Stopwatch]::GetTimestamp()-$pre)/[Diagnostics.Stopwatch]::Frequency
if($headroom -lt 12GB -or $age -gt 2){throw 'Fresh prelaunch memory guard failed'}
& wsl -d Ubuntu-24.04 -u root -- /usr/bin/timeout 10 /usr/bin/env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /root/miniconda3/envs/rap-inference/bin/python -B /mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/work/boundary_contract_01/check_contract.py
$code=$LASTEXITCODE
$elapsed=Elapsed
$result=Get-Content -Raw (Join-Path $out 'RESULTS.json') | ConvertFrom-Json
if($code -ne 0 -or $elapsed -ge 270 -or $result.max_rss_bytes -gt 512MB){throw 'Synthetic check or resource scope failed'}
[IO.File]::WriteAllText((Join-Path $out 'RUN_RECEIPT.json'),(@{exit_code=$code;elapsed_seconds=$elapsed;cap_seconds=300;headroom_bytes=$headroom;headroom_observation_seconds=$age;timeout_seconds=10;payload='synthetic stdlib only';live_native_integration=$false} | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
