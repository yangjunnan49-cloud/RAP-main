$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $taskRoot 'outputs/boundary_contract_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\boundary-contract-01'
if(Test-Path -LiteralPath $target){throw 'Destination must be new'}
New-Item -ItemType Directory -Path $target | Out-Null
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$agents='E:\githouse\RAP-main\AGENTS.md'
$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md')
Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$utf8=[Text.UTF8Encoding]::new($false)
$entry="Oct21 boundary byte-signature contract COMPLETE under distinct300s synthetic-only scope. All21 controls PASS, PythonpeakRSS16011264bytes, no raw/GT/native numerical imports/solver/newpredictions. Dtype/shape/endian/rowbytes and ordered immutable eventchain bound; prepared vs derived input changes separated, tamper/order/duplicate/sourcebinding controls verified. Equal records never certify hidden native state; outputdifference remains causeUNKNOWN and complete-state claims rejected. Prototype NOT integrated into native workload; native capture overhead/nonintervention/state coverage remain untested. Read docs/maintenance/2026-10-21/boundary-contract-01/snapshot/REPORT_CN.md,RESULTS and source_snapshot. P0 remains CLOSED_EQUIVALENCE_FAIL with originalbudgetFAIL; no original cap reset or newRAPincrement. Actual93%/ordinarytrue/reset1792582782 last observed is not exhaustion; authorized owner continuation remains active until actualboundary, no resetresume. Next finite work is delivery-integrity reconciliation and consolidated handoff only; no raw replay/candidate/default/production/Git/install/outreach/scheduler/goalstatus change. Original research objective remains unresolved.`r`n`r`n"
$old=[IO.File]::ReadAllBytes($agents)
$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
if($split -le 1){throw 'Header delimiter missing'}
$added=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$added.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($added,0,$new,$split,$added.Length);[Array]::Copy($old,$split,$new,$split+$added.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new)
[IO.File]::AppendAllText($phase,"`r`n### Oct21 boundary recording contract`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$cost=[ordered]@{status='CLOSED_SYNTHETIC_PASS';elapsed_seconds=$elapsed;cap_seconds=300;budget_compliant=($elapsed -lt 300);all_preparation_execution_documentation_included=$true;controls=21;raw_reads=0;GT_reads=0;new_predictions=0;native_cause='UNKNOWN';not_integrated=$true}
$json=$cost | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),$json,$utf8)
[IO.File]::WriteAllText((Join-Path $target 'COSTS_FINAL.json'),$json,$utf8)
$files=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {[ordered]@{path=$_.FullName.Substring($out.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($files | ConvertTo-Json -Depth 5),$utf8)
$json
