$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$base=Join-Path $root 'docs/maintenance/2026-10-15/official-demo-metadata-01'
$revision='c8deb301b32bb887acd48371ae93221251a056b5'
$api="https://huggingface.co/api/datasets/YuePanEdward/regx-benchmark/tree/$revision"
$resolve="https://huggingface.co/datasets/YuePanEdward/regx-benchmark/resolve/$revision/"
$utf8=[Text.UTF8Encoding]::new($false)
$handler=[Net.Http.HttpClientHandler]::new();$handler.AllowAutoRedirect=$false
$handler.AutomaticDecompression=[Net.DecompressionMethods]::None
$client=[Net.Http.HttpClient]::new($handler);$client.Timeout=[TimeSpan]::FromSeconds(20)
function Save-Json([string]$Name,$Value){
    $bytes=$utf8.GetBytes(($Value|ConvertTo-Json -Depth 50 -Compress)+"`n")
    $file=[IO.FileStream]::new((Join-Path $base $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$file.Write($bytes)}finally{$file.Dispose()}
}
function Receipts { return @(Get-ChildItem (Join-Path $base 'transfers') -Filter '*.json' | Sort-Object Name | ForEach-Object {Get-Content $_.FullName -Raw | ConvertFrom-Json -AsHashtable}) }
function Check-URL([string]$Url){
    $u=[Uri]$Url
    if($u.Scheme -ne 'https' -or $u.Host -ne 'huggingface.co' -or $u.Fragment){throw 'URL outside official metadata authority'}
    if($Url.StartsWith($api)){return}
    $prefix=if($Url.StartsWith($resolve)){$resolve}else{"https://huggingface.co/api/resolve-cache/datasets/YuePanEdward/regx-benchmark/$revision/"}
    if(-not $Url.StartsWith($prefix)){throw 'URL outside pinned metadata routes'}
    $name=[Uri]::UnescapeDataString($Url.Substring($prefix.Length).Split('?')[0])
    if($name -notin @('README.md','datasets.csv','ATTRIBUTION.md','LICENSE') -and -not $name.EndsWith('/metadata.yaml')){throw 'Nonmetadata payload prohibited'}
}
function Fetch([string]$Url,[string]$Kind){
    Check-URL $Url;$old=@(Receipts);$index=$old.Count
    $spent=[long](($old|Measure-Object acquired_body_bytes -Sum).Sum)
    if($index -ge 40 -or $spent -ge 4194304){throw 'Shared owner request/body cap'}
    $limit=[int][Math]::Min(524288,4194304-$spent)
    $memory=[IO.MemoryStream]::new();$response=$null;$input=$null
    $headers=@{};$status=$null;$final=$null;$complete=$false;$errorText=$null
    try{
        $current=$Url
        for($redirect=0;$redirect -lt 8;$redirect++){
            Check-URL $current;$request=[Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get,$current)
            $request.Headers.TryAddWithoutValidation('Accept-Encoding','identity')|Out-Null
            try{$response=$client.Send($request,[Net.Http.HttpCompletionOption]::ResponseHeadersRead)}finally{$request.Dispose()}
            if([int]$response.StatusCode -in @(301,302,303,307,308)){
                $next=[Uri]::new([Uri]$current,$response.Headers.Location).AbsoluteUri;Check-URL $next
                $response.Dispose();$response=$null;$current=$next;continue
            }
            break
        }
        if($null -eq $response){throw 'Redirect cap'}
        $status=[int]$response.StatusCode;$final=$current
        foreach($h in $response.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
        foreach($h in $response.Content.Headers){$headers[$h.Key.ToLowerInvariant()]=($h.Value -join ', ')}
        if($headers.ContainsKey('content-encoding') -and $headers['content-encoding'] -notin @('','identity')){throw 'Compressed body prohibited'}
        $length=$response.Content.Headers.ContentLength
        if($null -ne $length -and $length -gt $limit){throw 'Declared body exceeds reservation'}
        $input=$response.Content.ReadAsStream();$buffer=[byte[]]::new(65536)
        while($memory.Length -lt $limit){
            $count=[int][Math]::Min($buffer.Length,$limit-$memory.Length)
            $n=$input.Read($buffer,0,$count)
            if($n -eq 0){$complete=$true;break}
            $memory.Write($buffer,0,$n)
        }
        if($memory.Length -eq $limit){$complete=($null -ne $length -and $length -eq $limit)}
        if(-not $complete){throw 'Capped prefix retained; not complete'}
        if($null -ne $length -and $memory.Length -ne $length){throw 'Declared length mismatch'}
        if($status -ne 200){throw "HTTP $status body retained"}
    }catch{$errorText=$_.Exception.ToString()}
    finally{if($input){$input.Dispose()};if($response){$response.Dispose()}}
    $body=$memory.ToArray();$memory.Dispose();$relative='payload/{0:d3}.body' -f $index
    $stream=[IO.FileStream]::new((Join-Path $base $relative),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$stream.Write($body)}finally{$stream.Dispose()}
    $receipt=[ordered]@{index=$index;requested_url=$Url;final_url=$final;kind=$Kind;status=$status;headers=$headers;
        acquired_body_bytes=$body.Length;body_path=$relative;SHA256=[Convert]::ToHexStringLower([Security.Cryptography.SHA256]::HashData($body));
        complete=$complete;admitted=($null -eq $errorText);error=$errorText;transport='Windows HttpClient'}
    Save-Json ('transfers/{0:d3}.json' -f $index) $receipt
    return @{receipt=$receipt;body=$body}
}
try{
    $entries=[Collections.Generic.List[object]]::new();$pages=[Collections.Generic.List[int]]::new();$complete=$false
    $url=$api+'?recursive=true&expand=false&limit=1000'
    for($page=0;$page -lt 12;$page++){
        $f=Fetch $url 'catalog';$r=$f.receipt;$pages.Add($r.index)
        if(-not $r.admitted){break}
        $decoded=$utf8.GetString($f.body)|ConvertFrom-Json -AsHashtable
        foreach($entry in $decoded){$entries.Add($entry)}
        $link=$r.headers['link'];$next=$null
        if($link -match '<([^>]+)>;\s*rel="?next"?'){$next=$Matches[1]}
        if(-not $next){$complete=$true;break};if(-not $next.StartsWith($api)){throw 'Pagination authority changed'};$url=$next
    }
    Save-Json 'catalog_windows.json' @{revision=$revision;complete=$complete;pages=$pages.ToArray();entries=$entries.ToArray()}
    $local=(Get-Content (Join-Path $root 'docs/maintenance/2026-10-15/demo-source-role-01/source-attempt-02/headers_and_roles.json') -Raw|ConvertFrom-Json -AsHashtable).files
    $links=[Collections.Generic.List[object]]::new()
    foreach($row in $local){foreach($entry in $entries){
        $digest=if($entry.lfs.oid){$entry.lfs.oid}else{$entry.lfs.sha256}
        if($digest -eq $row.sha256 -and $entry.size -eq $row.bytes){
            $scene=$entry.path.Substring(0,$entry.path.LastIndexOf('/'))
            $links.Add(@{local_path=$row.path;remote_path=$entry.path;bytes=$row.bytes;SHA256=$digest;scene=$scene})
        }
    }}
    $scenes=@($links|ForEach-Object scene|Sort-Object -Unique)
    $known=@{};foreach($entry in $entries){if($entry.type -eq 'file'){$known[$entry.path]=$entry}}
    $selected=[Collections.Generic.List[string]]::new()
    foreach($name in @('README.md','datasets.csv','ATTRIBUTION.md','LICENSE')){if($known.ContainsKey($name) -and $known[$name].size -le 131072){$selected.Add($name)}}
    foreach($scene in $scenes){$name=$scene+'/metadata.yaml';if($known.ContainsKey($name) -and $known[$name].size -le 131072){$selected.Add($name)}}
    $acquired=[Collections.Generic.List[object]]::new()
    foreach($name in $selected){
        $old=@(Receipts);if($old.Count -ge 40 -or ($old|Measure-Object acquired_body_bytes -Sum).Sum -ge 4194304){break}
        $encoded=($name.Split('/')|ForEach-Object {[Uri]::EscapeDataString($_)}) -join '/'
        $kind=if($name.EndsWith('/metadata.yaml')){'scene_reference'}else{'documentation'}
        $f=Fetch ($resolve+$encoded) $kind
        $acquired.Add(@{path=$name;transfer_index=$f.receipt.index;admitted=$f.receipt.admitted})
    }
    $all=@(Receipts);$total=[long](($all|Measure-Object acquired_body_bytes -Sum).Sum)
    Save-Json 'identity_links.json' @{revision=$revision;catalog_complete=$complete;local_denominator=$local.Count;matches=$links.ToArray();
        matched_local_files=@($links|ForEach-Object local_path|Sort-Object -Unique).Count;matched_scene_parents=$scenes;
        selected_metadata=$selected.ToArray();acquired_metadata=$acquired.ToArray();network_body_bytes=$total;acquisition_body_cap_bytes=4194304;
        canonical_sample_manifests_acquired=$false;point_or_weight_payload_acquired=$false;numeric_coordinate_reference_pose_metric_or_model_calls=0;
        independent_confirmation_admitted=$false;source_link_scope='exact file bytes only; reference provenance/training membership remain separate'}
}finally{$client.Dispose();$handler.Dispose()}
