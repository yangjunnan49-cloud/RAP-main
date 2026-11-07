$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/native_stability_control_20261021'
$target='E:\githouse\RAP-main\docs\maintenance\2026-10-21\native-stability-control-01'
if(Test-Path -LiteralPath $target){throw 'Preserve existing native handoff'}
New-Item -ItemType Directory -Path $target | Out-Null
$agents='E:\githouse\RAP-main\AGENTS.md';$phase='E:\githouse\RAP-main\docs\maintenance\2026-10-21\PHASE_RECORD.md'
Copy-Item -LiteralPath $agents -Destination (Join-Path $target 'AGENTS.before.md');Copy-Item -LiteralPath $phase -Destination (Join-Path $target 'PHASE.before.md')
$entry="Oct21 evening N1 native coarse stability diagnostic ACTIVE after16source/codec/interception/nativeinterface controlsPASS and prospectiveADMISSION. New1800s inclusive scope starts13:30:14.5225411UTC,180sclose reserve,8MiBwork/output,4GiB/RSS/GPU0/original12GiB<=2snonces; originalnative threadpolicy retained. Fixed stages front(oneNEW complete1101scanG06frontend bank),native1/native2(twofreshserialcoarseinstances with exact same newposes+verifiedmapbytes),analysis. No GT/fine graph/RAPcalls/P0qualification or oldsuccessfulcell rerun. Externalwatcher/host owns exact stagePID/PGID/startticks/scriptSHA, immutablelease andblockedwork cleanup. Read docs/maintenance/2026-10-21/native-stability-control-01/ACTIVE_HANDOFF,PROTOCOL,ADMISSION and source_snapshot; full currentC:/Users/AAA/Documents/Codex/2026-10-21/y/outputs/native_stability_control_20261021/supervision/<stage>/runner_owned+worker_owned and receipts. Preparefailure01 reservedPSvariable retained;02rename mechanical beforepreflight/raw,no capreset. Actual29%/ordinarytrue/reset1792606845 at13:37:51UTC NOT exhaustion; owneruntilboundarycontinuationactive. Hiddenstate/causeUNKNOWN evenifrecordedinputsidentical; secondary outputrow-multisetfingerprints only diagnostic copies. OldP0closedFAIL/budgets and allproduction/default/Git/install/outreach/scheduler/goalstatus limits retained; originalresearchunresolved.`r`n`r`n"
$utf8=[Text.UTF8Encoding]::new($false);$old=[IO.File]::ReadAllBytes($agents);$first=[Array]::IndexOf($old,[byte]10);$split=[Array]::IndexOf($old,[byte]10,$first+1)+1
$add=$utf8.GetBytes($entry);$new=New-Object byte[] ($old.Length+$add.Length)
[Array]::Copy($old,0,$new,0,$split);[Array]::Copy($add,0,$new,$split,$add.Length);[Array]::Copy($old,$split,$new,$split+$add.Length,$old.Length-$split)
[IO.File]::WriteAllBytes($agents,$new);[IO.File]::AppendAllText($phase,"`r`n### Oct21 N1 fixed-input native diagnostic active`r`n`r`n"+$entry,$utf8)
foreach($name in @('ACTIVE_HANDOFF.md','PROTOCOL.md','ADMISSION.json','PREFLIGHT.json','INPUT_BINDINGS.json','RUNTIME_BINDING.json','PREP_FAILURE01.json')){Copy-Item -LiteralPath (Join-Path $out $name) -Destination $target}
Copy-Item -LiteralPath $PSScriptRoot -Destination (Join-Path $target 'source_snapshot') -Recurse
