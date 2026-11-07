$ErrorActionPreference='Stop'
$taskStarted=[DateTime]::UtcNow
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs\maintenance\2026-10-20\weekly-system-handoff-01'
$taskRecord=Join-Path $taskBase 'WINDOWS_SUPPLEMENT_CHECKS.json'
if(Test-Path -LiteralPath $taskRecord){throw 'Preserve old supplement verification'}
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
if($taskHeadroom -lt 12GB){throw 'Original launch guard'}
$taskSeal=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'FINAL_SUPPLEMENT_SEAL.json') | ConvertFrom-Json
$taskCount=0
foreach($taskEntry in $taskSeal.files.PSObject.Properties){
    if($taskEntry.Name -notmatch '^/mnt/([a-z])/(.*)$'){throw 'Unexpected source path'}
    $taskPath=$Matches[1].ToUpperInvariant()+':\'+$Matches[2].Replace('/','\')
    if((Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.Value){throw ('Supplement mismatch: '+$taskPath)}
    $taskCount++
}
if((Get-FileHash -LiteralPath (Join-Path $taskBase 'DELIVERY_SEAL.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskSeal.original_delivery_seal_sha256){throw 'Original seal changed'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Read-TaskZipBytes($taskArchive,[string]$taskName){
    $taskEntry=$taskArchive.GetEntry($taskName)
    if($null -eq $taskEntry){throw ('Missing archive member: '+$taskName)}
    $taskStream=$taskEntry.Open();$taskBuffer=[IO.MemoryStream]::new()
    try{$taskStream.CopyTo($taskBuffer);return ,$taskBuffer.ToArray()}finally{$taskStream.Dispose();$taskBuffer.Dispose()}
}
$taskZipPath=Join-Path $taskBase 'anchor_fine_component_complete_20261020.zip'
$taskPackageReceipt=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'PACKAGE_CHECKS02.json') | ConvertFrom-Json
if((Get-FileHash -LiteralPath $taskZipPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPackageReceipt.zip_sha256){throw 'Complete package identity mismatch'}
$taskArchive=[IO.Compression.ZipFile]::OpenRead($taskZipPath)
$taskPackageCount=0;$taskParentCount=0
try{
    foreach($taskEntry in $taskArchive.Entries){if($taskEntry.FullName.StartsWith('/') -or $taskEntry.FullName.Split('/') -contains '..'){throw 'Unsafe archive path'}}
    $taskManifest=[Text.Encoding]::UTF8.GetString((Read-TaskZipBytes $taskArchive 'PACKAGE_SHA256.json')) | ConvertFrom-Json
    foreach($taskEntry in $taskManifest.files.PSObject.Properties){
        $taskBytes=Read-TaskZipBytes $taskArchive $taskEntry.Name
        $taskHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskBytes)).ToLowerInvariant()
        if($taskHash -ne $taskEntry.Value){throw ('ZIP member mismatch: '+$taskEntry.Name)}
        $taskPackageCount++
    }
    $taskParent=[Text.Encoding]::UTF8.GetString((Read-TaskZipBytes $taskArchive 'DELIVERY_SEAL.json')) | ConvertFrom-Json
    foreach($taskEntry in $taskParent.files.PSObject.Properties){
        $taskHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData((Read-TaskZipBytes $taskArchive $taskEntry.Name))).ToLowerInvariant()
        if($taskHash -ne $taskEntry.Value){throw 'Parent archive seal mismatch'}
        $taskParentCount++
    }
}finally{$taskArchive.Dispose()}
$taskScientific=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'COST_SUPPLEMENT.json') | ConvertFrom-Json
if([double]$taskScientific.LMB_total_seconds -gt 1800){throw 'Original LMB cap exceeded'}
$taskDeliverySeconds=0.0
foreach($taskReceipt in Get-ChildItem -LiteralPath (Join-Path $taskBase 'supervision') -Filter child_exit.json -Recurse){
    $taskNative=Get-Content -Raw -LiteralPath $taskReceipt.FullName | ConvertFrom-Json;$taskSeconds=[double]$taskNative.wall_seconds
    $taskExitPath=Join-Path $taskReceipt.DirectoryName 'exit.json'
    if(Test-Path -LiteralPath $taskExitPath){$taskWindows=Get-Content -Raw -LiteralPath $taskExitPath | ConvertFrom-Json;$taskSeconds=[Math]::Max($taskSeconds,[double]$taskWindows.wall_seconds)}
    $taskDeliverySeconds+=$taskSeconds
}
# Charge the first direct Windows check by its actual enclosing tool wall, larger than native0.9300434.
$taskDeliverySeconds+=1.1554576
$taskBytes=(Get-ChildItem -LiteralPath $taskBase -Recurse -File | Measure-Object Length -Sum).Sum
if($taskBytes -gt 64MB){throw 'Original delivery artifact cap'}
$taskTimer.Stop();$taskDeliverySeconds+=$taskTimer.Elapsed.TotalSeconds
if($taskDeliverySeconds -gt 300){throw 'Original delivery time cap'}
$taskResult=[ordered]@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');supplement_source_identities=$taskCount;complete_ZIP_members_verified=$taskPackageCount;parent_ZIP_seal_members_verified=$taskParentCount;old_delivery_seal_unchanged=$true;LMB_total_seconds=$taskScientific.LMB_total_seconds;original_LMB_cap_seconds=1800;delivery_enclosing_plus_native_seconds=$taskDeliverySeconds;original_delivery_cap_seconds=300;delivery_bytes_before_receipt=$taskBytes;original_delivery_cap_bytes=64MB;headroom_bytes=$taskHeadroom;wall_seconds=$taskTimer.Elapsed.TotalSeconds;own_peak_working_set_bytes=(Get-Process -Id $PID).PeakWorkingSet64;full_process_tree_or_observer_peak='UNKNOWN';new_solver_or_model_calls=0}
[IO.File]::WriteAllText($taskRecord,($taskResult|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
$taskPaths=@($taskRecord,(Join-Path $taskBase 'PACKAGE_CHECKS02.json'),(Join-Path $taskBase 'COMPONENT_PACKAGE_NOTE02.md'),$taskZipPath,$PSCommandPath)
$taskHashes=[ordered]@{}
foreach($taskPath in $taskPaths){$taskHashes[$taskPath]=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskFinal=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');files=$taskHashes;prior_supplement_seal_sha256=(Get-FileHash -LiteralPath (Join-Path $taskBase 'FINAL_SUPPLEMENT_SEAL.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText((Join-Path $taskBase 'COMPLETE_PACKAGE_SEAL.json'),($taskFinal|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{passed=$true;supplement_identities=$taskCount;archive_members=$taskPackageCount;parent_seal_members=$taskParentCount;LMB_seconds=$taskScientific.LMB_total_seconds;delivery_seconds=$taskDeliverySeconds;wall_seconds=$taskTimer.Elapsed.TotalSeconds;delivery_bytes=$taskBytes} | ConvertTo-Json -Compress
