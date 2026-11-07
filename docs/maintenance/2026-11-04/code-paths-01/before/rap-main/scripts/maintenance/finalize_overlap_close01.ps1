$ErrorActionPreference='Stop'
$taskWatch=[Diagnostics.Stopwatch]::StartNew()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-21/runtime-overlap-01'
$taskEncoding=[Text.UTF8Encoding]::new($false)
function Save-Record([string]$Name,$Value){
    $taskPath=Join-Path $taskBase $Name
    if(Test-Path -LiteralPath $taskPath){throw "Do not overwrite: $Name"}
    [IO.File]::WriteAllText($taskPath,($Value|ConvertTo-Json -Depth 30)+"`n",$taskEncoding)
}
function Hash-Path([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Hash-Bytes([byte[]]$Bytes){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()}
$taskStatus=Get-Content -LiteralPath (Join-Path $taskBase 'STATUS.json') -Raw|ConvertFrom-Json
$taskProc=Get-Content -LiteralPath (Join-Path $taskBase 'OWNED_PROCESS_CLOSE_CHECK.json') -Raw|ConvertFrom-Json
if($taskStatus.scientific_status -ne 'RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED' -or -not $taskProc.passed){throw 'Closure prerequisites'}
Save-Record 'DOCUMENTARY_HOST_RECEIPTS.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');provenance='Observed exec_command wall_time_seconds; no clock reconstruction';close_capture_host_wall_seconds=2.9865963;owned_process_check_host_wall_seconds=2.7527766;these_overlap_corresponding_script_receipts=$true;sum_them_once_per_documentary_command=$true;earlier_readonly_command_and_finalization_costs_additional=$true;not_an_exact_whole_session_cost=$true})
$taskAgents=Join-Path $taskRoot 'AGENTS.md'
$taskOld=[IO.File]::ReadAllBytes($taskAgents)
$taskLF=[Array]::IndexOf($taskOld,[byte]10)
if($taskLF -lt 0){throw 'AGENTS header missing'}
$taskEntry=@'

Oct21 FINAL ROUND CLOSED after latest owner finish-and-record instruction: S1 validated raw-core delivery remains COMPLETE (36 cells, meanG/KATE0.648334140963/0.698991712360m,ter0.446953334008/0.478490321918%; individual07ter/10rer FAIL, no newRAPincrement/default promotion). P0 queue4 overlap rawcapture72/72cells/147552frames COMPLETE and sealed, but scientific validation INCOMPLETE: original max-receipt9000s account actually9316.8147729s BEFORE extra documentary closure, budgetFAIL. run02 Windows9082.9120766 vs Linuxwrapper8763.286421554993; discrepancycauseUNKNOWN, Linux-onlylive deadline failed to enforce max-clockrule. Originalsources/receipts and failedmetadataNameError216.3564823s retained, no capreset/borrow/replay. No independent packet/source/graph audit, paired-equivalence, newGTmetrics or speedupqualification run. NativeWindows1008bankhashes/33sourcebindings and1031ZIPmembers PASS; oldS1close unchanged. Actualprimary100%/ordinaryfalse/reset1792563859 observedfollowing04:09:41UTC; latestownerinstruction onlyfinishescurrentround, no reset/newcandidate/automaticresume. Exactownedcontroller exited/0scopedprocessmatches. Read docs/maintenance/2026-10-21/runtime-overlap-01/START_HERE.md,REPORT,CURRENT_HANDOFF,BUDGET_GUARD_INCIDENT,COSTS_FINAL,CAPTURE_CHECKS,ZIP_CHECKS,CLOSE_DELIVERY_SEAL and October21 PHASE_RECORD. Pendinghelpers remainunexecuted; nextneeds explicitboundedvalidation/clockguarddecision, no automaticlaunch. Originalresearchobjective unresolved; alloldstops/seals/outreachdecline/default/install/production/model/reference/Git/scheduler/goalstatuslimits unchanged. Earlier ACTIVE paragraphs below are historical.

