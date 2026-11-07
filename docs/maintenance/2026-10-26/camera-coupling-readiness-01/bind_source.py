import ast,hashlib,json
from pathlib import Path
root=Path(r"E:\githouse\RAP-main\docs\maintenance\2026-10-26\camera-coupling-readiness-01")
paths=[Path(r"E:\githouse\RAP-main\docs\maintenance\2026-10-14\physical-source-role-feasibility-01\source_snapshot\slam_real_dataset.py"),Path(r"E:\githouse\RAP-SLAM\rap_slam\real_dataset.py")]
out=[];trees=[]
for p in paths:
 text=p.read_text(encoding="utf-8")
 nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=="kitti_vertical_correction"]
 assert len(nodes)==1
 node=nodes[0]
 body=node.body[1:] if isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str) else node.body
 dump=ast.dump(ast.Module(body=body,type_ignores=[]),include_attributes=False)
 trees.append(dump)
 out.append(dict(path=str(p),file_bytes=p.stat().st_size,file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),function_start=node.lineno,function_end=node.end_lineno,numeric_body_AST_sha256=hashlib.sha256(dump.encode()).hexdigest()))
result=dict(files=out,numeric_function_AST_equal=trees[0]==trees[1],source_executed=False,point_pose_image_model_reads=0)
with (root/"SOURCE_BINDINGS.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
print(json.dumps(dict(function_AST_equal=result["numeric_function_AST_equal"],source_executed=False)))