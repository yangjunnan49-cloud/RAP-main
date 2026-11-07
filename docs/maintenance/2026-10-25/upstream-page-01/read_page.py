"""Offline main-HTML text/link extraction; links are never requested."""
import hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'run01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
result=json.loads((OUT/'RESULTS.json').read_text(encoding='utf-8'));assert result['passed']
body=OUT/result['final_body'];assert sha(body)==result['final_body_sha256']
assert result['requests']==1 and result['cumulative_delivered_body_bytes']==12443
class Extract(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=[];self.links=[];self.anchor=None
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if self.skip:
            if tag in ('script','style','nav','header','footer','noscript'):self.skip.append(tag)
            return
        if tag in ('script','style','nav','header','footer','noscript'):self.skip.append(tag);return
        if tag in ('p','div','h1','h2','h3','li','br','section','article','tr'):self.parts.append('\n')
        if tag=='a' and 'href' in values:
            self.anchor=dict(href=values['href'],resolved_URL=urljoin(result['final_URL'],values['href']),text='')
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag=='a' and self.anchor is not None:self.links.append(self.anchor);self.anchor=None
        if tag in ('p','div','h1','h2','h3','li','section','article','tr'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:
            self.parts.append(data)
            if self.anchor is not None:self.anchor['text']+=data
parser=Extract();parser.feed(body.read_text(encoding='utf-8'));parser.close()
lines=[re.sub(r'\s+',' ',s).strip() for s in ''.join(parser.parts).splitlines()]
lines=[s for s in lines if s]
with (ROOT/'PAGE_TEXT.txt').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
for row in parser.links:row['text']=re.sub(r'\s+',' ',row['text']).strip()
with (ROOT/'PAGE_LINKS.json').open('x',encoding='utf-8') as f:json.dump(dict(links=parser.links,links_followed=0),f,indent=2,ensure_ascii=False)
assert sha(body)==result['final_body_sha256']
with (ROOT/'TEXT_EXTRACTION_CHECKS.json').open('x',encoding='utf-8') as f:json.dump(dict(passed=True,
    body_sha256=sha(body),strict_UTF8=True,script_style_navigation_ignored=True,
    extracted_lines=len(lines),published_links=len(parser.links),links_followed=0,
    extraction_is_not_browser_rendering_or_complete_dataset_audit=True),f,indent=2)
for i,line in enumerate(lines,1):print(str(i)+': '+line)
