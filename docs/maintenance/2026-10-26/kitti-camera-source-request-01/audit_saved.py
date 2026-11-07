"""Independent saved-HTML link audit; no network or primary extractor import."""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / 'run01/RESULTS.json').read_text(encoding='utf-8'))
body = ROOT / 'run01' / result['final_body']
assert hashlib.sha256(body.read_bytes()).hexdigest().upper() == result['final_body_sha256']
text = body.read_text(encoding='utf-8')
found = []
pattern = r'<a\b[^>]*\bhref\s*=\s*[\x22\x27]([^\x22\x27]+)[\x22\x27][^>]*>(.*?)</a\s*>'
for href, contents in re.findall(pattern, text, re.I | re.S):
    label = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', contents))).strip()
    if label.startswith('Download odometry'):
        found.append(dict(text=label, href=html.unescape(href),
                          resolved_URL=urljoin(result['final_URL'], html.unescape(href))))
assert len(found) == 6 and all(row['href'] == 'user_login.php' for row in found)
saved = json.loads((ROOT / 'PAGE_LINKS.json').read_text(encoding='utf-8'))
primary = [row for row in saved['links'] if row['text'].startswith('Download odometry')]
assert found == [dict(text=row['text'], href=row['href'], resolved_URL=row['resolved_URL'])
                 for row in primary]
with (ROOT / 'FINDINGS.json').open('x', encoding='utf-8') as stream:
    json.dump(dict(passed=True, main_body_sha256=result['final_body_sha256'],
        independently_verified_download_links=found,
        public_direct_archive_URL_obtained=False, login_page_visited=False,
        links_followed=0, network_requests=0,
        first_extractor_console_exit='GBK UnicodeEncodeError after complete text/link/check files saved',
        original_failure_preserved=True, primary_extractor_reexecuted=False,
        no_claim_of_general_or_permanent_download_unavailability=True), stream, indent=2)
print(json.dumps(dict(download_buttons=len(found), all_point_to_login=True,
                      links_followed=0)))
