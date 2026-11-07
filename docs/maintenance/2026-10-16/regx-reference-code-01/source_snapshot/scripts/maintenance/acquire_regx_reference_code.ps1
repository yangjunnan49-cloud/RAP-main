$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-16/regx-reference-code-01'
$utf8=[Text.UTF8Encoding]::new($false)
function Save-New($path,$value){$b=$utf8.GetBytes(($value|ConvertTo-Json -Depth 25 -Compress)+"`n");$s=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$s.Write($b)}finally{$s.Dispose()}}
function Blob-Hash($path){$h=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA1);$f=[IO.File]::OpenRead($path);try{$h.AppendData([Text.Encoding]::ASCII.GetBytes("blob $($f.Length)`0"));$b=[byte[]]::new(65536);while(($n=$f.Read($b,0,$b.Length)) -gt 0){$h.AppendData($b,0,$n)};[Convert]::ToHexString($h.GetHashAndReset()).ToLowerInvariant()}finally{$f.Dispose();$h.Dispose()}}
$plan=Get-Content -Raw (Join-Path $base 'PACKAGE_PLAN.json')|ConvertFrom-Json
$auth=Get-Content -Raw (Join-Path $base 'AUTHORIZATION.json')|ConvertFrom-Json
if(-not $auth.authorized -or $auth.plan_SHA256 -ne (Get-FileHash (Join-Path $base 'PACKAGE_PLAN.json') -Algorithm SHA256).Hash.ToLowerInvariant()){throw 'Authorization binding failed'}
$out=Join-Path $base 'transfer-01'
if(Test-Path -LiteralPath $out){throw 'Existing transfer must remain untouched; no retry'}
[IO.Directory]::CreateDirectory($out)|Out-Null
$timer=[Diagnostics.Stopwatch]::StartNew();$total=[long]0;$cap=[long]65536;$errorText=$null
$rows=[Collections.Generic.List[object]]::new();$admitted=[Collections.Generic.List[object]]::new()
$ledger=[IO.StreamWriter]::new([IO.FileStream]::new((Join-Path $out 'requests.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write),$utf8);$ledger.AutoFlush=$true
$handler=[Net.Http.SocketsHttpHandler]::new();$handler.AllowAutoRedirect=$false;$handler.MaxResponseDrainSize=0;$handler.AutomaticDecompression=[Net.DecompressionMethods]::None;$handler.UseCookies=$false;$handler.Credentials=$null
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[Threading.Timeout]::InfiniteTimeSpan
$client.DefaultRequestHeaders.UserAgent.ParseAdd('RAP-source-validation/1.0')
Save-New (Join-Path $out 'STARTED.json') @{utc=[DateTime]::UtcNow.ToString('o');plan_SHA256=$auth.plan_SHA256;cap_bytes=$cap;no_retry=$true;redirect_policy='manual max5 per logical file; all bodies counted';body_scope='application stream delivered bytes, not wire/TLS'}
try{
 for($i=0;$i -lt $plan.files.Count;$i++){
  $item=$plan.files[$i];$uri=[Uri]$item.url;$done=$false
  for($hop=0;$hop -le 5;$hop++){
   if($uri.Scheme -ne 'https'){throw 'Non-HTTPS redirect rejected'}
   $body=Join-Path $out ('{0:d2}-{1:d2}.body' -f $i,$hop)
   $row=[ordered]@{file_index=$i;hop=$hop;logical_path=$item.path;host=$uri.Host;request_uri_SHA256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8.GetBytes($uri.AbsoluteUri))).ToLowerInvariant();utc_start=[DateTime]::UtcNow.ToString('o');status=$null;content_length=$null;body_bytes=[long]0;total_body_bytes_before=$total;error=$null;body_file=[IO.Path]::GetFileName($body)}
   $ledger.WriteLine((@{event='request_start';request=$row}|ConvertTo-Json -Depth 10 -Compress))
   $response=$null;$input=$null;$sink=$null;$cts=$null;$request=$null
   try{
    $remainingSeconds=300-$timer.Elapsed.TotalSeconds;if($remainingSeconds -le 0){throw '300s scope timeout'}
    $cts=[Threading.CancellationTokenSource]::new([TimeSpan]::FromSeconds($remainingSeconds))
    $request=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$uri)
    $response=$client.SendAsync($request,[Net.Http.HttpCompletionOption]::ResponseHeadersRead,$cts.Token).GetAwaiter().GetResult()
    $row.status=[int]$response.StatusCode;$row.content_length=$response.Content.Headers.ContentLength
    $headers=$response.Headers.ToString()+$response.Content.Headers.ToString()
    $row.decoded_header_text_utf8_bytes=$utf8.GetByteCount($headers)
    $row.header_scope='decoded header text only; wire bytes UNKNOWN'
    if($null -ne $row.content_length -and $row.content_length -gt ($cap-$total)){throw 'Content-Length exceeds remaining shared body cap'}
    if($row.status -eq 200 -and $row.content_length -ne $item.bytes){throw 'Successful response Content-Length differs from fixed plan'}
    $input=$response.Content.ReadAsStreamAsync($cts.Token).GetAwaiter().GetResult()
    $sink=[IO.FileStream]::new($body,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    $buffer=[byte[]]::new(65536)
    while($true){
     $room=$cap-$total;if($room -le 0){throw 'Body cap reached without independently confirmed EOF'}
     $want=[int][Math]::Min($buffer.Length,$room)
     $n=$input.ReadAsync($buffer,0,$want,$cts.Token).GetAwaiter().GetResult()
     if($n -eq 0){break}
     $total+=$n;$row.body_bytes+=$n;$sink.Write($buffer,0,$n)
    }
    $sink.Dispose();$sink=$null
    if($null -ne $row.content_length -and $row.body_bytes -ne $row.content_length){throw 'Truncated response'}
    if($row.status -in @(301,302,303,307,308)){
     if($hop -eq 5 -or $null -eq $response.Headers.Location){throw 'Redirect limit/location failure'}
     $uri=[Uri]::new($uri,$response.Headers.Location);continue
    }
    if($row.status -ne 200){throw "HTTP status $($row.status); no retry"}
    if($row.body_bytes -ne $item.bytes){throw 'Final length mismatch'}
    $sha=(Get-FileHash -LiteralPath $body -Algorithm SHA256).Hash.ToLowerInvariant()
    $git=if($item.LFS_SHA256){$null}else{Blob-Hash $body}
    if($item.LFS_SHA256){if($sha -ne $item.LFS_SHA256){throw 'LFS SHA256 mismatch'}}elseif($git -ne $item.Git_blob_SHA1){throw 'Git blob SHA1 mismatch'}
    $admitted.Add(@{path=$item.path;body_file=[IO.Path]::GetFileName($body);bytes=$row.body_bytes;SHA256=$sha;payload_Git_blob_SHA1=$git;LFS_pointer_Git_blob_SHA1=if($item.LFS_SHA256){$item.Git_blob_SHA1}else{$null};identity_match=$true})
    $done=$true;break
   }catch{$row.error=$_.Exception.ToString();throw}
   finally{
    if($sink){$sink.Dispose()};if($input){$input.Dispose()};if($response){$response.Dispose()};if($request){$request.Dispose()};if($cts){$cts.Dispose()}
    $row.utc_end=[DateTime]::UtcNow.ToString('o');$row.total_body_bytes_after=$total;$rows.Add($row)
    $ledger.WriteLine((@{event='request_end';request=$row}|ConvertTo-Json -Depth 10 -Compress))
   }
  }
  if(-not $done){throw 'Logical file incomplete'}
 }
 if($admitted.Count -ne 1 -or ($admitted|Measure-Object bytes -Sum).Sum -ne 39369){throw 'Package cardinality/length mismatch'}
 Save-New (Join-Path $out 'ADMITTED.json') @{revision=$plan.revision;files=$admitted.ToArray();all_body_bytes=$total;cap=$cap;all_matches=$true}
}catch{$errorText=$_.Exception.ToString()}
finally{
 $client.Dispose();$handler.Dispose();$ledger.Dispose()
 Save-New (Join-Path $out 'EXIT.json') @{success=($null -eq $errorText);error=$errorText;wall_seconds=$timer.Elapsed.TotalSeconds;body_bytes=$total;body_cap=$cap;requests=$rows.Count;admitted_files=$admitted.Count;native_memory='see acquisition_execution.json retained-handle observer';no_retry=$true;utc=[DateTime]::UtcNow.ToString('o')}
}
if($errorText){Write-Error $errorText;exit 1}
Write-Output "RegX fixed package admitted: $($admitted.Count) files, $total delivered body bytes"
