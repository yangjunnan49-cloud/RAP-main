param([Parameter(Mandatory=$true)][string]$Mode)
$ErrorActionPreference='Stop'
if($Mode -eq 'baseline'){Start-Sleep -Milliseconds 100;exit 0}
if($Mode -notin @('early_burst','late_burst')){throw 'Unknown fixed mode'}
$bytes=[byte[]]::new(64MB)
for($i=0;$i -lt $bytes.Length;$i+=4096){$bytes[$i]=1}
if($Mode -eq 'early_burst'){
    $bytes=$null;[GC]::Collect();[GC]::WaitForPendingFinalizers()
    Start-Sleep -Milliseconds 100
}
exit 0
