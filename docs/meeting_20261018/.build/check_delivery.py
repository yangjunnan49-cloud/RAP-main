from pathlib import Path
import json, hashlib, zipfile, re
from lxml import etree
from pypdf import PdfReader
from PIL import Image

B=Path(__file__).resolve().parent
W=B.parent
D=json.loads((B/'meeting_content.json').read_text(encoding='utf-8'))
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
deck=W/'output/RAP_SLAM_组会汇报_20261018.pptx'
word=W/'output/RAP_SLAM_组会讲解与问答_20261018.docx'
with zipfile.ZipFile(deck) as z:
    sp=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda n:int(re.search(r'slide(\d+)',n).group(1)))
    assert len(sp)==12
    texts=[''.join(etree.fromstring(z.read(n)).xpath('//a:t/text()',namespaces=NS)) for n in sp]
    assert len([n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)])==12
    for i,s in enumerate(D['slides']):
        assert s['title'] in texts[i],(i,s['title'])
    for row in D['system_table'][1:]:
        for cell in row:assert cell in texts[0],cell
    assert '56557' in texts[9] and '169671' in texts[9]
    assert len([n for n in z.namelist() if re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml',n)])==5
with zipfile.ZipFile(word) as z:
    body=''.join(etree.fromstring(z.read('word/document.xml')).xpath('//w:t/text()',namespaces=NS))
    for s in D['slides']:assert s['title'] in body
    for marker in ['40','56557','169671','198.329989556','194.401887634']:assert marker in body
    assert '2026年10月18日' in body
pdf=PdfReader(B/'final_word_v2.pdf')
assert len(pdf.pages)==15
counts=[len(p.extract_text().strip()) for p in pdf.pages]
assert all(n>150 for i,n in enumerate(counts,1) if i!=14),counts
assert counts[13]>40 and len(pdf.pages[13].images)>=2
changed=[];identical=[]
for i in range(1,13):
    old=Image.open(B/f'powerpoint_render/幻灯片{i}.PNG').convert('RGB')
    new=Image.open(B/f'powerpoint_final/幻灯片{i}.PNG').convert('RGB')
    (identical if old.size==new.size and old.tobytes()==new.tobytes() else changed).append(i)
refs=json.loads((B/'reference_inventory.json').read_text(encoding='utf-8'))['files']
for p,v in refs.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256']
report={'status':'PASS','ppt_slides':12,'word_pages':15,'native_charts':5,'native_tables':9,'notes':12,'new_scientific_experiment':False,'regx_figure_role':'Known transform construction illustration only; deterministic 450 point rows per view','powerpoint_native_export_changed_slides':changed,'powerpoint_native_export_identical_previously_inspected_slides':identical,'word_page_text_counts':counts,'source_files_unchanged':True,'files':[]}
for f in [deck,word]:report['files'].append({'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(B/'DELIVERY_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