'@
$taskInsert=$taskEncoding.GetBytes($taskEntry.Replace("`r`n","`n"))
$taskNew=[byte[]]::new($taskOld.Length+$taskInsert.Length)
[Array]::Copy($taskOld,0,$taskNew,0,$taskLF+1)
[Array]::Copy($taskInsert,0,$taskNew,$taskLF+1,$taskInsert.Length)
[Array]::Copy($taskOld,$taskLF+1,$taskNew,$taskLF+1+$taskInsert.Length,$taskOld.Length-$taskLF-1)
[IO.File]::WriteAllBytes($taskAgents,$taskNew)
$taskRestored=[byte[]]::new($taskOld.Length)
[Array]::Copy($taskNew,0,$taskRestored,0,$taskLF+1)
[Array]::Copy($taskNew,$taskLF+1+$taskInsert.Length,$taskRestored,$taskLF+1,$taskOld.Length-$taskLF-1)
if((Hash-Bytes $taskOld) -ne (Hash-Bytes $taskRestored)){throw 'AGENTS original bytes not preserved'}
Save-Record 'AGENTS_UPDATE_PROOF.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');path=$taskAgents;old_sha256=Hash-Bytes $taskOld;new_sha256=Hash-Path $taskAgents;old_bytes=$taskOld.Length;inserted_bytes=$taskInsert.Length;original_all_bytes_preserved_by_insertion_after_header=$true;reconstructed_old_sha256=Hash-Bytes $taskRestored})
$taskPhase=Join-Path $taskRoot 'docs/maintenance/2026-10-21/PHASE_RECORD.md'
$taskPhaseOld=[IO.File]::ReadAllBytes($taskPhase)
$taskPhaseEntry=@'

## Final round close — October21, explicit finish/update instruction

Latest owner request: 继续完成本轮任务，并且在结束后做好更新和记录. Actual100%/ordinaryUsageAllowed=false/reset1792563859 had been observed atfollowing04:09:41UTC; this later instruction authorized only current-round finish/closure and documentation, no quota/cap reset/new candidate.

P0 raw run02 completed all72 G/K × S/P × six-sequence × three-repeat cells,147552 frame occurrences. ALL72 bankseal predates any new GT or paired-equivalence read. NativeWindows1008 sealed file identities/exact member set,33source references and1031ZIP members PASS. raw_capture_72cells_PENDING_20261021.zip is an exact-byte unvalidated research capture, not a validated text-pose/system delivery. FirstmetadataNameError failure216.3564823s and binding02 mechanical import repair remain inoriginalbank/supervision and source freezes.

Important budget incident: frozen per-stage MAX(Windows/Linux/wrapper) gives9316.8147729s before added documentary closure, above original9000s. RawWindows9082.9120766s versusLinuxwrapper8763.286421554993s; differencecauseUNKNOWN. Linux-only live timeout did not enforce the larger host-clock duration. Originalprotocol/receipts unchanged, budgetFAIL, no newcap/borrow. Prepared independentaudit/GT/paired-equivalence/runtimequalification/report helpers NOT RUN. P0 scientificstatus RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED; documentaryclosure COMPLETE. Exactowned processcheck findsoriginalcontroller exited/0scopedmatches, no processcontrol/other-taskabsenceclaim. No automaticresume.

S1 remains COMPLETE DELIVERED: all36 fresh-raw-core cells; G/K meansATE0.648334140963/0.698991712360m,ter0.446953334008/0.478490321918%; primaryaveragepasses, individual07ter/10rerFAIL, GATEworse06/07/10,00ternot everyrepeatbetter. G11.391FPS/K27.092, no stableonline10Hz/newRAPincrement/fullnativeCLIclaim. OriginalS1closure hash7176381cdfad92ba5d7ebe34f8b86721a6cc0ba5f050b1a78fce7863ff828383 matches; original6762.0941485/7200s cost unchanged, no borrowedbalance.

