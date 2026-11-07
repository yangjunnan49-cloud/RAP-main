$ErrorActionPreference = 'Stop'
$taskOutput = $PSScriptRoot
$taskReceipt = Join-Path $taskOutput 'LIVE_CHECKS.json'
if (Test-Path -LiteralPath $taskReceipt) { throw 'Preserve the existing receipt; use a separate attempt directory.' }
$taskMigration = 'C:\Users\AAA\Documents\Codex\2026-10-21\y\outputs\wsl_migration_20261022'
$taskProbe = 'C:\Users\AAA\Documents\Codex\2026-10-21\y\work\wsl_migration_20261022_01\inspect_environment.py'
$taskRecord = [ordered]@{ started_utc = [DateTimeOffset]::UtcNow.ToString('o'); scope = 'Infrastructure verification and documentary review only' }

function Invoke-TaskWsl {
    param([string]$Label, [string[]]$WslArguments, [bool]$UnicodeOutput = $false)
    $taskStart = [System.Diagnostics.ProcessStartInfo]::new()
    $taskStart.FileName = 'wsl.exe'
    foreach ($taskArgument in $WslArguments) { [void]$taskStart.ArgumentList.Add($taskArgument) }
    $taskStart.UseShellExecute = $false
    $taskStart.RedirectStandardOutput = $true
    $taskStart.RedirectStandardError = $true
    $taskStart.StandardOutputEncoding = if ($UnicodeOutput) { [Text.Encoding]::Unicode } else { [Text.Encoding]::UTF8 }
    $taskStart.StandardErrorEncoding = [Text.Encoding]::Unicode
    $taskClock = [Diagnostics.Stopwatch]::StartNew()
    $taskProcess = [Diagnostics.Process]::Start($taskStart)
    $taskOut = $taskProcess.StandardOutput.ReadToEndAsync()
    $taskErr = $taskProcess.StandardError.ReadToEndAsync()
    $taskProcess.WaitForExit()
    $taskResult = [ordered]@{ arguments = $WslArguments; exit_code = $taskProcess.ExitCode; elapsed_seconds = $taskClock.Elapsed.TotalSeconds; stdout = $taskOut.GetAwaiter().GetResult(); stderr = $taskErr.GetAwaiter().GetResult() }
    $taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskOutput ($Label + '.json')) -Encoding utf8NoBOM
    if ($taskProcess.ExitCode -ne 0) { throw "WSL check failed: $Label" }
    return [pscustomobject]$taskResult
}

