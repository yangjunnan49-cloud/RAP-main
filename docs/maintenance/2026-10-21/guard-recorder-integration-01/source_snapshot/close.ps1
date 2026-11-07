$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/guard_recorder_integration_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$freeze=Get-Content -Raw (Join-Path $out 'run01/SOURCE_FREEZE.json') | ConvertFrom-Json
$changed=@($freeze.files.PSObject.Properties | Where-Object {(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $_.Name)).Hash -ne $_.Value})
if($changed.Count -ne 0){throw 'Frozen source changed'}
$all=@(& wsl -d Ubuntu-24.04 -u root -- /bin/ps -eo pid,pgid,args)
if($LASTEXITCODE -ne 0){throw 'Process snapshot failed'}
$matches=@($all | Where-Object {$_ -match 'guard_recorder_integration_01/(lease_runner|worker|grandchild)\.py'})
if($matches.Count -ne 0){throw 'Scoped integration process remains'}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\guard-recorder-integration-01'
if(Test-Path -LiteralPath $target){throw 'Preserve previous handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md')
Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 evening guard/recorder integration COMPLETE under distinct900s scope. Nine run01 controls PASS, no repair/retry; 8workers*15stub assertions=120, source mismatch launches0workers, 10frozenfiles unchanged. External Linux watcher protects blocking worker+grandchild; observerloss stop2.112962903s after lastvalidlease, both exitreceipts present. Host/Linux deadline, badnonce, injectedheadroom, RSSfault, forgedidentity+correctcleanup pass. 0scoped livehelper matches; no OScontainment or transientpeak guarantee. Workerrecorded peak84234240bytes belongs intentional64MiBallocation/32MiBfaultgate; ordinary~17MiB, watcher<=16789504bytes. Original12GiB fresh<=2snonces/GPU0 and immutablefiles retained. Recorder wrapper preserves tested argument/return/exceptionidentity and bytes/callorder; pre-capture error aborts before call. Allstdlibsynthetic; raw/GT/native numerical imports/solver/predictions0. NOT actualnativeintegration/nonintervention proof, hiddenstateUNKNOWN. Read docs/maintenance/2026-10-21/guard-recorder-integration-01/snapshot/REPORT_CN,PROTOCOL,run01/RESULTS and source_snapshot. Actual11%/ordinarytrue/reset1792606845 last observed is NOT exhaustion; explicitowner continuation ACTIVE. Next decision may define finite native observation scope, but no real payload admitted by this handoff. P0closedFAIL/oldcaps/default/Git/install/outreach/scheduler/goalstatus limits retained; original research unresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 external watchdog / recorder synthetic integration`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$result=@{closed=$true;elapsed_seconds=$elapsed;cap_seconds=900;budget_compliant=($elapsed -lt 900);cases=9;stub_assertions=120;source_files=@($freeze.files.PSObject.Properties).Count;changed_source_count=$changed.Count;scoped_live_matches=$matches.Count;raw_reads=0;GT_reads=0;native_numerical_imports=0;new_predictions=0;current_continuation='ACTIVE';OS_isolation_certified=$false}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($result | ConvertTo-Json),$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring($out.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$result | ConvertTo-Json
