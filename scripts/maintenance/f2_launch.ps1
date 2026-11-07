# F2 detached WSL run launcher (execution convenience; no analysis logic).
param([string]$Mode)
$wslArgs = @('-d','Ubuntu-24.04','-u','root','--','bash','/mnt/e/githouse/RAP-main/scripts/maintenance/f2_run.sh',$Mode)
Start-Process wsl.exe -ArgumentList $wslArgs -WindowStyle Hidden
Write-Output "launched $Mode"
