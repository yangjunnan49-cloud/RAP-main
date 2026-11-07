"""Offline identity-bound source extraction; no PDF links or scripts executed."""
import ctypes
import hashlib
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path

START = time.monotonic()
ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'run01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = []
        self.metas = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name', '').startswith('citation_'):
            self.metas.append(attrs)
        if self.skip:
            if tag in ('script', 'style', 'nav', 'header', 'footer', 'noscript'):
                self.skip.append(tag)
            return
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'noscript'):
            self.skip.append(tag)
        elif tag in ('p', 'div', 'h1', 'h2', 'h3', 'li', 'br', 'section'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
        elif tag in ('p', 'div', 'h1', 'h2', 'h3', 'li', 'section'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


result = json.loads((RUN / 'RESULTS.json').read_text(encoding='utf-8'))
assert result['passed'] and result['requests'] == 3
objects = {row['role']: row for row in result['objects']}
for row in objects.values():
    path = RUN / row['body_file']
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
abstract = RUN / objects['abstract']['body_file']
parser = Extract()
parser.feed(abstract.read_text(encoding='utf-8'))
parser.close()
lines = [re.sub(r'\s+', ' ', s).strip() for s in ''.join(parser.parts).splitlines()]
with (ROOT / 'ABSTRACT_TEXT.txt').open('x', encoding='utf-8') as stream:
    stream.write('\n'.join(line for line in lines if line) + '\n')
write('ABSTRACT_METADATA.json', parser.metas)

from pypdf import PdfReader

raw_pdf = RUN / objects['paper']['body_file']
reader = PdfReader(raw_pdf)
assert not reader.is_encrypted
pages = []
for number, page in enumerate(reader.pages, 1):
    pages.append(dict(page=number, text=page.extract_text()))
    assert time.monotonic() - START < 90
write('PAPER_PAGES.json', pages)
with (ROOT / 'PAPER_TEXT.txt').open('x', encoding='utf-8') as stream:
    for page in pages:
        stream.write(f'\n--- PDF PAGE {page["page"]} ---\n{page["text"]}\n')
with (ROOT / 'ParisLuco3D_2310.16542v3.pdf').open('xb') as stream:
    stream.write(raw_pdf.read_bytes())
assert sha(ROOT / 'ParisLuco3D_2310.16542v3.pdf') == objects['paper']['sha256']
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) < 16777216
write('EXTRACTION_CHECKS.json', dict(
    passed=True, pages=len(pages), PDF_SHA256=objects['paper']['sha256'],
    abstract_SHA256=objects['abstract']['sha256'], PDF_named_copy_byteexact=True,
    elapsed_seconds=time.monotonic() - START, network_requests=0,
    PDF_embedded_links_followed=0, scripts_executed=0,
    text_extraction_is_not_visual_layout_or_physical_authentication=True))
print(json.dumps(dict(pages=len(pages), text_chars=sum(len(p['text']) for p in pages),
                      PDF_SHA256=objects['paper']['sha256'])))
