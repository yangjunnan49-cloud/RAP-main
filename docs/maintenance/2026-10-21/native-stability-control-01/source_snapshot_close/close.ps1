$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_control_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$audit=Get-Content -Raw (Join-Path $out 'PARTIAL_AUDIT.json') | ConvertFrom-Json
if(-not $audit.passed -or $audit.native2_started){throw 'Partial audit or stop disposition inconsistent'}
foreach($name in @('SOURCE_FREEZE.json','SOURCE_FREEZE02.json')){
    $freeze=Get-Content -Raw (Join-Path $out ('supervision/'+$name)) | ConvertFrom-Json
    foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw ('Frozen source changed: '+$file.Name)}}
}
$all=@(& wsl -d Ubuntu-24.04 -u root -- /bin/ps -eo pid,pgid,args)
if($LASTEXITCODE -ne 0){throw 'Scoped process check failed'}
$matches=@($all | Where-Object {$_ -match 'native_stability_control_01/(lease_runner02?|native_stage)\.py'})
if($matches.Count -ne 0){throw 'Owned N1 process still present'}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\native-stability-control-01'
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.active.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.active.before.md')
$entry="Oct21 N1 CLOSED INCOMPLETE_ARRAY_CAPTURE_CAP, NOT stability/efficacy result. FreshG06frontend1101frames COMPLETE+sealed; native1stops atframe833 BEFORE detectorquery because841107x3f64=20186568bytes>original16777216singlearraycap. Native2/analysisnotlaunched, no capraise/replay. Partialaudit4364eventchainrows+834packetprefix exactmap/pose hashesPASS; completecoarsecomparison unavailable. NativeworkerOSpeak716955648bytes, watcherobserved651153408<4GiB; old1800s/8MiB scope costscloseunchanged.16preflightcontrolsPASS. Prepare01reservedPSvariable failure retained/repaired02beforedata. Frontwatcher inheritedsynthetic/zero-datafields INVALID; raw+front were real, oldreceiptretained plusclassificationcorrection. Guard02 changesonlyreceiptlabel/identityroutes, numericcodeunchanged. Rawframe reads1101+834, freshfrontregistration1101, partialnativeframecalls834attempted; noGT/finegraph/RAP.0scoped liveN1matches. Read native-stability-control-01/REPORT_CN,PARTIAL_AUDIT,COSTS_FINAL,RECEIPT_CLASSIFICATION_CORRECTION,BINDING02 and fullC outputs. Next permitted work is independently bounded synthetic chunkhash memory/byte-identity feasibility; no automatic realretry or launderingN1aspass. Actual37%/ordinarytrue/reset1792606845 lastobserved NOTexhaustion; ownercontinuationACTIVE. P0closedFAIL/oldcaps/production/default/Git/install/outreach/scheduler/goalstatus limits retained, originalresearchunresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 N1 recording-cap stop, incomplete comparison`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$bytes=[long](Get-ChildItem -LiteralPath $out -File -Recurse | Measure-Object Length -Sum).Sum+[long](Get-ChildItem -LiteralPath $PSScriptRoot -File -Recurse | Measure-Object Length -Sum).Sum
$result=@{status='CLOSED_INCOMPLETE_ARRAY_CAPTURE_CAP';elapsed_seconds=$elapsed;cap_seconds=1800;budget_compliant=($elapsed -lt 1800);work_output_bytes_at_close=$bytes;growth_cap_bytes=8MB;growth_compliant=($bytes -lt 8MB);frontend_frames_complete=1101;native_packet_prefix=834;verified_partial_events=4364;native_comparison_complete=$false;native2_launched=$false;all_failures_and_sources_retained=$true;scoped_live_matches=0;actual_raw_frame_reads=1935;fresh_frontend_registrations=1101;GT_reads=0;fine_graph_calls=0;new_RAP_calls=0;owner_continuation='ACTIVE';P0_qualification='CLOSED_FAIL_RETAINED'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($result | ConvertTo-Json -Depth 4),$utf8)
foreach($name in @('REPORT_CN.md','COSTS_FINAL.json','PARTIAL_AUDIT.json','RECEIPT_CLASSIFICATION_CORRECTION.json','BINDING02.md')){Copy-Item -LiteralPath (Join-Path $out $name) -Destination $target}
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot_close') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring($out.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$result | ConvertTo-Json -Depth 4
