"""Prepare isolated, source-equivalent post-capture validators; no data decode."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=Path('/mnt/e/githouse/RAP-main/scripts/maintenance')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
audit=(OLD/'audit_overlap02.py').read_text().replace('import overlap_core02 as d','import validation_core as d')
metric=(OLD/'overlap_metrics02.py').read_text().replace('import overlap_core02 as p','import validation_core as p')
metric=metric.replace('import numpy as np','import numpy as np\nimport hashlib')
metric=metric.replace("for p,h in seal['files'].items():assert sha(BASE/'bank02'/p)==h,p", "for file_path,h in seal['files'].items():assert sha(BASE/'bank02'/file_path)==h,file_path")
metric=metric.replace("for p,q in zip(seg,ca['kitti_segment_records']):", "for independent_segment,reference_segment in zip(seg,ca['kitti_segment_records']):")
metric=metric.replace('assert p[k]==q[k]','assert independent_segment[k]==reference_segment[k]')
metric=metric.replace('abs(p[k]-q[k])','abs(independent_segment[k]-reference_segment[k])')
assess=(OLD/'assess_overlap03.py').read_text().replace('import overlap_core02 as p','import validation_core as p').replace('from overlap_metrics02 import evaluate_rows','from metrics_adapted import evaluate_rows')
proof={}
for name,old,text in [('audit_adapted.py','audit_overlap02.py',audit),('metrics_adapted.py','overlap_metrics02.py',metric),('assess_adapted.py','assess_overlap03.py',assess)]:
    (ROOT/name).write_text(text)
    proof[name]={'original':str(OLD/old),'original_sha256':digest(OLD/old),'adapted_sha256':digest(ROOT/name)}
    # Compare after the exact documented mechanical substitutions above.
    assert ast.dump(ast.parse((ROOT/name).read_text()))==ast.dump(ast.parse(text))
    original=ast.parse((OLD/old).read_text()); adapted=ast.parse(text)
    original_numbers=[n.value for n in ast.walk(original) if isinstance(n,ast.Constant) and isinstance(n.value,(int,float))]
    adapted_numbers=[n.value for n in ast.walk(adapted) if isinstance(n,ast.Constant) and isinstance(n.value,(int,float))]
    assert original_numbers==adapted_numbers
    proof[name]['all_numeric_constants_unchanged']=True
write(ROOT/'MECHANICAL_DIFF_PROOF.json',proof)
inputroot=Path('/mnt/e/githouse/RAP-main/docs/maintenance/2026-10-21/runtime-overlap-01')
files=list(ROOT.glob('*.py'))+list(ROOT.glob('*.ps1'))+[ROOT/'MECHANICAL_DIFF_PROOF.json']
files += [inputroot/n for n in ('bank_seal02.json','PROTOCOL.md','COSTS_FINAL.json','STATUS.json','CLOSE_CHECK_SEAL.json','CLOSE_DELIVERY_SEAL.json')]
write(ROOT/'SOURCE_FREEZE.json',dict(files={str(p):digest(p) for p in files},original_dossier_bytes=sum(p.stat().st_size for p in inputroot.rglob('*') if p.is_file()),new_cap_seconds=1200,original_P0_cap_seconds=9000,original_P0_budget_compliant=False,source_roles='Original immutable inputs; new validation outputs separate; all numeric constants preserved',GT_numeric_read=False))
print('Prepared three isolated helpers; original files unchanged',flush=True)
