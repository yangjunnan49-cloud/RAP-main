param([Parameter(Mandatory=$true)][string]$InputDocx,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $InputDocx).Path
$pdfTarget = [IO.Path]::GetFullPath($OutputPdf)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($pdfTarget)) | Out-Null
$wordOwned = $null
$docOwned = $null
try {
    $wordOwned = New-Object -ComObject Word.Application
    $wordOwned.Visible = $false
    $wordOwned.DisplayAlerts = 0
    $wordOwned.AutomationSecurity = 3
    $docOwned = $wordOwned.Documents.Open($sourcePath,$false,$true,$false)
    $docOwned.Repaginate()
    $pages = $docOwned.ComputeStatistics(2)
    $docOwned.ExportAsFixedFormat($pdfTarget,17)
    [pscustomobject]@{source=$sourcePath;pdf=$pdfTarget;pages=$pages;bytes=(Get-Item -LiteralPath $pdfTarget).Length} | ConvertTo-Json -Compress
} finally {
    if ($null -ne $docOwned) { $docOwned.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($docOwned) | Out-Null }
    if ($null -ne $wordOwned) { $wordOwned.Quit(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($wordOwned) | Out-Null }
}
