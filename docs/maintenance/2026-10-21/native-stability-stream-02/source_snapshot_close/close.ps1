$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_stream_20261021'
$origin=Get-Content -Raw (Join-Path $PSScriptRoot 'origin.json') | ConvertFrom-Json
$result=Get-Content -Raw (Join-Path $out 'RESULTS.json') | ConvertFrom-Json
if(-not $result.complete -or -not $result.same_packet_bytes){throw 'Incomplete native pair'}
$freeze=Get-Content -Raw (Join-Path $out 'supervision/SOURCE_FREEZE.json') | ConvertFrom-Json
foreach($file in $freeze.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.Name)).Hash -ne $file.Value){throw 'Frozen N2 source changed'}}
$inputRoot=Join-Path $root 'outputs/native_stability_control_20261021'
foreach($file in $freeze.readonly_N1_inputs.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $inputRoot $file.Name)).Hash -ne $file.Value){throw 'Read-only N1 input/status changed'}}
$pair=Get-Content -Raw (Join-Path $out 'PAIRED_SEAL.json') | ConvertFrom-Json
foreach($file in $pair.files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $out ('supervision/'+$file.Name))).Hash -ne $file.Value){throw 'Sealed native product changed'}}
$all=@(& wsl -d Ubuntu-24.04 -u root -- /bin/ps -eo pid,pgid,args)
if($LASTEXITCODE -ne 0){throw 'Scoped process snapshot failed'}
$matches=@($all | Where-Object {$_ -match 'native_stability_stream_02/(lease_runner|native_stage)\.py'})
if($matches.Count -ne 0){throw 'Owned N2 helper remains'}
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\native-stability-stream-02'
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.active.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.active.before.md')
$entry="Oct21 N2 COMPLETE twofreshserialcoarseG06controls/2202frames, same sealednewfrontend+allmapbytes,24830eventchainsverified. First6340events contentidentical; firstdifference frame564/event6340 ICPafter(transform+inlier_rmse,fitnesssame), identicalrecorded source/targetpoints+normals/initialguess/threshold/criteria.20differentevents; finalcoarse translationelementmax2.7066136674136487e-6m(~2.71um),rotationentry1.4181037163996102e-8; resetlists11/closureendpoints5same. HiddennativecauseUNKNOWN; no secondarymultiset meansnoorder/value attribution. DoesNOTexplainhistorical4.31mm magnitude orqualifyP0. N1incomplete16MiBstop/925.7894816s unchanged, successfulfrontendnotregenerated. N2new1800sinclusivefromconservative13:47:49UTC/14MiB,source64MiB/hashscratch16MiB/chunk<=1MiB; original4GiB/12GiB<=2snonce/GPU0/config/autothreads and64MiB/256MiB retained.17source/interface+21synthetichashcontrolsPASS; gzipstorage,no realsort/pairconcat,upstreamvoxelcapture. NoGT/finegraph/RAP/newmodel.2coarseLiDARtexttrajectoriesZIP/2202exactfloat64roundtripsPASS. Read native-stability-stream-02/REPORT_CN,RESULTS,FIRST_ICP_EVIDENCE,COSTS_FINAL and fullC outputs.0scopedlivehelpers andN1readonly/source/pairsealsunchanged. Actual63%/ordinarytrue/reset1792606845 lastobserved NOTexhaustion; ownercontinuationACTIVE. Next read-only decision is verifyoriginalC0runbook/latestcompletion/source/budget givenreal12GiBguardnowpasses; doNOTrepeatalreadycompletedstages/newmodels/training orretiredfamilies. OldP0FAIL/budgets/production/default/Git/install/outreach/scheduler/goalstatuslimits retained; originalresearchunresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 N2 complete, first visible ICP difference`r`n`r`n"+$entry,$utf8)
$elapsed=[Math]::Max(([DateTimeOffset]::UtcNow-[DateTimeOffset]$origin.start_utc).TotalSeconds,([Diagnostics.Stopwatch]::GetTimestamp()-[double]$origin.start_ticks)/[double]$origin.frequency)
$bytes=[long](Get-ChildItem -LiteralPath $out -File -Recurse | Measure-Object Length -Sum).Sum+[long](Get-ChildItem -LiteralPath $PSScriptRoot -File -Recurse | Measure-Object Length -Sum).Sum
$cost=@{status='CLOSED_COMPLETE_NATIVE_DIAGNOSTIC';elapsed_seconds=$elapsed;cap_seconds=1800;budget_compliant=($elapsed -lt 1800);work_output_bytes_at_close=$bytes;growth_cap_bytes=14MB;growth_compliant=($bytes -lt 14MB);native_frame_calls=2202;event_rows=24830;first_difference_frame=564;hidden_cause='UNKNOWN';N1_remains_incomplete=$true;fresh_frontend_regenerations=0;raw_frame_reads=2202;GT_reads=0;fine_graph_calls=0;new_RAP_calls=0;scoped_live_matches=0;owner_continuation='ACTIVE';P0_qualification='CLOSED_FAIL_RETAINED'}
[IO.File]::WriteAllText((Join-Path $out 'COSTS_FINAL.json'),($cost | ConvertTo-Json -Depth 4),$utf8)
foreach($name in @('REPORT_CN.md','COSTS_FINAL.json','RESULTS.json','FIRST_ICP_EVIDENCE.json','PAIRED_SEAL.json','EXPORT_CHECKS.json')){Copy-Item -LiteralPath (Join-Path $out $name) -Destination $target}
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot_close') -Recurse
$seal=Get-ChildItem -LiteralPath $out -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring($out.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}}
[IO.File]::WriteAllText((Join-Path $out 'DELIVERY_SEAL.json'),($seal | ConvertTo-Json -Depth 4),$utf8)
$cost | ConvertTo-Json
