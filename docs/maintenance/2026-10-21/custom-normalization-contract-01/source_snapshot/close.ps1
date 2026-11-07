$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/custom_normalization_contract_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$worker=Get-Content -Raw (Join-Path $out 'run01/normal/worker_exit.json') | ConvertFrom-Json
$runner=Get-Content -Raw (Join-Path $out 'run01/normal/runner_exit.json') | ConvertFrom-Json
if(-not $worker.success -or -not $runner.success -or $worker.count -ne 17 -or $worker.scalar_coordinate_comparisons -ne 9882 -or $worker.normalized_roundtrip_comparisons -ne 1647){throw 'CN1 controls incomplete'}
$freeze=Get-Content -Raw (Join-Path $out 'run01/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'Frozen CN1 source changed'}}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\custom-normalization-contract-01'
if(Test-Path -LiteralPath $target){throw 'Preserve previous CN1 handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 CN1 custom publicnormalization/rigidpredictionrecovery syntheticcontract COMPLETE.17controlsPASS;9882independentDecimal recoverycoords+1647normalizationroundtrips, maxerror/budgetratio0.00008027571865, workerpeak16809984bytes. Publiccenters+singlepositive sharedscale, T_i->r=N_r^-1 A_r^-1 A_i N_i;3views/3scales/2leftgauges/allreferences. Rejectperviewscale/empty/nonfinite/degenerate/nonrigid/reflection/badhomogeneous/missingview withoutfit/projection. Purestdlibmodule has no file/reference API; knownsyntheticoracleA_i only, no actualRAP output/model/dataset/GT/feature/solver. NOTcanonical normalization/batch orauthenticatedRAPtransformsemantics/physicaltruth/efficacy; uninstalled/unintegrated. C0complete22.614594s andalloldstops unchanged. Read custom-normalization-contract-01/snapshot/REPORT_CN and source_snapshot/normalization.py; fullC outputs custom_normalization_contract_20261021/run01.1200s scope conservative14:00:23UTC includesdesign+UTCchargedprelude before firstmonotonicinit, no capreset. Actual88%/ordinarytrue/reset1792606845 lastobserved notexhaustion; owneruntilboundarycontinuationACTIVE. Next substantive prerequisite is source-boundactualRAPinput/outputdirection+externalreference separation, no automaticmodel/efficacy. Originalresearchunresolved/manuscriptpaused/P0closedFAIL; production/default/Git/install/outreach/scheduler/goalstatuslimits retained.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 CN1 conditional custom normalization/recovery contract`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$cost=@{status='CLOSED_SYNTHETIC_CONTRACT_PASS';elapsed_seconds=$elapsed;cap_seconds=1200;budget_compliant=($elapsed -lt 1200);conservative_origin_includes_planning=$true;controls=17;recovery_coordinates=9882;normalized_roundtrips=1647;worker_peak_RSS_bytes=$worker.max_RSS_bytes;actual_RAP_interface_authenticated=$false;canonical_normalization=$false;raw_file_decodes=0;GT_reads=0;model_solver_calls=0;owner_continuation='ACTIVE';original_research_goal='UNRESOLVED'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($cost | ConvertTo-Json),$utf8)
Copy-Item -LiteralPath $out -Destination (Join-Path $target 'snapshot') -Recurse;Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring($out.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$cost | ConvertTo-Json
