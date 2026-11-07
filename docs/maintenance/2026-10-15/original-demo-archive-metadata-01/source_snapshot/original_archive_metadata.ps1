param([ValidateSet('freeze','network')][string]$Stage)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/original-demo-archive-metadata-01'
$utf8=[Text.UTF8Encoding]::new($false)
$url='https://www.ipb.uni-bonn.de/html/projects/rap/demo_example_data.zip'
$timer=[Diagnostics.Stopwatch]::StartNew()
function Save([string]$Name,$Value){
    $bytes=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 30)+"`n")
    $current=[long]((Get-ChildItem -LiteralPath $base -Recurse -File|Measure-Object Length -Sum).Sum)
    if($current+$bytes.Length -gt 7MB){throw 'Dossier reserve exceeded'}
    $f=[IO.FileStream]::new((Join-Path $base $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$f.Write($bytes)}finally{$f.Dispose()}
}
function Hash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
if($Stage -eq 'freeze'){
    $paths=@((Join-Path $base 'OWNER_SCOPE.md'),(Join-Path $base 'PROTOCOL.md'),$PSCommandPath,
      (Join-Path $PSScriptRoot 'original_archive_control.ps1'),(Join-Path $PSScriptRoot 'native_memory_probe.ps1'),
      (Join-Path $root 'scripts/download_weights_and_demo_data.sh'),
      (Join-Path $root 'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json'),
      (Join-Path $root 'docs/maintenance/2026-10-15/official-demo-metadata-01/CHECKS.json'))
    $files=foreach($p in $paths){@{path=$p;bytes=(Get-Item -LiteralPath $p).Length;sha256=(Hash $p)}}
    Save 'freeze.json' @{files=@($files);network_URL=$url;prior_metadata_body_bytes=1273695;combined_body_cap=4194304;new_body_cap=2920609;utc=[DateTime]::UtcNow.ToString('o')}
    Save 'INCOMPLETE' @{pending='network metadata observation and independent decision'}
    exit 0
}
$freeze=Get-Content -LiteralPath (Join-Path $base 'freeze.json') -Raw|ConvertFrom-Json
foreach($f in $freeze.files){if((Hash $f.path) -ne $f.sha256 -or (Get-Item -LiteralPath $f.path).Length -ne $f.bytes){throw 'Frozen source mismatch'}}
$handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false
$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(25)
$receipts=[Collections.Generic.List[object]]::new();$spent=0L;$decision=$null;$failure=$null
function Fetch([string]$Kind,[long]$Start=-1,[long]$Count=0,[string]$Version=''){
    $method=if($Kind -eq 'HEAD'){[Net.Http.HttpMethod]::Head}else{[Net.Http.HttpMethod]::Get}
    $req=[Net.Http.HttpRequestMessage]::new($method,$url);$resp=$null;$body=[byte[]]::new(0);$errorText=$null;$headers=@{};$status=$null
    $req.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
    if($Kind -ne 'HEAD'){
        if($Count -le 0 -or $Count -gt 512KB -or $script:spent+$Count -gt 2920609){throw 'Range reservation exceeded'}
        $req.Headers.Range=[Net.Http.Headers.RangeHeaderValue]::new($Start,$Start+$Count-1)
        $req.Headers.TryAddWithoutValidation('If-Range',$Version)|Out-Null
    }
    try{
        $resp=$client.Send($req,[Net.Http.HttpCompletionOption]::ResponseHeadersRead);$status=[int]$resp.StatusCode
        foreach($h in $resp.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
        foreach($h in $resp.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
        if($Kind -eq 'HEAD'){if($status -ne 200){throw "HEAD status $status"}}
        else{
            if($status -ne 206){throw "Non206: archive body intentionally not read ($status)"}
            if($headers['content-encoding'] -and $headers['content-encoding'] -ne 'identity'){throw 'Encoded response'}
            if($headers['content-range'] -ne "bytes $Start-$($Start+$Count-1)/$script:length"){throw 'Unexpected content range'}
            if($resp.Content.Headers.ContentLength -ne $Count){throw 'Exact content length absent'}
            $v=if($headers['etag']){$headers['etag']}else{$headers['last-modified']}
            if($v -cne $Version){throw 'Archive version changed'}
            $input=$resp.Content.ReadAsStream();$mem=[IO.MemoryStream]::new()
            try{
                $buf=[byte[]]::new(65536)
                while($mem.Length -lt $Count){$n=$input.Read($buf,0,[int][Math]::Min($buf.Length,$Count-$mem.Length));if($n -eq 0){break};$mem.Write($buf,0,$n)}
                $body=$mem.ToArray();$script:spent+=$body.Length
                if($body.Length -ne $Count){throw 'Truncated metadata range'}
            }finally{$input.Dispose();$mem.Dispose()}
        }
    }catch{$errorText=$_.Exception.ToString()}
    finally{if($resp){$resp.Dispose()};$req.Dispose()}
    $index=$receipts.Count;$name=('response-{0:d2}.bin' -f $index)
    $file=[IO.FileStream]::new((Join-Path $base $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$file.Write($body)}finally{$file.Dispose()}
    $r=@{index=$index;kind=$Kind;url=$url;status=$status;headers=$headers;requested_start=$Start;requested_count=$Count;body_bytes=$body.Length;body_path=$name;sha256=(Hash (Join-Path $base $name));error=$errorText;admitted=($null -eq $errorText)}
    $receipts.Add($r);Save ('receipt-{0:d2}.json' -f $index) $r
    return @{receipt=$r;body=$body}
}
try{
    $h=Fetch 'HEAD';if(-not $h.receipt.admitted){throw 'HEAD prerequisite failed'}
    $script:length=[long]$h.receipt.headers['content-length'];if($length -lt 22){throw 'Unknown archive length'}
    $version=if($h.receipt.headers['etag']){$h.receipt.headers['etag']}else{$h.receipt.headers['last-modified']}
    if(-not $version -or $version.StartsWith('W/')){throw 'Usable If-Range validator absent'}
    $e=Fetch 'EOCD' ($length-22) 22 $version;if(-not $e.receipt.admitted){throw 'Trailer transport prerequisite failed'}
    $b=$e.body
    if([BitConverter]::ToUInt32($b,0) -ne 0x06054b50 -or [BitConverter]::ToUInt16($b,20) -ne 0){throw 'Standard zero-comment ZIP end absent'}
    $disk=[BitConverter]::ToUInt16($b,4);$dirDisk=[BitConverter]::ToUInt16($b,6)
    $entries=[BitConverter]::ToUInt16($b,10);$localEntries=[BitConverter]::ToUInt16($b,8)
    $size=[BitConverter]::ToUInt32($b,12);$offset=[BitConverter]::ToUInt32($b,16)
    if($disk -ne 0 -or $dirDisk -ne 0 -or $entries -eq 65535 -or $entries -ne $localEntries -or [long]$offset+$size -ne $length-22){throw 'Unsupported ZIP layout'}
    $d=Fetch 'CENTRAL_DIRECTORY' $offset $size $version;if(-not $d.receipt.admitted){throw 'Directory transport prerequisite failed'}
    Save 'directory_location.json' @{archive_length=$length;version=$version;entries=$entries;offset=$offset;bytes=$size;trailer_response=1;directory_response=2}
    $decision='COMPLETE_ORIGINAL_ARCHIVE_DIRECTORY_METADATA_OBSERVED_NOT_MEMBER_SHA256_AUTHENTICATION'
}catch{$failure=$_.Exception.ToString();$decision='ORIGINAL_ARCHIVE_METADATA_PREREQUISITE_STOP'}
finally{
    $client.Dispose();$handler.Dispose()
    Save 'network_result.json' @{decision=$decision;failure=$failure;new_body_bytes=$spent;combined_old_new_body_bytes=(1273695+$spent);requests=$receipts.Count;elapsed_seconds=$timer.Elapsed.TotalSeconds;point_or_weight_member_payload_requested=$false;external_reference_authenticated=$false;utc=[DateTime]::UtcNow.ToString('o')}
}
if($failure){exit 2}
