param([Parameter(Mandatory=$true)][string]$Mode)
$ErrorActionPreference='Stop'
$outputStream=[Console]::OpenStandardOutput()
$errorStream=[Console]::OpenStandardError()
$utf8=[System.Text.UTF8Encoding]::new($false)
switch($Mode){
    'normal' {$outputStream.Write($utf8.GetBytes("hello-out`n"));$errorStream.Write($utf8.GetBytes("hello-err`n"))}
    'stdout_overflow' {$outputStream.Write([byte[]]::new(4096))}
    'stderr_overflow' {$errorStream.Write([byte[]]::new(4096))}
    'both_flood' {for($i=0;$i -lt 128;$i++){$outputStream.Write([byte[]]::new(64));$errorStream.Write([byte[]]::new(64))}}
    'nonzero' {$errorStream.Write($utf8.GetBytes("planned exit7`n"));$errorStream.Flush();exit 7}
    'timeout' {Start-Sleep -Seconds 10}
    'empty' {}
    'binary' {$outputStream.Write([byte[]]@(255,0,254))}
    default {throw 'Unknown fixed fixture mode'}
}
$outputStream.Flush();$errorStream.Flush()
exit 0