try {
    $taskRecord.registration = @(Get-ChildItem -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {
        Get-ItemProperty -LiteralPath $_.PSPath | Select-Object PSChildName, DistributionName, BasePath, Version, DefaultUid, VhdFileName, Flags
    })
    $taskBefore = Invoke-TaskWsl -Label 'initial_distro_list' -WslArguments @('--list', '--verbose') -UnicodeOutput $true
    $taskRecord.initial_listing = $taskBefore.stdout
    $taskInitiallyStopped = $taskBefore.stdout -match 'Ubuntu-24\.04\s+Stopped\s+2'
    if (-not $taskInitiallyStopped) { throw 'Expected the separately observed Stopped state; do not interrupt another session.' }
    $taskRecord.initial_state = 'Stopped'

    $taskOldDirectory = 'C:\Users\AAA\AppData\Local\wsl\{b747c46b-d03b-4b14-8c3e-186c6a17f4ee}'
    $taskActive = 'E:\WSL\Ubuntu-24.04\ext4.vhdx'
    $taskBackup = 'E:\WSL-Backup\Ubuntu-24.04-before-move-20261022.vhdx'
    $taskRecord.storage = @(Get-Item -LiteralPath $taskActive, $taskBackup, $taskOldDirectory | Select-Object FullName, Length, Attributes, LinkType, Target, LastWriteTimeUtc)
    $taskRecord.active_file_id = (& fsutil.exe file queryfileid $taskActive | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Active VHD file ID query failed.' }
    $taskRecord.legacy_file_id = (& fsutil.exe file queryfileid (Join-Path $taskOldDirectory 'ext4.vhdx') | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Legacy VHD file ID query failed.' }
    $taskRecord.same_file_id = ($taskRecord.active_file_id -eq $taskRecord.legacy_file_id)
    $taskRecord.wslconfig = [ordered]@{
        current_sha256 = (Get-FileHash -LiteralPath 'C:\Users\AAA\.wslconfig' -Algorithm SHA256).Hash
        migration_snapshot_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskMigration 'wslconfig.before') -Algorithm SHA256).Hash
    }
    $taskRecord.wslconfig.unchanged = ($taskRecord.wslconfig.current_sha256 -eq $taskRecord.wslconfig.migration_snapshot_sha256)

    $taskRecord.environment_probe_sha256 = (Get-FileHash -LiteralPath $taskProbe -Algorithm SHA256).Hash
    Write-Output 'Starting a minimal default-user and environment metadata check.'
    try {
        $taskDefaultCode = 'import os,pwd,json; u=pwd.getpwuid(os.getuid()); print(json.dumps(dict(uid=os.getuid(),user=u.pw_name,home=os.path.expanduser("~")),sort_keys=True))'
        $taskDefault = Invoke-TaskWsl -Label 'default_user' -WslArguments @('-d', 'Ubuntu-24.04', '--exec', '/usr/bin/python3', '-B', '-c', $taskDefaultCode)
        $taskRecord.default_user = $taskDefault.stdout | ConvertFrom-Json
        $taskEnvironment = Invoke-TaskWsl -Label 'environment_metadata' -WslArguments @('-d', 'Ubuntu-24.04', '-u', 'root', '--exec', '/usr/bin/python3', '-B', '/mnt/c/Users/AAA/Documents/Codex/2026-10-21/y/work/wsl_migration_20261022_01/inspect_environment.py')
        $taskActual = $taskEnvironment.stdout | ConvertFrom-Json
        $taskBaseline = Get-Content -LiteralPath (Join-Path $taskMigration 'after_environment.json') -Raw | ConvertFrom-Json
        $taskRecord.environment_count = @($taskActual.environments.PSObject.Properties).Count
        $taskRecord.environment_metadata_matches_migration = (($taskActual.environments | ConvertTo-Json -Depth 30 -Compress) -eq ($taskBaseline.environments | ConvertTo-Json -Depth 30 -Compress))
        $taskRecord.selected_files_match_migration = (($taskActual.files | ConvertTo-Json -Depth 30 -Compress) -eq ($taskBaseline.files | ConvertTo-Json -Depth 30 -Compress))
        $taskRecord.home_directories_match_migration = (($taskActual.home_directories | ConvertTo-Json -Compress) -eq ($taskBaseline.home_directories | ConvertTo-Json -Compress))
        $taskRootMount = Invoke-TaskWsl -Label 'root_mount' -WslArguments @('-d', 'Ubuntu-24.04', '--exec', '/usr/bin/findmnt', '-no', 'SOURCE,FSTYPE,TARGET', '/')
        $taskRecord.root_mount = $taskRootMount.stdout.Trim()
        $taskGpu = Invoke-TaskWsl -Label 'gpu_visibility' -WslArguments @('-d', 'Ubuntu-24.04', '-u', 'root', '--exec', '/usr/lib/wsl/lib/nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader')
        $taskRecord.gpu_visibility = $taskGpu.stdout.Trim()
    }
    finally {
        # The distro was stopped before this check and only our finite probes were started.
        $taskStop = Invoke-TaskWsl -Label 'restore_stopped' -WslArguments @('--terminate', 'Ubuntu-24.04') -UnicodeOutput $true
        $taskAfter = Invoke-TaskWsl -Label 'final_distro_list' -WslArguments @('--list', '--verbose') -UnicodeOutput $true
        $taskRecord.final_listing = $taskAfter.stdout
        $taskRecord.restored_stopped = ($taskAfter.stdout -match 'Ubuntu-24\.04\s+Stopped\s+2')
    }

    Write-Output 'WSL probes finished and the initial Stopped state was restored. Hashing the retained offline backup.'
    $taskBackupClock = [Diagnostics.Stopwatch]::StartNew()
    $taskBackupHash = (Get-FileHash -LiteralPath $taskBackup -Algorithm SHA256).Hash
    $taskExpectedBackup = Get-Content -LiteralPath (Join-Path $taskMigration 'BACKUP_CHECKS.json') -Raw | ConvertFrom-Json
    $taskRecord.backup = [ordered]@{
        path = $taskBackup; bytes = (Get-Item -LiteralPath $taskBackup).Length
        sha256 = $taskBackupHash; expected_sha256 = $taskExpectedBackup.backup_sha256
        bytes_and_sha256_match = ($taskBackupHash -eq $taskExpectedBackup.backup_sha256 -and (Get-Item -LiteralPath $taskBackup).Length -eq $taskExpectedBackup.backup_bytes)
        hash_elapsed_seconds = $taskBackupClock.Elapsed.TotalSeconds
    }
    $taskRecord.disk_space = @(Get-PSDrive -Name C, E | Select-Object Name, Used, Free)
    $taskRecord.boot_with_junction_passed = $true
    $taskRecord.direct_boot_without_junction_tested = $false
    $taskRecord.active_vhd_hash_compared_to_preboot_hash = $false
    $taskRecord.model_loads = 0
    $taskRecord.research_runs = 0
    $taskRecord.solver_runs = 0
    $taskRecord.native_python_import_tests_repeated = $false
    $taskRecord.configuration_or_junction_changes = 0
    $taskRecord.passed = ($taskRecord.same_file_id -and $taskRecord.wslconfig.unchanged -and $taskRecord.environment_metadata_matches_migration -and $taskRecord.selected_files_match_migration -and $taskRecord.home_directories_match_migration -and $taskRecord.restored_stopped -and $taskRecord.backup.bytes_and_sha256_match -and $taskRecord.default_user.uid -eq 1000 -and $taskRecord.default_user.user -eq 'aaa' -and $taskRecord.default_user.home -eq '/home/aaa')
}
catch {
    $taskRecord.passed = $false
    $taskRecord.error = $_.Exception.Message
    throw
}
finally {
    $taskRecord.finished_utc = [DateTimeOffset]::UtcNow.ToString('o')
    $taskRecord | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $taskReceipt -Encoding utf8NoBOM
}
Write-Output ($taskRecord | ConvertTo-Json -Depth 30)
