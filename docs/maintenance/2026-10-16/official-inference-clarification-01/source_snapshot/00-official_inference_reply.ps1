param([ValidateSet('freeze','fetch','validate')][string]$Stage)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'docs/maintenance/2026-10-16/official-inference-clarification-01'
$taskUtf8=[Text.UTF8Encoding]::new($false)
$taskUrl='https://api.github.com/repos/PRBonn/RAP/issues/3/comments?per_page=30'
function Hash([string]$path){(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save([string]$name,$obj){
 $data=$taskUtf8.GetBytes(($obj|ConvertTo-Json -Depth 30)+[Environment]::NewLine)
 if([long]((Get-ChildItem -LiteralPath $taskBase -Recurse -File|Measure-Object Length -Sum).Sum)+$data.Length+131072 -gt 8MB){throw 'Dossier reservation'}
 $stream=[IO.FileStream]::new((Join-Path $taskBase $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$stream.Write($data)}finally{$stream.Dispose()}
}
if($Stage -eq 'freeze'){
 $paths=@($PSCommandPath,(Join-Path $PSScriptRoot 'official_inference_reply_control.ps1'),(Join-Path $PSScriptRoot 'native_memory_probe.ps1'),(Join-Path $taskBase 'OWNER_SCOPE.md'),(Join-Path $taskBase 'PROTOCOL.md'),(Join-Path $taskRoot 'docs/maintenance/2026-10-15/author-demo-clarification-01/response-00.json'))
 $snapshot=Join-Path $taskBase 'source_snapshot';New-Item -ItemType Directory -Path $snapshot|Out-Null
 $records=@();$index=0
 foreach($path in $paths){$name=('{0:d2}-' -f $index)+[IO.Path]::GetFileName($path);$copy=Join-Path $snapshot $name;$bytes=[IO.File]::ReadAllBytes($path);$stream=[IO.FileStream]::new($copy,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$stream.Write($bytes)}finally{$stream.Dispose()};$records+=[ordered]@{path=$path;bytes=$bytes.Length;sha256=(Hash $path);snapshot_file=('source_snapshot/'+$name)};$index++}
 Save 'SOURCE_FREEZE.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');url=$taskUrl;body_cap_bytes=65536;old_metadata_body_bytes=1357466;combined_metadata_cap_bytes=4194304;files=$records})
 Save 'INCOMPLETE' @{pending='One exact public reply and independent receipt validation'}
 exit 0
}
$freeze=Get-Content -LiteralPath (Join-Path $taskBase 'SOURCE_FREEZE.json') -Raw|ConvertFrom-Json
foreach($f in $freeze.files){if((Hash $f.path) -ne $f.sha256 -or (Get-Item -LiteralPath $f.path).Length -ne $f.bytes){throw 'Source identity mismatch'}}
if($Stage -eq 'validate'){
 $r=Get-Content -LiteralPath (Join-Path $taskBase 'RECEIPT.json') -Raw|ConvertFrom-Json
 $path=Join-Path $taskBase 'response.body'
 if(-not $r.admitted -or -not $r.complete -or $r.status -ne 200 -or $r.url -ne $taskUrl -or (Hash $path) -ne $r.sha256 -or (Get-Item $path).Length -ne $r.delivered_body_bytes -or $r.delivered_body_bytes -gt 65536){throw 'Receipt admission fails'}
 $comments=@(Get-Content -LiteralPath $path -Raw -Encoding utf8|ConvertFrom-Json)
 $summaries=@(foreach($c in $comments){if($c.url -notmatch '^https://api.github.com/repos/PRBonn/RAP/issues/comments/[0-9]+$' -or $c.html_url -notmatch '^https://github.com/PRBonn/RAP/issues/3#issuecomment-[0-9]+$' -or -not $c.user.login -or $null -eq $c.body){throw 'Unexpected comment schema'};[ordered]@{id=$c.id;login=$c.user.login;author_association=$c.author_association;created_at=$c.created_at;updated_at=$c.updated_at;html_url=$c.html_url;body=$c.body}})
 $completePage=-not $r.headers.link -and $comments.Count -lt 30
 Save 'VALIDATION.json' ([ordered]@{status='EXACT_PUBLIC_REPLY_IDENTITY_AND_SCHEMA_VALIDATED';response_sha256=$r.sha256;delivered_body_bytes=$r.delivered_body_bytes;combined_metadata_body_bytes=(1357466+$r.delivered_body_bytes);combined_metadata_cap_pass=(1357466+$r.delivered_body_bytes -le 4194304);complete_page_supported=$completePage;comment_count=$comments.Count;comments=$summaries;independent_body_rehash=$true;network_requests=0;no_model_or_pose_arithmetic=$true})
 Write-Output ($summaries|ConvertTo-Json -Depth 8)
 exit 0
}
if(Test-Path -LiteralPath (Join-Path $taskBase 'REQUEST_STARTED.json')){throw 'No request retry allowed'}
Save 'REQUEST_STARTED.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');url=$taskUrl;method='GET';maximum_requests=1})
$clock=[Diagnostics.Stopwatch]::StartNew()
$handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false;$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(30)
$request=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$taskUrl)
$request.Headers.TryAddWithoutValidation('User-Agent','RAP-fixed-compatibility-reply-audit')|Out-Null
$request.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
$memory=[IO.MemoryStream]::new();$response=$null;$headers=@{};$status=$null;$complete=$false;$errorText=$null
try{
 $response=$client.Send($request,[Net.Http.HttpCompletionOption]::ResponseHeadersRead);$status=[int]$response.StatusCode
 foreach($h in $response.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
 foreach($h in $response.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
 if($status -ne 200){throw "Non-200 HTTP $status; body not read"}
 if($headers['content-encoding'] -and $headers['content-encoding'] -ne 'identity'){throw 'Encoded body not admitted'}
 $length=$response.Content.Headers.ContentLength
 if($null -ne $length -and $length -gt 65536){throw 'Declared body exceeds fixed cap'}
 $stream=$response.Content.ReadAsStream()
 try{$buffer=[byte[]]::new(8192);while($memory.Length -lt 65536){if($clock.Elapsed.TotalSeconds -gt 60){throw 'Bounded source read deadline'};$n=$stream.Read($buffer,0,[int][Math]::Min($buffer.Length,65536-$memory.Length));if($n -eq 0){$complete=$true;break};$memory.Write($buffer,0,$n)}}finally{$stream.Dispose()}
 if($memory.Length -eq 65536){$complete=($null -ne $length -and $length -eq 65536)}
 if(-not $complete -or ($null -ne $length -and $length -ne $memory.Length)){throw 'Incomplete bounded body'}
}catch{$errorText=$_.Exception.ToString()}
finally{
 if($response){$response.Dispose()};$request.Dispose();$client.Dispose();$handler.Dispose()
 $body=$memory.ToArray();$memory.Dispose();$path=Join-Path $taskBase 'response.body'
 $out=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$out.Write($body)}finally{$out.Dispose()}
 Save 'RECEIPT.json' ([ordered]@{utc=[DateTime]::UtcNow.ToString('o');url=$taskUrl;status=$status;headers=$headers;delivered_body_bytes=$body.Length;sha256=(Hash $path);complete=$complete;admitted=($null -eq $errorText);error=$errorText;transport_seconds=$clock.Elapsed.TotalSeconds;requests=1;retries=0;redirects_followed=0;old_metadata_body_bytes=1357466;combined_metadata_body_bytes=(1357466+$body.Length)})
}
if($errorText){throw $errorText}
Write-Output 'Exact public reply body acquired; independent validation pending.'
