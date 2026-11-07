$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root 'outputs/guard_recorder_integration_20261021/run01'
if(Test-Path -LiteralPath $out){throw 'Preserve earlier run'}
New-Item -ItemType Directory -Path $out | Out-Null
$hashes=@{};foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File){$hashes[$file.Name]=(Get-FileHash -LiteralPath $file.FullName).Hash}
$utf8=[Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $out 'SOURCE_FREEZE.json'),(@{files=$hashes;protocol_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'outputs/guard_recorder_integration_20261021/PROTOCOL.md')).Hash;original_contract_sha256='1E6AE4C5D5158FF42983D1F9B758D2F5861B3D324E282D5C6810F5CF7305398F';no_payload=$true} | ConvertTo-Json -Depth 5),$utf8)
$results=@()
$expected=@{host_deadline='host_owned_stop';linux_deadline='linux_or_host_stage_deadline';observer_loss='host_lease_expired';bad_nonce='nonce_or_sequence_mismatch';headroom_fault='host_memory_guard';rss_fault='observed_worker_group_RSS_cap';identity_rejection='host_owned_stop';source_binding='source_binding_mismatch:worker.py'}
foreach($case in @('normal','host_deadline','linux_deadline','observer_loss','bad_nonce','headroom_fault','rss_fault','identity_rejection','source_binding')){
    & (Join-Path $PSScriptRoot 'host.ps1') -Case $case
    $code=$LASTEXITCODE
    if($case -eq 'observer_loss'){if($code -ne 17){throw 'Observer exit injection missing'}}elseif($code -ne 0){throw ('Host failed: '+$case)}
    $folder=Join-Path $out $case;$wait=[Diagnostics.Stopwatch]::StartNew()
    while(-not(Test-Path -LiteralPath (Join-Path $folder 'runner_exit.json')) -and $wait.Elapsed.TotalSeconds -lt 5){Start-Sleep -Milliseconds 50}
    if(-not(Test-Path -LiteralPath (Join-Path $folder 'runner_exit.json'))){throw ('Watcher did not close: '+$case)}
    $receipt=Get-Content -Raw (Join-Path $folder 'runner_exit.json') | ConvertFrom-Json
    if($receipt.cleanup_error){throw ('Cleanup failed: '+$case)}
    if($case -eq 'normal'){if(-not $receipt.success){throw ('Normal failed: '+$receipt.error)}}
    elseif($receipt.success -or $receipt.error -ne $expected[$case]){throw ('Expected guard not reached: '+$case+' '+$receipt.error)}
    if($case -eq 'source_binding'){if($receipt.worker_launched){throw 'Mismatched source launched worker'}}
    else{
        $worker=Get-Content -Raw (Join-Path $folder 'worker_exit.json') | ConvertFrom-Json
        if($worker.controls -ne 15){throw ('Stub controls incomplete: '+$case)}
    }
    if($case -eq 'observer_loss'){
        if($receipt.stop_after_last_accepted_reply -gt 2.5){throw 'Lease loss stop too slow'}
        $grandchild=Get-Content -Raw (Join-Path $folder 'grandchild_exit.json') | ConvertFrom-Json
        if(-not $grandchild.exited){throw 'Owned grandchild did not stop'}
    }
    $results+=@{case=$case;passed=$true;receipt=$receipt}
    Write-Output ($case+' PASS '+$receipt.error)
}
[IO.File]::WriteAllText((Join-Path $out 'RESULTS.json'),(@{passed=$true;cases=$results;cases_count=$results.Count;stub_controls_per_launched_worker=15;scientific_payloads=0;native_integration=$false;OS_isolation_certified=$false} | ConvertTo-Json -Depth 8),$utf8)
