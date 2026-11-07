"""Read-only installed metadata and selected source imports; no model import."""
import ast,hashlib,importlib.metadata,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
repo=root.parents[3]
rows=[]
for name in ('torch','numpy','hydra-core','omegaconf','diffusers','scipy','open3d','einops'):
    try:value=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:value='MISSING'
    rows.append(dict(distribution=name,version=value))
imports=[]
for name in ('rectified_point_flow/flow_model/point_cloud_dit.py','rectified_point_flow/flow_model/layer.py','rectified_point_flow/flow_model/embedding.py'):
    p=repo/name;b=p.read_bytes();tree=ast.parse(b)
    imports.append(dict(path=name,sha256=hashlib.sha256(b).hexdigest().upper(),
        import_statements=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]))
assert 'torch' not in sys.modules
with (root/'DEPENDENCY_INVENTORY.json').open('x') as f:json.dump(dict(distributions=rows,
    selected_source_imports=imports,metadata_only=True,project_modules_executed=False,
    full_transitive_dependency_or_model_load_not_validated=True),f,indent=2)
print(json.dumps(dict(distributions=rows,project_modules_executed=False)))
