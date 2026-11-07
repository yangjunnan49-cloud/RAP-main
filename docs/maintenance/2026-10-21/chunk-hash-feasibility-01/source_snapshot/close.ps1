$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/chunk_hash_feasibility_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$worker=Get-Content -Raw (Join-Path $out 'run01/normal/worker_exit.json') | ConvertFrom-Json
$runner=Get-Content -Raw (Join-Path $out 'run01/normal/runner_exit.json') | ConvertFrom-Json
if(-not $worker.success -or -not $runner.success -or $worker.count -ne 21){throw 'Feasibility controls incomplete'}
$freeze=Get-Content -Raw (Join-Path $out 'run01/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'Frozen source changed'}}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\chunk-hash-feasibility-01'
if(Test-Path -LiteralPath $target){throw 'Preserve prior handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 synthetic chunkhash feasibility COMPLETE under distinct600s scope.21controlsPASS originalNumPy runtime, exact C-byte SHA matches wholecopy reference acrossC/F/strides/endian/empty/scalar/integer/bool,20.186568MB and64MiB arrays. Tracedhashscratchmax3146897bytes<16MiB; chunk<=1MiB; workerpeak118693888/watchobserved119697408<512MiB; source>64MiB/objectdtype rejected. Referencewholecopy outside measuredwindow; notglobal/nativepeak guarantee. OriginalN1codec stillrejects20.186568MB; N1incomplete16MiB stop unchanged, no realrerun. FullC outputs chunk_hash_feasibility_20261021; repo docs/maintenance/2026-10-21/chunk-hash-feasibility-01/snapshot/REPORT_CN and run01. AllsyntheticNumPy only, raw/GT/SLAMnative/solver/predictions0. Future separately frozen observer may use boundedhashscratch, omitlargeoutputmultisets/pairconcatenation, and record upstream nativevoxelization tolocalizeinputchanges; no nativepayload admitted here. Actual47%/ordinarytrue/reset1792606845 lastobserved NOTexhaustion; ownercontinuationACTIVE. P0closedFAIL,oldcaps/production/default/Git/install/outreach/scheduler/goalstatus limits retained; originalresearchunresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 fixed-memory hash synthetic feasibility`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$result=@{status='CLOSED_SYNTHETIC_PASS';elapsed_seconds=$elapsed;cap_seconds=600;budget_compliant=($elapsed -lt 600);controls=21;max_scratch_bytes=3146897;worker_peak_RSS_bytes=$worker.max_rss_bytes;source_cap_bytes=64MB;chunk_bytes=1MB;N1_remains_incomplete=$true;real_replays=0;owner_continuation='ACTIVE'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($result | ConvertTo-Json),$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse;Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring($out.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$result | ConvertTo-Json
