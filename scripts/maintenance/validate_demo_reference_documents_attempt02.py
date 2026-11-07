"""DRD0 response/blob/selection validator; no network, model, or coordinates."""
import time
START=time.monotonic()
import base64,hashlib,json,resource,signal
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/maintenance/2026-10-15/demo-reference-documentation-01'
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('120s DRD0 validator cap')))
signal.alarm(120)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_path(text):
    text=text.replace('E:\\githouse\\RAP-main','/mnt/e/githouse/RAP-main').replace('\\','/')
    p=Path(text);return p if p.is_absolute() else ROOT/p
def save(name,value):
    data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    assert sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())+len(data)<8*2**20
    with (BASE/name).open('xb') as f:f.write(data)
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip-=1
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data.strip())
def run():
    for name in ('freeze.json','CONTINUATION02.json'):
        for row in read(BASE/name)['files']:
            p=source_path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    rs=[read(p) for p in sorted(BASE.glob('receipt-*.json'))]
    assert [r['index'] for r in rs]==list(range(5))
    for r in rs:
        p=BASE/r['body_path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
        assert r['bytes']<=524288
    assert rs[0]['status']==403 and rs[0]['bytes']==0 and not rs[0]['admitted']
    assert all(r['status']==200 and r['admitted'] and r['complete'] for r in rs[1:])
    assert rs[0]['url']=='https://www.ipb.uni-bonn.de/html/projects/rap/'
    assert rs[1]['url']=='https://register-any-point.github.io/'
    tree=read(BASE/rs[2]['body_path']);assert not tree['truncated'] and len(tree['tree'])==89
    candidates=[e for e in tree['tree'] if e['type']=='blob' and
        (e['path'] in ('README.md','scripts/download_weights_and_demo_data.sh') or
        ('demo' in e['path'].lower() and any(x in e['path'].lower() for x in ('manifest','reference','ground_truth','pose'))
        and e['path'].endswith(('.md','.json','.yaml','.txt'))))]
    candidates=sorted(candidates,key=lambda e:e['path'])[:3]
    obs=read(BASE/'observation.json');assert [e['path'] for e in candidates]==[d['path'] for d in obs['documents']]
    for entry,document in zip(candidates,obs['documents']):
        r=rs[document['response_index']];blob=read(BASE/r['body_path'])
        assert r['url']==f"https://api.github.com/repos/PRBonn/RAP/git/blobs/{entry['sha']}"
        decoded=base64.b64decode(blob['content']);gitsha=hashlib.sha1(f'blob {len(decoded)}\0'.encode()+decoded).hexdigest()
        assert gitsha==entry['sha']==blob['sha']==document['git_blob_SHA1']
        assert len(decoded)==entry['size']==document['bytes']<=131072
        assert (BASE/document['decoded_path']).read_bytes()==decoded
    assert [d['path'] for d in obs['documents']]==['README.md','scripts/download_weights_and_demo_data.sh']
    script=(BASE/obs['documents'][1]['decoded_path']).read_text()
    assert 'https://www.ipb.uni-bonn.de/html/projects/rap/demo_example_data.zip' in script
    parser=Text();parser.feed((BASE/rs[1]['body_path']).read_text())
    text='\n'.join(parser.parts)
    save('author_project_text.json',dict(text=text,source_receipt=1,assets_fetched=False))
    members=read(ROOT/'docs/maintenance/2026-10-15/continuation-handoff-06/DEMO_MEMBER_REQUEST.json')['members']
    documents=text+'\n'+'\n'.join((BASE/d['decoded_path']).read_text() for d in obs['documents'])
    named=[m['path'] for m in members if m['path'] in documents]
    assert not named
    total=sum(r['bytes'] for r in rs);assert total==obs['new_body_bytes']==48895
    assert obs['combined_body_bytes']==1296794+total==1345689<=4194304
    assert tree['sha']==obs['observed_tree_SHA']
    save('validation.json',dict(passed=True,receipts=5,admitted_complete_responses=4,retained_Bonn_403_no_body=True,
        tree_entries=89,tree_complete=True,exact_Git_blob_documents=2,source_tree_SHA=tree['sha'],
        explicitly_named_local_member_paths=named,reference_document_selection=candidates,
        new_body_bytes=48895,combined_body_bytes=1345689,new_network_calls=0,external_reference_authenticated=False,
        absence_claim_scope='Selected exact author metadata documents/tree filename rule only, not repository content or global absence',
        original_failure_retained='PowerShell read-only HOME assignment after retained response; continuation reused both receipts'))
try:run();ok=True;error=None
except BaseException as ex:ok=False;error=repr(ex)
finally:
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    save('validation_resource.json',dict(success=ok,error=error,seconds=time.monotonic()-START,peak_RSS_bytes=rss,GPU_bytes=0))
    assert rss<=128*2**20
    if not ok:raise RuntimeError(error)
