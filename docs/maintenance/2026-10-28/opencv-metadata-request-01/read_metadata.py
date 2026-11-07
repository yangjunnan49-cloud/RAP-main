import hashlib,importlib.metadata,json,platform,sys
from pathlib import Path
from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'run01/RESULTS.json').read_text(encoding='utf-8-sig'));p=ROOT/'run01'/r['final_body'];assert hashlib.sha256(p.read_bytes()).hexdigest().upper()==r['final_body_sha256'];j=json.loads(p.read_text(encoding='utf-8'))
tags=set(sys_tags());numpy_version=importlib.metadata.version('numpy');requirements=[]
for t in j['info'].get('requires_dist') or []:
    q=Requirement(t);active=q.marker is None or q.marker.evaluate();requirements.append({'text':t,'active_for_runtime':active,'existing_numpy_satisfies':(numpy_version in q.specifier) if active and q.name.lower()=='numpy' else None})
compatible=[]
for u in j['urls']:
    if u['packagetype']!='bdist_wheel':continue
    name,version,build,wt=parse_wheel_filename(u['filename'])
    if tags & wt:compatible.append({'filename':u['filename'],'url':u['url'],'bytes':u['size'],'sha256':u['digests']['sha256'],'requires_python':u.get('requires_python'),'yanked':u.get('yanked',False)})
o={'project':j['info']['name'],'version':j['info']['version'],'requires_python':j['info'].get('requires_python'),'runtime':{'executable':sys.executable,'version':sys.version,'machine':platform.machine(),'platform':sys.platform,'numpy_version':numpy_version},'requirements':requirements,'compatible_wheels':compatible,'new_package_downloads':0,'installs':0};(ROOT/'FINDINGS.json').write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8');print(json.dumps(o))
