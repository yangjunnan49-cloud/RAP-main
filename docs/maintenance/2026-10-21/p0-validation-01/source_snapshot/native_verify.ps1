$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskOut=Join-Path (Split-Path (Split-Path $taskRoot -Parent) -Parent) 'outputs\overlap_validation_20261021'
$taskOriginal='E:\githouse\RAP-main\docs\maintenance\2026-10-21\runtime-overlap-01'
$taskStart=[Diagnostics.Stopwatch]::GetTimestamp()
$taskSeal=Get-Content -Raw -LiteralPath (Join-Path $taskOriginal 'CLOSE_DELIVERY_SEAL.json')|ConvertFrom-Json
$taskCount=0
foreach($taskProperty in $taskSeal.files.PSObject.Properties){
    if((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskOriginal $taskProperty.Name)).Hash -ne $taskProperty.Value){throw ('Original sealed file changed: '+$taskProperty.Name)}
    $taskCount++
}
$taskSources=0
foreach($taskProperty in $taskSeal.source_helpers.PSObject.Properties){if((Get-FileHash -Algorithm SHA256 -LiteralPath $taskProperty.Name).Hash -ne $taskProperty.Value){throw ('Original helper changed: '+$taskProperty.Name)};$taskSources++}
$taskHandoffs=0
foreach($taskProperty in $taskSeal.handoff_files.PSObject.Properties){if((Get-FileHash -Algorithm SHA256 -LiteralPath $taskProperty.Name).Hash -ne $taskProperty.Value){throw ('Preupdate handoff changed: '+$taskProperty.Name)};$taskHandoffs++}
$taskNewFreeze=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'SOURCE_FREEZE.json')|ConvertFrom-Json
foreach($taskProperty in $taskNewFreeze.files.PSObject.Properties){
    $taskPath=$taskProperty.Name.Replace('/mnt/e/','E:/').Replace('/mnt/c/','C:/')
    if((Get-FileHash -Algorithm SHA256 -LiteralPath $taskPath).Hash -ne $taskProperty.Value){throw ('Validation source changed: '+$taskPath)}
}
$taskZipCheck=Get-Content -Raw -LiteralPath (Join-Path $taskOut 'TRAJECTORY_ZIP_CHECKS.json')|ConvertFrom-Json
$taskZip=[IO.Compression.ZipFile]::OpenRead((Join-Path $taskOut 'validated_72_trajectories_20261021.zip'))
$taskZipCount=0
try{
    if($taskZip.Entries.Count -ne $taskZipCheck.members){throw 'ZIP count mismatch'}
    foreach($taskEntry in $taskZip.Entries){
        $taskStream=$taskEntry.Open();$taskSHA=[Security.Cryptography.SHA256]::Create()
        try{$taskHash=[Convert]::ToHexString($taskSHA.ComputeHash($taskStream)).ToLowerInvariant()}finally{$taskStream.Dispose();$taskSHA.Dispose()}
        if($taskHash -ne $taskZipCheck.member_sha256.($taskEntry.FullName)){throw ('ZIP member changed: '+$taskEntry.FullName)}
        $taskZipCount++
    }
}finally{$taskZip.Dispose()}
$taskOriginalBytes=(Get-ChildItem -LiteralPath $taskOriginal -Recurse -File|Measure-Object Length -Sum).Sum
$taskNewBytes=0
foreach($taskDirectory in @($taskRoot,$taskOut)){$taskNewBytes+=(Get-ChildItem -LiteralPath $taskDirectory -Recurse -File|Measure-Object Length -Sum).Sum}
if($taskNewBytes -gt 64MB -or $taskOriginalBytes+$taskNewBytes+1MB -gt 256MB){throw 'Combined dossier cap'}
$taskOrigin=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'budget_origin.json')|ConvertFrom-Json
$taskMono=([Diagnostics.Stopwatch]::GetTimestamp()-$taskOrigin.initialization_ticks)/$taskOrigin.frequency+$taskOrigin.conservative_prelude_seconds
$taskWall=([DateTimeOffset]::UtcNow-[DateTimeOffset]$taskOrigin.start_utc).TotalSeconds
$taskElapsed=[Math]::Max($taskMono,$taskWall)
if($taskElapsed -ge 1200){throw 'Whole validation budget exceeded'}
$taskResult=[ordered]@{passed=$true;original_sealed_files_rehashed=$taskCount;original_helpers_rehashed=$taskSources;original_handoffs_before_update=$taskHandoffs;new_SOURCE_FREEZE_matches=$true;native_zip_members=$taskZipCount;original_dossier_bytes=$taskOriginalBytes;all_new_work_output_bytes=$taskNewBytes;combined_dossier_bytes=($taskOriginalBytes+$taskNewBytes);global_elapsed_seconds=$taskElapsed;cap_seconds=1200;original_P0_budget_compliant=$false;G_candidate_qualified=$false;K_candidate_qualified=$false;whole_native_tree_peak='UNKNOWN';native_verification_seconds=([Diagnostics.Stopwatch]::GetTimestamp()-$taskStart)/[Diagnostics.Stopwatch]::Frequency}
[IO.File]::WriteAllText((Join-Path $taskOut 'NATIVE_CHECKS.json'),($taskResult|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$taskResult|ConvertTo-Json -Depth 5
