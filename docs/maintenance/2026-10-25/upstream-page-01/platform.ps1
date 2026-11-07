$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskListing=(& wsl --list --verbose | Out-String).Replace([string][char]0,'')
if($LASTEXITCODE -ne 0){throw 'WSL listing failed'}
$taskDistro=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {Get-ItemProperty -LiteralPath $_.PSPath} | Where-Object DistributionName -eq 'Ubuntu-24.04')
if($taskDistro.Count -ne 1 -or $taskDistro[0].BasePath -ne 'E:\WSL\Ubuntu-24.04' -or $taskDistro[0].DefaultUid -ne 1000 -or $taskDistro[0].Version -ne 2){throw 'Registration differs'}
$taskActive=Get-Item -LiteralPath 'E:\WSL\Ubuntu-24.04\ext4.vhdx'
$taskBackup=Get-Item -LiteralPath 'E:\WSL-Backup\Ubuntu-24.04-before-move-20261022.vhdx'
$taskLegacy='C:\Users\AAA\AppData\Local\wsl\{b747c46b-d03b-4b14-8c3e-186c6a17f4ee}'
$taskLink=Get-Item -LiteralPath $taskLegacy
if($taskLink.LinkType -ne 'Junction' -or @($taskLink.Target)[0] -ne 'E:\WSL\Ubuntu-24.04'){throw 'Compatibility link differs'}
$taskIdE=(& fsutil file queryfileid 'E:\WSL\Ubuntu-24.04\ext4.vhdx' | Out-String).Trim()
if($LASTEXITCODE -ne 0){throw 'Active file ID query failed'}
$taskIdC=(& fsutil file queryfileid (Join-Path $taskLegacy 'ext4.vhdx') | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $taskIdE -ne $taskIdC){throw 'VHD identities differ'}
$taskConfigHash=(Get-FileHash -LiteralPath 'C:\Users\AAA\.wslconfig' -Algorithm SHA256).Hash
if($taskConfigHash -ne '8FD36EE0789EBE92BB06729A08FAD9C1779C8CC3EAEF8310905E5B7EBC8BB4DC'){throw 'WSL configuration differs'}
if($taskBackup.Length -ne 44881149952){throw 'Backup size differs'}
$taskGit=@{}
foreach($taskRepo in @('RAP-main','RAP-SLAM')){
    $taskPath='E:/githouse/'+$taskRepo
    $taskHead=(& git -c "safe.directory=$taskPath" -C $taskPath rev-parse HEAD | Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'Git HEAD read failed'}
    $taskStatus=(& git -c "safe.directory=$taskPath" -C $taskPath status --short --untracked-files=no | Out-String).TrimEnd()
    if($LASTEXITCODE -ne 0){throw 'Git status read failed'}
    $taskGit[$taskRepo]=@{HEAD=$taskHead;tracked_status=$taskStatus;remote_sync_checked=$false}
}
if($taskGit['RAP-main'].HEAD -ne '4055d929c594b0033aafc6eed339c910369eef55' -or $taskGit['RAP-SLAM'].HEAD -ne '6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6'){throw 'HEAD differs'}
$taskRecord=@{passed=$true;utc=[DateTimeOffset]::UtcNow.ToString('o');WSL_listing=$taskListing;registration=@{BasePath=$taskDistro[0].BasePath;DefaultUid=$taskDistro[0].DefaultUid;Version=$taskDistro[0].Version};active_vhd=@{bytes=$taskActive.Length;last_write_UTC=$taskActive.LastWriteTimeUtc.ToString('o')};backup=@{bytes=$taskBackup.Length;last_write_UTC=$taskBackup.LastWriteTimeUtc.ToString('o');full_hash_repeated=$false};junction=@{type=$taskLink.LinkType;target=@($taskLink.Target)[0]};file_id_E=$taskIdE;file_id_compatibility_C=$taskIdC;same_file_id=$true;wslconfig_sha256=$taskConfigHash;direct_boot_without_Junction_tested=$false;no_registry_service_config_link_or_backup_change=$true;WSL_started_by_this_round=$false;observed_Stopped=($taskListing -match 'Ubuntu-24.04\s+Stopped');git=$taskGit}
[IO.File]::WriteAllText((Join-Path $taskRoot 'PLATFORM_CHECKS.json'),($taskRecord | ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
@{passed=$true;WSL_observed_Stopped=($taskListing -match 'Ubuntu-24.04\s+Stopped');BasePath=$taskDistro[0].BasePath;same_file_id=$true;backup_retained=$true;HEADs_unchanged=$true} | ConvertTo-Json
