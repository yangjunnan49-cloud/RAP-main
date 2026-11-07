$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$out=Join-Path $root 'outputs/native_stability_stream_20261021'
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\native-stability-stream-02'
if(Test-Path -LiteralPath $target){throw 'Preserve prior N2 handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 N2 streaming-observer native diagnostic ACTIVE after17source/interface probesPASS and freshADMISSION. N1 remainsINCOMPLETE16MiBstop/925.7894816s, frontendbank sealed/read-only/no regeneration. New1800s conservative13:47:49UTC origin/180sclose reserve/14MiBworkoutput; exactchunkSHA supports64MiBsource with<=1MiBchunks/16MiBhashscratch, no realmultisetsort/pointnormalconcat; gzip storage+upstream nativevoxeldownsample capture. Original4GiB/12GiB<=2snonce/GPU0/threads/config and64MiB/256MiB dossier retained; twofreshserial1101-framecoarseworkers only, noGT/finegraph/RAP/P0qualification. Native1COMPLETE; native2thenanalysis aftersuccess. Source/runtime/N1bankseal match,17probes+21synthetichashcontrols prerequisites. AnyN2failure endsrealnativebranchthiswindow,no capacityescalation retry. Read native-stability-stream-02/ACTIVE_HANDOFF,PROTOCOL,ADMISSION andC:/Users/AAA/Documents/Codex/2026-10-21/y/outputs/native_stability_stream_20261021/supervision/<stage> exactrunner+workerownership. Hiddenstate/causeUNKNOWN. Actual55%/ordinarytrue/reset1792606845 at13:52:14UTC notexhaustion; ownercontinuationACTIVE. Oldfailures/budgets/production/default/Git/install/outreach/scheduler/goalstatus limits retained, originalresearchunresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 N2 streaming observation active`r`n`r`n"+$entry,$utf8)
foreach($name in @('ACTIVE_HANDOFF.md','PROTOCOL.md','ADMISSION.json','PREFLIGHT.json','INPUT_BINDINGS.json','RUNTIME_BINDING.json','PREPARATION.json')){Copy-Item -LiteralPath (Join-Path $out $name) -Destination $target}
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
