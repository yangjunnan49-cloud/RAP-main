from pathlib import Path
import json, hashlib, zipfile
from lxml import etree
from docx import Document
from pypdf import PdfReader
import pypdfium2 as pdfium

BASE = Path(__file__).resolve().parent
BASE.mkdir(parents=True, exist_ok=True)
DOC = Path('C:/Users/AAA/Downloads/RAP_SLAM_组会讲解与问答_20261011 (1).docx')
PDF = Path('C:/Users/AAA/Downloads/RAP_SLAM_20261011.pdf')
doc = Document(DOC)
parts = []
for child in doc.element.body:
    texts = child.xpath('.//w:t')
    line = ''.join(t.text or '' for t in texts)
    if line: parts.append(line)
(BASE/'reference_docx.txt').write_text('\n'.join(parts), encoding='utf-8')
summary = {'files':{},'sections':[],'styles':{},'paragraphs':[],'package':[]}
for f in (DOC,PDF):
    summary['files'][str(f)] = {'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
for s in doc.sections:
    summary['sections'].append({k:float(getattr(s,k).pt) if getattr(s,k) is not None else None for k in ['page_width','page_height','top_margin','bottom_margin','left_margin','right_margin','header_distance','footer_distance']})
for p in doc.paragraphs:
    if not p.text: continue
    summary['paragraphs'].append({'style':p.style.name,'text':p.text,'runs':[{'font':r.font.name,'pt':r.font.size.pt if r.font.size else None,'bold':r.bold} for r in p.runs]})
for st in doc.styles:
    if st.type == 1:
        summary['styles'][st.name] = {'font':st.font.name,'size':st.font.size.pt if st.font.size else None,'bold':st.font.bold,'xml':st.element.xml}
with zipfile.ZipFile(DOC) as z:
    for n in z.namelist():
        b=z.read(n)
        summary['package'].append({'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
reader=PdfReader(PDF)
summary['pdf_pages']=len(reader.pages)
summary['pdf_fonts']=[]
texts=[]
pdf=pdfium.PdfDocument(str(PDF))
out=BASE/'reference_slides';out.mkdir(exist_ok=True)
for i,p in enumerate(reader.pages):
    texts.append(f'PAGE {i+1}\n'+p.extract_text())
    summary.setdefault('pdf_sizes',[]).append([float(p.mediabox.width),float(p.mediabox.height)])
    for v in (p.get('/Resources',{}).get('/Font',{}) or {}).values():
        f=v.get_object()
        summary['pdf_fonts'].append(str(f.get('/BaseFont')))
    page=pdf[i]
    page.render(scale=1.6).to_pil().convert('RGB').save(out/f'page-{i+1:02d}.png')
    page.close()
pdf.close()
summary['pdf_fonts']=sorted(set(summary['pdf_fonts']))
(BASE/'reference_pdf.txt').write_text('\n\n'.join(texts),encoding='utf-8')
(BASE/'reference_inventory.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':summary['pdf_pages'],'pdf_sizes':summary['pdf_sizes'],'fonts':summary['pdf_fonts'],'docx_sections':summary['sections'],'docx_paragraphs':len(summary['paragraphs'])},ensure_ascii=False))
