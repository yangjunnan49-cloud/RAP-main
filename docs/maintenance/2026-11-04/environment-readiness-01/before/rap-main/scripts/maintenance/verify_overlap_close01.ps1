$ErrorActionPreference='Stop'
$taskWatch=[Diagnostics.Stopwatch]::StartNew()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-21/runtime-overlap-01'
$taskEncoding=[Text.UTF8Encoding]::new($false)
function Hash-Path([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Hash-Bytes([byte[]]$Bytes){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()}
function Save-Record([string]$Name,$Value){
    $taskPath=Join-Path $taskBase $Name
    if(Test-Path -LiteralPath $taskPath){throw "Preserve existing verification: $Name"}
    [IO.File]::WriteAllText($taskPath,($Value|ConvertTo-Json -Depth 20)+"`n",$taskEncoding)
}
$taskSeal=Get-Content -LiteralPath (Join-Path $taskBase 'CLOSE_DELIVERY_SEAL.json') -Raw|ConvertFrom-Json
$taskCount=0
foreach($taskProperty in $taskSeal.files.PSObject.Properties){
    $taskPath=Join-Path $taskBase $taskProperty.Name
    if((Hash-Path $taskPath) -ne $taskProperty.Value){throw "Close seal file mismatch: $taskPath"};$taskCount++
}
$taskSourceCount=0
foreach($taskProperty in $taskSeal.source_helpers.PSObject.Properties){
    if((Hash-Path $taskProperty.Name) -ne $taskProperty.Value){throw "Helper source mismatch: $($taskProperty.Name)"};$taskSourceCount++
}
foreach($taskProperty in $taskSeal.handoff_files.PSObject.Properties){if((Hash-Path $taskProperty.Name) -ne $taskProperty.Value){throw 'Handoff file mismatch'}}
$taskStatus=Get-Content -LiteralPath (Join-Path $taskBase 'STATUS.json') -Raw|ConvertFrom-Json
$taskCosts=Get-Content -LiteralPath (Join-Path $taskBase 'COSTS_FINAL.json') -Raw|ConvertFrom-Json
$taskCapture=Get-Content -LiteralPath (Join-Path $taskBase 'CAPTURE_CHECKS.json') -Raw|ConvertFrom-Json
$taskZip=Get-Content -LiteralPath (Join-Path $taskBase 'ZIP_CHECKS.json') -Raw|ConvertFrom-Json
$taskOwned=Get-Content -LiteralPath (Join-Path $taskBase 'OWNED_PROCESS_CLOSE_CHECK.json') -Raw|ConvertFrom-Json
if($taskStatus.round_closure -ne 'COMPLETE' -or $taskStatus.scientific_status -ne 'RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED'){throw 'Status mismatch'}
if($taskCosts.budget_compliant -ne $false -or [Math]::Abs($taskCosts.completed_scientific_and_preparatory_stage_seconds-9316.8147729) -gt 0.0000001){throw 'Budget result changed'}
if(-not $taskCapture.passed -or $taskCapture.bank_files -ne 1008 -or $taskCapture.successful_cells -ne 72 -or $taskCapture.frame_occurrences -ne 147552){throw 'Capture summary mismatch'}
if(-not $taskZip.passed -or $taskZip.members -ne 1031 -or (Hash-Path (Join-Path $taskBase $taskZip.archive)) -ne $taskZip.sha256){throw 'Archive changed after independent member verification'}
if(-not $taskOwned.passed -or $taskOwned.original_controller_alive -or $taskOwned.scoped_live_matches.Count){throw 'Owned process closure mismatch'}
foreach($taskPath in $taskStatus.pending_helpers_not_launched){if(Test-Path -LiteralPath (Join-Path $taskBase $taskPath)){throw 'Pending numeric stage unexpectedly exists'}}
$taskProof=Get-Content -LiteralPath (Join-Path $taskBase 'AGENTS_UPDATE_PROOF.json') -Raw|ConvertFrom-Json
$taskNew=[IO.File]::ReadAllBytes($taskProof.path);$taskLF=[Array]::IndexOf($taskNew,[byte]10)
$taskOld=[byte[]]::new([int]$taskProof.old_bytes)
[Array]::Copy($taskNew,0,$taskOld,0,$taskLF+1)
[Array]::Copy($taskNew,$taskLF+1+[int]$taskProof.inserted_bytes,$taskOld,$taskLF+1,$taskOld.Length-$taskLF-1)
if((Hash-Bytes $taskOld) -ne $taskProof.old_sha256 -or (Hash-Path $taskProof.path) -ne $taskProof.new_sha256){throw 'AGENTS byte-preserving update proof failed'}
$taskPhaseProof=Get-Content -LiteralPath (Join-Path $taskBase 'PHASE_APPEND_PROOF.json') -Raw|ConvertFrom-Json
$taskPhase=[IO.File]::ReadAllBytes($taskPhaseProof.path);$taskPrefix=[byte[]]::new([int]$taskPhaseProof.original_prefix_bytes)
[Array]::Copy($taskPhase,0,$taskPrefix,0,$taskPrefix.Length)
if((Hash-Bytes $taskPrefix) -ne $taskPhaseProof.old_sha256 -or (Hash-Path $taskPhaseProof.path) -ne $taskPhaseProof.new_sha256){throw 'PHASE historical prefix proof failed'}
$taskS1Seal=Join-Path $taskRoot 'docs/maintenance/2026-10-20/raw-input-contract-01/CLOSE_DELIVERY_SEAL.json'
if((Hash-Path $taskS1Seal) -ne '7176381cdfad92ba5d7ebe34f8b86721a6cc0ba5f050b1a78fce7863ff828383'){throw 'Original S1 seal changed'}
$taskDossier=[long](Get-ChildItem -LiteralPath $taskBase -File -Recurse|Measure-Object Length -Sum).Sum
if($taskDossier -gt 256MB){throw 'Final dossier size cap'}
Save-Record 'NATIVE_CLOSE_CHECKS.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');passed=$true;scope='Independent native Windows closure verification; no numeric array/GT decode';sealed_files_rehashed=$taskCount;helper_sources_rehashed=$taskSourceCount;handoff_files_rehashed=2;archive_SHA_still_matches_member_verified_archive=$true;bank_file_count=1008;successful_cells=72;frame_occurrences=147552;source_binding_references_previously_checked=33;ZIP_members_previously_independently_verified=1031;AGENTS_original_bytes_reconstructed_and_match=$true;PHASE_original_prefix_reconstructed_and_match=$true;S1_original_close_seal_unchanged=$true;pending_numerical_stage_paths_absent=$true;original_owned_controller_exited=$true;scoped_process_matches_at_owned_check=0;dossier_bytes_at_native_check=$taskDossier;size_cap_bytes=256MB;scientific_budget_compliant=$false;no_scientific_qualification_implied=$true;close_seal_sha256=Hash-Path (Join-Path $taskBase 'CLOSE_DELIVERY_SEAL.json');verification_script_sha256=Hash-Path $PSCommandPath;additional_documentary_seconds_to_snapshot=$taskWatch.Elapsed.TotalSeconds;later_envelope_writes_additional=$true;finalization_host_command_seconds=2.928655;finalization_host_seconds_overlap_internal_receipt=$true})
$taskEnvelope=[ordered]@{}
foreach($taskName in @('CLOSE_DELIVERY_SEAL.json','NATIVE_CLOSE_CHECKS.json')){$taskEnvelope[$taskName]=Hash-Path (Join-Path $taskBase $taskName)}
Save-Record 'CLOSE_CHECK_SEAL.json' ([ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');files=$taskEnvelope;verification_script_path=$PSCommandPath;verification_script_sha256=Hash-Path $PSCommandPath;documentary_closure='COMPLETE';scientific_status='RAW_COMPLETE_UNVALIDATED_CAP_EXCEEDED';automatic_continuation=$false;whole_session_exact_cost='UNKNOWN; lower bounds and individual receipts retained, budgetFAIL established'})
[ordered]@{native_close_checks='PASS';files=$taskCount;helper_sources=$taskSourceCount;handoff_files=2;archive_members=1031;dossier_bytes=$taskDossier;scientific_status=$taskStatus.scientific_status;elapsed_seconds=$taskWatch.Elapsed.TotalSeconds}|ConvertTo-Json
