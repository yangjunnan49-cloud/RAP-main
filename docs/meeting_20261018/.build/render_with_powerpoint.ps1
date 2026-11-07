param([Parameter(Mandatory=$true)][string]$InputPptx,[Parameter(Mandatory=$true)][string]$OutputDir)
$ErrorActionPreference='Stop'
$deckSource=(Resolve-Path -LiteralPath $InputPptx).Path
$renderTarget=[IO.Path]::GetFullPath($OutputDir)
[IO.Directory]::CreateDirectory($renderTarget) | Out-Null
$appOwned=$null
$deckOwned=$null
$priorCount=0
try {
    $appOwned=New-Object -ComObject PowerPoint.Application
    $priorCount=$appOwned.Presentations.Count
    $deckOwned=$appOwned.Presentations.Open($deckSource,-1,0,0)
    $deckOwned.Export($renderTarget,'PNG',1600,900)
    $charts=0
    foreach($slide in $deckOwned.Slides) { foreach($shape in $slide.Shapes) { if($shape.HasChart -eq -1) {$charts++} } }
    [pscustomobject]@{source=$deckSource;slides=$deckOwned.Slides.Count;charts=$charts;render=$renderTarget} | ConvertTo-Json -Compress
} finally {
    if($null -ne $deckOwned) {$deckOwned.Close();[Runtime.InteropServices.Marshal]::ReleaseComObject($deckOwned) | Out-Null}
    if($null -ne $appOwned) {if($priorCount -eq 0){$appOwned.Quit()};[Runtime.InteropServices.Marshal]::ReleaseComObject($appOwned) | Out-Null}
}
