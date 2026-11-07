# Read file metadata only. Never follow reparse points or run project code.
[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'inventory'),
    [ValidateRange(10, 1800)][int]$MaxSeconds = 300
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$phaseDirectory = [IO.Path]::GetFullPath($PSScriptRoot)
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $outputPath.StartsWith($phaseDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Inventory output must remain inside this maintenance phase.'
}
if (Test-Path -LiteralPath $outputPath) {
    throw 'Output already exists; choose a new directory to preserve the original observation.'
}
[IO.Directory]::CreateDirectory($outputPath) | Out-Null
$roots = @(
    @{id='rap-main'; path='E:/githouse/RAP-main'; recursive=$true},
    @{id='rap-slam'; path='E:/githouse/RAP-SLAM'; recursive=$true},
    @{id='reports'; path='E:/githouse/RAP-SLAM-report'; recursive=$true},
    @{id='datasets'; path='E:/githouse/Datasets'; recursive=$true},
    @{id='codex-records'; path='C:/Users/AAA/Documents/Codex'; recursive=$true},
    @{id='workspace-root'; path='E:/githouse'; recursive=$false}
)
$encoding = [Text.UTF8Encoding]::new($false)
$entriesWriter = [IO.StreamWriter]::new((Join-Path $outputPath 'entries.jsonl'), $false, $encoding)
$errorsWriter = [IO.StreamWriter]::new((Join-Path $outputPath 'errors.jsonl'), $false, $encoding)
$summaries = [Collections.Generic.List[object]]::new()
$buckets = @{}
$stopwatch = [Diagnostics.Stopwatch]::StartNew()
$startedUtc = [DateTime]::UtcNow.ToString('o')

function Write-InventoryError([string]$RootId, [string]$Path, [string]$Message) {
    $errorsWriter.WriteLine((@{root=$RootId; path=$Path; message=$Message} | ConvertTo-Json -Compress))
}

try {
    foreach ($root in $roots) {
        $rootPath = [IO.Path]::GetFullPath($root.path)
        $summary = [ordered]@{
            id=$root.id; path=$rootPath; recursive=$root.recursive;
            files=[long]0; directories=[long]0; logical_bytes=[long]0;
            errors=0; skipped_reparse_points=0; excluded_phase_directories=0;
            enumeration_complete=$true; stop_reason=$null
        }
        if ($stopwatch.Elapsed.TotalSeconds -ge $MaxSeconds) {
            $summary.enumeration_complete = $false
            $summary.stop_reason = 'shared_metadata_scan_wall_limit'
            $summaries.Add($summary)
            continue
        }
        if (-not [IO.Directory]::Exists($rootPath)) {
            $summary.enumeration_complete = $false
            $summary.errors++
            $summary.stop_reason = 'root_missing_or_inaccessible'
            Write-InventoryError $root.id $rootPath $summary.stop_reason
            $summaries.Add($summary)
            continue
        }
        $pending = [Collections.Generic.Stack[IO.DirectoryInfo]]::new()
        $pending.Push([IO.DirectoryInfo]::new($rootPath))
        while ($pending.Count -gt 0) {
            if ($stopwatch.Elapsed.TotalSeconds -ge $MaxSeconds) {
                $summary.enumeration_complete = $false
                $summary.stop_reason = 'shared_metadata_scan_wall_limit'
                break
            }
            $directory = $pending.Pop()
            try {
                foreach ($entry in $directory.EnumerateFileSystemInfos()) {
                    if ($stopwatch.Elapsed.TotalSeconds -ge $MaxSeconds) {
                        $summary.enumeration_complete = $false
                        $summary.stop_reason = 'shared_metadata_scan_wall_limit'
                        break
                    }
                    if ($entry.FullName.Equals($phaseDirectory, [StringComparison]::OrdinalIgnoreCase)) {
                        $summary.excluded_phase_directories++
                        continue
                    }
                    $relative = [IO.Path]::GetRelativePath($rootPath, $entry.FullName).Replace('\', '/')
                    try {
                        $attributes = $entry.Attributes
                        $isDirectory = ($attributes -band [IO.FileAttributes]::Directory) -ne 0
                        $isReparsePoint = ($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
                        $bytes = if ($isDirectory) { [long]0 } else { [long]$entry.Length }
                        $record = [ordered]@{
                            root=$root.id; path=$relative;
                            kind=if ($isDirectory) {'directory'} else {'file'};
                            bytes=$bytes; mtime_utc=$entry.LastWriteTimeUtc.ToString('o');
                            attributes=[string]$attributes; reparse_point=$isReparsePoint
                        }
                        $entriesWriter.WriteLine(($record | ConvertTo-Json -Compress))
                        if ($isReparsePoint) { $summary.skipped_reparse_points++ }
                        if ($isDirectory) {
                            $summary.directories++
                            if ($root.recursive -and -not $isReparsePoint) { $pending.Push($entry) }
                        } else {
                            $summary.files++
                            $summary.logical_bytes += $bytes
                            $parts = $relative.Split('/')
                            $bucketName = if ($parts.Count -gt 1) { $parts[0] } else {'[root-files]'}
                            $key = $root.id + ':' + $bucketName
                            if (-not $buckets.ContainsKey($key)) {
                                $buckets[$key] = [ordered]@{root=$root.id; directory=$bucketName; files=[long]0; logical_bytes=[long]0}
                            }
                            $buckets[$key].files++
                            $buckets[$key].logical_bytes += $bytes
                        }
                    } catch {
                        $summary.errors++
                        $summary.enumeration_complete = $false
                        Write-InventoryError $root.id $entry.FullName $_.Exception.Message
                    }
                }
            } catch {
                $summary.errors++
                $summary.enumeration_complete = $false
                Write-InventoryError $root.id $directory.FullName $_.Exception.Message
            }
        }
        $summaries.Add($summary)
        $entriesWriter.Flush()
        $errorsWriter.Flush()
        Write-Output ("{0}: {1} files, {2:N3} GiB, complete={3}, errors={4}" -f $root.id, $summary.files, ($summary.logical_bytes / 1GB), $summary.enumeration_complete, $summary.errors)
    }
} finally {
    $entriesWriter.Dispose()
    $errorsWriter.Dispose()
}
$result = [ordered]@{
    started_utc=$startedUtc; finished_utc=[DateTime]::UtcNow.ToString('o');
    elapsed_seconds=$stopwatch.Elapsed.TotalSeconds; wall_limit_seconds=$MaxSeconds;
    observation='metadata only; logical bytes may count hardlinks and duplicates repeatedly; contents not hashed; no coherent snapshot claimed';
    excluded_phase=$phaseDirectory; no_reparse_point_traversal=$true;
    roots=@($summaries); buckets=@($buckets.Values | Sort-Object root,directory)
}
[IO.File]::WriteAllText((Join-Path $outputPath 'SUMMARY.json'), ($result | ConvertTo-Json -Depth 6) + "`n", $encoding)
Write-Output ('Saved: ' + $outputPath)
