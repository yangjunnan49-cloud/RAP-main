$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-14/windows-pipe-capture-01'
$utf8=[System.Text.UTF8Encoding]::new($false)
$controller=Get-Process -Id $PID
$controllerStart=[System.Diagnostics.Stopwatch]::StartNew()
$executable=$controller.Path
$cases=@('normal','stdout_overflow','stderr_overflow','both_flood','nonzero','timeout','empty','binary')

function Write-ExclusiveJson([string]$Path,$Value,[int]$Limit){
    $body=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 20 -Compress)+"`n")
    if($body.Length -gt $Limit){throw 'Terminal metadata cap'}
    $stream=[System.IO.FileStream]::new($Path,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
    try{$stream.Write($body)}finally{$stream.Dispose()}
}

function Open-Journal([string]$Folder){
    $path=Join-Path $Folder 'evidence.rdj'
    $stream=[System.IO.FileStream]::new($path,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
    $binary=[System.IO.BinaryWriter]::new($stream,$utf8,$true)
    $binary.Write($utf8.GetBytes('RAPBEJ01'));$binary.Write([uint32]2048);$binary.Write([uint32]4)
    return @{Stream=$stream;Binary=$binary;Digest=[System.Security.Cryptography.IncrementalHash]::CreateHash([System.Security.Cryptography.HashAlgorithmName]::SHA256);Status=1;Reserved=0L;Actual=0L;Count=0;Charged=@{1=0;2=0;3=0;4=0};Limits=@{1=256;2=128;3=128;4=256};Closed=$false}
}

function Add-Record($State,[int]$Channel,[byte[]]$Body){
    if($State.Closed -or $State.Status -ne 1){throw 'Journal not writable'}
    $length=5+$Body.Length
    if($Body.Length -gt ($State.Limits[$Channel]-$State.Charged[$Channel]) -or $length -gt (2048-80-$State.Reserved)){
        $State.Status=2;return $false
    }
    $State.Reserved+=$length;$State.Charged[$Channel]+=$Body.Length
    $frame=[byte[]]::new($length);$frame[0]=[byte]$Channel
    [System.Buffer]::BlockCopy([System.BitConverter]::GetBytes([uint32]$Body.Length),0,$frame,1,4)
    [System.Buffer]::BlockCopy($Body,0,$frame,5,$Body.Length)
    try{$State.Stream.Write($frame);$State.Digest.AppendData($frame);$State.Actual+=$length;$State.Count++}
    catch{$State.Status=3;throw}
    return $true
}

function Close-Journal($State){
    if($State.Closed){return}
    try{
        $b=$State.Binary
        $b.Write($utf8.GetBytes('RAPEND01'));$b.Write([byte]$State.Status)
        $b.Write([uint64]$State.Reserved);$b.Write([uint32]$State.Count);$b.Write([uint64]$State.Actual)
        $b.Write($State.Digest.GetHashAndReset());$b.Write([byte[]]::new(3));$b.Flush()
    }finally{$State.Digest.Dispose();$State.Binary.Dispose();$State.Stream.Dispose();$State.Closed=$true}
}

function Invoke-FixedCase([string]$Mode){
    $folder=Join-Path $base "fixtures/$Mode"
    if(Test-Path -LiteralPath $folder){throw 'Existing fixture directory'}
    [System.IO.Directory]::CreateDirectory($folder)|Out-Null
    $state=Open-Journal $folder
    $launch=$utf8.GetBytes((@{event='launch';mode=$Mode}|ConvertTo-Json -Compress))
    if(-not (Add-Record $state 4 $launch)){throw 'Launch metadata overflow'}
    $start=[System.Diagnostics.Stopwatch]::StartNew()
    $process=[System.Diagnostics.Process]::new()
    $psi=[System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$executable;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    foreach($arg in @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'windows_pipe_fixture.ps1'),'-Mode',$Mode)){$psi.ArgumentList.Add($arg)}
    $process.StartInfo=$psi
    $nativeStarted=$false;$reaped=$false;$reason=$null;$terminated=$false
    $observed=@{2=0L;3=0L};$stored=@{2=0L;3=0L};$eof=@{2=$false;3=$false}
    $peak=0L;$cpu=0.0
    try{
        if(-not $process.Start()){throw 'Native start failed'}
        $nativeStarted=$true;$nativePid=$process.Id
        $streams=@{2=$process.StandardOutput.BaseStream;3=$process.StandardError.BaseStream}
        $buffers=@{2=[byte[]]::new(64);3=[byte[]]::new(64)};$tasks=@{}
        foreach($channel in @(2,3)){$tasks[$channel]=$streams[$channel].ReadAsync($buffers[$channel],0,64)}
        $deadline=if($Mode -eq 'timeout'){0.5}else{5.0}
        while(-not $process.HasExited -or -not ($eof[2] -and $eof[3])){
            $process.Refresh()
            try{$peak=[Math]::Max($peak,$process.PeakWorkingSet64);$cpu=$process.TotalProcessorTime.TotalSeconds}catch{}
            if($null -eq $reason -and $start.Elapsed.TotalSeconds -ge $deadline){$reason='timeout';$state.Status=3}
            if($null -ne $reason -and -not $process.HasExited -and -not $terminated){$process.Kill();$terminated=$true}
            foreach($channel in @(2,3)){
                if(-not $eof[$channel] -and $tasks[$channel].IsCompleted){
                    $n=$tasks[$channel].GetAwaiter().GetResult()
                    if($n -eq 0){$eof[$channel]=$true;continue}
                    $observed[$channel]+=$n
                    if($null -eq $reason){
                        $body=[byte[]]::new($n);[System.Buffer]::BlockCopy($buffers[$channel],0,$body,0,$n)
                        if(Add-Record $state $channel $body){$stored[$channel]+=$n}else{$reason='log_overflow'}
                    }
                    $tasks[$channel]=$streams[$channel].ReadAsync($buffers[$channel],0,64)
                }
            }
            Start-Sleep -Milliseconds 5
        }
        $process.WaitForExit();$reaped=$true
        $exitCode=$process.ExitCode
        try{$peak=[Math]::Max($peak,$process.PeakWorkingSet64);$cpu=$process.TotalProcessorTime.TotalSeconds}catch{}
        if($exitCode -ne 0 -and $null -eq $reason){$reason='nonzero_exit';$state.Status=3}
        if($peak -le 0 -or $peak -gt 256MB){throw 'Native child working-set cap'}
        Close-Journal $state
        $receipt=[ordered]@{mode=$Mode;pid=$nativePid;native_exit_code=$exitCode;peak_working_set_bytes=$peak;cpu_seconds=$cpu;reason=$reason;termination_requested=$terminated;observed_bytes=@{'2'=$observed[2];'3'=$observed[3]};stored_bytes=@{'2'=$stored[2];'3'=$stored[3]};discarded_observed_bytes=@{'2'=($observed[2]-$stored[2]);'3'=($observed[3]-$stored[3])};EOF_observed=@{'2'=$eof[2];'3'=$eof[3]};wall_seconds=$start.Elapsed.TotalSeconds;admitted=($null -eq $reason -and $exitCode -eq 0);full_intended_flood_output_claim=$false;cooperating_file_envelope=3072}
        Write-ExclusiveJson (Join-Path $folder 'exit.json') $receipt 1024
        return $receipt
    }finally{
        if($nativeStarted -and -not $reaped){if(-not $process.HasExited){$process.Kill()};$process.WaitForExit()}
        $process.Dispose();Close-Journal $state
    }
}

