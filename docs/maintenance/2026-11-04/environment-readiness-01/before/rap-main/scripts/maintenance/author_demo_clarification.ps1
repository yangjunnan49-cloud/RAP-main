param([ValidateSet('freeze','observe')][string]$Stage)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/author-demo-clarification-01'
$utf8=[Text.UTF8Encoding]::new($false)
function Hash([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save([string]$name,$value){$bytes=$utf8.GetBytes(($value|ConvertTo-Json -Depth 45)+"`n");if([long]((Get-ChildItem -LiteralPath $base -Recurse -File|Measure-Object Length -Sum).Sum)+$bytes.Length -gt 7MB){throw 'Dossier reserve'};$f=[IO.FileStream]::new((Join-Path $base $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$f.Write($bytes)}finally{$f.Dispose()}}
if($Stage -eq 'freeze'){
 $paths=@($PSCommandPath,(Join-Path $PSScriptRoot 'author_demo_clarification_control.ps1'),(Join-Path $base 'PROTOCOL.md'),(Join-Path $root 'docs/maintenance/2026-10-15/demo-reference-documentation-01/DELIVERY_SEAL.json'))
 Save 'freeze.json' @{files=@($paths|ForEach-Object {@{path=$_;bytes=(Get-Item -LiteralPath $_).Length;sha256=(Hash $_)}});prior_body_bytes=1345689;combined_body_cap=4194304;UTC=[DateTime]::UtcNow.ToString('o')};Save 'INCOMPLETE' @{pending='finite public clarification query'};exit 0
}
$frozen=Get-Content -LiteralPath (Join-Path $base 'freeze.json') -Raw|ConvertFrom-Json
foreach($f in $frozen.files){if((Hash $f.path) -cne $f.sha256 -or (Get-Item -LiteralPath $f.path).Length -ne $f.bytes){throw 'Frozen source mismatch'}}
$handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false;$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(20)
$receipts=[Collections.Generic.List[object]]::new();$spent=0L
function Fetch([string]$url){
 $u=[Uri]$url;if($u.Scheme -ne 'https' -or $u.Host -ne 'api.github.com' -or ($u.AbsolutePath -ne '/search/issues' -and $u.AbsolutePath -notmatch '^/repos/PRBonn/RAP/issues/[0-9]+/comments$')){throw 'Outside finite metadata query'}
 if($receipts.Count -ge 4){throw 'Request cap'};$limit=[int][Math]::Min(524288,1048576-$spent);if($limit -le 0){throw 'Body reservation'}
 $req=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$url);$req.Headers.TryAddWithoutValidation('User-Agent','RAP-exact-demo-reference-review')|Out-Null;$req.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
 $response=$null;$memory=[IO.MemoryStream]::new();$headers=@{};$status=$null;$errorText=$null;$complete=$false
 try{
  $response=$client.Send($req,[Net.Http.HttpCompletionOption]::ResponseHeadersRead);$status=[int]$response.StatusCode
  foreach($h in $response.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')};foreach($h in $response.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
  if($status -ne 200){throw "Non200 response $status; body not read"};if($headers['content-encoding'] -and $headers['content-encoding'] -ne 'identity'){throw 'Encoded response'}
  $length=$response.Content.Headers.ContentLength;if($null -ne $length -and $length -gt $limit){throw 'Declared metadata size exceeds reserve'}
  $stream=$response.Content.ReadAsStream();try{$buf=[byte[]]::new(65536);while($memory.Length -lt $limit){$n=$stream.Read($buf,0,[int][Math]::Min($buf.Length,$limit-$memory.Length));if($n -eq 0){$complete=$true;break};$memory.Write($buf,0,$n)}}finally{$stream.Dispose()}
  if($memory.Length -eq $limit){$complete=($null -ne $length -and $length -eq $limit)};if(-not $complete -or ($null -ne $length -and $length -ne $memory.Length)){throw 'Metadata incomplete'}
 }catch{$errorText=$_.Exception.ToString()}finally{if($response){$response.Dispose()};$req.Dispose()}
 $body=$memory.ToArray();$memory.Dispose();$script:spent+=$body.Length;$i=$receipts.Count;$name='response-{0:d2}.json' -f $i
 $out=[IO.FileStream]::new((Join-Path $base $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write);try{$out.Write($body)}finally{$out.Dispose()}
 $r=@{index=$i;url=$url;status=$status;headers=$headers;body_bytes=$body.Length;body_path=$name;sha256=(Hash (Join-Path $base $name));complete=$complete;error=$errorText;admitted=($null -eq $errorText)}
 $receipts.Add($r);Save ('receipt-{0:d2}.json' -f $i) $r;return @{receipt=$r;body=$body}
}
try{
 $search=Fetch 'https://api.github.com/search/issues?q=repo%3APRBonn%2FRAP%20demo&per_page=20'
 $items=@();$selected=@();$comments=@();$total=$null;$incomplete=$true
 if($search.receipt.admitted){
  $s=$utf8.GetString($search.body)|ConvertFrom-Json;$items=@($s.items);$total=$s.total_count;$incomplete=$s.incomplete_results -or $total -gt $items.Count
  $selected=@($items|Where-Object {$_.comments -gt 0 -and ($_.title+' '+$_.body) -match '(?i)demo_example_data|ground.?truth|pre.?align|reference|registered'}|Sort-Object number|Select-Object -First 3)
  foreach($issue in $selected){$c=Fetch ('https://api.github.com/repos/PRBonn/RAP/issues/'+$issue.number+'/comments?per_page=30');$comments+=@{issue=$issue.number;receipt=$c.receipt.index;admitted=$c.receipt.admitted;reported_comment_count=$issue.comments}}
 }
 Save 'observation.json' @{search_total=$total;returned_issues=$items.Count;search_incomplete=$incomplete;selected_issues=@($selected.number);comment_responses=$comments;requests=$receipts.Count;new_body_bytes=$spent;combined_body_bytes=1345689+$spent;independently_authenticated_reference=$false;external_messages=0;UTC=[DateTime]::UtcNow.ToString('o')}
}finally{$client.Dispose();$handler.Dispose()}
