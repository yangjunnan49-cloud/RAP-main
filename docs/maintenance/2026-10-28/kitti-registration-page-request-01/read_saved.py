"""Offline text/structure extraction. No network, imports of project code or form values."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
receipt = json.loads((ROOT/'run01/RESULTS.json').read_text(encoding='utf-8-sig'))
assert receipt['passed'] and receipt['EOF']
body = ROOT/'run01'/receipt['final_body']
raw = body.read_bytes()
assert hashlib.sha256(raw).hexdigest().upper() == receipt['final_body_sha256']

def location(href):
    p = urlsplit(href)
    return {'scheme':p.scheme,'host':p.netloc,'path':p.path,'query_present':bool(p.query),'fragment_present':bool(p.fragment)}

class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0;self.parts=[];self.forms=[];self.links=[];self.active=None;self.current_form=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','br','div','li','h1','h2','h3','form','tr'):self.parts.append('\n')
        if tag=='form':
            self.current_form={'method':a.get('method','GET').upper(),'action_location':location(a.get('action','')),'inputs':[]}
            self.forms.append(self.current_form)
        if tag=='input' and self.current_form is not None:
            self.current_form['inputs'].append({'type':a.get('type','text'),'name':a.get('name',''),'value_recorded':False})
        if tag=='a':
            self.active={'location':location(a.get('href','')),'text':[]};self.links.append(self.active)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag=='form':self.current_form=None
        if tag=='a':self.active=None
        if tag in ('p','div','li','h1','h2','h3','form','tr'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:
            self.parts.append(data)
            if self.active is not None:self.active['text'].append(data)

decoded=raw.decode('utf-8',errors='strict')
r=Reader();r.feed(decoded);r.close()
lines=[' '.join(line.split()) for line in ''.join(r.parts).splitlines()]
text='\n'.join(line for line in lines if line)+'\n'
for link in r.links:link['text']=' '.join(' '.join(link['text']).split())
(ROOT/'PAGE_TEXT.txt').write_text(text,encoding='utf-8')
structure={'body_sha256':receipt['final_body_sha256'],'body_bytes':len(raw),'UTF8_strict_pass':True,'forms':r.forms,'links':r.links,'form_values_recorded':False,'network_requests':0,'links_followed':0,'form_submissions':0}
(ROOT/'PAGE_STRUCTURE.json').write_text(json.dumps(structure,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
print(json.dumps({'body_bytes':len(raw),'forms':len(r.forms),'links':len(r.links),'extracted_lines':sum(bool(line) for line in lines),'no_network_or_form_action':True},ensure_ascii=True))
