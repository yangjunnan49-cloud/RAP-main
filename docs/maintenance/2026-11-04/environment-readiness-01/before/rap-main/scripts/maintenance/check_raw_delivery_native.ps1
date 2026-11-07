$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-20/raw-input-contract-01'
$taskDir=Join-Path $taskBase 'supervision/native_delivery_checks'
if(Test-Path -LiteralPath $taskDir){throw 'Preserve existing native checks'}
New-Item -ItemType Directory -Path $taskDir|Out-Null
$taskStart=[DateTime]::UtcNow;$taskWatch=[Diagnostics.Stopwatch]::StartNew();$taskSuccess=$false;$taskError=$null
try{
    $taskSeal=Get-Content -LiteralPath (Join-Path $taskBase 'DELIVERY_SEAL.json') -Raw|ConvertFrom-Json
    $taskN=0;$taskBytes=0
    foreach($taskEntry in $taskSeal.files.psobject.Properties){
        $taskFile=[IO.Path]::GetFullPath((Join-Path $taskBase $taskEntry.Name))
        if(-not $taskFile.StartsWith($taskBase+[IO.Path]::DirectorySeparatorChar)){throw 'Seal path escapes intended base'}
        $taskHash=(Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant()
        if($taskHash -ne $taskEntry.Value){throw "Seal mismatch: $($taskEntry.Name)"}
        $taskN++;$taskBytes+=(Get-Item -LiteralPath $taskFile).Length
    }
    $taskOld=(Get-FileHash -LiteralPath (Join-Path $taskBase '../raw-system-integration-01/R0_CLOSURE_SEAL.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if($taskOld -ne $taskSeal.old_R0_closure_seal_sha256){throw 'Original R0 closure changed'}
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $taskZip=[IO.Compression.ZipFile]::OpenRead((Join-Path $taskBase 'raw_core_GK_36_poses_20261020.zip'))
    try{
        $taskManifestEntry=$taskZip.GetEntry('FILE_SHA256.json');$taskReader=[IO.StreamReader]::new($taskManifestEntry.Open())
        try{$taskManifest=$taskReader.ReadToEnd()|ConvertFrom-Json}finally{$taskReader.Dispose()}
        $taskM=0
        foreach($taskEntry in $taskManifest.files.psobject.Properties){
            $taskMember=$taskZip.GetEntry($taskEntry.Name);if($null -eq $taskMember){throw 'Archive member absent'}
            $taskStream=$taskMember.Open();try{$taskHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskStream)).ToLowerInvariant()}finally{$taskStream.Dispose()}
            if($taskHash -ne $taskEntry.Value){throw "Archive hash mismatch: $($taskEntry.Name)"};$taskM++
        }
        if(@($taskZip.Entries|Where-Object FullName -like '*_lidar.txt').Count -ne 36){throw 'Trajectory export count'}
        $taskArchiveCount=$taskZip.Entries.Count
    }finally{$taskZip.Dispose()}
    $taskResult=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');passed=$true;native_Windows_seal_entries=$taskN;checked_bytes=$taskBytes;zip_members=$taskArchiveCount;zip_manifest_members=$taskM;standard_LiDAR_trajectories=36;old_R0_closure_unchanged=$true;metric_and_operations_figures_visually_checked=$true;new_scientific_predictions=0;new_metrics=0;all_history_certified=$false;native_full_tree_peak='UNKNOWN'}
    [IO.File]::WriteAllText((Join-Path $taskBase 'FINAL_NATIVE_CHECKS.json'),($taskResult|ConvertTo-Json),[Text.UTF8Encoding]::new($false));$taskSuccess=$true
    $taskResult|ConvertTo-Json -Compress
}catch{$taskError=$_.Exception.Message;throw}
finally{
    $taskWatch.Stop();$taskExit=[ordered]@{utc_start=$taskStart.ToString('o');utc_end=[DateTime]::UtcNow.ToString('o');success=$taskSuccess;error=$taskError;wall_seconds=$taskWatch.Elapsed.TotalSeconds;native_bookkeeping=$true;overlapping_Linux_clock_added=$false;new_scientific_predictions=0}
    [IO.File]::WriteAllText((Join-Path $taskDir 'exit.json'),($taskExit|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
}
