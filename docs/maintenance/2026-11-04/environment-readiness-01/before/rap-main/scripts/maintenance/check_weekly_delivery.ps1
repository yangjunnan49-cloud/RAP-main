$ErrorActionPreference='Stop'
$taskStarted=[DateTime]::UtcNow
$taskTimer=[Diagnostics.Stopwatch]::StartNew()
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskBase=Join-Path $taskRoot 'docs\maintenance\2026-10-20\weekly-system-handoff-01'
$taskFolders=@('direct-matching-factors-01','e0-local-map-bundle-01','e0-local-map-six-01','weekly-system-handoff-01')
$taskRecord=Join-Path $taskBase 'WINDOWS_DELIVERY_CHECKS.json'
if(Test-Path -LiteralPath $taskRecord){throw 'Preserve existing native verification'}
$taskMemory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$taskHeadroom=[long]$taskMemory.CommitLimit-[long]$taskMemory.CommittedBytes
if($taskHeadroom -lt 12GB){throw 'Original launch guard not met'}
$taskChecks=[Collections.Generic.List[object]]::new()
$taskSources=[Collections.Generic.List[object]]::new()
$taskSkipped=[Collections.Generic.List[object]]::new()
$taskTotal=0
foreach($taskName in $taskFolders){
    $taskFolder=Join-Path (Split-Path $taskBase) $taskName
    $taskSeal=Get-Content -Raw -LiteralPath (Join-Path $taskFolder 'DELIVERY_SEAL.json') | ConvertFrom-Json
    foreach($taskEntry in $taskSeal.files.PSObject.Properties){
        $taskPath=[IO.Path]::GetFullPath((Join-Path $taskFolder $taskEntry.Name))
        if(-not $taskPath.StartsWith($taskFolder+[IO.Path]::DirectorySeparatorChar)){throw 'Manifest outside intended directory'}
        $taskActual=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if($taskActual -ne $taskEntry.Value){throw ('Delivery identity mismatch: '+$taskPath)}
        $taskTotal++
    }
    $taskChecks.Add([ordered]@{folder=$taskName;entries=$taskSeal.files.PSObject.Properties.Count;seal_sha256=(Get-FileHash -LiteralPath (Join-Path $taskFolder 'DELIVERY_SEAL.json') -Algorithm SHA256).Hash.ToLowerInvariant()})
    if($taskName -ne 'weekly-system-handoff-01'){
        $taskFreeze=Get-Content -Raw -LiteralPath (Join-Path $taskFolder 'freeze.json') | ConvertFrom-Json
        foreach($taskEntry in $taskFreeze.files.PSObject.Properties){
            if($taskEntry.Name -match '^/mnt/([a-z])/(.*)$'){
                $taskPath=$Matches[1].ToUpperInvariant()+':\'+$Matches[2].Replace('/','\')
                $taskActual=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant()
                if($taskActual -ne $taskEntry.Value){throw ('Frozen mapped source mismatch: '+$taskPath)}
                $taskSources.Add([ordered]@{path=$taskPath;sha256=$taskActual})
            }else{$taskSkipped.Add($taskEntry.Name)}
        }
    }
}
$taskHandoff=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'HANDOFF_UPDATE_CHECKS.json') | ConvertFrom-Json
$taskAgents=[IO.File]::ReadAllBytes((Join-Path $taskRoot 'AGENTS.md'))
$taskCut=[Array]::IndexOf($taskAgents,[byte]10)+1
if($taskAgents[$taskCut] -ne 10){throw 'Unexpected inserted entry layout'}
$taskEnd=[Array]::IndexOf($taskAgents,[byte]10,$taskCut+1)+1
$taskRecovered=[byte[]]::new($taskAgents.Length-($taskEnd-$taskCut))
[Array]::Copy($taskAgents,0,$taskRecovered,0,$taskCut)
[Array]::Copy($taskAgents,$taskEnd,$taskRecovered,$taskCut,$taskAgents.Length-$taskEnd)
$taskOldHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskRecovered)).ToLowerInvariant()
if($taskOldHash -ne $taskHandoff.old_AGENTS_sha256){throw 'Prior AGENTS bytes not reproduced'}
if((Get-FileHash -LiteralPath (Join-Path $taskRoot 'AGENTS.md') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskHandoff.new_AGENTS_sha256){throw 'Current handoff identity changed'}
$taskCost=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'COSTS.json') | ConvertFrom-Json
$taskCostRows=[Collections.Generic.List[object]]::new()
foreach($taskPair in @(@('DMF','direct-matching-factors-01'),@('LMB_original','e0-local-map-bundle-01'),@('LMB_extension','e0-local-map-six-01'))){
    $taskSum=0.0
    $taskFolder=Join-Path (Split-Path $taskBase) $taskPair[1]
    foreach($taskReceipt in Get-ChildItem -LiteralPath (Join-Path $taskFolder 'supervision') -Filter child_exit.json -Recurse){
        $taskChild=Get-Content -Raw -LiteralPath $taskReceipt.FullName | ConvertFrom-Json
        $taskWall=[double]$taskChild.wall_seconds
        $taskWindowsPath=Join-Path $taskReceipt.DirectoryName 'exit.json'
        if(Test-Path -LiteralPath $taskWindowsPath){$taskWindows=Get-Content -Raw -LiteralPath $taskWindowsPath | ConvertFrom-Json; $taskWall=[Math]::Max($taskWall,[double]$taskWindows.wall_seconds)}
        $taskSum+=$taskWall
    }
    if([Math]::Abs($taskSum-[double]$taskCost.($taskPair[0]).enclosing_seconds) -gt 1e-7){throw 'Cost ledger differs'}
    $taskCostRows.Add([ordered]@{scope=$taskPair[0];enclosing_seconds=$taskSum})
}
$taskDmfBytes=(Get-ChildItem -LiteralPath (Join-Path (Split-Path $taskBase) 'direct-matching-factors-01') -Recurse -File | Measure-Object Length -Sum).Sum
$taskLmbBytes=0
foreach($taskName in @('e0-local-map-bundle-01','e0-local-map-six-01')){$taskLmbBytes+=(Get-ChildItem -LiteralPath (Join-Path (Split-Path $taskBase) $taskName) -Recurse -File | Measure-Object Length -Sum).Sum}
$taskDeliveryBytes=(Get-ChildItem -LiteralPath $taskBase -Recurse -File | Measure-Object Length -Sum).Sum
if($taskDmfBytes -gt 256MB -or $taskLmbBytes -gt 128MB -or $taskDeliveryBytes -gt 64MB){throw 'Original dossier cap exceeded'}
if([double]$taskCost.DMF.enclosing_seconds -gt 1800 -or [double]$taskCost.LMB_shared_account.enclosing_seconds -gt 1800){throw 'Original scientific time cap exceeded'}
$taskTimer.Stop()
$taskSelf=Get-Process -Id $PID
$taskResult=[ordered]@{passed=$true;utc_start=$taskStarted.ToString('o');utc_end=[DateTime]::UtcNow.ToString('o');native_windows_sha256_entries=$taskTotal;delivery_seals=$taskChecks;mapped_frozen_source_checks=$taskSources;linux_only_source_paths_not_independently_checked=$taskSkipped;old_AGENTS_bytes_recovered=$true;old_AGENTS_sha256=$taskOldHash;cost_ledger_checks=$taskCostRows;dmf_dossier_bytes=$taskDmfBytes;lmb_combined_dossier_bytes=$taskLmbBytes;delivery_bytes_before_this_receipt=$taskDeliveryBytes;guard_headroom_bytes=$taskHeadroom;wall_seconds=$taskTimer.Elapsed.TotalSeconds;own_peak_working_set_bytes=$taskSelf.PeakWorkingSet64;observer_or_full_native_tree_peak='UNKNOWN';no_model_or_solver=$true;no_raw_hash_replay=$true;historical_seals_rewritten=$false}
[IO.File]::WriteAllText($taskRecord,($taskResult | ConvertTo-Json -Depth 9),[Text.UTF8Encoding]::new($false))
$taskSupplement=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');files=[ordered]@{'WINDOWS_DELIVERY_CHECKS.json'=(Get-FileHash -LiteralPath $taskRecord -Algorithm SHA256).Hash.ToLowerInvariant()};helper_path=$PSCommandPath;helper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();original_delivery_seal_sha256=(Get-FileHash -LiteralPath (Join-Path $taskBase 'DELIVERY_SEAL.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText((Join-Path $taskBase 'WINDOWS_VERIFICATION_SEAL.json'),($taskSupplement | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{passed=$true;sealed_entries=$taskTotal;mapped_sources=$taskSources.Count;linux_only_sources=$taskSkipped.Count;old_AGENTS_bytes_recovered=$true;wall_seconds=$taskTimer.Elapsed.TotalSeconds;DMF_bytes=$taskDmfBytes;LMB_bytes=$taskLmbBytes;delivery_bytes=$taskDeliveryBytes} | ConvertTo-Json -Compress