$success=$false;$failure=$null;$rows=@()
try{
    if(-not [System.BitConverter]::IsLittleEndian){throw 'Unsupported byte order'}
    $fixtures=Join-Path $base 'fixtures'
    if(Test-Path -LiteralPath $fixtures){throw 'Existing fixtures preserved'}
    [System.IO.Directory]::CreateDirectory($fixtures)|Out-Null
    foreach($mode in $cases){
        $row=Invoke-FixedCase $mode
        $expected=$mode -in @('normal','empty','binary')
        if($row.admitted -ne $expected){throw "Unexpected admission $mode"}
        $rows+=$row
    }
    $success=$true
}catch{$failure=$_.Exception.ToString();Write-Error -Message $failure -ErrorAction Continue}
finally{
    $controller.Refresh()
    $record=[ordered]@{success=$success;error=$failure;pid=$PID;PowerShell=$PSVersionTable.PSVersion.ToString();executable=$executable;wall_seconds=$controllerStart.Elapsed.TotalSeconds;peak_working_set_bytes=$controller.PeakWorkingSet64;cpu_seconds=$controller.TotalProcessorTime.TotalSeconds;inner_children=$rows.Count;cases=$rows}
    Write-ExclusiveJson (Join-Path $base 'native_controller.json') $record 65536
}
if(-not $success){exit 1}
Write-Output 'WPC0 all8 fixed native Windows children reaped'
exit 0