Updated AGENTS top byte-preserving insertion and appended historical records. Currententry runtime-overlap-01/START_HERE.md; REPORT.md/CURRENT_HANDOFF.md/STATUS.json/INCOMPLETE.md/BUDGET_GUARD_INCIDENT.md/COSTS_FINAL.json/CAPTURE_CHECKS.json/ZIP_CHECKS.json/CLOSE_DELIVERY_SEAL.json govern finalstate. Future would first need explicit finitevalidation/clockguard scope and originalstrongcontrols; nothing launched/scheduled. Originalresearchobjective unresolved, alloldstops/seals/outreachdecline/default/install/production/model/reference/Git/scheduler/goalstatus limits preserved.
'@
[IO.File]::AppendAllText($taskPhase,$taskPhaseEntry.Replace("`r`n","`n")+"`n",$taskEncoding)
$taskPhaseNew=[IO.File]::ReadAllBytes($taskPhase);$taskPhasePrefix=[byte[]]::new($taskPhaseOld.Length)
[Array]::Copy($taskPhaseNew,0,$taskPhasePrefix,0,$taskPhaseOld.Length)
if((Hash-Bytes $taskPhaseOld) -ne (Hash-Bytes $taskPhasePrefix)){throw 'PHASE history changed'}
Save-Record 'PHASE_APPEND_PROOF.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');path=$taskPhase;old_sha256=Hash-Bytes $taskPhaseOld;new_sha256=Hash-Path $taskPhase;original_prefix_bytes=$taskPhaseOld.Length;original_prefix_preserved=$true})
[IO.File]::AppendAllText((Join-Path $taskBase 'ACTIVE_HANDOFF.md'),@'

## FINAL CLOSE — supersedes every live paragraph above

run02 exited0/all72 raw cells sealed. STATUS=RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED: originalmax-clock9000s account9316.8147729s before documentaryclose, budgetFAIL. No pendingnumeric audit/GT/assessment helper launched. Raw1008SHA/33sourcebindings/1031ZIPmembers integrity PASS; ownedexactprocesscheck originalcontroller gone/0scopedmatches. Finalentry START_HERE.md/REPORT.md/CURRENT_HANDOFF.md and BUDGET_GUARD_INCIDENT/COSTS_FINAL/CLOSE_DELIVERY_SEAL. Latest ownerfinishrecords instruction afteractual100%/ordinaryfalse handled by current-roundclosureonly; no newcandidate/capreset/automaticresume. Originalresearchgoal unresolved/limits unchanged. Earlier active instructions are historical, not an instruction to resume.
'@,$taskEncoding)
$taskCostPath=Join-Path $taskBase 'COSTS_FINAL.json'
Copy-Item -LiteralPath $taskCostPath -Destination (Join-Path $taskBase 'COSTS_INITIAL_CLOSE_SNAPSHOT.json')
$taskCost=Get-Content -LiteralPath $taskCostPath -Raw|ConvertFrom-Json -AsHashtable
$taskCost['finalization_utc']=[DateTimeOffset]::UtcNow.ToString('o')
$taskCost['documentary_host_commands_seconds']=2.9865963+2.7527766
$taskCost['final_documentary_stage_seconds_observed_to_snapshot']=$taskWatch.Elapsed.TotalSeconds
$taskCost['accounted_total_lower_bound_seconds']=[double]$taskCost.completed_scientific_and_preparatory_stage_seconds+2.9865963+2.7527766+$taskWatch.Elapsed.TotalSeconds
$taskCost['later_native_verification_and_documentary_writes_are_additional']=$true
[IO.File]::WriteAllText($taskCostPath,($taskCost|ConvertTo-Json -Depth 30)+"`n",$taskEncoding)
Save-Record 'FINAL_DOCUMENTARY_RECEIPT.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');wall_seconds_observed_before_seal=$taskWatch.Elapsed.TotalSeconds;script_sha256=Hash-Path $PSCommandPath;all_pending_science_still_not_run=$true;old_caps_not_reset=$true;later_seal_and_native_verification_seconds_additional=$true;AGENTS_and_PHASE_history_preserved=$true})
$taskFiles=[ordered]@{}
foreach($taskFile in Get-ChildItem -LiteralPath $taskBase -File -Recurse|Sort-Object FullName){$taskFiles[[IO.Path]::GetRelativePath($taskBase,$taskFile.FullName).Replace('\','/')]=Hash-Path $taskFile.FullName}
$taskHelpers=[ordered]@{}
foreach($taskFile in Get-ChildItem -LiteralPath (Join-Path $taskRoot 'scripts/maintenance') -File|Where-Object {$_.Name -match 'overlap' -or $_.Name -eq 'invoke_raw_guard06.ps1'}|Sort-Object Name){$taskHelpers[$taskFile.FullName]=Hash-Path $taskFile.FullName}
$taskHandoff=[ordered]@{};$taskHandoff[$taskAgents]=Hash-Path $taskAgents;$taskHandoff[$taskPhase]=Hash-Path $taskPhase
$taskSize=[long](Get-ChildItem -LiteralPath $taskBase -File -Recurse|Measure-Object Length -Sum).Sum
if($taskSize -gt 256MB){throw 'Dossier cap exceeded during close'}
Save-Record 'CLOSE_DELIVERY_SEAL.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');scope='P0 documentary closure; raw capture integrity only, no scientific qualification';status='RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED';files=$taskFiles;source_helpers=$taskHelpers;handoff_files=$taskHandoff;dossier_bytes_before_this_seal=$taskSize;original_dossier_cap_bytes=256MB;scientific_budget_compliant=$false;no_new_numeric_validation=$true;original_sources_failures_receipts_retained=$true;extra_native_check_envelope='CLOSE_CHECK_SEAL.json'})
[ordered]@{closure='COMPLETE';scientific_status=$taskStatus.scientific_status;sealed_files=$taskFiles.Count;helper_sources=$taskHelpers.Count;handoff_files=$taskHandoff.Count;AGENTS_original_bytes_preserved=$true;phase_original_prefix_preserved=$true;elapsed_seconds=$taskWatch.Elapsed.TotalSeconds}|ConvertTo-Json
