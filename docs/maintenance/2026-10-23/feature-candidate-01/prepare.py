"""Prepare immutable copies and source-bound candidate; do not edit production."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT.parents[3]/'dataset_process/extract_sample_features.py'
raw=source.read_bytes()
expected='0D64FB17E9325CA0C7A774A5CDFFD2611F181EA6E04B348603F2809495A669D1'
assert hashlib.sha256(raw).hexdigest().upper()==expected
old=b'keypoint_len = keypoints.shape[0] if keypoints.dim() > 1 else len(keypoints)'
new=b'keypoint_len = keypoints.shape[0] if keypoints.ndim > 1 else len(keypoints)'
assert raw.count(old)==1
candidate=raw.replace(old,new)
(ROOT/'source_snapshot/original.py').write_bytes(raw)
(ROOT/'source_snapshot/candidate.py').write_bytes(candidate)
a=ast.parse(raw);b=ast.parse(candidate)
changed=[]
class Rewrite(ast.NodeTransformer):
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='keypoints' and node.func.attr=='dim' and not node.args and not node.keywords:
            changed.append(node.lineno)
            return ast.copy_location(ast.Attribute(value=node.func.value,attr='ndim',ctx=ast.Load()),node)
        return node
transformed=Rewrite().visit(a)
assert len(changed)==1 and ast.dump(transformed,include_attributes=False)==ast.dump(b,include_attributes=False)
files={}
for f in (ROOT/'runtime').iterdir():
    if f.is_file():files[f.name]=hashlib.sha256(f.read_bytes()).hexdigest().upper()
freeze=dict(files=files,original_sha256=expected,candidate_sha256=hashlib.sha256(candidate).hexdigest().upper(),
    protocol_sha256=hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest().upper(),
    one_AST_expression_changed=True,line=changed[0],CUDA_disabled=True,scope='FC1 CPU synthetic only')
(ROOT/'run01/SOURCE_FREEZE.json').write_text(json.dumps(freeze,indent=2))
print(json.dumps(freeze))
